# Release Notes: v0.1.1-alpha

## 🐛 Bug Fix Release

**Release Date**: January 14, 2025  
**Type**: Patch Release

## Summary

This patch release fixes a critical bug in the test runner that could cause Nova CI-Rescue to incorrectly detect test failures.

## What's Fixed

### Test Runner JUnit Report Path Bug
- **Issue**: Missing f-string formatting in `test_runner.py` caused JUnit report path to be incorrectly formatted as literal `{junit_report_path}` instead of using a proper temporary file path
- **Impact**: Nova could read stale test reports from previous runs, leading to false failure detections
- **Fix**: Added proper f-string formatting to ensure JUnit reports are correctly saved to temporary files

## Technical Details

The bug was in `src/nova/runner/test_runner.py` line 68:
```python
# Before (incorrect):
"--junit-xml={junit_report_path}",

# After (fixed):
f"--junit-xml={junit_report_path}",
```

## Verification

The fix has been tested and verified:
- Nova now correctly identifies and fixes failing tests
- No more false positives from stale test reports
- Clean test runs with proper temporary file management

## Installation

Update to the latest version:
```bash
pip install --upgrade nova-ci-rescue
```

Or install from source:
```bash
git clone https://github.com/novasolve/ci-auto-rescue.git
cd ci-auto-rescue
git checkout v0.1.1-alpha
pip install -e .
```

## Compatibility

This release is fully compatible with v0.1.0-alpha configurations and does not introduce any breaking changes.

## Next Steps

Development continues on Milestone B features for v0.2.0, including:
- Enhanced telemetry system
- Quiet pytest defaults for CI environments
- Improved package distribution

## Support

For issues or questions, please open an issue on [GitHub](https://github.com/novasolve/ci-auto-rescue/issues).

---

**Full Changelog**: [v0.1.0-alpha...v0.1.1-alpha](https://github.com/novasolve/ci-auto-rescue/compare/v0.1.0-alpha...v0.1.1-alpha)
