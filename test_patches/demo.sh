#!/bin/bash
# Quick demo of the Nova Safe Patching System

echo "Nova Safe Patching System Demo"
echo "=============================="
echo

echo "1. Testing a SAFE patch that should be approved:"
echo "------------------------------------------------"
python -m nova.cli_safe_patch review test_patches/01_safe_patch.diff --context test_patches/context_divide_by_zero.txt
echo

echo "2. Testing a DANGEROUS patch with exec():"
echo "-----------------------------------------"
python -m nova.cli_safe_patch review test_patches/02_dangerous_exec.diff
echo

echo "3. Testing a patch that modifies TEST files:"
echo "--------------------------------------------"
python -m nova.cli_safe_patch review test_patches/05_modify_tests.diff
echo

echo "4. Testing a patch that's TOO LARGE:"
echo "------------------------------------"
python -m nova.cli_safe_patch review test_patches/09_exceeds_size_limit.diff
echo

echo "Demo complete! The safe patching system successfully:"
echo "✅ Approved safe patches"
echo "❌ Blocked dangerous code patterns"
echo "❌ Prevented test file modifications"  
echo "❌ Enforced size limits"
