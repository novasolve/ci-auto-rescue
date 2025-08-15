"""
Source file resolution for Nova CI-Rescue.
Discovers source roots and maps test imports to actual source files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Optional, Set, Tuple
import re

try:
    import tomllib  # Python >= 3.11
except ImportError:
    tomllib = None
    try:
        import tomli as tomllib  # fallback for older Pythons
    except ImportError:
        pass


_IMPORT_RE = re.compile(r'^\s*(from\s+([a-zA-Z0-9_\.]+)\s+import|import\s+([a-zA-Z0-9_\.]+))')
_TOP_LEVEL_NAME_RE = re.compile(r'^([a-zA-Z0-9_]+)')


class SourceResolver:
    """
    Discovers source roots (e.g., src/) and maps test imports to actual source files.
    """

    def __init__(self, repo_root: Path):
        self.repo_root = Path(repo_root).resolve()
        self._roots = self._discover_roots()

    # --- public API ---

    def roots(self) -> List[Path]:
        """Get discovered source roots."""
        return list(self._roots)

    def map_imports_from_tests(self, test_files: Iterable[Path]) -> Set[Path]:
        """
        Given test files, read import lines and map to candidate source paths.
        
        Args:
            test_files: Iterable of test file paths
            
        Returns:
            Set of resolved source file paths
        """
        candidates: Set[Path] = set()
        for tf in test_files:
            try:
                text = Path(tf).read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for mod in _extract_import_modules(text):
                for p in self._locate_module_file(mod):
                    candidates.add(p)
        return candidates

    def locate_module_file(self, module: str) -> Optional[Path]:
        """
        Convenience: return first match for a module, if any.
        
        Args:
            module: Module name like 'calculator' or 'package.module'
            
        Returns:
            Path to the module file or None if not found
        """
        for p in self._locate_module_file(module):
            return p
        return None

    # --- internals ---

    def _discover_roots(self) -> List[Path]:
        """
        Discover source roots using heuristics:
        1) If pyproject.toml defines a package_dir or similar → honor it
        2) If repo contains a top-level 'src' directory → include it
        3) Fallback to repo root
        
        Returns:
            List of discovered root paths
        """
        roots: List[Path] = []

        # Check pyproject.toml for package configuration
        pyproject = self.repo_root / "pyproject.toml"
        if pyproject.exists() and tomllib is not None:
            try:
                data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
                # Check for setuptools package-dir configuration
                pkg_dir = (
                    data.get("tool", {})
                        .get("setuptools", {})
                        .get("package-dir", {})
                        .get("", None)
                )
                if isinstance(pkg_dir, str):
                    p = (self.repo_root / pkg_dir).resolve()
                    if p.exists():
                        roots.append(p)
                
                # Check for poetry source configuration
                poetry_packages = data.get("tool", {}).get("poetry", {}).get("packages", [])
                for pkg in poetry_packages:
                    if isinstance(pkg, dict) and "from" in pkg:
                        p = (self.repo_root / pkg["from"]).resolve()
                        if p.exists():
                            roots.append(p)
            except Exception:
                pass

        # Check for conventional src/ directory
        p_src = (self.repo_root / "src").resolve()
        if p_src.exists() and p_src.is_dir():
            roots.append(p_src)

        # Always include repo root as fallback
        roots.append(self.repo_root)

        # De-duplicate while preserving order
        seen = set()
        out = []
        for r in roots:
            if r not in seen:
                seen.add(r)
                out.append(r)
        return out

    def _locate_module_file(self, module: str) -> Iterable[Path]:
        """
        Map 'calculator' or 'package.module' to file paths across discovered roots.
        
        Args:
            module: Module name
            
        Yields:
            Paths to potential module files
        """
        mod_path_py, mod_pkg_init = self._module_to_relpaths(module)
        for root in self._roots:
            # Try module.py
            cand1 = (root / mod_path_py).resolve()
            if cand1.exists() and cand1.is_file():
                yield cand1
            # Try module/__init__.py
            cand2 = (root / mod_pkg_init).resolve()
            if cand2.exists() and cand2.is_file():
                yield cand2

    @staticmethod
    def _module_to_relpaths(module: str) -> Tuple[Path, Path]:
        """
        Convert module name to relative paths.
        
        Args:
            module: Module name like 'calculator' or 'package.submodule'
            
        Returns:
            Tuple of (module.py path, module/__init__.py path)
        """
        parts = module.split(".")
        py = Path(*parts).with_suffix(".py")
        pkg_init = Path(*parts) / "__init__.py"
        return py, pkg_init


def _extract_import_modules(text: str) -> List[str]:
    """
    Extract imported module names from file text.
    
    Examples:
        'from calculator import add' -> 'calculator'
        'import calculator' -> 'calculator'
        'import package.module' -> 'package.module'
        'from package.submodule import func' -> 'package.submodule'
    
    Args:
        text: Python source code text
        
    Returns:
        List of module names found in imports
    """
    mods: List[str] = []
    for line in text.splitlines():
        m = _IMPORT_RE.match(line)
        if not m:
            continue
        # Extract module from either 'from X import' or 'import X'
        pkg = m.group(2) or m.group(3)
        if not pkg:
            continue
        
        # Skip obvious standard library modules
        if pkg in {'sys', 'os', 'json', 're', 'io', 'typing', 'pathlib', 
                   'datetime', 'time', 'math', 'random', 'collections',
                   'pytest', 'unittest', 'numpy', 'pandas'}:
            continue
            
        # Keep the full module path for proper resolution
        mods.append(pkg)
    
    return mods
