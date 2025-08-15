import sys
sys.path.insert(0, '/Users/seb/GPT5/working/ci-auto-rescue/src')

from nova.tools.patch_fixer import attempt_patch_reconstruction

# Simulate a patch with wrong comments (but correct path)
patch_text = """--- a/src/calculator.py
+++ b/src/calculator.py
@@ -1,4 +1,4 @@
 def add(a, b):
-    return a - b  # wrong
+    return a + b  # fixed
"""

repo_root = "/Users/seb/GPT5/working/ci-auto-rescue/demo-failing-tests"
reconstructed = attempt_patch_reconstruction(patch_text, repo_root, verbose=True)
print("\n=== RECONSTRUCTED PATCH ===")
print(reconstructed)
