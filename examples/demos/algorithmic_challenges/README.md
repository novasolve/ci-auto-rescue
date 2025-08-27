# Algorithmic Challenges Demo for Nova CI-Rescue

This demo showcases Nova's ability to fix complex algorithmic bugs that require deep understanding of computer science concepts.

## What's Included

The demo includes intentionally broken implementations of classic algorithms:

1. **Kadane's Algorithm** - Maximum subarray sum
   - Bug: Doesn't handle all-negative arrays correctly
2. **Longest Increasing Subsequence (LIS)** - Dynamic programming
   - Bug: Off-by-one error in DP recurrence relation
3. **Dijkstra's Shortest Path** - Graph algorithm
   - Bug: Path reconstruction returns reversed path
4. **Merge Intervals** - Array manipulation
   - Bugs: Missing sort, wrong overlap condition
5. **3Sum Problem** - Two-pointer technique
   - Bug: Duplicate handling issues
6. **0/1 Knapsack** - Dynamic programming
   - Bugs: Wrong DP table dimensions and indices
7. **Topological Sort** - Graph algorithm (Kahn's)
   - Bug: No cycle detection
8. **Coin Change** - Dynamic programming
   - Bugs: Array indexing errors

## Running the Demo

```bash
# Make sure you have an API key set
export OPENAI_API_KEY=sk-...

# Run the demo script
./demo-algorithmic.sh
```

## What Nova Will Fix

Nova will analyze the failing tests and fix each algorithm:

- **Kadane's**: Initialize `max_current` and `max_global` to `nums[0]` instead of 0
- **LIS**: Add 1 to `dp[j]` in the recurrence: `dp[i] = max(dp[i], dp[j] + 1)`
- **Dijkstra**: Reverse the path before returning
- **Merge Intervals**: Sort intervals first, fix overlap check to use `<=`
- **3Sum**: Add duplicate skipping logic for all pointers
- **Knapsack**: Fix DP table to size `(n+1) x (capacity+1)`, fix indices
- **Topological Sort**: Check if all courses are included (cycle detection)
- **Coin Change**: Fix array size to `amount + 1`, fix loop bounds and return index

## Key Insights

This demo illustrates that Nova can:

1. **Understand algorithmic correctness** - Not just syntax errors
2. **Fix multiple related bugs** - In a single iteration
3. **Maintain algorithm efficiency** - Fixes don't degrade time complexity
4. **Preserve code style** - Fixes blend seamlessly with existing code
5. **Handle edge cases** - Like empty arrays, negative numbers, cycles

## CI Integration

The demo includes a GitHub Actions workflow (`auto-fix-ci.yml`) that:

- Runs tests on every PR
- Automatically invokes Nova when tests fail
- Creates a fix PR with all corrections
- Comments on the original PR with status

This demonstrates how Nova can be integrated into your CI/CD pipeline for automatic test fixing.
