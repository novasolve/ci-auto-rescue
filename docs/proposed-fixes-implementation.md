# Proposed Fixes for Nova CI-Rescue Happy Path Issues

## 🔧 Critical Fix #1: Import Error in verify_installation.py

### Issue

The verification script tries to import `NovaConfig` but the actual class is `CLIConfig`.

### Current Code (Line 108)

```python
"from nova.config import NovaConfig",
```

### Proposed Fix

```python
"from nova.config import CLIConfig",
```

### Alternative: Update the entire test to be more robust

```python
# In verify_installation.py, replace lines 103-110 with:
test_imports = [
    "from nova import __version__",
    "from nova.cli import app",
    "from nova.config import CLIConfig, NovaSettings",  # Fixed import
    "from nova.agent.state import AgentState",
    "from nova.nodes.run_tests import RunTestsNode"
]
```

---

## 🔧 Critical Fix #2: Missing --version Command

### Issue

CLI doesn't support `--version` flag as documented.

### Proposed Implementation

#### Option A: Add as Typer callback (Recommended)

```python
# In src/nova/cli.py, after line 33, add:

def version_callback(value: bool):
    """Show version and exit."""
    if value:
        try:
            from nova import __version__
            console.print(f"nova-ci-rescue v{__version__}")
        except ImportError:
            console.print("nova-ci-rescue v0.1.1")
        raise typer.Exit()

# Then modify the app initialization (line 27-31):
app = typer.Typer(
    name="nova",
    help="Nova CI-Rescue: Automated test fixing agent",
    add_completion=False,
    callback=lambda version: bool = typer.Option(
        None, "--version", "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit"
    ): None
)
```

#### Option B: Add version command (Simpler)

```python
# Add before the final if __name__ == "__main__": block:

@app.command()
def version():
    """Display Nova CI-Rescue version information."""
    try:
        from nova import __version__
        version_str = __version__
    except ImportError:
        version_str = "0.1.1"

    console.print(f"[bold cyan]Nova CI-Rescue[/bold cyan] v{version_str}")
    console.print("Copyright (c) 2025 NovaSolve")
    console.print("License: Proprietary")

    # Show Python version for debugging
    import sys
    console.print(f"\n[dim]Python: {sys.version.split()[0]}[/dim]")
    console.print(f"[dim]Platform: {sys.platform}[/dim]")
```

---

## 🔧 Critical Fix #3: Version Number Consistency

### Issue

Documentation mixes v0.1.1, v1.0, and alpha references.

### Proposed Standardization

Use semantic versioning: **v0.1.1-alpha** everywhere

### Files to Update:

#### 1. src/nova/**init**.py

```python
# Ensure this exists and is consistent:
__version__ = "0.1.1-alpha"
```

#### 2. pyproject.toml

```toml
[tool.poetry]
name = "nova-ci-rescue"
version = "0.1.1-alpha"  # Standardize here
```

#### 3. README.md

```markdown
# Change line 4:

<p><strong>v0.1.1-alpha - Happy Path MVP</strong></p>

# Change line 14:

## ⚠️ Important: Happy Path v0.1.1-alpha Disclaimer

# Change line 16:

**Nova CI-Rescue v0.1.1-alpha is optimized for the "Happy Path"...**

# Update all references:

### ✅ What Nova v0.1.1-alpha CAN Do:

### ❌ What Nova v0.1.1-alpha CANNOT Do (Yet):
```

#### 4. docs/01-happy-path-one-pager.md

```markdown
# Line 3:

## Goal

Ship Nova CI-Rescue v0.1.1-alpha Happy Path...

# Line 15:

**In Scope (v0.1.1-alpha):**

# Line 62:

## Definition of Done (v0.1.1-alpha)
```

---

## 🔧 Critical Fix #4: Timeout Standardization

### Issue

Inconsistent timeout values: 300, 600, 1200, 1800 seconds across docs.

### Proposed Standard Configuration

#### 1. Create default config in src/nova/config.py

```python
class NovaSettings(BaseModel):
    """Runtime configuration for Nova CI-Rescue."""

    # Standardized timeout defaults
    DEFAULT_TIMEOUT_QUICK: int = 300    # 5 minutes for quick fixes
    DEFAULT_TIMEOUT_NORMAL: int = 600   # 10 minutes for normal runs
    DEFAULT_TIMEOUT_EXTENDED: int = 1200  # 20 minutes for complex fixes
    DEFAULT_TIMEOUT_MAX: int = 1800     # 30 minutes absolute maximum

    # Current timeout (use NORMAL as default)
    run_timeout_seconds: int = Field(
        default=600,
        description="Overall timeout for nova fix run (default: 10 minutes)",
        ge=60,  # minimum 1 minute
        le=1800  # maximum 30 minutes
    )
```

#### 2. Update all documentation to use these standards

```markdown
# In quickstart guide:

## Quick fix (5 minutes)

nova fix . --timeout 300

## Normal fix (10 minutes, default)

nova fix .

## Extended fix for complex issues (20 minutes)

nova fix . --timeout 1200

## Maximum allowed (30 minutes)

nova fix . --timeout 1800
```

---

## 🔧 High Priority Fix #1: Better API Key Error Messages

### Current Issue

Generic "API key not found" error.

### Proposed Implementation

```python
# In src/nova/agent/llm_client.py or similar:

def _validate_api_key(self):
    """Validate API key with helpful error messages."""
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        error_msg = """
🔑 API Key Not Found

Nova CI-Rescue requires an OpenAI or Anthropic API key to function.

To fix this, choose one of these options:

1. Set environment variable:
   export OPENAI_API_KEY="sk-..."

2. Create a .env file in your project root:
   echo "OPENAI_API_KEY=sk-..." > .env

3. Pass via command line:
   OPENAI_API_KEY="sk-..." nova fix .

4. Use a configuration file (see docs/quickstart-guide.md)

Get your API key from:
- OpenAI: https://platform.openai.com/api-keys
- Anthropic: https://console.anthropic.com/settings/keys

For more help, see: docs/troubleshooting-guide.md
"""
        console.print(Panel(error_msg, title="[red]Configuration Error[/red]"))
        raise typer.Exit(1)

    # Validate format
    if api_key.startswith("sk-proj-"):
        console.print("[green]✓ OpenAI project API key detected[/green]")
    elif api_key.startswith("sk-"):
        console.print("[green]✓ OpenAI API key detected[/green]")
    elif api_key.startswith("sk-ant-"):
        console.print("[green]✓ Anthropic API key detected[/green]")
    else:
        console.print("[yellow]⚠ API key format unrecognized, proceeding anyway...[/yellow]")
```

---

## 🔧 High Priority Fix #2: Rollback Documentation

### Create new file: docs/rollback-guide.md

````markdown
# Nova CI-Rescue Rollback Guide

## Automatic Rollback

Nova automatically creates a branch before making changes:

```bash
# Nova creates: nova-fix-YYYYMMDD-HHMMSS
git branch
* nova-fix-20250115-143022
  main
```
````

## Manual Rollback Methods

### Method 1: Reset to Original Branch

```bash
# Switch back to main
git checkout main

# Delete the fix branch
git branch -D nova-fix-*
```

### Method 2: Revert Specific Commits

```bash
# View Nova's commits
git log --oneline -n 5

# Revert the last Nova commit
git revert HEAD

# Or revert specific commit
git revert <commit-hash>
```

### Method 3: Hard Reset (Nuclear Option)

```bash
# WARNING: This discards ALL changes
git reset --hard origin/main
git clean -fd
```

## Recovering from Partial Fixes

If Nova was interrupted:

1. Check current state:

```bash
git status
git diff
```

2. Review patches:

```bash
ls -la .nova/*/patches/
cat .nova/*/patches/step-*.patch
```

3. Apply selectively:

```bash
# Apply only good patches
git apply .nova/*/patches/step-1.patch
```

## Best Practices

1. **Always review before committing:**

```bash
git diff
nova fix . --dry-run  # Future feature
```

2. **Create backup branch:**

```bash
git checkout -b backup-before-nova
```

3. **Use version control:**

```bash
git commit -m "Checkpoint before Nova fix"
```

````

---

## 🔧 High Priority Fix #3: Progress Indicators

### Add progress tracking to CLI
```python
# In src/nova/cli.py, enhance the fix command:

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.live import Live
from rich.table import Table

def run_with_progress(state: AgentState, agent, runner):
    """Run agent loop with progress indicators."""

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    ) as progress:

        # Main task
        main_task = progress.add_task(
            "[cyan]Fixing tests...",
            total=state.max_iterations
        )

        for iteration in range(1, state.max_iterations + 1):
            # Update main progress
            progress.update(main_task, advance=1)

            # Sub-tasks for each step
            step_task = progress.add_task(
                f"[yellow]Iteration {iteration}",
                total=6  # 6 steps in agent loop
            )

            # Step 1: Planner
            progress.update(step_task, description="[blue]Planning fix...", advance=1)
            plan = agent.create_plan(state.failing_tests, iteration)

            # Step 2: Actor
            progress.update(step_task, description="[blue]Generating patch...", advance=1)
            patch = agent.generate_patch(state.failing_tests, iteration, plan)

            # Continue for other steps...

            progress.remove_task(step_task)
````

---

## 🔧 Quick Fix Script

### Complete fix_all_issues.sh

```bash
#!/bin/bash
# Quick script to apply all proposed fixes

echo "🔧 Applying Nova CI-Rescue fixes..."

# Fix 1: Update imports
sed -i '' 's/from nova.config import NovaConfig/from nova.config import CLIConfig/g' verify_installation.py

# Fix 2: Standardize version
echo '__version__ = "0.1.1-alpha"' > src/nova/__init__.py

# Fix 3: Update README versions
sed -i '' 's/v1\.0 - Happy Path/v0.1.1-alpha - Happy Path MVP/g' README.md
sed -i '' 's/Nova v1\.0/Nova v0.1.1-alpha/g' README.md

# Fix 4: Create troubleshooting guide
cat > docs/troubleshooting-guide.md << 'EOF'
# Nova CI-Rescue Troubleshooting Guide
[Content from proposed fix above]
EOF

# Fix 5: Run tests
python verify_installation.py

echo "✅ Fixes applied! Run 'git diff' to review changes"
```

---

## 📋 Implementation Order

1. **Immediate (5 minutes):**

   - Fix import in verify_installation.py
   - Add **version** to **init**.py

2. **Quick (15 minutes):**

   - Add version command to CLI
   - Standardize version numbers in docs

3. **Short-term (30 minutes):**

   - Implement better error messages
   - Create troubleshooting guide
   - Add rollback documentation

4. **Medium-term (1-2 hours):**
   - Add progress indicators
   - Standardize timeout configuration
   - Create automated fix script

## 🎯 Testing After Fixes

```bash
# Test 1: Verify installation
python verify_installation.py

# Test 2: Check version command
nova version

# Test 3: Test with demo repo
cd demo-repo
nova fix . --timeout 300

# Test 4: Verify safety limits
python -m pytest tests/test_safety_limits.py

# Test 5: Full integration test
nova fix examples/demos/demo_test_repo --verbose
```

## Expected Outcomes

After implementing these fixes:

- ✅ Installation verification will pass completely
- ✅ Version command will work as documented
- ✅ Consistent version numbering throughout
- ✅ Clear, helpful error messages
- ✅ Standardized timeout values
- ✅ Complete rollback documentation
- ✅ Better user experience with progress indicators

These fixes address all critical issues and most high-priority items from the audit, making Nova CI-Rescue production-ready for the Happy Path MVP release.
