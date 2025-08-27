#!/usr/bin/env bash
set -euo pipefail

# Nova Agent Auto-Fixes Complex Algorithmic Bugs - Demo Script

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'

clear
echo -e "${BOLD}🎯 Demo: Nova Fixes Complex Algorithmic Bugs${NC}"
echo -e "${BOLD}=============================================${NC}"
echo
echo "This demo showcases Nova fixing subtle bugs in classic algorithms:"
echo "- Kadane's Algorithm (Maximum Subarray)"
echo "- Longest Increasing Subsequence"
echo "- Dijkstra's Shortest Path"
echo "- Merge Intervals"
echo "- 3Sum Problem"
echo "- 0/1 Knapsack"
echo "- Topological Sort"
echo "- Coin Change"
echo
read -p "Press Enter to start the demo..."

echo
echo -e "${BOLD}1. Current State: Broken Algorithm Implementations${NC}"
echo -e "${YELLOW}Each algorithm has subtle bugs that cause test failures:${NC}"
echo "• Kadane's: Doesn't handle all-negative arrays"
echo "• LIS: Off-by-one error in DP logic"
echo "• Dijkstra: Path reconstruction bug"
echo "• Merge Intervals: Missing sort, wrong overlap check"
echo "• 3Sum: Duplicate handling issues"
echo "• Knapsack: Wrong DP table dimensions"
echo "• Topological Sort: No cycle detection"
echo "• Coin Change: Array indexing errors"
echo
read -p "Press Enter to run the failing tests..."

# Ensure we're in the right directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Install dependencies if needed
if ! command -v pytest >/dev/null 2>&1; then
  echo -e "${YELLOW}Installing pytest...${NC}"
  pip install -q pytest
fi

echo
echo -e "${YELLOW}$ pytest tests/ -v${NC}"
set +e
pytest tests/ -v
TEST_RESULT=$?
set -e

if [ $TEST_RESULT -eq 0 ]; then
  echo -e "${GREEN}✅ Tests are already passing! Nothing to fix.${NC}"
  exit 0
fi

echo
echo -e "${RED}❌ Multiple algorithm tests are failing!${NC}"
echo
read -p "Press Enter to run Nova CI-Rescue..."

echo
echo -e "${BOLD}2. Running Nova CI-Rescue with Whole-File Mode${NC}"
echo -e "${YELLOW}Nova will analyze the failures and fix all bugs in one pass${NC}"
echo

# Check if Nova is available
if ! command -v nova >/dev/null 2>&1; then
  echo -e "${YELLOW}Installing Nova CI-Rescue...${NC}"
  pip install -e ../../../../  # Install from the repo root
fi

# Ensure we have an API key
if [ -z "${OPENAI_API_KEY:-}" ] && [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  echo -e "${RED}Error: No API key found!${NC}"
  echo "Please set either OPENAI_API_KEY or ANTHROPIC_API_KEY"
  exit 1
fi

# Run Nova with whole-file mode
echo -e "${YELLOW}$ nova fix . --whole-file --max-iters 5${NC}"
nova fix . --whole-file --max-iters 5

echo
echo -e "${BOLD}3. Verifying the Fix${NC}"
echo -e "${YELLOW}$ pytest tests/ -v${NC}"
pytest tests/ -v

echo
echo -e "${GREEN}✅ All algorithmic bugs have been fixed!${NC}"
echo
echo -e "${BOLD}What Nova Fixed:${NC}"
echo "• Kadane's: Proper initialization for negative arrays"
echo "• LIS: Correct DP recurrence relation"
echo "• Dijkstra: Fixed path reconstruction order"
echo "• Merge Intervals: Added sorting and fixed overlap logic"
echo "• 3Sum: Added duplicate skipping logic"
echo "• Knapsack: Fixed DP table dimensions and indices"
echo "• Topological Sort: Added cycle detection"
echo "• Coin Change: Fixed array bounds and return logic"
echo
echo -e "${BOLD}Key Insights:${NC}"
echo "1. Nova understands algorithmic correctness, not just syntax"
echo "2. It can fix multiple related bugs in a single iteration"
echo "3. The whole-file mode ensures consistent fixes across the codebase"
echo "4. Nova's fixes maintain code style and readability"
echo
echo -e "${YELLOW}This demonstrates Nova's ability to understand and fix"
echo -e "complex algorithmic bugs that require deep reasoning!${NC}"
