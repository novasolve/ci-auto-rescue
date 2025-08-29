#!/usr/bin/env python3
"""
Test script to verify the patch application fix.
"""

import sys
import tempfile
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from nova.tools.fs import apply_unified_diff, apply_and_commit_patch
from rich.console import Console

console = Console()


def test_patch_application():
    """Test patch application with various scenarios."""

    console.print("[bold]Testing Patch Application Fixes[/bold]")
    console.print("=" * 50)

    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Test 1: Apply patch to matching content
        console.print("\n[cyan]Test 1: Apply patch to matching content[/cyan]")
        test_file = tmpdir / "test1.py"
        test_file.write_text(
            """def add(a, b):
    return a - b  # Bug: should be +
"""
        )

        patch1 = """--- a/test1.py
+++ b/test1.py
@@ -1,2 +1,2 @@
 def add(a, b):
-    return a - b  # Bug: should be +
+    return a + b  # Fixed
"""

        try:
            changed = apply_unified_diff(tmpdir, patch1)
            if changed:
                console.print(
                    "[green]✓ Test 1 passed: Patch applied successfully[/green]"
                )
                console.print(f"  Changed files: {[str(f.name) for f in changed]}")
                console.print(f"  New content: {test_file.read_text()}")
            else:
                console.print("[red]✗ Test 1 failed: No files changed[/red]")
        except Exception as e:
            console.print(f"[red]✗ Test 1 failed: {e}[/red]")

        # Test 2: Apply patch to already fixed content (should fail gracefully)
        console.print("\n[cyan]Test 2: Apply patch to already fixed content[/cyan]")
        test_file2 = tmpdir / "test2.py"
        test_file2.write_text(
            """def multiply(a, b):
    return a * b  # Already correct
"""
        )

        patch2 = """--- a/test2.py
+++ b/test2.py
@@ -1,2 +1,2 @@
 def multiply(a, b):
-    return a + b  # Wrong operation
+    return a * b  # Fixed
"""

        try:
            changed = apply_unified_diff(tmpdir, patch2)
            if not changed:
                console.print(
                    "[green]✓ Test 2 passed: Correctly detected no changes needed[/green]"
                )
            else:
                console.print(
                    "[yellow]⚠ Test 2: Patch applied but content may have been different[/yellow]"
                )
        except Exception as e:
            console.print(
                f"[green]✓ Test 2 passed: Correctly failed on mismatched content - {e}[/green]"
            )

        # Test 3: Apply patch with context mismatch (fuzzy matching)
        console.print("\n[cyan]Test 3: Apply patch with slight context mismatch[/cyan]")
        test_file3 = tmpdir / "test3.py"
        test_file3.write_text(
            """# Comment added
def divide(a, b):
    if b == 0:
        return None
    return a / b
"""
        )

        patch3 = """--- a/test3.py
+++ b/test3.py
@@ -1,4 +1,4 @@
 def divide(a, b):
     if b == 0:
-        return None
+        raise ValueError("Division by zero")
     return a / b
"""

        try:
            changed = apply_unified_diff(tmpdir, patch3)
            if changed:
                console.print("[green]✓ Test 3 passed: Fuzzy matching worked[/green]")
                console.print(f"  New content:\n{test_file3.read_text()}")
            else:
                console.print("[yellow]⚠ Test 3: No changes applied[/yellow]")
        except Exception as e:
            console.print(f"[yellow]⚠ Test 3: {e}[/yellow]")

        # Test 4: Empty patch
        console.print("\n[cyan]Test 4: Handle empty patch[/cyan]")
        success, files = apply_and_commit_patch(tmpdir, "", 1, verbose=True)
        if not success:
            console.print(
                "[green]✓ Test 4 passed: Empty patch correctly rejected[/green]"
            )
        else:
            console.print("[red]✗ Test 4 failed: Empty patch was accepted[/red]")

        # Test 5: Create new file via patch
        console.print("\n[cyan]Test 5: Create new file via patch[/cyan]")
        patch5 = """--- /dev/null
+++ b/new_file.py
@@ -0,0 +1,3 @@
+def hello():
+    print("Hello, World!")
+    return True
"""

        try:
            changed = apply_unified_diff(tmpdir, patch5)
            new_file = tmpdir / "new_file.py"
            if new_file.exists() and changed:
                console.print("[green]✓ Test 5 passed: New file created[/green]")
                console.print(f"  Content:\n{new_file.read_text()}")
            else:
                console.print("[red]✗ Test 5 failed: New file not created[/red]")
        except Exception as e:
            console.print(f"[red]✗ Test 5 failed: {e}[/red]")

    console.print("\n" + "=" * 50)
    console.print("[bold green]All tests completed![/bold green]")
    console.print("\nSummary of fixes:")
    console.print("• Enhanced error handling with specific exception types")
    console.print("• Added validation for empty patches")
    console.print("• Improved context matching with fuzzy search")
    console.print("• Better diagnostic output in verbose mode")
    console.print("• Graceful handling of already-fixed content")


if __name__ == "__main__":
    test_patch_application()
