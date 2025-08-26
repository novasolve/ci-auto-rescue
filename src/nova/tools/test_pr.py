#!/usr/bin/env python3
"""
Test script for GitHub PR creation flow using the GitHub CLI (`gh`).
This script creates a test branch, commits a dummy change, pushes it,
and attempts to open a pull request using the `gh` CLI.
"""

import subprocess
import os
import sys
import shutil
import tempfile
from pathlib import Path

def run(cmd, cwd=None, env=None, check=True):
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)
    print("stdout:", result.stdout)
    print("stderr:", result.stderr)
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")
    return result

def ensure_gh_cli():
    gh_path = shutil.which("gh")
    if not gh_path:
        print("Error: GitHub CLI (`gh`) is not installed or not in PATH.")
        sys.exit(1)
    return gh_path

def get_repo_root():
    result = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if result.returncode != 0:
        print("Not in a git repository.")
        sys.exit(1)
    return Path(result.stdout.strip())

def get_current_branch():
    result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True)
    if result.returncode != 0:
        print("Failed to get current branch.")
        sys.exit(1)
    return result.stdout.strip()

def main():
    gh_path = ensure_gh_cli()
    repo_root = get_repo_root()
    orig_branch = get_current_branch()
    test_branch = "ci-test-gh-pr-script"
    test_file = repo_root / "ci_test_dummy.txt"

    # Check for GitHub token
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("Warning: GITHUB_TOKEN or GH_TOKEN not set. You may be prompted to authenticate with `gh`.")

    # Clean up any previous test branch
    run(["git", "checkout", orig_branch], cwd=repo_root, check=False)
    run(["git", "branch", "-D", test_branch], cwd=repo_root, check=False)

    # Create a new branch
    run(["git", "checkout", "-b", test_branch], cwd=repo_root)

    # Make a dummy change
    with open(test_file, "w") as f:
        f.write("This is a test file for PR creation flow.\n")

    run(["git", "add", str(test_file)], cwd=repo_root)
    run(["git", "commit", "-m", "test: add dummy file for PR creation flow"], cwd=repo_root)

    # Push the branch
    run(["git", "push", "-u", "origin", test_branch], cwd=repo_root)

    # Try to create a PR using gh
    pr_title = "Test PR: CI PR creation flow"
    pr_body = (
        "This is a test pull request created by the test_pr.py script to verify the GitHub CLI PR creation flow.\n\n"
        "---\n"
        "*This PR was created automatically for testing purposes. Please close and delete the branch after testing.*"
    )

    gh_env = dict(os.environ)
    if token:
        gh_env["GITHUB_TOKEN"] = token

    # Check if PR already exists
    pr_list = subprocess.run(
        [gh_path, "pr", "list", "--head", test_branch, "--json", "number"],
        cwd=repo_root,
        env=gh_env,
        capture_output=True,
        text=True
    )
    if pr_list.returncode == 0 and '"number":' in pr_list.stdout:
        print(f"PR already exists for branch {test_branch}. Skipping creation.")
    else:
        pr_cmd = [
            gh_path, "pr", "create",
            "--title", pr_title,
            "--body", pr_body,
            "--base", orig_branch,
            "--head", test_branch,
        ]
        print("\nAttempting to create PR using GitHub CLI...")
        result = subprocess.run(
            pr_cmd,
            cwd=repo_root,
            env=gh_env,
            capture_output=True,
            text=True
        )
        print("stdout:", result.stdout)
        print("stderr:", result.stderr)
        if result.returncode == 0:
            print("PR created successfully!")
            for line in result.stdout.splitlines():
                if line.startswith("https://github.com/"):
                    print("PR URL:", line)
        else:
            print("Failed to create PR with gh CLI.")
            sys.exit(1)

    print("\nDone. Please check your repository for the test PR.")
    print(f"To clean up: git checkout {orig_branch} && git branch -D {test_branch} && git push origin --delete {test_branch}")
    print(f"Also, close the test PR on GitHub.")

if __name__ == "__main__":
    main()
