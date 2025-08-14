#!/usr/bin/env python3
"""
Verification script for Milestone B: Quiet CI & Telemetry.

This script verifies that:
1. The package can be installed in a fresh venv
2. The nova CLI runs without errors or warnings
3. All required dependencies are properly specified
"""

import subprocess
import sys
import tempfile
import shutil
from pathlib import Path
import json


def run_command(cmd: list[str], cwd: Path = None, capture_output: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(
        cmd, 
        cwd=cwd, 
        capture_output=capture_output, 
        text=True,
        shell=False
    )
    return result


def verify_milestone_b():
    """Main verification function."""
    print("=" * 60)
    print("Milestone B: Quiet CI & Telemetry - Verification")
    print("=" * 60)
    
    # Get the project root
    project_root = Path(__file__).parent.absolute()
    print(f"Project root: {project_root}")
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory(prefix="nova_test_") as tmpdir:
        test_dir = Path(tmpdir)
        print(f"\nTest directory: {test_dir}")
        
        # Step 1: Create a fresh virtual environment
        print("\n1. Creating fresh virtual environment...")
        venv_dir = test_dir / "venv"
        result = run_command([sys.executable, "-m", "venv", str(venv_dir)])
        if result.returncode != 0:
            print(f"❌ Failed to create venv: {result.stderr}")
            return False
        print("✅ Virtual environment created")
        
        # Determine the pip and python paths in the venv
        if sys.platform == "win32":
            pip_path = venv_dir / "Scripts" / "pip"
            python_path = venv_dir / "Scripts" / "python"
        else:
            pip_path = venv_dir / "bin" / "pip"
            python_path = venv_dir / "bin" / "python"
        
        # Step 2: Install the package in editable mode
        print("\n2. Installing nova-ci-rescue with pip install -e ...")
        result = run_command([str(pip_path), "install", "-e", str(project_root)])
        if result.returncode != 0:
            print(f"❌ Installation failed: {result.stderr}")
            return False
        print("✅ Package installed successfully")
        
        # Step 3: Verify nova CLI is available
        print("\n3. Verifying nova CLI is available...")
        nova_path = venv_dir / "bin" / "nova" if sys.platform != "win32" else venv_dir / "Scripts" / "nova"
        if not nova_path.exists():
            # Try using python -m nova.cli instead
            print("   Nova binary not found, trying python -m...")
            result = run_command([str(python_path), "-m", "nova.cli", "--help"])
        else:
            result = run_command([str(nova_path), "--help"])
        
        if result.returncode != 0:
            print(f"❌ nova --help failed: {result.stderr}")
            return False
        
        # Check for warnings in output
        if "warning" in result.stderr.lower() or "warning" in result.stdout.lower():
            print(f"⚠️  Warnings detected in output:")
            if result.stderr:
                print(f"   stderr: {result.stderr}")
            if "warning" in result.stdout.lower():
                print(f"   stdout contains warnings")
            return False
        
        print("✅ nova --help runs without errors or warnings")
        
        # Step 4: Verify key commands are available
        print("\n4. Verifying nova commands...")
        commands_to_check = ["fix", "eval", "version"]
        for cmd in commands_to_check:
            if nova_path.exists():
                result = run_command([str(nova_path), cmd, "--help"])
            else:
                result = run_command([str(python_path), "-m", "nova.cli", cmd, "--help"])
            
            if result.returncode != 0:
                print(f"❌ nova {cmd} --help failed")
                return False
            print(f"✅ nova {cmd} command available")
        
        # Step 5: Verify dependencies
        print("\n5. Verifying key dependencies...")
        result = run_command([str(pip_path), "list", "--format=json"])
        if result.returncode == 0:
            try:
                installed_packages = json.loads(result.stdout)
                package_dict = {p["name"].lower(): p["version"] for p in installed_packages}
                
                required_packages = [
                    "typer",
                    "pytest",
                    "pytest-json-report",
                    "langgraph",
                    "langchain",
                    "pydantic",
                    "unidiff",
                    "httpx",
                    "python-dotenv",
                    "rich",
                    "pyyaml"
                ]
                
                for pkg in required_packages:
                    if pkg.lower() in package_dict:
                        print(f"✅ {pkg}: {package_dict[pkg.lower()]}")
                    else:
                        print(f"❌ {pkg}: NOT FOUND")
                        return False
                        
            except json.JSONDecodeError:
                print("⚠️  Could not parse pip list output")
        
        # Step 6: Test importing the nova module
        print("\n6. Testing nova module imports...")
        test_script = test_dir / "test_import.py"
        test_script.write_text("""
import sys
try:
    from nova import __version__
    from nova.cli import app
    from nova.config import NovaSettings
    from nova.telemetry import JSONLLogger
    from nova.agent import AgentState
    from nova.runner import TestRunner
    print("All imports successful")
    sys.exit(0)
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)
""")
        result = run_command([str(python_path), str(test_script)])
        if result.returncode != 0:
            print(f"❌ Import test failed: {result.stdout}")
            return False
        print("✅ All module imports successful")
        
    print("\n" + "=" * 60)
    print("✅ MILESTONE B VERIFICATION: ALL CHECKS PASSED")
    print("=" * 60)
    print("\nAcceptance Criteria Met:")
    print("✓ Fresh venv installation works with pip install -e .")
    print("✓ nova --help runs without errors or warnings")
    print("✓ All required dependencies are installed")
    print("✓ Nova module can be imported successfully")
    
    return True


if __name__ == "__main__":
    success = verify_milestone_b()
    sys.exit(0 if success else 1)
