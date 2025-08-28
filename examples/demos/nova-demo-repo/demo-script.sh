#!/bin/bash

# Nova CI-Rescue Demo Script
# This script demonstrates the full workflow of Nova fixing broken tests

set -e

echo "🎯 Nova CI-Rescue Live Demo"
echo "==========================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Show initial working state
echo -e "${GREEN}Step 1: Initial Working State${NC}"
echo "Running tests on the clean codebase..."
echo ""

# Install dependencies if needed
pip install -q -r requirements.txt

# Run initial tests
pytest -v
echo ""
echo -e "${GREEN}✅ All tests pass! The codebase is healthy.${NC}"
echo ""
read -p "Press Enter to continue to Step 2..."

# Step 2: Apply breaking changes
echo ""
echo -e "${YELLOW}Step 2: Simulating a Bad PR${NC}"
echo "A developer submits a PR with 'performance optimizations'..."
echo ""

# Show what changes will be applied
echo "Changes in the PR:"
cat breaking-changes.patch | grep -E "^[-+]" | grep -v "^[-+]{3}" || true
echo ""

# Apply the patch
git apply breaking-changes.patch
echo -e "${YELLOW}📝 Breaking changes applied${NC}"
echo ""
read -p "Press Enter to see the test failures..."

# Step 3: Run tests again (they should fail)
echo ""
echo -e "${RED}Step 3: Tests After Bad PR${NC}"
echo "Running tests again..."
echo ""

set +e  # Don't exit on test failure
pytest -v
TEST_RESULT=$?
set -e

if [ $TEST_RESULT -ne 0 ]; then
    echo ""
    echo -e "${RED}❌ Tests are failing! The pipeline is broken!${NC}"
    echo ""
    
    # Show which tests failed
    echo "Failed tests:"
    pytest -v 2>&1 | grep FAILED || true
else
    echo "Unexpected: tests should have failed!"
    exit 1
fi

echo ""
read -p "Press Enter to run Nova CI-Rescue..."

# Step 4: Run Nova to fix the issues
echo ""
echo -e "${GREEN}Step 4: Nova CI-Rescue to the Rescue!${NC}"
echo "🤖 Running Nova to automatically fix the failing tests..."
echo ""

# Check if Nova is available
if command -v nova &> /dev/null; then
    nova fix . --max-iters 3
else
    # Try to run from parent directory
    cd ..
    PYTHONPATH=./src python -m nova.cli fix nova-demo-repo --max-iters 3
    cd nova-demo-repo
fi

echo ""
echo -e "${GREEN}✅ Nova has fixed the issues!${NC}"
echo ""

# Step 5: Show the fixes
echo -e "${GREEN}Step 5: Reviewing Nova's Fixes${NC}"
echo "Let's see what Nova changed:"
echo ""

# Show the diff
git diff --stat
echo ""
git diff src/calculator.py | head -30
echo ""

read -p "Press Enter to run the tests again..."

# Step 6: Run tests one more time
echo ""
echo -e "${GREEN}Step 6: Final Test Run${NC}"
echo "Running tests after Nova's fixes..."
echo ""

pytest -v
echo ""
echo -e "${GREEN}🎉 All tests pass again! Nova saved the day!${NC}"
echo ""

# Summary
echo "📊 Demo Summary"
echo "==============="
echo "1. ✅ Started with working code and passing tests"
echo "2. ❌ Bad PR introduced multiple bugs"
echo "3. 🤖 Nova automatically detected and fixed all issues"
echo "4. ✅ Pipeline is green again - no human intervention needed!"
echo ""
echo "In a real CI/CD pipeline, this would happen automatically via GitHub Actions."
echo "Check out .github/workflows/ci.yml to see the integration!"
echo ""

# Optional: Show the Nova branch
if git branch | grep -q "nova-fix"; then
    echo "Nova created a fix branch:"
    git branch | grep "nova-fix"
    echo ""
    echo "In a real scenario, this would create a PR for review."
fi
