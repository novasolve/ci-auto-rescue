#!/usr/bin/env python3
"""
Nova PR Safety Check Test Script

This script automates testing of Nova CI-Rescue's safety mechanisms by creating
pull requests that intentionally violate safety limits. It tests:
1. CI configuration changes (restricted files)
2. Large patches (>200 lines)
3. Many files (>10 files)
4. Sensitive file edits (secrets/deploy)

Each PR should trigger the Nova PR Safety Check action and fail with appropriate
error messages.

Prerequisites:
- Git installed and configured
- GitHub CLI (gh) installed and authenticated
- Run from repository root with Nova safety check workflow configured
"""

import os
import subprocess
import sys
import shutil
from pathlib import Path

# Configuration
BASE_BRANCH = "main"  # default branch name
REMOTE_NAME = "origin"  # remote to push to (default 'origin')

# Define test scenarios with branch names, commit messages, and the modifications to apply
scenarios = [
    {
        "branch": "test-ci-config",
        "description": "Modify a CI workflow file to trigger restricted file rule",
        "modify_func": lambda: create_ci_workflow_file()
    },
    {
        "branch": "test-line-limit",
        "description": "Add a large patch exceeding 200 lines to trigger line limit rule",
        "modify_func": lambda: create_large_patch()
    },
    {
        "branch": "test-many-files",
        "description": "Add 11 files in one commit to trigger max files modified rule",
        "modify_func": lambda: create_many_files()
    },
    {
        "branch": "test-sensitive-files",
        "description": "Modify secret and deploy files to trigger restricted files rule",
        "modify_func": lambda: create_sensitive_files()
    },
]

# Helper functions to apply modifications for each scenario
def create_ci_workflow_file():
    """Create or modify a file in .github/workflows/ to simulate a CI config change."""
    ci_dir = ".github/workflows"
    os.makedirs(ci_dir, exist_ok=True)
    file_path = os.path.join(ci_dir, "safety-test.yml")
    content = (
        "name: Dummy CI Workflow\n"
        "on: push\n"
        "jobs:\n"
        "  test:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - run: echo 'CI config test'\n"
    )
    with open(file_path, "w") as f:
        f.write(content)
    print(f"  Created CI workflow file: {file_path}")

def create_large_patch():
    """Create a file with >200 lines of content to exceed the line change limit."""
    file_path = "large_patch.txt"
    # Write 250 lines of dummy content
    with open(file_path, "w") as f:
        for i in range(1, 251):
            f.write(f"Line {i}: This is a test line to exceed the maximum line change limit for Nova safety checks.\n")
    print(f"  Created large file with 250 lines: {file_path}")

def create_many_files():
    """Create 11 new files to exceed the max files modified limit."""
    os.makedirs("manyfiles", exist_ok=True)
    for i in range(1, 12):
        file_path = os.path.join("manyfiles", f"file{i}.txt")
        with open(file_path, "w") as f:
            f.write(f"Dummy content for file {i}\n")
            f.write(f"This file is part of the test to exceed max files modified limit.\n")
    print(f"  Created 11 files in manyfiles/ directory")

def create_sensitive_files():
    """Create files in 'secrets' and 'deploy' directories to simulate sensitive file edits."""
    # Create secrets directory and file
    os.makedirs("secrets", exist_ok=True)
    with open("secrets/api_key.txt", "w") as f:
        f.write("API_KEY=abcdef123456\n")
        f.write("SECRET_TOKEN=xyz789\n")
    print(f"  Created secrets/api_key.txt")
    
    # Create deploy directory and file
    os.makedirs("deploy", exist_ok=True)
    with open("deploy/config.txt", "w") as f:
        f.write("deployment_configuration: true\n")
        f.write("environment: production\n")
        f.write("auto_deploy: false\n")
    print(f"  Created deploy/config.txt")

def cleanup_test_files():
    """Clean up any test files from previous runs."""
    # Remove test directories if they exist
    test_dirs = ["manyfiles", "secrets", "deploy"]
    for dir_name in test_dirs:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"  Cleaned up directory: {dir_name}")
    
    # Remove test files if they exist
    test_files = ["large_patch.txt", ".github/workflows/safety-test.yml"]
    for file_name in test_files:
        if os.path.exists(file_name):
            os.remove(file_name)
            print(f"  Cleaned up file: {file_name}")

def run_command(cmd, capture_output=False, check=True):
    """Run a shell command and handle errors."""
    try:
        if capture_output:
            result = subprocess.run(cmd, capture_output=True, text=True, check=check)
            return result
        else:
            subprocess.run(cmd, check=check)
            return None
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {' '.join(cmd)}", file=sys.stderr)
        if e.output:
            print(f"Output: {e.output}", file=sys.stderr)
        if e.stderr:
            print(f"Error: {e.stderr}", file=sys.stderr)
        if check:
            raise
        return e

def main():
    """Main execution function."""
    print("=" * 60)
    print("Nova PR Safety Check Test Script")
    print("=" * 60)
    
    # Check prerequisites
    print("\n📋 Checking prerequisites...")
    
    # Check if gh CLI is installed
    gh_check = run_command(["gh", "--version"], capture_output=True, check=False)
    if gh_check.returncode != 0:
        print("❌ GitHub CLI (gh) is not installed or not in PATH.", file=sys.stderr)
        print("   Please install it: https://cli.github.com/", file=sys.stderr)
        sys.exit(1)
    print("✅ GitHub CLI is installed")
    
    # Check if we're in a git repository
    git_check = run_command(["git", "status"], capture_output=True, check=False)
    if git_check.returncode != 0:
        print("❌ Not in a git repository.", file=sys.stderr)
        sys.exit(1)
    print("✅ Git repository detected")
    
    # Store current branch to return to it later
    current_branch_result = run_command(["git", "branch", "--show-current"], capture_output=True)
    original_branch = current_branch_result.stdout.strip()
    print(f"📌 Current branch: {original_branch}")
    
    # Start processing each scenario
    created_prs = []
    
    for scenario in scenarios:
        branch = scenario["branch"]
        description = scenario["description"]
        print(f"\n{'='*60}")
        print(f"🧪 Testing scenario: {description}")
        print(f"{'='*60}")
        
        try:
            # Clean up any leftover test files
            print("\n🧹 Cleaning up any previous test files...")
            cleanup_test_files()
            
            # Check out base branch (main) and pull latest changes
            print(f"\n📥 Checking out {BASE_BRANCH} and pulling latest...")
            run_command(["git", "checkout", BASE_BRANCH])
            run_command(["git", "pull", REMOTE_NAME, BASE_BRANCH])
            
            # Delete branch if it exists (from previous runs)
            print(f"\n🔀 Creating branch '{branch}'...")
            run_command(["git", "branch", "-D", branch], check=False, capture_output=True)
            run_command(["git", "checkout", "-b", branch])
            
            # Apply the modifications for this scenario
            print(f"\n📝 Applying modifications...")
            scenario["modify_func"]()
            
            # Stage all changes and commit
            print(f"\n💾 Committing changes...")
            run_command(["git", "add", "."])
            commit_message = f"Test: {description}"
            run_command(["git", "commit", "-m", commit_message])
            print(f"  ✅ Created commit: {commit_message}")
            
            # Push the branch to remote
            print(f"\n📤 Pushing branch to {REMOTE_NAME}...")
            push_cmd = ["git", "push", "--force", "--set-upstream", REMOTE_NAME, branch]
            result = run_command(push_cmd, capture_output=True, check=False)
            if result.returncode != 0:
                print(f"❌ Error pushing branch {branch} to {REMOTE_NAME}", file=sys.stderr)
                if result.stderr:
                    print(f"   {result.stderr}", file=sys.stderr)
                continue
            print(f"  ✅ Pushed branch '{branch}' to remote")
            
            # Create a PR on GitHub using gh CLI
            print(f"\n🔗 Creating pull request...")
            pr_title = f"[TEST] {description}"
            pr_body = (
                f"## 🧪 Automated Safety Check Test\n\n"
                f"**Purpose**: {description}\n\n"
                f"This PR is automatically generated to test Nova CI-Rescue safety limits.\n"
                f"It should trigger a safety check failure.\n\n"
                f"### Expected Result\n"
                f"The Nova PR Safety Check should:\n"
                f"1. Run automatically on this PR\n"
                f"2. Detect the safety violation\n"
                f"3. Post a comment with violation details\n"
                f"4. Mark the check as failed\n\n"
                f"---\n"
                f"*This is a test PR and can be closed after verification.*"
            )
            
            pr_cmd = [
                "gh", "pr", "create",
                "--title", pr_title,
                "--body", pr_body,
                "--base", BASE_BRANCH,
                "--head", branch
            ]
            
            result = run_command(pr_cmd, capture_output=True, check=False)
            if result.returncode != 0:
                print(f"❌ Failed to create PR for branch '{branch}'", file=sys.stderr)
                if result.stderr:
                    print(f"   Error: {result.stderr}", file=sys.stderr)
                continue
            
            # Output the PR URL or number from gh CLI response
            pr_url = result.stdout.strip()
            if pr_url:
                print(f"  ✅ PR created: {pr_url}")
                created_prs.append((branch, pr_url))
            else:
                print("  ✅ PR created (no URL returned)")
                created_prs.append((branch, "Created but no URL"))
                
        except Exception as e:
            print(f"\n❌ Error processing scenario '{branch}': {e}", file=sys.stderr)
            continue
    
    # Return to original branch
    print(f"\n🔙 Returning to original branch: {original_branch}")
    run_command(["git", "checkout", original_branch], check=False)
    
    # Clean up test files from working directory
    print("\n🧹 Final cleanup of test files...")
    cleanup_test_files()
    
    # Print summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    
    if created_prs:
        print(f"\n✅ Successfully created {len(created_prs)} test PRs:")
        for branch, url in created_prs:
            print(f"   • {branch}: {url}")
        
        print("\n📋 Next Steps:")
        print("1. Navigate to each PR URL above")
        print("2. Wait for the Nova PR Safety Check action to run")
        print("3. Verify that each PR shows a failed safety check with appropriate error message")
        print("4. Review the comment posted by the safety check bot")
        print("5. Close the test PRs after verification")
        
        print("\n🎯 Expected Outcomes:")
        print("• test-ci-config: Should fail for modifying .github/workflows/*")
        print("• test-line-limit: Should fail for exceeding 200 lines changed")
        print("• test-many-files: Should fail for modifying >10 files")
        print("• test-sensitive-files: Should fail for modifying secrets/ and deploy/ files")
    else:
        print("\n⚠️ No PRs were created. Please check the errors above.")
    
    print("\n" + "="*60)
    print("✨ Test script completed!")
    print("="*60)

if __name__ == "__main__":
    main()
