#!/bin/bash
#
# Automated Nova CI-Rescue Demo Fixer
# 
# This script runs Nova CI-Rescue on all demo projects in examples/demos/
# sequentially, applying patches until all tests pass (or max iterations reached).
# 
# Patches are saved in each demo's .nova directory for review.
#
# Usage: ./scripts/fix_all_demos.sh [--dry-run]
#        --dry-run: Show what would be done without actually running Nova

set -e  # Exit on error

# Parse arguments
DRY_RUN=false
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "🔍 DRY RUN MODE - No changes will be made"
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the repository root (assuming script is in scripts/ directory)
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEMOS_DIR="$REPO_ROOT/examples/demos"

echo -e "${BLUE}Nova CI-Rescue Automated Demo Fixer${NC}"
echo "====================================="
echo "Repository: $REPO_ROOT"
echo "Demos directory: $DEMOS_DIR"
echo ""

# Check if nova is available
if ! command -v nova &> /dev/null; then
    echo -e "${RED}Error: 'nova' command not found. Please ensure Nova CI-Rescue is installed.${NC}"
    exit 1
fi

# Track results
declare -a successful_demos=()
declare -a failed_demos=()
declare -a skipped_demos=()

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
        
        # Check if tests exist
        if ! find "$demo_dir" -name "test_*.py" -o -name "*_test.py" | grep -q .; then
            echo -e "${YELLOW}⚠️  No test files found in $demo_name, skipping...${NC}"
            skipped_demos+=("$demo_name")
            echo ""
            continue
        fi
        
        if [[ "$DRY_RUN" == "true" ]]; then
            echo "Would run: nova fix \"$DEMOS_DIR/$demo_dir\" --verbose"
            successful_demos+=("$demo_name (dry-run)")
        else
            # Run Nova CI-Rescue on the demo directory
            if nova fix "$DEMOS_DIR/$demo_dir" --verbose; then
                echo -e "${GREEN}✅ Successfully fixed: $demo_name${NC}"
                successful_demos+=("$demo_name")
                
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

# List results
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

# Verify all tests pass
if [[ "$DRY_RUN" == "false" && ${#successful_demos[@]} -gt 0 ]]; then
    echo -e "${BLUE}🧪 Running final verification...${NC}"
    cd "$DEMOS_DIR"
    
    if pytest . -q --tb=no 2>&1 | grep -E "(FAILED|ERROR)" > /dev/null; then
        echo -e "${RED}⚠️  WARNING: Some tests still failing after fixes!${NC}"
        echo "Run 'pytest examples/demos -v' to see details"
    else
        echo -e "${GREEN}✅ All tests passing!${NC}"
    fi
fi

# Show how to review patches
if [[ "$DRY_RUN" == "false" && ${#successful_demos[@]} -gt 0 ]]; then
    echo ""
    echo -e "${BLUE}📋 To review patches:${NC}"
    echo "   find $DEMOS_DIR -path '*/.nova/*/patches/*.patch' -type f"
    echo ""
    echo -e "${BLUE}🔍 To view a specific patch:${NC}"
    echo "   cat <patch_file>"
    echo ""
    echo -e "${BLUE}🌿 To see git branches created:${NC}"
    echo "   git branch | grep nova-"
fi

# Exit with error if any demos failed
if [[ ${#failed_demos[@]} -gt 0 ]]; then
    exit 1
fi
