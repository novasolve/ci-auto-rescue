"""
Output Parser for Deep Agent Responses
=======================================

Parses and validates agent outputs to ensure compliance with format specifications.
"""

import json
import re
from typing import Any, Dict, Optional, Tuple
from pydantic import ValidationError

from .system_prompt import ResponseFormat, ToolResponse


class AgentOutputParser:
    """Parse and validate Deep Agent outputs."""
    
    @staticmethod
    def parse_json_response(text: str) -> Optional[ResponseFormat]:
        """
        Extract and parse JSON response from agent output.
        
        Args:
            text: Raw agent output text
            
        Returns:
            Parsed ResponseFormat or None if parsing fails
        """
        # Try to find JSON in code blocks first
        json_pattern = r'```json\s*\n(.*?)\n```'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        if matches:
            json_str = matches[0]
        else:
            # Try to find raw JSON
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            matches = re.findall(json_pattern, text)
            if matches:
                json_str = matches[0]
            else:
                return None
        
        try:
            data = json.loads(json_str)
            return ResponseFormat(**data)
        except (json.JSONDecodeError, ValidationError) as e:
            print(f"Failed to parse response: {e}")
            return None
    
    @staticmethod
    def parse_tool_response(tool_name: str, result: Any) -> ToolResponse:
        """
        Parse tool execution result into structured format.
        
        Args:
            tool_name: Name of the executed tool
            result: Raw tool result
            
        Returns:
            Structured ToolResponse
        """
        # Handle different result types
        if isinstance(result, dict):
            if "error" in result:
                return ToolResponse(
                    tool_name=tool_name,
                    success=False,
                    result=result.get("result", ""),
                    error=result["error"]
                )
            else:
                return ToolResponse(
                    tool_name=tool_name,
                    success=result.get("success", True),
                    result=result
                )
        elif isinstance(result, str):
            # Check for error patterns
            if result.startswith("ERROR:") or "error" in result.lower():
                return ToolResponse(
                    tool_name=tool_name,
                    success=False,
                    result="",
                    error=result
                )
            else:
                return ToolResponse(
                    tool_name=tool_name,
                    success=True,
                    result=result
                )
        else:
            return ToolResponse(
                tool_name=tool_name,
                success=True,
                result=str(result)
            )
    
    @staticmethod
    def validate_patch(patch_text: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that a patch follows correct format and rules.
        
        Args:
            patch_text: Unified diff patch text
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not patch_text:
            return False, "Empty patch"
        
        lines = patch_text.split('\n')
        
        # Check for test file modifications (CORE RULE #1)
        for line in lines:
            if line.startswith('+++') or line.startswith('---'):
                if any(pattern in line for pattern in ['test_', '_test.py', '/tests/', '/test/']):
                    return False, "VIOLATION: Attempting to modify test files"
        
        # Check patch size (CORE RULE #2)
        change_lines = sum(1 for l in lines if l.startswith('+') or l.startswith('-'))
        if change_lines > 500:
            return False, f"VIOLATION: Patch too large ({change_lines} lines > 500 max)"
        
        # Check for basic diff format
        has_header = any(line.startswith('---') for line in lines)
        if not has_header:
            return False, "Invalid patch format: missing header"
        
        # Check for blocked paths (CORE RULE #4)
        blocked_patterns = ['.env', '.git/', 'secrets', '.github/', 'gitlab-ci']
        for line in lines:
            if line.startswith('+++') or line.startswith('---'):
                if any(pattern in line for pattern in blocked_patterns):
                    return False, f"VIOLATION: Attempting to modify protected file"
        
        return True, None
    
    @staticmethod
    def extract_tool_calls(text: str) -> list[Dict[str, Any]]:
        """
        Extract tool calls from agent output.
        
        Args:
            text: Agent output text
            
        Returns:
            List of tool calls with names and arguments
        """
        tool_calls = []
        
        # Pattern for function-style calls
        func_pattern = r'(\w+)\((.*?)\)'
        for match in re.finditer(func_pattern, text):
            tool_name = match.group(1)
            args_str = match.group(2)
            
            # Only process known tools
            known_tools = ['open_file', 'write_file', 'run_tests', 'apply_patch', 'critic_review']
            if tool_name in known_tools:
                tool_calls.append({
                    'name': tool_name,
                    'arguments': args_str
                })
        
        return tool_calls
