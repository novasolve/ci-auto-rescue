#!/usr/bin/env python3
"""
fix_audit_issues.py - Automated fix script for Nova CI-Rescue Happy Path audit issues.

This script applies all the fixes identified in the Happy Path tutorial audit:
1. Fix NovaConfig -> CLIConfig import in verify_installation.py
2. Add global --version flag support in CLI
3. Align version references to 1.0.0
4. Fix timeout environment variable in GitHub Actions
5. Create troubleshooting documentation

Usage:
    python fix_audit_issues.py [--check-only]
    
Options:
    --check-only    Only check for issues without fixing them
"""

import sys
import pathlib
import re
import argparse
from typing import List, Tuple


class AuditFixer:
    """Applies fixes for Nova CI-Rescue audit issues."""
    
    def __init__(self, repo_root: pathlib.Path = None, check_only: bool = False):
        """Initialize the fixer with the repository root."""
        self.repo_root = repo_root or pathlib.Path(__file__).parent
        self.check_only = check_only
        self.issues_found = []
        self.fixes_applied = []
        
    def log(self, message: str, status: str = "INFO"):
        """Log a message with status indicator."""
        symbols = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "CHECK": "🔍",
            "FIX": "🔧"
        }
        print(f"{symbols.get(status, '•')} {message}")
    
    def check_file_exists(self, path: pathlib.Path) -> bool:
        """Check if a file exists."""
        full_path = self.repo_root / path
        if not full_path.exists():
            self.log(f"File not found: {path}", "WARNING")
            return False
        return True
    
    def fix_verify_installation_import(self) -> bool:
        """Fix NovaConfig -> CLIConfig import in verify_installation.py."""
        file_path = self.repo_root / "verify_installation.py"
        
        if not self.check_file_exists(pathlib.Path("verify_installation.py")):
            return False
            
        content = file_path.read_text()
        
        # Check if fix is needed
        if "NovaConfig" in content:
            self.issues_found.append("NovaConfig import in verify_installation.py")
            
            if not self.check_only:
                # Apply fix
                updated_content = content.replace("NovaConfig", "CLIConfig")
                file_path.write_text(updated_content)
                self.fixes_applied.append("Updated NovaConfig to CLIConfig in verify_installation.py")
                self.log("Fixed NovaConfig -> CLIConfig import", "SUCCESS")
                return True
            else:
                self.log("Found NovaConfig import that needs fixing", "CHECK")
        else:
            self.log("verify_installation.py already uses CLIConfig", "SUCCESS")
            
        return False
    
    def add_cli_version_flag(self) -> bool:
        """Add global --version flag support to CLI."""
        cli_path = self.repo_root / "src/nova/cli.py"
        
        if not self.check_file_exists(pathlib.Path("src/nova/cli.py")):
            return False
            
        content = cli_path.read_text()
        
        # Check if callback already exists
        if "@app.callback" in content:
            self.log("CLI already has callback (--version likely supported)", "SUCCESS")
            return False
            
        # Check if fix is needed
        if "--version" not in content or "version: bool = typer.Option" not in content:
            self.issues_found.append("Missing --version flag in CLI")
            
            if not self.check_only:
                # Find insertion point (after app = typer.Typer)
                app_pattern = r'(app = typer\.Typer\([^)]*\)\nconsole = Console\(\))'
                
                callback_code = '''

@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False, 
        "--version", 
        "-V", 
        help="Show Nova version and exit",
        is_eager=True
    )
):
    """
    Nova CI-Rescue: Automated test fixing agent.
    
    Main callback to handle global options like --version.
    """
    if version:
        from nova import __version__
        console.print(f"[green]Nova CI-Rescue[/green] v{__version__}")
        raise typer.Exit()
    
    # If no command is provided and not --version, show help
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        raise typer.Exit()
'''
                
                # Insert the callback after app initialization
                updated_content = re.sub(
                    app_pattern,
                    r'\1' + callback_code,
                    content
                )
                
                cli_path.write_text(updated_content)
                self.fixes_applied.append("Added global --version flag to CLI")
                self.log("Added --version flag support to CLI", "SUCCESS")
                return True
            else:
                self.log("CLI needs --version flag support", "CHECK")
        else:
            self.log("CLI already supports --version flag", "SUCCESS")
            
        return False
    
    def align_version_references(self) -> bool:
        """Align all version references to 1.0.0."""
        init_path = self.repo_root / "src/nova/__init__.py"
        version_path = self.repo_root / "VERSION"
        
        if not self.check_file_exists(pathlib.Path("src/nova/__init__.py")):
            return False
            
        init_content = init_path.read_text()
        target_version = "1.0.0"
        fixed = False
        
        # Check __init__.py version
        version_match = re.search(r"__version__\s*=\s*['\"]([^'\"]+)['\"]", init_content)
        if version_match:
            current_version = version_match.group(1)
            if current_version != target_version:
                self.issues_found.append(f"Version mismatch in __init__.py: {current_version}")
                
                if not self.check_only:
                    updated_content = re.sub(
                        r"__version__\s*=\s*['\"][^'\"]+['\"]",
                        f"__version__ = '{target_version}'",
                        init_content
                    )
                    init_path.write_text(updated_content)
                    self.fixes_applied.append(f"Updated __version__ to {target_version}")
                    self.log(f"Updated __version__ to {target_version}", "SUCCESS")
                    fixed = True
                else:
                    self.log(f"Version needs update: {current_version} -> {target_version}", "CHECK")
            else:
                self.log(f"__version__ already set to {target_version}", "SUCCESS")
        
        # Check VERSION file
        if version_path.exists():
            version_content = version_path.read_text().strip()
            if version_content != target_version:
                self.issues_found.append(f"VERSION file mismatch: {version_content}")
                
                if not self.check_only:
                    version_path.write_text(target_version)
                    self.fixes_applied.append(f"Updated VERSION file to {target_version}")
                    self.log(f"Updated VERSION file to {target_version}", "SUCCESS")
                    fixed = True
                else:
                    self.log(f"VERSION file needs update: {version_content} -> {target_version}", "CHECK")
            else:
                self.log(f"VERSION file already set to {target_version}", "SUCCESS")
                
        return fixed
    
    def fix_github_action_timeout(self) -> bool:
        """Fix timeout environment variable in GitHub Actions."""
        workflow_path = self.repo_root / ".github/workflows/nova.yml"
        
        if not workflow_path.exists():
            self.log("GitHub workflow nova.yml not found", "WARNING")
            return False
            
        content = workflow_path.read_text()
        
        # Check if fix is needed
        if "NOVA_TIMEOUT=" in content and "NOVA_RUN_TIMEOUT_SEC=" not in content:
            self.issues_found.append("Incorrect timeout env var in GitHub Actions")
            
            if not self.check_only:
                updated_content = content.replace(
                    "NOVA_TIMEOUT=",
                    "NOVA_RUN_TIMEOUT_SEC="
                )
                workflow_path.write_text(updated_content)
                self.fixes_applied.append("Fixed timeout env var in GitHub Actions")
                self.log("Fixed NOVA_TIMEOUT -> NOVA_RUN_TIMEOUT_SEC", "SUCCESS")
                return True
            else:
                self.log("GitHub Actions uses wrong timeout env var", "CHECK")
        else:
            self.log("GitHub Actions timeout configuration is correct", "SUCCESS")
            
        return False
    
    def create_troubleshooting_guide(self) -> bool:
        """Create or update troubleshooting documentation."""
        docs_dir = self.repo_root / "docs"
        troubleshoot_path = docs_dir / "troubleshooting.md"
        
        if troubleshoot_path.exists():
            self.log("Troubleshooting guide already exists", "SUCCESS")
            return False
            
        self.issues_found.append("Missing troubleshooting documentation")
        
        if not self.check_only:
            # Ensure docs directory exists
            docs_dir.mkdir(parents=True, exist_ok=True)
            
            # Create a basic troubleshooting guide
            content = """# Nova CI-Rescue Troubleshooting Guide

This guide helps resolve common issues when using Nova CI-Rescue.

## Common Issues

### Missing API Keys
**Problem:** Nova fails with API key error.  
**Solution:** Set your API keys via environment variables:
```bash
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"  # Optional
```

### Timeout Issues
**Problem:** Nova times out before completing.  
**Solution:** Increase the timeout:
```bash
nova fix . --timeout 1800  # 30 minutes
```

### Import Errors
**Problem:** Import errors with NovaConfig or CLIConfig.  
**Solution:** Reinstall the package:
```bash
pip uninstall nova-ci-rescue
pip install -e .
```

### Version Command Not Working
**Problem:** `nova --version` doesn't work.  
**Solution:** Update to version 1.0.0 or later.

## Getting Help

For more issues, please check:
- [GitHub Issues](https://github.com/your-org/nova-ci-rescue/issues)
- [Documentation](https://github.com/your-org/nova-ci-rescue/docs)
"""
            
            troubleshoot_path.write_text(content)
            self.fixes_applied.append("Created troubleshooting.md")
            self.log("Created troubleshooting documentation", "SUCCESS")
            return True
        else:
            self.log("Troubleshooting guide needs to be created", "CHECK")
            
        return False
    
    def run(self) -> Tuple[int, int]:
        """Run all fixes and return counts of issues and fixes."""
        self.log("Nova CI-Rescue Audit Fixer", "INFO")
        self.log("=" * 50, "INFO")
        
        if self.check_only:
            self.log("Running in CHECK-ONLY mode", "INFO")
        else:
            self.log("Applying fixes...", "INFO")
        
        print()
        
        # Run all fixes
        self.log("Checking verify_installation.py...", "CHECK")
        self.fix_verify_installation_import()
        
        print()
        self.log("Checking CLI version flag...", "CHECK")
        self.add_cli_version_flag()
        
        print()
        self.log("Checking version alignment...", "CHECK")
        self.align_version_references()
        
        print()
        self.log("Checking GitHub Actions...", "CHECK")
        self.fix_github_action_timeout()
        
        print()
        self.log("Checking troubleshooting docs...", "CHECK")
        self.create_troubleshooting_guide()
        
        return len(self.issues_found), len(self.fixes_applied)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Fix Nova CI-Rescue Happy Path audit issues"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check for issues without fixing them"
    )
    parser.add_argument(
        "--repo-root",
        type=pathlib.Path,
        help="Repository root directory (default: current directory)"
    )
    
    args = parser.parse_args()
    
    # Run the fixer
    fixer = AuditFixer(
        repo_root=args.repo_root,
        check_only=args.check_only
    )
    
    issues_count, fixes_count = fixer.run()
    
    # Print summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    
    if args.check_only:
        if issues_count > 0:
            print(f"❌ Found {issues_count} issue(s) that need fixing:")
            for issue in fixer.issues_found:
                print(f"   • {issue}")
            print(f"\nRun without --check-only to apply fixes.")
            sys.exit(1)
        else:
            print("✅ No issues found! All checks passed.")
            sys.exit(0)
    else:
        if fixes_count > 0:
            print(f"✅ Applied {fixes_count} fix(es):")
            for fix in fixer.fixes_applied:
                print(f"   • {fix}")
            print(f"\n✨ All fixes applied successfully!")
        else:
            print("✅ No fixes needed! Everything is already up to date.")
        sys.exit(0)


if __name__ == "__main__":
    main()