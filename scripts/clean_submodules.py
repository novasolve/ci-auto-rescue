#!/usr/bin/env python3
"""
Clean up submodule issues in the repository.
This script helps resolve "modified content, untracked content" warnings.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple


def run_command(cmd: List[str], cwd: Path = None) -> Tuple[bool, str]:
    """Run a command and return success status and output."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)


def find_submodules(repo_path: Path) -> List[Path]:
    """Find all directories that are git submodules or have .git directories."""
    submodules = []

    # Check .gitmodules file
    gitmodules = repo_path / ".gitmodules"
    if gitmodules.exists():
        print(f"Found .gitmodules file")
        # Parse it to find submodule paths
        with open(gitmodules) as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                if line.strip().startswith("path ="):
                    path = line.split("=", 1)[1].strip()
                    submodule_path = repo_path / path
                    if submodule_path.exists():
                        submodules.append(submodule_path)

    # Also find any directory with a .git inside (nested repos)
    for root, dirs, files in os.walk(repo_path):
        if ".git" in dirs and Path(root) != repo_path:
            # Skip if already identified as submodule
            if Path(root) not in submodules:
                submodules.append(Path(root))
        # Don't recurse into .git directories
        if ".git" in dirs:
            dirs.remove(".git")

    return submodules


def check_submodule_status(submodule_path: Path) -> Tuple[bool, bool]:
    """Check if a submodule has modified or untracked content."""
    success, output = run_command(["git", "status", "--porcelain"], cwd=submodule_path)
    if not success:
        return False, False

    has_modified = False
    has_untracked = False

    for line in output.strip().split("\n"):
        if not line:
            continue
        status = line[:2]
        if status[0] == "?" or status[1] == "?":
            has_untracked = True
        elif status.strip():
            has_modified = True

    return has_modified, has_untracked


def clean_submodule(submodule_path: Path, force: bool = False) -> bool:
    """Clean a submodule by discarding changes and removing untracked files."""
    print(f"\nCleaning submodule: {submodule_path}")

    if not force:
        has_modified, has_untracked = check_submodule_status(submodule_path)
        if has_modified or has_untracked:
            print(f"  Modified files: {'Yes' if has_modified else 'No'}")
            print(f"  Untracked files: {'Yes' if has_untracked else 'No'}")
            response = input("  Discard all changes? (y/N): ")
            if response.lower() != 'y':
                print("  Skipped.")
                return False

    # Reset tracked files
    success, output = run_command(["git", "reset", "--hard"], cwd=submodule_path)
    if success:
        print("  ✓ Reset tracked files")
    else:
        print(f"  ✗ Failed to reset: {output}")
        return False

    # Remove untracked files
    success, output = run_command(["git", "clean", "-fd"], cwd=submodule_path)
    if success:
        print("  ✓ Removed untracked files")
    else:
        print(f"  ✗ Failed to clean: {output}")
        return False

    return True


def main():
    """Main function to clean submodules."""
    if len(sys.argv) > 1:
        repo_path = Path(sys.argv[1])
    else:
        repo_path = Path.cwd()

    if not (repo_path / ".git").exists():
        print(f"Error: {repo_path} is not a git repository")
        sys.exit(1)

    print(f"Checking for submodules in: {repo_path}")

    # Find all submodules
    submodules = find_submodules(repo_path)

    if not submodules:
        print("No submodules or nested git repositories found.")
        return

    print(f"\nFound {len(submodules)} submodule(s):")
    for sub in submodules:
        print(f"  - {sub.relative_to(repo_path)}")

    # Check main repo status
    success, output = run_command(["git", "status", "--porcelain"], cwd=repo_path)
    if success and output:
        print("\nMain repository has uncommitted changes:")
        for line in output.strip().split("\n"):
            if line:
                print(f"  {line}")

    # Process each submodule
    cleaned_count = 0
    for submodule in submodules:
        if clean_submodule(submodule):
            cleaned_count += 1

    print(f"\nCleaned {cleaned_count} submodule(s).")

    # Update submodule references in main repo
    if cleaned_count > 0:
        print("\nUpdating submodule references in main repository...")
        for submodule in submodules:
            rel_path = submodule.relative_to(repo_path)
            success, _ = run_command(["git", "add", str(rel_path)], cwd=repo_path)
            if success:
                print(f"  ✓ Updated reference for {rel_path}")

    print("\nDone! Run 'git status' to verify the repository is clean.")


if __name__ == "__main__":
    main()
