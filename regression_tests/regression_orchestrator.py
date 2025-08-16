#!/usr/bin/env python3
"""
Nova CI-Rescue v1.1 Deep Agent Integration - Regression Test Orchestrator
Main script to run regression tests comparing v1.0 (legacy) vs v1.1 (Deep Agent)
"""

import os
import sys
import json
import subprocess
import time
import shutil
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import yaml
import tempfile
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('regression_tests.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RegressionTestOrchestrator:
    """Orchestrates regression testing between Nova v1.0 and v1.1"""
    
    def __init__(self, config_path: str, output_dir: str = "regression_results"):
        self.config_path = Path(config_path)
        self.output_dir = Path(output_dir)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results_dir = self.output_dir / self.timestamp
        
        # Create output directories
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Version-specific result directories
        self.v1_0_dir = self.results_dir / "v1_0"
        self.v1_1_dir = self.results_dir / "v1_1"
        self.v1_0_dir.mkdir(exist_ok=True)
        self.v1_1_dir.mkdir(exist_ok=True)
        
        # Load configuration
        self.config = self._load_config()
        
        # Results storage
        self.results = {
            "v1_0": {},
            "v1_1": {},
            "comparison": {},
            "summary": {}
        }
        
    def _load_config(self) -> Dict:
        """Load test configuration from YAML"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
            
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        # Validate config
        required_keys = ['nova_v1_0_cmd', 'nova_v1_1_cmd', 'runs']
        for key in required_keys:
            if key not in config:
                raise ValueError(f"Missing required config key: {key}")
                
        return config
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all regression tests"""
        logger.info(f"Starting regression tests at {self.timestamp}")
        logger.info(f"Results will be saved to: {self.results_dir}")
        
        # Run tests for v1.0
        logger.info("=" * 60)
        logger.info("Running Nova v1.0 (Legacy Agent) tests...")
        logger.info("=" * 60)
        self.results["v1_0"] = self._run_version_tests(
            version="v1_0",
            nova_cmd=self.config['nova_v1_0_cmd'],
            output_dir=self.v1_0_dir
        )
        
        # Run tests for v1.1
        logger.info("=" * 60)
        logger.info("Running Nova v1.1 (Deep Agent) tests...")
        logger.info("=" * 60)
        self.results["v1_1"] = self._run_version_tests(
            version="v1_1",
            nova_cmd=self.config['nova_v1_1_cmd'],
            output_dir=self.v1_1_dir
        )
        
        # Compare results
        logger.info("=" * 60)
        logger.info("Comparing results...")
        logger.info("=" * 60)
        self.results["comparison"] = self._compare_results()
        
        # Generate summary
        self.results["summary"] = self._generate_summary()
        
        # Save all results
        self._save_results()
        
        # Generate reports
        self._generate_reports()
        
        return self.results
        
    def _run_version_tests(self, version: str, nova_cmd: str, output_dir: Path) -> Dict:
        """Run tests for a specific Nova version"""
        version_results = {}
        
        # Check if using eval mode or individual runs
        use_eval_mode = self.config.get('use_eval_mode', True)
        
        if use_eval_mode:
            # Try to use nova eval command
            version_results = self._run_eval_mode(version, nova_cmd, output_dir)
        else:
            # Run individual test cases
            version_results = self._run_individual_mode(version, nova_cmd, output_dir)
            
        return version_results
        
    def _run_eval_mode(self, version: str, nova_cmd: str, output_dir: Path) -> Dict:
        """Run tests using Nova's eval mode"""
        logger.info(f"Running {version} in eval mode")
        
        # Create temporary config for this version
        eval_config = {
            "runs": self.config['runs']
        }
        
        config_file = output_dir / "eval_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(eval_config, f)
            
        # Run nova eval
        cmd = [nova_cmd, "eval", str(config_file), "--output", str(output_dir)]
        
        if self.config.get('verbose', False):
            cmd.append("--verbose")
            
        logger.info(f"Executing: {' '.join(cmd)}")
        
        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.get('global_timeout', 7200)  # 2 hour timeout
            )
            
            elapsed_time = time.time() - start_time
            
            # Parse results
            results_file = output_dir / "results.json"
            if results_file.exists():
                with open(results_file, 'r') as f:
                    eval_results = json.load(f)
            else:
                # Fall back to parsing output
                eval_results = self._parse_output(result.stdout, result.stderr)
                
            return {
                "status": "completed",
                "elapsed_time": elapsed_time,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "test_results": eval_results
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"{version} eval mode timed out after {self.config.get('global_timeout')} seconds")
            return {
                "status": "timeout",
                "elapsed_time": self.config.get('global_timeout'),
                "error": "Global timeout exceeded"
            }
        except Exception as e:
            logger.error(f"Error running {version} eval mode: {e}")
            return {
                "status": "error",
                "error": str(e),
                "traceback": traceback.format_exc()
            }
            
    def _run_individual_mode(self, version: str, nova_cmd: str, output_dir: Path) -> Dict:
        """Run tests individually for each repository"""
        logger.info(f"Running {version} in individual mode")
        
        results = {}
        
        for idx, run_config in enumerate(self.config['runs']):
            run_name = run_config.get('name', f'run_{idx}')
            logger.info(f"Running test case: {run_name}")
            
            # Prepare repository
            repo_path = self._prepare_repository(run_config, output_dir / run_name)
            
            if not repo_path:
                logger.error(f"Failed to prepare repository for {run_name}")
                results[run_name] = {"status": "error", "error": "Failed to prepare repository"}
                continue
                
            # Build command
            cmd = [nova_cmd, "fix", str(repo_path)]
            
            # Add optional parameters
            if 'max_iters' in run_config:
                cmd.extend(['--max-iters', str(run_config['max_iters'])])
            if 'timeout' in run_config:
                cmd.extend(['--timeout', str(run_config['timeout'])])
            if self.config.get('verbose', False):
                cmd.append('--verbose')
                
            # Run Nova
            logger.info(f"Executing: {' '.join(cmd)}")
            
            start_time = time.time()
            run_output_dir = output_dir / run_name
            run_output_dir.mkdir(exist_ok=True)
            
            try:
                # Get initial test status
                initial_failures = self._get_test_failures(repo_path)
                
                # Run Nova
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=str(repo_path),
                    timeout=run_config.get('timeout', 1200)
                )
                
                elapsed_time = time.time() - start_time
                
                # Get final test status
                final_failures = self._get_test_failures(repo_path)
                
                # Analyze results
                run_results = {
                    "status": "completed",
                    "elapsed_time": elapsed_time,
                    "exit_code": result.returncode,
                    "initial_failures": initial_failures,
                    "final_failures": final_failures,
                    "tests_fixed": len(initial_failures) - len(final_failures),
                    "success": len(final_failures) == 0,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
                
                # Extract iteration count and other metrics from output
                metrics = self._extract_metrics(result.stdout, result.stderr, repo_path)
                run_results.update(metrics)
                
                # Save outputs
                self._save_run_outputs(run_output_dir, run_results)
                
                # Copy Nova artifacts if they exist
                nova_dir = repo_path / ".nova"
                if nova_dir.exists():
                    shutil.copytree(nova_dir, run_output_dir / ".nova", dirs_exist_ok=True)
                    
                results[run_name] = run_results
                
            except subprocess.TimeoutExpired:
                logger.warning(f"{run_name} timed out")
                results[run_name] = {
                    "status": "timeout",
                    "elapsed_time": run_config.get('timeout', 1200),
                    "error": "Test timeout exceeded"
                }
            except Exception as e:
                logger.error(f"Error running {run_name}: {e}")
                results[run_name] = {
                    "status": "error",
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }
                
        return {
            "status": "completed",
            "test_results": results
        }
        
    def _prepare_repository(self, run_config: Dict, output_dir: Path) -> Optional[Path]:
        """Prepare repository for testing"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if 'path' in run_config:
            # Local repository
            src_path = Path(run_config['path'])
            if not src_path.exists():
                logger.error(f"Repository path does not exist: {src_path}")
                return None
                
            # Copy to test directory
            dest_path = output_dir / "repo"
            if dest_path.exists():
                shutil.rmtree(dest_path)
            shutil.copytree(src_path, dest_path)
            return dest_path
            
        elif 'url' in run_config:
            # Remote repository
            dest_path = output_dir / "repo"
            if dest_path.exists():
                shutil.rmtree(dest_path)
                
            # Clone repository
            cmd = ["git", "clone", run_config['url'], str(dest_path)]
            if 'branch' in run_config:
                cmd.extend(["-b", run_config['branch']])
                
            try:
                subprocess.run(cmd, check=True, capture_output=True)
                return dest_path
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to clone repository: {e}")
                return None
                
        else:
            logger.error("No repository path or URL specified")
            return None
            
    def _get_test_failures(self, repo_path: Path) -> List[str]:
        """Get list of failing tests in repository"""
        # Try to run tests and parse results
        # This is a simplified version - adjust based on your test framework
        
        test_cmd = ["pytest", "--tb=no", "-q", "--json-report", "--json-report-file=test_results.json"]
        
        try:
            result = subprocess.run(
                test_cmd,
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Parse test results
            results_file = repo_path / "test_results.json"
            if results_file.exists():
                with open(results_file, 'r') as f:
                    test_data = json.load(f)
                    failures = []
                    for test in test_data.get('tests', []):
                        if test.get('outcome') in ['failed', 'error']:
                            failures.append(test.get('nodeid', 'unknown'))
                    return failures
            else:
                # Parse from output
                failures = []
                for line in result.stdout.split('\n'):
                    if 'FAILED' in line or 'ERROR' in line:
                        failures.append(line.strip())
                return failures
                
        except Exception as e:
            logger.warning(f"Could not get test failures: {e}")
            return []
            
    def _extract_metrics(self, stdout: str, stderr: str, repo_path: Path) -> Dict:
        """Extract metrics from Nova output"""
        metrics = {
            "iterations": 0,
            "patches_applied": 0,
            "max_iterations_reached": False,
            "timeout_occurred": False
        }
        
        # Parse stdout for iteration count
        for line in stdout.split('\n'):
            if 'iteration' in line.lower():
                # Try to extract iteration number
                import re
                match = re.search(r'iteration\s+(\d+)', line, re.IGNORECASE)
                if match:
                    metrics["iterations"] = max(metrics["iterations"], int(match.group(1)))
                    
            if 'max iterations reached' in line.lower():
                metrics["max_iterations_reached"] = True
                
            if 'timeout' in line.lower():
                metrics["timeout_occurred"] = True
                
        # Count patches in .nova directory
        nova_dir = repo_path / ".nova"
        if nova_dir.exists():
            # Find latest run directory
            run_dirs = sorted([d for d in nova_dir.iterdir() if d.is_dir()])
            if run_dirs:
                latest_run = run_dirs[-1]
                diffs_dir = latest_run / "diffs"
                if diffs_dir.exists():
                    patches = list(diffs_dir.glob("*.patch"))
                    metrics["patches_applied"] = len(patches)
                    
        return metrics
        
    def _save_run_outputs(self, output_dir: Path, results: Dict):
        """Save run outputs to files"""
        # Save stdout
        with open(output_dir / "stdout.txt", 'w') as f:
            f.write(results.get('stdout', ''))
            
        # Save stderr
        with open(output_dir / "stderr.txt", 'w') as f:
            f.write(results.get('stderr', ''))
            
        # Save results JSON
        with open(output_dir / "results.json", 'w') as f:
            json.dump(results, f, indent=2)
            
    def _parse_output(self, stdout: str, stderr: str) -> Dict:
        """Parse Nova output when results.json is not available"""
        # This is a fallback parser - implement based on actual output format
        results = {}
        
        # Look for summary table or success indicators
        lines = stdout.split('\n')
        for line in lines:
            if 'success' in line.lower() or 'fixed' in line.lower():
                # Try to extract test case name and result
                pass
                
        return results
        
    def _compare_results(self) -> Dict:
        """Compare v1.0 and v1.1 results"""
        comparison = {}
        
        v1_0_results = self.results.get("v1_0", {}).get("test_results", {})
        v1_1_results = self.results.get("v1_1", {}).get("test_results", {})
        
        all_test_names = set(v1_0_results.keys()) | set(v1_1_results.keys())
        
        for test_name in all_test_names:
            v1_0_test = v1_0_results.get(test_name, {})
            v1_1_test = v1_1_results.get(test_name, {})
            
            comparison[test_name] = {
                "v1_0": {
                    "success": v1_0_test.get("success", False),
                    "tests_fixed": v1_0_test.get("tests_fixed", 0),
                    "iterations": v1_0_test.get("iterations", 0),
                    "elapsed_time": v1_0_test.get("elapsed_time", 0),
                    "status": v1_0_test.get("status", "not_run")
                },
                "v1_1": {
                    "success": v1_1_test.get("success", False),
                    "tests_fixed": v1_1_test.get("tests_fixed", 0),
                    "iterations": v1_1_test.get("iterations", 0),
                    "elapsed_time": v1_1_test.get("elapsed_time", 0),
                    "status": v1_1_test.get("status", "not_run")
                }
            }
            
            # Determine comparison outcome
            v1_0_success = v1_0_test.get("success", False)
            v1_1_success = v1_1_test.get("success", False)
            
            if v1_1_success and not v1_0_success:
                comparison[test_name]["outcome"] = "v1_1_better"
            elif v1_0_success and not v1_1_success:
                comparison[test_name]["outcome"] = "v1_0_better"
                comparison[test_name]["regression"] = True
            elif v1_0_success and v1_1_success:
                # Both succeeded, compare efficiency
                if v1_1_test.get("iterations", 0) < v1_0_test.get("iterations", 0):
                    comparison[test_name]["outcome"] = "v1_1_more_efficient"
                elif v1_1_test.get("iterations", 0) > v1_0_test.get("iterations", 0):
                    comparison[test_name]["outcome"] = "v1_0_more_efficient"
                else:
                    comparison[test_name]["outcome"] = "equal"
            else:
                comparison[test_name]["outcome"] = "both_failed"
                
        return comparison
        
    def _generate_summary(self) -> Dict:
        """Generate summary statistics"""
        v1_0_results = self.results.get("v1_0", {}).get("test_results", {})
        v1_1_results = self.results.get("v1_1", {}).get("test_results", {})
        comparison = self.results.get("comparison", {})
        
        # Count successes
        v1_0_successes = sum(1 for r in v1_0_results.values() if r.get("success", False))
        v1_1_successes = sum(1 for r in v1_1_results.values() if r.get("success", False))
        
        total_tests = len(comparison)
        
        # Count regressions
        regressions = sum(1 for c in comparison.values() if c.get("regression", False))
        improvements = sum(1 for c in comparison.values() if c.get("outcome") == "v1_1_better")
        
        # Calculate averages
        v1_0_avg_time = sum(r.get("elapsed_time", 0) for r in v1_0_results.values()) / max(len(v1_0_results), 1)
        v1_1_avg_time = sum(r.get("elapsed_time", 0) for r in v1_1_results.values()) / max(len(v1_1_results), 1)
        
        v1_0_avg_iters = sum(r.get("iterations", 0) for r in v1_0_results.values()) / max(len(v1_0_results), 1)
        v1_1_avg_iters = sum(r.get("iterations", 0) for r in v1_1_results.values()) / max(len(v1_1_results), 1)
        
        summary = {
            "total_tests": total_tests,
            "v1_0": {
                "successes": v1_0_successes,
                "failures": total_tests - v1_0_successes,
                "success_rate": (v1_0_successes / total_tests * 100) if total_tests > 0 else 0,
                "avg_time": v1_0_avg_time,
                "avg_iterations": v1_0_avg_iters
            },
            "v1_1": {
                "successes": v1_1_successes,
                "failures": total_tests - v1_1_successes,
                "success_rate": (v1_1_successes / total_tests * 100) if total_tests > 0 else 0,
                "avg_time": v1_1_avg_time,
                "avg_iterations": v1_1_avg_iters
            },
            "comparison": {
                "regressions": regressions,
                "improvements": improvements,
                "no_change": total_tests - regressions - improvements,
                "meets_criteria": (v1_1_successes / total_tests * 100) >= 70 if total_tests > 0 else False
            },
            "timestamp": self.timestamp,
            "recommendation": self._generate_recommendation(v1_0_successes, v1_1_successes, regressions, total_tests)
        }
        
        return summary
        
    def _generate_recommendation(self, v1_0_successes: int, v1_1_successes: int, 
                                regressions: int, total_tests: int) -> str:
        """Generate recommendation based on results"""
        if total_tests == 0:
            return "No tests run - cannot make recommendation"
            
        v1_1_success_rate = (v1_1_successes / total_tests * 100)
        
        if regressions > 0:
            return f"CAUTION: v1.1 has {regressions} regression(s). Investigation needed before adoption."
        elif v1_1_success_rate >= 70 and v1_1_successes >= v1_0_successes:
            return f"RECOMMENDED: v1.1 meets all criteria ({v1_1_success_rate:.1f}% success rate). Safe to consolidate to Deep Agent."
        elif v1_1_success_rate < 70:
            return f"NOT RECOMMENDED: v1.1 success rate ({v1_1_success_rate:.1f}%) below 70% threshold."
        else:
            return "NEEDS REVIEW: Mixed results require further analysis."
            
    def _save_results(self):
        """Save all results to JSON"""
        results_file = self.results_dir / "regression_results.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        logger.info(f"Results saved to: {results_file}")
        
    def _generate_reports(self):
        """Generate human-readable reports"""
        # Generate Markdown report
        from regression_report_generator import ReportGenerator
        
        generator = ReportGenerator(self.results, self.results_dir)
        report_path = generator.generate_markdown_report()
        logger.info(f"Markdown report generated: {report_path}")
        
        # Generate comparison chart
        chart_path = generator.generate_comparison_chart()
        if chart_path:
            logger.info(f"Comparison chart generated: {chart_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Nova CI-Rescue Regression Test Orchestrator"
    )
    parser.add_argument(
        "config",
        help="Path to test configuration YAML file"
    )
    parser.add_argument(
        "--output",
        default="regression_results",
        help="Output directory for results"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Run tests
    orchestrator = RegressionTestOrchestrator(args.config, args.output)
    results = orchestrator.run_all_tests()
    
    # Print summary
    summary = results.get("summary", {})
    print("\n" + "=" * 60)
    print("REGRESSION TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {summary.get('total_tests', 0)}")
    print(f"v1.0 Success Rate: {summary.get('v1_0', {}).get('success_rate', 0):.1f}%")
    print(f"v1.1 Success Rate: {summary.get('v1_1', {}).get('success_rate', 0):.1f}%")
    print(f"Regressions: {summary.get('comparison', {}).get('regressions', 0)}")
    print(f"Improvements: {summary.get('comparison', {}).get('improvements', 0)}")
    print(f"\nRecommendation: {summary.get('recommendation', 'Unknown')}")
    print("=" * 60)
    
    # Exit with appropriate code
    if summary.get("comparison", {}).get("regressions", 0) > 0:
        sys.exit(1)  # Failure - regressions detected
    elif summary.get("comparison", {}).get("meets_criteria", False):
        sys.exit(0)  # Success
    else:
        sys.exit(2)  # Does not meet criteria


if __name__ == "__main__":
    main()
