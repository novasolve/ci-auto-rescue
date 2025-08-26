"""
Fixed version of llm_client.py that generates complete file replacements instead of patches.
This is a temporary fix for earlier demos.
"""

from typing import Dict, Any, List, Optional


def build_full_file_prompt(plan: Dict[str, Any], failing_tests: List[Dict[str, Any]], 
                          test_contents: Dict[str, str] = None, 
                          source_contents: Dict[str, str] = None,
                          critic_feedback: Optional[str] = None) -> str:
    """
    Build a prompt for the actor to generate complete fixed files instead of patches.
    
    Args:
        plan: The plan created by the planner
        failing_tests: List of failing test details
        test_contents: Optional dict of test file contents
        source_contents: Optional dict of source file contents
        critic_feedback: Optional feedback from previous critic rejection
        
    Returns:
        Formatted prompt string
    """
    prompt = ""
    
    # Include critic feedback if available
    if critic_feedback:
        prompt += "⚠️ PREVIOUS FIX REJECTED:\n"
        prompt += f'"{critic_feedback}"\n\n'
        prompt += "Generate a DIFFERENT fix that avoids these issues.\n\n"
    
    prompt += "Generate the complete, corrected file contents to fix the failing tests.\n\n"
    
    # Include the plan
    if plan:
        prompt += "PLAN:\n"
        if isinstance(plan.get('approach'), str):
            prompt += f"Approach: {plan['approach']}\n"
        if plan.get('steps'):
            prompt += "Steps:\n"
            for i, step in enumerate(plan['steps'][:5], 1):
                prompt += f"  {i}. {step}\n"
        prompt += "\n"
    
    # Include failing test details
    prompt += "FAILING TESTS TO FIX:\n"
    for i, test in enumerate(failing_tests[:3], 1):
        prompt += f"\n{i}. Test: {test.get('name', 'unknown')}\n"
        prompt += f"   File: {test.get('file', 'unknown')}\n"
        prompt += f"   Line: {test.get('line', 0)}\n"
        
        # Extract actual vs expected from error message if present
        error_msg = test.get('short_traceback', 'No traceback')[:400]
        prompt += f"   Error:\n{error_msg}\n"
    
    # Include test file contents if provided
    if test_contents:
        prompt += "\n\nTEST FILE CONTENTS (for reference only):\n"
        for file_path, content in test_contents.items():
            prompt += f"\n=== {file_path} ===\n"
            prompt += content[:2000]
            if len(content) > 2000:
                prompt += "\n... (truncated)"
    
    # Include source file contents if provided - THIS IS WHAT WE NEED TO FIX
    if source_contents:
        prompt += "\n\nCURRENT SOURCE CODE (FIX THIS):\n"
        for file_path, content in source_contents.items():
            prompt += f"\n=== {file_path} ===\n"
            prompt += content
            if len(content) > 2000:
                prompt += "\n... (truncated)"
    
    prompt += "\n\n"
    prompt += "INSTRUCTIONS:\n"
    prompt += "1. Analyze the failing tests and current source code\n"
    prompt += "2. Identify what's wrong in the source code\n"
    prompt += "3. Generate the COMPLETE CORRECTED FILE CONTENTS that will make the tests pass\n"
    prompt += "4. The response format should be:\n\n"
    prompt += "FILE: <filename>\n"
    prompt += "```python\n"
    prompt += "<complete corrected file contents>\n"
    prompt += "```\n"
    prompt += "\n"
    prompt += "If multiple files need to be fixed, include each one with the FILE: header.\n"
    prompt += "Return ONLY the file contents, no explanations.\n"
    
    return prompt


def convert_full_file_to_patch(file_path: str, new_content: str, repo_path: Any) -> str:
    """
    Convert a full file replacement to a unified diff patch.
    
    Args:
        file_path: Path to the file being replaced
        new_content: The new complete file content
        repo_path: Repository root path
        
    Returns:
        Unified diff string
    """
    from pathlib import Path
    
    # Read the current file content
    full_path = Path(repo_path) / file_path
    if full_path.exists():
        old_content = full_path.read_text()
    else:
        old_content = ""
    
    # Ensure newlines are consistent
    if not new_content.endswith('\n'):
        new_content += '\n'
    
    # Generate a simple unified diff that replaces the entire file
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    
    # Build the diff - use exact line count
    old_line_count = len(old_lines) if old_lines else 0
    new_line_count = len(new_lines) if new_lines else 0
    
    diff_lines = [
        f"--- a/{file_path}\n",
        f"+++ b/{file_path}\n",
        f"@@ -1,{old_line_count} +1,{new_line_count} @@\n"
    ]
    
    # Remove all old lines (ensure they have newlines)
    for line in old_lines:
        if not line.endswith('\n'):
            line += '\n'
        diff_lines.append(f"-{line}")
    
    # Add all new lines (ensure they have newlines)
    for i, line in enumerate(new_lines):
        if not line.endswith('\n') and i < len(new_lines) - 1:
            line += '\n'
        diff_lines.append(f"+{line}")
    
    return "".join(diff_lines)
