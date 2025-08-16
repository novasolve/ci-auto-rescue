"""
Mock LLM agent for generating patches to fix test failures.
This is a simple implementation for the E2E demo that analyzes 
test failures and generates appropriate patches.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Any


class MockLLMAgent:
    """Mock LLM agent that generates patches based on test failures."""
    
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
    
    def generate_patch(self, failing_tests: List[Dict[str, Any]], iteration: int, plan: Dict[str, Any] = None, critic_feedback: Optional[str] = None) -> Optional[str]:
        """
        Generate a patch to fix failing tests.
        
        Args:
            failing_tests: List of failing test details
            iteration: Current iteration number
            
        Returns:
            Unified diff string or None if no patch can be generated
        """
        if not failing_tests:
            return None
        
        # Fix tests one at a time
        test_index = min(iteration - 1, len(failing_tests) - 1)
        test = failing_tests[test_index]
        test_file = test.get("file", "")
        test_name = test.get("name", "")
        traceback = test.get("short_traceback", "")
        
        # Read the test file
        test_path = self.repo_path / test_file
        if not test_path.exists():
            return None
        
        content = test_path.read_text()
        
        # Analyze the error and generate appropriate fix
        if "test_simple_assertion_failure" in test_name:
            # Fix the assertion failure (2+2 should equal 4, not 5)
            return self._create_patch(
                test_file,
                "    assert result == 5, f\"Expected 5 but got {result}\"",
                "    assert result == 4, f\"Expected 4 but got {result}\""
            )
        
        elif "test_division_by_zero" in test_name or "ZeroDivisionError" in traceback:
            # Fix division by zero
            if "test_demo_fail_3" in test_name:
                return self._create_patch(
                    test_file,
                    "    y = 0\n    result = x / y  # Will raise ZeroDivisionError",
                    "    y = 2  # Fixed: avoid division by zero\n    result = x / y"
                )
            else:
                return self._create_patch(
                    test_file,
                    "    denominator = 0\n    result = numerator / denominator  # This will raise ZeroDivisionError",
                    "    denominator = 1  # Fixed: avoid division by zero\n    result = numerator / denominator"
                )
        
        elif "test_undefined_variable" in test_name:
            # Fix undefined variable
            return self._create_patch(
                test_file,
                "    result = undefined_var + 5  # NameError",
                "    undefined_var = 5  # Define the variable\n    result = undefined_var + 5"
            )
        
        elif "test_list_index_error" in test_name:
            # Fix index error
            return self._create_patch(
                test_file,
                "    value = my_list[10]  # IndexError",
                "    value = my_list[-1] if my_list else 4  # Fixed: use safe index"
            )
        
        elif "test_type_error" in test_name:
            # Fix type error
            return self._create_patch(
                test_file,
                "    result = \"string\" + 5  # TypeError: can't concatenate str and int",
                "    result = \"string\" + str(5)  # Fixed: convert int to string"
            )
        
        elif "test_demo_fail_1" in test_name:
            # Fix demo assertion
            return self._create_patch(
                test_file,
                "    assert 1 == 2, \"Demo failure: 1 does not equal 2\"",
                "    assert 1 == 1, \"Fixed: 1 equals 1\""
            )
        
        elif "test_demo_fail_2" in test_name:
            # Fix status check
            return self._create_patch(
                test_file,
                "    result = {\"status\": \"error\"}",
                "    result = {\"status\": \"success\"}  # Fixed: set status to success"
            )
        
        return None
    
    def _create_patch(self, file_path: str, old_content: str, new_content: str) -> str:
        """
        Create a unified diff patch.
        
        Args:
            file_path: Path to the file being patched
            old_content: Content to replace
            new_content: New content
            
        Returns:
            Unified diff string
        """
        # Read the full file
        full_path = self.repo_path / file_path
        if not full_path.exists():
            return None
        
        lines = full_path.read_text().splitlines(keepends=True)
        
        # Find the line numbers
        old_lines = old_content.splitlines()
        start_line = None
        for i, line in enumerate(lines):
            if old_lines[0] in line:
                # Check if all lines match
                match = True
                for j, old_line in enumerate(old_lines):
                    if i + j >= len(lines) or old_line not in lines[i + j]:
                        match = False
                        break
                if match:
                    start_line = i + 1  # 1-based line numbers
                    break
        
        if start_line is None:
            return None
        
        # Create the unified diff
        new_lines = new_content.splitlines()
        
        diff = f"--- a/{file_path}\n"
        diff += f"+++ b/{file_path}\n"
        diff += f"@@ -{start_line},{len(old_lines)} +{start_line},{len(new_lines)} @@\n"
        
        # Add context (1 line before and after)
        if start_line > 1:
            diff += f" {lines[start_line - 2]}"
        
        # Add removed lines
        for old_line in old_lines:
            diff += f"-{old_line}\n"
        
        # Add new lines
        for new_line in new_lines:
            diff += f"+{new_line}\n"
        
        # Add context (1 line after)
        end_line = start_line + len(old_lines) - 1
        if end_line < len(lines):
            diff += f" {lines[end_line]}"
        
        return diff
    
    def review_patch(self, patch: str, failing_tests: List[Dict[str, Any]] = None) -> tuple[bool, str]:
        """
        Review a patch (mock critic).
        
        Args:
            patch: The patch diff to review
            failing_tests: Optional list of failing tests
            
        Returns:
            Tuple of (approved: bool, reason: str)
        """
        # Simple validation: check patch is not empty and not too large
        if not patch:
            return False, "Empty patch"
        
        lines = patch.split('\n')
        if len(lines) > 1000:  # Too large
            return False, f"Patch too large ({len(lines)} lines)"
        
        # Check that it's a valid diff format
        if not any(line.startswith('---') for line in lines):
            return False, "Invalid diff format: missing --- header"
        if not any(line.startswith('+++') for line in lines):
            return False, "Invalid diff format: missing +++ header"
        
        return True, "Patch approved (mock review)"
    
    def create_plan(self, failing_tests: List[Dict[str, Any]], iteration: int, critic_feedback: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a plan for fixing the failing tests (mock planner).
        
        Args:
            failing_tests: List of failing test details
            iteration: Current iteration number
            
        Returns:
            Plan dictionary with approach and steps
        """
        if not failing_tests:
            return {"approach": "No failures to fix", "target_tests": [], "steps": []}
        
        # Create a simple mock plan based on the test failures
        steps = []
        
        if any("assertion" in str(test.get("short_traceback", "")).lower() for test in failing_tests):
            steps.append("Fix assertion failures")
        
        if any("ZeroDivisionError" in str(test.get("short_traceback", "")) for test in failing_tests):
            steps.append("Fix division by zero errors")
        
        if any("NameError" in str(test.get("short_traceback", "")) for test in failing_tests):
            steps.append("Define undefined variables")
        
        if any("IndexError" in str(test.get("short_traceback", "")) for test in failing_tests):
            steps.append("Fix list index errors")
        
        if any("TypeError" in str(test.get("short_traceback", "")) for test in failing_tests):
            steps.append("Fix type errors")
        
        if not steps:
            steps = ["Analyze test failures", "Fix identified issues", "Verify fixes"]
        
        return {
            "approach": f"Fix {len(failing_tests)} failing test(s) systematically",
            "steps": steps,
            "target_tests": failing_tests[:3] if len(failing_tests) > 3 else failing_tests,
            "iteration": iteration
        }
