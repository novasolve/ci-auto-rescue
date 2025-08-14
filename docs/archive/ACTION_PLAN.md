# Action Plan: Making Nova CI-Rescue GitHub Integration Work

## ✅ Quick Checklist (5-10 minutes total)

### 1. **Update `src/nova/cli.py`** (3 minutes)

- [ ] Add import at top: `import os`
- [ ] Add the GitHub posting code after line 483 (see `github_integration_snippet.py`)
- [ ] Also add similar code for the "no failing tests" case around line 180

### 2. **Update `src/nova/tools/safety_limits.py`** (2 minutes)

- [ ] Add the nova.yml exception to `_is_denied_path()` method (see `safety_limits_patch.py`)

### 3. **Update GitHub Actions Workflow** (1 minute)

Already good! Just ensure these environment variables are passed:

```yaml
env:
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  GITHUB_REPOSITORY: ${{ github.repository }}
  PR_NUMBER: ${{ github.event.inputs.pr_number }} # Add this if missing
```

## 🔧 Detailed Steps

### Step 1: Update CLI Integration

**File:** `src/nova/cli.py`

**Location 1:** After `telemetry.end_run(success=success)` (line ~483)

```python
# Copy the code from github_integration_snippet.py here
```

**Location 2:** In the "no failing tests" block (line ~180)

```python
if not failing_tests:
    console.print("[green]✅ No failing tests found! Repository is already green.[/green]")
    state.final_status = "success"
    telemetry.log_event("completion", {"status": "no_failures"})
    telemetry.end_run(success=True)
    success = True

    # ADD THIS SECTION:
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPOSITORY")
    pr_num = os.getenv("PR_NUMBER")

    if token and repo:
        try:
            from nova.github_integration import GitHubAPI, RunMetrics, ReportGenerator
            api = GitHubAPI(token)

            # Simple metrics for no failures
            metrics = RunMetrics(
                runtime_seconds=1,
                iterations=0,
                files_changed=0,
                status="success",
                tests_fixed=0,
                tests_remaining=0,
                initial_failures=0,
                final_failures=0
            )

            # Post success status
            if git_manager:
                head_sha = git_manager._get_current_head()
                api.create_check_run(
                    repo=repo,
                    sha=head_sha,
                    name="CI-Auto-Rescue",
                    status="completed",
                    conclusion="success",
                    title="CI-Auto-Rescue: No failing tests",
                    summary="✅ All tests are passing - nothing to fix!"
                )

            if pr_num:
                api.create_pr_comment(
                    repo=repo,
                    pr_number=int(pr_num),
                    body="## ✅ Nova CI-Rescue\n\nNo failing tests found - all tests are already passing! 🎉"
                )
        except Exception as e:
            if verbose:
                console.print(f"[yellow]GitHub posting failed: {e}[/yellow]")

    return  # Keep existing return
```

### Step 2: Update Safety Limits

**File:** `src/nova/tools/safety_limits.py`

Replace the `_is_denied_path` method with the code from `safety_limits_patch.py`

### Step 3: Test Locally

```bash
# Test with mock environment variables
export GITHUB_TOKEN="test-token"
export GITHUB_REPOSITORY="owner/repo"
export PR_NUMBER="1"

# Run nova
nova fix . --verbose
```

## 🎯 What This Achieves

1. **GitHub Check Runs** ✅

   - Posts pass/fail status to commit SHA
   - Shows in PR checks tab
   - Includes detailed metrics

2. **PR Comments** ✅

   - Automatically comments on PRs
   - Updates existing comments (no spam)
   - Shows test fixes and stats

3. **Safety Exception** ✅
   - Allows Nova to modify its own workflow
   - Still blocks other CI/CD files

## 🚀 Optional Enhancements

### Add PR Number Detection (if not provided)

```python
# Try to detect PR from git branch or CI environment
if not pr_num:
    # GitHub Actions provides this
    pr_num = os.getenv("GITHUB_EVENT_NUMBER")
    # Or try to parse from branch name (e.g., "pr-123")
    if not pr_num and branch_name and "pr-" in branch_name:
        pr_num = branch_name.split("pr-")[-1].split("-")[0]
```

### Add Retry Logic

```python
# Wrap GitHub API calls with retry
import time
for attempt in range(3):
    try:
        # API call here
        break
    except Exception as e:
        if attempt < 2:
            time.sleep(2 ** attempt)  # Exponential backoff
        else:
            raise
```

## 📊 Expected Results

After these changes:

1. **In GitHub Actions:**

   - ✅ Check run appears on commit
   - ✅ PR comment with results
   - ✅ Status badge shows pass/fail

2. **Locally:**

   - ✅ Works without GitHub env vars (graceful skip)
   - ✅ With env vars, posts to GitHub

3. **Safety:**
   - ✅ Can modify nova.yml
   - ✅ Still blocks other CI files
   - ✅ Comprehensive path protection

## 🐛 Troubleshooting

| Issue                     | Solution                                                                    |
| ------------------------- | --------------------------------------------------------------------------- |
| "GitHub reporting failed" | Check GITHUB_TOKEN has `checks:write` and `pull-requests:write` permissions |
| No PR comment appears     | Ensure PR_NUMBER is set correctly                                           |
| Check run not showing     | Verify commit SHA is correct and token has permissions                      |
| Safety blocks nova.yml    | Ensure the exception code is added correctly                                |

## ✨ That's It!

With these 2-3 small changes, your superior architecture will be fully connected and working. The beauty is that you're just connecting existing, well-tested modules - not rewriting anything.

Your implementation will be:

- **More robust** than the example
- **More maintainable** with modular design
- **More feature-rich** with comment updates and detailed reports
- **Production-ready** with proper error handling
