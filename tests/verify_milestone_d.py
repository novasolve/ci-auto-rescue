#!/usr/bin/env python3
"""
Milestone D: Demo & Release - Evaluation Script.

This script reads a YAML configuration file that lists repository paths (or test run descriptors),
then runs `nova fix` on each repository sequentially. For each run, it captures:
 - Success or failure (whether all tests passed after Nova's fix)
 - Total runtime duration of the `nova fix` command
 - Number of iterations Nova took to reach completion

Results from all runs are saved to a timestamped JSON file under `evals/results/` (created if needed).
At the end, a summary table is printed to the console showing each repository, whether the run succeeded,
the runtime, and the iterations used.

Usage:
    python verify_milestone_d.py <path/to/config.yaml>
"""
import sys
import subprocess
import time
import logging
import json
from pathlib import Path
import re

try:
    import yaml
except ImportError:
    print("Missing dependency PyYAML. Please install the requirements.", file=sys.stderr)
    sys.exit(1)

# Configure logging for info and error messages
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Validate command-line arguments
if len(sys.argv) != 2:
    logger.error("Usage: python verify_milestone_d.py <config.yaml>")
    sys.exit(1)

config_file = Path(sys.argv[1])
if not config_file.is_file():
    logger.error(f"Config file not found: {config_file}")
    sys.exit(1)

# Load YAML configuration listing the runs
try:
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)
except Exception as e:
    logger.error(f"Failed to load YAML config file: {e}")
    sys.exit(1)

# Determine the list of repository runs from the config structure
if isinstance(config, dict):
    if "runs" in config:
        run_items = config["runs"]
    elif "repositories" in config:
        run_items = config["repositories"]
    elif "repos" in config:
        run_items = config["repos"]
    else:
        # If dict doesn't have a specific key, treat each key/value as name/path pair
        run_items = []
        for name, path in config.items():
            run_items.append({"name": str(name), "path": str(path)})
elif isinstance(config, list):
    run_items = config
else:
    logger.error("Invalid config format: top-level YAML should be a list or a dict with runs.")
    sys.exit(1)

if not run_items:
    logger.error("No repository runs specified in the config file.")
    sys.exit(1)

results = []
any_failure = False

# Regex pattern to find iteration count in Nova output (e.g., "Iterations completed: 3/6")
iter_pattern = re.compile(r"Iterations completed:\s+(\d+)/")

for entry in run_items:
    # Parse each entry to get repository path and name
    if isinstance(entry, str):
        repo_path = Path(entry)
        repo_name = repo_path.name
    elif isinstance(entry, dict):
        path_val = entry.get("path") or entry.get("repo")
        if not path_val:
            logger.error(f"Invalid config entry (missing path): {entry}")
            continue
        repo_path = Path(path_val)
        repo_name = entry.get("name") or repo_path.name
    else:
        logger.error(f"Ignoring invalid config entry: {entry}")
        continue

    # Resolve path and verify the repository directory exists
    repo_path = repo_path.expanduser().resolve()
    logger.info(f"=== Running Nova fix for '{repo_name}' ===")
    logger.info(f"Repository path: {repo_path}")
    if not repo_path.exists() or not repo_path.is_dir():
        logger.error(f"Path does not exist or is not a directory: {repo_path}")
        results.append({
            "name": repo_name,
            "repo": str(repo_path),
            "success": False,
            "iterations": 0,
            "duration_seconds": 0.0
        })
        any_failure = True
        continue

    # Run the Nova fix command as a subprocess and capture output
    start_time = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "nova.cli", "fix", str(repo_path)],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout per run
        )
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout running Nova on {repo_path} (exceeded 5 minutes)")
        duration = time.time() - start_time
        results.append({
            "name": repo_name,
            "repo": str(repo_path),
            "success": False,
            "iterations": 0,
            "duration_seconds": round(duration, 2),
            "error": "timeout"
        })
        any_failure = True
        continue
    except Exception as e:
        logger.error(f"Error launching Nova on {repo_path}: {e}")
        duration = time.time() - start_time
        results.append({
            "name": repo_name,
            "repo": str(repo_path),
            "success": False,
            "iterations": 0,
            "duration_seconds": round(duration, 2),
            "error": str(e)
        })
        any_failure = True
        continue
    duration = time.time() - start_time

    # Determine success from Nova's exit code (0 = tests fixed, 1 = failure or incomplete fix)
    run_success = (proc.returncode == 0)
    
    # Parse the number of iterations from Nova output if available
    iterations = 0
    match = iter_pattern.search(proc.stdout)
    if match:
        try:
            iterations = int(match.group(1))
        except ValueError:
            iterations = 0

    # Log and store the result for this run
    if run_success:
        logger.info(f"✅ {repo_name}: Success in {duration:.2f}s, iterations = {iterations}")
    else:
        logger.error(f"❌ {repo_name}: Failure in {duration:.2f}s, iterations = {iterations}")
    
    result_data = {
        "name": repo_name,
        "repo": str(repo_path),
        "success": run_success,
        "iterations": iterations,
        "duration_seconds": round(duration, 2)
    }
    
    # Include stderr/stdout snippets for debugging failed runs
    if not run_success:
        # Only include last 500 chars of output to avoid huge JSON files
        if proc.stderr:
            result_data["stderr_snippet"] = proc.stderr[-500:]
        if proc.stdout:
            result_data["stdout_snippet"] = proc.stdout[-500:]
    
    results.append(result_data)
    if not run_success:
        any_failure = True

# Ensure results directory exists and save the JSON results
results_dir = Path("evals") / "results"
results_dir.mkdir(parents=True, exist_ok=True)
timestamp = time.strftime("%Y%m%d_%H%M%S")
output_path = results_dir / f"{timestamp}.json"
try:
    with open(output_path, "w") as jf:
        json.dump(results, jf, indent=2)
    logger.info(f"Saved run results to {output_path}")
except Exception as e:
    logger.error(f"Failed to write results JSON: {e}")

# Print a summary table of all runs
try:
    from rich.console import Console
    from rich.table import Table
except ImportError:
    Console = None
    Table = None
    logger.warning("Rich not installed, printing plain summary.")

if Console and Table:
    console = Console()
    table = Table(show_header=True, header_style="bold")
    table.add_column("Repository", style="bold")
    table.add_column("Result", justify="center")
    table.add_column("Time")
    table.add_column("Iterations", justify="right")
    
    for res in results:
        repo_name = res["name"]
        result_text = "[green]SUCCESS[/green]" if res["success"] else "[red]FAIL[/red]"
        # Format time nicely (minutes & seconds or seconds with one decimal)
        dur = res["duration_seconds"]
        if dur >= 60:
            mins = int(dur // 60)
            secs = int(dur % 60)
            time_str = f"{mins}m {secs}s"
        else:
            time_str = f"{dur:.1f}s" if dur < 10 else f"{int(dur)}s"
        table.add_row(repo_name, result_text, time_str, str(res["iterations"]))
    
    console.print("\n[bold underline]Summary of Runs[/bold underline]")
    console.print(table)
    
    # Print overall statistics
    total_runs = len(results)
    successful_runs = sum(1 for r in results if r["success"])
    total_time = sum(r["duration_seconds"] for r in results)
    console.print(f"\n[bold]Total runs:[/bold] {total_runs}")
    console.print(f"[bold]Successful:[/bold] {successful_runs}/{total_runs} ({successful_runs*100//total_runs}%)")
    console.print(f"[bold]Total time:[/bold] {total_time:.1f}s")
else:
    # Fallback to plain text summary
    print("\nSummary of Runs:")
    print(f"{'Repository':30} {'Result':>8} {'Time':>8} {'Iters':>7}")
    print("-" * 55)
    for res in results:
        name = res['name'][:30]  # truncate name if too long for display
        result_text = "SUCCESS" if res["success"] else "FAIL"
        dur = res["duration_seconds"]
        if dur >= 60:
            mins = int(dur // 60)
            secs = int(dur % 60)
            time_str = f"{mins}m{secs}s"
        else:
            time_str = f"{int(dur)}s"
        print(f"{name:30} {result_text:>8} {time_str:>8} {res['iterations']:>7}")
    
    # Print overall statistics
    total_runs = len(results)
    successful_runs = sum(1 for r in results if r["success"])
    total_time = sum(r["duration_seconds"] for r in results)
    print(f"\nTotal runs: {total_runs}")
    print(f"Successful: {successful_runs}/{total_runs} ({successful_runs*100//total_runs}%)")
    print(f"Total time: {total_time:.1f}s")

# Exit with 0 if all runs succeeded, or 1 if any run failed
sys.exit(1 if any_failure else 0)
