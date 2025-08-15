# Nova CI-Rescue - UX & CLI Improvements Guide

## Overview

This document outlines UX improvements for Nova CI-Rescue's CLI output and error messages, focusing on clarity, actionability, and user-friendliness.

## Design Principles

1. **Clarity**: Every message should be immediately understandable
2. **Actionability**: Errors should suggest next steps
3. **Progressive Disclosure**: Show essential info first, details on demand
4. **Visual Hierarchy**: Use colors, icons, and formatting effectively
5. **Consistency**: Uniform message patterns across all commands

## CLI Output Improvements

### Progress Indicators

#### Current vs Improved

**Current (Basic):**

```
Running tests...
Applying patch...
Done.
```

**Improved (Informative):**

```
🧪 Running tests... [23/45 passed]
  └─ test_calculator.py::test_divide ✓
  └─ test_calculator.py::test_multiply ✓
  └─ test_calculator.py::test_power ✗ (2.3s)

🔧 Applying patch... [1/3 files]
  └─ calculator.py (15 lines modified)

✨ Completed successfully in 45.2s
```

### Status Messages

#### Level 1: Minimal (Default)

```bash
$ nova fix .
🚀 Nova CI-Rescue v1.0
📋 Found 3 failing tests
🔄 Iteration 1/3... ✅ (1 fixed)
🔄 Iteration 2/3... ✅ (2 fixed)
✨ Success: All tests fixed (42s)
```

#### Level 2: Normal (--verbose)

```bash
$ nova fix . --verbose
🚀 Nova CI-Rescue v1.0 starting...
📁 Repository: /path/to/project
🔧 Config: max_iters=3, timeout=300s, model=gpt-4

🔍 Analyzing test failures...
  ✗ test_calculator.py::test_divide - ZeroDivisionError
  ✗ test_calculator.py::test_power - ValueError
  ✗ test_calculator.py::test_absolute - AttributeError

📝 Iteration 1/3
  🧠 Planning fix for test_divide...
  💡 Identified: Missing zero-check in divide()
  🔨 Generating patch...
  ✅ Applied 5-line fix to calculator.py
  🧪 Running tests... 1/3 fixed

[continues...]
```

#### Level 3: Debug (--debug)

```bash
$ nova fix . --debug
[2024-03-15 14:23:45] DEBUG: Loading configuration from nova.yaml
[2024-03-15 14:23:45] DEBUG: API Key found: sk-...xxx (last 3 chars)
[2024-03-15 14:23:45] INFO: Starting Nova CI-Rescue v1.0
[2024-03-15 14:23:45] DEBUG: Git branch: feature/new-calc
[2024-03-15 14:23:46] DEBUG: Running: pytest --co -q
[2024-03-15 14:23:47] DEBUG: Found 45 tests total
[continues with detailed logs...]
```

### Real-time Feedback

```python
# Progress bar for long operations
def show_progress():
    """
    🧪 Running test suite [████████████████░░░░] 78% (23/30)
       Current: test_integration.py::test_api_endpoint
       Time elapsed: 12.3s | Est. remaining: 3.2s
    """

# Spinner for indeterminate operations
def show_spinner():
    """
    🤔 Analyzing failure pattern... ⣷
    """

# Live test results
def show_live_results():
    """
    Tests: 23 ✅ | 5 ❌ | 2 ⏭️ | 30 total
    ┌─────────────────────────────────┐
    │ ████████████░░░░░░░  60% pass   │
    └─────────────────────────────────┘
    """
```

## Error Messages

### Structure Template

```
[ICON] [ERROR_TYPE]: [BRIEF_DESCRIPTION]

[DETAILED_EXPLANATION]

💡 Suggested Actions:
1. [IMMEDIATE_ACTION]
2. [ALTERNATIVE_ACTION]
3. [HELP_RESOURCE]

📚 Learn more: [DOCUMENTATION_LINK]
```

### Common Error Scenarios

#### API Key Not Found

**Current:**

```
Error: OPENAI_API_KEY not set
```

**Improved:**

```
❌ Configuration Error: API key not found

Nova requires an OpenAI or Anthropic API key to function.

💡 Suggested Actions:
1. Set environment variable:
   export OPENAI_API_KEY="sk-..."

2. Create a .env file:
   echo 'OPENAI_API_KEY=sk-...' > .env

3. Pass via command line:
   nova fix . --api-key sk-...

📚 Learn more: https://docs.nova.ai/setup#api-keys
```

#### Test Discovery Failed

**Current:**

```
No tests found
```

**Improved:**

```
⚠️ Test Discovery Failed: No tests found in current directory

Nova couldn't locate any test files using pytest discovery.

💡 Suggested Actions:
1. Verify test files follow naming convention:
   - test_*.py or *_test.py
   - Located in tests/ directory

2. Check pytest configuration:
   pytest --collect-only

3. Specify test directory explicitly:
   nova fix . --test-dir tests/

📚 Learn more: https://docs.nova.ai/troubleshooting#test-discovery
```

#### Timeout Reached

**Current:**

```
Timeout: 300 seconds exceeded
```

**Improved:**

```
⏰ Timeout Reached: Execution stopped after 300 seconds

Nova couldn't fix all tests within the time limit.

📊 Progress when stopped:
- Tests fixed: 2/5
- Iterations completed: 3/6
- Last action: Analyzing test_complex.py

💡 Suggested Actions:
1. Increase timeout for complex fixes:
   nova fix . --timeout 600

2. Focus on specific test files:
   nova fix . --test-file tests/test_simple.py

3. Review partial fixes:
   cat .nova/latest/diffs/*.patch

📚 Learn more: https://docs.nova.ai/configuration#timeouts
```

#### Patch Application Failed

**Current:**

```
Failed to apply patch
```

**Improved:**

````
🚫 Patch Application Failed: Merge conflict detected

The generated patch conflicts with existing code.

📄 Conflicting file: src/calculator.py
   Lines: 45-52

   Expected:
   ```python
   def divide(a, b):
       return a / b
````

Found:

```python
def divide(a, b):
    # TODO: Add zero check
    return a / b
```

💡 Suggested Actions:

1. Ensure working directory is clean:
   git status

2. Reset and try again:
   git reset --hard HEAD
   nova fix .

3. Apply patch manually:
   cat .nova/latest/diffs/step-1.patch | git apply

📚 Learn more: https://docs.nova.ai/troubleshooting#patch-conflicts

```

#### Safety Limit Exceeded

**Current:**
```

Safety limit exceeded: too many changes

```

**Improved:**
```

🛡️ Safety Limit Exceeded: Proposed changes too large

Nova's safety system prevented a patch that would modify:

- Files: 15 (limit: 10)
- Lines: 347 (limit: 200)

This protects against unintended large-scale changes.

📊 Proposed changes breakdown:

- src/core/\*.py: 12 files, 289 lines
- src/utils/\*.py: 3 files, 58 lines

💡 Suggested Actions:

1. Review and increase limits if appropriate:
   nova fix . --max-lines 500 --max-files 20

2. Focus on specific modules:
   nova fix . --path src/utils/

3. Apply changes incrementally:
   nova fix . --incremental

⚠️ Warning: Large changes should be carefully reviewed

📚 Learn more: https://docs.nova.ai/safety#limits

````

## Interactive Prompts

### Confirmation Prompts

```python
# When changes are significant
def confirm_large_changes():
    """
    ⚠️ Large Change Detected

    Nova wants to modify 8 files with 156 line changes.

    Files to be modified:
    • src/calculator.py (45 lines)
    • src/utils.py (23 lines)
    • src/helpers.py (18 lines)
    • [+5 more files]

    Do you want to:
    [V]iew changes  [A]pply all  [S]elect files  [C]ancel
    > _
    """

# When fixes partially succeed
def handle_partial_success():
    """
    ⚡ Partial Success: 3/5 tests fixed

    Fixed:
    ✅ test_calculator.py::test_divide
    ✅ test_calculator.py::test_multiply
    ✅ test_calculator.py::test_subtract

    Still failing:
    ❌ test_calculator.py::test_power (complex logic)
    ❌ test_calculator.py::test_sqrt (missing import)

    Options:
    [C]ontinue trying  [K]eep partial fix  [R]evert all  [M]anual mode
    > _
    """
````

### Help System

```bash
# Contextual help
$ nova fix --help

Nova CI-Rescue - Automated Test Fixing

USAGE:
    nova fix [PATH] [OPTIONS]

EXAMPLES:
    nova fix .                    # Fix tests in current directory
    nova fix . --max-iters 3      # Limit to 3 attempts
    nova fix . --dry-run          # Preview without applying

OPTIONS:
    --max-iters NUM    Maximum fix attempts (default: 6)
    --timeout SECS     Time limit in seconds (default: 1200)
    --config FILE      Configuration file path
    --dry-run         Preview changes without applying
    --verbose         Show detailed progress
    --help            Show this help message

COMMON ISSUES:
    Tests not found?     Try: nova fix . --test-dir tests/
    Taking too long?     Try: nova fix . --timeout 600
    Too many changes?    Try: nova fix . --max-lines 100

MORE HELP:
    Docs:     https://docs.nova.ai
    Discord:  https://discord.gg/nova
    Examples: nova examples
```

## Visual Enhancements

### Color Coding

```python
# Status colors
SUCCESS = "\033[92m"  # Green
WARNING = "\033[93m"  # Yellow
ERROR = "\033[91m"    # Red
INFO = "\033[94m"     # Blue
BOLD = "\033[1m"      # Bold
RESET = "\033[0m"     # Reset

# Usage
print(f"{SUCCESS}✅ Test passed{RESET}")
print(f"{ERROR}❌ Test failed{RESET}")
print(f"{WARNING}⚠️ Warning: Large change{RESET}")
print(f"{INFO}ℹ️ Info: Using GPT-4{RESET}")
```

### Icons and Symbols

```python
ICONS = {
    'success': '✅',
    'failure': '❌',
    'warning': '⚠️',
    'info': 'ℹ️',
    'working': '🔄',
    'thinking': '🤔',
    'planning': '🧠',
    'fixing': '🔧',
    'testing': '🧪',
    'complete': '✨',
    'rocket': '🚀',
    'clock': '⏰',
    'shield': '🛡️',
    'lightbulb': '💡',
    'book': '📚',
    'folder': '📁',
    'chart': '📊',
    'page': '📄',
    'clipboard': '📋'
}
```

### Formatted Output Tables

```python
def show_results_table():
    """
    ┌─────────────────────────────────────────────────────┐
    │                  Nova Fix Results                   │
    ├──────────────────────┬──────────────────────────────┤
    │ Metric               │ Value                        │
    ├──────────────────────┼──────────────────────────────┤
    │ Tests Fixed          │ 5/7 (71%)                    │
    │ Iterations Used      │ 3                            │
    │ Time Taken           │ 1m 23s                       │
    │ Files Modified       │ 3                            │
    │ Lines Changed        │ +42 -18                      │
    │ Model Used           │ gpt-4                        │
    │ API Cost (estimate)  │ $0.08                        │
    └──────────────────────┴──────────────────────────────┘
    """
```

## Command Shortcuts

### Aliases and Shortcuts

```bash
# Common operations as shortcuts
nova f     → nova fix
nova e     → nova eval
nova s     → nova status
nova r     → nova reset
nova h     → nova history

# Quick commands
nova quick   → nova fix . --max-iters 2 --timeout 120
nova safe    → nova fix . --dry-run --verbose
nova full    → nova fix . --max-iters 6 --timeout 600
nova focused → nova fix . --test-file {auto-detect-failing}
```

### Smart Defaults

```python
# Detect and suggest appropriate settings
def suggest_configuration(test_count, failure_count, complexity):
    if failure_count == 1 and complexity == "simple":
        return "nova quick"  # Fast mode for simple fixes
    elif failure_count > 5:
        return "nova full"   # Thorough mode for many failures
    elif complexity == "complex":
        return "nova safe"   # Careful mode for complex code
    else:
        return "nova fix"    # Standard mode
```

## Exit Codes and Scripts

### Meaningful Exit Codes

```python
EXIT_CODES = {
    0: "Success - All tests fixed",
    1: "Partial success - Some tests fixed",
    2: "No fixes - Unable to fix any tests",
    3: "Configuration error",
    4: "Timeout reached",
    5: "Safety limit exceeded",
    6: "User cancelled",
    7: "Environment error (missing deps)",
    8: "API error (key, rate limit)",
    9: "Unknown error"
}

# Usage in scripts
nova fix . || handle_exit_code $?
```

### Script-Friendly Output

```bash
# Machine-readable output
$ nova fix . --output json
{
  "success": true,
  "tests_fixed": 3,
  "tests_total": 3,
  "iterations": 2,
  "duration_seconds": 42,
  "files_changed": ["calculator.py"],
  "lines_added": 15,
  "lines_removed": 3
}

# Quiet mode for scripts
$ nova fix . --quiet
3/3 fixed in 42s

# Parse-friendly format
$ nova fix . --format csv
success,tests_fixed,tests_total,iterations,duration
true,3,3,2,42
```

## Accessibility Features

### Screen Reader Support

```python
# Provide text alternatives for icons
def format_for_screen_reader(icon_text):
    if SCREEN_READER_MODE:
        return icon_text.replace('✅', '[SUCCESS]')
                        .replace('❌', '[FAILURE]')
                        .replace('⚠️', '[WARNING]')
    return icon_text
```

### High Contrast Mode

```python
# Option for no colors/simple output
$ nova fix . --no-color
[INFO] Nova CI-Rescue v1.0 starting...
[INFO] Found 3 failing tests
[WORKING] Iteration 1/3...
[SUCCESS] Fixed test_divide
[WORKING] Iteration 2/3...
[SUCCESS] Fixed test_power
[COMPLETE] All tests fixed in 42 seconds
```

### Keyboard Navigation

```python
# Interactive mode with keyboard shortcuts
def interactive_mode():
    """
    Nova Interactive Mode
    =====================
    [R]un fix  [D]ry run  [C]onfig  [H]istory  [Q]uit

    Use arrow keys to navigate, Enter to select
    Press 'h' for help at any time
    """
```

## Summary

Good UX in CLI tools means:

1. **Clear, actionable error messages** with suggested fixes
2. **Progressive detail levels** (minimal → verbose → debug)
3. **Visual hierarchy** using colors, icons, and formatting
4. **Smart defaults** with easy overrides
5. **Script-friendly output** options
6. **Accessibility** considerations

These improvements make Nova CI-Rescue more approachable for new users while maintaining power-user efficiency.
