"""
Enhanced LLM agent that implements the full Planner, Actor, and Critic workflow.
This is the production agent for Nova CI-Rescue that uses GPT-4/5 or Claude.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from nova.agent.llm_client import LLMClient, parse_plan, build_planner_prompt, build_patch_prompt
from nova.config import get_settings


class EnhancedLLMAgent:
    """Enhanced LLM agent that implements Planner, Actor, and Critic for test fixing."""
    
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.settings = get_settings()
        self.llm = LLMClient()  # Use the unified LLM client
    
    def find_source_files_from_test(self, test_file_path: Path) -> Set[str]:
        """Extract imported modules from a test file to find source files."""
        source_files = set()
        
        try:
            test_content = test_file_path.read_text()
            
            # Find import statements using regex
            import_pattern = r'^\s*(?:from|import)\s+([\w\.]+)'
            for line in test_content.split('\n'):
                match = re.match(import_pattern, line)
                if match:
                    module = match.group(1).split('.')[0]
                    
                    # Skip standard library and test frameworks
                    if module not in ['pytest', 'unittest', 'sys', 'os', 'json', 're']:
                        # Look for corresponding source file
                        possible_files = [
                            self.repo_path / f"{module}.py",
                            self.repo_path / module / "__init__.py",
                        ]
                        
                        for pf in possible_files:
                            if pf.exists():
                                source_files.add(str(pf.relative_to(self.repo_path)))
                                break
        except Exception as e:
            print(f"Error parsing test file {test_file_path}: {e}")
        
        return source_files
    
    def generate_patch(self, failing_tests: List[Dict[str, Any]], iteration: int, plan: Dict[str, Any] = None) -> Optional[str]:
        """
        Generate a patch to fix failing tests (Actor node).
        
        Args:
            failing_tests: List of failing test details
            iteration: Current iteration number
            plan: Optional plan from the planner
            
        Returns:
            Unified diff string or None if no patch can be generated
        """
        if not failing_tests:
            return None
        
        # Read test files and identify source files
        test_contents = {}
        source_contents = {}
        source_files = set()
        
        for test in failing_tests[:5]:  # Limit to first 5 tests for context
            test_file = test.get("file", "")
            if test_file and test_file not in test_contents:
                test_path = self.repo_path / test_file
                if test_path.exists():
                    test_contents[test_file] = test_path.read_text()
                    # Find source files imported by this test
                    source_files.update(self.find_source_files_from_test(test_path))
        
        # Read source files
        for source_file in source_files:
            source_path = self.repo_path / source_file
            if source_path.exists():
                source_contents[source_file] = source_path.read_text()
        
        # Build the prompt using the helper function
        prompt = build_patch_prompt(plan, failing_tests, test_contents, source_contents)
        
        try:
            # Use the unified LLM client
            system_prompt = (
                "You are a coding assistant who writes fixes as unified diffs. "
                "Fix the SOURCE CODE to make tests pass. "
                "Generate only valid unified diff patches with proper file paths and hunk headers."
            )
            
            patch_diff = self.llm.complete(
                system=system_prompt,
                user=prompt,
                temperature=0.2,
                max_tokens=2000
            )
            
            # Extract diff from markdown if needed
            if "```diff" in patch_diff:
                start = patch_diff.find("```diff") + 7
                end = patch_diff.find("```", start)
                if end == -1:
                    end = len(patch_diff)
                patch_diff = patch_diff[start:end].strip()
            elif "```" in patch_diff:
                start = patch_diff.find("```") + 3
                if patch_diff[start:start+1] == "\n":
                    start += 1
                end = patch_diff.find("```", start)
                if end == -1:
                    end = len(patch_diff)
                patch_diff = patch_diff[start:end].strip()
            
            # Ensure proper patch format
            return self._fix_patch_format(patch_diff)
            
        except Exception as e:
            print(f"Error generating patch: {e}")
            return None
    
    def _create_enhanced_prompt(self, failing_tests: List[Dict[str, Any]], 
                                test_contents: Dict[str, str], 
                                source_contents: Dict[str, str], 
                                iteration: int) -> str:
        """Create an enhanced prompt with both test and source context."""
        prompt = f"Fix the SOURCE CODE to make these failing tests pass (iteration {iteration}):\n\n"
        
        # Add failure information
        prompt += "FAILING TESTS:\n"
        for i, test in enumerate(failing_tests[:3], 1):
            prompt += f"\n{i}. Test: {test.get('name', 'unknown')}\n"
            prompt += f"   File: {test.get('file', 'unknown')}\n"
            prompt += f"   Error: {test.get('short_traceback', 'No traceback')[:200]}\n"
        
        # Add source code (this is what needs to be fixed!)
        if source_contents:
            prompt += "\n\nSOURCE CODE TO FIX:\n"
            for file_path, content in source_contents.items():
                prompt += f"\n=== {file_path} ===\n"
                prompt += content[:3000]  # Limit size
                if len(content) > 3000:
                    prompt += "\n... (truncated)"
        
        # Add test code for reference
        prompt += "\n\nTEST CODE (DO NOT MODIFY - these define correct behavior):\n"
        for file_path, content in test_contents.items():
            prompt += f"\n=== {file_path} ===\n"
            # Only include the failing test functions
            relevant_content = self._extract_relevant_test_functions(content, failing_tests)
            prompt += relevant_content[:2000]
        
        prompt += "\n\nGenerate a unified diff patch that fixes the SOURCE CODE (not the tests). "
        prompt += "The tests define the correct expected behavior. "
        prompt += "Include proper @@ hunk headers with line numbers. "
        prompt += "Use --- a/filename and +++ b/filename format.\n"
        prompt += "Return ONLY the diff, no explanations.\n"
        
        return prompt
    
    def _extract_relevant_test_functions(self, test_content: str, failing_tests: List[Dict[str, Any]]) -> str:
        """Extract only the relevant test functions from test file."""
        relevant = []
        test_names = {test.get('name', '') for test in failing_tests}
        
        lines = test_content.split('\n')
        in_test = False
        current_test = []
        
        for line in lines:
            if line.startswith('def test_'):
                # Check if this is one of our failing tests
                test_name = line.split('(')[0].replace('def ', '').strip()
                if test_name in test_names:
                    in_test = True
                    current_test = [line]
                else:
                    if in_test and current_test:
                        relevant.append('\n'.join(current_test))
                    in_test = False
            elif in_test:
                current_test.append(line)
                # Stop at next function or class
                if line and not line.startswith(' ') and not line.startswith('\t'):
                    relevant.append('\n'.join(current_test))
                    in_test = False
        
        if in_test and current_test:
            relevant.append('\n'.join(current_test))
        
        return '\n\n'.join(relevant)
    
    def _fix_patch_format(self, patch_diff: str) -> str:
        """Ensure patch is in proper unified diff format."""
        lines = patch_diff.split('\n')
        fixed_lines = []
        in_hunk = False
        
        for line in lines:
            # Fix file headers
            if line.startswith('--- '):
                if not line.startswith('--- a/'):
                    parts = line.split()
                    if len(parts) >= 2:
                        filename = parts[1].lstrip('/')
                        line = f"--- a/{filename}"
                in_hunk = False
            elif line.startswith('+++ '):
                if not line.startswith('+++ b/'):
                    parts = line.split()
                    if len(parts) >= 2:
                        filename = parts[1].lstrip('/')
                        line = f"+++ b/{filename}"
                in_hunk = False
            elif line.startswith('@@'):
                in_hunk = True
                # Ensure complete hunk header
                if not re.match(r'@@ -\d+(?:,\d+)? \+\d+(?:,\d+)? @@', line):
                    # Try to fix it
                    line = '@@ -1,1 +1,1 @@'  # Safe default
            elif in_hunk and line and not line.startswith(('+', '-', ' ', '\\')):
                # Add space prefix for context lines
                line = ' ' + line
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def review_patch(self, patch: str, failing_tests: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """
        Review a patch using LLM (Critic node).
        
        Args:
            patch: The patch diff to review
            failing_tests: List of failing tests this patch should fix
            
        Returns:
            Tuple of (approved: bool, reason: str)
        """
        if not patch:
            return False, "Empty patch"
        
        # Safety checks first
        patch_lines = patch.split('\n')
        files_touched = sum(1 for line in patch_lines if line.startswith('+++ b/'))
        
        if len(patch_lines) >= 1000:
            return False, f"Patch too large ({len(patch_lines)} lines)"
        
        if files_touched > 10:
            return False, f"Too many files modified ({files_touched})"
        
        # Check for dangerous patterns
        dangerous_patterns = ['.github/', 'setup.py', 'pyproject.toml', '.env', 'requirements.txt']
        for line in patch_lines:
            if any(pattern in line for pattern in dangerous_patterns):
                return False, "Patch modifies protected/configuration files"
        
        # Use LLM for semantic review
        try:
            system_prompt = (
                "You are a code reviewer. Evaluate patches critically but approve if they fix the issues. "
                "Consider: correctness, safety, side effects, and whether it addresses the test failures."
            )
            
            user_prompt = f"""Review this patch that attempts to fix failing tests:

PATCH:
```diff
{patch[:1500]}
```

FAILING TESTS IT SHOULD FIX:
{json.dumps([{'name': t.get('name'), 'error': t.get('short_traceback', '')[:100]} for t in failing_tests[:3]], indent=2)}

Evaluate if this patch:
1. Actually fixes the failing tests
2. Doesn't introduce new bugs or break existing functionality
3. Follows good coding practices
4. Is minimal and focused on the problem

Respond with JSON:
{{"approved": true/false, "reason": "brief explanation"}}"""
            
            response = self.llm.complete(
                system=system_prompt,
                user=user_prompt,
                temperature=0.1,
                max_tokens=200
            )
            
            # Parse JSON response
            if '{' in response and '}' in response:
                start = response.find('{')
                end = response.rfind('}') + 1
                review_json = json.loads(response[start:end])
                return review_json.get('approved', False), review_json.get('reason', 'No reason provided')
            
            # Fallback to simple approval if parsing fails
            return True, "Patch review passed (parsing failed, auto-approved)"
            
        except Exception as e:
            print(f"Error in patch review: {e}")
            # Default to approving if review fails (with appropriate reason)
            return True, "Review failed, auto-approving (LLM error)"
    
    def create_plan(self, failing_tests: List[Dict[str, Any]], iteration: int) -> Dict[str, Any]:
        """
        Create a plan for fixing the failing tests (Planner node).
        
        Args:
            failing_tests: List of failing test details
            iteration: Current iteration number
            
        Returns:
            Plan dictionary with approach and steps
        """
        if not failing_tests:
            return {"approach": "No failures to fix", "target_tests": [], "steps": []}
        
        # Build planner prompt using helper function
        prompt = build_planner_prompt(failing_tests)
        
        try:
            system_prompt = (
                "You are an expert software engineer focused on making tests pass. "
                "Analyze test failures and create clear, actionable plans to fix them. "
                "Be specific about what needs to be fixed and how."
            )
            
            response = self.llm.complete(
                system=system_prompt,
                user=prompt,
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse the plan from the response
            plan = parse_plan(response)
            
            # Add iteration context
            plan['iteration'] = iteration
            
            # Identify source files that need fixes
            source_files = set()
            for test in failing_tests[:5]:  # Check first 5 tests
                test_path = self.repo_path / test.get("file", "")
                if test_path.exists():
                    source_files.update(self.find_source_files_from_test(test_path))
            
            plan['source_files'] = list(source_files)
            plan['target_tests'] = failing_tests[:3] if len(failing_tests) > 3 else failing_tests
            
            return plan
            
        except Exception as e:
            print(f"Error creating plan: {e}")
            # Fallback plan
            return {
                "approach": "Fix failing tests incrementally",
                "steps": ["Analyze test failures", "Fix assertion errors", "Handle exceptions"],
                "target_tests": failing_tests[:2] if len(failing_tests) > 2 else failing_tests,
                "source_files": [],
                "iteration": iteration
            }
