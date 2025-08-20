"""
PR Generator - Uses GPT-5 to create pull request descriptions and submit them via GitHub CLI.
"""

import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from nova.agent.llm_client import LLMClient


class PRGenerator:
    """Generates and creates pull requests using AI and GitHub CLI."""
    
    def __init__(self, repo_path: Path):
        self.repo_path = Path(repo_path)
        self.llm = LLMClient()
    
    def generate_pr_content(self, 
                          fixed_tests: List[Dict],
                          patches_applied: List[str],
                          changed_files: List[str],
                          execution_time: str,
                          reasoning_logs: Optional[List[Dict]] = None) -> Tuple[str, str]:
        """
        Use GPT-5 to generate PR title and description based on what was fixed.
        
        Returns:
            Tuple of (title, description)
        """
        # Get the final diff
        final_diff = self._get_combined_diff()
        
        # Extract reasoning summary from logs
        reasoning_summary = self._extract_reasoning_summary(reasoning_logs) if reasoning_logs else ""
        
        # Build the comprehensive prompt based on the user's template
        prompt = f"""TASK: Write a compelling pull request title and a detailed pull request description for the following code changes.

The code changes (diff) were made to automatically fix failing tests. Below you have:
- A GIT DIFF of the changes.
- A summary of the test failures and reasoning behind the fixes.

FORMAT:
Title: <strong, action-oriented PR title that emphasizes the value/impact>

<Multiple lines of PR description in Markdown>

GUIDELINES for the PR title:
- Use strong action verbs (e.g., "Restore", "Repair", "Fix critical", "Resolve")
- Be specific about what was fixed (e.g., "Restore calculator operations and error handling")
- Convey urgency/importance when appropriate
- Avoid generic titles like "Fix failing tests"

GUIDELINES for the PR description:
- Start with a brief sentence or two explaining the *problem* and the *solution* at a high level.
- Then provide details: what was changed in the code and why those changes fix the issue.
- Reference relevant functions/files (e.g., "Adjusted logic in `calculator.py` to handle negative inputs").
- Mention the outcome (e.g., "Now all tests pass, including X and Y that previously failed.").
- Use bullet points for multiple changes or steps, if it improves readability.
- Use a professional, clear tone. (Imagine a developer writing the PR.)
- Include sections: ## Summary, ## What was fixed, ## Changes made, ## Test results, ## Technical details (if relevant)

Do NOT include raw diff or implementation details that are obvious from the code – focus on intent and impact.

DIFF:
```diff
{final_diff[:3000]}{'...(truncated)' if len(final_diff) > 3000 else ''}
```

TEST & REASONING CONTEXT:

Initially failing tests: {len(fixed_tests)} tests were failing:
{self._format_failing_tests(fixed_tests)}

Fix approach: {reasoning_summary or self._extract_fix_approach(patches_applied)}

Result: All {len(fixed_tests)} tests now pass after these changes.

Execution details:
- Time taken: {execution_time}
- Iterations needed: {len(patches_applied)}
- Files modified: {', '.join(f'`{f}`' for f in changed_files)}

Now generate the PR title and body."""
        
        try:
            response = self.llm.complete(
                system="You are a helpful AI that writes excellent pull request descriptions. Be specific about what was fixed and professional in tone. Think through the changes carefully to provide an accurate and helpful description.",
                user=prompt,
                temperature=1.0,  # GPT-5 only supports temperature=1
                max_tokens=2000  # Will be handled by LLMClient with reasoning_effort=high
            )
            
            # Debug: log the response
            if not response:
                print("[yellow]Warning: Empty response from LLM[/yellow]")
            
            # Parse response based on new format
            lines = response.split('\n') if response else []
            title = ""
            description_lines = []
            
            # Look for "Title: " prefix
            for i, line in enumerate(lines):
                if line.startswith("Title: "):
                    title = line[7:].strip()
                    # Everything after the title line (skipping blank line) is description
                    if i + 2 < len(lines):
                        description_lines = lines[i + 2:]
                    break
                elif i == 0 and not line.startswith("Title:") and len(line) <= 72:
                    # If first line is short and no "Title:" prefix, assume it's the title
                    title = line.strip()
                    if len(lines) > 2:
                        description_lines = lines[2:]
                    break
            
            description = '\n'.join(description_lines).strip()
            
            # If we couldn't parse properly, try alternative parsing
            if not title and response:
                # Look for any line that looks like a title
                for line in lines[:5]:  # Check first 5 lines
                    if line and not line.startswith("#") and len(line) <= 72:
                        title = line.strip()
                        # Get rest as description
                        idx = lines.index(line)
                        if idx + 1 < len(lines):
                            description = '\n'.join(lines[idx + 1:]).strip()
                        break
            
            # Final fallback
            if not title:
                title = f"fix: Fix {len(fixed_tests)} failing test(s)"
            
            if not description and response:
                description = response
            elif not description:
                description = "This PR fixes failing tests in the codebase."
            
            # Clean up the title (remove quotes if present)
            title = title.strip('"\'`')
            
            # Add automation footer if not present
            if "Nova CI-Rescue" not in description and "automatically generated" not in description:
                description += "\n\n---\n*This PR was automatically generated by [Nova CI-Rescue](https://github.com/novasolve/ci-auto-rescue) 🤖*"
            
            return title, description
            
        except Exception as e:
            # Fallback to simple description
            print(f"Error generating PR with AI: {e}")
            title = f"fix: Fix {len(fixed_tests)} failing test(s)"
            description = f"""## Summary

This PR fixes {len(fixed_tests)} failing test(s) that were automatically identified and resolved.

## Changes Made

The following files were modified:
{chr(10).join(f'- `{f}`' for f in changed_files)}

## Test Results

- **Before**: {len(fixed_tests)} tests failing ❌
- **After**: All tests passing ✅

## Execution Details

- Time taken: {execution_time}
- Iterations needed: {len(patches_applied)}

---
*This PR was automatically generated by [Nova CI-Rescue](https://github.com/novasolve/ci-auto-rescue) 🤖*
"""
            return title, description
    
    def create_pr(self, 
                  branch_name: str,
                  title: str, 
                  description: str,
                  base_branch: str = "main",
                  draft: bool = False) -> Tuple[bool, str]:
        """
        Create a PR using GitHub CLI.
        
        Args:
            branch_name: The branch with fixes
            title: PR title
            description: PR description
            base_branch: Target branch (default: main)
            draft: Create as draft PR
            
        Returns:
            Tuple of (success, pr_url_or_error)
        """
        try:
            # First check if gh is installed
            check_gh = subprocess.run(
                ["which", "gh"],
                capture_output=True,
                text=True
            )
            
            if check_gh.returncode != 0:
                return False, "GitHub CLI (gh) not found. Install with: brew install gh"
            
            # Check if we have a git remote
            remote_check = subprocess.run(
                ["git", "remote", "-v"],
                capture_output=True,
                text=True,
                cwd=self.repo_path
            )
            
            if not remote_check.stdout.strip():
                return False, "No git remotes found. This appears to be a local repository without a GitHub remote."
            
            # Check if we're authenticated
            auth_check = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True,
                cwd=self.repo_path
            )
            
            if auth_check.returncode != 0:
                return False, "Not authenticated with GitHub. Run: gh auth login"
            
            # Create the PR
            cmd = [
                "gh", "pr", "create",
                "--base", base_branch,
                "--head", branch_name,
                "--title", title,
                "--body", description
            ]
            
            if draft:
                cmd.append("--draft")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.repo_path
            )
            
            if result.returncode == 0:
                pr_url = result.stdout.strip()
                return True, pr_url
            else:
                error_msg = result.stderr or result.stdout
                return False, f"Failed to create PR: {error_msg}"
                
        except Exception as e:
            return False, f"Error creating PR: {str(e)}"
    
    def check_pr_exists(self, branch_name: str) -> bool:
        """Check if a PR already exists for this branch."""
        try:
            result = subprocess.run(
                ["gh", "pr", "list", "--head", branch_name, "--json", "number"],
                capture_output=True,
                text=True,
                cwd=self.repo_path
            )
            
            if result.returncode == 0 and result.stdout.strip() != "[]":
                                    return True
            return False
        except:
            return False
    
    def _get_combined_diff(self) -> str:
        """Get the combined diff of all changes against the base branch."""
        try:
            # First try to get diff against main/master
            for base in ["main", "master", "HEAD~"]:
                result = subprocess.run(
                    ["git", "diff", f"{base}...HEAD"],
                    capture_output=True,
                    text=True,
                    cwd=self.repo_path
                )
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout
            
            # Fallback to diff of staged/unstaged changes
            result = subprocess.run(
                ["git", "diff", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.repo_path
            )
            return result.stdout or "No diff available"
        except Exception as e:
            print(f"Error getting diff: {e}")
            return "Error retrieving diff"
    
    def _extract_reasoning_summary(self, reasoning_logs: List[Dict]) -> str:
        """Extract key reasoning points from Nova's logs."""
        if not reasoning_logs:
            return ""
        
        summary_points = []
        for log in reasoning_logs:
            if log.get("event") == "planner_complete":
                plan = log.get("data", {}).get("plan", {})
                if plan.get("approach"):
                    summary_points.append(f"Approach: {plan['approach']}")
            elif log.get("event") == "critic_approved":
                reason = log.get("data", {}).get("reason", "")
                if reason:
                    summary_points.append(f"Fix rationale: {reason}")
        
        return " ".join(summary_points[:3])  # Limit to avoid too much text
    
    def _format_failing_tests(self, tests: List[Dict]) -> str:
        """Format failing tests for the prompt."""
        if not tests:
            return "No test details available"
        
        formatted = []
        for test in tests[:10]:  # Limit to 10 for space
            name = test.get('name', 'Unknown')
            file = test.get('file', 'unknown')
            error = test.get('short_traceback', test.get('error', 'No error details'))[:100]
            formatted.append(f"- `{name}` in {file}: {error}")
        
        if len(tests) > 10:
            formatted.append(f"- ... and {len(tests) - 10} more tests")
        
        return "\n".join(formatted)
    
    def _extract_fix_approach(self, patches: List[str]) -> str:
        """Extract fix approach from patches if no reasoning logs available."""
        if not patches:
            return "Automated fixes applied to resolve test failures"
        
        # Try to summarize based on patch content
        changes = []
        for patch in patches[:2]:  # Look at first 2 patches
            lines = patch.split('\n')
            for line in lines:
                if line.startswith('--- a/'):
                    file = line[6:]
                    changes.append(f"Modified {file}")
        
        if changes:
            return "Changes made to: " + ", ".join(changes[:3])
        return "Multiple fixes applied to resolve test failures"
