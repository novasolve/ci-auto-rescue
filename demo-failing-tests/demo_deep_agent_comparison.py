#!/usr/bin/env python3
"""
Comprehensive demonstration and validation of Nova Deep Agent implementations.
This script compares and validates both the provided and existing implementations.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import tempfile
import shutil

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{title}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")

def print_status(status: str, message: str):
    """Print a status message with appropriate coloring."""
    if status == "✅":
        color = Colors.OKGREEN
    elif status == "❌":
        color = Colors.FAIL
    elif status == "⚠️":
        color = Colors.WARNING
    else:
        color = Colors.OKCYAN
    print(f"{color}{status} {message}{Colors.ENDC}")

class ImplementationValidator:
    """Validates and compares Nova Deep Agent implementations."""
    
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.validation_results = {}
        
    def check_dependencies(self) -> Dict:
        """Check if all required dependencies are installed."""
        print_section("1. DEPENDENCY VALIDATION")
        
        dependencies = {
            "langchain": "LangChain core",
            "langchain_openai": "LangChain OpenAI integration",
            "langchain_anthropic": "LangChain Anthropic integration",
            "openai": "OpenAI API client",
            "anthropic": "Anthropic API client",
            "pydantic": "Data validation",
            "unidiff": "Unified diff support",
            "docker": "Docker integration"
        }
        
        results = {}
        for package, description in dependencies.items():
            try:
                module = package.replace('_', '-')
                __import__(package.replace('-', '_'))
                print_status("✅", f"{description} ({module})")
                results[package] = True
            except ImportError:
                print_status("❌", f"{description} ({module}) - NOT INSTALLED")
                results[package] = False
        
        self.validation_results['dependencies'] = results
        return results
    
    def check_implementation_files(self) -> Dict:
        """Check if key implementation files exist."""
        print_section("2. IMPLEMENTATION FILES")
        
        files_to_check = {
            "src/nova/agent/deep_agent.py": "Deep Agent (current implementation)",
            "src/nova/agent/llm_agent.py": "Legacy LLM Agent",
            "src/nova/agent/state.py": "Agent State management",
            "src/nova/agent/tools.py": "Agent tools",
            "src/nova/nodes/apply_patch.py": "Patch application node",
            "src/nova/nodes/critic.py": "Critic node",
            "src/nova/tools/patch_fixer.py": "Patch fixing utilities",
            "docker/Dockerfile": "Docker sandbox",
            "docker/run_python.py": "Docker Python runner"
        }
        
        results = {}
        for file_path, description in files_to_check.items():
            full_path = self.repo_path / file_path
            if full_path.exists():
                print_status("✅", f"{description}")
                results[file_path] = True
            else:
                print_status("❌", f"{description} - MISSING")
                results[file_path] = False
        
        self.validation_results['files'] = results
        return results
    
    def analyze_deep_agent_implementation(self) -> Dict:
        """Analyze the current Deep Agent implementation."""
        print_section("3. DEEP AGENT ANALYSIS")
        
        deep_agent_path = self.repo_path / "src/nova/agent/deep_agent.py"
        if not deep_agent_path.exists():
            print_status("❌", "Deep Agent file not found")
            return {}
        
        with open(deep_agent_path, 'r') as f:
            content = f.read()
        
        analysis = {
            "uses_langchain": "from langchain" in content,
            "has_agent_executor": "AgentExecutor" in content,
            "has_tools": "Tool" in content,
            "has_react_pattern": "ReAct" in content.lower() or "react" in content.lower(),
            "has_critic": "critic" in content.lower(),
            "has_patch_application": "apply_patch" in content.lower() or "ApplyPatch" in content,
            "uses_openai_functions": "OPENAI_FUNCTIONS" in content,
            "has_run_tests": "run_tests" in content
        }
        
        for feature, present in analysis.items():
            status = "✅" if present else "⚠️"
            feature_name = feature.replace('_', ' ').title()
            print_status(status, f"{feature_name}: {'Present' if present else 'Not detected'}")
        
        self.validation_results['deep_agent_analysis'] = analysis
        return analysis
    
    def compare_implementations(self) -> Dict:
        """Compare provided implementation with current implementation."""
        print_section("4. IMPLEMENTATION COMPARISON")
        
        print(f"\n{Colors.BOLD}Provided Implementation (from user):{Colors.ENDC}")
        print("  • Architecture: LangChain ReAct with ZeroShotAgent")
        print("  • Tools: RunTests, ApplyPatch, CriticReview (3 specialized)")
        print("  • Patch Format: Unified diff patches")
        print("  • Critic: Built-in CriticReviewTool with JSON response")
        print("  • Safety: Preflight checks, safety limits")
        
        print(f"\n{Colors.BOLD}Current Implementation (in codebase):{Colors.ENDC}")
        print("  • Architecture: LangChain with OPENAI_FUNCTIONS agent")
        print("  • Tools: plan_todo, open_file, write_file, run_tests (4 generic)")
        print("  • Patch Format: File read/write operations")
        print("  • Critic: Uses legacy LLMAgent")
        print("  • Safety: Limited safety checks")
        
        comparison = {
            "architecture_match": False,  # Different approaches
            "tool_strategy_match": False,  # Different tool sets
            "patch_format_match": False,  # Different patch handling
            "critic_integration_match": False,  # Different critic approaches
            "langchain_present": True  # Both use LangChain
        }
        
        print(f"\n{Colors.BOLD}Compatibility Assessment:{Colors.ENDC}")
        for aspect, matches in comparison.items():
            status = "✅" if matches else "⚠️"
            aspect_name = aspect.replace('_', ' ').title().replace(' Match', '')
            print_status(status, f"{aspect_name}: {'Compatible' if matches else 'Different approach'}")
        
        self.validation_results['comparison'] = comparison
        return comparison
    
    def test_calculator_demo(self) -> bool:
        """Test if the calculator demo works."""
        print_section("5. CALCULATOR DEMO TEST")
        
        # First restore buggy version
        calc_file = self.repo_path / "demo-failing-tests/src/calculator.py"
        buggy_content = """\"\"\"
Simple calculator module with a deliberately buggy implementation.
This is for demonstrating Nova CI-Rescue's automated fixing capabilities.
\"\"\"

def add(a, b):
    \"\"\"Add two numbers.\"\"\"
    # Bug: incorrect operation used
    return a - b  # (Should be a + b)

def subtract(a, b):
    \"\"\"Subtract b from a.\"\"\"
    # Bug: off-by-one error in subtraction
    return a - b - 1  # (Should be a - b)

def multiply(a, b):
    \"\"\"Multiply two numbers.\"\"\"
    # Bug: incorrect operation used
    return a + b  # (Should be a * b)

def divide(a, b):
    \"\"\"Divide a by b.\"\"\"
    # Bug: missing zero division check and wrong division behavior
    return a // b  # (Should handle b=0 and use float division a / b)"""
        
        calc_file.write_text(buggy_content)
        print_status("✅", "Restored buggy calculator.py")
        
        # Run tests to confirm they fail
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/test_calculator.py", "-v"],
            cwd=self.repo_path / "demo-failing-tests",
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print_status("✅", "Tests are failing as expected (ready for fixing)")
            # Count failures
            failures = result.stdout.count("FAILED")
            print_status("🔍", f"Found {failures} failing tests")
        else:
            print_status("⚠️", "Tests are passing (already fixed)")
        
        return result.returncode != 0
    
    def check_linear_tasks(self) -> Dict:
        """Check status of Linear tasks based on screenshot."""
        print_section("6. LINEAR TASK STATUS")
        
        tasks = {
            "OS-1005": {
                "title": "Add LangChain & OpenAI Dependencies",
                "expected": "Draft/In Progress",
                "actual": "✅ COMPLETED" if self.validation_results.get('dependencies', {}).get('langchain', False) else "❌ NOT DONE"
            },
            "OS-1006": {
                "title": "Prepare Docker Test Sandbox", 
                "expected": "Backlog",
                "actual": "✅ COMPLETED" if (self.repo_path / "docker/Dockerfile").exists() else "❌ NOT DONE"
            }
        }
        
        for task_id, task_info in tasks.items():
            print(f"\n{Colors.BOLD}{task_id}: {task_info['title']}{Colors.ENDC}")
            print(f"  Expected Status: {task_info['expected']}")
            print(f"  Actual Status: {task_info['actual']}")
        
        self.validation_results['linear_tasks'] = tasks
        return tasks
    
    def generate_unified_diff_demo(self) -> str:
        """Generate a unified diff patch for the calculator fixes."""
        print_section("7. UNIFIED DIFF GENERATION")
        
        diff = """--- a/src/calculator.py
+++ b/src/calculator.py
@@ -6,18 +6,22 @@
 def add(a, b):
     \"\"\"Add two numbers.\"\"\"
     # Bug: incorrect operation used
-    return a - b  # (Should be a + b)
+    return a + b
 
 def subtract(a, b):
     \"\"\"Subtract b from a.\"\"\"
     # Bug: off-by-one error in subtraction
-    return a - b - 1  # (Should be a - b)
+    return a - b
 
 def multiply(a, b):
     \"\"\"Multiply two numbers.\"\"\"
     # Bug: incorrect operation used
-    return a + b  # (Should be a * b)
+    return a * b
 
 def divide(a, b):
     \"\"\"Divide a by b.\"\"\"
     # Bug: missing zero division check and wrong division behavior
-    return a // b  # (Should handle b=0 and use float division a / b)
+    if b == 0:
+        raise ValueError("Cannot divide by zero")
+    return a / b"""
        
        print("Generated unified diff patch:")
        print(Colors.OKCYAN + diff[:300] + "..." + Colors.ENDC)
        
        # Save patch for potential use
        patch_file = self.repo_path / "demo-failing-tests/fix.patch"
        patch_file.write_text(diff)
        print_status("✅", f"Saved patch to {patch_file.name}")
        
        return diff
    
    def run_validation(self) -> Dict:
        """Run complete validation suite."""
        print(f"{Colors.HEADER}{Colors.BOLD}")
        print("╔═══════════════════════════════════════════════════════════╗")
        print("║     NOVA DEEP AGENT IMPLEMENTATION VALIDATION SUITE      ║")
        print("╚═══════════════════════════════════════════════════════════╝")
        print(Colors.ENDC)
        
        # Run all checks
        self.check_dependencies()
        self.check_implementation_files()
        self.analyze_deep_agent_implementation()
        self.compare_implementations()
        self.test_calculator_demo()
        self.check_linear_tasks()
        self.generate_unified_diff_demo()
        
        # Generate summary
        print_section("VALIDATION SUMMARY")
        
        total_checks = 0
        passed_checks = 0
        
        # Count dependency checks
        for dep, status in self.validation_results.get('dependencies', {}).items():
            total_checks += 1
            if status:
                passed_checks += 1
        
        # Count file checks
        for file, status in self.validation_results.get('files', {}).items():
            total_checks += 1
            if status:
                passed_checks += 1
        
        # Overall assessment
        percentage = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        
        print(f"\n{Colors.BOLD}Overall Status:{Colors.ENDC}")
        print(f"  • Total Checks: {total_checks}")
        print(f"  • Passed: {passed_checks}")
        print(f"  • Failed: {total_checks - passed_checks}")
        print(f"  • Completion: {percentage:.1f}%")
        
        if percentage >= 80:
            print_status("✅", "Implementation is MOSTLY COMPLETE")
            print("\n📝 Recommendations:")
            print("  1. The current implementation differs from the provided approach")
            print("  2. Consider migrating to unified diff patches for efficiency")
            print("  3. Integrate the specialized CriticReviewTool")
        elif percentage >= 50:
            print_status("⚠️", "Implementation is PARTIALLY COMPLETE")
            print("\n📝 Next Steps:")
            print("  1. Complete missing dependencies")
            print("  2. Implement missing components")
            print("  3. Align with the provided architecture")
        else:
            print_status("❌", "Implementation is INCOMPLETE")
            print("\n📝 Required Actions:")
            print("  1. Install missing dependencies")
            print("  2. Implement core components")
            print("  3. Follow the provided implementation guide")
        
        return self.validation_results


def main():
    """Run the validation and demonstration."""
    repo_path = Path(__file__).parent.parent
    validator = ImplementationValidator(repo_path)
    
    try:
        results = validator.run_validation()
        
        # Save results to JSON for reference
        results_file = repo_path / "demo-failing-tests/validation_results.json"
        with open(results_file, 'w') as f:
            # Convert Path objects to strings for JSON serialization
            json_safe_results = json.dumps(results, default=str, indent=2)
            f.write(json_safe_results)
        
        print(f"\n{Colors.OKGREEN}Validation results saved to: {results_file}{Colors.ENDC}")
        
    except Exception as e:
        print(f"{Colors.FAIL}Error during validation: {e}{Colors.ENDC}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

