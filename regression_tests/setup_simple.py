#!/usr/bin/env python3
"""
Simplified setup script for Nova CI-Rescue regression tests
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd, description=None):
    """Run a command and print output"""
    if description:
        print(f"\n{description}...")
    
    print(f"  Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False, text=True)
    
    if result.returncode != 0:
        print(f"  ⚠️ Command failed with exit code {result.returncode}")
        return False
    
    print(f"  ✓ Success")
    return True

def main():
    print("=" * 60)
    print("Nova CI-Rescue Regression Test Setup (Simplified)")
    print("=" * 60)
    
    base_dir = Path(__file__).parent
    os.chdir(base_dir)
    
    # 1. Create directories
    print("\n1. Creating directories...")
    dirs = ["venvs", "test_repos", "regression_results", "requirements"]
    for d in dirs:
        Path(d).mkdir(exist_ok=True)
        print(f"  ✓ Created {d}/")
    
    # 2. Create requirements files
    print("\n2. Creating requirements files...")
    
    # Base requirements for both versions
    base_reqs = """pytest>=7.0.0
pytest-timeout>=2.1.0
pytest-json-report>=1.5.0
pyyaml>=6.0
matplotlib>=3.5.0
numpy>=1.21.0
"""
    
    Path("requirements/base.txt").write_text(base_reqs)
    print("  ✓ Created requirements/base.txt")
    
    # 3. Setup v1.0 environment
    print("\n3. Setting up Nova v1.0 environment...")
    venv_v1_0 = Path("venvs/nova_v1_0")
    
    # Create venv
    if venv_v1_0.exists():
        import shutil
        shutil.rmtree(venv_v1_0)
    
    if not run_command([sys.executable, "-m", "venv", str(venv_v1_0)], 
                      "Creating v1.0 virtual environment"):
        return 1
    
    # Get python path
    if sys.platform == "win32":
        python_v1_0 = venv_v1_0 / "Scripts" / "python.exe"
    else:
        python_v1_0 = venv_v1_0 / "bin" / "python"
    
    # Install requirements
    run_command([str(python_v1_0), "-m", "pip", "install", "--upgrade", "pip"],
                "Upgrading pip for v1.0")
    run_command([str(python_v1_0), "-m", "pip", "install", "-r", "requirements/base.txt"],
                "Installing requirements for v1.0")
    
    # 4. Setup v1.1 environment
    print("\n4. Setting up Nova v1.1 environment...")
    venv_v1_1 = Path("venvs/nova_v1_1")
    
    # Create venv
    if venv_v1_1.exists():
        import shutil
        shutil.rmtree(venv_v1_1)
    
    if not run_command([sys.executable, "-m", "venv", str(venv_v1_1)],
                      "Creating v1.1 virtual environment"):
        return 1
    
    # Get python path
    if sys.platform == "win32":
        python_v1_1 = venv_v1_1 / "Scripts" / "python.exe"
    else:
        python_v1_1 = venv_v1_1 / "bin" / "python"
    
    # Install requirements
    run_command([str(python_v1_1), "-m", "pip", "install", "--upgrade", "pip"],
                "Upgrading pip for v1.1")
    run_command([str(python_v1_1), "-m", "pip", "install", "-r", "requirements/base.txt"],
                "Installing requirements for v1.1")
    
    # 5. Create wrapper scripts
    print("\n5. Creating wrapper scripts...")
    
    # v1.0 wrapper
    wrapper_v1_0 = Path("nova_v1_0")
    wrapper_v1_0.write_text(f"""#!/bin/bash
export NOVA_VERSION="v1_0"
"{python_v1_0}" -m nova "$@"
""")
    wrapper_v1_0.chmod(0o755)
    print("  ✓ Created nova_v1_0 wrapper")
    
    # v1.1 wrapper
    wrapper_v1_1 = Path("nova_v1_1")
    wrapper_v1_1.write_text(f"""#!/bin/bash
export NOVA_VERSION="v1_1"
export NOVA_USE_DEEP_AGENT="true"
"{python_v1_1}" -m nova "$@"
""")
    wrapper_v1_1.chmod(0o755)
    print("  ✓ Created nova_v1_1 wrapper")
    
    # 6. Generate test repositories
    print("\n6. Generating test repositories...")
    result = subprocess.run([sys.executable, "edge_case_generator.py"], 
                          capture_output=True, text=True)
    if result.returncode == 0:
        print("  ✓ Test repositories generated")
    else:
        print("  ⚠️ Failed to generate test repositories")
        print(f"    Error: {result.stderr}")
    
    # 7. Create run script
    print("\n7. Creating run script...")
    run_script = Path("run_tests.sh")
    run_script.write_text("""#!/bin/bash
CONFIG="${1:-test_repos.yaml}"
echo "Running regression tests with config: $CONFIG"
python regression_orchestrator.py "$CONFIG" --output regression_results --verbose
""")
    run_script.chmod(0o755)
    print("  ✓ Created run_tests.sh")
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ Setup Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Set your API key:")
    print("   export OPENAI_API_KEY='your-key'")
    print("\n2. Run the tests:")
    print("   ./run_tests.sh")
    print("\n3. Validate results:")
    print("   python validate_results.py regression_results/*/regression_results.json")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
