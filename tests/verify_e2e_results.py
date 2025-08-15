import os
import sys
import glob
import xml.etree.ElementTree as ET

# Usage: python verify_e2e_results.py <target_repo_path> <nova_log_file>
# Example: python verify_e2e_results.py demo-repo demo-repo/nova_run.log

if len(sys.argv) < 2:
    print("Usage: verify_e2e_results.py <target_repo_path> [nova_log_file]")
    sys.exit(1)

target_path = sys.argv[1].rstrip("/\\")
# Determine Nova log file path
if len(sys.argv) >= 3:
    nova_log_path = sys.argv[2]
else:
    # Default to target_path/nova_run.log if not provided
    nova_log_path = os.path.join(target_path, "nova_run.log")

# Ensure required files exist
initial_report = os.path.join(target_path, "initial_tests.xml")
final_report = os.path.join(target_path, "final_tests.xml")
if not os.path.isfile(initial_report):
    print(f"ERROR: Initial test report not found at {initial_report}")
    sys.exit(1)
if not os.path.isfile(final_report):
    print(f"ERROR: Final test report not found at {final_report}")
    sys.exit(1)
if not os.path.isfile(nova_log_path):
    print(f"ERROR: Nova output log not found at {nova_log_path}")
    sys.exit(1)

# Parse JUnit XML reports to get failure counts
def get_fail_count(xml_path: str) -> int:
    """Parse a JUnit XML file and return total failures (failures + errors)."""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"ERROR: Failed to parse XML report {xml_path}: {e}")
        sys.exit(1)
    # The root may be <testsuite> or <testsuites>, sum all failures and errors
    failures = 0
    errors = 0
    # If root has 'failures' attribute, use it (could be testsuite or testsuites)
    if 'failures' in root.attrib:
        try:
            failures += int(root.attrib.get('failures', 0) or 0)
        except ValueError:
            failures += 0
    if 'errors' in root.attrib:
        try:
            errors += int(root.attrib.get('errors', 0) or 0)
        except ValueError:
            errors += 0
    # Also accumulate nested testsuite elements, if any
    for ts in root.findall('.//testsuite'):
        if 'failures' in ts.attrib:
            try:
                failures += int(ts.attrib.get('failures', 0) or 0)
            except ValueError:
                pass
        if 'errors' in ts.attrib:
            try:
                errors += int(ts.attrib.get('errors', 0) or 0)
            except ValueError:
                pass
    return failures + errors

initial_failures = get_fail_count(initial_report)
final_failures = get_fail_count(final_report)

# Check that Nova reduced the number of failing tests
print(f"Initial failing tests: {initial_failures}")
print(f"Final failing tests: {final_failures}")
if initial_failures < 1:
    print("WARNING: No failing tests were detected initially. (Repository may have been green to start.)")
if final_failures >= initial_failures:
    print(f"ERROR: Final failing tests ({final_failures}) not less than initial failures ({initial_failures}).")
    sys.exit(1)
if final_failures != 0:
    print(f"ERROR: There are still {final_failures} failing tests after Nova run (expected 0).")
    sys.exit(1)

# Verify that Nova telemetry artifacts exist in the target repo's .nova directory
nova_dir = os.path.join(target_path, ".nova")
if not os.path.isdir(nova_dir):
    print(f"ERROR: Nova telemetry directory not found: {nova_dir}")
    sys.exit(1)

# Find patch files and telemetry logs in .nova
patch_files = glob.glob(os.path.join(nova_dir, "**", "*.patch"), recursive=True)
if len(patch_files) == 0:
    print("ERROR: No patch files found in .nova directory (Nova did not generate any patches).")
    sys.exit(1)
else:
    print(f"Found {len(patch_files)} patch file(s) in .nova directory.")

log_files = glob.glob(os.path.join(nova_dir, "**", "trace.jsonl"), recursive=True)
if len(log_files) == 0:
    # If no JSONL trace, check for any log or telemetry files
    log_files = glob.glob(os.path.join(nova_dir, "**", "*.jsonl"), recursive=True)
if len(log_files) == 0:
    print("ERROR: No telemetry log found in .nova directory (trace.jsonl missing).")
    sys.exit(1)
else:
    print(f"Telemetry log present: {log_files[0]}")

# Scan Nova output log for success/failure indicators
with open(nova_log_path, "r", errors="ignore") as f:
    log_text = f.read()

# Remove ANSI escape codes for easier searching
import re
ansi_escape = re.compile(r'\x1B\[[0-9;]*[A-Za-z]')
clean_log = ansi_escape.sub("", log_text)

# Detect Nova exit reason and any safety/iteration issues
exit_reason_line = None
for line in clean_log.splitlines():
    if "Exit Reason:" in line:
        exit_reason_line = line
        break

if exit_reason_line:
    # Extract reason after 'Exit Reason:'
    reason = exit_reason_line.split("Exit Reason:")[1].strip()
    reason = reason.upper()
else:
    reason = ""
    # If Nova ended early due to no failures, treat as success
    if "No failing tests found" in clean_log or initial_failures == 0:
        reason = "SUCCESS"

# Check for explicit markers of problems
if "MAX ITERATIONS" in reason or "TIMEOUT" in reason or "ERROR" in reason or "PATCH_ERROR" in reason or "SAFETY_VIOLATION" in reason or "PATCH REJECTED" in reason:
    print(f"ERROR: Nova did not successfully complete – {exit_reason_line.strip() if exit_reason_line else reason}")
    sys.exit(1)
if "Patch rejected due to safety limits" in clean_log:
    print("ERROR: Nova patch was rejected due to safety limits (safety violation occurred).")
    sys.exit(1)

# Ensure Nova reported success
if "SUCCESS" not in reason:
    print(f"ERROR: Nova run did not end with success. Exit reason: {reason or 'Unknown'}")
    sys.exit(1)

print("✅ Nova CI-Rescue run completed successfully and fixed all failing tests.")
