#!/bin/bash
#
# Automated Nova CI-Rescue Demo Fixer
# 
# This script runs Nova CI-Rescue on all demo projects in examples/demos/
# sequentially, applying patches until all tests pass (or max iterations reached).
# 
# Patches are saved in each demo's .nova directory for review.
#
# Usage: ./scripts/fix_all_demos.sh [--dry-run] [--no-auto-pr] [--merge]
#        --dry-run: Show what would be done without actually running Nova
#        --no-auto-pr: Disable automatic PR creation (enabled by default)
#        --merge: Merge fix branches back to current branch

set -e  # Exit on error
set -o pipefail  # Ensure pipeline failures are caught

# Parse arguments
DRY_RUN=false
AUTO_PR="--auto-pr"  # Default to auto PR creation
MERGE_FIXES=false
for arg in "$@"; do
    case $arg in
        --dry-run)
            DRY_RUN=true
            echo "🔍 DRY RUN MODE - No changes will be made"
            ;;
        --no-auto-pr)
            AUTO_PR=""
            echo "📌 AUTO PR DISABLED - Will not create PRs"
            ;;
        --merge)
            MERGE_FIXES=true
            echo "🔀 MERGE MODE - Will merge fixes back to current branch"
            ;;
    esac
done

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the repository root (assuming script is in scripts/ directory)
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEMOS_DIR="$REPO_ROOT/examples/demos"

# Store the original branch if merging
ORIGINAL_BRANCH=""
if [[ "$MERGE_FIXES" == "true" ]]; then
    ORIGINAL_BRANCH=$(cd "$REPO_ROOT" && git rev-parse --abbrev-ref HEAD)
fi

echo -e "${BLUE}Nova CI-Rescue Automated Demo Fixer${NC}"
echo "====================================="
echo "Repository: $REPO_ROOT"
echo "Demos directory: $DEMOS_DIR"
if [[ -n "$ORIGINAL_BRANCH" ]]; then
    echo "Current branch: $ORIGINAL_BRANCH"
fi
echo ""

# Check if nova is available
if ! command -v nova &> /dev/null; then
    echo -e "${RED}Error: 'nova' command not found. Please ensure Nova CI-Rescue is installed.${NC}"
    exit 1
fi

# Check GitHub auth if --auto-pr is set
if [[ -n "$AUTO_PR" ]]; then
    echo -e "${BLUE}🔐 Checking GitHub authentication...${NC}"
    if command -v gh &> /dev/null && gh auth status --hostname github.com &>/dev/null; then
        echo -e "${GREEN}✓ GitHub CLI authenticated${NC}"
    elif [[ -n "$GITHUB_TOKEN" ]] || [[ -n "$GH_TOKEN" ]]; then
        echo -e "${GREEN}✓ GitHub token available${NC}"
    else
        echo -e "${YELLOW}⚠️  Warning: No GitHub authentication found${NC}"
        echo -e "${YELLOW}   PR creation may fail. To fix this:${NC}"
        echo -e "${YELLOW}   Option 1: Run 'gh auth login'${NC}"
        echo -e "${YELLOW}   Option 2: Set GITHUB_TOKEN environment variable${NC}"
        echo ""
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Aborted."
            exit 1
        fi
    fi
    echo ""
fi

# Track results
declare -a successful_demos=()
declare -a failed_demos=()
declare -a skipped_demos=()
declare -a fix_branches=()

# Change to demos directory
cd "$DEMOS_DIR"

# Count total demos
total_demos=$(find . -maxdepth 1 -name "demo_*" -type d | wc -l | tr -d ' ')
current_demo=0

echo -e "Found ${GREEN}$total_demos${NC} demo directories to process"
echo ""

# Loop through each demo_* subdirectory
for demo_dir in demo_*/; do
    if [[ -d "$demo_dir" ]]; then
        current_demo=$((current_demo + 1))
        demo_name="${demo_dir%/}"  # Remove trailing slash
        
        echo -e "${BLUE}[$current_demo/$total_demos]${NC} Processing: ${YELLOW}$demo_name${NC}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        # Check if tests exist in the demo directory
        if ! find "$demo_dir" -type f \( -name "test_*.py" -o -name "*_test.py" \) | grep -q .; then
            echo -e "${YELLOW}⚠️  No test files found in $demo_name, skipping...${NC}"
            skipped_demos+=("$demo_name")
            echo ""
            continue
        fi
        
        if [[ "$DRY_RUN" == "true" ]]; then
            echo "Would run: nova fix $DEMOS_DIR/$demo_dir --verbose --whole-file $AUTO_PR"
            successful_demos+=("$demo_name (dry-run)")
        else
            # Ensure we're on the original branch before each demo if merging
            if [[ "$MERGE_FIXES" == "true" ]]; then
                cd "$REPO_ROOT"
                git checkout "$ORIGINAL_BRANCH" --quiet
                cd "$DEMOS_DIR"
            fi
            
            # Log file to capture nova output for analysis
            LOG_FILE="/tmp/nova_fix_${demo_name}.log"
            # Run Nova CI-Rescue and capture output (force colors)
            # Use whole-file mode for more reliable fixes
            if FORCE_COLOR=1 nova fix "$DEMOS_DIR/$demo_dir" --verbose --whole-file $AUTO_PR 2>&1 | tee "$LOG_FILE"; then
                echo -e "${GREEN}✅ Successfully fixed: $demo_name${NC}"
                successful_demos+=("$demo_name")
                
                # Extract the branch name from the log if merging
                if [[ "$MERGE_FIXES" == "true" ]]; then
                    BRANCH_NAME=$(grep -oE "nova-auto-fix/[0-9_]+" "$LOG_FILE" | tail -1)
                    if [[ -n "$BRANCH_NAME" ]]; then
                        fix_branches+=("$BRANCH_NAME:$demo_name")
                        
                        # Merge the fix branch back to the original branch
                        cd "$REPO_ROOT"
                        echo -e "${BLUE}🔀 Merging $BRANCH_NAME back to $ORIGINAL_BRANCH...${NC}"
                        if git merge "$BRANCH_NAME" --no-edit; then
                            echo -e "${GREEN}✓ Merged successfully${NC}"
                            # Delete the temporary branch after successful merge
                            git branch -d "$BRANCH_NAME" --quiet
                            echo -e "${BLUE}🗑️  Cleaned up temporary branch${NC}"
                        else
                            echo -e "${RED}❌ Failed to merge $BRANCH_NAME${NC}"
                            echo "You may need to resolve conflicts manually"
                        fi
                        cd "$DEMOS_DIR"
                    fi
                fi
                
                # List saved patches if any exist
                if [[ -d "$demo_dir/.nova" ]]; then
                    echo -e "${BLUE}📄 Saved patches:${NC}"
                    find "$demo_dir/.nova" -name "*.patch" -type f 2>/dev/null | while read -r patch; do
                        echo "   - ${patch#$demo_dir/}"
                    done
                fi
            else
                echo -e "${RED}❌ Failed to fix: $demo_name${NC}"
                failed_demos+=("$demo_name")
                # List any patches that were generated before failure
                if [[ -d "$demo_dir/.nova" ]]; then
                    echo -e "${BLUE}📄 Saved patches (attempted fixes):${NC}"
                    find "$demo_dir/.nova" -name "*.patch" -type f 2>/dev/null | while read -r patch; do
                        echo "   - ${patch#$demo_dir/}"
                    done
                fi
                # Highlight important issues from the Nova output log
                if [[ -f "$LOG_FILE" ]]; then
                    if grep -q -E "No progress|^Error:|Exit Reason:" "$LOG_FILE"; then
                        echo -e "${YELLOW}⚠️  Issues encountered during fix of $demo_name:${NC}"
                        grep -E "No progress|^Error:|Exit Reason:" "$LOG_FILE" | sed 's/^/   - /'
                    fi
                fi
            fi
        fi
        
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        
        # Small pause between runs to avoid overwhelming the system
        sleep 1
    fi
done

# Summary report
echo -e "${BLUE}Summary Report${NC}"
echo "==============="
echo -e "Total demos processed: ${YELLOW}$current_demo${NC}"
echo -e "Successful: ${GREEN}${#successful_demos[@]}${NC}"
echo -e "Failed: ${RED}${#failed_demos[@]}${NC}"
echo -e "Skipped: ${YELLOW}${#skipped_demos[@]}${NC}"
echo ""

# List results for each category
if [[ ${#successful_demos[@]} -gt 0 ]]; then
    echo -e "${GREEN}✅ Successfully fixed:${NC}"
    for demo in "${successful_demos[@]}"; do
        echo "   - $demo"
    done
    echo ""
fi

if [[ ${#failed_demos[@]} -gt 0 ]]; then
    echo -e "${RED}❌ Failed to fix:${NC}"
    for demo in "${failed_demos[@]}"; do
        echo "   - $demo"
    done
    echo ""
fi

if [[ ${#skipped_demos[@]} -gt 0 ]]; then
    echo -e "${YELLOW}⚠️  Skipped (no tests):${NC}"
    for demo in "${skipped_demos[@]}"; do
        echo "   - $demo"
    done
    echo ""
fi

# Verify all tests pass if not a dry run and some fixes were applied
if [[ "$DRY_RUN" == "false" && ${#successful_demos[@]} -gt 0 ]]; then
    echo -e "${BLUE}🧪 Running final verification on all demos...${NC}"
    cd "$DEMOS_DIR"
    if pytest . -q --tb=no 2>&1 | grep -E "(FAILED|ERROR)" > /dev/null; then
        echo -e "${RED}⚠️  WARNING: Some tests are still failing after fixes!${NC}"
        echo "Run 'pytest examples/demos -v' to see details."
    else
        echo -e "${GREEN}✅ All tests passing across demos!${NC}"
    fi
fi

# Instructions to review patches if needed
if [[ "$DRY_RUN" == "false" && ${#successful_demos[@]} -gt 0 ]]; then
    echo ""
    echo -e "${BLUE}📋 To review patches:${NC}"
    echo "   find $DEMOS_DIR -path '*/.nova/*/patches/*.patch' -type f"
    echo ""
    echo -e "${BLUE}🔍 To view a specific patch:${NC}"
    echo "   cat <patch_file>"
    echo ""
    
    if [[ "$MERGE_FIXES" == "true" ]]; then
        # Show current status if merging
        echo -e "${BLUE}📊 Current Git Status:${NC}"
        cd "$REPO_ROOT"
        git status --short
        echo ""
        echo -e "${BLUE}📋 Next steps:${NC}"
        echo "   1. Review the changes: git diff"
        echo "   2. Commit all fixes: git add -A && git commit -m \"Fix all demo tests\""
        echo "   3. Push to remote: git push"
    else
        echo -e "${BLUE}🌿 To see git branches created:${NC}"
        echo "   git branch | grep nova-"
        echo ""
        echo -e "${BLUE}💡 To merge all fixes to current branch:${NC}"
        echo "   Run again with --merge flag: $0 --merge"
    fi
fi

# Exit with error if any demo fixes failed
if [[ ${#failed_demos[@]} -gt 0 ]]; then
    exit 1
fi