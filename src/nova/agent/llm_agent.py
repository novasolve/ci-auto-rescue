"""
LLM agent that implements the full Planner, Actor, and Critic workflow for test fixing.
Uses a unified LLM client (OpenAI/Anthropic) to analyze failures and generate fixes.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from nova.agent.llm_client import LLMClient, parse_plan, build_planner_prompt, build_patch_prompt
from nova.config import get_settings


class LLMAgent:
    """LLM agent that implements Planner, Actor, and Critic for test fixing."""
    
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.settings = get_settings()
        self.llm = LLMClient()  # Initialize unified LLM client (handles OpenAI/Anthropic)
    
    def find_source_files_from_test(self, test_file_path: Path) -> Set[str]:
        """Extract imported modules from a test file to find corresponding source files."""
        source_files = set()
        try:
            test_content = test_file_path.read_text()
            # Find import statements using regex
            import_pattern = r'^\s*(?:from|import)\s+([\w\.]+)'
            for line in test_content.split('\n'):
                match = re.match(import_pattern, line)
                if match:
                    module = match.group(1).split('.')[0]
                    # Skip standard library and common test frameworks
                    if module not in ['pytest', 'unittest', 'sys', 'os', 'json', 're']:
                        # Look for a corresponding source file (module.py or module/__init__.py)
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
    
    def generate_patch(self, failing_tests: List[Dict[str, Any]], iteration: int,
                       plan: Dict[str, Any] = None, critic_feedback: Optional[str] = None) -> Optional[str]:
        """
        Generate a patch to fix failing tests (Actor node).
        
        Args:
            failing_tests: List of failing test details.
            iteration: Current iteration number.
            plan: Optional plan from the planner.
            critic_feedback: Optional feedback from previous critic rejection.
        
        Returns:
            Unified diff string or None if no patch can be generated.
        """
        if not failing_tests:
            return None
        
        # Read failing test files and identify related source files
        test_contents: Dict[str, str] = {}
        source_contents: Dict[str, str] = {}
        source_files = set()
        for test in failing_tests[:5]:  # Limit to first 5 tests for context
            test_file = test.get("file", "")
            if test_file and test_file not in test_contents:
                test_path = self.repo_path / test_file
                if test_path.exists():
                    test_contents[test_file] = test_path.read_text()
                    # Find source files imported by this test
                    source_files.update(self.find_source_files_from_test(test_path))
        
        # Read content of identified source files
        for source_file in source_files:
            source_path = self.repo_path / source_file
            if source_path.exists():
                source_contents[source_file] = source_path.read_text()
        
        # Build the LLM prompt using helper (includes plan and critic feedback if provided)
        prompt = build_patch_prompt(plan, failing_tests, test_contents, source_contents, critic_feedback)
        
        try:
            # System prompt guiding the LLM to produce a patch diff
            system_prompt = (
                "You are a coding assistant who writes fixes as unified diffs. "
                "Fix the SOURCE CODE to make tests pass. "
                "Generate only valid unified diff patches with proper file paths and hunk headers. "
                "Ensure that each diff hunk header's line counts exactly match the changes made."
            )
            patch_diff = self.llm.complete(
                system=system_prompt,
                user=prompt,
                temperature=0.2,
                max_tokens=8000  # Use a high token limit to avoid truncation
            )
            
            # Extract the diff content from the LLM response if it's wrapped in markdown
            if "```diff" in patch_diff:
                start = patch_diff.find("```diff") + 7
                end = patch_diff.find("```", start)
                if end == -1:
                    # Closing ``` not found, patch might be truncated
                    print(f"Warning: Patch might be truncated (no closing ```)")
                    end = len(patch_diff)
                patch_diff = patch_diff[start:end].strip()
            elif "```" in patch_diff:
                start = patch_diff.find("```") + 3
                if patch_diff[start:start+1] == "\n":
                    start += 1
                end = patch_diff.find("```", start)
                if end == -1:
                    print(f"Warning: Patch might be truncated (no closing ```)")
                    end = len(patch_diff)
                patch_diff = patch_diff[start:end].strip()
            
            # Check if the diff appears incomplete (e.g., truncated mid-hunk)
            lines = patch_diff.split('\n')
            if lines and not lines[-1].startswith(('+', '-', ' ', '@', '\\')):
                # The last line of diff is not a standard diff line; likely truncated
                if len(lines) > 15:
                    print(f"Warning: Patch might be truncated at line {len(lines)}")
                    # Ask LLM to continue the diff from where it left off
                    continuation_prompt = "Continue generating the patch from where you left off. Start with the next line of the diff."
                    continuation = self.llm.complete(
                        system="Continue the unified diff patch. Output only the remaining diff lines.",
                        user=continuation_prompt,
                        temperature=0.2,
                        max_tokens=4000
                    )
                    # Append the continuation if it looks like valid diff content
                    if continuation and (continuation[0] in '+-@ \\' or continuation.startswith('@@')):
                        patch_diff = patch_diff + '\n' + continuation.strip()
                        print(f"Added {len(continuation.split(chr(10)))} continuation lines to patch")
            
            # Ensure the patch diff is properly formatted
            return self._fix_patch_format(patch_diff)
            
        except Exception as e:
            print(f"Error generating patch: {e}")
            return None
    
    def _fix_patch_format(self, patch_diff: str) -> str:
        """Ensure the patch diff is in proper unified diff format."""
        patch_diff = patch_diff.rstrip()
        # Remove any trailing partial characters that aren't part of the diff
        if patch_diff and patch_diff[-1] not in '\n+-@ \\':
            while patch_diff and patch_diff[-1] not in '\n+-@ \\abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789)"}\'':
                patch_diff = patch_diff[:-1]
        
        lines = patch_diff.split('\n')
        fixed_lines: List[str] = []
        in_hunk = False
        
        for line in lines:
            # Fix diff file header lines if missing prefix
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
                # Ensure the hunk header has valid format
                if not re.match(r'@@ -\d+(?:,\d+)? \+\d+(?:,\d+)? @@', line):
                    line = '@@ -1,1 +1,1 @@'  # Default safe hunk header if missing
            elif in_hunk and line and not line.startswith(('+', '-', ' ', '\\')):
                # Prepend a space for context lines that are missing a leading space
                line = ' ' + line
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def review_patch(self, patch: str, failing_tests: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """
        Review a patch using LLM (Critic node).
        
        Args:
            patch: The patch diff to review.
            failing_tests: List of failing tests this patch is intended to fix.
        
        Returns:
            (approved: bool, reason: str) indicating if the patch is approved and the reason.
        """
        if not patch:
            return False, "Empty patch"
        
        # Basic safety limits for the patch before LLM review
        patch_lines = patch.split('\n')
        files_touched = sum(1 for line in patch_lines if line.startswith('+++ b/'))
        
        if len(patch_lines) >= 1000:
            return False, f"Patch too large ({len(patch_lines)} lines)"
        
        if files_touched > 10:
            return False, f"Too many files modified ({files_touched})"
        
        # Disallow modifications to critical or config files for safety
        dangerous_patterns = ['.github/', 'setup.py', 'pyproject.toml', '.env', 'requirements.txt']
        for line in patch_lines:
            if any(pattern in line for pattern in dangerous_patterns):
                return False, "Patch modifies protected/configuration files"
        
        # Repo-aware duplicate function definition check before LLM review
        try:
            dup_error = self._detect_duplicate_defs_against_repo(patch)
            if dup_error:
                return False, dup_error
        except Exception:
            # Non-fatal; fall through to LLM critic
            pass

        # Use LLM to perform semantic review of the patch
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
 5. Doesn't introduce duplicate function definitions (modifies existing functions rather than adding new ones)
 
 Respond with JSON:
 {"approved": true/false, "reason": "brief explanation"}"""
            
            response = self.llm.complete(
                system=system_prompt,
                user=user_prompt,
                temperature=0.1,
                max_tokens=200
            )
            
            # Parse JSON response from LLM
            if '{' in response and '}' in response:
                start = response.find('{')
                end = response.rfind('}') + 1
                review_json = json.loads(response[start:end])
                return review_json.get('approved', False), review_json.get('reason', 'No reason provided')
            
            # If parsing fails, default to approving (with generic reason)
            return True, "Patch review passed (parsing failed, auto-approved)"
            
        except Exception as e:
            print(f"Error in patch review: {e}")
            # If review process fails, default to approving the patch
            return True, "Review failed, auto-approving (LLM error)"

    def _detect_duplicate_defs_against_repo(self, patch: str) -> Optional[str]:
        """Detect added function definitions that duplicate existing ones in repo without removal.
        Returns an error message if duplication is detected; otherwise None.
        """
        try:
            patch_lines = patch.split('\n')
            current_file: Optional[str] = None
            for line in patch_lines:
                if line.startswith('+++ '):
                    parts = line.split()
                    if len(parts) > 1:
                        file_path = parts[1]
                        if file_path.startswith('b/'):
                            file_path = file_path[2:]
                        current_file = file_path
                    else:
                        current_file = None
                    continue

                if not current_file:
                    continue

                # Only consider python files
                if not current_file.endswith('.py'):
                    continue

                if line.startswith('+'):
                    stripped = line[1:].lstrip()
                    if stripped.startswith('def '):
                        func_name = stripped[len('def '):].split('(')[0].strip()
                        orig_path = self.repo_path / current_file
                        original_content = ""
                        try:
                            original_content = orig_path.read_text()
                        except Exception:
                            original_content = ""
                        if f"def {func_name}(" in original_content:
                            # Ensure the original def is being removed somewhere in patch
                            original_def_removed = any(
                                ol.startswith('-') and ol[1:].lstrip().startswith(f"def {func_name}(")
                                for ol in patch_lines
                            )
                            if not original_def_removed:
                                return (
                                    f"Patch introduces a duplicate definition of function '{func_name}' "
                                    f"in {current_file}. Modify the existing function in-place instead."
                                )
            return None
        except Exception:
            return None
    
    def create_plan(self, failing_tests: List[Dict[str, Any]], iteration: int,
                    critic_feedback: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a plan for fixing the failing tests (Planner node).
        
        Args:
            failing_tests: List of failing test details.
            iteration: Current iteration number.
            critic_feedback: Optional feedback from previous critic rejection.
        
        Returns:
            Plan dictionary with approach and steps (and additional context like target tests and source files).
        """
        if not failing_tests:
            return {"approach": "No failures to fix", "target_tests": [], "steps": []}
        
        # Build planner prompt, including any critic feedback from a rejected attempt
        prompt = build_planner_prompt(failing_tests, critic_feedback)
        
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
            
            # Parse the plan from the LLM response
            plan = parse_plan(response)
            
            # Attach iteration info
            plan['iteration'] = iteration
            
            # Determine source files that likely need fixes (from test imports)
            source_files = set()
            for test in failing_tests[:5]:
                test_path = self.repo_path / test.get("file", "")
                if test_path.exists():
                    source_files.update(self.find_source_files_from_test(test_path))
            
            plan['source_files'] = list(source_files)
            
            # Select a subset of failing tests to prioritize (first 3 or all if fewer)
            plan['target_tests'] = failing_tests[:3] if len(failing_tests) > 3 else failing_tests
            
            return plan
            
        except Exception as e:
            print(f"Error creating plan: {e}")
            # Fallback plan if LLM plan generation fails
            return {
                "approach": "Fix failing tests incrementally",
                "steps": ["Analyze test failures", "Fix assertion errors", "Handle exceptions"],
                "target_tests": failing_tests[:2] if len(failing_tests) > 2 else failing_tests,
                "source_files": [],
                "iteration": iteration
            }


# For backward compatibility, create an alias
EnhancedLLMAgent = LLMAgent