# 🔧 Nova CI-Rescue - Proposed Fixes Summary

## Quick Fix Commands

### Option 1: Automatic Fix (Recommended)

```bash
# Review what will be changed (dry run)
python apply_proposed_fixes.py --dry-run

# Apply all fixes
python apply_proposed_fixes.py

# Verify fixes worked
python verify_installation.py
nova version
```

### Option 2: Manual Quick Fixes

```bash
# Fix 1: Import error
sed -i '' 's/NovaConfig/CLIConfig/g' verify_installation.py

# Fix 2: Add version
echo '__version__ = "0.1.1-alpha"' >> src/nova/__init__.py

# Fix 3: Test
nova version
```

## Critical Fixes (Must Do)

| Issue                | Current State                        | Proposed Fix                        | File                     |
| -------------------- | ------------------------------------ | ----------------------------------- | ------------------------ |
| Import Error         | `from nova.config import NovaConfig` | `from nova.config import CLIConfig` | verify_installation.py   |
| Missing Version      | No `__version__`                     | Add `__version__ = "0.1.1-alpha"`   | src/nova/\_\_init\_\_.py |
| No --version Command | Command not found                    | Add `@app.command() def version()`  | src/nova/cli.py          |
| Version Confusion    | Mix of v1.0, v0.1.1                  | Standardize to v0.1.1-alpha         | README.md, docs/\*.md    |

## High Priority Fixes

| Issue                 | Impact           | Solution                                           |
| --------------------- | ---------------- | -------------------------------------------------- |
| No API Key Error Help | Users confused   | Add detailed error message with setup instructions |
| No Rollback Docs      | Users can't undo | Create docs/rollback-guide.md                      |
| Inconsistent Timeouts | Confusion        | Standardize: 300/600/1200/1800 seconds             |
| No Troubleshooting    | Users stuck      | Create docs/troubleshooting-guide.md               |

## Files That Will Be Modified

```
✏️ verify_installation.py      - Fix import
✏️ src/nova/__init__.py        - Add version
✏️ src/nova/cli.py             - Add version command
✏️ src/nova/config.py          - Add timeout constants
✏️ README.md                   - Standardize versions
✏️ docs/01-happy-path-one-pager.md - Update versions
✏️ pyproject.toml              - Version to 0.1.1-alpha
📝 docs/troubleshooting-guide.md - NEW FILE
📝 docs/rollback-guide.md      - NEW FILE
```

## Testing After Fixes

```bash
# 1. Verify installation works
python verify_installation.py
# Expected: All tests pass

# 2. Check version command
nova version
# Expected: nova-ci-rescue v0.1.1-alpha

# 3. Test with demo
cd demo-repo
pytest  # Should fail
nova fix . --timeout 300
pytest  # Should pass

# 4. Check safety limits
python -m pytest tests/test_safety_limits.py
```

## Impact Assessment

### Before Fixes

- ❌ Installation verification fails
- ❌ Version command doesn't work
- ❌ Confusing version numbers
- ❌ Poor error messages
- ❌ No rollback documentation

### After Fixes

- ✅ Clean installation verification
- ✅ Working version command
- ✅ Consistent v0.1.1-alpha everywhere
- ✅ Helpful error messages with solutions
- ✅ Complete rollback & troubleshooting guides
- ✅ Standardized timeout configuration

## Time Estimate

- **Automatic application**: 30 seconds (run script)
- **Manual application**: 10-15 minutes
- **Testing & verification**: 5 minutes
- **Total**: ~15-20 minutes

## Risk Assessment

**Risk Level: LOW** ✅

All proposed fixes are:

- Non-breaking (backward compatible)
- Additive (mostly adding missing features)
- Well-tested (script includes validation)
- Reversible (git reset if needed)

## Rollback Plan

If anything goes wrong:

```bash
# Check what changed
git status
git diff

# Undo all changes
git reset --hard HEAD
git clean -fd
```

## Next Steps After Fixes

1. **Immediate**: Run test suite
2. **Short-term**: Update changelog
3. **Medium-term**: Tag release v0.1.1-alpha
4. **Long-term**: Plan v0.2.0 features

---

**Ready to apply?** Run: `python apply_proposed_fixes.py`
