# Nova CI-Rescue Audit Report

Date: 2025-08-17
Auditor: Assistant

## Issue 1: File Resolution Bug (Agent Hallucination)

### Problem

When Nova agent encounters Python imports like `from broken import ...`, it incorrectly guesses the filename as `broken_module.py` instead of properly resolving the import to `src/broken.py`.

### Root Cause

The LLM agent lacks guidance on Python import resolution. The system prompt didn't include instructions on how to:

1. Check for `sys.path` modifications in test files
2. Resolve module imports to actual file paths
3. Common Python project structures (e.g., `src/` directories)

### Solution Applied

Enhanced the system prompt in `src/nova/agent/deep_agent.py` (line 379) to include explicit Python import resolution guidance:

```python
"6. **PYTHON IMPORTS**: When resolving Python imports:\n"
"   - Check test files for sys.path modifications (e.g., sys.path.insert)\n"
"   - If tests import 'from module_name import ...', look for:\n"
"     * module_name.py in the same directory\n"
"     * module_name.py in directories added to sys.path\n"
"     * module_name/__init__.py for packages\n"
"   - Common patterns: src/module_name.py, lib/module_name.py\n"
"   - NEVER guess filenames like 'module_name_module.py' or 'broken_module.py'\n\n"
```

This should prevent the agent from hallucinating incorrect filenames.

## Issue 2: Docker Sandbox Not Working

### Problem

Nova is designed to run tests in a Docker sandbox for isolation, but it's falling back to local execution with the warning: "⚠️ Sandbox unavailable – running tests without isolation."

### Root Cause Analysis

1. **Docker daemon not running**: The primary issue is that Docker daemon is not running on the system

   ```
   Cannot connect to the Docker daemon at unix:///Users/seb/.docker/run/docker.sock
   ```

2. **Docker image likely not built**: Even if Docker were running, the required image `nova-ci-rescue-sandbox:latest` needs to be built first

3. **Fallback mechanism working correctly**: The code properly falls back to local execution when Docker is unavailable

### Docker Setup Requirements

To enable Docker sandbox:

1. **Start Docker daemon**:

   - On macOS: Start Docker Desktop application
   - On Linux: `sudo systemctl start docker`

2. **Build the Docker image**:

   ```bash
   cd docker/
   ./build.sh
   ```

3. **Verify setup**:
   ```bash
   docker images | grep nova-ci-rescue-sandbox
   ```

### Security Implications

Running without Docker sandbox means:

- No memory limits (default: 512MB in Docker)
- No CPU limits (default: 1 CPU in Docker)
- No network isolation
- No process limits (default: 100 PIDs in Docker)
- Tests run with full access to the host system

## Recommendations

1. **For Issue 1**: The prompt enhancement should help, but consider also:

   - Adding a tool that can analyze Python imports and suggest file paths
   - Creating examples in the prompt showing common import patterns
   - Testing with various Python project structures

2. **For Issue 2**:

   - Add a setup check command that verifies Docker is installed and running
   - Improve error messages to guide users on Docker setup
   - Consider adding a `--no-docker` flag for intentional local execution
   - Document Docker requirements clearly in README

3. **Additional Improvements**:
   - Add a `nova doctor` command that checks system requirements
   - Include Docker setup in the quickstart guide
   - Log when falling back to local execution for audit trails

## Test Case for Verification

To verify the fixes work:

```bash
# 1. Start Docker (if not running)
# On macOS: Open Docker Desktop

# 2. Build the Docker image
cd docker/
./build.sh

# 3. Test Nova with the demo project
nova fix examples/demos/demo_broken_project/

# Expected: Should use Docker sandbox and correctly find src/broken.py
```
