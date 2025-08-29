#!/bin/bash

# Nova CI-Rescue Complete Demo Script
# This script demonstrates the entire end-to-end workflow

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Ensure we're in the nova-demo-repo directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Demo configuration
REPO_URL="https://github.com/novasolve/nova-ci-rescue-demo"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BRANCH_NAME="bugfix/calculator-optimization-$TIMESTAMP"

clear
echo -e "${BOLD}🎯 Nova CI-Rescue Complete Demo${NC}"
echo -e "${BOLD}================================${NC}"
echo ""
echo "This demo shows how Nova automatically fixes failing tests in a CI/CD pipeline."
echo ""
echo -e "Repository: ${BLUE}$REPO_URL${NC}"
echo ""
read -p "Press Enter to start the demo..."

# Step 1: Clone the repository
echo ""
echo -e "${BOLD}Step 1: Clone the Demo Repository${NC}"
echo -e "${YELLOW}$ git clone $REPO_URL${NC}"
if [ -d "nova-ci-rescue-demo" ]; then
    rm -rf nova-ci-rescue-demo
fi
git clone $REPO_URL
cd nova-ci-rescue-demo
echo ""

# Step 2: Show initial working state
echo -e "${BOLD}Step 2: Verify Initial Tests Pass${NC}"
echo -e "${YELLOW}$ python -m pip install -r requirements.txt${NC}"
python -m pip install -q -r requirements.txt
echo ""
echo -e "${YELLOW}$ pytest -v tests/${NC}"
pytest -v tests/
echo ""
echo -e "${GREEN}✅ All tests pass! The codebase is healthy.${NC}"
echo ""
read -p "Press Enter to continue..."

# Step 3: Create a feature branch
echo ""
echo -e "${BOLD}Step 3: Create a Feature Branch${NC}"
# Clean up any existing branches from previous runs
if git show-ref --verify --quiet refs/heads/demo/latest; then
  git checkout demo/latest 2>/dev/null || git switch demo/latest 2>/dev/null || true
else
  git checkout main 2>/dev/null || true
fi
git branch -D $BRANCH_NAME 2>/dev/null || true
echo -e "${YELLOW}$ git checkout -b $BRANCH_NAME${NC}"
git checkout -b $BRANCH_NAME
echo ""

# Step 4: Apply breaking changes
echo -e "${BOLD}Step 4: Apply 'Performance Optimizations' (Breaking Changes)${NC}"
echo ""
echo "A developer wants to 'optimize' the calculator..."
echo ""
echo -e "${YELLOW}$ git apply breaking-changes.patch${NC}"
git apply breaking-changes.patch
echo ""
echo "Changes applied:"
echo -e "${YELLOW}$ git diff --stat${NC}"
git diff --stat
echo ""
read -p "Press Enter to see the specific changes..."
echo ""
echo -e "${YELLOW}$ git diff src/calculator.py | head -30${NC}"
git diff src/calculator.py | head -30
echo ""
read -p "Press Enter to commit and push these changes..."

# Step 5: Commit and push
echo ""
echo -e "${BOLD}Step 5: Commit and Push the Changes${NC}"
echo -e "${YELLOW}$ git add -A${NC}"
git add -A
echo -e "${YELLOW}$ git commit -m 'feat: optimize calculator performance'${NC}"
git commit -m "feat: optimize calculator performance

- Improved addition algorithm
- Simplified subtraction logic  
- Removed unnecessary error checks
- Performance improvements"
echo ""
echo -e "${YELLOW}$ git push origin $BRANCH_NAME${NC}"
git push origin $BRANCH_NAME
echo ""

# Step 6: Create PR
echo -e "${BOLD}Step 6: Create Pull Request${NC}"
echo ""
echo "Creating a PR for our 'optimizations'..."
echo -e "${YELLOW}$ gh pr create${NC}"

# Create PR using GitHub CLI
PR_URL=$(gh pr create \
    --title "feat: Optimize calculator performance" \
    --body "## Summary
This PR optimizes the calculator module for better performance.

## Changes
- 🚀 Faster addition algorithm
- ⚡ Simplified subtraction logic
- 🎯 Removed redundant error checks
- 📈 Overall performance improvements

All changes are backward compatible." \
    --base demo/latest \
    --head $BRANCH_NAME)

echo ""
echo -e "${GREEN}✅ Pull Request created!${NC}"
echo -e "URL: ${BLUE}$PR_URL${NC}"
echo ""
read -p "Press Enter to check CI status..."

# Step 7: Watch CI fail
echo ""
echo -e "${BOLD}Step 7: CI Pipeline Running...${NC}"
echo ""
echo "GitHub Actions is now running tests on the PR..."
echo ""

# Wait for CI to start
echo -n "Waiting for CI to start"
for i in {1..10}; do
    echo -n "."
    sleep 1
done
echo ""

# Check PR status
echo -e "${YELLOW}$ gh pr checks${NC}"
gh pr checks || true
echo ""
echo -e "${RED}❌ CI Failed! Tests are not passing.${NC}"
echo ""
echo "Failed tests:"
echo "- test_subtraction"
echo "- test_division_by_zero" 
echo "- test_square_root_negative"
echo "- test_average_empty_list"
echo ""
read -p "Press Enter to see Nova CI-Rescue in action..."

# Step 8: Nova fixes (simulated locally for demo)
echo ""
echo -e "${BOLD}Step 8: Nova CI-Rescue Activates${NC}"
echo ""
echo -e "${BLUE}🤖 Nova detected failing tests and is analyzing the issues...${NC}"
echo ""

# Simulate Nova's output
cat << 'EOF'
[Nova] ❌ Detected failing tests:
       - tests/test_calculator.py::test_subtraction
       - tests/test_calculator.py::test_division_by_zero
       - tests/test_calculator.py::test_square_root_negative
       - tests/test_calculator.py::test_average_empty_list

[Nova] 🔍 Analyzing failures...
       - subtract(7, 3) returns 10 (expected 4) - using addition instead
       - divide(10, 0) raises no error - missing zero check
       - square_root(-4) raises no error - missing negative check
       - average([]) raises ZeroDivisionError - missing empty check

[Nova] 🧠 Using GPT-5 with reasoning_effort='high' to generate fixes...

[Nova] 🔧 Applying fixes:
       ✓ Fixed subtract() to use subtraction operator
       ✓ Added zero check in divide()
       ✓ Added negative check in square_root()  
       ✓ Added empty list check in average()

[Nova] ✅ All tests now pass!

[Nova] 📤 Creating fix branch: nova-fix-$(date +%Y%m%d-%H%M%S)
[Nova] 🎯 Opening Pull Request with AI-generated description...
EOF

echo ""
read -p "Press Enter to see Nova's PR..."

# Step 9: Show Nova's PR
echo ""
echo -e "${BOLD}Step 9: Nova's Fix Pull Request${NC}"
echo ""
echo -e "${GREEN}Nova created PR #2: 'Nova Fix: Correct calculator logic errors'${NC}"
echo ""
echo "PR Description:"
echo -e "${BLUE}---${NC}"
cat << 'EOF'
## Summary

This PR fixes multiple failing tests in the calculator module that were introduced
in PR #1. The issues were related to incorrect operators and missing error checks.

## What was fixed

### 1. Subtraction Logic
- **Problem**: The `subtract()` function was using addition (`+`) instead of subtraction (`-`)
- **Fix**: Changed operator from `a + b` to `a - b`
- **Impact**: `test_subtraction` now passes correctly

### 2. Division by Zero Check
- **Problem**: The `divide()` function had its zero check removed
- **Fix**: Restored the zero check with proper error handling
- **Impact**: `test_division_by_zero` now correctly raises ValueError

### 3. Square Root Negative Check
- **Problem**: The `square_root()` function was missing negative number validation
- **Fix**: Added check for negative inputs with appropriate error
- **Impact**: `test_square_root_negative` now passes

### 4. Average Empty List Check
- **Problem**: The `average()` function would crash on empty lists
- **Fix**: Added empty list validation
- **Impact**: `test_average_empty_list` now handles edge case properly

## Test Results

Before: 4 failing tests ❌
After: All tests passing ✅

## Technical Details

- Execution time: 42s
- Iterations needed: 1
- Files modified: `src/calculator.py`
- Reasoning effort: high (GPT-5)

---
*This PR was automatically generated by [Nova CI-Rescue](https://github.com/novasolve/ci-auto-rescue) 🤖*
EOF
echo -e "${BLUE}---${NC}"
echo ""

# Step 10: Final status
echo -e "${BOLD}Step 10: Final Status${NC}"
echo ""
echo -e "${GREEN}✅ Nova's PR has all checks passing!${NC}"
echo -e "${GREEN}✅ Ready for human review and merge${NC}"
echo ""
echo -e "${BOLD}Summary:${NC}"
echo "1. Developer created PR with bugs → Tests failed ❌"
echo "2. Nova detected failures → Analyzed with GPT-5 🤖"
echo "3. Nova fixed the code → Created fix PR 🔧"
echo "4. All tests now pass → Ready to merge ✅"
echo ""
echo -e "${BOLD}Time saved: ~15-30 minutes of debugging${NC}"
echo ""
echo -e "${GREEN}Demo completed successfully!${NC}"

# Cleanup
cd ..
echo ""
echo "To reset the demo, run:"
echo "  rm -rf nova-ci-rescue-demo"
echo ""
echo "To see the live repository:"
echo -e "  ${BLUE}$REPO_URL${NC}"
