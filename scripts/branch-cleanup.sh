#!/bin/bash
# Branch cleanup script for trunk-based development migration

set -e

echo "🚀 Starting branch cleanup for trunk-based development..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Ensure we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    print_error "Not in the project root directory. Please run from the repository root."
    exit 1
fi

# Fetch all remote branches
print_status "Fetching all remote branches..."
git fetch --all --prune

# Show current branch status
print_status "Current branch status:"
git branch -a

# Get current branch
current_branch=$(git branch --show-current)
print_status "Currently on branch: $current_branch"

# List branches that match ephemeral patterns
print_status "Identifying ephemeral branches for cleanup..."

ephemeral_patterns=(
    "nova-auto-fix/*"
    "bot/*"
    "demo/*"
    "temp/*"
    "experiment/*"
    "test/*"
    "hotfix/*"
)

# Find local branches matching ephemeral patterns
ephemeral_branches=()
for pattern in "${ephemeral_patterns[@]}"; do
    # Use git for-each-ref to safely get branch names
    while IFS= read -r branch; do
        if [[ -n "$branch" ]]; then
            ephemeral_branches+=("$branch")
        fi
    done < <(git for-each-ref --format='%(refname:short)' refs/heads/ | grep -E "^${pattern//\*/.*}$" || true)
done

if [ ${#ephemeral_branches[@]} -eq 0 ]; then
    print_success "No ephemeral branches found to clean up."
else
    print_warning "Found ${#ephemeral_branches[@]} ephemeral branches:"
    for branch in "${ephemeral_branches[@]}"; do
        echo "  - $branch"
    done
    
    echo
    read -p "Do you want to delete these branches? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        for branch in "${ephemeral_branches[@]}"; do
            if [ "$branch" != "$current_branch" ]; then
                print_status "Deleting branch: $branch"
                git branch -D "$branch" || print_warning "Failed to delete $branch"
            else
                print_warning "Skipping current branch: $branch"
            fi
        done
        print_success "Local ephemeral branch cleanup completed!"
    else
        print_status "Skipped local branch cleanup."
    fi
fi

# Check for merged branches
print_status "Finding merged branches..."
merged_branches=()
while IFS= read -r branch; do
    if [[ -n "$branch" && "$branch" != "main" && "$branch" != "master" && "$branch" != "$current_branch" ]]; then
        merged_branches+=("$branch")
    fi
done < <(git branch --merged main 2>/dev/null | sed 's/^[* ] //' | grep -v '^main$' | grep -v '^master$' || true)

if [ ${#merged_branches[@]} -eq 0 ]; then
    print_success "No merged branches found to clean up."
else
    print_warning "Found ${#merged_branches[@]} merged branches:"
    for branch in "${merged_branches[@]}"; do
        echo "  - $branch"
    done
    
    echo
    read -p "Do you want to delete these merged branches? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        for branch in "${merged_branches[@]}"; do
            if [ "$branch" != "$current_branch" ]; then
                print_status "Deleting merged branch: $branch"
                git branch -d "$branch" || print_warning "Failed to delete $branch"
            else
                print_warning "Skipping current branch: $branch"
            fi
        done
        print_success "Merged branch cleanup completed!"
    else
        print_status "Skipped merged branch cleanup."
    fi
fi

# Show final branch status
print_status "Final branch status:"
git branch -a

print_success "Branch cleanup completed! 🎉"
print_status "Next steps:"
echo "  1. Review remaining branches"
echo "  2. Ensure main branch protection is enabled on GitHub"
echo "  3. Set up branch naming conventions in your team"
echo "  4. Configure automated branch cleanup workflows"