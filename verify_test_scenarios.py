#!/usr/bin/env python3
"""
Verification script to ensure all test scenarios have bugs in the correct place.
Rule: Bugs should be in implementation files, not test files (except for intentional edge cases).
"""

import os
import sys
import tempfile
from pathlib import Path

# Add parent directory to path to import our test suite
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nova_unified_test_suite import SyntheticRepoGenerator

def verify_scenario(name: str, repo_path: Path) -> dict:
    """Verify a single test scenario."""
    result = {
        "name": name,
        "path": str(repo_path),
        "implementation_files": [],
        "test_files": [],
        "issues": [],
        "status": "✅ OK"
    }
    
    # Find implementation and test files
    src_dir = repo_path / "src"
    tests_dir = repo_path / "tests"
    
    if src_dir.exists():
        for file in src_dir.glob("*.py"):
            if file.name != "__init__.py":
                content = file.read_text()
                result["implementation_files"].append(file.name)
                
                # Check for bug indicators in implementation
                if "# Bug:" in content:
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if "# Bug:" in line:
                            print(f"  ✓ {file.name}:{i+1} - {line.strip()}")
    
    if tests_dir.exists():
        for file in tests_dir.glob("test_*.py"):
            content = file.read_text()
            result["test_files"].append(file.name)
            
            # Check for wrong expectations in tests (should only be in unfixable scenarios)
            if "wrong" in content.lower() or "should be" in content.lower():
                if name not in ["unfixable_bug", "no_op_patch"]:
                    result["issues"].append(f"Test file {file.name} may have wrong expectations")
                    result["status"] = "⚠️ WARNING"
                else:
                    print(f"  ✓ {file.name} - Intentionally wrong expectations (edge case)")
    
    return result

def main():
    """Run verification on all test scenarios."""
    print("=" * 70)
    print("Test Scenario Verification")
    print("=" * 70)
    print("\nRule: Bugs should be in implementation files, NOT in test files")
    print("Exception: 'unfixable_bug' and 'no_op_patch' are intentional edge cases\n")
    
    # Create temporary directory for test repos
    with tempfile.TemporaryDirectory(prefix="verify_test_") as tmpdir:
        generator = SyntheticRepoGenerator(Path(tmpdir) / "repos")
        
        # Generate all test scenarios
        scenarios = generator.generate_all()
        
        results = []
        issues_found = False
        
        for scenario in scenarios:
            name = scenario["name"]
            print(f"\n📁 Checking: {name}")
            print("-" * 40)
            
            # Get the repo path
            repo_path = Path(scenario["path"])
            
            # Verify the scenario
            result = verify_scenario(name, repo_path)
            results.append(result)
            
            # Report status
            print(f"Status: {result['status']}")
            
            if result["issues"]:
                issues_found = True
                print("Issues found:")
                for issue in result["issues"]:
                    print(f"  ❌ {issue}")
        
        # Summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        
        # Group by status
        ok_count = sum(1 for r in results if r["status"] == "✅ OK")
        warning_count = sum(1 for r in results if "WARNING" in r["status"])
        
        print(f"\nTotal scenarios checked: {len(results)}")
        print(f"✅ Correct: {ok_count}")
        print(f"⚠️  Warnings: {warning_count}")
        
        # Special scenarios
        print("\n📌 Special Edge Cases (intentionally have wrong test expectations):")
        for name in ["unfixable_bug", "no_op_patch"]:
            scenario = next((s for s in results if s["name"] == name), None)
            if scenario:
                print(f"  • {name}: {scenario['status']}")
        
        # List scenarios with correct bug placement
        print("\n✅ Scenarios with bugs correctly in implementation:")
        for result in results:
            if result["status"] == "✅ OK" and result["name"] not in ["unfixable_bug", "no_op_patch"]:
                print(f"  • {result['name']}")
        
        if not issues_found:
            print("\n✅ All scenarios follow the correct pattern!")
            print("   Bugs are in implementation files, tests have correct expectations.")
            print("   (Except for intentional edge cases: unfixable_bug and no_op_patch)")
        else:
            print("\n⚠️ Some issues found - review the warnings above.")
        
        return 0 if not issues_found else 1

if __name__ == "__main__":
    sys.exit(main())
