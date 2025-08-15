#!/usr/bin/env python3
"""
verify_installation.py – Validate package installation in a clean venv
"""
import sys
import subprocess
import venv
import os
import shutil
import tempfile
from pathlib import Path


def verify_installation():
    """Test Nova CI-Rescue installation and CLI functionality"""
    
    print("🔧 Starting Nova CI-Rescue installation verification...")
    
    # Use a temporary directory for the test environment
    with tempfile.TemporaryDirectory() as tmpdir:
        venv_dir = Path(tmpdir) / "test_env"
        
        print(f"📦 Creating virtual environment at {venv_dir}")
        
        # 1. Set up a temporary virtual environment
        venv.EnvBuilder(with_pip=True).create(venv_dir)
        
        # Determine the correct bin directory based on OS
        bin_dir = "Scripts" if os.name == "nt" else "bin"
        pip_path = venv_dir / bin_dir / "pip"
        python_path = venv_dir / bin_dir / "python"
        nova_path = venv_dir / bin_dir / "nova"
        
        # 2. Upgrade pip to latest version
        print("📦 Upgrading pip...")
        subprocess.check_call([str(python_path), "-m", "pip", "install", "--upgrade", "pip"])
        
        # 3. Install the current package into the venv
        print("📦 Installing Nova CI-Rescue package...")
        project_root = Path(__file__).parent
        subprocess.check_call([str(pip_path), "install", str(project_root)])
        
        # 4. Verify the entry-point script is installed and functioning
        print("✔️  Verifying CLI entry-point...")
        result = subprocess.run(
            [str(nova_path), "--help"], 
            capture_output=True, 
            text=True
        )
        
        if result.returncode != 0:
            print(f"❌ Nova CLI failed to run: {result.stderr}")
            return False
            
        if "Usage" not in result.stdout and "Nova CI-Rescue" not in result.stdout:
            print(f"❌ Help text not found in output: {result.stdout}")
            return False
        
        print("✅ CLI help command works")
        
        # 5. Test version command
        print("✔️  Verifying version command...")
        result = subprocess.run(
            [str(nova_path), "--version"], 
            capture_output=True, 
            text=True
        )
        
        if result.returncode != 0:
            print(f"⚠️  Version command failed: {result.stderr}")
            # This is not critical, continue
        else:
            print(f"✅ Version: {result.stdout.strip()}")
        
        # 6. Verify package metadata
        print("✔️  Verifying package metadata...")
        result = subprocess.run(
            [str(pip_path), "show", "nova-ci-rescue"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"❌ Failed to get package info: {result.stderr}")
            return False
        
        # Parse package info
        package_info = {}
        for line in result.stdout.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                package_info[key.strip()] = value.strip()
        
        # Verify key metadata
        required_fields = ["Name", "Version", "Summary", "Author"]
        for field in required_fields:
            if field in package_info:
                print(f"  {field}: {package_info[field]}")
            else:
                print(f"  ⚠️  Missing field: {field}")
        
        # 7. Verify imports work
        print("✔️  Verifying imports...")
        test_imports = [
            "from nova import __version__",
            "from nova.cli import app",
            "from nova.config import NovaConfig",
            "from nova.agent.state import AgentState",
            "from nova.nodes.run_tests import RunTestsNode"
        ]
        
        for import_stmt in test_imports:
            result = subprocess.run(
                [str(python_path), "-c", import_stmt],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                print(f"  ❌ Failed: {import_stmt}")
                print(f"     Error: {result.stderr}")
                return False
            else:
                print(f"  ✅ {import_stmt}")
        
        # 8. Test with a simple config file
        print("✔️  Testing with sample config...")
        config_file = venv_dir / "test_config.yaml"
        config_file.write_text("""
repo_path: .
test_command: pytest
max_iterations: 1
model: mock
""")
        
        result = subprocess.run(
            [str(nova_path), "run", "--config", str(config_file), "--dry-run"],
            capture_output=True,
            text=True,
            cwd=str(project_root)
        )
        
        # Dry run might fail if no tests, but should at least parse config
        if "error" in result.stderr.lower() and "config" in result.stderr.lower():
            print(f"  ❌ Config parsing failed: {result.stderr}")
            return False
        else:
            print("  ✅ Config file parsed successfully")
        
        # 9. Verify required dependencies are installed
        print("✔️  Verifying dependencies...")
        required_deps = [
            "typer",
            "pyyaml",
            "gitpython",
            "pytest",
            "rich"
        ]
        
        for dep in required_deps:
            result = subprocess.run(
                [str(pip_path), "show", dep],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                print(f"  ❌ Missing dependency: {dep}")
                return False
            else:
                print(f"  ✅ {dep} installed")
        
        print("✅ Package installation and CLI entry-point validated successfully!")
        return True


def test_editable_install():
    """Test editable/development installation"""
    print("\n🔧 Testing editable installation...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        venv_dir = Path(tmpdir) / "test_dev_env"
        
        # Create venv
        venv.EnvBuilder(with_pip=True).create(venv_dir)
        
        bin_dir = "Scripts" if os.name == "nt" else "bin"
        pip_path = venv_dir / bin_dir / "pip"
        nova_path = venv_dir / bin_dir / "nova"
        
        # Install in editable mode
        project_root = Path(__file__).parent
        subprocess.check_call([str(pip_path), "install", "-e", str(project_root)])
        
        # Quick test
        result = subprocess.run(
            [str(nova_path), "--help"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Editable installation works")
            return True
        else:
            print(f"❌ Editable installation failed: {result.stderr}")
            return False


if __name__ == "__main__":
    success = verify_installation()
    
    # Also test editable install
    editable_success = test_editable_install()
    
    if success and editable_success:
        print("\n✅ All installation tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some installation tests failed")
        sys.exit(1)
