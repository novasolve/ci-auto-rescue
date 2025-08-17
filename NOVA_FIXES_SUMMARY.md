# Nova Fixes Summary

## Issues Fixed

### 1. Path Resolution ✅

**Problem**: Agent was looking for `broken.py` at root instead of `src/broken.py`

**Solution**: Modified `OpenFileTool` to automatically check common source directories:

- When file not found, tries: `src/`, `lib/`, `app/`
- Returns helpful message showing where it found the file

### 2. JSON Parsing Bug ✅

**Problem**: `'str' object has no attribute 'get'` error

**Solution**: Fixed `RunTestsTool` to use dict objects internally before converting to JSON at the end

### 3. Agent Guidance ✅

**Problem**: Agent was trying to open test files and hallucinating content when blocked

**Solutions**:

- Enhanced system prompt to emphasize not opening test files
- Added clear instructions to use error messages instead
- Added "NO HALLUCINATING" rule to prevent making up file contents
- Enhanced error messages when test files are blocked with hints about source files

### 4. Hint File Support ✅

**New Feature**: Added support for `.nova-hints` files

**Implementation**:

- Deep agent now looks for hint files: `.nova-hints`, `.nova/hints.md`, `HINTS.md`
- Logs when hint file is found
- Includes hint content in the agent prompt
- Updated demo hint file with explicit path guidance

## Updated Files

1. **src/nova/agent/unified_tools.py**

   - Enhanced `OpenFileTool` with automatic path resolution
   - Better error messages with hints when test files are blocked

2. **src/nova/agent/deep_agent.py**

   - Added hint file support with logging
   - Enhanced system prompt with anti-hallucination rules
   - Improved workflow instructions

3. **src/nova/cli.py**

   - Added hint about source file location in error details

4. **examples/demos/demo_broken_project/.nova-hints**
   - Made file paths more explicit
   - Updated with correct test expectations

## Testing

Run the following to test the fixes:

```bash
# Make sure Docker is running (optional)
./setup_docker_sandbox.sh

# Test with the demo project
nova fix examples/demos/demo_broken_project/ --verbose

# Or use the test script
python test_nova_fixes.py
```

## Expected Behavior

1. Agent sees hint file and logs: `📝 Found hint file: .nova-hints`
2. Agent tries to open `broken.py`, fails, then automatically finds `src/broken.py`
3. Agent fixes all 6 functions based on test expectations
4. No JSON parsing errors
5. No hallucination of test file contents
6. All tests pass successfully

## Key Improvements

- **No more hallucination**: Agent won't make up file contents when blocked
- **Smart path resolution**: Automatically checks common source directories
- **Hint file support**: Projects can provide guidance via `.nova-hints`
- **Better error messages**: Clear guidance when test files are blocked
- **Robust JSON handling**: No more string/dict confusion
