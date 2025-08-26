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
                "-q",  # Quiet mode
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
        """Parse pytest JSON report to extract failing tests."""
        try:
            with open(report_path, 'r') as f:
                report = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
        
        failing_tests = []
        
        # Extract failing tests from all phases (setup/call/teardown)
        for test in report.get("tests", []):
            outcome = test.get("outcome")
            if outcome not in {"failed", "error"}:
                continue
            nodeid = test.get("nodeid", "")
            file_part = nodeid.split("::", 1)[0] if "::" in nodeid else nodeid
            test_name = nodeid.split("::")[-1] if "::" in nodeid else Path(nodeid).stem
            # Normalize file relative to repo root
            repo_name = self.repo_path.name
            if file_part.startswith(f"{repo_name}/"):
                file_part = file_part[len(repo_name)+1:]
            # Phase-prefer: call > setup > teardown
            phase = None
            longrepr = ""
            for ph in ("call", "setup", "teardown"):
                if ph in test:
                    phase = ph
                    longrepr = test[ph].get("longrepr", "") or longrepr
                    if test[ph].get("outcome") in {"failed", "error"}:
                        break
            # Line extraction
            line_no = 0
            for ln in (longrepr or "").splitlines():
                if file_part in ln and ":" in ln:
                    parts = ln.split(":")
                    try:
                        idx = parts.index(file_part) if file_part in parts else 0
                        cand = parts[idx+1] if idx+1 < len(parts) else parts[1]
                        line_no = int("".join([c for c in cand if c.isdigit()]))
                        break
                    except Exception:
                        pass
            # Short traceback (first E-line or up to 5 lines)
            tlines = (longrepr or "").splitlines()
            short = []
            for ln in tlines:
                short.append(ln)
                if ln.strip().startswith("E"):
                    break
                if len(short) >= 5:
                    break
            failing_tests.append(FailingTest(
                name=test_name,
                file=file_part,
                line=line_no,
                short_traceback="\n".join(short) or "Test failed",
                full_traceback=longrepr or None,
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
