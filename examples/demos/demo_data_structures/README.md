# Demo Data Structures - Broken Implementation

This demo contains intentionally broken implementations of common data structures to test Nova's ability to fix failing tests.

## Running the Demo

To see the failing tests:
```bash
cd examples/demos/demo_data_structures
python -m pytest test_data_structures.py -v
```

To fix with Nova:
```bash
# From the repo root
nova fix examples/demos/demo_data_structures/
```

## Intentional Bugs

### Stack Implementation
1. `pop()` returns `None` instead of raising `IndexError` when empty
2. `peek()` accidentally modifies the stack by popping
3. `size()` has an off-by-one error

### Queue Implementation
1. `enqueue()` adds to front instead of rear (stack-like behavior)
2. `dequeue()` removes from rear instead of front
3. Wrong exception message ("Queue is full" instead of "Queue is empty")

### Function Bugs
1. `reverse_list()` creates a new list instead of modifying in place
2. `find_duplicates()` includes all items and returns a set instead of list

## Expected Behavior

After Nova fixes the bugs:
- All Stack operations should work correctly (LIFO)
- All Queue operations should work correctly (FIFO)
- `reverse_list()` should modify the list in place
- `find_duplicates()` should return only duplicated values as a list

## Files
- `data_structures.py` - The broken implementation
- `test_data_structures.py` - The test suite
- `.nova-hints` - Hints for Nova about the bugs
