#!/bin/bash
# Migration script: Shows how to replace old test suites with the unified one

set -e

echo "=========================================="
echo "Nova Test Suite Migration Helper"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print comparisons
compare_usage() {
    echo -e "${BLUE}Migration Examples:${NC}"
    echo ""
}

# Check which test suites exist
echo -e "${YELLOW}Checking existing test suites...${NC}"
echo ""

if [ -f "nova_test_suite.py" ]; then
    echo "✓ Found: nova_test_suite.py"
    echo "  OLD: python nova_test_suite.py --verbose"
    echo -e "  ${GREEN}NEW: ./nova_unified_test_suite.py --verbose${NC}"
    echo ""
fi

if [ -f "regression_tests/regression_orchestrator.py" ]; then
    echo "✓ Found: regression_tests/regression_orchestrator.py"
    echo "  OLD: python regression_tests/regression_orchestrator.py test_repos.yaml"
    echo -e "  ${GREEN}NEW: ./nova_unified_test_suite.py --compare --config test_repos.yaml --v1-cmd './nova_v1_0' --v2-cmd './nova_v1_1'${NC}"
    echo ""
fi

if [ -f "nova_regression_test.py" ]; then
    echo "✓ Found: nova_regression_test.py (provided harness)"
    echo "  OLD: python nova_regression_test.py --generate -j results.json"
    echo -e "  ${GREEN}NEW: ./nova_unified_test_suite.py --generate --json-out results.json${NC}"
    echo ""
fi

echo "=========================================="
echo -e "${BLUE}Quick Test Commands:${NC}"
echo "=========================================="
echo ""

echo "1. Quick Smoke Test (replaces nova_test_suite.py):"
echo "   ./nova_unified_test_suite.py --generate --timeout 300 --max-iters 3"
echo ""

echo "2. Full Test Suite with Reports:"
echo "   ./nova_unified_test_suite.py --generate --json-out results.json --md-out report.md"
echo ""

echo "3. Version Comparison (replaces regression_orchestrator.py):"
echo "   ./nova_unified_test_suite.py --compare --config unified_test_config.yaml \\"
echo "     --v1-cmd 'nova' --v2-cmd 'nova' --output-dir comparison_results"
echo ""

echo "4. CI/CD Pipeline Integration:"
echo "   ./nova_unified_test_suite.py --no-color --json-out artifacts/results.json"
echo ""

echo "5. Development Testing (fast, no venv):"
echo "   ./nova_unified_test_suite.py --skip-venv --keep-files --verbose"
echo ""

echo "=========================================="
echo -e "${YELLOW}Feature Comparison:${NC}"
echo "=========================================="
echo ""

cat << 'EOF'
┌─────────────────────────┬──────────────┬────────────────┬──────────────┐
│ Feature                 │ Old Suite    │ Orchestrator   │ Unified      │
├─────────────────────────┼──────────────┼────────────────┼──────────────┤
│ Auto-setup              │ ✓            │ ✗              │ ✓            │
│ Version comparison      │ ✗            │ ✓              │ ✓            │
│ Edge cases              │ Basic        │ Basic          │ Advanced     │
│ Unfixable bugs          │ ✗            │ ✗              │ ✓            │
│ No-op patches           │ ✗            │ ✗              │ ✓            │
│ YAML config             │ ✗            │ Required       │ Optional     │
│ Built-in tests          │ 4            │ 0              │ 10           │
│ Patch counting          │ ✗            │ ✓              │ ✓            │
│ Professional output     │ ✓            │ ✓              │ ✓✓           │
│ CI/CD ready             │ Basic        │ ✓              │ ✓            │
└─────────────────────────┴──────────────┴────────────────┴──────────────┘
EOF

echo ""
echo "=========================================="
echo -e "${GREEN}Ready to Test?${NC}"
echo "=========================================="
echo ""

echo "Run this command to test the unified suite with all features:"
echo ""
echo "  ./nova_unified_test_suite.py --generate --verbose"
echo ""

# Ask if user wants to run a demo
read -p "Would you like to run a quick demo now? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Running quick demo (this will take a few seconds)..."
    echo ""
    
    # Run with minimal settings for quick demo
    python nova_unified_test_suite.py \
        --generate \
        --timeout 60 \
        --max-iters 2 \
        --no-color \
        --skip-venv \
        2>/dev/null | head -n 50
    
    echo ""
    echo "... (output truncated for demo)"
    echo ""
    echo -e "${GREEN}✓ Demo completed! For full test, remove the demo limits.${NC}"
else
    echo ""
    echo "You can run the full test suite anytime with:"
    echo "  ./nova_unified_test_suite.py --generate"
fi

echo ""
echo "=========================================="
echo -e "${BLUE}Documentation:${NC}"
echo "=========================================="
echo ""
echo "• Full Guide: NOVA_UNIFIED_TEST_SUITE_GUIDE.md"
echo "• Config Example: unified_test_config.yaml"
echo "• Quick Reference: TEST_SUITE_QUICK_REFERENCE.md"
echo ""
