# Implementation Comparison: Current Nova CI-Rescue vs Proposed Improvements

This document provides a comprehensive comparison between the existing Nova CI-Rescue implementation and the proposed improvements to address patch application issues and "no progress" cycles.

## Executive Summary

The proposed implementation offers significant improvements in:

1. **Source Resolution**: More robust source file discovery and mapping from tests
2. **Patch Guards**: Better duplicate function detection and test edit policies
3. **Patch Application**: Smarter fallback strategies with fuzzy matching
4. **Post-Apply Validation**: AST syntax checking to catch errors immediately
5. **Path Handling**: Auto-recovery from common path mismatches

## 1. Source Resolution

### Current Implementation (`src/nova/agent/llm_agent.py`)

**Approach**: Basic import parsing with manual path discovery

- Uses regex to extract imports from test files
- Maintains a hardcoded skip list of standard library modules
- Falls back to searching common directories (`src/`, `lib/`, `app/`)
- Limited pyproject.toml parsing

**Limitations**:

- Can miss imports with complex module structures
- No support for namespace packages
- Limited understanding of project structure
- May include irrelevant source files

```python
# Current approach
def find_source_files_from_test(self, test_file_path: Path) -> Set[str]:
    # Simple regex parsing
    import_pattern = r'^\s*(?:from\s+([\w\.]+)\s+import|import\s+([\w\.]+))'
    # Manual skip list
    skip_modules = {'pytest', 'unittest', 'sys', 'os', ...}
```

### Proposed Implementation (`src/nova/engine/source_resolver.py`)

**Approach**: Dedicated `SourceResolver` class with intelligent root discovery

- Discovers source roots from pyproject.toml configuration
- Handles both file and package forms of imports
- Uses tomllib for proper TOML parsing
- Supports multiple source roots

**Improvements**:

- ✅ Automatic source root discovery (respects `src/` layout)
- ✅ Better import resolution with package support
- ✅ No hardcoded module lists
- ✅ Handles relative imports properly

```python
# Proposed approach
class SourceResolver:
    def _discover_roots(self) -> List[Path]:
        # Intelligent root discovery from pyproject.toml
        # Supports setuptools package-dir configuration
        # Falls back to conventional src/ layout
```

## 2. Patch Guards and Validation

### Current Implementation (`src/nova/tools/safety_limits.py`)

**Approach**: Basic duplicate function detection

- Checks if `+def function_name` appears without corresponding `-def`
- Limited to exact string matching
- No handling of comment differences

**Limitations**:

- Can't detect duplicates when comments differ
- No policy enforcement for test modifications
- Simple regex-based detection

```python
# Current validation
if re.match(r'\+\s*def\s+(\w+)\s*\(', line):
    # Check for corresponding removal
    has_removal = any(
        re.match(rf'-\s*def\s+{re.escape(func_name)}\s*\(', l)
        for l in lines
    )
```

### Proposed Implementation (`src/nova/engine/patch_guard.py`)

**Approach**: Comprehensive preflight checks with policy enforcement

- Per-file tracking of added/removed definitions
- Explicit test modification policy
- Better duplicate detection logic

**Improvements**:

- ✅ Tracks definitions per file accurately
- ✅ Enforces "no test edits" policy (configurable)
- ✅ Returns actionable error messages
- ✅ Prevents the exact duplicate function bug

```python
# Proposed validation
def preflight_patch_checks(patch_text: str, *,
                          forbid_test_edits: bool = True) -> Tuple[bool, List[str]]:
    # Per-file tracking
    per_file_added = {}
    per_file_removed = {}
    # Policy enforcement
    if forbid_test_edits and any(p.startswith("tests/") for p in files_touched):
        issues.append("Patch attempts to modify tests/")
```

## 3. Patch Application

### Current Implementation (`src/nova/tools/fs.py` + `patch_fixer.py`)

**Approach**: Git apply with basic fallback

- Uses `git apply` as primary method
- Falls back to `unidiff` library for Python-based application
- Limited path adjustment (only checks `src/` prefix)
- Simple line-by-line reconstruction for truncated patches

**Limitations**:

- Fallback can leave duplicate lines when context doesn't match
- Limited fuzzy matching capability
- No handling of comment differences
- Can't recover from common path issues

```python
# Current fallback (simplified)
def apply_unified_diff(repo_root: Path, diff_text: str) -> List[Path]:
    # Uses unidiff library
    # Limited context matching
    # Can duplicate lines if context doesn't match exactly
```

### Proposed Implementation (`src/nova/engine/patch_applier.py` + enhanced `patch_fixer.py`)

**Approach**: Smart fallback with multiple recovery strategies

- Path prefix stripping (handles `demo-failing-tests/` prefix)
- Automatic `src/` insertion for missing files
- Fuzzy matching that ignores comment differences
- Reconstructs patches using actual file content

**Improvements**:

- ✅ **Fuzzy Matching**: Ignores inline comment differences
- ✅ **Path Recovery**: Auto-fixes common path issues
- ✅ **Smart Reconstruction**: Rebuilds patch with correct context
- ✅ **No Duplicates**: Ensures lines are replaced, not just added

```python
# Proposed fuzzy matching
def strip_comment(s: str) -> str:
    # Compare code ignoring comments
    return s.split('#')[0].rstrip() if '#' in s else s

# Smart path fallback
def _strip_common_prefix_from_paths(patch_text: str, prefix: str) -> str:
    candidates = {prefix, "demo-failing-tests"}  # Known prefixes
    # Auto-strip problematic prefixes
```

## 4. Post-Apply Validation

### Current Implementation

**Approach**: No syntax validation after patch application

- Relies on test execution to catch syntax errors
- No immediate feedback on broken code

**Limitations**:

- Syntax errors only discovered during test run
- Wasted compute on obviously broken patches
- No early termination for syntax issues

### Proposed Implementation (`src/nova/engine/post_apply_check.py`)

**Approach**: AST-based syntax validation

- Parses all changed Python files
- Immediate syntax error detection
- Detailed error reporting with line numbers

**Improvements**:

- ✅ **Immediate Feedback**: Catch syntax errors before running tests
- ✅ **Detailed Errors**: Shows exact line and error message
- ✅ **Rollback Support**: Can revert bad patches immediately

```python
def ast_sanity_check(paths: Iterable[Path]) -> Tuple[bool, List[str]]:
    for p in paths:
        try:
            ast.parse(p.read_text(encoding="utf-8"))
        except SyntaxError as e:
            issues.append(f"{p}: SyntaxError at line {e.lineno}: {e.msg}")
```

## 5. Integration Points

### Current Implementation

The current `llm_agent.py` has these integration points:

1. Source discovery in `generate_patch()`
2. Duplicate check in `review_patch()`
3. Patch application via `apply_and_commit_patch()`

### Proposed Implementation

Enhanced integration with better separation of concerns:

1. **Source Resolution**: Use `SourceResolver` before building prompts
2. **Preflight Checks**: Validate patch before any application attempt
3. **Smart Application**: Use `apply_patch_with_fallback()` with recovery
4. **Post-Apply Validation**: Check syntax before running tests
5. **No-Progress Detection**: Explicit path mismatch detection

```python
# Proposed integration flow
def fix_failures(repo_root: Path, failing_tests: List[dict], ...):
    # 1. Resolve sources properly
    resolver = SourceResolver(repo_root)
    candidate_sources = resolver.map_imports_from_tests(test_paths)

    # 2. Generate patch with correct context
    patch_text = llm.complete(...)

    # 3. Preflight validation
    ok, issues = preflight_patch_checks(patch_text)
    if not ok:
        return _reject_and_replan(issues)

    # 4. Apply with smart fallbacks
    changed = apply_patch_with_fallback(patch_text, repo_root)

    # 5. Post-apply syntax check
    ok, issues = ast_sanity_check(changed)
    if not ok:
        _git_reset_hard(repo_root)
        return _reject_and_replan(issues)
```

## Key Benefits of Proposed Implementation

### 1. **Prevents Duplicate Functions Bug**

- The exact issue in your example (duplicate `add`, `subtract`, etc.) would be caught by preflight checks
- Fuzzy matching ensures the original lines are properly removed

### 2. **Handles Path Mismatches**

- Auto-strips `demo-failing-tests/` prefix
- Auto-inserts `src/` when needed
- Recovers from common LLM path mistakes

### 3. **Better Context for LLM**

- Only includes relevant source files (via import analysis)
- Reduces token usage and improves patch quality

### 4. **Immediate Error Detection**

- Syntax errors caught before test execution
- Duplicate definitions blocked before application
- Clear error messages for debugging

### 5. **No-Progress Detection**

- Explicitly detects when patches target wrong files
- Provides actionable feedback to the planner

## Migration Path

To adopt the proposed implementation:

1. **Phase 1**: Add new modules without changing existing code

   - Add `source_resolver.py`, `patch_guard.py`, `patch_applier.py`, `post_apply_check.py`
   - Test independently

2. **Phase 2**: Integrate preflight and post-apply checks

   - Add checks to existing flow
   - Monitor rejection rates

3. **Phase 3**: Replace patch application logic

   - Switch to `apply_patch_with_fallback()`
   - Enable fuzzy matching

4. **Phase 4**: Full integration
   - Use `SourceResolver` for all source discovery
   - Remove old fallback code

## Metrics to Track

The proposed implementation suggests tracking:

- % patches rejected at preflight (duplicate defs, test edits)
- % patches requiring path fallback
- % syntax rejections post-apply
- Average failing tests reduced per iteration

These metrics will help identify remaining issues and validate improvements.

## Conclusion

The proposed implementation addresses the root causes of the "no progress" issue:

1. **Wrong file targeting**: Fixed by better source resolution
2. **Duplicate functions**: Prevented by preflight checks and fuzzy matching
3. **Context mismatches**: Handled by smart reconstruction
4. **Silent syntax errors**: Caught by AST validation

These improvements would prevent the exact scenario shown in the example, where the agent got stuck applying patches that didn't reduce failing tests due to duplicate function definitions.
