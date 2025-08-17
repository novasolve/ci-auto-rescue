# Test Patches for Nova Safe Patching System

This directory contains test patches to validate the Safe Patching system's various safety checks.

## Test Cases

### ✅ Safe Patches (Should Pass)

1. **`01_safe_patch.diff`** - A safe patch that adds error handling
   - Small change (< 500 lines)
   - Single file modification
   - No dangerous patterns
   - Use with: `context_divide_by_zero.txt`

### ❌ Dangerous Code Patterns (Should Fail)

2. **`02_dangerous_exec.diff`** - Contains `exec()` call
3. **`03_dangerous_eval.diff`** - Contains `eval()` call
4. **`04_dangerous_os_system.diff`** - Contains `os.system()` call

### ❌ Forbidden File Modifications (Should Fail)

5. **`05_modify_tests.diff`** - Attempts to modify test files
6. **`06_modify_config.diff`** - Attempts to modify CI/CD configuration
7. **`07_modify_pyproject.diff`** - Attempts to modify pyproject.toml

### ❌ Code Quality Issues (Should Fail)

8. **`08_duplicate_function.diff`** - Adds duplicate function definition
9. **`09_exceeds_size_limit.diff`** - Exceeds 500 line change limit
10. **`10_too_many_files.diff`** - Modifies more than 10 files

## Usage Examples

### Review a safe patch:

```bash
python -m nova.cli_safe_patch review test_patches/01_safe_patch.diff --context test_patches/context_divide_by_zero.txt
```

### Test dangerous code detection:

```bash
python -m nova.cli_safe_patch review test_patches/02_dangerous_exec.diff
python -m nova.cli_safe_patch review test_patches/03_dangerous_eval.diff
```

### Test file restriction:

```bash
python -m nova.cli_safe_patch review test_patches/05_modify_tests.diff
python -m nova.cli_safe_patch review test_patches/06_modify_config.diff
```

### Test size limits:

```bash
python -m nova.cli_safe_patch review test_patches/09_exceeds_size_limit.diff
python -m nova.cli_safe_patch review test_patches/10_too_many_files.diff
```

## Expected Results

- Patch 01 should **PASS** all safety checks
- Patches 02-10 should **FAIL** with specific safety violations

## Testing the Full Workflow

1. First, review patches to see what passes/fails:

   ```bash
   for patch in test_patches/*.diff; do
       echo "Testing: $patch"
       python -m nova.cli_safe_patch review "$patch"
       echo "---"
   done
   ```

2. Apply the safe patch:

   ```bash
   python -m nova.cli_safe_patch apply test_patches/01_safe_patch.diff --context test_patches/context_divide_by_zero.txt
   ```

3. Check rollback status:

   ```bash
   python -m nova.cli_safe_patch status
   ```

4. Rollback if needed:
   ```bash
   python -m nova.cli_safe_patch rollback
   ```
