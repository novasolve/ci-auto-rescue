"""
Run Tests Tool for Nova Deep Agent
====================================

Class-based tool that combines the best of both implementations.
Uses Nova's TestRunner and Docker sandbox for safe test execution.
"""

from typing import Optional, Dict, Any, Type
from pathlib import Path
import json
import time

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from nova.runner.test_runner import TestRunner
from nova.agent.tools import run_tests as run_tests_func


class RunTestsInput(BaseModel):
    """Input schema for RunTestsTool."""
    max_failures: Optional[int] = Field(
        default=5,
        description="Maximum number of failing tests to capture"
    )


class RunTestsTool(BaseTool):
    """
    Tool to run tests and collect failing test details.
    
    Combines class-based structure with our Docker sandbox implementation.
    """
    name: str = "run_tests"
    description: str = (
        "Run the project's test suite to identify failing tests. "
        "Returns a summary with test names, locations, and error messages. "
        "Use this first and after applying patches to check progress."
    )
    args_schema: Type[BaseModel] = RunTestsInput
    
    repo_path: Path
    verbose: bool = False
    
    def __init__(self, repo_path: Path, verbose: bool = False, **kwargs):
        """Initialize the tool with repository path."""
        super().__init__(**kwargs)
        self.repo_path = Path(repo_path)
        self.verbose = verbose
    
    def _run(self, max_failures: int = 5) -> str:
        """
        Execute tests and return structured summary.
        
        Uses our Docker sandbox implementation when available.
        """
        start_time = time.time()
        
        # Try to use our Docker-based run_tests function first
        try:
            result_json = run_tests_func()
            result = json.loads(result_json)
            
            # Format output for agent consumption
            if result.get("exit_code") == 0:
                return "FAILURES: 0\nAll tests passed."
            
            # Extract failure count and details
            failures = []
            if "failing_tests" in result:
                for test in result["failing_tests"]:
                    failures.append({
                        "name": test.get("nodeid", test.get("name", "unknown")),
                        "error": test.get("message", test.get("error", ""))[:200]
                    })
            elif "test_summary" in result:
                # Use summary if detailed failures not available
                summary = result["test_summary"]
                return f"FAILURES: {summary.get('failed', 0)}\nPassed: {summary.get('passed', 0)}\nSkipped: {summary.get('skipped', 0)}"
            
            # Format failures for output
            output_lines = [f"FAILURES: {len(failures)}"]
            for i, test in enumerate(failures[:max_failures], 1):
                output_lines.append(f"{i}. {test['name']}: {test['error']}")
            
            if len(failures) > max_failures:
                output_lines.append(f"... and {len(failures) - max_failures} more")
            
            return "\n".join(output_lines)
            
        except Exception as docker_error:
            # Fallback to local TestRunner if Docker fails
            if self.verbose:
                print(f"Docker test run failed: {docker_error}, falling back to local")
            
            try:
                runner = TestRunner(self.repo_path, verbose=self.verbose)
                failing_tests, _ = runner.run_tests(max_failures=max_failures)
                
                if not failing_tests:
                    return "FAILURES: 0\nAll tests passed."
                
                output_lines = [f"FAILURES: {len(failing_tests)}"]
                for i, test in enumerate(failing_tests, 1):
                    error_line = test.short_traceback.split("\n")[0] if hasattr(test, 'short_traceback') else "Unknown error"
                    output_lines.append(f"{i}. {test.name}: {error_line[:100]}")
                
                return "\n".join(output_lines)
                
            except Exception as e:
                return f"ERROR: Test execution failed: {e}"
    
    async def _arun(self, max_failures: int = 5) -> str:
        """Async version not implemented."""
        raise NotImplementedError("RunTestsTool does not support async execution")
