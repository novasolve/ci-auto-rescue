#!/usr/bin/env python3
"""
Apply all proposed fixes for Nova CI-Rescue Happy Path issues.
This script implements the fixes detailed in docs/proposed-fixes-implementation.md
"""

import os
import sys
import re
from pathlib import Path
from typing import Tuple, List

class NovaFixer:
    """Applies fixes to Nova CI-Rescue codebase."""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.fixes_applied = []
        self.fixes_failed = []
        
    def log(self, message: str, level: str = "info"):
        """Log messages with color coding."""
        colors = {
            "info": "\033[0m",     # Default
            "success": "\033[92m",  # Green
            "warning": "\033[93m",  # Yellow
            "error": "\033[91m",    # Red
            "fix": "\033[94m"       # Blue
        }
        prefix = {
            "info": "ℹ️ ",
            "success": "✅",
            "warning": "⚠️ ",
            "error": "❌",
            "fix": "🔧"
        }
        color = colors.get(level, "\033[0m")
        icon = prefix.get(level, "")
        print(f"{color}{icon} {message}\033[0m")
    
    def fix_import_error(self) -> bool:
        """Fix 1: Fix NovaConfig import in verify_installation.py"""
        self.log("Fixing import error in verify_installation.py", "fix")
        
        file_path = Path("verify_installation.py")
        if not file_path.exists():
            self.log(f"File not found: {file_path}", "error")
            return False
        
        content = file_path.read_text()
        original = content
        
        # Fix the specific import line
        content = content.replace(
            '"from nova.config import NovaConfig",',
            '"from nova.config import CLIConfig",',
        )
        
        # Also update the test to use CLIConfig correctly
        content = content.replace(
            '"from nova.config import NovaConfig"',
            '"from nova.config import CLIConfig, NovaSettings"'
        )
        
        if content != original:
            if not self.dry_run:
                file_path.write_text(content)
            self.log("Fixed import statements", "success")
            self.fixes_applied.append("Import error fix")
            return True
        else:
            self.log("No changes needed for imports", "info")
            return False
    
    def add_version_file(self) -> bool:
        """Fix 2: Ensure __version__ is defined."""
        self.log("Adding version to __init__.py", "fix")
        
        init_path = Path("src/nova/__init__.py")
        if not init_path.exists():
            self.log(f"File not found: {init_path}", "error")
            return False
        
        content = init_path.read_text()
        
        # Check if version already exists
        if "__version__" in content:
            self.log("Version already defined", "info")
            return False
        
        # Add version at the top of the file
        version_line = '__version__ = "0.1.1-alpha"\n\n'
        content = version_line + content
        
        if not self.dry_run:
            init_path.write_text(content)
        self.log("Added version definition", "success")
        self.fixes_applied.append("Version definition")
        return True
    
    def add_version_command(self) -> bool:
        """Fix 3: Add version command to CLI."""
        self.log("Adding version command to CLI", "fix")
        
        cli_path = Path("src/nova/cli.py")
        if not cli_path.exists():
            self.log(f"File not found: {cli_path}", "error")
            return False
        
        content = cli_path.read_text()
        
        # Check if version command already exists
        if "def version():" in content:
            self.log("Version command already exists", "info")
            return False
        
        # Find the last command or the main block
        version_command = '''
@app.command()
def version():
    """Display Nova CI-Rescue version information."""
    try:
        from nova import __version__
        version_str = __version__
    except ImportError:
        version_str = "0.1.1-alpha"
    
    console.print(f"[bold cyan]Nova CI-Rescue[/bold cyan] v{version_str}")
    console.print("Copyright (c) 2025 NovaSolve")
    console.print("License: Proprietary")
    
    # Show environment info for debugging
    import sys
    import platform
    console.print(f"\\n[dim]Python: {sys.version.split()[0]}[/dim]")
    console.print(f"[dim]Platform: {platform.platform()}[/dim]")
    
    # Show configuration path
    from pathlib import Path
    config_paths = [
        Path.cwd() / ".nova-config.yaml",
        Path.home() / ".nova" / "config.yaml",
        Path.cwd() / ".env"
    ]
    for config_path in config_paths:
        if config_path.exists():
            console.print(f"[dim]Config: {config_path}[/dim]")
            break


'''
        
        # Find where to insert (before main block)
        main_pattern = r'if __name__ == "__main__":'
        if main_pattern in content:
            content = content.replace(
                'if __name__ == "__main__":',
                version_command + 'if __name__ == "__main__":'
            )
            if not self.dry_run:
                cli_path.write_text(content)
            self.log("Added version command", "success")
            self.fixes_applied.append("Version command")
            return True
        else:
            self.log("Could not find insertion point for version command", "error")
            return False
    
    def standardize_versions(self) -> bool:
        """Fix 4: Standardize version numbers across documentation."""
        self.log("Standardizing version numbers in documentation", "fix")
        
        changes_made = False
        
        # Files to update with version replacements
        updates = [
            ("README.md", [
                ("**v1.0 - Happy Path Edition**", "**v0.1.1-alpha - Happy Path MVP**"),
                ("## ⚠️ Important: Happy Path v1.0 Disclaimer", 
                 "## ⚠️ Important: Happy Path v0.1.1-alpha Disclaimer"),
                ("Nova CI-Rescue v1.0", "Nova CI-Rescue v0.1.1-alpha"),
                ("Nova v1.0 CAN", "Nova v0.1.1-alpha CAN"),
                ("Nova v1.0 CANNOT", "Nova v0.1.1-alpha CANNOT"),
            ]),
            ("docs/01-happy-path-one-pager.md", [
                ("Ship Nova CI-Rescue v1.0 Happy Path",
                 "Ship Nova CI-Rescue v0.1.1-alpha Happy Path"),
                ("**In Scope (v1.0):**", "**In Scope (v0.1.1-alpha):**"),
                ("## Definition of Done (v1.0)", "## Definition of Done (v0.1.1-alpha)"),
            ]),
            ("pyproject.toml", [
                ('version = "0.1.1"', 'version = "0.1.1-alpha"'),
            ])
        ]
        
        for file_path, replacements in updates:
            path = Path(file_path)
            if not path.exists():
                self.log(f"File not found: {path}", "warning")
                continue
            
            content = path.read_text()
            original = content
            
            for old, new in replacements:
                content = content.replace(old, new)
            
            if content != original:
                if not self.dry_run:
                    path.write_text(content)
                self.log(f"Updated versions in {file_path}", "success")
                changes_made = True
        
        if changes_made:
            self.fixes_applied.append("Version standardization")
        return changes_made
    
    def create_troubleshooting_guide(self) -> bool:
        """Fix 5: Create comprehensive troubleshooting guide."""
        self.log("Creating troubleshooting guide", "fix")
        
        guide_path = Path("docs/troubleshooting-guide.md")
        
        if guide_path.exists():
            self.log("Troubleshooting guide already exists", "info")
            return False
        
        content = '''# Nova CI-Rescue Troubleshooting Guide

## Quick Fixes for Common Issues

### 1. API Key Not Found

**Error:** `Error: OPENAI_API_KEY not found in environment`

**Solutions:**
```bash
# Option 1: Export in shell
export OPENAI_API_KEY="sk-..."

# Option 2: Create .env file
echo "OPENAI_API_KEY=sk-..." > .env

# Option 3: Pass via command line
OPENAI_API_KEY="sk-..." nova fix .
```

### 2. Installation Problems

**Error:** `ModuleNotFoundError: No module named 'nova'`

**Solutions:**
```bash
# Reinstall Nova
pip uninstall nova-ci-rescue -y
pip install -e .

# Verify installation
python -c "import nova; print(nova.__version__)"
```

### 3. Version Command Issues

**Error:** `No such option: --version`

**Solution:**
```bash
# Use the version command instead
nova version

# Or check via Python
python -c "from nova import __version__; print(__version__)"
```

### 4. Timeout Errors

**Error:** `Timeout reached: Exceeded 600s limit`

**Solutions:**
```bash
# Increase timeout
nova fix . --timeout 1200  # 20 minutes

# Or set via environment
export NOVA_RUN_TIMEOUT_SEC=1200
nova fix .
```

### 5. Safety Limit Violations

**Error:** `Patch rejected: Exceeds maximum lines changed`

**Solutions:**
```bash
# Option 1: Review and apply manually
git diff > manual_review.patch
patch -p1 < manual_review.patch

# Option 2: Temporarily increase limits
nova fix . --max-lines 500 --max-files 20

# Option 3: Fix one issue at a time
nova fix . --max-iters 1
```

### 6. Git Branch Conflicts

**Error:** `Branch 'nova-fix-...' already exists`

**Solutions:**
```bash
# Clean up old branches
git branch | grep nova-fix | xargs git branch -D

# Or reset to main
git checkout main
git reset --hard origin/main
git clean -fd
```

### 7. Pytest Not Found

**Error:** `pytest: command not found`

**Solutions:**
```bash
# Install pytest with required plugins
pip install pytest pytest-json-report pytest-timeout

# Verify installation
pytest --version
```

### 8. Import Errors

**Error:** `ImportError: cannot import name 'NovaConfig'`

**Solution:**
```bash
# The class was renamed to CLIConfig
# Update your imports:
# from nova.config import NovaConfig  # Old
from nova.config import CLIConfig     # New
```

## Environment Variables

Nova supports these environment variables:

```bash
# API Keys
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."

# Configuration
export NOVA_RUN_TIMEOUT_SEC=1200
export NOVA_MAX_ITERS=5
export NOVA_DEBUG=true
export NOVA_LOG_LEVEL=DEBUG

# Safety Limits
export NOVA_MAX_LINES_CHANGED=500
export NOVA_MAX_FILES_MODIFIED=20
```

## Debug Mode

Enable detailed debugging:

```bash
# Maximum verbosity
export NOVA_DEBUG=true
export NOVA_LOG_LEVEL=DEBUG
nova fix . --verbose

# Check configuration
nova config

# Trace execution
ls -la .nova/*/trace.jsonl
tail -f .nova/*/trace.jsonl
```

## Checking Logs

Nova creates detailed logs in `.nova/<timestamp>/`:

```bash
# List all runs
ls -la .nova/

# View latest run
ls -la .nova/$(ls -t .nova/ | head -1)/

# Check trace log
cat .nova/*/trace.jsonl | jq '.'

# View patches
cat .nova/*/patches/*.patch

# Check test reports
cat .nova/*/reports/*.xml
```

## Recovery Procedures

### After a Failed Run

```bash
# 1. Check what changed
git status
git diff

# 2. Review Nova's patches
ls .nova/*/patches/
cat .nova/*/patches/step-*.patch

# 3. Reset if needed
git reset --hard HEAD
git clean -fd

# 4. Try again with different settings
nova fix . --max-iters 1 --verbose
```

### Rollback Changes

```bash
# Option 1: Switch back to original branch
git checkout main

# Option 2: Revert Nova's commits
git log --oneline -5
git revert HEAD

# Option 3: Hard reset (loses all changes)
git reset --hard origin/main
```

## Performance Issues

### Slow Execution

```bash
# Reduce scope
nova fix . --max-iters 1 --timeout 300

# Limit test discovery
nova fix . --test-pattern "test_*.py"

# Use faster model (future feature)
nova fix . --model gpt-3.5-turbo
```

### Memory Issues

```bash
# Monitor memory usage
watch -n 1 free -h

# Limit concurrent operations
export NOVA_PARALLEL_JOBS=1
nova fix .
```

## Getting Help

1. **Check documentation:**
   - README.md
   - docs/quickstart-guide.md
   - docs/safety-limits.md

2. **View examples:**
   - examples/demos/demo_happy_path.py
   - demo-repo/ (working example)

3. **Community support:**
   - GitHub Issues: [Report bugs](https://github.com/nova-solve/nova-ci-rescue/issues)
   - Discord: [Join community](https://discord.gg/nova-solve)
   - Email: support@novasolve.ai

## FAQ

**Q: Can I use Nova with my CI/CD pipeline?**
A: Yes! See `.github/workflows/nova-ci-rescue.yml` for GitHub Actions example.

**Q: How much do API calls cost?**
A: Typical fixes cost $0.05-$0.15 depending on complexity and model used.

**Q: Is my code secure?**
A: Only relevant context is sent to the API, not your entire codebase. Use environment variables for API keys, never commit them.

**Q: Can Nova fix all test failures?**
A: Nova v0.1.1-alpha handles simple unit test failures. Complex integration tests, environment issues, and flaky tests may not be fixable automatically.

**Q: How do I contribute?**
A: See CONTRIBUTING.md (coming soon) or open a discussion on GitHub.

---

*Last updated: January 2025 | Nova CI-Rescue v0.1.1-alpha*
'''
        
        if not self.dry_run:
            guide_path.parent.mkdir(parents=True, exist_ok=True)
            guide_path.write_text(content)
        
        self.log("Created comprehensive troubleshooting guide", "success")
        self.fixes_applied.append("Troubleshooting guide")
        return True
    
    def create_rollback_guide(self) -> bool:
        """Fix 6: Create rollback documentation."""
        self.log("Creating rollback guide", "fix")
        
        guide_path = Path("docs/rollback-guide.md")
        
        if guide_path.exists():
            self.log("Rollback guide already exists", "info")
            return False
        
        content = '''# Nova CI-Rescue Rollback Guide

## How Nova Manages Changes

Nova automatically creates a branch before making changes:

```bash
# Nova creates branches like: nova-fix-20250115-143022
git branch
* nova-fix-20250115-143022
  main
```

## Quick Rollback Methods

### Method 1: Return to Original Branch (Recommended)

```bash
# Switch back to your original branch
git checkout main

# Optionally delete the Nova branch
git branch -D nova-fix-*
```

### Method 2: Cherry-Pick Good Changes

```bash
# View what Nova changed
git log --oneline nova-fix-* ^main

# Cherry-pick specific commits you want to keep
git checkout main
git cherry-pick <commit-hash>
```

### Method 3: Revert Specific Changes

```bash
# If you've already merged Nova's changes
git log --oneline -5

# Revert the last commit
git revert HEAD

# Or revert a specific commit
git revert <commit-hash>
```

### Method 4: Hard Reset (Nuclear Option)

```bash
# WARNING: This discards ALL local changes
git fetch origin
git reset --hard origin/main
git clean -fd
```

## Recovering from Interrupted Runs

If Nova was interrupted mid-fix:

### 1. Assess Current State

```bash
# Check what's changed
git status
git diff

# See what Nova was doing
cat .nova/*/trace.jsonl | tail -20
```

### 2. Review Partial Changes

```bash
# List Nova's patches
ls -la .nova/*/patches/

# Review each patch
cat .nova/*/patches/step-1.patch
cat .nova/*/patches/step-2.patch
```

### 3. Apply Selectively

```bash
# Apply only the patches that worked
git apply .nova/*/patches/step-1.patch

# Or manually apply parts of a patch
git apply --interactive .nova/*/patches/step-2.patch
```

## Preventing Issues

### Before Running Nova

```bash
# 1. Create a backup branch
git checkout -b backup-$(date +%Y%m%d)

# 2. Commit current work
git add -A
git commit -m "Checkpoint before Nova fix"

# 3. Push to remote
git push origin backup-$(date +%Y%m%d)
```

### During Nova Runs

```bash
# Use dry-run first (when available)
nova fix . --dry-run

# Limit scope
nova fix . --max-iters 1

# Review after each iteration
nova fix . --pause-after-iteration
```

### After Nova Completes

```bash
# Always review changes
git diff

# Test thoroughly
pytest

# Commit with clear message
git commit -m "fix: Applied Nova automatic fixes for failing tests

- Fixed: [list what was fixed]
- Nova run ID: $(ls -t .nova/ | head -1)
- Review patches in .nova/*/patches/"
```

## Troubleshooting Rollback Issues

### "Cannot switch branch - uncommitted changes"

```bash
# Option 1: Stash changes
git stash
git checkout main
git stash pop  # If you want the changes back

# Option 2: Commit changes
git add -A
git commit -m "WIP: Nova partial fix"
git checkout main
```

### "Branch nova-fix-* has diverged"

```bash
# Force checkout
git checkout -f main

# Clean up diverged branch
git branch -D nova-fix-*
```

### "Patch does not apply"

```bash
# Try with fuzzy matching
git apply --3way .nova/*/patches/step-1.patch

# Or apply manually
patch -p1 < .nova/*/patches/step-1.patch
```

## Best Practices

1. **Review Mode**: Always review Nova's changes before committing
2. **Incremental Fixes**: Use `--max-iters 1` for step-by-step fixes
3. **Version Control**: Commit before and after Nova runs
4. **Documentation**: Note Nova run IDs in commit messages
5. **Testing**: Run full test suite after Nova fixes

## Emergency Recovery

If everything goes wrong:

```bash
# 1. Don't panic!
# 2. Check if you have uncommitted changes worth saving
git stash

# 3. Return to last known good state
git fetch origin
git reset --hard origin/main

# 4. Clean up
git clean -fd
rm -rf .nova/

# 5. Start fresh
git checkout -b nova-retry
```

## Getting Help

- Check logs: `.nova/*/trace.jsonl`
- Review patches: `.nova/*/patches/*.patch`
- Ask for help: [GitHub Issues](https://github.com/nova-solve/nova-ci-rescue/issues)

---

*Remember: Git is your safety net. When in doubt, create a backup branch first!*
'''
        
        if not self.dry_run:
            guide_path.parent.mkdir(parents=True, exist_ok=True)
            guide_path.write_text(content)
        
        self.log("Created rollback guide", "success")
        self.fixes_applied.append("Rollback guide")
        return True
    
    def standardize_timeouts(self) -> bool:
        """Fix 7: Add standardized timeout configuration."""
        self.log("Standardizing timeout configuration", "fix")
        
        config_path = Path("src/nova/config.py")
        if not config_path.exists():
            self.log(f"File not found: {config_path}", "error")
            return False
        
        content = config_path.read_text()
        
        # Check if timeout constants already exist
        if "DEFAULT_TIMEOUT_QUICK" in content:
            self.log("Timeout constants already defined", "info")
            return False
        
        # Add timeout constants after the imports
        timeout_config = '''
# Standardized timeout defaults (in seconds)
DEFAULT_TIMEOUT_QUICK = 300      # 5 minutes for quick fixes
DEFAULT_TIMEOUT_NORMAL = 600     # 10 minutes for normal runs (default)
DEFAULT_TIMEOUT_EXTENDED = 1200  # 20 minutes for complex fixes  
DEFAULT_TIMEOUT_MAX = 1800       # 30 minutes absolute maximum

'''
        
        # Find a good insertion point (after imports, before first class)
        import_end = content.rfind('\n\n') 
        if import_end > 0:
            # Find first class definition
            class_start = content.find('\nclass ')
            if class_start > import_end:
                # Insert between imports and first class
                content = content[:class_start] + timeout_config + content[class_start:]
                
                if not self.dry_run:
                    config_path.write_text(content)
                self.log("Added timeout constants", "success")
                self.fixes_applied.append("Timeout standardization")
                return True
        
        self.log("Could not find insertion point for timeout config", "warning")
        return False
    
    def run_all_fixes(self) -> Tuple[int, int]:
        """Run all fixes and return counts of applied and failed fixes."""
        fixes = [
            ("Import error fix", self.fix_import_error),
            ("Version definition", self.add_version_file),
            ("Version command", self.add_version_command),
            ("Version standardization", self.standardize_versions),
            ("Troubleshooting guide", self.create_troubleshooting_guide),
            ("Rollback guide", self.create_rollback_guide),
            ("Timeout configuration", self.standardize_timeouts),
        ]
        
        for name, fix_func in fixes:
            try:
                self.log(f"\nApplying: {name}", "info")
                fix_func()
            except Exception as e:
                self.log(f"Failed to apply {name}: {e}", "error")
                self.fixes_failed.append(name)
        
        return len(self.fixes_applied), len(self.fixes_failed)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Apply proposed fixes for Nova CI-Rescue Happy Path issues"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without modifying files"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🔧 Nova CI-Rescue Fix Application Script")
    print("=" * 60)
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No files will be modified\n")
    
    fixer = NovaFixer(dry_run=args.dry_run)
    applied, failed = fixer.run_all_fixes()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    if fixer.fixes_applied:
        print(f"✅ Fixes applied: {len(fixer.fixes_applied)}")
        for fix in fixer.fixes_applied:
            print(f"   • {fix}")
    
    if fixer.fixes_failed:
        print(f"❌ Fixes failed: {len(fixer.fixes_failed)}")
        for fix in fixer.fixes_failed:
            print(f"   • {fix}")
    
    if not args.dry_run and fixer.fixes_applied:
        print("\n📝 Next steps:")
        print("1. Review changes: git diff")
        print("2. Test the fixes:")
        print("   - python verify_installation.py")
        print("   - nova version")
        print("   - pytest tests/")
        print("3. Commit changes:")
        print("   - git add -A")
        print('   - git commit -m "fix: Apply Happy Path audit fixes"')
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
