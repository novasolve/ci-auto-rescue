# Quick Implementation Guide: Connecting GitHub Integration

## What You Need to Add to `src/nova/cli.py`

### 1. Add imports at the top

```python
import os
import httpx  # or use requests since you already have it
from nova.github_integration import GitHubAPI, RunMetrics, ReportGenerator
```

### 2. Add GitHub posting after the main loop (around line 483)

Replace the current section after `telemetry.end_run(success=success)` with:

```python
# Log final completion status
telemetry.log_event("completion", {
    "status": state.final_status,
    "iterations": state.current_iteration,
    "total_patches": len(state.patches_applied),
    "final_failures": state.total_failures
})
telemetry.end_run(success=success)

# Post to GitHub if environment variables are set
token = os.getenv("GITHUB_TOKEN")
repo = os.getenv("GITHUB_REPOSITORY")  # e.g. "owner/repo"
pr_num = os.getenv("PR_NUMBER")

if token and repo:
    try:
        # Calculate metrics
        elapsed = (datetime.now() - state.start_time).total_seconds()
        files_changed = set()
        for patch in state.patches_applied:
            # Parse patch to count unique files (you have this in safety_limits)
            from nova.tools.safety_limits import SafetyLimits
            safety = SafetyLimits()
            analysis = safety.analyze_patch(patch)
            files_changed.update(analysis.files_modified | analysis.files_added)

        # Create metrics object
        metrics = RunMetrics(
            runtime_seconds=int(elapsed),
            iterations=state.current_iteration,
            files_changed=len(files_changed),
            status="success" if success else state.final_status,
            tests_fixed=len(state.failing_tests) - state.total_failures if state.failing_tests else 0,
            tests_remaining=state.total_failures,
            initial_failures=len(state.failing_tests) if state.failing_tests else 0,
            final_failures=state.total_failures,
            branch_name=branch_name,
            error_message=None  # Could extract from state if needed
        )

        # Initialize API client
        api = GitHubAPI(token)
        generator = ReportGenerator()

        # Get commit SHA
        head_sha = git_manager._get_current_head() if git_manager else None

        # If PR number provided, try to get PR head SHA
        if pr_num:
            try:
                import requests
                headers = {"Authorization": f"token {token}"}
                resp = requests.get(
                    f"https://api.github.com/repos/{repo}/pulls/{pr_num}",
                    headers=headers
                )
                if resp.status_code == 200:
                    pr_data = resp.json()
                    head_sha = pr_data.get("head", {}).get("sha", head_sha)
            except:
                pass  # Use current HEAD if can't get PR SHA

        # Create check run
        if head_sha:
            check_summary = generator.generate_check_summary(metrics)
            api.create_check_run(
                repo=repo,
                sha=head_sha,
                name="CI-Auto-Rescue",
                status="completed",
                conclusion="success" if success else "failure",
                title=f"CI-Auto-Rescue: {'SUCCESS' if success else state.final_status.upper()}",
                summary=check_summary
            )
            if verbose:
                console.print("[dim]✅ Posted check run to GitHub[/dim]")

        # Create PR comment if PR number is known
        if pr_num:
            pr_comment = generator.generate_pr_comment(metrics)

            # Check for existing comment to update
            existing_id = api.find_pr_comment(
                repo=repo,
                pr_number=int(pr_num),
                identifier="<!-- ci-auto-rescue-report -->"
            )

            if existing_id:
                api.update_pr_comment(repo=repo, comment_id=existing_id, body=pr_comment)
                if verbose:
                    console.print("[dim]✅ Updated existing PR comment[/dim]")
            else:
                api.create_pr_comment(repo=repo, pr_number=int(pr_num), body=pr_comment)
                if verbose:
                    console.print("[dim]✅ Created new PR comment[/dim]")

    except Exception as e:
        console.print(f"[yellow]⚠️ Warning: GitHub reporting failed: {e}[/yellow]")
        if verbose:
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
```

### 3. Add early exit handling for no failing tests (around line 180)

```python
if not failing_tests:
    console.print("[green]✅ No failing tests found! Repository is already green.[/green]")
    state.final_status = "success"
    telemetry.log_event("completion", {"status": "no_failures"})
    telemetry.end_run(success=True)
    success = True

    # Post to GitHub even when no tests to fix
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPOSITORY")
    pr_num = os.getenv("PR_NUMBER")

    if token and repo:
        try:
            from nova.github_integration import GitHubAPI, RunMetrics, ReportGenerator

            api = GitHubAPI(token)
            metrics = RunMetrics(
                runtime_seconds=0,
                iterations=0,
                files_changed=0,
                status="success",
                tests_fixed=0,
                tests_remaining=0,
                initial_failures=0,
                final_failures=0
            )

            # Get SHA for check run
            head_sha = git_manager._get_current_head() if git_manager else None

            if head_sha:
                api.create_check_run(
                    repo=repo,
                    sha=head_sha,
                    name="CI-Auto-Rescue",
                    status="completed",
                    conclusion="success",
                    title="CI-Auto-Rescue: No failing tests",
                    summary="✅ No failing tests found - repository is already green!"
                )

            if pr_num:
                api.create_pr_comment(
                    repo=repo,
                    pr_number=int(pr_num),
                    body="## ✅ Nova CI-Rescue: No failing tests to fix! 🎉\n\nAll tests are passing."
                )

        except Exception as e:
            if verbose:
                console.print(f"[yellow]Warning: Could not post to GitHub: {e}[/yellow]")

    return
```

### 4. Update the safety limits to allow nova.yml

In `src/nova/tools/safety_limits.py`, modify the `_is_denied_path` method:

```python
def _is_denied_path(self, file_path: str) -> bool:
    """
    Check if a file path matches any denied patterns.

    Args:
        file_path: Path to check.

    Returns:
        True if the path is denied, False otherwise.
    """
    # Special exception for our own workflow
    if file_path == '.github/workflows/nova.yml':
        if self.verbose:
            print(f"[SafetyLimits] Allowing modification to nova.yml (own workflow)")
        return False

    # ... rest of the existing implementation
```

## Environment Variables Required

When running Nova in GitHub Actions or locally with GitHub integration:

```bash
export GITHUB_TOKEN="ghp_..."  # GitHub token with checks:write and pull-requests:write
export GITHUB_REPOSITORY="owner/repo"  # Repository in owner/repo format
export PR_NUMBER="123"  # Optional: PR number for PR comments
```

## Testing the Integration

1. **Local test with mock values:**

```bash
GITHUB_TOKEN="test" GITHUB_REPOSITORY="test/repo" PR_NUMBER="1" nova fix . --verbose
```

2. **In GitHub Actions:** The workflow already sets these environment variables correctly.

## Benefits of This Approach

1. **Uses existing robust modules** - No code duplication
2. **Maintains separation of concerns** - GitHub logic stays in its module
3. **Easy to test** - Can mock environment variables
4. **Backward compatible** - Works without GitHub variables set
5. **Reuses existing error handling** - The GitHub module already handles errors well

## Alternative: Minimal Inline Implementation

If you prefer the simpler inline approach from the provided code, you could add it directly in `cli.py`, but this would:

- Duplicate code
- Be harder to test
- Miss features like comment updates

The recommended approach above leverages your superior existing implementation.
