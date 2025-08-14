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