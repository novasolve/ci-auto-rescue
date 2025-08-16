#!/usr/bin/env python3
"""
Validation and Verification Script for Nova CI-Rescue Regression Tests
Analyzes results and determines if v1.1 meets criteria for adoption
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime
import argparse


class RegressionValidator:
    """Validate regression test results against success criteria"""
    
    def __init__(self, results_file: str):
        self.results_file = Path(results_file)
        self.results = self._load_results()
        
        # Success criteria
        self.MIN_SUCCESS_RATE = 70.0  # Minimum 70% success rate
        self.MAX_REGRESSIONS = 0      # No regressions allowed
        self.REQUIRED_EDGE_CASES = [  # Edge cases that must pass
            "edge_no_failures",
            "edge_patch_conflict", 
            "edge_timeout"
        ]
        
    def _load_results(self) -> Dict:
        """Load regression test results"""
        if not self.results_file.exists():
            raise FileNotFoundError(f"Results file not found: {self.results_file}")
            
        with open(self.results_file, 'r') as f:
            return json.load(f)
            
    def validate_all(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Run all validation checks
        
        Returns:
            Tuple of (success, validation_report)
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "results_file": str(self.results_file),
            "checks": {},
            "summary": {},
            "recommendation": None,
            "all_criteria_met": False
        }
        
        # Run validation checks
        checks_passed = []
        
        # Check 1: Success rate
        success_rate_check = self.check_success_rate()
        report["checks"]["success_rate"] = success_rate_check
        checks_passed.append(success_rate_check["passed"])
        
        # Check 2: No regressions
        regression_check = self.check_regressions()
        report["checks"]["regressions"] = regression_check
        checks_passed.append(regression_check["passed"])
        
        # Check 3: Performance comparison
        performance_check = self.check_performance()
        report["checks"]["performance"] = performance_check
        checks_passed.append(performance_check["passed"])
        
        # Check 4: Edge cases
        edge_case_check = self.check_edge_cases()
        report["checks"]["edge_cases"] = edge_case_check
        checks_passed.append(edge_case_check["passed"])
        
        # Check 5: Stability
        stability_check = self.check_stability()
        report["checks"]["stability"] = stability_check
        checks_passed.append(stability_check["passed"])
        
        # Overall result
        all_passed = all(checks_passed)
        report["all_criteria_met"] = all_passed
        
        # Generate summary
        report["summary"] = self.generate_summary()
        
        # Generate recommendation
        report["recommendation"] = self.generate_recommendation(all_passed, report["checks"])
        
        return all_passed, report
        
    def check_success_rate(self) -> Dict[str, Any]:
        """Check if v1.1 meets minimum success rate"""
        summary = self.results.get("summary", {})
        v1_1_stats = summary.get("v1_1", {})
        
        success_rate = v1_1_stats.get("success_rate", 0)
        
        return {
            "name": "Success Rate Check",
            "description": f"v1.1 must achieve ≥{self.MIN_SUCCESS_RATE}% success rate",
            "target": self.MIN_SUCCESS_RATE,
            "actual": success_rate,
            "passed": success_rate >= self.MIN_SUCCESS_RATE,
            "details": {
                "total_tests": summary.get("total_tests", 0),
                "successes": v1_1_stats.get("successes", 0),
                "failures": v1_1_stats.get("failures", 0)
            }
        }
        
    def check_regressions(self) -> Dict[str, Any]:
        """Check for regressions where v1.1 fails but v1.0 succeeds"""
        comparison = self.results.get("comparison", {})
        
        regressions = []
        for test_name, comp in comparison.items():
            if comp.get("regression", False) or comp.get("outcome") == "v1_0_better":
                regressions.append({
                    "test": test_name,
                    "v1_0_success": comp.get("v1_0", {}).get("success", False),
                    "v1_1_success": comp.get("v1_1", {}).get("success", False)
                })
                
        return {
            "name": "Regression Check",
            "description": f"v1.1 must have ≤{self.MAX_REGRESSIONS} regressions",
            "target": self.MAX_REGRESSIONS,
            "actual": len(regressions),
            "passed": len(regressions) <= self.MAX_REGRESSIONS,
            "regressions": regressions
        }
        
    def check_performance(self) -> Dict[str, Any]:
        """Check performance metrics comparison"""
        summary = self.results.get("summary", {})
        v1_0_stats = summary.get("v1_0", {})
        v1_1_stats = summary.get("v1_1", {})
        
        # Compare average time and iterations
        time_delta = v1_1_stats.get("avg_time", 0) - v1_0_stats.get("avg_time", 0)
        iter_delta = v1_1_stats.get("avg_iterations", 0) - v1_0_stats.get("avg_iterations", 0)
        
        # Allow some performance degradation (e.g., 20% slower is acceptable)
        MAX_TIME_DEGRADATION = 1.2  # 20% slower
        MAX_ITER_DEGRADATION = 1.5  # 50% more iterations
        
        time_ratio = (v1_1_stats.get("avg_time", 1) / 
                     max(v1_0_stats.get("avg_time", 1), 0.01))
        iter_ratio = (v1_1_stats.get("avg_iterations", 1) / 
                     max(v1_0_stats.get("avg_iterations", 1), 0.01))
        
        return {
            "name": "Performance Check",
            "description": "v1.1 performance should be comparable to v1.0",
            "metrics": {
                "time": {
                    "v1_0_avg": v1_0_stats.get("avg_time", 0),
                    "v1_1_avg": v1_1_stats.get("avg_time", 0),
                    "delta": time_delta,
                    "ratio": time_ratio,
                    "acceptable": time_ratio <= MAX_TIME_DEGRADATION
                },
                "iterations": {
                    "v1_0_avg": v1_0_stats.get("avg_iterations", 0),
                    "v1_1_avg": v1_1_stats.get("avg_iterations", 0),
                    "delta": iter_delta,
                    "ratio": iter_ratio,
                    "acceptable": iter_ratio <= MAX_ITER_DEGRADATION
                }
            },
            "passed": (time_ratio <= MAX_TIME_DEGRADATION and 
                      iter_ratio <= MAX_ITER_DEGRADATION)
        }
        
    def check_edge_cases(self) -> Dict[str, Any]:
        """Check if required edge cases are handled properly"""
        comparison = self.results.get("comparison", {})
        
        edge_case_results = {}
        all_passed = True
        
        for edge_case in self.REQUIRED_EDGE_CASES:
            if edge_case in comparison:
                comp = comparison[edge_case]
                v1_1_status = comp.get("v1_1", {}).get("status", "unknown")
                
                # Edge case passes if v1.1 handles it at least as well as v1.0
                v1_0_handled = comp.get("v1_0", {}).get("status") in ["completed", "timeout"]
                v1_1_handled = v1_1_status in ["completed", "timeout"]
                
                passed = v1_1_handled or (not v1_0_handled and not v1_1_handled)
                
                edge_case_results[edge_case] = {
                    "v1_0_status": comp.get("v1_0", {}).get("status", "unknown"),
                    "v1_1_status": v1_1_status,
                    "passed": passed
                }
                
                if not passed:
                    all_passed = False
            else:
                edge_case_results[edge_case] = {
                    "error": "Test case not found in results",
                    "passed": False
                }
                all_passed = False
                
        return {
            "name": "Edge Case Check",
            "description": "Required edge cases must be handled properly",
            "required_cases": self.REQUIRED_EDGE_CASES,
            "results": edge_case_results,
            "passed": all_passed
        }
        
    def check_stability(self) -> Dict[str, Any]:
        """Check for crashes, timeouts, and other stability issues"""
        comparison = self.results.get("comparison", {})
        
        stability_issues = []
        
        for test_name, comp in comparison.items():
            v1_1_status = comp.get("v1_1", {}).get("status", "unknown")
            
            # Check for errors or crashes
            if v1_1_status == "error":
                stability_issues.append({
                    "test": test_name,
                    "issue": "error/crash",
                    "status": v1_1_status
                })
                
        # Calculate error rate
        total_tests = len(comparison)
        error_rate = (len(stability_issues) / total_tests * 100) if total_tests > 0 else 0
        
        # Allow up to 5% error rate
        MAX_ERROR_RATE = 5.0
        
        return {
            "name": "Stability Check",
            "description": "v1.1 must be stable with minimal crashes",
            "max_error_rate": MAX_ERROR_RATE,
            "actual_error_rate": error_rate,
            "issues": stability_issues,
            "passed": error_rate <= MAX_ERROR_RATE
        }
        
    def generate_summary(self) -> Dict[str, Any]:
        """Generate summary of validation results"""
        summary = self.results.get("summary", {})
        comparison_stats = summary.get("comparison", {})
        
        return {
            "total_tests": summary.get("total_tests", 0),
            "v1_0_success_rate": summary.get("v1_0", {}).get("success_rate", 0),
            "v1_1_success_rate": summary.get("v1_1", {}).get("success_rate", 0),
            "regressions": comparison_stats.get("regressions", 0),
            "improvements": comparison_stats.get("improvements", 0),
            "no_change": comparison_stats.get("no_change", 0)
        }
        
    def generate_recommendation(self, all_passed: bool, checks: Dict) -> Dict[str, Any]:
        """Generate final recommendation based on validation results"""
        if all_passed:
            return {
                "decision": "ADOPT",
                "confidence": "HIGH",
                "message": "✅ Nova v1.1 with Deep Agent meets all criteria and is ready for adoption",
                "next_steps": [
                    "Merge v1.1 Deep Agent to main branch",
                    "Deprecate v1.0 legacy agent",
                    "Update documentation",
                    "Release v1.1 as default"
                ]
            }
            
        # Analyze which checks failed
        failed_checks = [name for name, check in checks.items() if not check.get("passed", False)]
        
        if "regressions" in failed_checks:
            return {
                "decision": "REJECT",
                "confidence": "HIGH",
                "message": "❌ Nova v1.1 has regressions that must be fixed before adoption",
                "failed_checks": failed_checks,
                "next_steps": [
                    "Investigate and fix all regressions",
                    "Re-run regression tests after fixes",
                    "Do not proceed with adoption until regressions are resolved"
                ]
            }
            
        if "success_rate" in failed_checks:
            return {
                "decision": "REJECT",
                "confidence": "HIGH",
                "message": "❌ Nova v1.1 does not meet minimum success rate requirement",
                "failed_checks": failed_checks,
                "next_steps": [
                    "Improve Deep Agent to handle more test scenarios",
                    "Consider incorporating techniques from Harrison Chase's deepagents",
                    "Re-test after improvements"
                ]
            }
            
        # Some checks failed but not critical ones
        return {
            "decision": "CONDITIONAL",
            "confidence": "MEDIUM",
            "message": "⚠️ Nova v1.1 shows promise but needs improvements in some areas",
            "failed_checks": failed_checks,
            "next_steps": [
                "Address failed checks",
                "Consider gradual rollout with feature flags",
                "Monitor performance in production",
                "Keep v1.0 as fallback option"
            ]
        }


def validate_and_decide(results_file: str, output_file: str = None) -> bool:
    """
    Main validation function
    
    Args:
        results_file: Path to regression test results JSON
        output_file: Optional path to save validation report
        
    Returns:
        True if all criteria met, False otherwise
    """
    validator = RegressionValidator(results_file)
    
    print("=" * 60)
    print("Nova CI-Rescue v1.1 Regression Test Validation")
    print("=" * 60)
    
    # Run validation
    all_passed, report = validator.validate_all()
    
    # Print results
    print(f"\n📊 Summary:")
    print(f"  Total Tests: {report['summary']['total_tests']}")
    print(f"  v1.0 Success Rate: {report['summary']['v1_0_success_rate']:.1f}%")
    print(f"  v1.1 Success Rate: {report['summary']['v1_1_success_rate']:.1f}%")
    print(f"  Regressions: {report['summary']['regressions']}")
    print(f"  Improvements: {report['summary']['improvements']}")
    
    print(f"\n✓ Validation Checks:")
    for check_name, check in report["checks"].items():
        status = "✅" if check["passed"] else "❌"
        print(f"  {status} {check['name']}")
        
    print(f"\n📋 Recommendation:")
    rec = report["recommendation"]
    print(f"  Decision: {rec['decision']}")
    print(f"  Confidence: {rec['confidence']}")
    print(f"  {rec['message']}")
    
    if rec.get("next_steps"):
        print(f"\n  Next Steps:")
        for step in rec["next_steps"]:
            print(f"    - {step}")
            
    # Save report if requested
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n💾 Validation report saved to: {output_file}")
        
    return all_passed


def compare_with_deepagents() -> Dict[str, Any]:
    """
    Compare our Deep Agent with Harrison Chase's deepagents framework
    This provides guidance on whether to switch implementations
    """
    comparison = {
        "framework": "Harrison Chase's DeepAgents",
        "url": "https://github.com/langchain-ai/deepagents",
        "comparison_date": datetime.now().isoformat(),
        "analysis": {}
    }
    
    # Key features of deepagents
    deepagents_features = {
        "multi_step_planning": "Advanced planning with sub-goals",
        "agent_orchestration": "Multiple specialized sub-agents",
        "claude_code_inspired": "Based on Claude's coding patterns",
        "structured_reasoning": "Formal reasoning chains",
        "tool_integration": "Rich tool ecosystem"
    }
    
    # Our implementation features
    our_features = {
        "multi_step_planning": "Iterative plan-act-reflect loop",
        "agent_orchestration": "Single unified Deep Agent",
        "custom_tailored": "Optimized for test fixing",
        "structured_reasoning": "Critic-actor pattern",
        "tool_integration": "Custom tools for Nova use case"
    }
    
    comparison["analysis"] = {
        "deepagents_strengths": [
            "More general-purpose and flexible",
            "Better for complex multi-agent scenarios",
            "Stronger planning capabilities",
            "Active community and updates"
        ],
        "our_strengths": [
            "Tailored specifically for test fixing",
            "Simpler and more maintainable",
            "Already integrated with Nova",
            "Proven through regression testing"
        ],
        "recommendation": (
            "Stay with in-house implementation if regression tests pass. "
            "Consider adopting specific techniques from deepagents "
            "(e.g., planning algorithms) without full replacement."
        )
    }
    
    return comparison


def main():
    parser = argparse.ArgumentParser(
        description="Validate Nova CI-Rescue regression test results"
    )
    parser.add_argument(
        "results_file",
        help="Path to regression test results JSON file"
    )
    parser.add_argument(
        "--output",
        help="Path to save validation report",
        default=None
    )
    parser.add_argument(
        "--compare-deepagents",
        action="store_true",
        help="Include comparison with Harrison Chase's deepagents"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Use strict validation (no tolerance for any failures)"
    )
    
    args = parser.parse_args()
    
    # Run validation
    passed = validate_and_decide(args.results_file, args.output)
    
    # Compare with deepagents if requested
    if args.compare_deepagents:
        print("\n" + "=" * 60)
        print("DeepAgents Framework Comparison")
        print("=" * 60)
        
        comparison = compare_with_deepagents()
        print(f"\nFramework: {comparison['framework']}")
        print(f"URL: {comparison['url']}")
        print(f"\nRecommendation: {comparison['analysis']['recommendation']}")
        
    # Exit with appropriate code
    if passed:
        print("\n✅ All validation criteria met!")
        sys.exit(0)
    else:
        print("\n❌ Validation failed - criteria not met")
        sys.exit(1)


if __name__ == "__main__":
    main()
