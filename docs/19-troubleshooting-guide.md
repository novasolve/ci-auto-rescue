# Nova CI-Rescue - Troubleshooting Guide

## Quick Diagnosis Flowchart

```
Is Nova installed correctly?
├─ No → See "Installation Issues"
└─ Yes → Can Nova find your tests?
         ├─ No → See "Test Discovery Issues"
         └─ Yes → Does Nova start running?
                  ├─ No → See "Configuration Issues"
                  └─ Yes → Does Nova complete?
                           ├─ No (Timeout) → See "Performance Issues"
                           ├─ No (Error) → See "Runtime Errors"
                           └─ Yes → Are tests fixed?
                                    ├─ No → See "Fix Quality Issues"
                                    └─ Yes → Success! 🎉
```

## Common Issues and Solutions

### Installation Issues

#### Problem: `nova: command not found`

**Diagnosis:**

```bash
which nova
pip show nova-ci-rescue
```

**Solutions:**

1. **Not installed:**

   ```bash
   pip install nova-ci-rescue
   ```

2. **Not in PATH:**

   ```bash
   # Find where it's installed
   pip show -f nova-ci-rescue | grep nova

   # Add to PATH (example for user install)
   export PATH="$HOME/.local/bin:$PATH"

   # Make permanent (add to .bashrc/.zshrc)
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
   ```

3. **Wrong Python environment:**

   ```bash
   # Check active environment
   which python

   # Activate correct environment
   source venv/bin/activate  # or conda activate myenv

   # Reinstall in correct environment
   pip install nova-ci-rescue
   ```

#### Problem: `ModuleNotFoundError: No module named 'nova'`

**Solutions:**

```bash
# Reinstall with dependencies
pip install --force-reinstall nova-ci-rescue

# Check for conflicts
pip check

# Install from source if needed
git clone https://github.com/nova-solve/ci-auto-rescue
cd ci-auto-rescue
pip install -e .
```

### Configuration Issues

#### Problem: `API key not found`

**Error Message:**

```
❌ Configuration Error: API key not found
```

**Diagnosis:**

```bash
# Check environment
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY

# Check .env file
cat .env

# Check config file
cat nova-config.yaml
```

**Solutions:**

1. **Set environment variable:**

   ```bash
   export OPENAI_API_KEY="sk-..."
   ```

2. **Create .env file:**

   ```bash
   cat > .env << EOF
   OPENAI_API_KEY=sk-...
   EOF
   ```

3. **Fix quotes in .env:**

   ```bash
   # Wrong:
   OPENAI_API_KEY='sk-...'  # Single quotes
   OPENAI_API_KEY="sk-..."  # Double quotes

   # Correct:
   OPENAI_API_KEY=sk-...     # No quotes
   ```

#### Problem: `Invalid API key`

**Diagnosis:**

```bash
# Test OpenAI key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Test Anthropic key
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01"
```

**Solutions:**

1. **Check key format:**

   - OpenAI: Should start with `sk-`
   - Anthropic: Should start with `sk-ant-`

2. **Regenerate key:**

   - Visit API provider's dashboard
   - Create new key
   - Update configuration

3. **Check billing:**
   - Ensure account has credits
   - Check usage limits

### Test Discovery Issues

#### Problem: `No tests found`

**Diagnosis:**

```bash
# Check pytest discovery
pytest --collect-only

# Check test file naming
find . -name "test_*.py" -o -name "*_test.py"

# Check for pytest.ini or setup.cfg
cat pytest.ini
cat setup.cfg
```

**Solutions:**

1. **Fix test naming:**

   ```python
   # Tests must be named:
   test_something.py  # Prefix with test_
   something_test.py  # Suffix with _test

   # Test functions must start with test_
   def test_my_function():
       pass
   ```

2. **Specify test directory:**

   ```bash
   nova fix . --test-dir tests/
   nova fix . --test-dir src/tests/
   ```

3. **Fix pytest configuration:**
   ```ini
   # pytest.ini
   [pytest]
   testpaths = tests
   python_files = test_*.py *_test.py
   python_classes = Test*
   python_functions = test_*
   ```

#### Problem: `Import errors in tests`

**Diagnosis:**

```bash
# Check if tests run manually
python -m pytest tests/test_example.py -v

# Check Python path
python -c "import sys; print(sys.path)"
```

**Solutions:**

1. **Add to PYTHONPATH:**

   ```bash
   export PYTHONPATH="${PYTHONPATH}:${PWD}"
   nova fix .
   ```

2. **Install package in development mode:**

   ```bash
   pip install -e .
   ```

3. **Fix import statements:**

   ```python
   # Relative imports
   from ..src import module

   # Absolute imports
   from mypackage.src import module
   ```

### Runtime Errors

#### Problem: `Timeout reached`

**Diagnosis:**

```bash
# Check how long tests take
time pytest

# Check Nova's progress
tail -f .nova/latest/trace.jsonl
```

**Solutions:**

1. **Increase timeout:**

   ```bash
   nova fix . --timeout 600  # 10 minutes
   nova fix . --timeout 1800  # 30 minutes
   ```

2. **Reduce scope:**

   ```bash
   # Fix specific test file
   nova fix . --test-file tests/test_simple.py

   # Limit iterations
   nova fix . --max-iters 2
   ```

3. **Optimize tests:**
   ```python
   # Add test timeout
   @pytest.mark.timeout(30)
   def test_slow_function():
       pass
   ```

#### Problem: `Patch application failed`

**Error:**

```
🚫 Patch Application Failed: Merge conflict detected
```

**Diagnosis:**

```bash
# Check git status
git status

# Check for uncommitted changes
git diff

# Try applying patch manually
cat .nova/latest/diffs/step-1.patch | git apply --check
```

**Solutions:**

1. **Clean working directory:**

   ```bash
   git stash  # Save current changes
   nova fix .
   git stash pop  # Restore changes
   ```

2. **Reset and retry:**

   ```bash
   git reset --hard HEAD
   nova fix .
   ```

3. **Apply patches manually:**

   ```bash
   # Review patch
   cat .nova/latest/diffs/step-1.patch

   # Apply with git
   git apply .nova/latest/diffs/step-1.patch

   # Or use patch command
   patch -p1 < .nova/latest/diffs/step-1.patch
   ```

#### Problem: `Memory/CPU limits exceeded`

**Symptoms:**

- Process killed
- System becomes unresponsive
- Tests hang indefinitely

**Solutions:**

1. **Limit test resources:**

   ```python
   # In test file
   import resource
   resource.setrlimit(resource.RLIMIT_AS, (1024*1024*1024, -1))  # 1GB
   ```

2. **Run with limitations:**

   ```bash
   # Linux/Mac
   ulimit -v 2097152  # 2GB virtual memory
   nova fix .
   ```

3. **Use Docker:**
   ```bash
   docker run --memory=2g --cpus=2 \
     -v $(pwd):/workspace \
     nova-ci-rescue nova fix /workspace
   ```

### Performance Issues

#### Problem: Nova is very slow

**Diagnosis:**

```bash
# Check API response time
time curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models

# Monitor Nova's progress
watch -n 1 'tail -n 20 .nova/latest/trace.jsonl'
```

**Solutions:**

1. **Use faster model:**

   ```yaml
   # nova-config.yaml
   model: gpt-4-turbo  # Faster than gpt-4
   model: gpt-3.5-turbo  # Much faster, less capable
   ```

2. **Reduce context:**

   ```bash
   # Focus on specific files
   nova fix . --include "src/utils/*.py"
   ```

3. **Check network:**

   ```bash
   # Test latency to API
   ping api.openai.com

   # Use different network
   # Switch from WiFi to ethernet
   # Try different DNS (8.8.8.8)
   ```

### Fix Quality Issues

#### Problem: Nova's fixes don't work

**Diagnosis:**

```bash
# Review Nova's reasoning
cat .nova/latest/trace.jsonl | grep -A5 "planning"

# Check what Nova changed
git diff HEAD~1

# Run tests with verbose output
pytest -xvs
```

**Solutions:**

1. **Provide better context:**

   ```yaml
   # nova-config.yaml
   context_hints:
     - "This is a Django project"
     - "Using Python 3.11 features"
     - "Tests use mocking extensively"
   ```

2. **Simplify test structure:**

   ```python
   # Before: Complex test
   def test_complex():
       with mock.patch('module.function'):
           with override_settings(DEBUG=True):
               result = complex_operation()
               assert result == expected

   # After: Simpler test
   def test_simple():
       result = simple_operation(test_input)
       assert result == expected_output
   ```

3. **Use different model:**

   ```bash
   # Try GPT-4 if using GPT-3.5
   nova fix . --model gpt-4

   # Try Claude if using GPT
   nova fix . --model claude-3-sonnet
   ```

#### Problem: Nova fixes symptoms, not root cause

**Example:**
Nova hardcodes expected values instead of fixing logic

**Solutions:**

1. **Review and refine:**

   ```bash
   # Let Nova attempt
   nova fix . --dry-run

   # Review suggestions
   cat .nova/latest/diffs/*.patch

   # Apply selectively
   git apply -p1 --interactive .nova/latest/diffs/step-1.patch
   ```

2. **Add test descriptions:**

   ```python
   def test_calculation():
       """Test that discount calculation applies 10% off."""
       # Nova will understand the intent better
       result = calculate_discount(100)
       assert result == 90  # 10% off of 100
   ```

3. **Use Nova as hint, fix manually:**
   - Review Nova's analysis for clues
   - Understand what Nova attempted
   - Implement proper fix yourself

### CI/CD Integration Issues

#### Problem: Nova doesn't post PR comments

**Diagnosis:**

```bash
# Check environment variables in CI
echo $GITHUB_TOKEN
echo $GITHUB_REPOSITORY
echo $PR_NUMBER
```

**Solutions:**

1. **Fix permissions:**

   ```yaml
   # .github/workflows/nova.yml
   permissions:
     contents: write
     pull-requests: write
     checks: write
   ```

2. **Pass environment correctly:**

   ```yaml
   - name: Run Nova
     env:
       GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
       GITHUB_REPOSITORY: ${{ github.repository }}
       PR_NUMBER: ${{ github.event.pull_request.number }}
     run: nova fix .
   ```

3. **Debug token scopes:**
   ```bash
   # Check token permissions
   curl -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/user
   ```

#### Problem: Nova fails in CI but works locally

**Common Causes:**

1. Different Python versions
2. Missing dependencies
3. Environment variables not set
4. Different file paths

**Solutions:**

1. **Match environments:**

   ```yaml
   # Use same Python version
   - uses: actions/setup-python@v4
     with:
       python-version: "3.11" # Match local
   ```

2. **Install all dependencies:**

   ```yaml
   - run: |
       pip install -r requirements.txt
       pip install -r requirements-dev.txt
       pip install nova-ci-rescue
   ```

3. **Debug in CI:**
   ```yaml
   - name: Debug environment
     run: |
       python --version
       pip list
       pytest --version
       env | sort
   ```

## Advanced Debugging

### Enable Debug Logging

```bash
# Maximum verbosity
nova fix . --debug --verbose

# Save debug output
nova fix . --debug 2>&1 | tee nova-debug.log

# Python logging
export NOVA_LOG_LEVEL=DEBUG
nova fix .
```

### Analyze Nova's Trace

```python
#!/usr/bin/env python3
import json
import sys
from pathlib import Path

trace_file = Path(".nova/latest/trace.jsonl")

with open(trace_file) as f:
    for line in f:
        event = json.loads(line)

        # Find errors
        if event.get("level") == "ERROR":
            print(f"ERROR: {event.get('message')}")

        # Find planning
        if event.get("type") == "planning":
            print(f"PLAN: {event.get('content')}")

        # Find patches
        if event.get("type") == "patch":
            print(f"PATCH: {event.get('file')}")
```

### Manual API Testing

```python
#!/usr/bin/env python3
import openai
import os

# Test API connectivity
client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))

try:
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Test"}],
        max_tokens=10
    )
    print("API works:", response.choices[0].message.content)
except Exception as e:
    print("API error:", e)
```

### Check System Resources

```bash
# Memory
free -h  # Linux
vm_stat  # macOS

# Disk space
df -h

# Process limits
ulimit -a

# Python resources
python -c "import resource; print(resource.getrlimit(resource.RLIMIT_AS))"
```

## Getting Help

### Before Asking for Help

1. **Check documentation:**

   - This troubleshooting guide
   - [FAQ](./18-faq.md)
   - [Limitations](./13-limitations-and-known-issues.md)

2. **Gather information:**

   ```bash
   nova --version
   python --version
   pip show nova-ci-rescue
   cat .nova/latest/trace.jsonl | tail -50
   ```

3. **Try common fixes:**
   - Update Nova: `pip install -U nova-ci-rescue`
   - Clear cache: `rm -rf .nova`
   - Reset git: `git reset --hard HEAD`

### Where to Get Help

1. **GitHub Issues:**

   - Search existing issues first
   - Include minimal reproduction
   - Attach relevant logs

2. **Discord Community:**

   - #troubleshooting channel
   - #nova-help for general questions

3. **Support Email:**
   - support@joinnova.com
   - Include license key if applicable

### Creating a Good Bug Report

```markdown
## Environment

- Nova version: 1.0.0
- Python version: 3.11.0
- OS: Ubuntu 22.04
- API: OpenAI GPT-4

## Steps to Reproduce

1. Run `nova fix .`
2. Wait for timeout
3. Error appears

## Expected Behavior

Nova should fix the test

## Actual Behavior

Nova times out after 300 seconds

## Logs

[Attach .nova/latest/trace.jsonl]

## Additional Context

- Working on Django project
- Tests use PostgreSQL
```

## Emergency Procedures

### Nova Broke My Code

```bash
# Stop Nova immediately
Ctrl+C

# Check what changed
git status
git diff

# Revert all changes
git reset --hard HEAD
git clean -fd

# Revert last commit
git revert HEAD

# Go back to specific commit
git log --oneline
git reset --hard <commit-hash>
```

### Nova Used Too Much API Credit

```bash
# Set strict limits
export NOVA_MAX_ITERS=1
export NOVA_TIMEOUT=60

# Use cheaper model
nova fix . --model gpt-3.5-turbo

# Dry run only
nova fix . --dry-run
```

### Nova Is Stuck

```bash
# Find Nova process
ps aux | grep nova

# Kill it
kill -9 <process-id>

# Clean up
rm -rf .nova/current
```

## Prevention Tips

1. **Always commit before running Nova**
2. **Start with dry-run for new projects**
3. **Use conservative limits initially**
4. **Test on small subset first**
5. **Monitor API usage regularly**
6. **Keep Nova updated**
7. **Read error messages completely**
8. **Check logs before retrying**

Remember: Most issues have simple solutions. When in doubt, start fresh with a clean git state and minimal configuration.
