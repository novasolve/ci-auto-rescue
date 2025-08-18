# Summary: Why Nova Agent Can't Run Tests

## The Problem

The Nova agent is **hallucinating fake tool responses** instead of actually running the tools. When it tries to use tools, it's making up error messages that don't exist:

- `"ERROR: Access to run_tests is blocked in this environment."` ← **This is made up!**
- `"ERROR: Access to src/broken.py is blocked."` ← **This is also made up!**

## Why This Happens

1. **GPT-5 ReAct Mode**: The agent runs in text-based ReAct mode for GPT-5
2. **Text Generation**: In ReAct, the model generates chains like:
   ```
   Thought: I need to run tests
   Action: run_tests
   Action Input:
   Observation: [SHOULD WAIT FOR REAL RESPONSE HERE]
   ```
3. **The Bug**: Instead of stopping after "Action Input:" and waiting for the real tool response, GPT-5 is continuing to generate fake "Observation:" lines

## What I Fixed

I've added multiple safeguards:

### 1. **Explicit Instructions** (line 373-374):

```python
"- CRITICAL: Do NOT generate 'Observation:' lines - wait for actual tool responses"
"- After 'Action Input:', STOP and wait for the tool to run"
```

### 2. **Format Instructions in Suffix** (line 563):

```
"IMPORTANT: Generate ONLY 'Thought:', 'Action:', and 'Action Input:'.
Do NOT generate 'Observation:' - the system will provide real observations"
```

### 3. **Parser Fix** (lines 69-74):

The parser now detects and removes any hallucinated observations

### 4. **Clear Format Guide** (lines 689-696):

Added explicit ReAct format example showing where to STOP

## Expected Behavior After Fix

The agent should now:

1. Generate: `Thought: I need to open the source file`
2. Generate: `Action: open_file`
3. Generate: `Action Input: src/broken.py`
4. **STOP and wait for real tool response**
5. Get actual response: `# Note: Found file at src/broken.py\n[file contents]`
6. Continue with next action

## Test It

Run Nova again:

```bash
nova fix examples/demos/demo_broken_project/ --verbose
```

The agent should:

- ✅ Actually run the `run_tests` tool (returns JSON)
- ✅ Actually try to open `src/broken.py` (finds it with path resolution)
- ✅ Fix the code based on real file contents
- ✅ Not hallucinate any fake error messages
