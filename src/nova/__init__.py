import importlib.metadata
import sys
from pathlib import Path

try:
    # Preferred: installed package metadata
    __version__ = importlib.metadata.version("nova-ci-rescue")
except importlib.metadata.PackageNotFoundError:
    # Dev fallback: read version from pyproject.toml
    try:
        if sys.version_info >= (3, 11):
            import tomllib  # stdlib
        else:
            import tomli as tomllib  # backport

        root = Path(__file__).resolve().parents[2]  # repo root
        with open(root / "pyproject.toml", "rb") as f:
            pyproject = tomllib.load(f)
            __version__ = pyproject["project"]["version"]
    except Exception:
        # Last resort default (keep in sync with your latest tag)
        __version__ = "0.4.2"
