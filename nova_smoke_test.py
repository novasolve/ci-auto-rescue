#!/usr/bin/env python3
"""
Nova CI-Rescue E2E Smoke Test Script.

Assumptions:
- Running inside a virtual environment with Nova CI-Rescue installed (providing the `nova` CLI).
- An OpenAI API key is set in the environment (OPENAI_API_KEY) for the real LLM agent.
- A demo repository folder named 'demo_test_repo' is present, initialized as a git repo with intentional test failures.

This script will:
1. Verify that the environment is correctly set up (Nova installed, API key present, demo repo exists).
2. Run the tests in the demo repo to confirm the number of failing tests (initial state).
3. Invoke `nova fix` on the repo to attempt to automatically fix the failing tests.
4. Capture Nova's output logs to a file (demo_test_repo/nova_fix_run.log).
5. After Nova completes, run the tests again to check if all failures were resolved.
6. Print a summary of the results (initial vs final failures, success/failure status).
7. Optionally clean up the git branch that Nova created for the fixes (if the run was successful).

Note: The Nova fix run is limited to 3 iterations and 5 minutes for this smoke test.
"""
import subprocess
import sys
import os
import re
import shutil
from pathlib import Path

# Try to load .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # If python-dotenv is not installed, try manual loading
    env_path = Path('.env')
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

# Regex to strip ANSI escape sequences from output (for parsing)
ANSI_ESCAPE_RE = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')

def run_command(cmd, cwd=None):
    """Run a shell command and return (exit_code, stdout, stderr)."""
    result = subprocess.run(cmd, cwd=cwd, shell=isinstance(cmd, str),
                             capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr

def main():
    # 1. Environment checks
    if not shutil.which("nova"):
        print("Error: 'nova' CLI not found. Ensure Nova CI-Rescue is installed and activated.")
        return 1
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY is not set. Please export your OpenAI API key for Nova.")
        return 1
    repo_path = Path("demo_test_repo")
    if not repo_path.is_dir():
        print(f"Error: Demo repository not found at {repo_path.resolve()}.")
        return 1

    print(f"🔎 Using demo repository at: {repo_path}")
    print("📋 Starting Nova CI-Rescue smoke test...")

    # 2. Run initial tests to gather failing test count
    print("🧪 Running initial test suite to confirm failing tests...")
    code, out, err = run_command(["pytest"], cwd=repo_path)
    initial_output = out + err
    # Strip ANSI codes for parsing
    initial_output_clean = ANSI_ESCAPE_RE.sub('', initial_output)
    initial_fail_count = 0
    initial_pass_count = 0
    for line in initial_output_clean.splitlines():
        if "failed" in line or "passed" in line:
            # Look for "X failed, Y passed" or variations
            match = re.search(r'(\d+)\s+failed,?\s+(\d+)\s+passed', line)
            if match:
                initial_fail_count = int(match.group(1))
                initial_pass_count = int(match.group(2))
                break
            if "failed" in line and "passed" not in line:
                m2 = re.search(r'(\d+)\s+failed', line)
                if m2:
                    initial_fail_count = int(m2.group(1))
                    initial_pass_count = 0
                    break
            if "passed" in line and "failed" not in line:
                m3 = re.search(r'(\d+)\s+passed', line)
                if m3:
                    initial_pass_count = int(m3.group(1))
                    initial_fail_count = 0
                    break
    if code == 0:
        initial_fail_count = 0

    # If no failures, abort (nothing to fix)
    total_tests = initial_pass_count + initial_fail_count
    if initial_fail_count == 0:
        print(f"✅ All tests passed ({initial_pass_count} passed, 0 failed) – nothing to fix. Aborting test.")
        return 0  # or return 1 since it's an unexpected scenario for smoke test
    else:
        print(f"   Initial tests: {initial_pass_count} passed, {initial_fail_count} failed (out of {total_tests})")

    # 3. Run Nova fix on the repository
    print("\n🤖 Invoking Nova CI-Rescue (nova fix) on the repository...")
    nova_cmd = ["nova", "fix", ".", "--max-iters", "3", "--timeout", "300", "--verbose"]
    code, out, err = run_command(nova_cmd, cwd=repo_path)
    nova_logs = out + err
    # Save Nova's logs to a file for debugging/inspection
    log_path = repo_path / "nova_fix_run.log"
    try:
        with open(log_path, "w") as f:
            f.write(nova_logs)
    except Exception as e:
        print(f"⚠️  Warning: Could not write logs to {log_path}: {e}")
    else:
        print(f"📄 Nova output logged to: {log_path}")

    # Determine if Nova reported success (exit code 0 typically means all tests fixed)
    success = (code == 0)

    # Extract the name of the fix branch Nova created (if any), from Nova's output
    branch_name = None
    logs_clean = ANSI_ESCAPE_RE.sub('', nova_logs)
    for line in logs_clean.splitlines():
        if "Changes saved to branch" in line:
            # e.g. "Success! Changes saved to branch: nova-fix/20250814_072910"
            branch_name = line.split("branch:")[-1].strip()
            break
        if branch_name is None and "Created branch" in line:
            # e.g. "Created branch: nova-fix/20250814_072910"
            branch_name = line.split("branch:")[-1].strip()
            # don't break, in case "Changes saved..." comes later in output
            continue

    if success:
        print("✅ Nova fix run completed **successfully** – now running tests to verify fixes...")
    else:
        print("❌ Nova fix run **failed** or did not fix all issues (exit code {}).".format(code))
        print("   (Check the log file for detailed Nova output.)")

    # 4. Run tests again after Nova to see if failures remain
    final_fail_count = None
    final_pass_count = None
    if success:
        code2, out2, err2 = run_command(["pytest"], cwd=repo_path)
        after_output = out2 + err2
        after_clean = ANSI_ESCAPE_RE.sub('', after_output)
        final_fail_count = 0
        final_pass_count = 0
        for line in after_clean.splitlines():
            if "failed" in line or "passed" in line:
                match = re.search(r'(\d+)\s+failed,?\s+(\d+)\s+passed', line)
                if match:
                    final_fail_count = int(match.group(1))
                    final_pass_count = int(match.group(2))
                    break
                if "failed" in line and "passed" not in line:
                    m2 = re.search(r'(\d+)\s+failed', line)
                    if m2:
                        final_fail_count = int(m2.group(1))
                        final_pass_count = 0
                        break
                if "passed" in line and "failed" not in line:
                    m3 = re.search(r'(\d+)\s+passed', line)
                    if m3:
                        final_pass_count = int(m3.group(1))
                        final_fail_count = 0
                        break
        if code2 == 0:
            # All tests passed
            final_fail_count = 0
            if final_pass_count is None:
                final_pass_count = initial_pass_count + initial_fail_count
        # Print verification result
        if final_fail_count == 0:
            print(f"🎉 After Nova fix: ALL tests are passing ({final_pass_count} passed, 0 failed).")
        else:
            print(f"⚠️  After Nova fix: {final_fail_count} tests are still failing.")
            success = False  # mark as overall failure if any tests still failing
    else:
        # If Nova failed, the repository was likely reset to original state.
        # We can re-run tests to confirm the failures are as before.
        code2, out2, err2 = run_command(["pytest"], cwd=repo_path)
        final_output = out2 + err2
        final_clean = ANSI_ESCAPE_RE.sub('', final_output)
        final_fail_count = 0
        for line in final_clean.splitlines():
            if "failed" in line:
                m2 = re.search(r'(\d+)\s+failed', line)
                if m2:
                    final_fail_count = int(m2.group(1))
                    break
        print(f"(Post-run, tests still failing: {final_fail_count} failures)")

    # 5. (Optional) Clean up the Nova fix branch
    CLEANUP_BRANCH = False  # set to True to delete the Nova fix branch after the test
    if success and branch_name:
        if CLEANUP_BRANCH:
            print(f"🗑️  Cleaning up Git branch '{branch_name}'...")
            # Switch back to main (or master) before deleting the branch
            checked_out = False
            for base in ("main", "master"):
                co_code, _, _ = run_command(["git", "checkout", base], cwd=repo_path)
                if co_code == 0:
                    checked_out = True
                    break
            if not checked_out:
                print("   ⚠️  Warning: Could not checkout 'main' or 'master'. Branch not deleted.")
            else:
                del_code, _, del_err = run_command(["git", "branch", "-D", branch_name], cwd=repo_path)
                if del_code != 0:
                    print(f"   ⚠️  Warning: Failed to delete branch {branch_name}: {del_err.strip()}")
                else:
                    print(f"   ✅ Deleted branch '{branch_name}'.")
        else:
            print(f"ℹ️  Fixes were applied on branch '{branch_name}'. (Branch not deleted for inspection.)")

    # 6. Print a final summary of the smoke test
    print("\n====== Smoke Test Summary ======")
    print(f"Initial Failures : {initial_fail_count}")
    print(f"Final Failures   : {0 if success and final_fail_count == 0 else final_fail_count}")
    if success:
        print("Result           : ✅ SUCCESS - Nova fixed all failing tests.")
        if branch_name and not CLEANUP_BRANCH:
            print(f"Fix Branch       : {branch_name} (contains the applied fixes)")
    else:
        print("Result           : ❌ FAILURE - Some tests remain failing or an error occurred.")
        print(f"Please check the log file ({log_path.name}) for details on Nova's run.")
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
