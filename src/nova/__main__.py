"""
Main entry point for nova module execution.

Runs the Nova CI-Rescue CLI when invoked with python -m nova
"""

from nova.cli import app


if __name__ == "__main__":
    app()
