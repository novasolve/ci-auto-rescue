#!/bin/bash
# Test all patches with the Nova Safe Patching system

echo "Nova Safe Patching System - Test Suite"
echo "======================================"
echo

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test each patch
for patch in test_patches/*.diff; do
    if [[ "$patch" == "test_patches/*.diff" ]]; then
        echo "No patch files found!"
        exit 1
    fi
    
    echo -e "${YELLOW}Testing: $(basename "$patch")${NC}"
    
    # Run the review command and capture the exit code
    if [[ "$patch" == *"01_safe_patch.diff" ]]; then
        # Test with context for the safe patch
        python -m nova.cli_safe_patch review "$patch" --context test_patches/context_divide_by_zero.txt
    else
        python -m nova.cli_safe_patch review "$patch"
    fi
    
    exit_code=$?
    
    # Check expected results
    if [[ "$patch" == *"01_safe_patch.diff" ]]; then
        if [[ $exit_code -eq 0 ]]; then
            echo -e "${GREEN}✅ PASS: Safe patch correctly approved${NC}"
        else
            echo -e "${RED}❌ FAIL: Safe patch should have been approved${NC}"
        fi
    else
        if [[ $exit_code -ne 0 ]]; then
            echo -e "${GREEN}✅ PASS: Unsafe patch correctly rejected${NC}"
        else
            echo -e "${RED}❌ FAIL: Unsafe patch should have been rejected${NC}"
        fi
    fi
    
    echo "--------------------------------------"
    echo
done

echo "Test suite complete!"
