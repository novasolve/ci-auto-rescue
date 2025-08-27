"""
Robust pytest runner with JSON plugin detection, JUnit XML fallback,
and explicit handling of collection/config errors.

Usage (library):
    from nova.runner.test_runner import TestRunner
    failures, junit_xml = TestRunner(Path.cwd(), verbose=True, pytest_args="-k foo").run_tests()
    print(TestRunner.format_failures_table(failures))

Usage (CLI):
    # Installed as `nova`:
    nova fix . --verbose
"""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
import shlex
import sys
from dataclasses import dataclass
import os
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import xml.etree.ElementTree as ET

try:
    from rich.console import Console
    _console = Console()
    def _print(msg: str) -> None:
        _console.print(msg)
except Exception:
    # Strip simple [tag]...[/tag] markup when rich is unavailable
    _TAG_RE = re.compile(r"\[(\/?[a-zA-Z][^\]]*)\]")
    def _print(msg: str) -> None:
        print(_TAG_RE.sub("", msg))

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

    # ---- Public API -----------------------------------------------------

    def run_tests(self) -> Tuple[List[FailingTest], Optional[str]]:
        """
        Run pytest and capture all failing tests.

        Returns:
            Tuple of (List of FailingTest objects, JUnit XML report content)
        """
        _print("[cyan]Running pytest to identify failing tests...[/cyan]")

        # Create temp files for reports
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            json_report_path = tmp.name
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as tmp:
            junit_report_path = tmp.name

        junit_xml_content = None

        try:
            # Build the pytest command, preferring a repo-local venv or pytest on PATH.
            cmd = self._build_pytest_cmd(json_report_path, junit_report_path)

            # Append user-provided pytest args (e.g., -k filters)
            if self.pytest_args:
                try:
                    cmd.extend(shlex.split(self.pytest_args))
                except ValueError:
                    cmd.append(self.pytest_args)

            if self.verbose:
                _print(f"[dim]Running: {' '.join(cmd)}[/dim]")

            # Run pytest (it may exit non-zero when tests fail/collect fails)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.repo_path),
                timeout=300,
            )
            combined_output = (result.stderr or '') + '\n' + (result.stdout or '')

            # If JSON plugin is missing, pytest will complain about --json-report
            if ("unrecognized arguments" in combined_output and
                ("--json-report" in combined_output or "--json-report-file" in combined_output)):
                cmd_no_json = [
                    a for a in cmd
                    if not (a == "--json-report" or a.startswith("--json-report-file="))
                ]
                if self.verbose:
                    _print(f"[dim]Re-running without json-report: {' '.join(cmd_no_json)}[/dim]")
                result = subprocess.run(
                    cmd_no_json,
                    capture_output=True,
                    text=True,
                    cwd=str(self.repo_path),
                    timeout=300,
                )
                combined_output = (result.stderr or '') + '\n' + (result.stdout or '')

            # Parse JSON report first (best fidelity)
            failing_tests = self._parse_json_report(json_report_path)

            # Read the JUnit XML always, so callers can capture it
            junit_path = Path(junit_report_path)
            if junit_path.exists():
                try:
                    junit_xml_content = junit_path.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    junit_xml_content = None

            # Fallback: parse JUnit if JSON yielded nothing
            if not failing_tests:
                try:
                    failing_tests = self._parse_junit_report(junit_report_path)
                except Exception:
                    # Ignore XML parsing issues; handle via exit code below.
                    pass

            # If still nothing and pytest returned non-zero, surface as a collection/config error
            if not failing_tests:
                # Special-case pytest exit code 5: no tests collected
                if result.returncode == 5:
                    summarized = self._summarize_first_line(combined_output) or "No tests were collected."
                    dummy = FailingTest(
                        name="<no tests collected>",
                        file="<session>",
                        line=0,
                        short_traceback=summarized,
                        full_traceback=combined_output.strip() or None,
                    )
                    _print("[yellow]⚠ No tests were collected (pytest exit code 5).[/yellow]")
                    return [dummy], junit_xml_content
                if result.returncode != 0:
                    _print(f"[red]⚠ Pytest exited with code {result.returncode} but no test failures were parsed. Likely a collection/config error.[/red]")
                    summarized = self._summarize_first_line(combined_output) or f"Pytest failed with exit code {result.returncode}"
                    dummy = FailingTest(
                        name="<pytest collection error>",
                        file="<session>",
                        line=0,
                        short_traceback=summarized,
                        full_traceback=combined_output.strip() or None,
                    )
                    return [dummy], junit_xml_content
                _print("[green]✓ No failing tests found![/green]")
                return [], junit_xml_content

            _print(f"[yellow]Found {len(failing_tests)} failing test(s)[/yellow]")
            return failing_tests, junit_xml_content

        except FileNotFoundError:
            _print("[red]Error: pytest not found in the current interpreter. Activate your venv and install pytest.[/red]")
            return [], None
        except subprocess.TimeoutExpired:
            _print("[red]Error: pytest timed out.[/red]")
            return [], None
        except Exception as e:
            _print(f"[red]Error running tests: {e}[/red]")
            return [], None
        finally:
            # Best-effort cleanup
            try:
                Path(json_report_path).unlink(missing_ok=True)
            except Exception:
                pass
            try:
                Path(junit_report_path).unlink(missing_ok=True)
            except Exception:
                pass

    # ---- Command construction ------------------------------------------

    def _build_pytest_cmd(self, json_report_path: str, junit_report_path: str) -> List[str]:
        """
        Prefer a repo-local venv Python (./.venv/bin/python or ./venv/bin/python).
        If not found, prefer a pytest executable on PATH.
        Otherwise, fall back to the current process's interpreter.
        """
        args = [
            "--tb=short",
            "-q",
            "--json-report",
            f"--json-report-file={json_report_path}",
            f"--junitxml={junit_report_path}",
        ]

        # 1) Repo-local venv python
        venv_candidates = [self.repo_path / ".venv" / "bin" / "python",
                           self.repo_path / "venv" / "bin" / "python"]
        for py in venv_candidates:
            if py.exists():
                return [str(py), "-m", "pytest"] + args

        # 2) Pytest on PATH
        pytest_exe = shutil.which("pytest", path=os.environ.get("PATH"))
        if pytest_exe:
            return [pytest_exe] + args

        # 3) Fallback: the interpreter running Nova (may be pyenv/global)
        return [sys.executable, "-m", "pytest"] + args

    @staticmethod
    def format_failures_table(failures: List[FailingTest]) -> str:
        """Format failing tests as a markdown table suitable for planner/LLM prompts."""
        if not failures:
            return "No failing tests found."

        table = "| Test Name | File:Line | Error |\n"
        table += "|-----------|-----------|-------|\n"

        for test in failures:
            location = f"{test.file}:{test.line}" if (test.file and test.line > 0) else (test.file or "<unknown>")
            st = (test.short_traceback or "")
            error = None
            # Prefer pytest-style error/assert lines
            for line in st.splitlines():
                ls = line.strip()
                if ls.startswith("E "):
                    error = ls[2:].strip()
                    break
                if "AssertionError" in ls or ls.startswith("assert "):
                    error = ls
                    break
            # Fallback: first non-empty line (covers collection/config errors)
            if not error:
                for line in st.splitlines():
                    ls = line.strip()
                    if ls:
                        error = ls
                        break
            if not error:
                error = "Test failed"
            if len(error) > 120:
                error = error[:117] + "..."
            table += f"| {test.name} | {location} | {error} |\n"

        return table

    # ---- Internals ------------------------------------------------------

    def _parse_json_report(self, report_path: str) -> List[FailingTest]:
        """Parse pytest JSON report (from pytest-json-report) to extract failing tests and collectors."""
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                report = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

        failures: List[FailingTest] = []

        for test in report.get("tests", []) or []:
            if test.get("outcome") not in ("failed", "error"):
                continue

            nodeid = test.get("nodeid", "") or ""
            file_part, test_name = self._split_nodeid(nodeid)

            # Pick the most informative longrepr across phases
            longrepr = self._pick_longrepr_from_json_test(test)
            traceback_lines = (longrepr or "").splitlines()
            short_traceback = self._shorten_traceback(traceback_lines)

            line_no = self._extract_line_number(file_part, traceback_lines)

            failures.append(FailingTest(
                name=test_name,
                file=file_part,
                line=line_no,
                short_traceback=short_traceback,
                full_traceback=longrepr or None,
            ))

        # Include collection/collector errors if present
        for col in report.get("collectors", []) or []:
            if col.get("outcome") != "failed":
                continue
            nodeid = col.get("nodeid", "") or ""
            longrepr = col.get("longrepr", "") or ""
            if not isinstance(longrepr, str):
                try:
                    longrepr = json.dumps(longrepr)
                except Exception:
                    longrepr = str(longrepr)

            file_part, test_name = self._split_nodeid(nodeid) if nodeid else ("<collection>", "<collection error>")
            lines = (longrepr or "").splitlines()
            short_traceback = self._shorten_traceback(lines)
            failures.append(FailingTest(
                name=test_name,
                file=file_part,
                line=0,
                short_traceback=short_traceback,
                full_traceback=longrepr or None,
            ))

        return failures

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
        # Fallback: some JSON reports put it at top-level
        lr = test.get("longrepr")
        if isinstance(lr, str) and lr.strip():
            return lr
        return ""

    def _parse_junit_report(self, report_path: str) -> List[FailingTest]:
        """Parse JUnit XML report (xunit2) to extract failing/error tests as fallback."""
        p = Path(report_path)
        if not p.exists():
            return []

        try:
            tree = ET.parse(str(p))
            root = tree.getroot()
        except ET.ParseError:
            return []

        failures: List[FailingTest] = []

        for tc in root.iter("testcase"):
            failure_el = tc.find("failure")
            error_el = tc.find("error")
            if failure_el is None and error_el is None:
                continue
            problem_el = failure_el or error_el

            name = tc.get("name") or "<unknown>"
            classname = tc.get("classname") or ""
            display_name = f"{classname}::{name}" if (classname and "::" not in name) else name

            # File/line are often absent in JUnit; try several fallbacks
            file_part = tc.get("file") or ""
            line_no = self._safe_int(tc.get("line") or "0")

            if not file_part and classname:
                # Convert module-like to path hint; not perfect, but helpful.
                file_part = classname.replace(".", "/") + ".py"

            message = (problem_el.get("message") or "").strip()
            text = (problem_el.text or "").strip()
            short = message or text or "Test failed"

            failures.append(FailingTest(
                name=display_name,
                file=file_part or "<unknown>",
                line=line_no,
                short_traceback=short,
                full_traceback=text or None,
            ))

        return failures

    # ---- Helpers --------------------------------------------------------

    def _split_nodeid(self, nodeid: str) -> Tuple[str, str]:
        """
        Split pytest nodeid into (file_part, test_display_name).
        Examples:
            tests/test_foo.py::TestX::test_y -> ("tests/test_foo.py", "TestX.test_y")
            tests/test_foo.py::test_bar      -> ("tests/test_foo.py", "test_bar")
        """
        file_part = nodeid
        test_name = Path(nodeid).stem
        if "::" in nodeid:
            file_part, test_part = nodeid.split("::", 1)
            test_name = test_part.replace("::", ".")
        # Normalize if nodeid accidentally includes repo root name
        repo_name = self.repo_path.name
        if file_part.startswith(f"{repo_name}/"):
            file_part = file_part[len(repo_name) + 1 :]
        return file_part, test_name

    def _shorten_traceback(self, lines: List[str]) -> str:
        out: List[str] = []
        for ln in lines:
            out.append(ln)
            if ln.strip().startswith("E "):  # error line
                break
            if len(out) >= 5:
                break
        return "\n".join(out) if out else "Test failed"

    def _extract_line_number(self, file_part: str, traceback_lines: List[str]) -> int:
        # Prefer pattern "path/to/file.py:123"
        if file_part:
            m = re.search(rf"({re.escape(file_part)})[:](\d+)", "\n".join(traceback_lines))
            if m:
                return self._safe_int(m.group(2))
        # Heuristic: look for ".../file.py:<line>"
        for ln in traceback_lines:
            if file_part in ln and ":" in ln:
                parts = ln.split(":")
                for i, part in enumerate(parts):
                    if file_part in part and i + 1 < len(parts):
                        return self._safe_int(parts[i + 1].split()[0])
        return 0

    def _summarize_first_line(self, text: str) -> str:
        if not text:
            return ""
        # Prefer pytest-style error lines or common import errors
        patterns = [
            r"^E +.*",
            r".*ModuleNotFoundError.*",
            r".*ImportError.*",
            r".*ERROR.*",
        ]
        for pat in patterns:
            m = re.search(pat, text, flags=re.MULTILINE)
            if m:
                return m.group(0).strip()
        for line in text.splitlines():
            s = line.strip()
            if s:
                return s
        return ""

    def _safe_int(self, s: str) -> int:
        try:
            return int(s)
        except Exception:
            return 0
