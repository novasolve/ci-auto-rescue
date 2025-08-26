"""
Git operations for Nova CI-Rescue.
Handles branch management and repository state, and creates GitHub PRs.

Improvements:
- Prefer GitHub CLI (gh) for PR creation if available & authenticated
- Fallback to GitHub REST API (token from env or gh)
- Clear errors; no bare `except:`
"""

from __future__ import annotations

import os
import re
import json
import shutil
import signal
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List

from rich.console import Console

console = Console()


class GitBranchManager:
    """Manages Git branch creation and cleanup for Nova fix operations."""

    def __init__(self, repo_path: Path, verbose: bool = False):
        self.repo_path = repo_path
        self.verbose = verbose
        self.original_head: Optional[str] = None
        self.original_branch: Optional[str] = None  # Store original branch name
        self.branch_name: Optional[str] = None
        self._original_sigint_handler = None
        self._handling_interrupt = False

    # ---------------------------
    # Low-level command helpers
    # ---------------------------
    def _run_git_command(self, *args: str) -> Tuple[bool, str]:
        """Run a git command and return (success, output)."""
        try:
            result = subprocess.run(
                ["git"] + list(args),
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False,
            )
            out = (result.stdout or result.stderr or "").strip()
            return result.returncode == 0, out
        except Exception as e:
            return False, f"git {' '.join(args)} failed: {e}"

    def _run_cli(self, args: List[str]) -> Tuple[bool, str]:
        """Run an arbitrary CLI command and return (success, output)."""
        try:
            result = subprocess.run(
                args,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False,
            )
            out = (result.stdout or result.stderr or "").strip()
            return result.returncode == 0, out
        except FileNotFoundError as e:
            return False, f"{args[0]} not found: {e}"
        except Exception as e:
            return False, f"{args[0]} failed: {e}"

    # ---------------------------
    # Current repo state helpers
    # ---------------------------
    def _get_current_head(self) -> Optional[str]:
        success, output = self._run_git_command("rev-parse", "HEAD")
        return output if success else None

    def _get_current_branch(self) -> Optional[str]:
        success, output = self._run_git_command("rev-parse", "--abbrev-ref", "HEAD")
        return output if success else None

    def _get_remote_url(self, remote: str = "origin") -> Optional[str]:
        success, output = self._run_git_command("config", "--get", f"remote.{remote}.url")
        return output if success and output else None

    def _parse_repo_slug(self, url: str) -> Optional[Tuple[str, str]]:
        """
        Parse a remote URL into (owner, repo).
        Supports SSH and HTTPS forms.
        """
        if not url:
            return None
        m = re.match(r"git@[^:]+:([^/]+)/(.+?)(?:\.git)?$", url)
        if not m:
            m = re.match(r"https?://[^/]+/([^/]+)/(.+?)(?:\.git)?$", url)
        if not m:
            return None
        owner, repo = m.group(1), m.group(2)
        return owner, repo

    def _check_clean_working_tree(self) -> bool:
        """Check if the working tree is clean (ignoring submodules and untracked files)."""
        success, output = self._run_git_command(
            "status", "--porcelain", "--ignore-submodules=dirty", "--untracked-files=no"
        )
        if not success:
            return False
        return output.strip() == ""

    def get_default_branch(self) -> str:
        """Get the default branch name (main, master, etc.)."""
        success, output = self._run_git_command("symbolic-ref", "refs/remotes/origin/HEAD")
        if success and output:
            branch = output.replace("refs/remotes/origin/", "").strip()
            if branch:
                return branch
        for branch in ["main", "master"]:
            success, _ = self._run_git_command("rev-parse", "--verify", branch)
            if success:
                return branch
        return "main"

    # ---------------------------
    # gh / token helpers
    # ---------------------------
    @staticmethod
    def _gh_available() -> bool:
        return shutil.which("gh") is not None

    def _gh_authenticated(self) -> bool:
        """Return True if `gh` is installed and logged in for github.com."""
        if not self._gh_available():
            return False
        ok, _ = self._run_cli(["gh", "auth", "status", "--hostname", "github.com"])
        return ok

    def _gh_token_from_cli(self) -> Optional[str]:
        """Return a token from `gh auth token` if available."""
        if not self._gh_available():
            return None
        ok, out = self._run_cli(["gh", "auth", "token"])
        if ok and out:
            return out.splitlines()[0].strip()
        return None

    def ensure_github_token_env(self) -> Optional[str]:
        """
        Ensure a token is available in env (GITHUB_TOKEN).
        Try existing env, then gh CLI, return token or None.
        """
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if token:
            return token
        token = self._gh_token_from_cli()
        if token:
            os.environ["GITHUB_TOKEN"] = token
            return token
        return None

    # ---------------------------
    # Branch lifecycle
    # ---------------------------
    def create_fix_branch(self) -> str:
        """Create a new nova-auto-fix/<timestamp> branch and switch to it."""
        self.original_head = self._get_current_head()
        if not self.original_head:
            raise RuntimeError("Failed to get current HEAD commit")

        self.original_branch = self._get_current_branch()
        if self.original_branch == "HEAD":
            success, output = self._run_git_command("branch", "--contains", self.original_head)
            if success and output:
                branches = output.strip().split("\n")
                for branch in branches:
                    branch = branch.strip().lstrip("* ")
                    if not branch.startswith("nova-auto-fix/"):
                        self.original_branch = branch
                        break
            if self.original_branch == "HEAD":
                success, _ = self._run_git_command("rev-parse", "--verify", "main")
                if success:
                    self.original_branch = "main"
                else:
                    success, _ = self._run_git_command("rev-parse", "--verify", "master")
                    if success:
                        self.original_branch = "master"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.branch_name = f"nova-auto-fix/{timestamp}"

        success, output = self._run_git_command("checkout", "-b", self.branch_name)
        if not success:
            raise RuntimeError(f"Failed to create branch {self.branch_name}: {output}")

        if self.verbose:
            console.print(f"[dim]Created branch: {self.branch_name}[/dim]")

        nested_repos = self._detect_nested_git_repos()
        if nested_repos:
            console.print("[yellow]⚠️  Warning: Detected nested git repositories:[/yellow]")
            for repo_path in nested_repos:
                console.print(f"[yellow]   - {repo_path}[/yellow]")
            console.print("[yellow]These will be ignored as only specific changed files will be staged.[/yellow]")

        return self.branch_name

    def push_branch(self, remote: str = "origin") -> Tuple[bool, str]:
        """Push the current fix branch to the given remote."""
        if not self.branch_name:
            return False, "No branch_name set on manager"
        return self._run_git_command("push", "-u", remote, self.branch_name)

    def commit_patch(
        self,
        step_number: int,
        changed_files: Optional[List[Path]] = None,
        message: Optional[str] = None,
    ) -> bool:
        """Commit current changes with a step message."""
        if message is None:
            message = f"nova: step {step_number}"

        if changed_files is not None:
            BATCH_SIZE = 100
            for i in range(0, len(changed_files), BATCH_SIZE):
                batch = changed_files[i : i + BATCH_SIZE]
                file_args = ["add", "--"] + [str(f) for f in batch]
                success, output = self._run_git_command(*file_args)
                if not success:
                    if self.verbose:
                        console.print(f"[red]Failed to stage changes: {output}[/red]")
                    return False
        else:
            success, output = self._run_git_command("add", "-A")
            if not success:
                if self.verbose:
                    console.print(f"[red]Failed to stage changes: {output}[/red]")
                return False

        success, _ = self._run_git_command("diff", "--cached", "--quiet")
        if success:
            if self.verbose:
                console.print("[dim]No changes to commit[/dim]")
            return True

        success, output = self._run_git_command("commit", "-m", message)
        if not success:
            if self.verbose:
                console.print(f"[red]Failed to commit: {output}[/red]")
            return False

        if self.verbose:
            console.print(f"[green]✓ Committed: {message}[/green]")
        return True

    def _detect_nested_git_repos(self) -> List[Path]:
        nested_repos: List[Path] = []
        for git_dir in self.repo_path.glob("**/.git"):
            if git_dir.parent == self.repo_path:
                continue
            nested_repos.append(git_dir.parent)
        return nested_repos

    # ---------------------------
    # PR creation
    # ---------------------------
    def create_or_update_pr(
        self,
        title: str,
        body: str = "",
        base: Optional[str] = None,
        draft: bool = False,
        labels: Optional[List[str]] = None,
        reviewers: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        prefer_gh_cli: bool = True,
    ) -> Tuple[bool, str]:
        """
        Create (or reuse) a PR for the current fix branch.

        Returns:
            (True, url) on success; (False, error_message) on failure.
        """
        if not self.branch_name:
            return False, "No branch_name set on manager"

        base = base or self.get_default_branch()

        # 1) Ensure branch is pushed
        ok, out = self.push_branch()
        if not ok:
            return False, f"Failed to push branch to origin: {out}"

        # 2) Resolve repo slug
        remote_url = self._get_remote_url() or ""
        slug = self._parse_repo_slug(remote_url)
        repo_slug = f"{slug[0]}/{slug[1]}" if slug else None
        branch = self.branch_name

        # 3) Prefer gh CLI if available and authenticated
        if prefer_gh_cli and self._gh_authenticated():
            # Check if an open PR already exists for this head/base
            cmd = ["gh", "pr", "list", "--state", "open", "--head", branch, "--base", base, "--json", "url", "--jq", ".[0].url"]
            if repo_slug:
                cmd[2:2] = ["-R", repo_slug]  # insert after "gh", "pr"
            ok, url = self._run_cli(cmd)
            if ok and url:
                return True, url

            # Create PR
            cmd = ["gh", "pr", "create", "--title", title, "--body", body, "--base", base, "--head", branch]
            if repo_slug:
                cmd[2:2] = ["-R", repo_slug]
            if draft:
                cmd.append("--draft")
            for l in labels or []:
                cmd += ["--label", l]
            for r in reviewers or []:
                cmd += ["--reviewer", r]
            for a in assignees or []:
                cmd += ["--assignee", a]

            ok, out = self._run_cli(cmd)
            if not ok:
                return False, f"`gh pr create` failed: {out}"

            # Get the URL of the created PR
            cmd = ["gh", "pr", "view", "--json", "url", "--jq", ".url"]
            if repo_slug:
                cmd[2:2] = ["-R", repo_slug]
            ok, url = self._run_cli(cmd)
            if ok and url:
                return True, url
            return False, f"PR created but failed to fetch URL: {out}"

        # 4) Fallback to REST API with token
        token = self.ensure_github_token_env()
        if not token:
            return False, (
                "No GitHub token found and GitHub CLI isn't authenticated. "
                "Run `gh auth login` or set GITHUB_TOKEN / GH_TOKEN."
            )
        if not repo_slug:
            return False, f"Unable to parse repository slug from remote URL: {remote_url}"

        owner, repo = slug
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "nova-ci-rescue",
        }

        try:
            # Does an open PR already exist for this head/base?
            q_head = f"{owner}:{branch}"
            url = (
                "https://api.github.com/repos/"
                f"{owner}/{repo}/pulls?state=open&head={urllib.parse.quote(q_head)}&base={urllib.parse.quote(base)}"
            )
            req = urllib.request.Request(url, headers=headers, method="GET")
            with urllib.request.urlopen(req) as resp:
                existing = json.loads(resp.read().decode("utf-8"))
            if isinstance(existing, list) and existing:
                pr_url = existing[0].get("html_url") or existing[0].get("url")
                return True, pr_url or "Open PR already exists"

            # Create PR
            create_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
            payload = {
                "title": title,
                "body": body,
                "head": branch,  # same-repo branch
                "base": base,
                "draft": draft,
            }
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(create_url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req) as resp:
                pr = json.loads(resp.read().decode("utf-8"))
            pr_url = pr.get("html_url") or pr.get("url") or ""
            # Optionally add labels/reviewers/assignees (best done via gh; skipping for REST fallback simplicity)
            return True, pr_url or "PR created (no URL returned)"

        except urllib.error.HTTPError as e:
            try:
                body = e.read().decode("utf-8")
            except Exception:
                body = ""
            return False, f"GitHub API error {e.code} {e.reason}: {body or 'no body'}"
        except Exception as e:
            return False, f"PR creation failed: {e}"

    # ---------------------------
    # Cleanup & signals
    # ---------------------------
    def cleanup(self, success: bool = False):
        """Clean up the repository state."""
        if not self.original_head:
            return

        if success:
            console.print(f"\n[green]✅ Success! Changes saved to branch: {self.branch_name}[/green]")
        else:
            console.print("\n[yellow]⚠️  Cleaning up... resetting to original state[/yellow]")
            current_branch = self._get_current_branch()
            if current_branch and current_branch.startswith("nova-auto-fix/"):
                if self.original_branch and self.original_branch != "HEAD":
                    ok, output = self._run_git_command("checkout", "-f", self.original_branch)
                    if not ok:
                        console.print(f"[yellow]Warning: Failed to checkout {self.original_branch}, trying HEAD[/yellow]")
                        ok, _ = self._run_git_command("checkout", "-f", self.original_head)
                        if not ok:
                            console.print("[red]Warning: Failed to checkout original state[/red]")
                else:
                    self._run_git_command("checkout", "-f", self.original_head)

            ok, output = self._run_git_command("reset", "--hard", self.original_head)
            if ok:
                console.print("[dim]Repository reset to original state[/dim]")
                if self.branch_name:
                    ok, _ = self._run_git_command("branch", "-D", self.branch_name)
                    if ok and self.verbose:
                        console.print(f"[dim]Deleted branch: {self.branch_name}[/dim]")
            else:
                console.print(f"[red]Failed to reset repository: {output}[/red]")

    def _signal_handler(self, signum, frame):
        """Handle interrupt signal (Ctrl+C)."""
        if self._handling_interrupt:
            return
        self._handling_interrupt = True
        console.print("\n[yellow]Interrupted! Cleaning up...[/yellow]")
        self.restore_signal_handler()
        self.cleanup(success=False)
        sys.exit(130)

    def setup_signal_handler(self):
        if self._original_sigint_handler is None:
            self._original_sigint_handler = signal.signal(signal.SIGINT, self._signal_handler)

    def restore_signal_handler(self):
        if self._original_sigint_handler:
            signal.signal(signal.SIGINT, self._original_sigint_handler)
            self._original_sigint_handler = None


@contextmanager
def managed_fix_branch(repo_path: Path, verbose: bool = False):
    """
    Context manager for Git branch operations during nova fix.

    Creates a nova-auto-fix/<timestamp> branch on entry, and handles cleanup on exit.
    On success, leaves the branch. On failure or interrupt, hard resets to original HEAD.
    """
    manager = GitBranchManager(repo_path, verbose)

    try:
        if not manager._check_clean_working_tree():
            console.print("[yellow]⚠️  Warning: Working tree is not clean. Uncommitted changes may be lost.[/yellow]")
            response = input("Continue anyway? (y/N): ")
            if response.lower() != "y":
                console.print("[dim]Aborted.[/dim]")
                sys.exit(1)

        manager.setup_signal_handler()
        branch_name = manager.create_fix_branch()
        yield branch_name
        manager.cleanup(success=True)
    except KeyboardInterrupt:
        manager.cleanup(success=False)
        sys.exit(130)
    except Exception:
        manager.cleanup(success=False)
        raise
    finally:
        manager.restore_signal_handler()