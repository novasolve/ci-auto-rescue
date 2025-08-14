"""
Main entry point for nova module execution.

Allows running Nova modules with python -m nova.<module>
"""

import sys
import importlib


def main():
    """Route to appropriate module based on command line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python -m nova.<module> [args...]")
        print("Available modules:")
        print("  - github_integration: GitHub API integration for CI-Auto-Rescue")
        sys.exit(1)
    
    # Get the module name from the first argument after 'nova'
    # When called as 'python -m nova.github_integration', sys.argv[0] contains the full module path
    module_path = sys.argv[0] if sys.argv[0].endswith('.py') else None
    
    # Import and run the appropriate module
    if 'github_integration' in str(sys.argv[0]) or (len(sys.argv) > 1 and 'github_integration' in sys.argv[1]):
        from . import github_integration
        github_integration.main()
    else:
        print(f"Unknown module. Use 'python -m nova.github_integration' for GitHub integration.")
        sys.exit(1)


if __name__ == "__main__":
    main()
