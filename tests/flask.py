"""
A very small stub of the 'flask' package to satisfy environments where the real
Flask dependency is unavailable. It provides minimal interfaces commonly used
in simple scripts and unit tests, without implementing a real web framework.
"""

from types import SimpleNamespace
import json as _json
import html as _html
import urllib.parse as _urlparse


__version__ = "0.0"


class Response:
    def __init__(self, data=None, status=200, headers=None, mimetype=None):
        self.data = data if data is not None else b""
        self.status_code = status
        self.headers = {} if headers is None else dict(headers)
        self.mimetype = mimetype

    def get_data(self, as_text=False):
        if isinstance(self.data, bytes):
            return self.data.decode("utf-8") if as_text else self.data
        # Assume str or other object
        text = str(self.data)
        return text if as_text else text.encode("utf-8")

    def set_data(self, data):
        self.data = data

    def get_json(self, silent=False):
        try:
            if isinstance(self.data, (bytes, bytearray)):
                return _json.loads(self.data.decode("utf-8"))
            if isinstance(self.data, str):
                return _json.loads(self.data)
            # Not JSON-encoded
            return self.data
        except Exception:
            if silent:
                return None
            raise


def jsonify(*args, **kwargs):
    if args and kwargs:
        data = {"args": list(args), **kwargs}
    elif kwargs:
        data = kwargs
    elif len(args) == 1:
        data = args[0]
    else:
        data = list(args)
    return Response(_json.dumps(data), status=200, headers={"Content-Type": "application/json"}, mimetype="application/json")


def make_response(data=None, status=200, headers=None):
    return Response(data=data, status=status, headers=headers)


class HTTPException(Exception):
    def __init__(self, code=500, description=None):
        super().__init__(description or f"HTTP {code}")
        self.code = code
        self.description = description


def abort(code=400, description=None):
    raise HTTPException(code=code, description=description)


def redirect(location, code=302):
    return Response("", status=code, headers={"Location": location})


def url_for(endpoint, **values):
    base = f"/{endpoint.lstrip('/')}"
    if values:
        qs = _urlparse.urlencode(values)
        return f"{base}?{qs}" if qs else base
    return base


def render_template(template_string, **context):
    try:
        return template_string.format(**context)
    except Exception:
        return template_string


def escape(s):
    return _html.escape(str(s), quote=True)


class Request:
    def __init__(self):
        self.args = {}
        self.form = {}
        self.json = None
        self.method = "GET"
        self.path = "/"

    def get_json(self, silent=False):
        try:
            return self.json
        except Exception:
            if silent:
                return None
            raise


# Simple global placeholders to satisfy imports.
request = Request()
g = SimpleNamespace()
current_app = None


class Blueprint:
    def __init__(self, name, import_name):
        self.name = name
        self.import_name = import_name
        self._routes = {}

    def route(self, rule, methods=None, **options):
        def decorator(f):
            self._routes[rule] = f
            return f
        return decorator


class Flask:
    def __init__(self, import_name):
        self.import_name = import_name
        self._routes = {}
        self.blueprints = {}
        self.config = {}

    def route(self, rule, methods=None, **options):
        def decorator(f):
            self._routes[rule] = f
            return f
        return decorator

    def register_blueprint(self, blueprint, url_prefix=""):
        self.blueprints[blueprint.name] = (blueprint, url_prefix)

    def run(self, *args, **kwargs):
        # No-op for stub
        pass

    def test_client(self):
        return _TestClient(self)


class _TestClient:
    def __init__(self, app: Flask):
        self.app = app

    def _find_view(self, path):
        # Exact match first
        if path in self.app._routes:
            return self.app._routes[path]
        # Check blueprints with url_prefix
        for bp, prefix in self.app.blueprints.values():
            full = f"{prefix.rstrip('/')}/{path.lstrip('/')}" if prefix else path
            if full in bp._routes:
                return bp._routes[full]
            if path in bp._routes:
                return bp._routes[path]
        return None

    def get(self, path, query_string=None, headers=None):
        request.method = "GET"
        request.path = path
        request.args = query_string or {}
        view = self._find_view(path)
        if view is None:
            return Response("Not Found", status=404)
        result = view()
        return _coerce_to_response(result)

    def post(self, path, data=None, json=None, headers=None):
        request.method = "POST"
        request.path = path
        request.form = data or {}
        request.json = json
        view = self._find_view(path)
        if view is None:
            return Response("Not Found", status=404)
        result = view()
        return _coerce_to_response(result)


def _coerce_to_response(result):
    if isinstance(result, Response):
        return result
    if isinstance(result, tuple):
        # (data, status) or (data, status, headers)
        if len(result) == 2:
            data, status = result
            return make_response(data, status=status)
        if len(result) == 3:
            data, status, headers = result
            return make_response(data, status=status, headers=headers)
    return make_response(result)


class _JsonModule:
    dumps = staticmethod(_json.dumps)
    loads = staticmethod(_json.loads)


# Provide a 'json' attribute like flask.json
json = _JsonModule()