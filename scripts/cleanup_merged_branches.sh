#!/bin/bash

# cleanup_merged_branches.sh
# Script to clean up local and remote branches that have been merged to main

set -e

echo "🧹 Branch Cleanup Script"
echo "========================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fetch latest changes
echo -e "${BLUE}📡 Fetching latest changes...${NC}"
git fetch --prune origin

# Switch to main branch
echo -e "${BLUE}🔄 Switching to main branch...${NC}"
git checkout main
git pull origin main

# Function to check if branch is merged
is_merged() {
    local branch=$1
    git merge-base --is-ancestor "origin/$branch" main 2>/dev/null
}

# Function to check if branch follows new naming convention
follows_convention() {
    local branch=$1
    if [[ $branch =~ ^(feat|fix|docs|chore|ci|perf|bot)/.+ ]]; then
        return 0
    else
        return 1
    fi
}

# Get list of remote branches (excluding main, release/*, and protected branches)
echo -e "${BLUE}🔍 Analyzing remote branches...${NC}"
remote_branches=$(git branch -r | grep -v 'origin/HEAD' | grep -v 'origin/main' | grep -v 'origin/release/' | sed 's/origin\///' | tr -d ' ')

merged_branches=()
old_convention_branches=()
active_branches=()

for branch in $remote_branches; do
    # Skip if branch doesn't exist (might have been deleted)
    if ! git show-ref --verify --quiet "refs/remotes/origin/$branch"; then
        continue
    fi

    if is_merged "$branch"; then
        merged_branches+=("$branch")
    elif ! follows_convention "$branch"; then
        old_convention_branches+=("$branch")
    else
        active_branches+=("$branch")
    fi
done

# Report findings
echo
echo -e "${GREEN}✅ Merged branches (safe to delete):${NC}"
if [ ${#merged_branches[@]} -eq 0 ]; then
    echo "  None found"
else
    printf '  %s\n' "${merged_branches[@]}"
fi

echo
echo -e "${YELLOW}⚠️  Branches using old naming convention:${NC}"
if [ ${#old_convention_branches[@]} -eq 0 ]; then
    echo "  None found"
else
    printf '  %s\n' "${old_convention_branches[@]}"
fi

echo
echo -e "${BLUE}🔄 Active branches (following new convention):${NC}"
if [ ${#active_branches[@]} -eq 0 ]; then
    echo "  None found"
else
    printf '  %s\n' "${active_branches[@]}"
fi

# Interactive cleanup
echo
echo -e "${YELLOW}🤔 What would you like to do?${NC}"
echo "1) Delete merged branches"
echo "2) Show old convention branches that need renaming"
echo "3) Delete specific branches"
echo "4) Exit without changes"
read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        if [ ${#merged_branches[@]} -eq 0 ]; then
            echo -e "${GREEN}✨ No merged branches to delete!${NC}"
        else
            echo -e "${RED}🗑️  Deleting merged branches...${NC}"
            for branch in "${merged_branches[@]}"; do
                echo "  Deleting origin/$branch"
                git push origin --delete "$branch" 2>/dev/null || echo "    (already deleted)"
                # Delete local branch if it exists
                git branch -d "$branch" 2>/dev/null || true
            done
            echo -e "${GREEN}✅ Cleanup complete!${NC}"
        fi
        ;;
    2)
        if [ ${#old_convention_branches[@]} -eq 0 ]; then
            echo -e "${GREEN}✨ All branches follow the new convention!${NC}"
        else
            echo -e "${YELLOW}📋 Branches that should be renamed:${NC}"
            for branch in "${old_convention_branches[@]}"; do
                # Suggest new name based on content
                suggested_name=""
                if [[ $branch == *"fix"* ]] || [[ $branch == *"bug"* ]]; then
                    suggested_name="fix/${branch//[^a-zA-Z0-9-]/-}"
                elif [[ $branch == *"feat"* ]] || [[ $branch == *"feature"* ]]; then
                    suggested_name="feat/${branch//[^a-zA-Z0-9-]/-}"
                elif [[ $branch == *"doc"* ]]; then
                    suggested_name="docs/${branch//[^a-zA-Z0-9-]/-}"
                else
                    suggested_name="chore/${branch//[^a-zA-Z0-9-]/-}"
                fi
                echo "  $branch → $suggested_name"
            done
            echo
            echo -e "${BLUE}💡 To rename a branch:${NC}"
            echo "  git checkout $branch"
            echo "  git checkout -b new-name"
            echo "  git push origin new-name"
            echo "  git push origin --delete old-name"
        fi
        ;;
    3)
        echo "Enter branch names to delete (space-separated):"
        read -p "> " branches_to_delete
        for branch in $branches_to_delete; do
            echo "Deleting origin/$branch"
            git push origin --delete "$branch" 2>/dev/null || echo "  (branch not found)"
            git branch -d "$branch" 2>/dev/null || true
        done
        ;;
    4)
        echo -e "${BLUE}👋 Exiting without changes${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}❌ Invalid choice${NC}"
        exit 1
        ;;
esac

echo
echo -e "${GREEN}🎉 Branch cleanup completed!${NC}"
echo -e "${BLUE}📚 See docs/BRANCH_STRATEGY.md for more information about our branch model${NC}"
