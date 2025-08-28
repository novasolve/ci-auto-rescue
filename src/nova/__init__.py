import importlib.metadata
from pathlib import Path

try:
    __version__ = importlib.metadata.version('nova-ci-rescue')
except importlib.metadata.PackageNotFoundError:
    # Fallback for development - try to read from pyproject.toml
    try:
        try:
            # Python 3.11+
            import tomllib
        except ImportError:
            # Python < 3.11
            import tomli as tomllib
        
        root = Path(__file__).parent.parent.parent
        with open(root / 'pyproject.toml', 'rb') as f:
            pyproject = tomllib.load(f)
            __version__ = pyproject['project']['version']
    except:
        # If all else fails, use a default
        __version__ = '0.4.2'