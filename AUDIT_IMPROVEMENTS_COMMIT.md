feat: Implement deep agent audit recommendations for improved reliability

This commit implements the recommendations from the comprehensive audit of Nova's Deep Agent tools, focusing on:

## Enhanced Tool Reliability

### RunTestsTool Improvements
- Added configurable `use_docker` flag to respect NovaSettings.use_docker
- Added telemetry logger support for recording test execution events
- Enhanced error reporting with stderr output in Docker failures
- Added fallback event logging when sandbox is unavailable
- Improved error messages with contextual information

### ApplyPatchTool Improvements  
- Added comprehensive telemetry logging for all patch operations
- Added git commit validation to catch "nothing to commit" scenarios
- Enhanced state management with current_iteration increment
- Added detailed event logging for patch rejections and failures
- Improved verbose output with clear status indicators

### Tool Creation Updates
- Updated `create_default_tools` to accept and pass logger parameter
- Updated deep_agent.py to pass telemetry logger to tools
- Added use_docker setting propagation from NovaSettings

## Enforced Test Verification

### System Prompt Updates
- Added new core rule #6: "ALWAYS VERIFY FIXES" requiring tests after every change
- Updated workflow to mark test verification as MANDATORY
- Enhanced prompts to prevent agents from declaring success without running tests

### Agent Workflow Changes  
- Replaced "DETERMINISTIC MULTI-FAILURE FIX" with "VERIFIED INCREMENTAL FIXES"
- Changed from batch-all-then-test to test-after-each-change approach
- Added clear guidelines on acceptable vs unacceptable approaches
- Emphasized immediate verification after code changes

## Telemetry Improvements

### Event Logging
- `sandbox_fallback`: Logged when Docker unavailable with reason
- `test_run_completed`: Logged after each test execution with results
- `patch_rejected`: Logged for safety/critic rejections with reasons
- `patch_apply_failed`: Logged for apply failures with details
- `patch_applied`: Logged on success with lines changed count

## Benefits
1. **Better Debugging**: Rich telemetry events help diagnose agent behavior
2. **Increased Reliability**: Enforced test verification prevents false positives
3. **Improved Safety**: Better error handling and validation at each step
4. **Enhanced Transparency**: Detailed logging of all tool operations
5. **Flexible Configuration**: Respects user settings for Docker usage

## Testing
- Verified tool creation with logger parameters
- Confirmed logger attributes present on updated tools
- Tested Python compilation for syntax errors
- Maintained backward compatibility with existing interfaces

This implementation addresses the key issues identified in the audit while maintaining the existing API and improving the overall reliability of the Nova Deep Agent system.
