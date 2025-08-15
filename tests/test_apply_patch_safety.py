"""
Test apply patch safety checks to ensure CI safety limits are enforced
"""
import pytest
import subprocess
import tempfile
from pathlib import Path


def test_apply_patch_rejects_unsafe_changes(tmp_path):
    """Test that patches violating safety limits are rejected"""
    from nova.agent.state import AgentState
    from nova.nodes.apply_patch import ApplyPatchNode
    
    # Create a dummy repository (git init) in a temp dir
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    
    # Initialize git repo
    subprocess.run(["git", "init"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path)
    
    # Commit an initial file to allow branch creation
    (repo_path / "README.md").write_text("# Test Repository\n\nThis is a test.")
    subprocess.run(["git", "add", "README.md"], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True)
    
    # Create the .github/workflows directory
    workflows_dir = repo_path / ".github" / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)
    (workflows_dir / "test.yml").write_text("name: Old\n")
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Add workflow"], cwd=repo_path, check=True)
    
    # Prepare a patch that violates safety limits (modifies a restricted file)
    unsafe_patch = """\
--- a/.github/workflows/test.yml
+++ b/.github/workflows/test.yml
@@ -1 +1 @@
-name: Old
+name: New
"""
    
    state = AgentState(repo_path=str(repo_path))
    node = ApplyPatchNode(verbose=False)  # verbose=False to suppress console output
    
    # Execute with safety checks enabled (default)
    result = node.execute(state, patch_text=unsafe_patch, skip_safety_check=False)
    
    # Assert that the patch was rejected due to safety violation
    assert result["success"] is False, "Unsafe patch should have been rejected"
    assert result.get("safety_violation") is True, "Should indicate safety violation"
    
    # The safety_message should mention the restricted file
    safety_msg = result.get("safety_message", "")
    assert "workflows/test.yml" in safety_msg or ".github" in safety_msg, \
        f"Safety message should mention restricted path: {safety_msg}"


def test_apply_patch_allows_safe_changes(tmp_path):
    """Test that safe patches are allowed through"""
    from nova.agent.state import AgentState
    from nova.nodes.apply_patch import ApplyPatchNode
    
    # Create a dummy repository
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    
    # Initialize git repo
    subprocess.run(["git", "init"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path)
    
    # Create initial files
    src_dir = repo_path / "src"
    src_dir.mkdir()
    (src_dir / "calculator.py").write_text("""
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
""")
    
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True)
    
    # Prepare a safe patch (modifies regular source code)
    safe_patch = """\
--- a/src/calculator.py
+++ b/src/calculator.py
@@ -4,3 +4,6 @@ def add(a, b):
 
 def subtract(a, b):
     return a - b
+
+def multiply(a, b):
+    return a * b
"""
    
    state = AgentState(repo_path=str(repo_path))
    node = ApplyPatchNode(verbose=False)
    
    # Execute with safety checks enabled
    result = node.execute(state, patch_text=safe_patch, skip_safety_check=False)
    
    # Assert that the safe patch was applied successfully
    assert result["success"] is True, f"Safe patch should have been applied: {result}"
    assert result.get("safety_violation") is False or "safety_violation" not in result
    
    # Verify the file was actually modified
    modified_content = (src_dir / "calculator.py").read_text()
    assert "def multiply" in modified_content, "File should have been modified"


def test_safety_limits_file_size_restriction(tmp_path):
    """Test that patches creating files over size limit are rejected"""
    from nova.agent.state import AgentState
    from nova.nodes.apply_patch import ApplyPatchNode
    from nova.tools.safety_limits import SafetyLimits
    
    # Create a dummy repository
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    
    # Initialize git repo
    subprocess.run(["git", "init"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path)
    
    # Create initial file
    (repo_path / "README.md").write_text("# Test")
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Initial"], cwd=repo_path, check=True)
    
    # Generate a patch that adds too many lines (over default limit)
    large_content = "\n".join([f"+Line {i}" for i in range(SafetyLimits.MAX_LINES_PER_FILE + 100)])
    oversized_patch = f"""\
--- /dev/null
+++ b/large_file.py
@@ -0,0 +1,{SafetyLimits.MAX_LINES_PER_FILE + 100} @@
{large_content}
"""
    
    state = AgentState(repo_path=str(repo_path))
    node = ApplyPatchNode(verbose=False)
    
    result = node.execute(state, patch_text=oversized_patch, skip_safety_check=False)
    
    # Should be rejected due to file size
    assert result["success"] is False, "Oversized file patch should be rejected"
    assert result.get("safety_violation") is True
    assert "lines" in result.get("safety_message", "").lower(), \
        "Should mention line limit violation"


def test_safety_limits_multiple_violations(tmp_path):
    """Test detection of multiple safety violations in one patch"""
    from nova.agent.state import AgentState
    from nova.nodes.apply_patch import ApplyPatchNode
    
    # Create a dummy repository
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    
    # Initialize git repo
    subprocess.run(["git", "init"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path)
    
    # Create initial structure
    (repo_path / "README.md").write_text("# Test")
    (repo_path / ".github").mkdir()
    (repo_path / ".github" / "CODEOWNERS").write_text("* @owner")
    
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Initial"], cwd=repo_path, check=True)
    
    # Create a patch with multiple violations:
    # 1. Modifies .github/CODEOWNERS (restricted)
    # 2. Modifies package.json (restricted)
    multi_violation_patch = """\
--- a/.github/CODEOWNERS
+++ b/.github/CODEOWNERS
@@ -1 +1 @@
-* @owner
+* @hacker
--- /dev/null
+++ b/package.json
@@ -0,0 +1,3 @@
+{
+  "name": "malicious"
+}
"""
    
    state = AgentState(repo_path=str(repo_path))
    node = ApplyPatchNode(verbose=False)
    
    result = node.execute(state, patch_text=multi_violation_patch, skip_safety_check=False)
    
    # Should be rejected with multiple violations noted
    assert result["success"] is False
    assert result.get("safety_violation") is True
    
    safety_msg = result.get("safety_message", "")
    # Should mention at least one of the restricted files
    assert ("CODEOWNERS" in safety_msg or "package.json" in safety_msg or 
            ".github" in safety_msg), \
        f"Should mention restricted files: {safety_msg}"


def test_skip_safety_check_flag(tmp_path):
    """Test that skip_safety_check flag bypasses safety limits"""
    from nova.agent.state import AgentState
    from nova.nodes.apply_patch import ApplyPatchNode
    
    # Create a dummy repository
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    
    # Initialize git repo
    subprocess.run(["git", "init"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path)
    
    # Create initial file and restricted directory
    (repo_path / "README.md").write_text("# Test")
    workflows_dir = repo_path / ".github" / "workflows"
    workflows_dir.mkdir(parents=True)
    (workflows_dir / "ci.yml").write_text("name: CI\n")
    
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Initial"], cwd=repo_path, check=True)
    
    # Unsafe patch that would normally be rejected
    unsafe_patch = """\
--- a/.github/workflows/ci.yml
+++ b/.github/workflows/ci.yml
@@ -1 +1,2 @@
 name: CI
+# Modified
"""
    
    state = AgentState(repo_path=str(repo_path))
    node = ApplyPatchNode(verbose=False)
    
    # Try with skip_safety_check=True
    result = node.execute(state, patch_text=unsafe_patch, skip_safety_check=True)
    
    # Should succeed when safety checks are skipped
    assert result["success"] is True, \
        f"Patch should succeed with skip_safety_check=True: {result}"
    
    # Verify file was actually modified
    modified = (workflows_dir / "ci.yml").read_text()
    assert "# Modified" in modified, "File should have been modified"


def test_safety_message_clarity(tmp_path):
    """Test that safety violation messages are clear and actionable"""
    from nova.agent.state import AgentState
    from nova.nodes.apply_patch import ApplyPatchNode
    
    # Create a dummy repository
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    
    # Initialize git repo
    subprocess.run(["git", "init"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path)
    
    # Create initial files
    (repo_path / "README.md").write_text("# Test")
    (repo_path / "setup.py").write_text("# Setup file")
    
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Initial"], cwd=repo_path, check=True)
    
    # Try to modify setup.py (restricted)
    restricted_patch = """\
--- a/setup.py
+++ b/setup.py
@@ -1 +1,2 @@
 # Setup file
+# Malicious change
"""
    
    state = AgentState(repo_path=str(repo_path))
    node = ApplyPatchNode(verbose=False)
    
    result = node.execute(state, patch_text=restricted_patch, skip_safety_check=False)
    
    # Check that the message is informative
    assert result["success"] is False
    safety_msg = result.get("safety_message", "")
    
    # Message should be non-empty and informative
    assert len(safety_msg) > 20, "Safety message should be detailed"
    assert "setup.py" in safety_msg.lower() or "restricted" in safety_msg.lower(), \
        f"Message should explain the issue: {safety_msg}"
    
    # Should not contain technical jargon only
    assert not safety_msg.startswith("Error:"), \
        "Message should be user-friendly, not just an error"
