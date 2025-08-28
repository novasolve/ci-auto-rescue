import importlib.metadata
import sys
from pathlib import Path

try:
    __version__ = importlib.metadata.version("nova-ci-rescue")
except importlib.metadata.PackageNotFoundError:
    # Fallback for development - try to read from pyproject.toml
    try:
        if sys.version_info >= (3, 11):
            import tomllib
        else:
            import tomli as tomllib

        root = Path(__file__).parent.parent.parent
        with open(root / "pyproject.toml", "rb") as f:
            pyproject = tomllib.load(f)
            __version__ = pyproject["project"]["version"]
    except Exception:
        # If all else fails, use a default
        __version__ = "0.4.2"