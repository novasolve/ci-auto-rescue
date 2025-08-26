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
DEBUG=false
PYTHON_TRACEBACK=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            echo "🔍 DRY RUN MODE - No changes will be made"
            shift
            ;;
        --debug)
            DEBUG=true
            PYTHON_TRACEBACK="PYTHONTRACEBACK=1"
            echo "🐛 DEBUG MODE - Full tracebacks enabled"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --dry-run    Show what would be done without actually running"
            echo "  --debug      Enable debug mode with full Python tracebacks"
            echo "  -h, --help   Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
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
            # Create log directory for this demo
            LOG_DIR="$DEMOS_DIR/.nova_logs/$demo_name"
            mkdir -p "$LOG_DIR"
            
            # Run Nova CI-Rescue on the demo directory with full logging
            LOG_FILE="$LOG_DIR/nova_run_$(date +%Y%m%d_%H%M%S).log"
            echo -e "${BLUE}📝 Logging to: ${LOG_FILE#$REPO_ROOT/}${NC}"
            
            # Run with full error capture
            if $PYTHON_TRACEBACK nova fix "$DEMOS_DIR/$demo_dir" --verbose 2>&1 | tee "$LOG_FILE"; then
                echo -e "${GREEN}✅ Successfully fixed: $demo_name${NC}"
                successful_demos+=("$demo_name")
                
                # Save patches and telemetry
                if [[ -d "$demo_dir/.nova" ]]; then
                    echo -e "${BLUE}📄 Artifacts saved:${NC}"
                    
                    # Copy patches to log directory
                    find "$demo_dir/.nova" -name "*.patch" -type f 2>/dev/null | while read -r patch; do
                        cp "$patch" "$LOG_DIR/"
                        echo "   - Patch: ${patch#$demo_dir/}"
                    done
                    
                    # Copy telemetry logs
                    find "$demo_dir/.nova" -name "*.jsonl" -type f 2>/dev/null | while read -r jsonl; do
                        cp "$jsonl" "$LOG_DIR/"
                        echo "   - Telemetry: ${jsonl#$demo_dir/}"
                    done
                fi
            else
                EXIT_CODE=$?
                echo -e "${RED}❌ Failed to fix: $demo_name (exit code: $EXIT_CODE)${NC}"
                failed_demos+=("$demo_name")
                
                # Extract error details from log
                echo -e "${RED}📋 Error details:${NC}"
                grep -E "Error:|Exception:|Traceback|datetime.*float|unsupported operand" "$LOG_FILE" | tail -20
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

# Log information
if [[ "$DRY_RUN" != "true" ]]; then
    echo -e "${BLUE}📁 Logs saved to: $DEMOS_DIR/.nova_logs/${NC}"
    echo -e "${DIM}   Each demo has its own subdirectory with:${NC}"
    echo -e "${DIM}   - Full execution logs${NC}"
    echo -e "${DIM}   - Applied patches${NC}"
    echo -e "${DIM}   - Telemetry data${NC}"
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
