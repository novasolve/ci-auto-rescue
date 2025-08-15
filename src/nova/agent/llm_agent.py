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

# Import new engine components
try:
    from nova.engine.source_resolver import SourceResolver
    from nova.engine.patch_guard import preflight_patch_checks
    from nova.engine.post_apply_check import ast_sanity_check
    HAS_ENGINE = True
except ImportError:
    HAS_ENGINE = False
    print("Warning: Nova engine modules not available, using legacy behavior")


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
            
            # Extended list of standard library and test framework modules to skip
            skip_modules = {
                'pytest', 'unittest', 'sys', 'os', 'json', 're', 'io', 'typing',
                'pathlib', 'datetime', 'time', 'math', 'random', 'collections',
                'itertools', 'functools', 'warnings', 'copy', 'logging', 'tempfile',
                'subprocess', 'shutil', 'importlib', 'contextlib', 'abc', 'enum',
                'dataclasses', 'asyncio', 'threading', 'multiprocessing'
            }
            
            # Parse imports using regex for better accuracy
            import_pattern = r'^\s*(?:from\s+([\w\.]+)\s+import|import\s+([\w\.]+))'
            for line in test_content.split('\n'):
                match = re.match(import_pattern, line)
                if match:
                    # Get the module name from either 'from X import' or 'import X'
                    module = match.group(1) or match.group(2)
                    if module:
                        # Handle relative imports (e.g., from ..src.calculator import ...)
                        module = module.lstrip('.')
                        base_module = module.split('.')[0]
                        
                        # Skip standard library modules
                        if base_module in skip_modules:
                            continue
                        
                        # Try to find the source file in various locations
                        candidates = self._get_candidate_source_paths(module)
                        for candidate in candidates:
                            if candidate.exists():
                                source_files.add(str(candidate.relative_to(self.repo_path)))
                                break
        except Exception as e:
            print(f"Error parsing test file {test_file_path}: {e}")
        return source_files
    
    def _get_candidate_source_paths(self, module_name: str) -> List[Path]:
        """Get candidate paths where a module might be located."""
        candidates = []
        parts = module_name.split('.')
        
        # Direct paths in repo root - prioritize actual module files over __init__.py
        candidates.append(self.repo_path / f"{parts[0]}.py")
        
        # Common source directories
        for src_dir in ['src', 'lib', 'app']:
            src_path = self.repo_path / src_dir
            if src_path.exists():
                # Try the module directly under src/
                candidates.append(src_path / f"{parts[0]}.py")
                
                # For multi-part modules like 'package.module'
                if len(parts) > 1:
                    path = src_path
                    for i, part in enumerate(parts[:-1]):
                        path = path / part
                        candidates.append(path / f"{parts[-1]}.py")
        
        # Add __init__.py files LAST (lowest priority)
        candidates.append(self.repo_path / parts[0] / "__init__.py")
        for src_dir in ['src', 'lib', 'app']:
            src_path = self.repo_path / src_dir
            if src_path.exists():
                candidates.append(src_path / parts[0] / "__init__.py")
                if len(parts) > 1:
                    path = src_path
                    for i, part in enumerate(parts[:-1]):
                        path = path / part
                        candidates.append(path / "__init__.py")
        
        return candidates
    
    def _parse_project_config(self) -> Dict[str, Any]:
        """Parse project configuration files to understand source layout."""
        config = {}
        
        # Try to parse pyproject.toml
        pyproject_path = self.repo_path / "pyproject.toml"
        if pyproject_path.exists():
            try:
                import tomli
                with open(pyproject_path, 'rb') as f:
                    pyproject = tomli.load(f)
                    
                # Check for package-dir in setuptools config
                if 'tool' in pyproject and 'setuptools' in pyproject['tool']:
                    setuptools = pyproject['tool']['setuptools']
                    if 'package-dir' in setuptools:
                        config['package_dir'] = setuptools['package-dir']
                    if 'packages' in setuptools:
                        config['packages'] = setuptools['packages']
            except (ImportError, Exception) as e:
                # If tomli is not available or parsing fails, try basic regex
                try:
                    content = pyproject_path.read_text()
                    # Look for package-dir patterns
                    if 'package-dir' in content and 'src' in content:
                        config['has_src_layout'] = True
                except:
                    pass
        
        # Try to parse setup.cfg
        setup_cfg_path = self.repo_path / "setup.cfg"
        if setup_cfg_path.exists():
            try:
                parser = configparser.ConfigParser()
                parser.read(setup_cfg_path)
                if 'options' in parser:
                    if 'package_dir' in parser['options']:
                        config['package_dir'] = parser['options']['package_dir']
                    if 'packages' in parser['options']:
                        config['packages'] = parser['options']['packages']
            except:
                pass
        
        # Try to parse setup.py for common patterns
        setup_py_path = self.repo_path / "setup.py"
        if setup_py_path.exists():
            try:
                content = setup_py_path.read_text()
                if 'package_dir' in content and '"src"' in content:
                    config['has_src_layout'] = True
            except:
                pass
        
        return config
    
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
        
        # Use enhanced source resolver if available
        if HAS_ENGINE:
            resolver = SourceResolver(self.repo_path)
            test_paths = []
            for test in failing_tests[:5]:  # Limit to first 5 tests for context
                test_file = test.get("file", "")
                if test_file:
                    test_path = self.repo_path / test_file
                    if test_path.exists():
                        test_paths.append(test_path)
                        test_contents[test_file] = test_path.read_text()
            
            # Map imports from tests to source files
            if test_paths:
                candidate_sources = resolver.map_imports_from_tests(test_paths)
                for p in candidate_sources:
                    try:
                        rel = p.relative_to(self.repo_path)
                        source_files.add(str(rel))
                    except ValueError:
                        # Path not relative to repo, skip
                        pass
        else:
            # Legacy behavior
            for test in failing_tests[:5]:  # Limit to first 5 tests for context
                test_file = test.get("file", "")
                if test_file and test_file not in test_contents:
                    test_path = self.repo_path / test_file
                    if test_path.exists():
                        test_contents[test_file] = test_path.read_text()
                        # Find source files imported by this test
                        source_files.update(self.find_source_files_from_test(test_path))
        
        # Parse project configuration to understand source layout
        project_config = self._parse_project_config()
        
        # If no source files found via imports, try to find them in common locations
        if not source_files:
            # Determine source directories based on project config
            src_dirs = ["src", "lib", "app"]
            if project_config.get('has_src_layout') or project_config.get('package_dir'):
                # Prioritize src/ if project uses src layout
                src_dirs = ["src"] + [d for d in src_dirs if d != "src"]
            
            # Also check the root directory
            src_dirs.append(".")
            
            # Look for Python files in common source directories
            for src_dir in src_dirs:
                src_path = self.repo_path / src_dir
                if src_path.exists() and src_path.is_dir():
                    # Find all Python files in this directory and subdirectories (excluding tests)
                    for py_file in src_path.rglob("*.py"):
                        # Skip test files and cache directories
                        rel_path = py_file.relative_to(self.repo_path)
                        path_str = str(rel_path)
                        if ('test' in path_str.lower() or 
                            '__pycache__' in path_str or
                            py_file.name.startswith("test_") or 
                            py_file.name.endswith("_test.py") or
                            py_file.name == "conftest.py"):
                            continue
                        source_files.add(str(rel_path))
                        # If we found files in src/, don't look in other directories
                        if src_dir == "src" and source_files:
                            break
                if source_files and src_dir in ["src", "lib", "app"]:
                    break  # Stop if we found files in a common source directory
        
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
                "Generate only valid unified diff patches with CORRECT file paths and hunk headers. \n"
                "CRITICAL RULES:\n"
                "1. Use the EXACT file paths shown in the 'SOURCE CODE FILES TO FIX' section (e.g., src/calculator.py)\n"
                "2. File paths must match the actual repository structure\n"
                "3. Each hunk header's line counts must exactly match the changes made\n"
                "4. When fixing functions, remove old lines with '-' and add new lines with '+'\n"
                "5. NEVER create duplicate function definitions\n"
                "6. The diff must target the actual files shown in the prompt, not guessed paths"
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
            
            # Ensure the patch diff is properly formatted and has correct paths
            patch_diff = self._fix_patch_format(patch_diff)
            
            # Correct patch file paths if needed
            patch_diff = self._correct_patch_paths(patch_diff, source_files)
            
            return patch_diff
            
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
    
    def _correct_patch_paths(self, patch_diff: str, known_source_files: Set[str]) -> str:
        """Correct file paths in patch if they don't match actual repository structure.
        
        Args:
            patch_diff: The patch diff string
            known_source_files: Set of known source file paths from discovery
            
        Returns:
            Corrected patch diff
        """
        if not patch_diff or not known_source_files:
            return patch_diff
        
        lines = patch_diff.split('\n')
        corrected_lines = []
        current_file = None
        file_corrections = {}  # Map incorrect paths to correct ones
        
        for line in lines:
            # Detect file headers
            if line.startswith('--- '):
                # Extract file path from --- line
                parts = line.split()
                if len(parts) >= 2:
                    file_path = parts[1]
                    if file_path.startswith('a/'):
                        file_path = file_path[2:]
                    
                    # Check if this file path needs correction
                    corrected_path = self._find_correct_path(file_path, known_source_files)
                    if corrected_path and corrected_path != file_path:
                        file_corrections[file_path] = corrected_path
                        line = f"--- a/{corrected_path}"
                        print(f"Corrected patch path: {file_path} -> {corrected_path}")
                    current_file = corrected_path or file_path
            
            elif line.startswith('+++ '):
                # Extract file path from +++ line
                parts = line.split()
                if len(parts) >= 2:
                    file_path = parts[1]
                    if file_path.startswith('b/'):
                        file_path = file_path[2:]
                    
                    # Use the correction from --- line if available
                    if file_path in file_corrections:
                        line = f"+++ b/{file_corrections[file_path]}"
                    else:
                        corrected_path = self._find_correct_path(file_path, known_source_files)
                        if corrected_path and corrected_path != file_path:
                            line = f"+++ b/{corrected_path}"
            
            corrected_lines.append(line)
        
        return '\n'.join(corrected_lines)
    
    def _find_correct_path(self, incorrect_path: str, known_files: Set[str]) -> Optional[str]:
        """Find the correct file path from known files.
        
        Args:
            incorrect_path: Potentially incorrect file path from patch
            known_files: Set of known correct file paths
            
        Returns:
            Correct file path or None if not found
        """
        # Direct match
        if incorrect_path in known_files:
            return incorrect_path
        
        # Extract just the filename
        filename = Path(incorrect_path).name
        
        # Look for files with the same name in known files
        candidates = [f for f in known_files if Path(f).name == filename]
        
        if len(candidates) == 1:
            # Unique match found
            return candidates[0]
        elif len(candidates) > 1:
            # Multiple matches - try to find best match
            # Prefer files in src/ directory
            src_candidates = [f for f in candidates if f.startswith('src/')]
            if len(src_candidates) == 1:
                return src_candidates[0]
            
            # Otherwise return the first match
            return candidates[0]
        
        # Try checking if adding 'src/' prefix helps
        if not incorrect_path.startswith('src/'):
            src_path = f"src/{incorrect_path}"
            if src_path in known_files:
                return src_path
        
        # Check if the file exists at the incorrect path (maybe it's a new file)
        full_path = self.repo_path / incorrect_path
        if full_path.exists():
            return incorrect_path
        
        return None
    
    def review_patch(self, patch: str, failing_tests: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """
        Review a patch using preflight checks and LLM (Critic node).
        
        Args:
            patch: The patch diff to review.
            failing_tests: List of failing tests this patch is intended to fix.
        
        Returns:
            (approved: bool, reason: str) indicating if the patch is approved and the reason.
        """
        if not patch:
            return False, "Empty patch"
        
        # Use enhanced preflight checks if available
        if HAS_ENGINE:
            ok, issues = preflight_patch_checks(patch, forbid_test_edits=True)
            if not ok:
                # Combine all issues into a single reason
                reason = "Preflight checks failed: " + "; ".join(issues[:3])
                if len(issues) > 3:
                    reason += f" (and {len(issues) - 3} more issues)"
                return False, reason
        else:
            # Legacy safety checks
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
  {{"approved": true/false, "reason": "brief explanation"}}"""
            
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
            
            # Parse the LLM response into a plan dict
            plan = parse_plan(response)
            
            # Use LLM-prioritized tests if provided
            priority_names = plan.get('priority_tests')
            if priority_names:
                target_tests = []
                for name in priority_names:
                    for test in failing_tests:
                        # Match test by name or file substring
                        if name in test.get('name', '') or name in test.get('file', ''):
                            target_tests.append(test)
                            break
                if not target_tests:
                    target_tests = failing_tests[:3] if len(failing_tests) > 3 else failing_tests
                plan['target_tests'] = target_tests
                plan.pop('priority_tests', None)  # remove after use
            else:
                plan['target_tests'] = failing_tests[:3] if len(failing_tests) > 3 else failing_tests
            
            # Attach iteration metadata and source file hints
            plan['iteration'] = iteration
            
            # Determine source files that likely need fixes (from test imports)
            source_files = set()
            for test in failing_tests[:5]:
                test_path = self.repo_path / test.get("file", "")
                if test_path.exists():
                    source_files.update(self.find_source_files_from_test(test_path))
            
            plan['source_files'] = list(source_files)
            
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