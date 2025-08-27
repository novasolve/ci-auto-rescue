"""
Test runner module for capturing pytest failures.
"""

import json
import re
import subprocess
import tempfile
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from rich.console import Console
import xml.etree.ElementTree as ET

console = Console()


@dataclass
class FailingTest:
    """Represents a failing test with its details."""
    name: str
    file: str
    line: int
    short_traceback: str
    full_traceback: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "file": self.file,
            "line": self.line,
            "short_traceback": self.short_traceback,
        }


class TestRunner:
    """Runs pytest and captures failing tests."""
    
    def __init__(self, repo_path: Path, verbose: bool = False, pytest_args: Optional[str] = None):
        self.repo_path = repo_path
        self.verbose = verbose
        self.pytest_args = pytest_args
        
    def run_tests(self) -> Tuple[List[FailingTest], Optional[str]]:
        """
        Run pytest and capture all failing tests.
            
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
            # Run pytest with JSON and JUnit reports (use correct --junitxml flag)
            cmd = [
                "python", "-m", "pytest",
                "--json-report",
                f"--json-report-file={json_report_path}",
                f"--junitxml={junit_report_path}",
                "--tb=short",
                "-q",  # Quiet mode
                "--no-header",
                "--no-summary",
                "-rN",  # Don't show any summary info
            ]
            
            # Append any user-provided pytest args (e.g., -k filters)
            if self.pytest_args:
                try:
                    extra_args = shlex.split(self.pytest_args)
                    cmd.extend(extra_args)
                except ValueError:
                    # Fallback to raw append if splitting fails
                    cmd.append(self.pytest_args)
            
            if self.verbose:
                console.print(f"[dim]Running: {' '.join(cmd)}[/dim]")
            
            # Run pytest (we expect it to fail if there are failing tests)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.repo_path),
                timeout=120,
            )

            # If the pytest-json-report plugin is missing, rerun without json flags so JUnit is produced
            combined_output = (result.stderr or '') + '\n' + (result.stdout or '')
            if 'unrecognized arguments: --json-report' in combined_output:
                cmd_no_json = [
                    arg for arg in cmd
                    if not (arg == '--json-report' or arg.startswith('--json-report-file='))
                ]
                if self.verbose:
                    console.print(f"[dim]Re-running without json-report: {' '.join(cmd_no_json)}[/dim]")
                result = subprocess.run(
                    cmd_no_json,
                    capture_output=True,
                    text=True,
                    cwd=str(self.repo_path),
                    timeout=120,
                )
                combined_output = (result.stderr or '') + '\n' + (result.stdout or '')
            
            # Parse the JSON report
            failing_tests = self._parse_json_report(json_report_path)
            
            # Read the JUnit XML report if it exists
            junit_path = Path(junit_report_path)
            if junit_path.exists():
                junit_xml_content = junit_path.read_text()
            
            # Fallback: if no failures parsed from JSON, try JUnit XML
            if not failing_tests:
                try:
                    failing_tests = self._parse_junit_report(junit_report_path)
                except Exception:
                    # Ignore XML parsing issues; we'll handle as collection/config error below
                    pass

            if not failing_tests:
                # If pytest returned non-zero but we have no parsed failures, treat as collection/config error
                if result.returncode != 0:
                    console.print(f"[red]⚠ Pytest exited with code {result.returncode} but no test failures were parsed. Likely a collection/config error.[/red]")
                    output = (result.stderr or "").strip()
                    if not output:
                        output = (result.stdout or "").strip()
                    summary = (output.splitlines()[0] if output else f"Pytest failed with exit code {result.returncode}")
                    dummy = FailingTest(
                        name="<pytest collection error>",
                        file="<session>",
                        line=0,
                        short_traceback=summary[:200],
                        full_traceback=output or None,
                    )
                    return [dummy], junit_xml_content
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
    
    def _parse_json_report(self, report_path: str) -> List[FailingTest]:
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
                # Remove repo directory prefix if it's included in the path
                repo_name = self.repo_path.name
                if file_part.startswith(f"{repo_name}/"):
                    file_part = file_part[len(repo_name)+1:]
                
                # Choose best available traceback among call/setup/teardown phases
                longrepr = self._pick_longrepr_from_json_test(test)
                
                # Extract short traceback - capture up to the assertion error line
                traceback_lines = longrepr.split('\n') if longrepr else []
                short_trace = []
                for line in traceback_lines:
                    short_trace.append(line)
                    if line.strip().startswith("E"):  # error/exception line
                        break
                    if len(short_trace) >= 5:
                        break
                short_traceback = '\n'.join(short_trace) if short_trace else 'Test failed'
                
                # Try to get line number from the traceback (prefer regex match path:line)
                line_no = 0
                if longrepr:
                    m = re.search(rf"({re.escape(file_part)})[:](\\d+)", longrepr)
                    if m:
                        try:
                            line_no = int(m.group(2))
                        except ValueError:
                            line_no = 0
                if line_no == 0:
                    for line in traceback_lines:
                        if file_part in line and ':' in line:
                            try:
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
        
        # NEW: include collection errors (collectors)
        repo_name = self.repo_path.name
        for collector in report.get('collectors', []):
            if collector.get('outcome') == 'failed':
                nodeid = collector.get('nodeid', '') or ''
                longrepr = collector.get('longrepr', '') or ''
                # Determine file and name
                file_part = nodeid.split('::')[0] if nodeid else '<collection>'
                test_name = Path(nodeid.split('::')[-1] or file_part).stem if nodeid else '<collection error>'
                if file_part.startswith(f"{repo_name}/"):
                    file_part = file_part[len(repo_name)+1:]
                traceback_lines = longrepr.split('\n') if longrepr else []
                short = []
                for line in traceback_lines:
                    short.append(line)
                    if line.strip().startswith('E') or len(short) >= 5:
                        break
                short_msg = '\n'.join(short) if short else 'Test collection failed'
                failing_tests.append(FailingTest(
                    name=test_name,
                    file=file_part,
                    line=0,
                    short_traceback=short_msg,
                    full_traceback=longrepr or None,
                ))

        return failing_tests

    def _pick_longrepr_from_json_test(self, test: Dict[str, Any]) -> str:
        """Pick the most relevant longrepr among call/setup/teardown phases from JSON report entry."""
        for phase in ("call", "setup", "teardown"):
            sec = test.get(phase) or {}
            longrepr = sec.get("longrepr")
            if isinstance(longrepr, str) and longrepr.strip():
                return longrepr
            if longrepr:
                try:
                    return str(longrepr)
                except Exception:
                    pass
        return ""

    def _parse_junit_report(self, report_path: str) -> List[FailingTest]:
        """Parse JUnit XML report (xunit2) to extract failing/error tests as fallback.

        This covers environments where pytest-json-report is not installed.
        """
        path = Path(report_path)
        if not path.exists():
            return []

        try:
            tree = ET.parse(str(path))
            root = tree.getroot()
        except ET.ParseError:
            return []

        failing_tests: List[FailingTest] = []

        # pytest xunit2 places test cases under testsuite/testcase
        for testcase in root.iter('testcase'):
            # A failure or error element indicates a failing test
            failure_el = testcase.find('failure')
            error_el = testcase.find('error')
            if failure_el is None and error_el is None:
                continue

            problem_el = failure_el or error_el

            test_name = testcase.get('name') or '<unknown>'
            classname = testcase.get('classname') or ''
            file_part = testcase.get('file') or ''
            line_no_str = testcase.get('line') or '0'
            try:
                line_no = int(line_no_str)
            except ValueError:
                line_no = 0

            # Compose a more descriptive name if possible
            if classname and test_name and '::' not in test_name:
                display_name = f"{classname}::{test_name}"
            else:
                display_name = test_name

            # Fallbacks if file attribute is missing
            if not file_part and classname:
                # Convert python module path to file-ish hint
                file_part = classname.replace('.', '/') + '.py'

            # Short traceback/message
            message = (problem_el.get('message') or '').strip()
            text = (problem_el.text or '').strip()
            short_trace = message or text or 'Test failed'

            # Full traceback can include the element text
            full_traceback = text or None

            failing_tests.append(FailingTest(
                name=display_name,
                file=file_part or '<unknown>',
                line=line_no,
                short_traceback=short_trace[:200],
                full_traceback=full_traceback,
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
            # Extract the most relevant error line (assertion or exception)
            error_lines = test.short_traceback.split('\n')
            error = "Test failed"
            for line in error_lines:
                if line.strip().startswith("E"):
                    error = line.strip()[2:].strip()  # Remove "E " prefix
                    break
                elif "AssertionError" in line or "assert" in line:
                    error = line.strip()
                    break
            # Truncate if too long
            if len(error) > 80:
                error = error[:77] + "..."
            table += f"| {test.name} | {location} | {error} |\n"
        
        return table
