#!/usr/bin/env python3
"""
Nova Runner Wrapper - Provides unified interface for v1.0 and v1.1
Handles differences between legacy and Deep Agent implementations
"""

import os
import sys
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import yaml
import time


class NovaRunnerWrapper:
    """Wrapper to run Nova v1.0 or v1.1 with consistent interface"""
    
    def __init__(self, version: str, nova_cmd: str = None):
        """
        Initialize wrapper for specific Nova version
        
        Args:
            version: Version identifier ('v1_0' or 'v1_1')
            nova_cmd: Path to Nova command/script
        """
        self.version = version
        self.nova_cmd = nova_cmd or self._find_nova_cmd()
        self.is_legacy = version == "v1_0"
        self.is_deep_agent = version == "v1_1"
        
    def _find_nova_cmd(self) -> str:
        """Find Nova command based on version"""
        script_dir = Path(__file__).parent
        
        # Look for wrapper scripts
        if sys.platform == "win32":
            wrapper = script_dir / f"nova_{self.version}.bat"
        else:
            wrapper = script_dir / f"nova_{self.version}"
            
        if wrapper.exists():
            return str(wrapper)
            
        # Fall back to Python module
        if self.version == "v1_0":
            return f"{sys.executable} -m nova_v1_0"
        else:
            return f"{sys.executable} -m nova"
            
    def run_fix(self, 
                repo_path: str,
                max_iters: int = 6,
                timeout: int = 1200,
                verbose: bool = False,
                output_dir: Optional[str] = None,
                additional_args: List[str] = None) -> Dict[str, Any]:
        """
        Run Nova fix command on repository
        
        Args:
            repo_path: Path to repository
            max_iters: Maximum iterations
            timeout: Timeout in seconds
            verbose: Enable verbose output
            output_dir: Directory to save outputs
            additional_args: Additional CLI arguments
            
        Returns:
            Dict with results including success status, metrics, etc.
        """
        # Build command
        cmd = self._build_fix_command(
            repo_path, max_iters, timeout, verbose, additional_args
        )
        
        # Setup environment
        env = self._setup_environment()
        
        # Run command
        start_time = time.time()
        result = self._execute_command(cmd, env, timeout, repo_path)
        elapsed_time = time.time() - start_time
        
        # Parse results
        parsed_results = self._parse_fix_results(
            result, repo_path, elapsed_time, output_dir
        )
        
        return parsed_results
        
    def run_eval(self,
                config_path: str,
                output_dir: str,
                verbose: bool = False) -> Dict[str, Any]:
        """
        Run Nova eval command (batch evaluation)
        
        Args:
            config_path: Path to evaluation config YAML
            output_dir: Directory for results
            verbose: Enable verbose output
            
        Returns:
            Dict with evaluation results
        """
        # Check if eval mode is supported
        if not self._supports_eval_mode():
            # Fall back to individual runs
            return self._simulate_eval_mode(config_path, output_dir, verbose)
            
        # Build eval command
        cmd = self._build_eval_command(config_path, output_dir, verbose)
        
        # Setup environment
        env = self._setup_environment()
        
        # Run command
        result = self._execute_command(cmd, env, timeout=7200)
        
        # Parse results
        return self._parse_eval_results(result, output_dir)
        
    def _build_fix_command(self, 
                          repo_path: str,
                          max_iters: int,
                          timeout: int, 
                          verbose: bool,
                          additional_args: List[str]) -> List[str]:
        """Build Nova fix command"""
        cmd = []
        
        # Parse nova_cmd if it contains spaces
        if ' ' in self.nova_cmd:
            cmd.extend(self.nova_cmd.split())
        else:
            cmd.append(self.nova_cmd)
            
        # Add fix subcommand
        cmd.append("fix")
        
        # Add repository path
        cmd.append(repo_path)
        
        # Add options based on version
        if self.is_legacy:
            # v1.0 options
            cmd.extend(["--max-iterations", str(max_iters)])
            cmd.extend(["--timeout", str(timeout)])
            if verbose:
                cmd.append("--verbose")
        else:
            # v1.1 options
            cmd.extend(["--max-iters", str(max_iters)])
            cmd.extend(["--timeout", str(timeout)])
            if verbose:
                cmd.append("--verbose")
            # Enable Deep Agent for v1.1
            cmd.append("--use-deep-agent")
            
        # Add any additional arguments
        if additional_args:
            cmd.extend(additional_args)
            
        return cmd
        
    def _build_eval_command(self,
                          config_path: str,
                          output_dir: str,
                          verbose: bool) -> List[str]:
        """Build Nova eval command"""
        cmd = []
        
        # Parse nova_cmd
        if ' ' in self.nova_cmd:
            cmd.extend(self.nova_cmd.split())
        else:
            cmd.append(self.nova_cmd)
            
        # Add eval subcommand
        cmd.append("eval")
        
        # Add config path
        cmd.append(config_path)
        
        # Add output directory
        cmd.extend(["--output", output_dir])
        
        # Add verbose flag
        if verbose:
            cmd.append("--verbose")
            
        return cmd
        
    def _setup_environment(self) -> Dict[str, str]:
        """Setup environment variables"""
        env = os.environ.copy()
        
        # Set version-specific variables
        env["NOVA_VERSION"] = self.version
        env["NOVA_LOG_LEVEL"] = "INFO"
        
        if self.is_deep_agent:
            env["NOVA_USE_DEEP_AGENT"] = "true"
            
        # Ensure API keys are set if available
        for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"]:
            if key in os.environ:
                env[key] = os.environ[key]
                
        return env
        
    def _execute_command(self, 
                        cmd: List[str],
                        env: Dict[str, str],
                        timeout: int,
                        cwd: str = None) -> subprocess.CompletedProcess:
        """Execute command with timeout and capture output"""
        try:
            result = subprocess.run(
                cmd,
                env=env,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result
        except subprocess.TimeoutExpired as e:
            # Create a pseudo-result for timeout
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=-1,
                stdout=e.stdout or "",
                stderr=f"Command timed out after {timeout} seconds"
            )
        except Exception as e:
            # Create a pseudo-result for other errors
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=-2,
                stdout="",
                stderr=str(e)
            )
            
    def _parse_fix_results(self,
                         result: subprocess.CompletedProcess,
                         repo_path: str,
                         elapsed_time: float,
                         output_dir: Optional[str]) -> Dict[str, Any]:
        """Parse results from Nova fix command"""
        parsed = {
            "version": self.version,
            "command": " ".join(result.args),
            "exit_code": result.returncode,
            "elapsed_time": elapsed_time,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "status": "unknown",
            "success": False,
            "tests_fixed": 0,
            "iterations": 0,
            "max_iterations_reached": False,
            "timeout_occurred": False,
            "patches_applied": 0
        }
        
        # Determine status
        if result.returncode == -1:
            parsed["status"] = "timeout"
            parsed["timeout_occurred"] = True
        elif result.returncode == -2:
            parsed["status"] = "error"
        elif result.returncode == 0:
            parsed["status"] = "completed"
        else:
            parsed["status"] = "failed"
            
        # Parse output for metrics
        if result.stdout:
            parsed.update(self._extract_metrics_from_output(result.stdout))
            
        # Check for success indicators
        success_indicators = [
            "all tests passed",
            "all tests are passing",
            "✅ all tests passed",
            "success: all failing tests fixed"
        ]
        
        for indicator in success_indicators:
            if indicator.lower() in result.stdout.lower():
                parsed["success"] = True
                break
                
        # Get Nova artifacts if available
        nova_artifacts = self._collect_nova_artifacts(repo_path)
        if nova_artifacts:
            parsed["artifacts"] = nova_artifacts
            
            # Extract metrics from artifacts
            if "iterations" in nova_artifacts:
                parsed["iterations"] = nova_artifacts["iterations"]
            if "patches" in nova_artifacts:
                parsed["patches_applied"] = len(nova_artifacts["patches"])
                
        # Save outputs if directory specified
        if output_dir:
            self._save_outputs(parsed, output_dir)
            
        return parsed
        
    def _extract_metrics_from_output(self, output: str) -> Dict[str, Any]:
        """Extract metrics from Nova output"""
        metrics = {}
        
        import re
        
        # Extract iteration count
        iter_patterns = [
            r"iteration\s+(\d+)",
            r"iteration:\s*(\d+)",
            r"step\s+(\d+)",
            r"round\s+(\d+)"
        ]
        
        max_iter = 0
        for pattern in iter_patterns:
            matches = re.findall(pattern, output, re.IGNORECASE)
            if matches:
                max_iter = max(max_iter, max(int(m) for m in matches))
                
        if max_iter > 0:
            metrics["iterations"] = max_iter
            
        # Check for max iterations
        if "max iterations reached" in output.lower():
            metrics["max_iterations_reached"] = True
            
        # Extract test counts
        test_patterns = [
            r"(\d+)\s+tests?\s+fixed",
            r"fixed\s+(\d+)\s+tests?",
            r"(\d+)\s+failing\s+tests?\s+remaining",
            r"(\d+)\s+tests?\s+still\s+failing"
        ]
        
        for pattern in test_patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                metrics["tests_fixed"] = int(match.group(1))
                break
                
        return metrics
        
    def _collect_nova_artifacts(self, repo_path: str) -> Optional[Dict[str, Any]]:
        """Collect Nova artifacts from repository"""
        repo_path = Path(repo_path)
        nova_dir = repo_path / ".nova"
        
        if not nova_dir.exists():
            return None
            
        artifacts = {}
        
        # Find latest run directory
        run_dirs = sorted([d for d in nova_dir.iterdir() if d.is_dir()])
        if not run_dirs:
            return None
            
        latest_run = run_dirs[-1]
        
        # Collect patches
        diffs_dir = latest_run / "diffs"
        if diffs_dir.exists():
            patches = sorted(diffs_dir.glob("*.patch"))
            artifacts["patches"] = [p.name for p in patches]
            artifacts["iterations"] = len(patches)
            
        # Collect test reports
        reports_dir = latest_run / "reports"
        if reports_dir.exists():
            reports = sorted(reports_dir.glob("*.xml"))
            artifacts["test_reports"] = [r.name for r in reports]
            
        # Read trace if available
        trace_file = latest_run / "trace.jsonl"
        if trace_file.exists():
            artifacts["has_trace"] = True
            
            # Extract key events from trace
            try:
                events = []
                with open(trace_file, 'r') as f:
                    for line in f:
                        event = json.loads(line)
                        if event.get("type") in ["error", "success", "failure"]:
                            events.append(event)
                artifacts["key_events"] = events
            except:
                pass
                
        return artifacts
        
    def _save_outputs(self, results: Dict[str, Any], output_dir: str):
        """Save command outputs to files"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save stdout
        (output_path / "stdout.txt").write_text(results.get("stdout", ""))
        
        # Save stderr
        (output_path / "stderr.txt").write_text(results.get("stderr", ""))
        
        # Save parsed results
        with open(output_path / "results.json", 'w') as f:
            # Create serializable copy
            serializable = results.copy()
            # Remove non-serializable fields
            serializable.pop("stdout", None)
            serializable.pop("stderr", None)
            json.dump(serializable, f, indent=2)
            
    def _supports_eval_mode(self) -> bool:
        """Check if this version supports eval mode"""
        # Try to check if eval command exists
        test_cmd = []
        if ' ' in self.nova_cmd:
            test_cmd.extend(self.nova_cmd.split())
        else:
            test_cmd.append(self.nova_cmd)
            
        test_cmd.extend(["eval", "--help"])
        
        try:
            result = subprocess.run(
                test_cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0 or "eval" in result.stdout
        except:
            return False
            
    def _simulate_eval_mode(self,
                          config_path: str,
                          output_dir: str,
                          verbose: bool) -> Dict[str, Any]:
        """Simulate eval mode by running individual fixes"""
        # Load config
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        runs = config.get("runs", [])
        results = {
            "version": self.version,
            "mode": "simulated_eval",
            "test_results": {}
        }
        
        # Run each test case
        for run_config in runs:
            run_name = run_config.get("name", "unnamed")
            print(f"Running {run_name}...")
            
            # Get repository path
            if "path" in run_config:
                repo_path = run_config["path"]
            elif "url" in run_config:
                # Clone repository
                repo_path = self._clone_repo(
                    run_config["url"],
                    run_config.get("branch"),
                    output_dir
                )
            else:
                print(f"Skipping {run_name}: no path or URL")
                continue
                
            # Run fix
            fix_result = self.run_fix(
                repo_path=repo_path,
                max_iters=run_config.get("max_iters", 6),
                timeout=run_config.get("timeout", 1200),
                verbose=verbose,
                output_dir=Path(output_dir) / run_name
            )
            
            results["test_results"][run_name] = fix_result
            
        # Save combined results
        results_file = Path(output_dir) / "results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
            
        return results
        
    def _clone_repo(self, url: str, branch: Optional[str], base_dir: str) -> str:
        """Clone repository for testing"""
        import hashlib
        
        # Create unique directory name
        repo_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        repo_dir = Path(base_dir) / f"repo_{repo_hash}"
        
        if repo_dir.exists():
            shutil.rmtree(repo_dir)
            
        # Clone repository
        cmd = ["git", "clone", url, str(repo_dir)]
        if branch:
            cmd.extend(["-b", branch])
            
        subprocess.run(cmd, check=True, capture_output=True)
        
        return str(repo_dir)
        
    def _parse_eval_results(self,
                          result: subprocess.CompletedProcess,
                          output_dir: str) -> Dict[str, Any]:
        """Parse results from eval command"""
        parsed = {
            "version": self.version,
            "command": " ".join(result.args),
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "status": "completed" if result.returncode == 0 else "failed"
        }
        
        # Look for results.json
        results_file = Path(output_dir) / "results.json"
        if results_file.exists():
            with open(results_file, 'r') as f:
                eval_results = json.load(f)
                parsed["test_results"] = eval_results
                
        return parsed


# Convenience functions for direct usage
def run_nova_v1_0(repo_path: str, **kwargs) -> Dict[str, Any]:
    """Run Nova v1.0 on a repository"""
    wrapper = NovaRunnerWrapper("v1_0")
    return wrapper.run_fix(repo_path, **kwargs)
    

def run_nova_v1_1(repo_path: str, **kwargs) -> Dict[str, Any]:
    """Run Nova v1.1 on a repository"""
    wrapper = NovaRunnerWrapper("v1_1")
    return wrapper.run_fix(repo_path, **kwargs)


def compare_versions(repo_path: str, **kwargs) -> Dict[str, Any]:
    """Run both versions and compare results"""
    v1_0_results = run_nova_v1_0(repo_path, **kwargs)
    v1_1_results = run_nova_v1_1(repo_path, **kwargs)
    
    comparison = {
        "repository": repo_path,
        "v1_0": {
            "success": v1_0_results["success"],
            "iterations": v1_0_results["iterations"],
            "time": v1_0_results["elapsed_time"]
        },
        "v1_1": {
            "success": v1_1_results["success"],
            "iterations": v1_1_results["iterations"],
            "time": v1_1_results["elapsed_time"]
        }
    }
    
    # Determine winner
    if v1_1_results["success"] and not v1_0_results["success"]:
        comparison["winner"] = "v1_1"
    elif v1_0_results["success"] and not v1_1_results["success"]:
        comparison["winner"] = "v1_0"
        comparison["regression"] = True
    elif v1_0_results["success"] and v1_1_results["success"]:
        if v1_1_results["iterations"] < v1_0_results["iterations"]:
            comparison["winner"] = "v1_1_efficient"
        else:
            comparison["winner"] = "tie"
    else:
        comparison["winner"] = "both_failed"
        
    return comparison


if __name__ == "__main__":
    # Test wrapper functionality
    import argparse
    
    parser = argparse.ArgumentParser(description="Nova Runner Wrapper Test")
    parser.add_argument("repo", help="Repository path to test")
    parser.add_argument("--version", choices=["v1_0", "v1_1", "both"], 
                       default="both", help="Version to test")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.version == "both":
        results = compare_versions(args.repo, verbose=args.verbose)
        print(json.dumps(results, indent=2))
    else:
        wrapper = NovaRunnerWrapper(args.version)
        results = wrapper.run_fix(args.repo, verbose=args.verbose)
        print(f"Success: {results['success']}")
        print(f"Iterations: {results['iterations']}")
        print(f"Time: {results['elapsed_time']:.2f}s")
