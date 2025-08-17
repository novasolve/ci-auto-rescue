# Nova Safe Patching System - Demo Guide

## Quick Start

The Safe Patching system provides multi-layer safety validation for patches before they are applied.

### 1. Review a Patch

Review a patch without applying it:

```bash
python -m nova.cli_safe_patch review my_fix.patch
```

### 2. Apply a Patch

Apply a patch with full safety checks:

```bash
python -m nova.cli_safe_patch apply my_fix.patch --context failing_tests.txt
```

### 3. Check Status

View rollback history:

```bash
python -m nova.cli_safe_patch status
```

### 4. Rollback Changes

Rollback the last applied patch:

```bash
python -m nova.cli_safe_patch rollback
```

## Safety Features

The system protects against:

1. **Large patches**: Patches exceeding 500 lines or 10 files are rejected
2. **Test modifications**: Test files cannot be modified
3. **Config changes**: CI/CD and configuration files are protected
4. **Dangerous code**: Patterns like `exec()`, `eval()`, `os.system` are blocked
5. **Duplicate definitions**: Adding functions without removing originals is prevented

## Example Output

### Successful Review
```
1. Safety Analysis:
   ✅ No safety violations detected

2. Critic Review:
   ✅ APPROVED: Patch looks good and addresses the issues

3. Patch Statistics:
   • Lines added: 4
   • Lines removed: 1
   • Files affected: 1
```

### Safety Violation
```
1. Safety Analysis:
   ❌ Safety violations found:
      • Contains dangerous code pattern: exec(
      • Attempts to modify restricted files: tests/test_example.py

2. Critic Review:
   ❌ REJECTED: Safety violations detected
```

## Integration

To use the safe patching system in your code:

```python
from nova.engine.safe_patching import PatchSafetyGuard, ApplyPatchTool

# Validate a patch
guard = PatchSafetyGuard()
is_safe, violations = guard.validate_patch(patch_text)

# Apply if safe
if is_safe:
    applier = ApplyPatchTool()
    success, message = applier.apply_patch(patch_text)
```

## Configuration

Safety limits can be configured via environment variables:
- `NOVA_MAX_LINES_CHANGED`: Maximum lines changed (default: 500)
- `NOVA_MAX_FILES_MODIFIED`: Maximum files modified (default: 10)
- `NOVA_DENIED_PATHS`: Additional comma-separated paths to deny
