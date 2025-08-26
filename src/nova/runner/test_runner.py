"""
Test runner module for capturing pytest failures.
"""

import json
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from rich.console import Console

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
    
    def __init__(self, repo_path: Path, verbose: bool = False):
        self.repo_path = repo_path
        self.verbose = verbose
        
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
            # Run pytest with JSON and JUnit reports
            cmd = [
                "python", "-m", "pytest",
                "--json-report",
                f"--json-report-file={json_report_path}",
                f"--junit-xml={junit_report_path}",
                "--tb=short",
                # Forcefully disable failfast even if -x/maxfail is set in addopts/PYTEST_ADDOPTS
                "--maxfail=0",
                "-q",  # Quiet mode (does not affect JSON/JUnit reports)
                "--no-header",
                "--no-summary",
                "-rN",  # Don't show any summary info
            ]
            
            if self.verbose:
                console.print(f"[dim]Running: {' '.join(cmd)}[/dim]")
            
            # Run pytest (we expect it to fail if there are failing tests)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.repo_path),
            )
            
            # Parse the JSON report
            failing_tests = self._parse_json_report(json_report_path)
            
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
    
    def _parse_json_report(self, report_path: str) -> List[FailingTest]:
        """Parse pytest JSON report to extract failing tests (call/setup/teardown)."""
        try:
            with open(report_path, 'r') as f:
                report = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
        
        failing_tests = []
        
        # Extract failing tests from the report
        for test in report.get('tests', []):
            if test.get('outcome') in ['failed', 'error']:
                # --- Node/test name parsing ---
                nodeid = test.get('nodeid', '')
                if '::' in nodeid:
                    file_part, test_part = nodeid.split('::', 1)
                    test_name = test_part.replace('::', '.')
                else:
                    file_part = nodeid
                    test_name = Path(nodeid).stem
                
                # Normalize file path to be relative to repo root when possible
                try:
                    p = Path(file_part)
                    if p.is_absolute():
                        file_part = str(p.relative_to(self.repo_path))
                    else:
                        repo_name = self.repo_path.name
                        if file_part.startswith(f"{repo_name}/"):
                            file_part = file_part[len(repo_name)+1:]
                except Exception:
                    # If not inside repo, keep as-is
                    pass
                
                # --- Prefer the phase that actually failed (call/setup/teardown) ---
                phase_info = None
                for ph in ("call", "setup", "teardown"):
                    info = test.get(ph)
                    if isinstance(info, dict) and info.get('outcome') in ('failed', 'error'):
                        phase_info = info
                        break
                if not phase_info:
                    phase_info = test.get("call") or test.get("setup") or test.get("teardown") or {}
                
                longrepr_obj = phase_info.get('longrepr', '')
                
                # Convert longrepr to a string, whether it's already a string or a structured dict
                def _longrepr_to_text(lr: Any) -> str:
                    if isinstance(lr, str):
                        return lr
                    if isinstance(lr, dict):
                        parts = []
                        rc = lr.get('reprcrash') or {}
                        path = rc.get('path')
                        lineno = rc.get('lineno')
                        message = rc.get('message')
                        if path or lineno or message:
                            parts.append(f"{path or ''}:{lineno or ''}: {message or ''}".strip())
                        tb = lr.get('reprtraceback') or {}
                        for entry in tb.get('reprentries', []):
                            # entries may carry formatted lines under different keys
                            data = entry.get('data') or {}
                            lines = data.get('lines') or entry.get('lines') or []
                            parts.extend(lines)
                        return "\n".join([p for p in parts if p])
                    return str(lr) if lr is not None else ""
                
                longrepr_text = _longrepr_to_text(longrepr_obj)
                traceback_lines = longrepr_text.splitlines() if longrepr_text else []
                
                # Build a short traceback: try up to first AssertionError line; else last few lines
                short_lines = []
                saw_error = False
                for line in traceback_lines:
                    short_lines.append(line)
                    if line.strip().startswith("E"):
                        saw_error = True
                        break
                    if len(short_lines) >= 10:
                        break
                if not saw_error and traceback_lines:
                    short_lines = traceback_lines[-6:]
                short_traceback = "\n".join(short_lines) if short_lines else "Test failed"
                
                # Extract line number: prefer structured reprcrash.lineno; else regex from text
                line_no = 0
                try:
                    if isinstance(longrepr_obj, dict):
                        rc = longrepr_obj.get('reprcrash') or {}
                        if isinstance(rc.get('lineno'), int):
                            line_no = int(rc['lineno'])
                    if not line_no and file_part and longrepr_text:
                        m = re.search(rf"{re.escape(file_part)}:(\d+)", longrepr_text)
                        if m:
                            line_no = int(m.group(1))
                except Exception:
                    line_no = 0
                
                failing_tests.append(FailingTest(
                    name=test_name,
                    file=file_part,
                    line=line_no,
                    short_traceback=short_traceback,
                    full_traceback=longrepr_text,
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
