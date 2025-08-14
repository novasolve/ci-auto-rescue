# In src/nova/tools/safety_limits.py, replace the _is_denied_path method with:

def _is_denied_path(self, file_path: str) -> bool:
    """
    Check if a file path matches any denied patterns.
    
    Args:
        file_path: Path to check.
        
    Returns:
        True if the path is denied, False otherwise.
    """
    # Normalize the path
    path = Path(file_path).as_posix()
    
    # SPECIAL EXCEPTION: Allow our own workflow file
    if path == '.github/workflows/nova.yml':
        if self.verbose:
            print(f"[SafetyLimits] Allowing modification to nova.yml (own workflow)")
        return False
    
    # Check glob patterns
    for pattern in self.config.denied_paths:
        # Convert glob pattern to work with pathlib
        if self._matches_glob(path, pattern):
            if self.verbose:
                print(f"[SafetyLimits] File '{path}' matches denied pattern '{pattern}'")
            return True
    
    # Check regex patterns
    for regex_pattern in self.denied_patterns:
        if regex_pattern.match(path):
            if self.verbose:
                print(f"[SafetyLimits] File '{path}' matches denied regex pattern")
            return True
    
    return False
