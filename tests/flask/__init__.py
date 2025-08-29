from http import HTTPStatus
import contextvars
import io
import json as _json
import urllib.parse
import html

__all__ = [
    "Flask",
    "request",
    "g",
    "Response",
    "jsonify",
    "make_response",
    "abort",
    "redirect",
    "escape",
    "__version__",
]

__version__ = "0.1-testshim"


# -----------------------------
# Utilities: Headers, MultiDict
# -----------------------------
class Headers:
    def __init__(self, headers=None):
        self._list = []
        if headers:
            if isinstance(headers, Headers):
                self._list.extend(headers._list)
            elif hasattr(headers, "items"):
                for k, v in headers.items():
                    self.add(k, v)
            else:
                for k, v in headers:
                    self.add(k, v)

    @staticmethod
    def _normalize_name(name):
        return str(name)

    def add(self, name, value):
        self._list.append((self._normalize_name(name), str(value)))

    def set(self, name, value):
        lname = name.lower()
        self._list = [(k, v) for (k, v) in self._list if k.lower() != lname]
        self._list.append((self._normalize_name(name), str(value)))

    def get(self, name, default=None):
        lname = str(name).lower()
        for k, v in reversed(self._list):
            if k.lower() == lname:
                return v
        return default

    def getlist(self, name):
        lname = str(name).lower()
        return [v for (k, v) in self._list if k.lower() == lname]

    def __contains__(self, name):
        lname = str(name).lower()
        return any(k.lower() == lname for (k, _) in self._list)

    def __getitem__(self, name):
        value = self.get(name)
        if value is None:
            raise KeyError(name)
        return value

    def __setitem__(self, name, value):
        self.set(name, value)

    def items(self):
        return list(self._list)

    def to_wsgi_list(self):
        return [(str(k), str(v)) for (k, v) in self._list]

    def update(self, other):
        if hasattr(other, "items"):
            for k, v in other.items():
                self.add(k, v)
        else:
            for k, v in other:
                self.add(k, v)


class MultiDict:
    def __init__(self, pairs=None):
        self._data = {}
        if pairs:
            for k, v in pairs:
                self._data.setdefault(k, []).append(v)

    def get(self, key, default=None):
        lst = self._data.get(key)
        if not lst:
            return default
        return lst[-1]

    def getlist(self, key):
        return list(self._data.get(key, []))

    def __getitem__(self, key):
        lst = self._data.get(key)
        if not lst:
            raise KeyError(key)
        return lst[-1]

    def __contains__(self, key):
        return key in self._data

    def items(self):
        for k, lst in self._data.items():
            yield (k, lst[-1])

    def keys(self):
        return self._data.keys()

    def to_dict(self):
        return {k: v[-1] for k, v in self._data.items()}


class EnvironHeaders:
    def __init__(self, environ):
        self.environ = environ

    def get(self, name, default=None):
        lname = name.lower()
        if lname == "content-type":
            return self.environ.get("CONTENT_TYPE", default)
        if lname == "content-length":
            return self.environ.get("CONTENT_LENGTH", default)
        key = "HTTP_" + name.upper().replace("-", "_")
        return self.environ.get(key, default)

    def __getitem__(self, name):
        value = self.get(name)
        if value is None:
            raise KeyError(name)
        return value

    def items(self):
        items = []
        for k, v in self.environ.items():
            if k.startswith("HTTP_"):
                name = k[5:].replace("_", "-").title()
                items.append((name, v))
        if "CONTENT_TYPE" in self.environ:
            items.append(("Content-Type", self.environ["CONTENT_TYPE"]))
        if "CONTENT_LENGTH" in self.environ:
            items.append(("Content-Length", self.environ["CONTENT_LENGTH"]))
        return items


# -----------------------------
# Request and context handling
# -----------------------------
_request_var = contextvars.ContextVar("flask.request")
_g_var = contextvars.ContextVar("flask.g")


class _LocalProxy:
    def __init__(self, getter):
        object.__setattr__(self, "_getter", getter)

    def _get(self):
        return object.__getattribute__(self, "_getter")()

    def __getattr__(self, name):
        return getattr(self._get(), name)

    def __setattr__(self, name, value):
        setattr(self._get(), name, value)

    def __delattr__(self, name):
        delattr(self._get(), name)


def _get_request():
    try:
        return _request_var.get()
    except LookupError:
        raise RuntimeError("Working outside of request context")


def _get_g():
    try:
        return _g_var.get()
    except LookupError:
        raise RuntimeError("Working outside of request context")


request = _LocalProxy(_get_request)
g = _LocalProxy(_get_g)


class Request:
    def __init__(self, environ):
        self.environ = environ
        self.method = environ.get("REQUEST_METHOD", "GET").upper()
        self.path = environ.get("PATH_INFO") or "/"
        self.query_string = environ.get("QUERY_STRING", "")
        self.args = MultiDict(urllib.parse.parse_qsl(self.query_string, keep_blank_values=True))
        self.headers = EnvironHeaders(environ)
        self._cached_data = None

    @property
    def data(self):
        if self._cached_data is None:
            wsgi_input = self.environ.get("wsgi.input", io.BytesIO())
            try:
                length = int(self.environ.get("CONTENT_LENGTH") or 0)
            except (TypeError, ValueError):
                length = 0
            if length > 0:
                self._cached_data = wsgi_input.read(length)
            else:
                self._cached_data = wsgi_input.read()
            if self._cached_data is None:
                self._cached_data = b""
        return self._cached_data

    def get_data(self, as_text=False):
        data = self.data
        return data.decode("utf-8") if as_text else data

    def get_json(self, silent=False):
        data = self.data
        if not data:
            return None
        try:
            return _json.loads(data.decode("utf-8"))
        except Exception:
            if silent:
                return None
            raise

    @property
    def json(self):
        return self.get_json(silent=True)

    @property
    def form(self):
        ctype = (self.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        if ctype in ("application/x-www-form-urlencoded", "multipart/form-data"):
            try:
                decoded = self.data.decode("utf-8")
            except Exception:
                decoded = ""
            return MultiDict(urllib.parse.parse_qsl(decoded, keep_blank_values=True))
        return MultiDict([])

    @property
    def values(self):
        merged = []
        seen = set()
        for k, v in urllib.parse.parse_qsl(self.query_string, keep_blank_values=True):
            merged.append((k, v))
            seen.add(k)
        for k, v in self.form.items():
            merged.append((k, v))
        return MultiDict(merged)


class _G:
    pass


# -----------------------------
# Response and helpers
# -----------------------------
def _status_string(code):
    try:
        phrase = HTTPStatus(code).phrase
    except Exception:
        phrase = "UNKNOWN"
    return f"{code} {phrase}"


def _to_bytes(value):
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return value.encode("utf-8")
    return str(value).encode("utf-8")


class Response:
    def __init__(self, data=b"", status=200, headers=None, mimetype=None, auto_content_length=True):
        self._data = _to_bytes(data)
        self.status_code = self._parse_status(status)
        self.headers = Headers(headers)
        self.mimetype = None
        self._auto_content_length = auto_content_length

        if mimetype:
            self.mimetype = mimetype
            if "Content-Type" not in self.headers:
                self.headers.set("Content-Type", mimetype)
        elif "Content-Type" not in self.headers:
            self.headers.set("Content-Type", "text/plain; charset=utf-8")

        if self._auto_content_length:
            self.headers.set("Content-Length", str(len(self._data)))

    @staticmethod
    def _parse_status(status):
        if isinstance(status, int):
            return status
        if isinstance(status, str):
            parts = status.split()
            try:
                return int(parts[0])
            except Exception:
                pass
        raise ValueError(f"Invalid status: {status!r}")

    @property
    def data(self):
        return self._data

    def set_data(self, data, update_content_length=True):
        self._data = _to_bytes(data)
        if update_content_length and self._auto_content_length:
            self.headers.set("Content-Length", str(len(self._data)))

    def get_data(self, as_text=False):
        return self._data.decode("utf-8") if as_text else self._data

    @property
    def status(self):
        return _status_string(self.status_code)

    @property
    def content_type(self):
        return self.headers.get("Content-Type")

    def get_json(self, silent=False):
        data = self.get_data()
        if not data:
            return None
        try:
            return _json.loads(data.decode("utf-8"))
        except Exception:
            if silent:
                return None
            raise

    @property
    def json(self):
        return self.get_json(silent=True)


def jsonify(*args, **kwargs):
    if args and kwargs:
        raise TypeError("jsonify() behavior not defined for both args and kwargs")
    obj = None
    if args:
        obj = args[0] if len(args) == 1 else list(args)
    else:
        obj = kwargs
    data = _json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return Response(data=data, status=200, mimetype="application/json")


def make_response(rv):
    status = None
    headers = None
    body = rv

    if isinstance(rv, Response):
        return rv

    if isinstance(rv, tuple):
        if len(rv) == 2:
            body, status = rv
        elif len(rv) == 3:
            body, status, headers = rv
        else:
            raise TypeError("The view function did not return a valid response tuple")

    if isinstance(body, (dict, list)):
        resp = jsonify(body)
    else:
        resp = Response(body)

    if status is not None:
        resp.status_code = Response._parse_status(status)

    if headers:
        resp.headers.update(headers)

    return resp


class HTTPError(Exception):
    def __init__(self, code, description=None):
        super().__init__(description or _status_string(code))
        self.code = code
        self.description = description


def abort(code, description=None):
    raise HTTPError(code, description)


def redirect(location, code=302):
    resp = Response("", status=code)
    resp.headers.set("Location", location)
    return resp


def escape(s):
    return html.escape(s, quote=True)


# -----------------------------
# Flask application
# -----------------------------
class Flask:
    response_class = Response

    def __init__(self, import_name):
        self.import_name = import_name
        self.name = import_name
        self.config = {}
        self.testing = False
        # route map: path -> { METHOD: (view_func, endpoint) }
        self._routes = {}
        self._before_request_funcs = []
        self._after_request_funcs = []

    def add_url_rule(self, rule, endpoint=None, view_func=None, methods=None):
        if view_func is None:
            raise ValueError("view_func is required")
        if methods is None:
            methods = ["GET"]
        methods = [m.upper() for m in methods]
        mapping = self._routes.setdefault(rule, {})
        for m in methods:
            mapping[m] = (view_func, endpoint or getattr(view_func, "__name__", endpoint))
        if "GET" in methods and "HEAD" not in methods:
            mapping["HEAD"] = (view_func, endpoint or getattr(view_func, "__name__", endpoint))

    def route(self, rule, methods=None):
        def decorator(f):
            self.add_url_rule(rule, view_func=f, methods=methods)
            return f

        return decorator

    def before_request(self, f):
        self._before_request_funcs.append(f)
        return f

    def after_request(self, f):
        self._after_request_funcs.append(f)
        return f

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)

    def wsgi_app(self, environ, start_response):
        req = Request(environ)
        g_obj = _G()
        tok_req = _request_var.set(req)
        tok_g = _g_var.set(g_obj)
        try:
            resp = self._handle_request(req)
            if resp.headers.get("Content-Length") is None:
                resp.headers.set("Content-Length", str(len(resp.data)))
            status = resp.status
            headers = resp.headers.to_wsgi_list()
            if req.method == "HEAD":
                start_response(status, headers)
                return []
            start_response(status, headers)
            return [resp.data]
        finally:
            _request_var.reset(tok_req)
            _g_var.reset(tok_g)

    def _handle_request(self, req):
        for bf in self._before_request_funcs:
            rv = bf()
            if rv is not None:
                resp = make_response(rv)
                for af in self._after_request_funcs:
                    maybe = af(resp)
                    resp = maybe if isinstance(maybe, Response) else resp
                return resp

        mapping = self._routes.get(req.path)
        if not mapping:
            resp = Response("Not Found", status=404)
            for af in self._after_request_funcs:
                maybe = af(resp)
                resp = maybe if isinstance(maybe, Response) else resp
            return resp

        allowed = set(mapping.keys())
        effective_allowed = set(allowed)
        if "GET" in allowed:
            effective_allowed.add("HEAD")

        method = req.method
        if method not in effective_allowed:
            resp = Response("Method Not Allowed", status=405)
            resp.headers.set("Allow", ", ".join(sorted(effective_allowed)))
            for af in self._after_request_funcs:
                maybe = af(resp)
                resp = maybe if isinstance(maybe, Response) else resp
            return resp

        try:
            view_info = mapping.get(method)
            if view_info is None:
                view_info = mapping.get("GET")
            view_func = view_info[0]
            rv = view_func()
            resp = make_response(rv)
        except HTTPError as he:
            resp = Response(he.description or _status_string(he.code), status=he.code)
        except Exception:
            resp = Response("Internal Server Error", status=500)

        for af in self._after_request_funcs:
            maybe = af(resp)
            resp = maybe if isinstance(maybe, Response) else resp

        return resp

    def test_client(self):
        app = self

        class Client:
            def __init__(self, app):
                self.app = app

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def open(self, path, method="GET", data=None, headers=None, json=None, query_string=None):
                method = method.upper()
                headers = headers or {}
                body = b""

                if query_string is not None:
                    if isinstance(query_string, dict):
                        qs = urllib.parse.urlencode(query_string, doseq=True)
                    else:
                        qs = str(query_string)
                else:
                    parsed = urllib.parse.urlsplit(path)
                    qs = parsed.query
                    path = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", parsed.fragment))

                if json is not None:
                    body = _json.dumps(json, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
                    headers.setdefault("Content-Type", "application/json")
                elif data is not None:
                    if isinstance(data, (bytes, bytearray)):
                        body = bytes(data)
                    elif isinstance(data, str):
                        body = data.encode("utf-8")
                    elif isinstance(data, dict):
                        body = urllib.parse.urlencode(data, doseq=True).encode("utf-8")
                        headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
                    else:
                        body = _to_bytes(data)

                environ = {
                    "REQUEST_METHOD": method,
                    "PATH_INFO": path or "/",
                    "QUERY_STRING": qs or "",
                    "SERVER_NAME": "localhost",
                    "SERVER_PORT": "80",
                    "wsgi.version": (1, 0),
                    "wsgi.url_scheme": "http",
                    "wsgi.input": io.BytesIO(body),
                    "wsgi.errors": io.StringIO(),
                    "wsgi.multithread": False,
                    "wsgi.multiprocess": False,
                    "wsgi.run_once": False,
                    "SCRIPT_NAME": "",
                    "CONTENT_LENGTH": str(len(body)) if body else "",
                }

                for k, v in headers.items():
                    if k.lower() == "content-type":
                        environ["CONTENT_TYPE"] = v
                    elif k.lower() == "content-length":
                        environ["CONTENT_LENGTH"] = str(v)
                    else:
                        http_key = "HTTP_" + k.upper().replace("-", "_")
                        environ[http_key] = str(v)

                captured = {}

                def start_response(status, response_headers, exc_info=None):
                    captured["status"] = status
                    captured["headers"] = response_headers

                result_iter = self.app.wsgi_app(environ, start_response)
                body_bytes = b"".join(result_iter)

                status_str = captured.get("status", "200 OK")
                status_code = int(status_str.split()[0])
                resp_headers = Headers(captured.get("headers", []))

                resp = Response(
                    data=body_bytes,
                    status=status_code,
                    headers=resp_headers.items(),
                    mimetype=resp_headers.get("Content-Type"),
                    auto_content_length=False,
                )
                return resp

            def get(self, path, **kwargs):
                return self.open(path, method="GET", **kwargs)

            def post(self, path, **kwargs):
                return self.open(path, method="POST", **kwargs)

            def put(self, path, **kwargs):
                return self.open(path, method="PUT", **kwargs)

            def patch(self, path, **kwargs):
                return self.open(path, method="PATCH", **kwargs)

            def delete(self, path, **kwargs):
                return self.open(path, method="DELETE", **kwargs)

            def head(self, path, **kwargs):
                return self.open(path, method="HEAD", **kwargs)

        return Client(app)