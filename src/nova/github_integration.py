"""
GitHub integration for Nova CI-Rescue.
Provides check runs and PR comments for CI integration.
"""

import json
import os
from dataclasses import dataclass
from typing import Optional, Dict, Any
import requests
from datetime import datetime


@dataclass
class RunMetrics:
    """Metrics from a Nova CI-Rescue run."""
    runtime_seconds: int
    iterations: int
    files_changed: int
    status: str  # success, failure, timeout, etc.
    tests_fixed: int
    tests_remaining: int
    initial_failures: int
    final_failures: int
    branch_name: Optional[str] = None
    
    # Enhanced error reporting fields (OS-1182)
    success: bool = False
    failure_type: Optional[str] = None    # e.g. "MaxIterationsExceeded", "SafetyGuardTriggered"
    failure_reason: Optional[str] = None  # Human-readable explanation


class GitHubAPI:
    """Wrapper for GitHub API operations."""
    
    def __init__(self, token: str):
        """Initialize with GitHub token."""
        self.token = token
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
        self.base_url = "https://api.github.com"
    
    def create_check_run(
        self, 
        repo: str, 
        sha: str, 
        name: str, 
        status: str,
        conclusion: Optional[str] = None,
        title: Optional[str] = None,
        summary: Optional[str] = None,
        details: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a GitHub check run.
        
        Args:
            repo: Repository in format "owner/repo"
            sha: Git commit SHA
            name: Name of the check run
            status: Status (queued, in_progress, completed)
            conclusion: Conclusion if status is completed (success, failure, neutral, cancelled, skipped, timed_out, action_required)
            title: Title for the check run
            summary: Summary markdown text
            details: Detailed markdown text
        
        Returns:
            API response as dict
        """
        url = f"{self.base_url}/repos/{repo}/check-runs"
        
        payload = {
            "name": name,
            "head_sha": sha,
            "status": status
        }
        
        if conclusion:
            payload["conclusion"] = conclusion
        
        if title or summary or details:
            payload["output"] = {}
            if title:
                payload["output"]["title"] = title
            if summary:
                payload["output"]["summary"] = summary
            if details:
                payload["output"]["text"] = details
        
        if status == "completed" and not payload.get("completed_at"):
            payload["completed_at"] = datetime.utcnow().isoformat() + "Z"
        
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def create_pr_comment(self, repo: str, pr_number: int, body: str) -> Dict[str, Any]:
        """
        Create a comment on a pull request.
        
        Args:
            repo: Repository in format "owner/repo"
            pr_number: Pull request number
            body: Comment body in markdown
        
        Returns:
            API response as dict
        """
        url = f"{self.base_url}/repos/{repo}/issues/{pr_number}/comments"
        payload = {"body": body}
        
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def update_pr_comment(self, repo: str, comment_id: int, body: str) -> Dict[str, Any]:
        """
        Update an existing PR comment.
        
        Args:
            repo: Repository in format "owner/repo"
            comment_id: Comment ID to update
            body: New comment body
        
        Returns:
            API response as dict
        """
        url = f"{self.base_url}/repos/{repo}/issues/comments/{comment_id}"
        payload = {"body": body}
        
        response = requests.patch(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def find_pr_comment(self, repo: str, pr_number: int, marker: str) -> Optional[int]:
        """
        Find a PR comment containing a specific marker.
        
        Args:
            repo: Repository in format "owner/repo"
            pr_number: Pull request number
            marker: Marker string to search for in comment body
        
        Returns:
            Comment ID if found, None otherwise
        """
        url = f"{self.base_url}/repos/{repo}/issues/{pr_number}/comments"
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        comments = response.json()
        for comment in comments:
            if marker in comment.get("body", ""):
                return comment["id"]
        
        return None


class ReportGenerator:
    """Generate formatted reports for GitHub."""
    
    def generate_check_summary(self, metrics: RunMetrics) -> str:
        """
        Generate a markdown summary for check run.
        
        Args:
            metrics: Run metrics
        
        Returns:
            Markdown formatted summary
        """
        if metrics.status == "success":
            status_emoji = "✅"
            status_text = "All tests fixed successfully!"
        else:
            status_emoji = "❌"
            status_text = f"Fix attempt {metrics.status}"
        
        summary = f"""## {status_emoji} Nova CI-Rescue Result

**Status:** {status_text}
**Runtime:** {metrics.runtime_seconds}s
**Iterations:** {metrics.iterations}
**Files Changed:** {metrics.files_changed}

### Test Results
- **Initial failures:** {metrics.initial_failures}
- **Tests fixed:** {metrics.tests_fixed}
- **Tests remaining:** {metrics.tests_remaining}
"""
        
        if metrics.branch_name:
            summary += f"\n**Branch:** `{metrics.branch_name}`"
        
        # Add performance indicator
        if metrics.runtime_seconds > 0:
            fix_rate = metrics.tests_fixed / max(metrics.runtime_seconds, 1)
            if fix_rate > 0.1:  # More than 0.1 fixes per second
                summary += f"\n\n⚡ High performance: {fix_rate:.2f} fixes/second"
            elif fix_rate > 0.01:
                summary += f"\n\n📊 Performance: {fix_rate:.3f} fixes/second"
        
        return summary
    
    def generate_pr_comment(self, metrics: RunMetrics) -> str:
        """
        Generate a detailed PR comment.
        
        Args:
            metrics: Run metrics
        
        Returns:
            Markdown formatted PR comment
        """
        # Hidden marker for comment identification
        marker = "<!-- ci-auto-rescue-report -->"
        
        if metrics.status == "success":
            header = "## ✅ CI Auto-Rescue: All Tests Fixed!"
            status_badge = "![success](https://img.shields.io/badge/status-success-green)"
        elif metrics.status == "timeout":
            header = "## ⏰ CI Auto-Rescue: Timeout Reached"
            status_badge = "![timeout](https://img.shields.io/badge/status-timeout-yellow)"
        elif metrics.status == "failure":
            header = "## ❌ CI Auto-Rescue: Fix Incomplete"
            status_badge = "![failure](https://img.shields.io/badge/status-failure-red)"
        else:
            header = f"## 🔧 CI Auto-Rescue: {metrics.status.title()}"
            status_badge = "![status](https://img.shields.io/badge/status-unknown-gray)"
        
        # Calculate success percentage
        success_pct = 0
        if metrics.initial_failures > 0:
            success_pct = (metrics.tests_fixed / metrics.initial_failures) * 100
        
        # Format runtime
        minutes, seconds = divmod(metrics.runtime_seconds, 60)
        runtime_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
        
        comment = f"""{marker}
{header}

{status_badge}

### 📊 Summary

| Metric | Value |
|--------|-------|
| **Runtime** | {runtime_str} |
| **Iterations Used** | {metrics.iterations} |
| **Files Modified** | {metrics.files_changed} |
| **Tests Fixed** | {metrics.tests_fixed}/{metrics.initial_failures} ({success_pct:.0f}%) |
| **Tests Remaining** | {metrics.tests_remaining} |
"""
        
        # Add progress bar
        if metrics.initial_failures > 0:
            filled = int((metrics.tests_fixed / metrics.initial_failures) * 10)
            empty = 10 - filled
            progress_bar = "█" * filled + "░" * empty
            comment += f"\n### Progress\n`[{progress_bar}]` {success_pct:.0f}%\n"
        
        # Add next steps based on status
        if metrics.status == "success":
            comment += """
### ✨ Next Steps
All tests are now passing! The changes are ready for review.
"""
        elif metrics.tests_remaining > 0:
            comment += f"""
### ⚠️ Manual Review Required
{metrics.tests_remaining} test(s) still failing and may require manual intervention.

Consider:
- Reviewing the remaining test failures
- Running Nova CI-Rescue again with more iterations
- Manually fixing complex test issues
"""
        
        # Add footer
        comment += """
---
<sub>Generated by [Nova CI-Rescue](https://github.com/yourusername/nova-ci-rescue) 🚀</sub>
"""
        
        return comment
    
    def generate_json_report(self, metrics: RunMetrics) -> str:
        """
        Generate a JSON report of the metrics.
        
        Args:
            metrics: Run metrics
        
        Returns:
            JSON string
        """
        report = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "status": metrics.status,
            "metrics": {
                "runtime_seconds": metrics.runtime_seconds,
                "iterations": metrics.iterations,
                "files_changed": metrics.files_changed,
                "tests_fixed": metrics.tests_fixed,
                "tests_remaining": metrics.tests_remaining,
                "initial_failures": metrics.initial_failures,
                "final_failures": metrics.final_failures,
                "success_rate": (metrics.tests_fixed / max(metrics.initial_failures, 1)) * 100
            }
        }
        
        if metrics.branch_name:
            report["branch"] = metrics.branch_name
        
        return json.dumps(report, indent=2)


class OutcomeReporter:
    """
    Generates transparent error reports for CLI, API, and PR outputs based on RunMetrics.
    Implements OS-1182 for unified error reporting across all interfaces.
    """
    
    def __init__(self, metrics: RunMetrics):
        self.metrics = metrics

    def generate_cli_summary(self) -> str:
        """Produce a console-friendly summary of results, including error info if any."""
        m = self.metrics
        lines = []
        
        # Basic stats line
        total = m.initial_failures
        fixed = m.tests_fixed
        
        if m.success:
            lines.append(f"✅ All tests passed! Fixed {fixed} of {total} failing tests in {m.iterations} iterations.")
        else:
            lines.append(f"❌ Failed to fix all tests. Fixed {fixed} of {total}, still failing: {total - fixed}.")
            if m.failure_reason:
                lines.append(f"Reason: {m.failure_reason}")
        
        # Include runtime and file changes
        lines.append(f"Iterations: {m.iterations}, Files changed: {m.files_changed}, Time: {m.runtime_seconds}s")
        
        # Add suggestions based on failure type
        if m.failure_type == "MaxIterationsExceeded":
            lines.append("\nConsider: Running Nova again with --max-iters flag to allow more attempts.")
        elif m.failure_type == "SafetyGuardTriggered":
            lines.append("\nConsider: Reviewing safety policies or manually fixing the restricted changes.")
        elif m.failure_type == "TestExecutionError":
            lines.append("\nConsider: Checking test infrastructure and environment setup.")
            
        return "\n".join(lines)
    
    def generate_pr_comment(self) -> str:
        """Generate a PR comment with transparent error reporting."""
        m = self.metrics
        
        # Header
        if m.success:
            comment = f"## ✅ Nova CI-Rescue - All Tests Fixed!\n\n"
        else:
            comment = f"## ⚠️ Nova CI-Rescue - Partial Fix Applied\n\n"
        
        # Summary stats
        comment += "### Summary\n"
        comment += f"- **Tests Fixed**: {m.tests_fixed}/{m.initial_failures}\n"
        comment += f"- **Files Changed**: {m.files_changed}\n"
        comment += f"- **Iterations**: {m.iterations}\n"
        comment += f"- **Runtime**: {m.runtime_seconds}s\n"
        
        if m.branch_name:
            comment += f"- **Branch**: `{m.branch_name}`\n"
        
        # Error details if failed
        if not m.success and m.failure_reason:
            comment += "\n### Why did it stop?\n"
            comment += f"{m.failure_reason}\n"
            
            # Specific suggestions
            if m.failure_type == "MaxIterationsExceeded":
                comment += "\n**Suggestion**: The agent needs more iterations. Consider:\n"
                comment += "- Running Nova locally with `--max-iters 10` or higher\n"
                comment += "- Simplifying the failing tests\n"
            elif m.failure_type == "SafetyGuardTriggered":
                comment += "\n**Suggestion**: Safety policies prevented some changes. Consider:\n"
                comment += "- Reviewing the safety configuration\n"
                comment += "- Manually applying restricted changes\n"
            elif m.failure_type == "TestExecutionError":
                comment += "\n**Suggestion**: Test execution failed. Check:\n"
                comment += "- Test environment and dependencies\n"
                comment += "- Docker availability (if using sandboxing)\n"
        
        # Footer
        comment += "\n---\n"
        comment += "<sub>Generated by [Nova CI-Rescue](https://github.com/novasolve/ci-auto-rescue) 🚀</sub>"
        
        return comment
    
    def generate_api_response(self) -> Dict[str, Any]:
        """Generate API response with transparent error details."""
        m = self.metrics
        
        response = {
            "success": m.success,
            "tests_fixed": m.tests_fixed,
            "tests_remaining": m.tests_remaining,
            "iterations": m.iterations,
            "runtime_seconds": m.runtime_seconds,
            "files_changed": m.files_changed
        }
        
        if m.branch_name:
            response["branch"] = m.branch_name
            
        if not m.success:
            response["error"] = {
                "type": m.failure_type,
                "reason": m.failure_reason
            }
            
        return response