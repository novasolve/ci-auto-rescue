"""
Enhanced prompts for complete test fixes in a single iteration.
This module focuses on pushing the LLM to analyze and fix ALL test failures at once.
"""

from typing import Dict, Any, List, Optional
import json


def build_comprehensive_planner_prompt(failing_tests: List[Dict[str, Any]], 
                                     critic_feedback: Optional[str] = None) -> str:
    """
    Build an enhanced prompt that pushes the planner to create a comprehensive fix strategy.
    """
    prompt = ""
    
    if critic_feedback:
        prompt += "⚠️ CRITICAL FEEDBACK FROM PREVIOUS ATTEMPT:\n"
        prompt += f'"{critic_feedback}"\n\n'
        prompt += "The previous approach was INCOMPLETE. This time, you MUST fix ALL tests in ONE comprehensive solution.\n\n"
    
    prompt += "🎯 YOUR MISSION: Fix ALL failing tests in a SINGLE, comprehensive solution.\n\n"
    
    prompt += f"You have {len(failing_tests)} failing tests. Here are ALL of them:\n\n"
    prompt += "COMPLETE LIST OF FAILING TESTS:\n"
    prompt += "=" * 80 + "\n"
    
    # Group tests by file for better understanding
    tests_by_file = {}
    for test in failing_tests:
        file_path = test.get('file', 'unknown')
        if file_path not in tests_by_file:
            tests_by_file[file_path] = []
        tests_by_file[file_path].append(test)
    
    # Show ALL tests with full details
    for file_path, tests in tests_by_file.items():
        prompt += f"\n📁 File: {file_path}\n"
        prompt += "-" * 40 + "\n"
        for test in tests:
            prompt += f"\n❌ Test: {test.get('name', 'unknown')}\n"
            prompt += f"   Line: {test.get('line', 0)}\n"
            prompt += f"   Error Type: {test.get('error_type', 'Unknown')}\n"
            prompt += f"   Full Error:\n"
            error_msg = test.get('short_traceback', 'No traceback')
            prompt += f"   {error_msg}\n"
            prompt += "\n"
    
    prompt += "=" * 80 + "\n\n"
    
    prompt += "CRITICAL REQUIREMENTS:\n"
    prompt += "1. You MUST analyze ALL {0} failing tests above\n".format(len(failing_tests))
    prompt += "2. Your plan MUST address EVERY SINGLE failure\n"
    prompt += "3. Look for PATTERNS - many failures likely have the SAME root cause\n"
    prompt += "4. DO NOT fix tests incrementally - create ONE comprehensive solution\n"
    prompt += "5. Consider that multiple test failures often stem from 1-2 core issues\n"
    prompt += "\n"
    
    prompt += "ANALYZE THE PATTERNS:\n"
    prompt += "- Are multiple tests failing for the same reason?\n"
    prompt += "- Is there a common function/method causing multiple failures?\n"
    prompt += "- Are the failures related to:\n"
    prompt += "  • Wrong arithmetic operations (e.g., + instead of -)\n"
    prompt += "  • Missing error handling (e.g., division by zero, negative square roots)\n"
    prompt += "  • Wrong return values\n"
    prompt += "  • Off-by-one errors\n"
    prompt += "\n"
    
    prompt += "YOUR RESPONSE MUST INCLUDE:\n"
    prompt += "1. ROOT CAUSE ANALYSIS: What are the 1-3 core issues causing ALL failures?\n"
    prompt += "2. COMPREHENSIVE APPROACH: A strategy that fixes ALL tests at once\n"
    prompt += "3. COMPLETE FIX LIST: Exactly what to change in each function\n"
    prompt += "4. VERIFICATION: How your fix addresses each of the {0} failing tests\n".format(len(failing_tests))
    prompt += "\n"
    prompt += "Remember: Partial fixes are UNACCEPTABLE. Fix everything in one go!"
    
    return prompt


def build_complete_fix_prompt(plan: Dict[str, Any], 
                            failing_tests: List[Dict[str, Any]], 
                            test_contents: Dict[str, str] = None, 
                            source_contents: Dict[str, str] = None,
                            critic_feedback: Optional[str] = None) -> str:
    """
    Build an enhanced prompt that demands a complete fix for ALL tests.
    """
    prompt = ""
    
    if critic_feedback:
        prompt += "⚠️ YOUR PREVIOUS FIX WAS REJECTED:\n"
        prompt += f'"{critic_feedback}"\n\n'
        prompt += "This time, you MUST fix ALL tests completely. No partial solutions!\n\n"
    
    prompt += f"🎯 OBJECTIVE: Fix ALL {len(failing_tests)} failing tests in ONE complete solution.\n\n"
    
    # Show the comprehensive plan
    if plan:
        prompt += "YOUR COMPREHENSIVE PLAN:\n"
        prompt += "=" * 60 + "\n"
        if isinstance(plan.get('approach'), str):
            prompt += f"{plan['approach']}\n"
        prompt += "=" * 60 + "\n\n"
    
    # List ALL failing tests with their exact errors
    prompt += f"ALL {len(failing_tests)} TESTS YOU MUST FIX:\n"
    prompt += "=" * 80 + "\n"
    
    # Group by error pattern to help identify common fixes
    error_patterns = {}
    for test in failing_tests:
        error = test.get('short_traceback', '')
        # Extract key error indicators
        if 'assert' in error and '==' in error:
            pattern = "Assertion mismatch"
        elif 'ZeroDivisionError' in error:
            pattern = "Division by zero"
        elif 'ValueError' in error or 'RAISE' in error:
            pattern = "Missing error handling"
        else:
            pattern = "Other error"
        
        if pattern not in error_patterns:
            error_patterns[pattern] = []
        error_patterns[pattern].append(test)
    
    # Show tests grouped by pattern
    for pattern, tests in error_patterns.items():
        prompt += f"\n🔍 Pattern: {pattern} ({len(tests)} tests)\n"
        prompt += "-" * 40 + "\n"
        for test in tests:
            prompt += f"• {test.get('name')}: {test.get('short_traceback', '')[:100]}...\n"
    
    prompt += "\n" + "=" * 80 + "\n\n"
    
    # Include current source code
    if source_contents:
        prompt += "CURRENT BROKEN CODE (FIX THIS):\n"
        for file_path, content in source_contents.items():
            prompt += f"\n=== {file_path} ===\n"
            prompt += content
            prompt += "\n"
    
    # Include test code for reference
    if test_contents:
        prompt += "\nTEST EXPECTATIONS (for reference):\n"
        for file_path, content in test_contents.items():
            prompt += f"\n=== {file_path} ===\n"
            # Show only the test function signatures and assertions
            lines = content.split('\n')
            in_test = False
            for line in lines:
                if line.strip().startswith('def test_'):
                    in_test = True
                    prompt += f"\n{line}\n"
                elif in_test and ('assert' in line or 'with pytest.raises' in line):
                    prompt += f"    {line.strip()}\n"
                elif in_test and line.strip() == "":
                    in_test = False
    
    prompt += "\n\nCRITICAL INSTRUCTIONS:\n"
    prompt += "1. Generate the COMPLETE FIXED FILE that makes ALL tests pass\n"
    prompt += "2. Fix ALL issues at once - do not leave any test failing\n"
    prompt += "3. Common fixes needed based on the patterns above:\n"
    prompt += "   - Wrong arithmetic operators (+ vs -, * vs /)\n"
    prompt += "   - Missing error checks (division by zero, negative square roots, empty lists)\n"
    prompt += "   - Incorrect return values\n"
    prompt += "4. Your fix MUST address all {0} failing tests\n".format(len(failing_tests))
    prompt += "5. Generate the COMPLETE file with ALL fixes applied\n"
    prompt += "6. PRESERVE all docstrings and comments from the original file\n"
    prompt += "7. Keep the original code style and formatting when possible\n"
    prompt += "\n"
    prompt += "FORMAT YOUR RESPONSE AS:\n"
    prompt += "FILE: <filename>\n"
    prompt += "```python\n"
    prompt += "<COMPLETE FIXED FILE CONTENTS>\n"
    prompt += "```\n"
    prompt += "\n"
    prompt += "REMEMBER: This is your ONE chance to fix EVERYTHING. Make it count!"
    
    return prompt


def build_strict_critic_prompt(patch: str, failing_tests: List[Dict[str, Any]], 
                             num_original_failures: int) -> str:
    """
    Build a strict critic prompt that rejects partial solutions.
    """
    prompt = f"""You are a STRICT code reviewer. Your job is to ensure the fix addresses ALL test failures.

ORIGINAL SITUATION:
- Total failing tests: {num_original_failures}
- Tests that MUST be fixed: {len(failing_tests)}

PATCH TO REVIEW:
```diff
{patch[:2000]}{'...(truncated)' if len(patch) > 2000 else ''}
```

REQUIREMENTS FOR APPROVAL:
1. The patch MUST fix ALL {num_original_failures} failing tests
2. Partial fixes are UNACCEPTABLE
3. The fix must be comprehensive and complete
4. No test should remain failing after this patch

ANALYZE:
1. Does this patch address ALL the failing tests listed?
2. Are there any tests that might still fail after this patch?
3. Is this a complete solution or just a partial fix?

BE EXTREMELY STRICT: If this patch doesn't fix ALL tests in one go, REJECT IT.

Respond with JSON:
{{"approved": true/false, "reason": "explanation", "fixes_all_tests": true/false, "estimated_tests_fixed": number}}

IMPORTANT: Only approve if you're confident this fixes ALL {num_original_failures} tests!"""
    
    return prompt


def parse_comprehensive_plan(response: str) -> Dict[str, Any]:
    """
    Parse the comprehensive plan from the planner's response.
    """
    plan = {
        "approach": "",
        "root_causes": [],
        "fixes": {},
        "verification": {}
    }
    
    # Extract root cause analysis
    if "ROOT CAUSE" in response:
        root_section = response[response.find("ROOT CAUSE"):].split("\n\n")[0]
        plan["approach"] = root_section
    
    # Extract specific fixes
    if "FIX LIST" in response or "COMPLETE FIX" in response:
        fix_section = response[response.find("FIX"):].split("\n\n")[0]
        # Parse individual fixes
        for line in fix_section.split('\n'):
            if '•' in line or '-' in line or line.strip().startswith(('1.', '2.', '3.')):
                fix = line.strip().lstrip('•-123456789. ')
                if ':' in fix:
                    func, change = fix.split(':', 1)
                    plan["fixes"][func.strip()] = change.strip()
    
    # If no structured parsing worked, use the whole response
    if not plan["approach"]:
        plan["approach"] = response.strip()
    
    return plan
