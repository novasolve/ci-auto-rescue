"""
GitHub Integration Module for Nova CI-Rescue

Handles posting check runs and PR comments with run summaries.
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
import argparse
import requests
from dataclasses import dataclass, asdict


@dataclass
class RunMetrics:
    """Metrics from a Nova CI-Rescue run."""
    runtime_seconds: int
    iterations: int
    files_changed: int
    status: str  # 'success' or 'failure'
    tests_fixed: int = 0
    tests_remaining: int = 0
    initial_failures: int = 0
    final_failures: int = 0
    branch_name: Optional[str] = None
    error_message: Optional[str] = None


class GitHubAPI:
    """GitHub API client for posting check runs and comments."""
    
    def __init__(self, token: str):
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
        conclusion: Optional[str],
        title: str,
        summary: str,
        details: Optional[str] = None,
        annotations: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Create or update a check run on GitHub.
        
        Args:
            repo: Repository in format "owner/repo"
            sha: Commit SHA
            name: Name of the check
            status: Status of the check ('queued', 'in_progress', 'completed')
            conclusion: Conclusion if completed ('success', 'failure', 'neutral', etc.)
            title: Title for the check output
            summary: Summary markdown for the check
            details: Optional detailed markdown
            annotations: Optional list of file annotations
        
        Returns:
            Response from GitHub API
        """
        url = f"{self.base_url}/repos/{repo}/check-runs"
        
        payload = {
            "name": name,
            "head_sha": sha,
            "status": status,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "output": {
                "title": title,
                "summary": summary
            }
        }
        
        if status == "completed":
            payload["completed_at"] = datetime.now(timezone.utc).isoformat()
            payload["conclusion"] = conclusion
        
        if details:
            payload["output"]["text"] = details
        
        if annotations:
            payload["output"]["annotations"] = annotations
        
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
            Response from GitHub API
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
            Response from GitHub API
        """
        url = f"{self.base_url}/repos/{repo}/issues/comments/{comment_id}"
        
        payload = {"body": body}
        
        response = requests.patch(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def find_pr_comment(self, repo: str, pr_number: int, identifier: str) -> Optional[int]:
        """
        Find an existing PR comment by identifier string.
        
        Args:
            repo: Repository in format "owner/repo"
            pr_number: Pull request number
            identifier: String to search for in comment
        
        Returns:
            Comment ID if found, None otherwise
        """
        url = f"{self.base_url}/repos/{repo}/issues/{pr_number}/comments"
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        comments = response.json()
        for comment in comments:
            if identifier in comment.get("body", ""):
                return comment["id"]
        
        return None


class ReportGenerator:
    """Generate formatted reports for Nova CI-Rescue runs."""
    
    @staticmethod
    def format_duration(seconds: int) -> str:
        """Format duration in human-readable format."""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}m {secs}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"
    
    @staticmethod
    def generate_check_summary(metrics: RunMetrics) -> str:
        """Generate a summary for the check run."""
        status_emoji = "✅" if metrics.status == "success" else "❌"
        
        summary = f"""## {status_emoji} CI-Auto-Rescue Report

**Status:** {metrics.status.upper()}
**Runtime:** ⏱ {ReportGenerator.format_duration(metrics.runtime_seconds)}
**Iterations:** 🔁 {metrics.iterations}
**Files Changed:** 📝 {metrics.files_changed}

### Test Results
- **Initial Failures:** {metrics.initial_failures}
- **Tests Fixed:** {metrics.tests_fixed}
- **Remaining Failures:** {metrics.final_failures}
"""
        
        if metrics.branch_name:
            summary += f"\n**Fix Branch:** `{metrics.branch_name}`\n"
        
        if metrics.error_message:
            summary += f"\n### Error\n```\n{metrics.error_message}\n```\n"
        
        return summary
    
    @staticmethod
    def generate_pr_comment(metrics: RunMetrics, run_url: Optional[str] = None) -> str:
        """Generate a formatted PR comment."""
        status_emoji = "✅" if metrics.status == "success" else "❌"
        
        comment = f"""<!-- ci-auto-rescue-report -->
## {status_emoji} CI-Auto-Rescue Results

{ReportGenerator._generate_metrics_table(metrics)}

### 📊 Summary
"""
        
        if metrics.status == "success":
            comment += f"""
Successfully fixed **{metrics.tests_fixed}** failing test{'s' if metrics.tests_fixed != 1 else ''}! 🎉

All tests are now passing. The fixes have been applied to branch `{metrics.branch_name or 'current branch'}`.
"""
        else:
            if metrics.tests_fixed > 0:
                comment += f"""
Partially fixed **{metrics.tests_fixed}** out of **{metrics.initial_failures}** failing tests.
**{metrics.final_failures}** test{'s' if metrics.final_failures != 1 else ''} still failing.

The tool made progress but couldn't fix all issues. Manual intervention may be required.
"""
            else:
                comment += f"""
Unable to fix the failing tests. All **{metrics.initial_failures}** tests are still failing.

Manual intervention is required to resolve the test failures.
"""
        
        if run_url:
            comment += f"""
### 🔗 Links
- [View Full Run Details]({run_url})
- [Download Artifacts]({run_url})
"""
        
        comment += """
---
<sub>🤖 Generated by [Nova CI-Rescue](https://github.com/nova-ci/nova-ci-rescue)</sub>
"""
        
        return comment
    
    @staticmethod
    def _generate_metrics_table(metrics: RunMetrics) -> str:
        """Generate a metrics table in markdown."""
        return f"""| Metric | Value |
|--------|-------|
| ⏱ Runtime | {ReportGenerator.format_duration(metrics.runtime_seconds)} |
| 🔁 Iterations | {metrics.iterations} |
| 📝 Files Changed | {metrics.files_changed} |
| 🧪 Tests Fixed | {metrics.tests_fixed}/{metrics.initial_failures} |
| {'✅' if metrics.status == 'success' else '❌'} Outcome | {metrics.status.upper()} |"""
    
    @staticmethod
    def generate_details(nova_log: Optional[str] = None) -> str:
        """Generate detailed output from Nova logs."""
        if not nova_log:
            return ""
        
        # Extract key information from logs
        details = "## Detailed Output\n\n"
        
        # Try to extract plan, patches, and results
        sections = {
            "### Fix Plan": [],
            "### Applied Patches": [],
            "### Test Results": []
        }
        
        current_section = None
        for line in nova_log.split('\n'):
            if "Planning" in line or "plan" in line.lower():
                current_section = "### Fix Plan"
            elif "Applying" in line or "patch" in line.lower():
                current_section = "### Applied Patches"
            elif "Running tests" in line or "pytest" in line:
                current_section = "### Test Results"
            
            if current_section and line.strip():
                sections[current_section].append(line)
        
        for section, lines in sections.items():
            if lines:
                details += f"{section}\n```\n"
                details += '\n'.join(lines[:20])  # Limit to 20 lines per section
                if len(lines) > 20:
                    details += f"\n... ({len(lines) - 20} more lines)"
                details += "\n```\n\n"
        
        return details


def parse_test_results(results_file: Path) -> Dict[str, Any]:
    """Parse pytest JSON report file."""
    if not results_file.exists():
        return {"tests": 0, "passed": 0, "failed": 0, "errors": 0}
    
    try:
        with open(results_file, 'r') as f:
            data = json.load(f)
        
        summary = data.get("summary", {})
        return {
            "tests": summary.get("total", 0),
            "passed": summary.get("passed", 0),
            "failed": summary.get("failed", 0),
            "errors": summary.get("error", 0)
        }
    except Exception as e:
        print(f"Warning: Could not parse test results: {e}")
        return {"tests": 0, "passed": 0, "failed": 0, "errors": 0}


def generate_report_command(args):
    """Generate a report from Nova run results."""
    # Parse test results
    initial_results = parse_test_results(Path(args.initial_results)) if args.initial_results else {}
    final_results = parse_test_results(Path(args.final_results)) if args.final_results else {}
    
    # Calculate metrics
    initial_failures = initial_results.get("failed", 0) + initial_results.get("errors", 0)
    final_failures = final_results.get("failed", 0) + final_results.get("errors", 0)
    tests_fixed = max(0, initial_failures - final_failures)
    
    # Read Nova log if provided
    nova_log = None
    if args.nova_log and Path(args.nova_log).exists():
        with open(args.nova_log, 'r') as f:
            nova_log = f.read()
    
    # Create metrics object
    metrics = RunMetrics(
        runtime_seconds=int(args.runtime),
        iterations=int(args.iterations),
        files_changed=int(args.files_changed),
        status=args.status,
        tests_fixed=tests_fixed,
        tests_remaining=final_failures,
        initial_failures=initial_failures,
        final_failures=final_failures
    )
    
    # Generate report
    generator = ReportGenerator()
    report = {
        "metrics": asdict(metrics),
        "check_summary": generator.generate_check_summary(metrics),
        "pr_comment": generator.generate_pr_comment(metrics),
        "details": generator.generate_details(nova_log) if nova_log else ""
    }
    
    # Save report
    output_path = Path(args.output)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Report generated: {output_path}")


def create_check_command(args):
    """Create a GitHub check run."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN environment variable not set")
        sys.exit(1)
    
    # Load report
    with open(args.report, 'r') as f:
        report = json.load(f)
    
    # Create check run
    api = GitHubAPI(token)
    metrics = RunMetrics(**report["metrics"])
    
    conclusion = "success" if metrics.status == "success" else "failure"
    title = f"CI-Auto-Rescue: {metrics.status.upper()}"
    
    try:
        result = api.create_check_run(
            repo=args.repo,
            sha=args.sha,
            name="CI-Auto-Rescue",
            status="completed",
            conclusion=conclusion,
            title=title,
            summary=report["check_summary"],
            details=report.get("details")
        )
        print(f"Check run created: {result.get('html_url', 'N/A')}")
    except Exception as e:
        print(f"Error creating check run: {e}")
        sys.exit(1)


def post_comment_command(args):
    """Post a comment on a pull request."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN environment variable not set")
        sys.exit(1)
    
    # Load report
    with open(args.report, 'r') as f:
        report = json.load(f)
    
    # Post or update comment
    api = GitHubAPI(token)
    
    try:
        # Check for existing comment
        existing_comment_id = api.find_pr_comment(
            repo=args.repo,
            pr_number=int(args.pr),
            identifier="<!-- ci-auto-rescue-report -->"
        )
        
        if existing_comment_id:
            # Update existing comment
            result = api.update_pr_comment(
                repo=args.repo,
                comment_id=existing_comment_id,
                body=report["pr_comment"]
            )
            print(f"Updated existing comment: {result.get('html_url', 'N/A')}")
        else:
            # Create new comment
            result = api.create_pr_comment(
                repo=args.repo,
                pr_number=int(args.pr),
                body=report["pr_comment"]
            )
            print(f"Created new comment: {result.get('html_url', 'N/A')}")
    except Exception as e:
        print(f"Error posting comment: {e}")
        sys.exit(1)


def main():
    """Main entry point for the GitHub integration module."""
    parser = argparse.ArgumentParser(description="Nova CI-Rescue GitHub Integration")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Generate report command
    report_parser = subparsers.add_parser("generate_report", help="Generate a report from run results")
    report_parser.add_argument("--runtime", required=True, help="Runtime in seconds")
    report_parser.add_argument("--iterations", required=True, help="Number of iterations")
    report_parser.add_argument("--files-changed", required=True, help="Number of files changed")
    report_parser.add_argument("--status", required=True, choices=["success", "failure"], help="Run status")
    report_parser.add_argument("--initial-results", help="Path to initial test results JSON")
    report_parser.add_argument("--final-results", help="Path to final test results JSON")
    report_parser.add_argument("--nova-log", help="Path to Nova output log")
    report_parser.add_argument("--output", default="report.json", help="Output report path")
    
    # Create check command
    check_parser = subparsers.add_parser("create_check", help="Create a GitHub check run")
    check_parser.add_argument("--repo", required=True, help="Repository (owner/repo)")
    check_parser.add_argument("--sha", required=True, help="Commit SHA")
    check_parser.add_argument("--report", required=True, help="Path to report JSON")
    
    # Post comment command
    comment_parser = subparsers.add_parser("post_comment", help="Post a PR comment")
    comment_parser.add_argument("--repo", required=True, help="Repository (owner/repo)")
    comment_parser.add_argument("--pr", required=True, help="Pull request number")
    comment_parser.add_argument("--report", required=True, help="Path to report JSON")
    
    args = parser.parse_args()
    
    if args.command == "generate_report":
        generate_report_command(args)
    elif args.command == "create_check":
        create_check_command(args)
    elif args.command == "post_comment":
        post_comment_command(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
