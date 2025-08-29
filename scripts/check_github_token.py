#!/usr/bin/env python3
"""
Check GitHub token validity and permissions.

- Reads token from GITHUB_TOKEN (fallback GH_TOKEN)
- Verifies with GitHub REST API (/user)
- Prints token owner, visible scopes, and rate limit
- If a repo is detected (env GITHUB_REPOSITORY or git remote), checks access and prints permissions
- Exit code: 0 if valid; non‑zero otherwise
"""

import os
import sys
import json
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Tuple

import requests


def obfuscate(token: str) -> str:
    if not token or len(token) < 8:
        return "****"
    return f"{token[:4]}...{token[-4:]}"


def get_repo_from_env_or_git(cwd: Path) -> Optional[Tuple[str, str]]:
    repo_env = os.environ.get("GITHUB_REPOSITORY")
    if repo_env and "/" in repo_env:
        owner, repo = repo_env.split("/", 1)
        return owner, repo
    try:
        r = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            cwd=cwd,
        )
        if r.returncode != 0:
            return None
        url = r.stdout.strip()
        if "github.com" not in url:
            return None
        if url.startswith("https://"):
            # https://github.com/owner/repo.git
            parts = (
                url.replace("https://github.com/", "").replace(".git", "").split("/")
            )
        elif url.startswith("git@"):
            # git@github.com:owner/repo.git
            parts = url.replace("git@github.com:", "").replace(".git", "").split("/")
        else:
            return None
        if len(parts) >= 2:
            return parts[0], parts[1]
    except Exception:
        return None
    return None


def main() -> int:
    cwd = Path.cwd()

    # Prefer GitHub CLI auth if available and configured
    gh = shutil.which("gh")
    if gh:
        st = subprocess.run([gh, "auth", "status"], capture_output=True, text=True)
        if st.returncode == 0:
            print("gh CLI: authenticated")
            # Get user via gh api
            who = subprocess.run([gh, "api", "user"], capture_output=True, text=True)
            if who.returncode == 0 and who.stdout.strip():
                try:
                    u = json.loads(who.stdout)
                    print(f"User: {u.get('login', '<unknown>')}")
                except Exception:
                    print("User: <unknown>")
            # Rate limit via gh api
            rl = subprocess.run(
                [gh, "api", "rate_limit"], capture_output=True, text=True
            )
            if rl.returncode == 0 and rl.stdout.strip():
                try:
                    core = json.loads(rl.stdout).get("resources", {}).get("core", {})
                    print(
                        f"Rate limit: {core.get('remaining', '?')}/{core.get('limit', '?')} remaining, resets at {core.get('reset', '?')}"
                    )
                except Exception:
                    pass
            # Repo permissions if resolvable
            repo = get_repo_from_env_or_git(cwd)
            if repo:
                owner, name = repo
                rp = subprocess.run(
                    [gh, "api", f"repos/{owner}/{name}"], capture_output=True, text=True
                )
                if rp.returncode == 0 and rp.stdout.strip():
                    try:
                        data = json.loads(rp.stdout)
                        perms = data.get("permissions", {})
                        print(f"Repo: {owner}/{name}")
                        if perms:
                            print(f"Permissions: {json.dumps(perms)}")
                            print(
                                f"PR creation likely requires: push=true -> {perms.get('push', False)}"
                            )
                    except Exception:
                        pass
            print("OK: gh CLI authentication valid.")
            return 0
        else:
            print("gh CLI present but not authenticated (gh auth login)")

    # Fallback to token-based check
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("ERROR: No GITHUB_TOKEN or GH_TOKEN in environment.")
        print('Help: export GITHUB_TOKEN="<your_token>"')
        return 2

    print(f"Token: {obfuscate(token)}")

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "nova-ci-rescue-token-check",
    }

    # 1) /user
    try:
        r = requests.get("https://api.github.com/user", headers=headers, timeout=10)
    except requests.RequestException as e:
        print(f"ERROR: Network/Request error calling /user: {e}")
        return 3

    if r.status_code != 200:
        print(f"ERROR: GitHub /user returned {r.status_code}: {r.text}")
        if r.status_code == 401:
            print(
                "Diagnosis: Bad credentials – token invalid or lacks required access."
            )
        return 4

    user = r.json().get("login", "<unknown>")
    scopes = r.headers.get("X-OAuth-Scopes", "")
    accepted = r.headers.get("X-Accepted-OAuth-Scopes", "")
    print(f"User: {user}")
    print(f"Scopes: {scopes or '<none visible>'}")
    if accepted:
        print(f"Accepted-Scopes (for this endpoint): {accepted}")

    # 2) Rate limit
    try:
        rl = requests.get(
            "https://api.github.com/rate_limit", headers=headers, timeout=10
        )
        if rl.status_code == 200:
            core = rl.json().get("resources", {}).get("core", {})
            print(
                f"Rate limit: {core.get('remaining', '?')}/{core.get('limit', '?')} remaining, resets at {core.get('reset', '?')}"
            )
    except requests.RequestException:
        pass

    # 3) Repository access (if resolvable)
    cwd = Path.cwd()
    repo = get_repo_from_env_or_git(cwd)
    if repo:
        owner, name = repo
        try:
            resp = requests.get(
                f"https://api.github.com/repos/{owner}/{name}",
                headers=headers,
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                perms = data.get("permissions", {})
                print(f"Repo: {owner}/{name}")
                if perms:
                    print(f"Permissions: {json.dumps(perms)}")
                    print(
                        f"PR creation likely requires: repo access with write on target; current perms -> push={perms.get('push', False)}"
                    )
                else:
                    print(
                        "Permissions: <not visible> (token may be fine-grained; ensure it has PR:write on this repo)"
                    )
            else:
                print(
                    f"Warning: Could not access repo {owner}/{name}: {resp.status_code} {resp.text}"
                )
        except requests.RequestException as e:
            print(f"Warning: Repo check failed: {e}")

    print("OK: Token appears valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
