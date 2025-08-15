"""
Test runner module for capturing pytest failures.
"""

import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from rich.console import Console
from nova.config import get_settings

console = Console()


@dataclass
class FailingTest:
    """Represents a failing test with its details."""
    name: str
    file: str
    line: int
    short_traceback: str
    full_traceback: Optional[str] = None
    suspect_file: Optional[str] = None
    suspect_line: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "file": self.file,
            "line": self.line,
            "short_traceback": self.short_traceback,
            "suspect_file": self.suspect_file,
            "suspect_line": self.suspect_line,
        }


class TestRunner:
    """Runs pytest and captures failing tests."""
    
    def __init__(self, repo_path: Path, verbose: bool = False):
        self.repo_path = repo_path
        self.verbose = verbose
        
    def run_tests(self, max_failures: int = 5, use_docker: bool = False) -> Tuple[List[FailingTest], Optional[str]]:
        """
        Run pytest and capture failing tests.
        
        Args:
            max_failures: Maximum number of failures to capture (default: 5)
            
        Returns:
            Tuple of (List of FailingTest objects, JUnit XML report content)
        """
        console.print("[cyan]Running pytest to identify failing tests...[/cyan]")
        
        # Create temporary files for reports
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            json_report_path = tmp.name
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as tmp:
            junit_report_path = tmp.name
        
        junit_xml_content = None
        
        try:
            # Run pytest with JSON and JUnit reports
            cmd = [
                "python", "-m", "pytest",
                str(self.repo_path),
                "--json-report",
                f"--json-report-file={json_report_path}",
                f"--junit-xml={junit_report_path}",
                "--tb=short",
                f"--maxfail={max_failures}",
                "-q",  # Quiet mode
                "--no-header",
                "--no-summary",
                "-rN",  # Don't show any summary info
            ]
            
            if self.verbose:
                console.print(f"[dim]Running: {' '.join(cmd)}[/dim]")
            
            # Run pytest (we expect it to fail if there are failing tests)
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=str(self.repo_path),
                    timeout=get_settings().test_timeout_sec  # enforce test run timeout
                )
            except subprocess.TimeoutExpired:
                console.print(f"[red]Error: Test execution timed out after {get_settings().test_timeout_sec} seconds[/red]")
                return [], None
            
            # Parse the JSON report
            failing_tests = self._parse_json_report(json_report_path, max_failures)
            
            # Read the JUnit XML report if it exists
            junit_path = Path(junit_report_path)
            if junit_path.exists():
                junit_xml_content = junit_path.read_text()
            
            if not failing_tests:
                console.print("[green]✓ No failing tests found![/green]")
                return [], junit_xml_content
            
            console.print(f"[yellow]Found {len(failing_tests)} failing test(s)[/yellow]")
            return failing_tests, junit_xml_content
            
        except FileNotFoundError:
            # pytest not installed or not found
            console.print("[red]Error: pytest not found. Please install pytest.[/red]")
            return [], None
        except Exception as e:
            console.print(f"[red]Error running tests: {e}[/red]")
            return [], None
        finally:
            # Clean up temp files
            Path(json_report_path).unlink(missing_ok=True)
            Path(junit_report_path).unlink(missing_ok=True)
    
    def _parse_json_report(self, report_path: str, max_failures: int) -> List[FailingTest]:
        """Parse pytest JSON report to extract failing tests."""
        try:
            with open(report_path, 'r') as f:
                report = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
        
        failing_tests = []
        
        # Extract failing tests from the report
        for test in report.get('tests', []):
            if test.get('outcome') in ['failed', 'error']:
                if len(failing_tests) >= max_failures:
                    break
                
                # Extract test details
                nodeid = test.get('nodeid', '')
                
                # Parse file and line from nodeid (format: path/to/test.py::TestClass::test_method)
                if '::' in nodeid:
                    file_part, test_part = nodeid.split('::', 1)
                    test_name = test_part.replace('::', '.')
                else:
                    file_part = nodeid
                    test_name = Path(nodeid).stem
                
                # Normalize the file path to be relative to repo root
                file_path = Path(file_part)
                try:
                    # Try to make file_part relative to the repo root if possible
                    # This handles absolute paths or paths that include the repo path
                    if file_path.is_absolute():
                        file_part = str(file_path.relative_to(self.repo_path))
                    else:
                        # For relative paths, check if they contain the full repo path
                        # Convert to absolute for comparison
                        abs_file = (self.repo_path / file_path).resolve()
                        if abs_file.exists():
                            file_part = str(abs_file.relative_to(self.repo_path))
                except (ValueError, Exception):
                    # If relative_to fails, try manual stripping
                    # This handles cases like "examples/demos/demo_math_ops/test_math_ops.py"
                    repo_name = self.repo_path.name
                    
                    # Find the repo name in the path and strip everything before it
                    pos = str(file_path).find(f"{repo_name}/")
                    if pos != -1:
                        # Found repo name in path, extract everything after it
                        file_part = str(file_path)[pos + len(repo_name) + 1:]
                    elif file_part.startswith(f"{repo_name}/"):
                        # Simple case: path starts with repo name
                        file_part = file_part[len(repo_name)+1:]
                    # else: leave file_part as-is if we can't normalize it
                
                # Get the traceback
                call_info = test.get('call', {})
                longrepr = call_info.get('longrepr', '')
                
                # Extract short traceback (first few lines)
                traceback_lines = longrepr.split('\n') if longrepr else []
                short_traceback = '\n'.join(traceback_lines[:3]) if traceback_lines else 'Test failed'
                
                # Try to get line number from the traceback
                line_no = 0
                for line in traceback_lines:
                    if file_part in line and ':' in line:
                        try:
                            # Extract line number from traceback line like "test.py:42"
                            parts = line.split(':')
                            for i, part in enumerate(parts):
                                if file_part in part and i + 1 < len(parts):
                                    line_no = int(parts[i + 1].split()[0])
                                    break
                        except (ValueError, IndexError):
                            pass
                
                failing_tests.append(FailingTest(
                    name=test_name,
                    file=file_part,
                    line=line_no,
                    short_traceback=short_traceback,
                    full_traceback=longrepr,
                ))
        
        return failing_tests
    
    def format_failures_table(self, failures: List[FailingTest]) -> str:
        """Format failing tests as a markdown table for the planner prompt."""
        if not failures:
            return "No failing tests found."
        
        table = "| Test Name | File:Line | Error |\n"
        table += "|-----------|-----------|-------|\n"
        
        for test in failures:
            location = f"{test.file}:{test.line}" if test.line > 0 else test.file
            # Truncate error message for table
            error = test.short_traceback.split('\n')[0][:50] + "..."
            table += f"| {test.name} | {location} | {error} |\n"
        
        return table
    
    def check_flakiness(self, failing_tests: List[FailingTest], reruns: int = 3) -> List[FailingTest]:
        """
        Check if tests are flaky by re-running them multiple times.
        
        Args:
            failing_tests: List of tests that failed
            reruns: Number of times to re-run each test (default: 3)
            
        Returns:
            List of tests that are flaky (pass on re-run)
        """
        flaky_tests = []
        
        for test in failing_tests:
            # Run the specific test multiple times
            passes = 0
            for _ in range(reruns):
                cmd = [
                    "python", "-m", "pytest",
                    f"{test.file}::{test.name}",
                    "-q", "--no-header", "--no-summary", "-rN"
                ]
                
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        cwd=str(self.repo_path),
                        timeout=get_settings().test_timeout_sec  # enforce test run timeout
                    )
                except subprocess.TimeoutExpired:
                    # If test times out during flakiness check, skip it
                    result = type('obj', (object,), {'returncode': 1})()
                
                if result.returncode == 0:
                    passes += 1
            
            # If test passes at least once, it's flaky
            if passes > 0:
                flaky_tests.append(test)
        
        return flaky_tests
    
    def run_tests_with_coverage(self) -> Optional[Dict[str, Any]]:
        """
        Run tests with coverage collection.
        
        Returns:
            Coverage data as a dictionary, or None if coverage collection fails
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            coverage_file = tmp.name
        
        try:
            # Run pytest with coverage
            cmd = [
                "python", "-m", "pytest",
                str(self.repo_path),
                "--cov=" + str(self.repo_path),
                "--cov-report=json:" + coverage_file,
                "-q", "--no-header", "--no-summary"
            ]
            
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=str(self.repo_path),
                    timeout=get_settings().test_timeout_sec  # enforce test run timeout
                )
            except subprocess.TimeoutExpired:
                if self.verbose:
                    console.print(f"[yellow]Warning: Coverage collection timed out after {get_settings().test_timeout_sec} seconds[/yellow]")
                return None
            
            # Load and return coverage data
            coverage_path = Path(coverage_file)
            if coverage_path.exists():
                with open(coverage_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            if self.verbose:
                console.print(f"[yellow]Warning: Failed to collect coverage: {e}[/yellow]")
        finally:
            # Clean up
            Path(coverage_file).unlink(missing_ok=True)
        
        return None


class FaultLocalizer:
    """Simple fault localization based on test failures and coverage."""
    
    @staticmethod
    def localize_failures(failing_tests: List[FailingTest], coverage_data: Optional[Dict[str, Any]]) -> None:
        """
        Analyze failing tests to identify suspect lines of code.
        
        Args:
            failing_tests: List of failing tests
            coverage_data: Optional coverage data from test run
        """
        for test in failing_tests:
            # Simple heuristic: parse the traceback to find the most likely error location
            if test.full_traceback:
                lines = test.full_traceback.split('\n')
                for i, line in enumerate(lines):
                    # Look for file references in traceback
                    if 'File "' in line and ', line ' in line:
                        # Extract file and line number
                        parts = line.split('"')
                        if len(parts) >= 2:
                            file_path = parts[1]
                            line_parts = line.split(', line ')
                            if len(line_parts) >= 2:
                                try:
                                    line_num = int(line_parts[1].split(',')[0])
                                    # Skip test files themselves
                                    if not file_path.startswith('test_') and not '/test_' in file_path:
                                        test.suspect_file = file_path
                                        test.suspect_line = line_num
                                        break
                                except ValueError:
                                    pass
            
            # If we have coverage data, use it to refine the localization
            if coverage_data and test.suspect_file:
                # This is a placeholder for more sophisticated fault localization
                # using coverage information
                pass
