#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Repository configuration
REPO_OWNER="seabass011"
REPO_NAME="personal-demo-repo"
BRANCH_NAME="test-nova-fixes"
PR_TITLE="Test Nova CI-Rescue Auto-Fix"
PR_BODY_FILE="/tmp/pr_body.md"

echo -e "${BLUE}🚀 Nova CI-Rescue Workflow Tester${NC}"
echo -e "${BLUE}=================================${NC}"

# Check current branch and switch if necessary
echo -e "${YELLOW}📋 Checking current branch...${NC}"
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: $CURRENT_BRANCH"

if [ "$CURRENT_BRANCH" != "main" ] && [ "$CURRENT_BRANCH" != "master" ]; then
    echo -e "${YELLOW}🔄 Switching to main branch...${NC}"
    git checkout main 2>/dev/null || git checkout master 2>/dev/null || {
        echo -e "${RED}❌ Could not find main or master branch${NC}"
        exit 1
    }
fi

# Push latest changes
echo -e "${YELLOW}⬆️  Pushing latest changes to remote...${NC}"
git pull --rebase
git push origin HEAD

# Create PR body file
echo -e "${YELLOW}📝 Creating PR description...${NC}"
cat > "$PR_BODY_FILE" << 'PR_EOF'
# 🔧 Test Nova CI-Rescue Auto-Fix

This PR is created to test the Nova CI-Rescue GitHub App functionality.

## What this PR does:
- Tests the Nova CI-Rescue workflow integration
- Demonstrates automatic bug detection and fixing capabilities
- Shows how Nova analyzes failing tests and provides solutions

## Expected behavior:
1. CI workflow should run and detect test failures
2. Nova CI-Rescue should analyze the failures
3. Nova should provide detailed analysis and fix recommendations
4. The workflow should complete successfully with analysis results

## Files changed:
- `calculator.py` - Calculator implementation with intentional bugs
- `test_calculator.py` - Comprehensive test suite
- `.nova-ci-rescue.yml` - Nova configuration
- GitHub workflows for CI and Nova CI-Rescue

## Testing:
- Run `pytest test_calculator.py -v` to see current test status
- Check GitHub Actions for workflow execution
- Review Nova CI-Rescue analysis and recommendations

---

*This PR was created automatically by the Nova CI-Rescue workflow tester*
PR_EOF

echo -e "${GREEN}✅ PR description created${NC}"

# Function to create PR via GitHub CLI
create_pr_gh_cli() {
    echo -e "${YELLOW}🔧 Attempting to create PR via GitHub CLI...${NC}"
    
    if command -v gh &> /dev/null; then
        echo -e "${BLUE}📦 GitHub CLI found, creating PR...${NC}"
        if gh pr create \
            --title "$PR_TITLE" \
            --body-file "$PR_BODY_FILE" \
            --head "$BRANCH_NAME" \
            --base "main"; then
            echo -e "${GREEN}✅ PR created successfully via GitHub CLI!${NC}"
            return 0
        else
            echo -e "${RED}❌ GitHub CLI PR creation failed${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ GitHub CLI not found${NC}"
        return 1
    fi
}

# Function to create PR via GitHub API
create_pr_api() {
    echo -e "${YELLOW}🔧 Attempting to create PR via GitHub API...${NC}"
    
    # Check for GitHub token
    if [ -z "$GITHUB_TOKEN" ]; then
        echo -e "${RED}❌ GITHUB_TOKEN environment variable not set${NC}"
        return 1
    fi
    
    echo -e "${BLUE}📦 Using GitHub API to create PR...${NC}"
    
    # Get the commit SHA of the current branch
    BRANCH_SHA=$(git rev-parse HEAD)
    
    # Create PR using GitHub API
    API_RESPONSE=$(curl -s -X POST \
        -H "Authorization: Bearer $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        -H "Content-Type: application/json" \
        https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/pulls \
        -d "{
            \"title\": \"$PR_TITLE\",
            \"body\": \"$(cat "$PR_BODY_FILE" | sed 's/"/\\"/g' | tr -d '\n')\",
            \"head\": \"$BRANCH_NAME\",
            \"base\": \"main\"
        }")
    
    # Check if PR was created successfully
    if echo "$API_RESPONSE" | grep -q '"number":'; then
        PR_NUMBER=$(echo "$API_RESPONSE" | grep '"number":' | head -1 | sed -E 's/.*"number": ([0-9]+).*/\1/')
        echo -e "${GREEN}✅ PR #$PR_NUMBER created successfully via GitHub API!${NC}"
        return 0
    else
        echo -e "${RED}❌ GitHub API PR creation failed${NC}"
        echo -e "${RED}Response: $API_RESPONSE${NC}"
        return 1
    fi
}

# Function to provide manual instructions
manual_instructions() {
    echo -e "${YELLOW}📋 Manual PR Creation Instructions:${NC}"
    echo ""
    echo -e "${BLUE}1. Go to GitHub: https://github.com/$REPO_OWNER/$REPO_NAME${NC}"
    echo -e "${BLUE}2. Click 'Pull requests' tab${NC}"
    echo -e "${BLUE}3. Click 'New pull request' button${NC}"
    echo -e "${BLUE}4. Select '$BRANCH_NAME' as the compare branch${NC}"
    echo -e "${BLUE}5. Use the following title and description:${NC}"
    echo ""
    echo -e "${GREEN}Title: $PR_TITLE${NC}"
    echo ""
    echo -e "${GREEN}Description:${NC}"
    cat "$PR_BODY_FILE"
    echo ""
    echo -e "${YELLOW}6. Click 'Create pull request'${NC}"
    echo ""
    echo -e "${BLUE}After creating the PR, watch the GitHub Actions to see Nova CI-Rescue in action!${NC}"
}

# Main execution: try CLI, then API, then manual instructions
echo -e "${YELLOW}🔄 Attempting to create PR...${NC}"

if create_pr_gh_cli; then
    echo -e "${GREEN}🎉 Success! PR created via GitHub CLI${NC}"
elif create_pr_api; then
    echo -e "${GREEN}🎉 Success! PR created via GitHub API${NC}"
else
    echo -e "${RED}❌ Automated PR creation failed. Please create manually.${NC}"
    echo ""
    manual_instructions
fi

# Cleanup
rm -f "$PR_BODY_FILE"

echo ""
echo -e "${BLUE}🎯 Next Steps:${NC}"
echo -e "${BLUE}1. Check GitHub Actions for workflow execution${NC}"
echo -e "${BLUE}2. Watch the Nova CI-Rescue workflow run${NC}"
echo -e "${BLUE}3. Review the analysis and recommendations${NC}"
echo -e "${BLUE}4. See how Nova detects and analyzes test failures${NC}"

echo ""
echo -e "${GREEN}🚀 Nova CI-Rescue is ready to demonstrate its magic!${NC}"
