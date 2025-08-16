#!/usr/bin/env python3
"""
Cross-platform environment setup for Nova CI-Rescue regression tests
Sets up isolated environments for v1.0 and v1.1
"""

import os
import sys
import subprocess
import shutil
import venv
from pathlib import Path
import platform
import json


class EnvironmentSetup:
    """Setup regression test environments"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent
        self.venv_dir = self.base_dir / "venvs"
        self.requirements_dir = self.base_dir / "requirements"
        self.test_repos_dir = self.base_dir / "test_repos"
        self.results_dir = self.base_dir / "regression_results"
        
        # Detect platform
        self.is_windows = platform.system() == "Windows"
        self.python_exe = sys.executable
        
    def setup_all(self):
        """Run complete setup process"""
        print("=" * 60)
        print("Nova CI-Rescue Regression Test Environment Setup")
        print("=" * 60)
        print(f"Python: {sys.version}")
        print(f"Platform: {platform.system()}")
        print(f"Base directory: {self.base_dir}")
        print()
        
        # Check Python version
        if sys.version_info < (3, 8):
            print("ERROR: Python 3.8+ required")
            sys.exit(1)
            
        # Create directory structure
        self.create_directories()
        
        # Create requirements files
        self.create_requirements()
        
        # Setup environments
        self.setup_nova_env("v1_0", "nova_v1_0", "nova_v1_0.txt")
        self.setup_nova_env("v1_1", "nova_v1_1", "nova_v1_1.txt")
        
        # Generate test repositories
        self.generate_test_repos()
        
        # Create run scripts
        self.create_run_scripts()
        
        # Print summary
        self.print_summary()
        
    def create_directories(self):
        """Create necessary directories"""
        print("Creating directory structure...")
        
        for directory in [self.venv_dir, self.requirements_dir, 
                         self.test_repos_dir, self.results_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            
        print("✓ Directories created")
        
    def create_requirements(self):
        """Create requirements files for each version"""
        print("\nCreating requirements files...")
        
        # v1.0 requirements
        v1_0_reqs = """# Nova v1.0 (Legacy) Requirements
pytest>=7.0.0
pytest-timeout>=2.1.0
pytest-json-report>=1.5.0
pyyaml>=6.0
gitpython>=3.1.0
click>=8.0.0
rich>=13.0.0
openai>=1.0.0
anthropic>=0.5.0
tenacity>=8.0.0
jsonschema>=4.0.0
matplotlib>=3.5.0
numpy>=1.21.0
"""
        
        # v1.1 requirements
        v1_1_reqs = """# Nova v1.1 (Deep Agent) Requirements
pytest>=7.0.0
pytest-timeout>=2.1.0
pytest-json-report>=1.5.0
pyyaml>=6.0
gitpython>=3.1.0
click>=8.0.0
rich>=13.0.0
openai>=1.0.0
anthropic>=0.5.0
tenacity>=8.0.0
jsonschema>=4.0.0
pydantic>=2.0.0
matplotlib>=3.5.0
numpy>=1.21.0
"""
        
        # Write requirements files
        (self.requirements_dir / "nova_v1_0.txt").write_text(v1_0_reqs)
        (self.requirements_dir / "nova_v1_1.txt").write_text(v1_1_reqs)
        
        print("✓ Requirements files created")
        
    def setup_nova_env(self, version: str, venv_name: str, requirements_file: str):
        """Setup a Nova environment"""
        print(f"\nSetting up Nova {version} environment...")
        
        venv_path = self.venv_dir / venv_name
        
        # Remove existing venv if it exists
        if venv_path.exists():
            print(f"Removing existing {venv_name}...")
            shutil.rmtree(venv_path)
            
        # Create virtual environment
        print(f"Creating virtual environment: {venv_name}")
        venv.create(venv_path, with_pip=True)
        
        # Get pip path
        if self.is_windows:
            pip_path = venv_path / "Scripts" / "pip.exe"
            python_path = venv_path / "Scripts" / "python.exe"
        else:
            pip_path = venv_path / "bin" / "pip"
            python_path = venv_path / "bin" / "python"
            
        # Upgrade pip
        print("Upgrading pip...")
        subprocess.run([str(python_path), "-m", "pip", "install", "--upgrade", "pip"], 
                      capture_output=True)
        
        # Install requirements
        req_file = self.requirements_dir / requirements_file
        if req_file.exists():
            print(f"Installing requirements from {requirements_file}...")
            subprocess.run([str(pip_path), "install", "-r", str(req_file)], 
                          capture_output=True)
        
        # Install Nova source
        nova_source = self._find_nova_source(version)
        if nova_source:
            print(f"Installing Nova from {nova_source}")
            subprocess.run([str(pip_path), "install", "-e", str(nova_source)], 
                          capture_output=True)
        else:
            print(f"⚠️ Warning: Nova {version} source not found")
            
        # Create wrapper script
        self._create_wrapper_script(version, venv_path)
        
        print(f"✓ Nova {version} environment setup complete")
        
    def _find_nova_source(self, version: str) -> Path:
        """Find Nova source directory for version"""
        if version == "v1_0":
            # Look for v1.0 release
            release_path = self.base_dir.parent / "releases" / "v0.1.0-alpha"
            if release_path.exists():
                return release_path
        elif version == "v1_1":
            # Use current source
            src_path = self.base_dir.parent / "src"
            if src_path.exists():
                return self.base_dir.parent
                
        return None
        
    def _create_wrapper_script(self, version: str, venv_path: Path):
        """Create wrapper script for Nova version"""
        if self.is_windows:
            wrapper_path = self.base_dir / f"nova_{version}.bat"
            python_path = venv_path / "Scripts" / "python.exe"
            
            wrapper_content = f"""@echo off
set NOVA_VERSION={version}
set NOVA_LOG_LEVEL=INFO
"""
            
            if version == "v1_1":
                wrapper_content += "set NOVA_USE_DEEP_AGENT=true\n"
                
            wrapper_content += f'"{python_path}" -m nova %*\n'
            
        else:
            wrapper_path = self.base_dir / f"nova_{version}"
            python_path = venv_path / "bin" / "python"
            
            wrapper_content = f"""#!/bin/bash
source "{venv_path}/bin/activate"
export NOVA_VERSION="{version}"
export NOVA_LOG_LEVEL="INFO"
"""
            
            if version == "v1_1":
                wrapper_content += 'export NOVA_USE_DEEP_AGENT="true"\n'
                
            wrapper_content += 'python -m nova "$@"\n'
            
        wrapper_path.write_text(wrapper_content)
        
        if not self.is_windows:
            wrapper_path.chmod(0o755)
            
    def generate_test_repos(self):
        """Generate test repositories"""
        print("\nGenerating test repositories...")
        
        # Import and run edge case generator
        sys.path.insert(0, str(self.base_dir))
        from edge_case_generator import EdgeCaseGenerator
        
        generator = EdgeCaseGenerator(str(self.test_repos_dir))
        generator.generate_all_edge_cases()
        
        print("✓ Test repositories generated")
        
    def create_run_scripts(self):
        """Create run scripts for testing"""
        print("\nCreating run scripts...")
        
        if self.is_windows:
            # Windows batch script
            run_script = self.base_dir / "run_regression_tests.bat"
            run_content = f"""@echo off
set CONFIG_FILE=%1
if "%CONFIG_FILE%"=="" set CONFIG_FILE={self.base_dir}\\test_repos.yaml

echo Starting regression tests with config: %CONFIG_FILE%
python "{self.base_dir}\\regression_orchestrator.py" "%CONFIG_FILE%" --output "{self.results_dir}" --verbose

if %ERRORLEVEL% EQU 0 (
    echo Regression tests completed successfully
    echo Results available in: {self.results_dir}
) else (
    echo Regression tests failed or found regressions
    echo Check results in: {self.results_dir}
    exit /b 1
)
"""
        else:
            # Unix shell script
            run_script = self.base_dir / "run_regression_tests.sh"
            run_content = f"""#!/bin/bash
CONFIG_FILE="${{1:-{self.base_dir}/test_repos.yaml}}"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Configuration file not found: $CONFIG_FILE"
    echo "Usage: $0 [config_file]"
    exit 1
fi

echo "Starting regression tests with config: $CONFIG_FILE"
python3 "{self.base_dir}/regression_orchestrator.py" "$CONFIG_FILE" \\
    --output "{self.results_dir}" \\
    --verbose

if [ $? -eq 0 ]; then
    echo -e "\\033[0;32m✓ Regression tests completed successfully\\033[0m"
    echo "Results available in: {self.results_dir}/"
else
    echo -e "\\033[0;31m✗ Regression tests failed or found regressions\\033[0m"
    echo "Check results in: {self.results_dir}/"
    exit 1
fi
"""
            run_script.chmod(0o755)
            
        run_script.write_text(run_content)
        
        # Create Python run script for cross-platform
        py_run_script = self.base_dir / "run_tests.py"
        py_run_content = f"""#!/usr/bin/env python3
import sys
import subprocess
from pathlib import Path

config_file = sys.argv[1] if len(sys.argv) > 1 else "{self.base_dir}/test_repos.yaml"

print(f"Starting regression tests with config: {{config_file}}")

result = subprocess.run([
    sys.executable,
    "{self.base_dir}/regression_orchestrator.py",
    config_file,
    "--output", "{self.results_dir}",
    "--verbose"
])

if result.returncode == 0:
    print("✓ Regression tests completed successfully")
    print(f"Results available in: {self.results_dir}/")
else:
    print("✗ Regression tests failed or found regressions")
    print(f"Check results in: {self.results_dir}/")
    sys.exit(1)
"""
        py_run_script.write_text(py_run_content)
        
        if not self.is_windows:
            py_run_script.chmod(0o755)
            
        print("✓ Run scripts created")
        
    def print_summary(self):
        """Print setup summary"""
        print("\n" + "=" * 60)
        print("Environment Setup Complete!")
        print("=" * 60)
        print("\nCreated:")
        print(f"  - Virtual environments in: {self.venv_dir}/")
        print("  - Wrapper scripts:")
        print(f"    - nova_v1_0 (for v1.0 legacy)")
        print(f"    - nova_v1_1 (for v1.1 Deep Agent)")
        print(f"  - Test repositories in: {self.test_repos_dir}/")
        print(f"  - Run scripts:")
        
        if self.is_windows:
            print(f"    - run_regression_tests.bat")
        else:
            print(f"    - run_regression_tests.sh")
            
        print(f"    - run_tests.py (cross-platform)")
        
        print("\nTo run regression tests:")
        
        if self.is_windows:
            print("  run_regression_tests.bat")
            print("\nOr:")
        else:
            print("  ./run_regression_tests.sh")
            print("\nOr:")
            
        print("  python run_tests.py")
        
        print("\nTo run with custom config:")
        print("  python run_tests.py /path/to/config.yaml")
        
        print("\n⚠️ Note: Set OPENAI_API_KEY or other LLM API keys before running tests")
        
    def check_dependencies(self):
        """Check if required dependencies are available"""
        print("Checking dependencies...")
        
        missing = []
        
        # Check Python version
        if sys.version_info < (3, 8):
            missing.append("Python 3.8+")
            
        # Check git
        try:
            subprocess.run(["git", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing.append("git")
            
        # Check pip
        try:
            subprocess.run([sys.executable, "-m", "pip", "--version"], 
                          capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing.append("pip")
            
        if missing:
            print("❌ Missing dependencies:")
            for dep in missing:
                print(f"  - {dep}")
            return False
            
        print("✓ All dependencies satisfied")
        return True


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Setup Nova CI-Rescue regression test environments"
    )
    parser.add_argument(
        "--base-dir",
        help="Base directory for setup (default: current directory)",
        default=None
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check dependencies, don't setup"
    )
    
    args = parser.parse_args()
    
    setup = EnvironmentSetup(args.base_dir)
    
    if args.check_only:
        if setup.check_dependencies():
            print("\n✓ Ready to setup environments")
            sys.exit(0)
        else:
            print("\n❌ Please install missing dependencies first")
            sys.exit(1)
    else:
        if not setup.check_dependencies():
            print("\n❌ Cannot proceed without required dependencies")
            sys.exit(1)
            
        setup.setup_all()


if __name__ == "__main__":
    main()
