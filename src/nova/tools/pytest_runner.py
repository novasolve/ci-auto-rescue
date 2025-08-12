from __future__ import annotations

import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional


class PytestRunError(Exception):
    pass


def run_pytest(repo: Path, timeout_s: int, junit_xml_path: Path, extra_args: Optional[List[str]] = None) -> Dict:
    repo = repo.resolve()
    junit_xml_path = junit_xml_path.resolve()
    junit_xml_path.parent.mkdir(parents=True, exist_ok=True)
    args = [
        "pytest",
        "-q",
        "--maxfail=1",
        "--disable-warnings",
        f"--junitxml={junit_xml_path}",
    ]
    if extra_args:
        args.extend(extra_args)
    try:
        cp = subprocess.run(args, cwd=str(repo), capture_output=True, text=True, timeout=timeout_s)
    except subprocess.TimeoutExpired as e:
        raise PytestRunError(f"pytest timed out after {timeout_s}s") from e
    # Pytest returns non-zero on failures; that's okay. Ensure the report exists.
    if not junit_xml_path.exists():
        # Include some output for debugging
        out = (cp.stdout or "") + "\n" + (cp.stderr or "")
        raise PytestRunError(f"pytest did not produce JUnit XML: {out[:4000]}")
    results = parse_junit(junit_xml_path)
    results.update({
        "returncode": cp.returncode,
        "stdout": cp.stdout,
        "stderr": cp.stderr,
        "junit_xml": str(junit_xml_path),
    })
    return results


def parse_junit(path: Path) -> Dict:
    tree = ET.parse(path)
    root = tree.getroot()
    # Support both testsuite at root or testsuites > testsuite
    suites = []
    if root.tag == "testsuite":
        suites = [root]
    else:
        suites = [s for s in root.iter("testsuite")]
    total = failures = errors = skipped = passed = 0
    failing: List[Dict] = []
    for s in suites:
        total += int(s.attrib.get("tests", 0))
        failures += int(s.attrib.get("failures", 0))
        errors += int(s.attrib.get("errors", 0))
        skipped += int(s.attrib.get("skipped", 0))
        for tc in s.iter("testcase"):
            tc_name = tc.attrib.get("classname", "") + "." + tc.attrib.get("name", "")
            failure_el = tc.find("failure")
            error_el = tc.find("error")
            if failure_el is not None or error_el is not None:
                el = failure_el or error_el
                msg = (el.attrib.get("message") if el is not None else "") or ""
                text = (el.text or "").strip() if el is not None else ""
                failing.append({
                    "nodeid": tc_name.strip("."),
                    "message": msg,
                    "trace": text,
                    "type": "error" if error_el is not None else "failure",
                })
    passed = total - failures - errors - skipped
    return {
        "total": total,
        "failed": failures,
        "errors": errors,
        "skipped": skipped,
        "passed": passed,
        "failing": failing,
    }
