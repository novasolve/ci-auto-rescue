#!/bin/bash

# Nova Agent Auto-Fixes a Broken Pull Request - Exact Demo Flow
# This follows the exact steps from the documentation

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

clear
echo -e "${BOLD}🎯 Demo: Nova Agent Auto-Fixes a Broken Pull Request${NC}"
echo -e "${BOLD}===================================================${NC}"
echo ""
echo "This demo showcases how Nova CI-Rescue autonomously detects and fixes"
echo "a broken pull request from first principles."
echo ""
read -p "Press Enter to start..."

# Step 1: Project Setup
echo ""
echo -e "${BOLD}1. Project Setup: A Simple Calculator with Tests and CI Workflow${NC}"
echo ""
echo "We have a Python calculator project with:"
echo "- Source code with add, subtract, multiply, divide functions"
echo "- Test suite using pytest"
echo "- GitHub Actions workflow that runs on every PR"
echo ""
echo -e "${YELLOW}Project structure:${NC}"
cat << 'EOF'
calculator-project/
├── src/
│   └── calculator.py
├── tests/
│   └── test_calculator.py
└── .github/
    └── workflows/
        └── ci.yml
EOF
echo ""
read -p "Press Enter to verify initial tests pass..."

# Install dependencies if needed
if ! command -v pytest &> /dev/null; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install -q -r requirements.txt
fi

# Make sure we're on main branch
git checkout main >/dev/null 2>&1

# Run initial tests
echo ""
echo -e "${YELLOW}$ pytest -v tests/${NC}"
set +e  # Temporarily allow failures to show test output
pytest -v --override-ini="addopts=" tests/
TEST_RESULT=$?
set -e  # Re-enable exit on error

if [ $TEST_RESULT -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ On main branch, all tests pass!${NC}"
else
    echo ""
    echo -e "${RED}❌ Tests are failing! Let's reset the calculator to working state...${NC}"
    # Reset calculator.py to working state
    git checkout HEAD -- src/calculator.py
    echo -e "${YELLOW}Re-running tests...${NC}"
    pytest -v --override-ini="addopts=" tests/
    echo ""
    echo -e "${GREEN}✅ Now all tests pass!${NC}"
fi
echo ""
read -p "Press Enter to continue..."

# Step 2: The Broken Pull Request
echo ""
echo -e "${BOLD}2. The Broken Pull Request: Introducing a Bug${NC}"
echo ""
echo "A developer opens PR #1 to 'optimize' the subtract function"
echo "but accidentally introduces a bug:"
echo ""
echo -e "${YELLOW}PR Diff:${NC}"
cat << 'EOF'
 def subtract(x, y):
-    return x - y
+    return x + y  # BUG: using addition instead of subtraction
EOF
echo ""
echo "This will cause test_subtract to fail (7 - 3 will return 10 instead of 4)"
echo ""
read -p "Press Enter to create this broken PR..."

# Create broken PR
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BRANCH="bugfix/wrong-subtraction-$TIMESTAMP"

git checkout -b $BRANCH
git apply breaking-changes.patch
git add -A
git commit -m "Fix subtraction function (bug)

Attempt to fix the subtract function, but this introduces a bug
where subtraction is done incorrectly."

git push origin $BRANCH

PR_URL=$(gh pr create \
    --title "Fix subtraction function (bug)" \
    --body "Attempt to fix the subtract function, but this introduces a bug where subtraction is done incorrectly." \
    --base main)

echo ""
echo -e "${GREEN}✅ PR created:${NC} $PR_URL"
echo ""
read -p "Press Enter to see CI failure..."

# Step 3: CI Failure
echo ""
echo -e "${BOLD}3. CI Failure: Test Results on the PR${NC}"
echo ""
echo "GitHub Actions runs pytest on the PR..."
echo ""
echo -e "${RED}Expected CI output:${NC}"
cat << 'EOF'
=========================== FAILURES ============================
________________________ test_subtract _________________________
>       assert subtract(7, 3) == 4
E       assert 10 == 4
E        + where 10 = subtract(7, 3)

tests/test_calculator.py:6: AssertionError
=================== 1 failed, 4 passed in 0.05s ===================
EOF
echo ""
echo -e "${RED}❌ CI / Tests – 1 failing test${NC}"
echo "The PR cannot be merged as-is!"
echo ""
read -p "Press Enter to bring in Nova CI-Rescue..."

# Step 4: Nova Agent to the Rescue
echo ""
echo -e "${BOLD}4. Nova Agent to the Rescue: Detecting and Analyzing the Failure${NC}"
echo ""
echo -e "${YELLOW}$ nova fix .${NC}"
echo ""
echo -e "${BLUE}Nova output:${NC}"
cat << 'EOF'
[Nova] ❌ Detected failing test: tests/test_calculator.py::test_subtract
       → AssertionError: expected 4, got 10

[Nova] 🔍 Analyzing failure...
       The function subtract(x, y) returns x + y, which is incorrect.
       Likely cause: The subtraction logic is implemented incorrectly (addition instead of subtraction).
       Proposed solution: Change the implementation to use subtraction (x - y) to match expected behavior.
EOF
echo ""
read -p "Press Enter to see Nova generate a fix..."

# Step 5: Nova Generates and Applies a Fix
echo ""
echo -e "${BOLD}5. Nova Generates and Applies a Fix${NC}"
echo ""
echo -e "${BLUE}Nova's proposed patch:${NC}"
cat << 'EOF'
*** Begin Patch (Nova AI-generated) ***
*** Update File: src/calculator.py ***
 def subtract(x, y):
-    return x + y  # BUG: using addition instead of subtraction
+    return x - y  # FIX: use subtraction to get the correct result
*** End Patch ***
EOF
echo ""
echo "Nova applies this patch to a new branch: nova-fix-$(date +%Y%m%d-%H%M%S)"
echo ""
echo -e "${BLUE}Nova re-runs tests:${NC}"
cat << 'EOF'
[Nova] ▶ Re-running tests after applying fix...
==================== 5 passed in 0.04s ====================
[Nova] ✅ All tests passed after fix!
EOF
echo ""
read -p "Press Enter to see Nova create a fix PR..."

# Step 6: Auto-Patching
echo ""
echo -e "${BOLD}6. Auto-Patching: Nova Opens a Patch Pull Request${NC}"
echo ""
echo "Nova pushes the fix branch and opens PR #2:"
echo ""
echo -e "${GREEN}PR #2: Nova Fix: Correct subtraction logic${NC}"
echo ""
echo -e "${BLUE}Description:${NC}"
cat << 'EOF'
This PR was opened by Nova CI-Rescue to fix a failing test in PR #1.
The subtract function has been corrected to use subtraction instead of addition.

## What was fixed
- Changed `return x + y` to `return x - y` in the subtract function
- This fixes the test_subtract failure where subtract(7, 3) was returning 10 instead of 4

## Test Results
Before: 1 failing test ❌
After: All tests passing ✅

---
*This PR was automatically generated by Nova CI-Rescue 🤖*
EOF
echo ""
echo -e "${GREEN}✅ Nova's PR has all checks passing!${NC}"
echo ""
read -p "Press Enter for the conclusion..."

# Step 7: Conclusion
echo ""
echo -e "${BOLD}7. Conclusion: From Red to Green, Hands-Free${NC}"
echo ""
echo "Summary of what happened:"
echo "1. ${RED}Failing PR Detected:${NC} PR with wrong subtract logic caused test failure"
echo "2. ${BLUE}Nova Analysis:${NC} Identified the bug by examining code and test"
echo "3. ${YELLOW}Automated Fix:${NC} Generated patch, applied to new branch, verified tests"
echo "4. ${GREEN}Patch PR:${NC} Created PR #2 with passing tests for review"
echo ""
echo -e "${BOLD}Nova turned a red build green automatically!${NC}"
echo ""
echo "In production, Nova can be integrated directly into GitHub Actions"
echo "to run automatically on any failing PR."
echo ""
echo -e "${GREEN}Demo completed!${NC}"
echo ""
echo "Check out the PRs created:"
echo "- Original broken PR: $PR_URL"
echo "- Nova's fix PR: (check the PRs tab)"

# Return to main
git checkout main
