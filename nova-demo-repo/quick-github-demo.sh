#!/bin/bash

# Quick GitHub Demo - Shows Nova in action on GitHub
# This script creates a breaking PR and watches Nova fix it

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# Ensure we're in the nova-demo-repo directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BOLD}🚀 Quick Nova CI-Rescue GitHub Demo${NC}"
echo -e "${BOLD}===================================${NC}"
echo ""
echo "This demo creates a breaking PR and shows Nova fixing it automatically."
echo ""

# Check if we're in the right directory
if [ ! -f "breaking-changes.patch" ]; then
    echo -e "${RED}Error: Please run this script from the nova-ci-rescue-demo directory${NC}"
    exit 1
fi

# Check GitHub CLI
if ! command -v gh &> /dev/null; then
    echo -e "${RED}Error: GitHub CLI (gh) is required. Install it first.${NC}"
    exit 1
fi

echo -e "${GREEN}Prerequisites checked ✓${NC}"
echo ""
read -p "Press Enter to start..."

# Create unique branch name
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BRANCH="demo-break-$TIMESTAMP"

echo ""
echo -e "${BOLD}1. Creating a new branch for our 'improvements'${NC}"
if git show-ref --verify --quiet refs/heads/demo/latest; then
  git checkout demo/latest || git switch demo/latest
  git pull origin demo/latest || true
else
  git checkout main || git switch main
  git pull origin main || true
fi
git checkout -b $BRANCH

echo ""
echo -e "${BOLD}2. Applying breaking changes${NC}"
git apply breaking-changes.patch

echo ""
echo -e "${BOLD}3. Committing the changes${NC}"
git add -A
git commit -m "perf: optimize calculator algorithms

- Enhanced addition performance
- Streamlined subtraction
- Removed redundant checks"

echo ""
echo -e "${BOLD}4. Pushing to GitHub${NC}"
git push origin $BRANCH

echo ""
echo -e "${BOLD}5. Creating Pull Request${NC}"
PR_URL=$(gh pr create \
    --title "perf: Optimize calculator performance 🚀" \
    --body "## Performance Improvements

This PR includes several optimizations:
- ⚡ Faster addition
- 🎯 Streamlined subtraction
- 📈 Removed unnecessary checks

These changes should improve performance significantly!" \
    --base demo/latest || gh pr create \
    --title "perf: Optimize calculator performance 🚀" \
    --body "## Performance Improvements

This PR includes several optimizations:
- ⚡ Faster addition
- 🎯 Streamlined subtraction
- 📈 Removed unnecessary checks

These changes should improve performance significantly!" \
    --base main)

echo ""
echo -e "${GREEN}✅ Pull Request created!${NC}"
echo -e "📍 URL: ${BLUE}$PR_URL${NC}"
echo ""
echo -e "${YELLOW}⏳ GitHub Actions is now running tests...${NC}"
echo ""
echo "In a few moments you'll see:"
echo "1. ❌ Tests fail on the PR"
echo "2. 🤖 Nova detects the failures"
echo "3. 🔧 Nova creates a fix PR"
echo "4. ✅ All tests pass on Nova's PR"
echo ""
echo -e "${BOLD}Watch the magic happen at:${NC}"
echo -e "${BLUE}$PR_URL${NC}"
echo ""
echo "You can also check the Actions tab to see Nova running!"

# Return to base branch
if git show-ref --verify --quiet refs/heads/demo/latest; then
  git checkout demo/latest || git switch demo/latest
else
  git checkout main || git switch main
fi
