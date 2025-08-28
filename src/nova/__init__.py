import importlib.metadata
import sys
from pathlib import Path

try:
    # Preferred: use installed package metadata
    __version__ = importlib.metadata.version("nova-ci-rescue")
except importlib.metadata.PackageNotFoundError:
    # Dev fallback: read version from pyproject.toml
    try:
        if sys.version_info >= (3, 11):
            import tomllib  # stdlib in 3.11+
        else:
            import tomli as tomllib  # backport for 3.10

        # Resolve repo root (…/src/nova/__init__.py -> repo/)
        root = Path(__file__).resolve().parents[2]

        with open(root / "pyproject.toml", "rb") as f:
            pyproject = tomllib.load(f)
        __version__ = pyproject.get("project", {}).get("version", "0.4.2")
    except Exception:
        # Last resort default (keep in sync with your latest tag)
        __version__ = "0.4.2"
