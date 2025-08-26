# Loop Prevention Improvements from Old Development Branch

## Key Features to Implement

### 1. File Content Caching (from commit 4d8b63b)
- Cache file contents when opened to avoid re-reading
- Return cached content with SKIP message when file is re-opened
- Prevents agent confusion when operations are skipped

### 2. SKIP Message Prefix (from commit 3ac67f7)
Replace error/success messages with SKIP prefix:
- `ERROR: File already opened` → `SKIP: File already opened`
- `SUCCESS: File already up-to-date` → `SKIP: File already up-to-date`
- `SUCCESS: Patch already applied` → `SKIP: Patch already applied`
- `Plan already noted` → `SKIP: Plan already noted`

### 3. Clear Guidance Messages
When skipping operations, provide clear guidance:
```
SKIP: File '{path}' was already opened in this session.
Please refer to your previous observations above for the file content.
Continue with your next action using that information.
```

## Implementation Strategy for Current Codebase

### For src/nova/tools/fs.py:
1. Add file content caching mechanism
2. Track opened files per session
3. Return cached content with SKIP messages

### For src/nova/agent/state.py:
1. Add `used_actions` set to track operations
2. Add `modifications_count` to track changes
3. Add file cache dictionary

### For test runner and other tools:
1. Add duplicate operation detection
2. Return SKIP messages instead of re-running

## Example Implementation Pattern

```python
class FileOperationTool:
    def __init__(self):
        self._file_cache = {}
        self._used_actions = set()
        self._modifications_count = 0
    
    def open_file(self, path):
        cache_key = f"{path}_{self._modifications_count}"
        action_key = ('open_file', path, self._modifications_count)
        
        if action_key in self._used_actions:
            if cache_key in self._file_cache:
                return self._file_cache[cache_key]
            return f"SKIP: File '{path}' was already opened. Refer to previous observations."
        
        # Read file
        content = read_file_content(path)
        
        # Cache and track
        self._file_cache[cache_key] = content
        self._used_actions.add(action_key)
        
        return content
```

## Benefits
1. Prevents infinite loops when agent doesn't understand skip messages
2. Reduces redundant operations
3. Provides clear guidance to the agent
4. Maintains context through caching
