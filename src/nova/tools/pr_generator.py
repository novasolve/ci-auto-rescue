"""
PR Generator - Uses GPT-5 to create pull request descriptions and submit them via GitHub CLI.
"""

import subprocess
import os
import requests
import json
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
        prompt = f"""TASK: Write a concise pull request title and a detailed pull request description for the following code changes.

The code changes (diff) were made to fix failing tests. Below you have:
- A GIT DIFF of the changes.
- A summary of the test failures and reasoning behind the fixes.

FORMAT:
Title: <one-line PR title summarizing the change>

<Multiple lines of PR description in Markdown>

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
        Create a PR using GitHub API directly.
        
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
            # Get GitHub token from environment
            token = os.environ.get('GITHUB_TOKEN')
            if not token:
                return False, "GITHUB_TOKEN environment variable not set"
            
            # Get repository info
            repo_info = self._get_repository_info()
            if not repo_info:
                return False, "Could not determine repository owner/name"
            
            owner, repo = repo_info
            
            # Create PR using GitHub API
            url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            data = {
                "title": title,
                "body": description,
                "head": branch_name,
                "base": base_branch,
                "draft": draft
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 201:
                pr_data = response.json()
                pr_url = pr_data.get('html_url', '')
                return True, pr_url
            else:
                error_msg = response.json().get('message', response.text)
                return False, f"Failed to create PR: {error_msg}"
                
        except Exception as e:
            return False, f"Error creating PR: {str(e)}"
    
    def check_pr_exists(self, branch_name: str) -> bool:
        """Check if a PR already exists for this branch using GitHub API."""
        try:
            token = os.environ.get('GITHUB_TOKEN')
            if not token:
                return False
            
            repo_info = self._get_repository_info()
            if not repo_info:
                return False
            
            owner, repo = repo_info
            
            # Check existing PRs
            url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json"
            }
            params = {
                "head": f"{owner}:{branch_name}",
                "state": "open"
            }
            
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                prs = response.json()
                return len(prs) > 0
            return False
        except:
            return False
    
    def _get_repository_info(self) -> Optional[Tuple[str, str]]:
        """Get repository owner and name from git remote or environment."""
        # First try environment variable (for CI)
        repo_env = os.environ.get('GITHUB_REPOSITORY')
        if repo_env and '/' in repo_env:
            parts = repo_env.split('/')
            return parts[0], parts[1]
        
        # Try to get from git remote
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                cwd=self.repo_path
            )
            
            if result.returncode == 0:
                url = result.stdout.strip()
                # Parse GitHub URL
                if "github.com" in url:
                    # Handle both https and ssh URLs
                    if url.startswith("https://"):
                        # https://github.com/owner/repo.git
                        parts = url.replace("https://github.com/", "").replace(".git", "").split("/")
                    elif url.startswith("git@"):
                        # git@github.com:owner/repo.git
                        parts = url.replace("git@github.com:", "").replace(".git", "").split("/")
                    else:
                        return None
                    
                    if len(parts) >= 2:
                        return parts[0], parts[1]
        except:
            pass
        
        return None
    
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











