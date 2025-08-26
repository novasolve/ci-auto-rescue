# Nova CI-Rescue Demo Examples

This directory contains various demo projects with intentionally broken code and failing tests. These are designed to test Nova CI-Rescue's ability to automatically fix different types of bugs.

## Demo Projects

### 1. **demo_math_ops/**
Mathematical operations with various arithmetic bugs:
- Off-by-one errors in addition
- Swapped operands in subtraction
- Wrong operators (+ instead of *)
- Missing edge case handling
- Incorrect algorithm implementations

### 2. **demo_string_ops/**
String manipulation functions with bugs:
- Character exclusion in string reversal
- Case sensitivity issues
- Missing character handling
- Wrong string methods
- Order preservation problems

### 3. **demo_data_structures/**
Common data structure implementations with bugs:
- Stack/Queue implementation errors
- Linked list traversal issues
- Binary search boundary problems
- Sorting algorithm bugs
- Collection manipulation errors

### 4. **demo_file_io/**
File I/O operations with various issues:
- Wrong file modes (read vs write)
- Missing error handling
- Binary vs text mode confusion
- Resource cleanup problems
- Path handling issues

### 5. **demo_exceptions/**
Exception handling demonstrations:
- Missing try/except blocks
- Wrong exception types
- Incomplete error handling
- Resource cleanup in finally blocks
- Custom exception problems

### 6. **demo_oop/**
Object-oriented programming bugs:
- Incorrect inheritance
- Property/method implementation errors
- Encapsulation violations
- Wrong method signatures
- State management issues

### 7. **demo_type_hints/**
Type annotation problems:
- Wrong return types
- Incorrect parameter types
- Missing Optional handling
- Union type issues
- Generic type problems

### 8. **demo_imports/**
Import-related issues:
- Missing imports
- Circular imports
- Wrong module imports
- Star import problems
- Import ordering issues

### 9. **demo_broken_project/**
A complete calculator project with multiple bugs:
- Arithmetic operation errors
- Memory management issues
- Missing error handling
- State management problems
- Edge case failures

### 10. **demo_llm_repo/**
Examples for testing LLM-based fixes (existing)

### 11. **demo_nova_test/**
Nova-specific test scenarios (existing)

### 12. **demo_test_repo/**
General test repository examples (existing)

## Running the Demos

To test Nova CI-Rescue on any demo:

```bash
# Navigate to a demo directory
cd demo_math_ops

# Run the tests to see failures
pytest

# Use Nova to fix the failing tests
nova fix

# Verify the fixes
pytest
```

## Expected Behavior

Each demo contains:
- Source code with intentional bugs
- Comprehensive test suites that will fail
- Comments indicating the bugs (marked with "BUG:")

Nova CI-Rescue should:
1. Detect all failing tests
2. Analyze the code and test expectations
3. Generate patches to fix the bugs
4. Apply the fixes
5. Verify all tests pass

## Adding New Demos

To add a new demo:
1. Create a new directory under `examples/demos/`
2. Add source files with intentional bugs
3. Write comprehensive tests that fail due to the bugs
4. Add comments to indicate what's wrong
5. Update this README with the new demo description

## Bug Categories Covered

- **Logic Errors**: Wrong algorithms, incorrect conditions
- **Type Errors**: Wrong types, missing conversions
- **Boundary Issues**: Off-by-one, edge cases
- **State Management**: Incorrect state updates
- **Error Handling**: Missing or wrong exception handling
- **Import Problems**: Missing or circular imports
- **Resource Management**: Leaks, cleanup issues
- **API Misuse**: Wrong method calls, incorrect parameters
