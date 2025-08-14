"""
Tests for the safety limits module.
"""

import pytest
from pathlib import Path
from nova.tools.safety_limits import (
    SafetyLimits,
    SafetyConfig,
    PatchAnalysis,
    check_patch_safety
)


class TestSafetyLimits:
    """Test suite for SafetyLimits class."""
    
    def test_init_default_config(self):
        """Test initialization with default configuration."""
        safety = SafetyLimits()
        assert safety.config.max_lines_changed == 200
        assert safety.config.max_files_modified == 10
        assert len(safety.config.denied_paths) > 0
        
    def test_init_custom_config(self):
        """Test initialization with custom configuration."""
        config = SafetyConfig(
            max_lines_changed=100,
            max_files_modified=5,
            denied_paths=["custom/*"]
        )
        safety = SafetyLimits(config=config)
        assert safety.config.max_lines_changed == 100
        assert safety.config.max_files_modified == 5
        assert "custom/*" in safety.config.denied_paths
    
    def test_analyze_patch_simple(self):
        """Test analyzing a simple patch."""
        patch = """
--- a/src/main.py
+++ b/src/main.py
@@ -1,3 +1,4 @@
 def main():
-    print("Hello")
+    print("Hello World")
+    return 0
"""
        safety = SafetyLimits()
        analysis = safety.analyze_patch(patch)
        
        assert analysis.total_lines_added == 2
        assert analysis.total_lines_removed == 1
        assert analysis.total_lines_changed == 3
        assert "src/main.py" in analysis.files_modified
        
    def test_analyze_patch_multiple_files(self):
        """Test analyzing a patch with multiple files."""
        patch = """
--- a/src/main.py
+++ b/src/main.py
@@ -1,2 +1,3 @@
 def main():
+    # New comment
     print("Hello")
--- a/src/utils.py
+++ b/src/utils.py
@@ -1,1 +1,2 @@
-def helper():
+def helper(arg):
+    return arg
"""
        safety = SafetyLimits()
        analysis = safety.analyze_patch(patch)
        
        assert analysis.total_lines_added == 3
        assert analysis.total_lines_removed == 1
        assert analysis.total_lines_changed == 4
        assert "src/main.py" in analysis.files_modified
        assert "src/utils.py" in analysis.files_modified
        assert len(analysis.files_modified) == 2
        
    def test_analyze_patch_new_file(self):
        """Test analyzing a patch that creates a new file."""
        patch = """
--- /dev/null
+++ b/src/new_file.py
@@ -0,0 +1,3 @@
+def new_function():
+    pass
+
"""
        safety = SafetyLimits()
        analysis = safety.analyze_patch(patch)
        
        assert analysis.total_lines_added == 3
        assert analysis.total_lines_removed == 0
        assert "src/new_file.py" in analysis.files_added
        assert len(analysis.files_modified) == 0
        
    def test_analyze_patch_delete_file(self):
        """Test analyzing a patch that deletes a file."""
        patch = """
--- a/src/old_file.py
+++ /dev/null
@@ -1,3 +0,0 @@
-def old_function():
-    pass
-
"""
        safety = SafetyLimits()
        analysis = safety.analyze_patch(patch)
        
        assert analysis.total_lines_added == 0
        assert analysis.total_lines_removed == 3
        assert "src/old_file.py" in analysis.files_deleted
        assert len(analysis.files_modified) == 0
        
    def test_validate_patch_within_limits(self):
        """Test validating a patch within safety limits."""
        patch = """
--- a/src/main.py
+++ b/src/main.py
@@ -1,3 +1,4 @@
 def main():
-    print("Hello")
+    print("Hello World")
+    return 0
"""
        safety = SafetyLimits()
        is_safe, violations = safety.validate_patch(patch)
        
        assert is_safe is True
        assert len(violations) == 0
        
    def test_validate_patch_exceeds_line_limit(self):
        """Test validating a patch that exceeds line limit."""
        # Create a patch with many line changes
        lines = []
        for i in range(250):  # More than default 200 limit
            lines.append(f"+    line_{i}()")
        
        patch = f"""
--- a/src/main.py
+++ b/src/main.py
@@ -1,1 +1,251 @@
 def main():
{chr(10).join(lines)}
"""
        safety = SafetyLimits()
        is_safe, violations = safety.validate_patch(patch)
        
        assert is_safe is False
        assert len(violations) > 0
        assert "Exceeds maximum lines changed" in violations[0]
        
    def test_validate_patch_exceeds_file_limit(self):
        """Test validating a patch that modifies too many files."""
        patch_parts = []
        for i in range(15):  # More than default 10 limit
            patch_parts.append(f"""
--- a/src/file_{i}.py
+++ b/src/file_{i}.py
@@ -1,1 +1,1 @@
-old_line
+new_line
""")
        
        patch = "\n".join(patch_parts)
        safety = SafetyLimits()
        is_safe, violations = safety.validate_patch(patch)
        
        assert is_safe is False
        assert len(violations) > 0
        assert "Exceeds maximum files modified" in violations[0]
        
    def test_validate_patch_denied_ci_file(self):
        """Test validating a patch that modifies CI configuration."""
        patch = """
--- a/.github/workflows/test.yml
+++ b/.github/workflows/test.yml
@@ -1,1 +1,2 @@
 name: Test
+# Modified
"""
        safety = SafetyLimits()
        is_safe, violations = safety.validate_patch(patch)
        
        assert is_safe is False
        assert len(violations) > 0
        assert "restricted files" in violations[0].lower()
        
    def test_validate_patch_denied_deployment_file(self):
        """Test validating a patch that modifies deployment files."""
        patch = """
--- a/deploy/production.yml
+++ b/deploy/production.yml
@@ -1,1 +1,1 @@
-replicas: 2
+replicas: 3
"""
        safety = SafetyLimits()
        is_safe, violations = safety.validate_patch(patch)
        
        assert is_safe is False
        assert "restricted files" in violations[0].lower()
        
    def test_validate_patch_denied_secrets_file(self):
        """Test validating a patch that modifies secrets."""
        patch = """
--- a/config/secrets/api_key.txt
+++ b/config/secrets/api_key.txt
@@ -1,1 +1,1 @@
-old_key
+new_key
"""
        safety = SafetyLimits()
        is_safe, violations = safety.validate_patch(patch)
        
        assert is_safe is False
        assert "restricted files" in violations[0].lower()
        
    def test_validate_patch_denied_env_file(self):
        """Test validating a patch that modifies .env files."""
        patch = """
--- a/.env.production
+++ b/.env.production
@@ -1,1 +1,1 @@
-API_KEY=old
+API_KEY=new
"""
        safety = SafetyLimits()
        is_safe, violations = safety.validate_patch(patch)
        
        assert is_safe is False
        assert "restricted files" in violations[0].lower()
        
    def test_validate_patch_multiple_violations(self):
        """Test patch with multiple violations."""
        # Create a patch that violates multiple rules
        lines = []
        for i in range(250):  # Exceeds line limit
            lines.append(f"+    line_{i}()")
        
        patch = f"""
--- a/.github/workflows/ci.yml
+++ b/.github/workflows/ci.yml
@@ -1,1 +1,251 @@
 name: CI
{chr(10).join(lines)}
"""
        safety = SafetyLimits()
        is_safe, violations = safety.validate_patch(patch)
        
        assert is_safe is False
        assert len(violations) >= 2  # At least line limit and denied file
        
    def test_friendly_error_message(self):
        """Test generation of user-friendly error messages."""
        violations = [
            "Exceeds maximum lines changed: 300 > 200",
            "Attempts to modify restricted files: .github/workflows/ci.yml"
        ]
        
        safety = SafetyLimits()
        message = safety.get_friendly_error_message(violations)
        
        assert "Safety Check Failed" in message
        assert "300 > 200" in message
        assert ".github/workflows/ci.yml" in message
        assert "What to do next" in message
        
    def test_check_patch_safety_convenience_function(self):
        """Test the convenience function for checking patch safety."""
        patch = """
--- a/src/main.py
+++ b/src/main.py
@@ -1,1 +1,1 @@
-print("old")
+print("new")
"""
        is_safe, message = check_patch_safety(patch)
        
        assert is_safe is True
        assert message == ""
        
    def test_check_patch_safety_with_violations(self):
        """Test convenience function with violations."""
        patch = """
--- a/.github/workflows/test.yml
+++ b/.github/workflows/test.yml
@@ -1,1 +1,1 @@
-name: Old
+name: New
"""
        is_safe, message = check_patch_safety(patch)
        
        assert is_safe is False
        assert "Safety Check Failed" in message
        
    def test_custom_config_override(self):
        """Test that custom config properly overrides defaults."""
        config = SafetyConfig(
            max_lines_changed=10,
            max_files_modified=2,
            denied_paths=["test/*"]
        )
        
        # Patch with 15 lines changed
        patch = """
--- a/src/main.py
+++ b/src/main.py
@@ -1,5 +1,10 @@
-line1
-line2
-line3
-line4
-line5
+new_line1
+new_line2
+new_line3
+new_line4
+new_line5
+new_line6
+new_line7
+new_line8
+new_line9
+new_line10
"""
        
        safety = SafetyLimits(config=config)
        is_safe, violations = safety.validate_patch(patch)
        
        assert is_safe is False
        assert "Exceeds maximum lines changed: 15 > 10" in violations[0]
        
    def test_denied_path_patterns(self):
        """Test regex pattern matching for denied paths."""
        config = SafetyConfig(
            denied_path_patterns=[r".*\.min\.js$", r".*\.pyc$"]
        )
        
        patch = """
--- a/static/app.min.js
+++ b/static/app.min.js
@@ -1,1 +1,1 @@
-minified_old
+minified_new
"""
        
        safety = SafetyLimits(config=config)
        is_safe, violations = safety.validate_patch(patch)
        
        assert is_safe is False
        assert "restricted files" in violations[0].lower()
        
    def test_glob_pattern_matching(self):
        """Test glob pattern matching for various path formats."""
        config = SafetyConfig(
            denied_paths=["**/migrations/*", "db/migrate/*", "*.lock"]
        )
        
        safety = SafetyLimits(config=config)
        
        # Test various paths
        assert safety._is_denied_path("app/migrations/001_initial.py") is True
        assert safety._is_denied_path("db/migrate/20240101_create_users.rb") is True
        assert safety._is_denied_path("package.lock") is True
        assert safety._is_denied_path("src/main.py") is False
        assert safety._is_denied_path("tests/test_app.py") is False
        
    def test_empty_patch(self):
        """Test handling of empty patch."""
        safety = SafetyLimits()
        analysis = safety.analyze_patch("")
        
        assert analysis.total_lines_changed == 0
        assert len(analysis.files_modified) == 0
        
        is_safe, violations = safety.validate_patch("")
        assert is_safe is True
        assert len(violations) == 0
        
    def test_malformed_patch_handling(self):
        """Test handling of malformed patches."""
        # Patch without proper headers
        patch = """
This is not a valid patch
Random text here
"""
        safety = SafetyLimits()
        analysis = safety.analyze_patch(patch)
        
        # Should handle gracefully without crashing
        assert analysis.total_lines_changed == 0
        assert len(analysis.files_modified) == 0


class TestPatchAnalysis:
    """Test suite for PatchAnalysis dataclass."""
    
    def test_default_values(self):
        """Test PatchAnalysis default values."""
        analysis = PatchAnalysis()
        
        assert analysis.total_lines_added == 0
        assert analysis.total_lines_removed == 0
        assert analysis.total_lines_changed == 0
        assert len(analysis.files_modified) == 0
        assert len(analysis.files_added) == 0
        assert len(analysis.files_deleted) == 0
        assert len(analysis.denied_files) == 0
        assert len(analysis.violations) == 0
        assert analysis.is_safe is True
        
    def test_field_updates(self):
        """Test updating PatchAnalysis fields."""
        analysis = PatchAnalysis()
        
        analysis.total_lines_added = 10
        analysis.total_lines_removed = 5
        analysis.total_lines_changed = 15
        analysis.files_modified.add("test.py")
        analysis.violations.append("Test violation")
        analysis.is_safe = False
        
        assert analysis.total_lines_added == 10
        assert analysis.total_lines_removed == 5
        assert analysis.total_lines_changed == 15
        assert "test.py" in analysis.files_modified
        assert "Test violation" in analysis.violations
        assert analysis.is_safe is False


class TestSafetyConfig:
    """Test suite for SafetyConfig dataclass."""
    
    def test_default_values(self):
        """Test SafetyConfig default values."""
        config = SafetyConfig()
        
        assert config.max_lines_changed == 200
        assert config.max_files_modified == 10
        assert len(config.denied_paths) > 0
        assert ".github/workflows/*" in config.denied_paths
        assert "deploy/*" in config.denied_paths
        
    def test_custom_values(self):
        """Test SafetyConfig with custom values."""
        config = SafetyConfig(
            max_lines_changed=500,
            max_files_modified=20,
            denied_paths=["custom/*"],
            denied_path_patterns=[r".*\.test$"]
        )
        
        assert config.max_lines_changed == 500
        assert config.max_files_modified == 20
        assert config.denied_paths == ["custom/*"]
        assert config.denied_path_patterns == [r".*\.test$"]


# Integration tests
class TestIntegration:
    """Integration tests for safety limits with real-world scenarios."""
    
    def test_typical_safe_patch(self):
        """Test a typical safe patch that should pass all checks."""
        patch = """
--- a/src/calculator.py
+++ b/src/calculator.py
@@ -10,7 +10,11 @@ class Calculator:
     def add(self, a, b):
         return a + b
     
-    def subtract(self, a, b):
-        return a - b
+    def subtract(self, a, b, absolute=False):
+        result = a - b
+        if absolute:
+            return abs(result)
+        return result
     
     def multiply(self, a, b):
         return a * b
--- a/tests/test_calculator.py
+++ b/tests/test_calculator.py
@@ -15,6 +15,10 @@ class TestCalculator:
     def test_subtract(self):
         assert self.calc.subtract(5, 3) == 2
         
+    def test_subtract_absolute(self):
+        assert self.calc.subtract(3, 5, absolute=True) == 2
+        assert self.calc.subtract(5, 3, absolute=True) == 2
+        
     def test_multiply(self):
         assert self.calc.multiply(3, 4) == 12
"""
        
        is_safe, message = check_patch_safety(patch)
        assert is_safe is True
        
    def test_large_refactoring_patch(self):
        """Test a large refactoring that exceeds limits."""
        # Simulate a large refactoring across many files
        files = []
        for i in range(15):
            files.append(f"""
--- a/src/module{i}/component.py
+++ b/src/module{i}/component.py
@@ -1,20 +1,35 @@
""")
            for j in range(20):
                files.append(f"-    old_line_{j}()")
            for j in range(35):
                files.append(f"+    new_line_{j}()")
        
        patch = "\n".join(files)
        
        is_safe, message = check_patch_safety(patch)
        assert is_safe is False
        assert "Exceeds maximum files modified" in message
        assert "Exceeds maximum lines changed" in message
        
    def test_security_sensitive_patch(self):
        """Test patch modifying security-sensitive files."""
        patch = """
--- a/src/auth.py
+++ b/src/auth.py
@@ -5,3 +5,4 @@
 def authenticate(username, password):
     # Check credentials
     return True
+    # TODO: Actually implement auth
--- a/.env.production
+++ b/.env.production
@@ -1,2 +1,2 @@
-SECRET_KEY=old_secret_key_12345
+SECRET_KEY=new_secret_key_67890
 API_URL=https://api.example.com
--- a/deploy/kubernetes.yml
+++ b/deploy/kubernetes.yml
@@ -10,7 +10,7 @@ spec:
   selector:
     app: myapp
   replicas: 3
-  minReadySeconds: 10
+  minReadySeconds: 5
"""
        
        is_safe, message = check_patch_safety(patch)
        assert is_safe is False
        assert "restricted files" in message.lower()
        # Should detect both .env.production and deploy/kubernetes.yml
        
    def test_dependency_update_patch(self):
        """Test patch updating dependency lock files."""
        patch = """
--- a/requirements.txt
+++ b/requirements.txt
@@ -1,5 +1,5 @@
-django==3.2.0
+django==3.2.1
 requests==2.28.0
--- a/poetry.lock
+++ b/poetry.lock
@@ -100,7 +100,7 @@
 [[package]]
 name = "django"
-version = "3.2.0"
+version = "3.2.1"
"""
        
        is_safe, message = check_patch_safety(patch)
        assert is_safe is False
        assert "poetry.lock" in message


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
