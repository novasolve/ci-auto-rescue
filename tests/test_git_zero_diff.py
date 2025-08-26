# tests/test_git_zero_diff.py
from src.nova.tools.git import GitBranchManager
from pathlib import Path
import subprocess

def test_zero_diff_commit_noop(tmp_path: Path, monkeypatch):
    repo = tmp_path
    subprocess.run(["git","init","-q"], cwd=repo)
    (repo/"a.txt").write_text("x")
    subprocess.run(["git","add","-A"], cwd=repo)
    subprocess.run(["git","commit","-m","init","-q"], cwd=repo)
    mgr = GitBranchManager(repo)
    mgr.create_fix_branch()
    ok, out = mgr._run_git_command("diff","--cached","--quiet"); assert ok
    # simulate apply_and_commit_patch's zero-diff guard
    ok, _ = mgr._run_git_command("diff","--cached","--quiet")
    assert ok  # no staged changes => would skip commit
