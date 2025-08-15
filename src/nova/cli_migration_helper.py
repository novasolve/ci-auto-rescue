#!/usr/bin/env python3
"""
Migration helper for transitioning from separate CLI files to unified CLI.
This script helps update existing scripts and documentation.
"""

import sys
import re
from pathlib import Path
from typing import List, Tuple

def find_old_cli_usage(directory: Path) -> List[Tuple[Path, int, str]]:
    """Find instances of old CLI usage in scripts and documentation."""
    patterns = [
        r'python.*cli_enhanced\.py',
        r'nova\.cli_enhanced',
        r'from nova\.cli_enhanced import',
        r'import nova\.cli_enhanced',
    ]
    
    findings = []
    
    for pattern in patterns:
        for file_path in directory.rglob('*'):
            if file_path.is_file() and file_path.suffix in ['.py', '.sh', '.md', '.txt', '.yml', '.yaml']:
                try:
                    with open(file_path, 'r') as f:
                        for line_num, line in enumerate(f, 1):
                            if re.search(pattern, line):
                                findings.append((file_path, line_num, line.strip()))
                except Exception:
                    pass
    
    return findings


def suggest_migration(old_command: str) -> str:
    """Suggest the new command format for old CLI usage."""
    migrations = {
        'python -m nova.cli_enhanced fix': 'nova enhanced fix',
        'python src/nova/cli_enhanced.py fix': 'nova enhanced fix',
        'python cli_enhanced.py fix': 'nova enhanced fix',
        'python -m nova.cli_enhanced eval': 'nova enhanced eval',
        'python src/nova/cli_enhanced.py eval': 'nova enhanced eval',
        'python cli_enhanced.py eval': 'nova enhanced eval',
    }
    
    for old, new in migrations.items():
        if old in old_command:
            return old_command.replace(old, new)
    
    if 'cli_enhanced' in old_command:
        return old_command.replace('cli_enhanced', 'cli enhanced')
    
    return old_command


def print_migration_guide():
    """Print a comprehensive migration guide."""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                  Nova CLI Migration Guide                             ║
╚══════════════════════════════════════════════════════════════════════╝

The Nova CLI has been unified into a single entry point with subcommands.

OLD USAGE → NEW USAGE
─────────────────────────────────────────────────────────────────────
Standard Commands (unchanged):
  nova fix                    →  nova fix
  nova eval                   →  nova eval
  nova config                 →  nova config
  nova version                →  nova version

Enhanced Commands (changed):
  python -m nova.cli_enhanced fix  →  nova enhanced fix
  python cli_enhanced.py fix       →  nova enhanced fix
  python -m nova.cli_enhanced eval →  nova enhanced eval
  python cli_enhanced.py eval       →  nova enhanced eval

NEW FEATURES IN UNIFIED CLI
─────────────────────────────────────────────────────────────────────
✅ Enhanced mode now supports --config flag
✅ Shared utility functions reduce code duplication
✅ Consistent error handling across all modes
✅ Better help documentation with examples
✅ Single source of truth for version info

MIGRATION STEPS
─────────────────────────────────────────────────────────────────────
1. Update your scripts to use the new command format
2. Update CI/CD pipelines to use 'nova enhanced' subcommand
3. Remove any direct imports from cli_enhanced.py
4. Update documentation to reflect new command structure

BACKWARD COMPATIBILITY
─────────────────────────────────────────────────────────────────────
The cli_enhanced.py file is deprecated but temporarily retained.
It will be removed in the next major version.
""")


def main():
    """Main migration helper function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Nova CLI Migration Helper")
    parser.add_argument('--check', type=str, help="Directory to check for old CLI usage")
    parser.add_argument('--guide', action='store_true', help="Show migration guide")
    
    args = parser.parse_args()
    
    if args.guide or (not args.check):
        print_migration_guide()
    
    if args.check:
        directory = Path(args.check)
        if not directory.exists():
            print(f"Error: Directory {directory} does not exist")
            sys.exit(1)
        
        findings = find_old_cli_usage(directory)
        
        if findings:
            print(f"\nFound {len(findings)} instance(s) of old CLI usage:\n")
            for file_path, line_num, line in findings:
                print(f"  {file_path}:{line_num}")
                print(f"    Old: {line}")
                print(f"    New: {suggest_migration(line)}")
                print()
        else:
            print(f"\n✅ No old CLI usage found in {directory}")


if __name__ == "__main__":
    main()
