# Nova CI-Rescue — Demo Script

## Pre-Demo Setup

### 1. Prepare Demo Repository

```bash
# Clone the demo template
git clone https://github.com/nova-solve/demo-failing-tests
cd demo-failing-tests

# Verify tests are failing
pytest
# Expected: 3 failures, 7 passed
```

### 2. Environment Check

```bash
# Verify Nova is installed
nova --version

# Verify API key is set
echo $OPENAI_API_KEY | cut -c1-10
# Should show: sk-proj-xx
```

## Live Demo Flow

### 1. Show the Problem (30 seconds)

```bash
# Run tests to show failures
pytest --tb=short

# Highlight the failures
echo "❌ 3 tests failing - blocking our deployment"
```

### 2. Run Nova Fix (2-3 minutes)

```bash
# Start the fix
nova fix . --max-iters 3

# While running, explain:
# - "Nova is analyzing the failures"
# - "It's generating targeted fixes"
# - "Each iteration learns from the previous"
```

### 3. Show Success (30 seconds)

```bash
# Tests should now pass
pytest
# Expected: 10 passed, 0 failed

echo "✅ All tests green - ready to ship!"
```

### 4. Inspect the Changes (1 minute)

```bash
# Show what Nova changed
git diff

# Show the artifacts
ls -la .nova/*/
cat .nova/*/diffs/step-1.patch
```

### 5. GitHub Action Demo (1 minute)

```bash
# Push to trigger Action
git add -A
git commit -m "Fix failing tests with Nova"
git push origin nova-fix-demo

# Open browser to GitHub
# Show the Action running
# Point out the PR comment with metrics
```

## Key Talking Points

### During Setup

- "This is a real Python project with actual test failures"
- "No pre-scripting - Nova will figure this out live"

### During Fix

- "Notice how Nova preserves the original logic"
- "It's not just pattern matching - it understands the intent"
- "Each iteration builds on learnings"

### After Success

- "From red to green in under 3 minutes"
- "Full audit trail in .nova directory"
- "Can be integrated into any CI pipeline"

## Screenshot Moments

Capture these for social proof:

1. ❌ Initial failing tests (terminal)
2. 🔄 Nova running (terminal with progress)
3. ✅ Green tests (terminal)
4. 📊 PR comment with metrics (GitHub)
5. 🎯 Git diff showing the fix (terminal or GitHub)

## Handling Questions

### "What if it doesn't fix it?"

"Nova respects the max-iterations limit. If it can't fix within bounds, it reports what it learned for human review."

### "How much does this cost?"

"This demo run cost about $0.05. A typical fix is under $0.10."

### "Does it work with [framework]?"

"Nova works with any Python test framework. We're adding JS/TS support next quarter."

### "Is my code secure?"

"Your code never leaves your infrastructure. API calls only send relevant context, not your entire codebase."

## Post-Demo

### Share Links

- Demo repository: [github.com/nova-solve/demo-failing-tests]
- Live recording: [Record with Loom]
- Documentation: [Your Slite docs]

### Call to Action

"Try it yourself - first 100 fixes are free:

````bash
pipx run nova-solve
```"

## Backup Plan

If live demo fails:
1. Switch to pre-recorded Loom video
2. Show screenshots of successful run
3. Walk through the .nova artifacts from a previous run
4. Emphasize "even Nova has bad days - but it learns from them"
````
