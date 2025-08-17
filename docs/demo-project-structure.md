# Demo Project Structure Guide

## demo_broken_project Structure

The `demo_broken_project` has the following structure:

```
examples/demos/demo_broken_project/
├── src/                    # Source code directory
│   ├── broken.py          # The main source file with functions to fix
│   └── fixed.py           # Reference implementation (for testing)
├── tests/                 # Test directory
│   ├── test_broken.py     # Tests for broken.py
│   └── test_fixed.py      # Tests for fixed.py
└── telemetry/             # Nova execution logs
```

## Important Notes for Nova Agent

1. **Source files are in `src/` directory** - When looking for implementation files like `broken.py`, check the `src/` subdirectory
2. **Test files are protected** - Nova cannot modify files in `tests/` or files matching `test_*.py`
3. **The main file to fix is `src/broken.py`** - This contains the implementations that need fixing

## Common File Not Found Fix

If the agent reports "File not found: broken.py", it should try:

- `src/broken.py` (correct path)
- NOT just `broken.py` (incorrect path)

## Functions in broken.py

The following functions need to be fixed:

- `divide_numbers` - Handle division by zero
- `concatenate_strings` - Add proper spacing
- `calculate_average` - Use float division
- `get_first_char` - Handle empty strings
- `sort_list` - Sort the list correctly
