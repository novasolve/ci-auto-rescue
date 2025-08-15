#!/usr/bin/env python3
import os
import sys
import argparse
import subprocess
import time
import re
import xml.etree.ElementTree as ET
import yaml

def find_test_repositories(base_dir):
    """Return a list of subdirectories in base_dir that contain at least one test_*.py file."""
    repos = []
    base_path = os.path.abspath(base_dir)
    if not os.path.isdir(base_path):
        return repos
    for entry in os.listdir(base_path):
        repo_path = os.path.join(base_path, entry)
        if os.path.isdir(repo_path):
            # Look for any Python test file under this directory
            for root, _, files in os.walk(repo_path):
                if any(f.startswith("test_") and f.endswith(".py") for f in files):
                    repos.append(repo_path)
                    break
    return sorted(repos)

def inject_failures_in_repo(repo_path):
    """Inject a failing assertion into every test function in the repository (in-place file modification)."""
    for root, _, files in os.walk(repo_path):
        for fname in files:
            if fname.startswith("test_") and fname.endswith(".py"):
                file_path = os.path.join(root, fname)
                try:
                    with open(file_path, "r") as f:
                        lines = f.readlines()
                except Exception as e:
                    print(f"WARNING: Could not read {file_path}: {e}", file=sys.stderr)
                    continue
                new_lines = []
                for line in lines:
                    # Expand one-line test definitions (e.g., def test_x(): pass) into multi-line
                    if line.lstrip().startswith("def test_") and ":" in line:
                        # Split at the colon
                        parts = line.split(":", 1)
                        def_line = parts[0] + ":"  # keep the colon
                        tail = parts[1].strip()
                        if tail:  # if there's code (or pass) after the colon
                            new_lines.append(def_line + "\n")
                            indent = " " * ((len(line) - len(line.lstrip())) + 4)
                            # Split multiple statements separated by ';' if any
                            for stmt in tail.split(";"):
                                stmt = stmt.strip()
                                if stmt:
                                    new_lines.append(f"{indent}{stmt}\n")
                            continue
                    new_lines.append(line)
                # Now insert failing assertion at end of each test function
                modified_lines = []
                i = 0
                while i < len(new_lines):
                    line = new_lines[i]
                    modified_lines.append(line)
                    stripped = line.lstrip()
                    if stripped.startswith("def test_"):
                        # Determine indent for this function
                        def_indent = len(line) - len(stripped)
                        # Find where this function block ends
                        j = i + 1
                        last_body_line = None
                        while j < len(new_lines):
                            # Skip over any blank lines within the function
                            if new_lines[j].strip() == "":
                                j += 1
                                continue
                            curr_indent = len(new_lines[j]) - len(new_lines[j].lstrip())
                            if curr_indent <= def_indent:
                                break  # function ends before line j
                            last_body_line = j
                            j += 1
                        if last_body_line is not None:
                            # Insert failure assertion before the function dedents
                            indent_spaces = " " * (def_indent + 4)
                            modified_lines.append(f"{indent_spaces}assert False, \"Injected failure\"\n")
                            # When adding a line, the function end shifts by one
                            i = last_body_line
                            # (Note: loop will increment i further at end)
                    i += 1
                # Write back the modified file
                try:
                    with open(file_path, "w") as f:
                        f.writelines(modified_lines)
                except Exception as e:
                    print(f"WARNING: Could not write to {file_path}: {e}", file=sys.stderr)

def get_fail_count_from_junit(xml_path):
    """Parse a JUnit XML file to count total failures (failures + errors)."""
    if not os.path.isfile(xml_path):
        return None
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except Exception as e:
        print(f"ERROR: Failed to parse XML report {xml_path}: {e}", file=sys.stderr)
        return None
    failures = 0
    errors = 0
    # Sum failures/errors from the root (testsuite/testsuites) and any nested testsuite elements
    if 'failures' in root.attrib:
        failures += int(root.attrib.get('failures', 0) or 0)
    if 'errors' in root.attrib:
        errors += int(root.attrib.get('errors', 0) or 0)
    for ts in root.findall(".//testsuite"):
        if 'failures' in ts.attrib:
            failures += int(ts.attrib.get('failures', 0) or 0)
        if 'errors' in ts.attrib:
            errors += int(ts.attrib.get('errors', 0) or 0)
    return failures + errors

def main():
    parser = argparse.ArgumentParser(description="Run nova fix on multiple test repositories and collect results.")
    parser.add_argument("base_dir", help="Base directory containing test repository subfolders (e.g. examples/demos/).")
    parser.add_argument("--break-tests", action="store_true",
                        help="Inject failing assertions into all tests to force initial failures.")
    parser.add_argument("--output", "-o", default="nova_e2e_summary.yaml",
                        help="Filename for the YAML summary report (default: nova_e2e_summary.yaml).")
    parser.add_argument("--nova-timeout", type=int, default=300,
                        help="Timeout in seconds for each 'nova fix' run (default: 300).")
    args = parser.parse_args()
    base_dir = args.base_dir
    repo_list = find_test_repositories(base_dir)
    if not repo_list:
        print(f"No test repositories found under {base_dir}")
        sys.exit(1)
    # Optionally break tests
    if args.break_tests:
        print(f"Injecting failures into tests for {len(repo_list)} repositories...")
        for repo in repo_list:
            inject_failures_in_repo(repo)
    results = []
    any_failure = False
    ansi_escape = re.compile(r'\x1B\[[0-9;]*[A-Za-z]')  # regex to strip ANSI escape codes
    for repo_path in repo_list:
        repo_name = os.path.basename(os.path.abspath(repo_path))
        print(f"\n=== Running Nova CI-Rescue on '{repo_name}' ===")
        # Run initial tests with pytest, output JUnit XML
        initial_xml = os.path.join(repo_path, "initial_tests.xml")
        final_xml = os.path.join(repo_path, "final_tests.xml")
        # Use pytest with maxfail to run all tests even if some fail
        result = subprocess.run(
            ["pytest", "--tb=short", "--maxfail=999", "--junitxml", initial_xml],
            cwd=repo_path,
            check=False  # Don't raise exception on test failures
        )
        if result.returncode > 1:  # pytest returns 1 for test failures, >1 for errors
            print(f"ERROR: Initial tests failed to run in {repo_name} (pytest exited with code {result.returncode})", file=sys.stderr)
            initial_failures = None
        else:
            initial_failures = get_fail_count_from_junit(initial_xml)
        if initial_failures is None:
            # Could not get initial failures, skip Nova run
            results.append({
                "name": repo_name,
                "initial_failures": None,
                "final_failures": None,
                "success": False,
                "exit_reason": "ERROR",
                "iterations": 0,
                "patches_applied": 0,
                "runtime_seconds": 0.0
            })
            any_failure = True
            continue
        print(f"Initial failing tests: {initial_failures}")
        # Run Nova fix (with verbose logging), capture output to nova_run.log
        log_path = os.path.join(repo_path, "nova_run.log")
        start_time = time.time()
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "nova.cli", "fix", "." , "--verbose"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=args.nova_timeout
            )
        except subprocess.TimeoutExpired:
            elapsed = time.time() - start_time
            print(f"ERROR: Nova fix timed out after {args.nova_timeout}s in {repo_name}", file=sys.stderr)
            # Mark as failure due to timeout
            results.append({
                "name": repo_name,
                "initial_failures": initial_failures,
                "final_failures": None,
                "success": False,
                "exit_reason": "TIMEOUT",
                "iterations": 0,
                "patches_applied": 0,
                "runtime_seconds": round(elapsed, 2)
            })
            any_failure = True
            # Skip final tests in case of timeout
            continue
        elapsed = time.time() - start_time
        # Write Nova output to nova_run.log file
        try:
            with open(log_path, "w") as lf:
                lf.write(proc.stdout or "")
                if proc.stderr:
                    # Separate stderr content if any
                    lf.write("\n[stderr]\n")
                    lf.write(proc.stderr)
        except Exception as e:
            print(f"WARNING: Could not write log file {log_path}: {e}", file=sys.stderr)
        # Run final tests and parse results
        result = subprocess.run(
            ["pytest", "--tb=short", "--maxfail=999", "--junitxml", final_xml],
            cwd=repo_path,
            check=False  # Don't raise exception on test failures
        )
        if result.returncode > 1:  # pytest returns 1 for test failures, >1 for errors
            print(f"ERROR: Final tests failed to run in {repo_name} (code {result.returncode})", file=sys.stderr)
            final_failures = None
        else:
            final_failures = get_fail_count_from_junit(final_xml)
        if final_failures is None:
            # If final tests couldn't run, mark as failure
            success = False
        else:
            success = (proc.returncode == 0 and final_failures == 0)
        # Parse Nova output for iterations, patches, exit reason
        stdout_clean = ansi_escape.sub("", proc.stdout)  # remove ANSI escape sequences
        iterations = 0
        patches = 0
        exit_reason = ""
        # Find "Iterations completed: X/" in output
        match_iter = re.search(r"Iterations completed:\s+(\d+)/", stdout_clean)
        if match_iter:
            try:
                iterations = int(match_iter.group(1))
            except ValueError:
                iterations = 0
        # Find "Patches applied: Y"
        match_patch = re.search(r"Patches applied:\s+(\d+)", stdout_clean)
        if match_patch:
            try:
                patches = int(match_patch.group(1))
            except ValueError:
                patches = 0
        # Find the "Exit Reason: ..." line
        reason_line = None
        for line in stdout_clean.splitlines():
            if "Exit Reason:" in line:
                reason_line = line
                break
        if reason_line:
            # Extract text after "Exit Reason:"
            reason_text = reason_line.split("Exit Reason:")[1].strip()
            # Use the code (before any dash) as exit reason
            if " - " in reason_text:
                exit_reason = reason_text.split(" - ", 1)[0].upper()
            else:
                exit_reason = reason_text.upper()
        else:
            # If Nova did not print an exit reason (e.g., no failures to start)
            if initial_failures == 0 or proc.returncode == 0:
                exit_reason = "SUCCESS"
            else:
                exit_reason = "ERROR"
        # Log success/failure for CLI output
        status_text = "SUCCESS" if success else "FAILURE"
        print(f"Final failing tests: {final_failures if final_failures is not None else 'N/A'}")
        print(f"Result: {status_text} (Exit Reason: {exit_reason}, Iterations: {iterations}, Patches: {patches}, Time: {elapsed:.2f}s)")
        # Append results for this repo
        results.append({
            "name": repo_name,
            "initial_failures": int(initial_failures),
            "final_failures": int(final_failures) if final_failures is not None else None,
            "success": bool(success),
            "exit_reason": exit_reason,
            "iterations": int(iterations),
            "patches_applied": int(patches),
            "runtime_seconds": round(elapsed, 2)
        })
        if not success:
            any_failure = True
    # Save YAML summary
    summary = results  # list of dicts
    try:
        with open(args.output, "w") as yf:
            yaml.safe_dump(summary, yf)
        print(f"\nSaved summary report to {args.output}")
    except Exception as e:
        print(f"ERROR: Could not write YAML summary: {e}", file=sys.stderr)
    # Print a final summary table in console
    try:
        from rich.console import Console
        from rich.table import Table
        console = Console()
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Repository", style="bold")
        table.add_column("Initial Failures", justify="center")
        table.add_column("Final Failures", justify="center")
        table.add_column("Iterations", justify="center")
        table.add_column("Patches", justify="center")
        table.add_column("Time (s)", justify="center")
        table.add_column("Status", justify="center")
        for res in results:
            final_fail_str = str(res["final_failures"]) if res["final_failures"] is not None else "N/A"
            status = "[green]SUCCESS[/green]" if res["success"] else "[red]FAIL[/red]"
            table.add_row(res["name"], str(res["initial_failures"]), final_fail_str,
                          str(res["iterations"]), str(res["patches_applied"]),
                          f"{res['runtime_seconds']:.1f}", status)
        console.print("\n[bold underline]Nova CI-Rescue Results Summary[/bold underline]")
        console.print(table)
    except ImportError:
        # Fallback to plain text if Rich is not installed
        print("\nSummary of Results:")
        print(f"{'Repository':30} {'InitFail':>9} {'FinalFail':>9} {'Iter':>5} {'Patch':>6} {'Time(s)':>8} {'Status':>8}")
        print("-" * 80)
        for res in results:
            name = res["name"][:30]
            init_fails = res["initial_failures"]
            final_fails = res["final_failures"] if res["final_failures"] is not None else "N/A"
            status = "SUCCESS" if res["success"] else "FAIL"
            print(f"{name:30} {init_fails:>9} {str(final_fails):>9} {res['iterations']:>5} {res['patches_applied']:>6} {res['runtime_seconds']:>8.1f} {status:>8}")
    # Exit with code 1 if any failures, else 0
    sys.exit(1 if any_failure else 0)

if __name__ == "__main__":
    main()
