#!/usr/bin/env python3
"""
Post Nova CI-Rescue run summary to GitHub check-runs and PR comments.
This script analyzes the Nova run results and posts a comprehensive summary.
"""

import os
import json
import re
import sys
from datetime import datetime
from pathlib import Path
import requests


def main():
    """Main entry point for posting Nova summary."""
    # GitHub context from environment
    repo = os.getenv("GITHUB_REPOSITORY")  # "owner/repo"
    commit_sha = os.getenv("GITHUB_SHA")   # commit SHA
    token = os.getenv("GITHUB_TOKEN")
    pr_number = os.getenv("PR_NUMBER")  # Optional PR number
    run_id = os.getenv("GITHUB_RUN_ID")
    run_url = f"https://github.com/{repo}/actions/runs/{run_id}" if repo and run_id else None

    if not repo or not commit_sha or not token:
        print("Missing GitHub environment context (repo, SHA, or token).")
        print("This script should be run from GitHub Actions.")
        sys.exit(1)

    owner, repository_name = repo.split("/")
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Locate Nova telemetry output
    telemetry_dir = Path(".nova")
    if not telemetry_dir.exists():
        telemetry_dir = Path("telemetry")  # Fallback to old location
    
    if not telemetry_dir.exists():
        print("No Nova telemetry directory found.")
        # Still post a minimal report
        post_minimal_report(headers, owner, repository_name, commit_sha, pr_number)
        sys.exit(0)

    # Find the latest run folder
    run_dirs = [d for d in telemetry_dir.iterdir() if d.is_dir()]
    if not run_dirs:
        print("No Nova run data found.")
        post_minimal_report(headers, owner, repository_name, commit_sha, pr_number)
        sys.exit(0)

    # Sort to get latest run
    run_dirs.sort(key=lambda p: str(p))
    latest_run_dir = run_dirs[-1]
    print(f"Analyzing run: {latest_run_dir}")

    # Initialize metrics
    metrics = {
        "files_changed": set(),
        "total_lines_changed": 0,
        "iterations": 0,
        "outcome_status": "failure",
        "outcome_message": "",
        "runtime_seconds": 0,
        "tests_fixed": 0,
        "initial_failures": 0,
        "final_failures": 0,
        "safety_violation": False,
        "timeout": False,
        "max_iterations_reached": False
    }

    # Parse telemetry trace
    trace_file = latest_run_dir / "trace.jsonl"
    if trace_file.exists():
        parse_trace_file(trace_file, metrics)

    # Analyze patches
    patch_dir = latest_run_dir / "patches"
    if patch_dir.exists():
        analyze_patches(patch_dir, metrics)

    # Check safety limits
    check_safety_limits(metrics)

    # Generate and post reports
    summary_text = generate_summary(metrics)
    detailed_text = generate_detailed_report(metrics, run_url)

    # Create check run
    post_check_run(
        headers, owner, repository_name, commit_sha,
        metrics["outcome_status"], summary_text, detailed_text
    )

    # Post PR comment if PR number provided
    if pr_number:
        post_pr_comment(
            headers, owner, repository_name, pr_number,
            metrics, summary_text, run_url
        )

    print(f"✅ Posted GitHub reports (status: {metrics['outcome_status']})")


def parse_trace_file(trace_file, metrics):
    """Parse Nova trace file for metrics."""
    start_time = None
    end_time = None
    
    with open(trace_file) as f:
        for line in f:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            
            event_type = event.get("event")
            data = event.get("data", {})
            
            if event_type == "start":
                start_time = event.get("ts")
            elif event_type == "end":
                end_time = event.get("ts")
            elif event_type == "test_discovery":
                metrics["initial_failures"] = data.get("total_failures", 0)
            elif event_type == "completion":
                metrics["iterations"] = data.get("iterations", 0)
                status = data.get("status", "")
                
                # Map status to outcome
                if status in ("success", "no_failures"):
                    metrics["outcome_status"] = "success"
                elif status == "timeout":
                    metrics["timeout"] = True
                    metrics["outcome_status"] = "failure"
                elif status == "max_iters":
                    metrics["max_iterations_reached"] = True
                    metrics["outcome_status"] = "failure"
                elif status == "safety_violation":
                    metrics["safety_violation"] = True
                    metrics["outcome_status"] = "failure"
                
                metrics["final_failures"] = data.get("final_failures", 0)
            elif event_type == "test_results":
                # Track test results from iterations
                if "failures_after" in data:
                    metrics["final_failures"] = data["failures_after"]

    # Calculate runtime
    if start_time and end_time:
        try:
            t_start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            t_end = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
            metrics["runtime_seconds"] = int((t_end - t_start).total_seconds())
        except Exception:
            pass

    # Calculate tests fixed
    metrics["tests_fixed"] = max(0, metrics["initial_failures"] - metrics["final_failures"])


def analyze_patches(patch_dir, metrics):
    """Analyze patch files for changed files and lines."""
    for patch_file in patch_dir.glob("*.patch"):
        with open(patch_file) as f:
            for line in f:
                # Track files
                if line.startswith("--- "):
                    path = line.split()[1].strip()
                    if path != "/dev/null" and path.startswith("a/"):
                        metrics["files_changed"].add(path[2:])
                elif line.startswith("+++ "):
                    path = line.split()[1].strip()
                    if path != "/dev/null" and path.startswith("b/"):
                        metrics["files_changed"].add(path[2:])
                # Count changed lines
                elif line.startswith("+") and not line.startswith("+++"):
                    metrics["total_lines_changed"] += 1
                elif line.startswith("-") and not line.startswith("---"):
                    metrics["total_lines_changed"] += 1


def check_safety_limits(metrics):
    """Check if safety limits were violated."""
    MAX_LINES = 200
    MAX_FILES = 10
    DENY_PATTERNS = [
        re.compile(r"^deploy/"),
        re.compile(r"^secrets/"),
        re.compile(r"^\.github/workflows/(?!nova\.yml)"),  # Allow nova.yml
        re.compile(r"^ci/config/")
    ]

    num_files = len(metrics["files_changed"])
    
    # Check for denied files
    denied_files = []
    for file_path in metrics["files_changed"]:
        for pattern in DENY_PATTERNS:
            if pattern.match(file_path):
                denied_files.append(file_path)
                break

    # Set safety violation if limits exceeded
    if num_files > MAX_FILES or metrics["total_lines_changed"] > MAX_LINES or denied_files:
        metrics["safety_violation"] = True
        
        if denied_files:
            metrics["outcome_message"] = f"⚠️ Aborted: Changes to protected paths: {', '.join(denied_files[:3])}"
        elif num_files > MAX_FILES:
            metrics["outcome_message"] = f"⚠️ Aborted: Too many files changed ({num_files} > {MAX_FILES})"
        else:
            metrics["outcome_message"] = f"⚠️ Aborted: Too many lines changed ({metrics['total_lines_changed']} > {MAX_LINES})"
        
        # Override outcome to failure if safety violated
        if metrics["outcome_status"] == "success":
            metrics["outcome_status"] = "failure"


def generate_summary(metrics):
    """Generate a concise summary string."""
    duration = format_duration(metrics["runtime_seconds"])
    num_files = len(metrics["files_changed"])
    status_emoji = "✅" if metrics["outcome_status"] == "success" else "❌"
    
    summary = (
        f"⏱ Duration: {duration}, "
        f"🔁 Iterations: {metrics['iterations']}, "
        f"Files changed: {num_files}, "
        f"Lines changed: {metrics['total_lines_changed']}, "
        f"{status_emoji} Outcome: {metrics['outcome_status'].upper()}"
    )
    
    if metrics["safety_violation"]:
        summary += " (Safety limits exceeded)"
    elif metrics["timeout"]:
        summary += " (Timeout)"
    elif metrics["max_iterations_reached"]:
        summary += " (Max iterations)"
    
    return summary


def generate_detailed_report(metrics, run_url):
    """Generate detailed report text."""
    report = []
    
    # Add outcome message
    if metrics["outcome_message"]:
        report.append(metrics["outcome_message"])
    elif metrics["outcome_status"] == "success":
        report.append("✅ **Success:** All tests passed.")
    else:
        report.append("❌ **Failed:** Some tests are still failing.")
        
        if metrics["safety_violation"]:
            report.append("\n**Safety Limits Violated**")
            report.append("The run was stopped due to safety limits to prevent risky changes.")
        elif metrics["timeout"]:
            report.append("\n**Timeout Reached**")
            report.append("The run exceeded the configured time limit.")
        elif metrics["max_iterations_reached"]:
            report.append("\n**Maximum Iterations Reached**")
            report.append("The tool reached the maximum number of fix attempts.")
    
    # Add test results
    report.append(f"\n**Test Results:**")
    report.append(f"- Initial failures: {metrics['initial_failures']}")
    report.append(f"- Tests fixed: {metrics['tests_fixed']}")
    report.append(f"- Remaining failures: {metrics['final_failures']}")
    
    # Add change summary
    if metrics["files_changed"]:
        report.append(f"\n**Changes Made:**")
        report.append(f"- Files modified: {len(metrics['files_changed'])}")
        report.append(f"- Lines changed: {metrics['total_lines_changed']}")
        
        # List first few files
        file_list = sorted(metrics["files_changed"])[:5]
        if file_list:
            report.append("\nModified files:")
            for f in file_list:
                report.append(f"  - `{f}`")
            if len(metrics["files_changed"]) > 5:
                report.append(f"  - ... and {len(metrics['files_changed']) - 5} more")
    
    # Add artifacts link
    if run_url:
        report.append(f"\n[View artifacts and logs]({run_url})")
    
    return "\n".join(report)


def format_duration(seconds):
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    secs = seconds % 60
    if minutes < 60:
        return f"{minutes}m {secs}s"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m"


def post_check_run(headers, owner, repo, sha, conclusion, summary, details):
    """Post a check run to GitHub."""
    url = f"https://api.github.com/repos/{owner}/{repo}/check-runs"
    
    payload = {
        "name": "CI-Auto-Rescue",
        "head_sha": sha,
        "status": "completed",
        "conclusion": "success" if conclusion == "success" else "failure",
        "output": {
            "title": "CI-Auto-Rescue Results",
            "summary": summary
        }
    }
    
    if details:
        payload["output"]["text"] = details
    
    try:
        resp = requests.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        print(f"✓ Created check run: {resp.json().get('html_url', 'N/A')}")
    except Exception as e:
        print(f"Warning: Failed to create check run: {e}")


def post_pr_comment(headers, owner, repo, pr_number, metrics, summary, run_url):
    """Post or update a PR comment."""
    # First, try to find existing comment
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    
    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        comments = resp.json()
        
        existing_id = None
        for comment in comments:
            if "<!-- ci-auto-rescue-report -->" in comment.get("body", ""):
                existing_id = comment["id"]
                break
        
        # Build comment body
        status_emoji = "✅" if metrics["outcome_status"] == "success" else "❌"
        body = f"""<!-- ci-auto-rescue-report -->
## {status_emoji} CI-Auto-Rescue Summary

{summary}

{metrics.get('outcome_message', '')}"""
        
        if run_url:
            body += f"\n\n[View full run details and artifacts]({run_url})"
        
        if existing_id:
            # Update existing comment
            url = f"https://api.github.com/repos/{owner}/{repo}/issues/comments/{existing_id}"
            resp = requests.patch(url, json={"body": body}, headers=headers)
            resp.raise_for_status()
            print(f"✓ Updated PR comment: {resp.json().get('html_url', 'N/A')}")
        else:
            # Create new comment
            resp = requests.post(url, json={"body": body}, headers=headers)
            resp.raise_for_status()
            print(f"✓ Created PR comment: {resp.json().get('html_url', 'N/A')}")
            
    except Exception as e:
        print(f"Warning: Failed to post PR comment: {e}")


def post_minimal_report(headers, owner, repo, sha, pr_number):
    """Post a minimal report when no telemetry is found."""
    summary = "⚠️ No Nova telemetry data found. The run may have failed to start."
    
    # Post check run
    post_check_run(
        headers, owner, repo, sha, "failure",
        summary, "No telemetry data was generated. Check the workflow logs for errors."
    )
    
    # Post PR comment if applicable
    if pr_number:
        url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
        body = f"""<!-- ci-auto-rescue-report -->
## ⚠️ CI-Auto-Rescue: No Data

No telemetry data was found. The Nova run may have failed to start.
Please check the workflow logs for more information."""
        
        try:
            requests.post(url, json={"body": body}, headers=headers)
        except Exception:
            pass


if __name__ == "__main__":
    main()
