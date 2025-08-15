#!/usr/bin/env python3
"""
Script to fix critical issues found in the Happy Path audit.
Run this to address the immediate problems identified.
"""

import os
import sys
from pathlib import Path

def fix_verify_installation():
    """Fix the import issue in verify_installation.py"""
    file_path = Path("verify_installation.py")
    if not file_path.exists():
        print(f"⚠️  File not found: {file_path}")
        return False
    
    content = file_path.read_text()
    
    # Fix the import statement
    old_import = '"from nova.config import NovaConfig",'
    new_import = '"from nova.config import CLIConfig",'
    
    if old_import in content:
        content = content.replace(old_import, new_import)
        file_path.write_text(content)
        print(f"✅ Fixed import in {file_path}")
        return True
    else:
        print(f"ℹ️  Import already fixed or different in {file_path}")
        return False

def add_version_command():
    """Add version command to CLI if missing"""
    cli_path = Path("src/nova/cli.py")
    if not cli_path.exists():
        print(f"⚠️  CLI file not found: {cli_path}")
        return False
    
    content = cli_path.read_text()
    
    # Check if version command already exists
    if "@app.command()\ndef version():" in content:
        print("ℹ️  Version command already exists")
        return False
    
    # Add version command after the last command
    version_command = '''
@app.command()
def version():
    """Display Nova CI-Rescue version."""
    try:
        from nova import __version__
        console.print(f"nova-ci-rescue v{__version__}")
    except ImportError:
        console.print("nova-ci-rescue v0.1.1")  # Fallback version
'''
    
    # Find a good place to insert (before if __name__ == "__main__":)
    insertion_point = 'if __name__ == "__main__":'
    if insertion_point in content:
        content = content.replace(
            insertion_point,
            version_command + "\n\n" + insertion_point
        )
        cli_path.write_text(content)
        print(f"✅ Added version command to {cli_path}")
        return True
    else:
        print(f"⚠️  Could not find insertion point in {cli_path}")
        return False

def update_readme_version():
    """Update README to clarify version numbering"""
    readme_path = Path("README.md")
    if not readme_path.exists():
        print(f"⚠️  README not found: {readme_path}")
        return False
    
    content = readme_path.read_text()
    
    # Update version references to be consistent
    changes_made = False
    
    # Fix version in title area
    old_version = "**v1.0 - Happy Path Edition**"
    new_version = "**v0.1.1 - Happy Path MVP Edition**"
    if old_version in content:
        content = content.replace(old_version, new_version)
        changes_made = True
    
    # Fix version disclaimer title
    old_title = "## ⚠️ Important: Happy Path v1.0 Disclaimer"
    new_title = "## ⚠️ Important: Happy Path v0.1.1 (MVP) Disclaimer"
    if old_title in content:
        content = content.replace(old_title, new_title)
        changes_made = True
    
    # Fix version references in text
    content = content.replace("Nova v1.0 CAN", "Nova v0.1.1 CAN")
    content = content.replace("Nova v1.0 CANNOT", "Nova v0.1.1 CANNOT")
    
    if changes_made:
        readme_path.write_text(content)
        print(f"✅ Updated version references in {readme_path}")
        return True
    else:
        print(f"ℹ️  No version updates needed in {readme_path}")
        return False

def create_troubleshooting_guide():
    """Create a basic troubleshooting guide"""
    guide_path = Path("docs/troubleshooting-guide.md")
    
    if guide_path.exists():
        print(f"ℹ️  Troubleshooting guide already exists: {guide_path}")
        return False
    
    content = '''# Nova CI-Rescue Troubleshooting Guide

## Common Issues and Solutions

### 1. API Key Not Found

**Error:** `Error: OPENAI_API_KEY not found in environment`

**Solution:**
```bash
# Option 1: Export in shell
export OPENAI_API_KEY="sk-..."

# Option 2: Create .env file
echo "OPENAI_API_KEY=sk-..." > .env

# Option 3: Pass via command line
OPENAI_API_KEY="sk-..." nova fix .
```

### 2. Installation Issues

**Error:** `ModuleNotFoundError: No module named 'nova'`

**Solution:**
```bash
# Reinstall Nova
pip uninstall nova-ci-rescue
pip install -e .

# Verify installation
python -c "import nova; print(nova.__version__)"
```

### 3. Version Command Not Working

**Error:** `No such option: --version`

**Solution:**
```bash
# Use the version command instead
nova version

# Or check via Python
python -c "import nova; print(nova.__version__)"
```

### 4. Timeout Errors

**Error:** `Timeout reached: Exceeded 600s limit`

**Solution:**
```bash
# Increase timeout
nova fix . --timeout 1800  # 30 minutes

# Or set via environment
export NOVA_RUN_TIMEOUT_SEC=1800
nova fix .
```

### 5. Patch Rejected by Safety Limits

**Error:** `Patch rejected: Exceeds maximum lines changed: 350 > 200`

**Solution:**
```bash
# Option 1: Review and apply manually
git diff > manual_review.patch

# Option 2: Increase limits (use with caution)
nova fix . --max-lines 500

# Option 3: Break into smaller changes
nova fix . --max-iters 1  # One fix at a time
```

### 6. Git Branch Conflicts

**Error:** `Branch 'nova-fix-...' already exists`

**Solution:**
```bash
# Clean up old branches
git branch -D nova-fix-*

# Or reset to main
git checkout main
git reset --hard origin/main
```

### 7. Test Runner Not Found

**Error:** `pytest: command not found`

**Solution:**
```bash
# Install pytest
pip install pytest pytest-json-report

# Verify installation
pytest --version
```

### 8. Memory or Resource Issues

**Error:** `Process killed` or system becomes unresponsive

**Solution:**
```bash
# Limit iterations
nova fix . --max-iters 1

# Run with verbose output to see progress
nova fix . --verbose

# Check system resources
top  # or htop
```

## Getting Help

If you encounter issues not covered here:

1. Check the logs: `.nova/<run>/trace.jsonl`
2. Search existing issues: [GitHub Issues](https://github.com/nova-solve/nova-ci-rescue/issues)
3. Ask in Discord: [discord.gg/nova-solve]
4. Email support: support@novasolve.ai

## Debug Mode

For detailed debugging:

```bash
# Enable debug logging
export NOVA_DEBUG=true
export NOVA_LOG_LEVEL=DEBUG
nova fix . --verbose

# Check Python path issues
python -c "import sys; print(sys.path)"
python -c "import nova; print(nova.__file__)"
```

## Reporting Issues

When reporting issues, please include:

1. Nova version: `nova version` or `pip show nova-ci-rescue`
2. Python version: `python --version`
3. Operating system: `uname -a` (Unix) or `ver` (Windows)
4. Error message and stack trace
5. Relevant logs from `.nova/<run>/trace.jsonl`
6. Minimal reproduction steps

## FAQ

**Q: Why does Nova make seemingly incorrect changes?**
A: Nova uses LLM models which can sometimes misunderstand context. Always review changes before committing.

**Q: Can I use Nova with private/enterprise models?**
A: Yes, configure your API endpoint in the environment or config file.

**Q: How much does it cost to run Nova?**
A: Typical fixes cost $0.05-$0.15 in API calls, depending on complexity.

**Q: Can Nova fix all test failures?**
A: No, Nova v0.1.1 handles simple unit test failures. Complex integration tests, flaky tests, and environment-specific issues may not be fixable.

**Q: Is my code sent to OpenAI/Anthropic?**
A: Only relevant code context is sent, not your entire codebase. Use self-hosted models for sensitive code.
'''
    
    guide_path.write_text(content)
    print(f"✅ Created troubleshooting guide: {guide_path}")
    return True

def main():
    """Run all fixes"""
    print("🔧 Fixing audit issues...\n")
    
    fixes_applied = 0
    
    # Fix critical issues
    if fix_verify_installation():
        fixes_applied += 1
    
    if add_version_command():
        fixes_applied += 1
    
    if update_readme_version():
        fixes_applied += 1
    
    if create_troubleshooting_guide():
        fixes_applied += 1
    
    print(f"\n✅ Applied {fixes_applied} fixes")
    
    if fixes_applied > 0:
        print("\n📝 Next steps:")
        print("1. Review the changes with: git diff")
        print("2. Test the fixes:")
        print("   - python verify_installation.py")
        print("   - nova version")
        print("3. Commit the changes:")
        print("   - git add -A")
        print('   - git commit -m "fix: Address critical issues from Happy Path audit"')
    else:
        print("\nℹ️  No fixes were needed or all issues already addressed")

if __name__ == "__main__":
    main()
