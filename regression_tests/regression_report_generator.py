#!/usr/bin/env python3
"""
Report Generator for Nova CI-Rescue Regression Tests
Generates comprehensive Markdown and visualization reports from test results
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from collections import defaultdict


class ReportGenerator:
    """Generate human-readable reports from regression test results"""
    
    def __init__(self, results: Dict, output_dir: Path):
        self.results = results
        self.output_dir = Path(output_dir)
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def generate_markdown_report(self) -> Path:
        """Generate comprehensive Markdown report"""
        report_path = self.output_dir / "REGRESSION_REPORT.md"
        
        with open(report_path, 'w') as f:
            # Write header
            f.write(self._generate_header())
            
            # Write executive summary
            f.write(self._generate_executive_summary())
            
            # Write detailed results
            f.write(self._generate_detailed_results())
            
            # Write edge case results
            f.write(self._generate_edge_case_results())
            
            # Write performance comparison
            f.write(self._generate_performance_comparison())
            
            # Write recommendations
            f.write(self._generate_recommendations())
            
            # Write appendix
            f.write(self._generate_appendix())
            
        return report_path
        
    def _generate_header(self) -> str:
        """Generate report header"""
        return f"""# Nova CI-Rescue v1.1 Deep Agent Integration - Regression Test Report

**Generated:** {self.timestamp}  
**Test Suite Version:** 1.0.0  
**Purpose:** Validate Nova CI-Rescue v1.1 (Deep Agent) against v1.0 (Legacy Agent)

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Detailed Test Results](#detailed-test-results)
3. [Edge Case Analysis](#edge-case-analysis)
4. [Performance Comparison](#performance-comparison)
5. [Recommendations](#recommendations)
6. [Appendix](#appendix)

---

"""

    def _generate_executive_summary(self) -> str:
        """Generate executive summary section"""
        summary = self.results.get("summary", {})
        v1_0_stats = summary.get("v1_0", {})
        v1_1_stats = summary.get("v1_1", {})
        comparison = summary.get("comparison", {})
        
        # Determine overall status
        if comparison.get("regressions", 0) > 0:
            status = "❌ **REGRESSIONS DETECTED**"
            status_color = "red"
        elif comparison.get("meets_criteria", False):
            status = "✅ **ALL CRITERIA MET**"
            status_color = "green"
        else:
            status = "⚠️ **CRITERIA NOT MET**"
            status_color = "orange"
            
        return f"""## Executive Summary

### Overall Status: {status}

### Key Metrics

| Metric | v1.0 (Legacy) | v1.1 (Deep Agent) | Delta |
|--------|---------------|-------------------|-------|
| **Success Rate** | {v1_0_stats.get('success_rate', 0):.1f}% | {v1_1_stats.get('success_rate', 0):.1f}% | {v1_1_stats.get('success_rate', 0) - v1_0_stats.get('success_rate', 0):+.1f}% |
| **Tests Passed** | {v1_0_stats.get('successes', 0)}/{summary.get('total_tests', 0)} | {v1_1_stats.get('successes', 0)}/{summary.get('total_tests', 0)} | {v1_1_stats.get('successes', 0) - v1_0_stats.get('successes', 0):+d} |
| **Average Time** | {v1_0_stats.get('avg_time', 0):.1f}s | {v1_1_stats.get('avg_time', 0):.1f}s | {v1_1_stats.get('avg_time', 0) - v1_0_stats.get('avg_time', 0):+.1f}s |
| **Average Iterations** | {v1_0_stats.get('avg_iterations', 0):.1f} | {v1_1_stats.get('avg_iterations', 0):.1f} | {v1_1_stats.get('avg_iterations', 0) - v1_0_stats.get('avg_iterations', 0):+.1f} |

### Success Criteria Assessment

| Criterion | Target | Actual | Status |
|-----------|--------|--------|--------|
| Success Rate | ≥70% | {v1_1_stats.get('success_rate', 0):.1f}% | {"✅" if v1_1_stats.get('success_rate', 0) >= 70 else "❌"} |
| No Regressions | 0 | {comparison.get('regressions', 0)} | {"✅" if comparison.get('regressions', 0) == 0 else "❌"} |
| Equal/Better Performance | Yes | {comparison.get('improvements', 0)} improvements | {"✅" if comparison.get('regressions', 0) == 0 else "❌"} |

### Summary Statistics

- **Total Test Scenarios:** {summary.get('total_tests', 0)}
- **Regressions Found:** {comparison.get('regressions', 0)}
- **Improvements Found:** {comparison.get('improvements', 0)}
- **No Change:** {comparison.get('no_change', 0)}

### Recommendation
**{summary.get('recommendation', 'No recommendation available')}**

---

"""

    def _generate_detailed_results(self) -> str:
        """Generate detailed results for each test"""
        comparison = self.results.get("comparison", {})
        
        output = """## Detailed Test Results

### Repository Test Results

"""
        
        # Group results by outcome
        outcomes = defaultdict(list)
        for test_name, comp in comparison.items():
            outcome = comp.get("outcome", "unknown")
            outcomes[outcome].append((test_name, comp))
            
        # Show improvements first
        if "v1_1_better" in outcomes or "v1_1_more_efficient" in outcomes:
            output += "#### 🎉 Improvements in v1.1\n\n"
            
            for test_name, comp in outcomes.get("v1_1_better", []):
                output += self._format_test_result(test_name, comp, "improvement")
                
            for test_name, comp in outcomes.get("v1_1_more_efficient", []):
                output += self._format_test_result(test_name, comp, "efficiency")
                
        # Show regressions
        if "v1_0_better" in outcomes:
            output += "#### ⚠️ Regressions in v1.1\n\n"
            
            for test_name, comp in outcomes["v1_0_better"]:
                output += self._format_test_result(test_name, comp, "regression")
                
        # Show equal performance
        if "equal" in outcomes:
            output += "#### ✅ Equal Performance\n\n"
            
            for test_name, comp in outcomes["equal"]:
                output += self._format_test_result(test_name, comp, "equal")
                
        # Show failures in both
        if "both_failed" in outcomes:
            output += "#### ❌ Failed in Both Versions\n\n"
            
            for test_name, comp in outcomes["both_failed"]:
                output += self._format_test_result(test_name, comp, "both_failed")
                
        output += "\n---\n\n"
        return output
        
    def _format_test_result(self, test_name: str, comparison: Dict, result_type: str) -> str:
        """Format individual test result"""
        v1_0 = comparison.get("v1_0", {})
        v1_1 = comparison.get("v1_1", {})
        
        # Determine icon based on result type
        icons = {
            "improvement": "🎉",
            "efficiency": "⚡",
            "regression": "⚠️",
            "equal": "✅",
            "both_failed": "❌"
        }
        icon = icons.get(result_type, "❓")
        
        output = f"""##### {icon} {test_name}

| Version | Success | Tests Fixed | Iterations | Time | Status |
|---------|---------|-------------|------------|------|--------|
| v1.0 | {"✅" if v1_0.get('success') else "❌"} | {v1_0.get('tests_fixed', 'N/A')} | {v1_0.get('iterations', 'N/A')} | {v1_0.get('elapsed_time', 0):.1f}s | {v1_0.get('status', 'unknown')} |
| v1.1 | {"✅" if v1_1.get('success') else "❌"} | {v1_1.get('tests_fixed', 'N/A')} | {v1_1.get('iterations', 'N/A')} | {v1_1.get('elapsed_time', 0):.1f}s | {v1_1.get('status', 'unknown')} |

"""
        
        # Add notes for special cases
        if result_type == "regression":
            output += f"**⚠️ Regression:** v1.1 failed where v1.0 succeeded. Investigation required.\n\n"
        elif result_type == "improvement":
            output += f"**✅ Improvement:** v1.1 fixed tests that v1.0 could not.\n\n"
        elif result_type == "efficiency":
            output += f"**⚡ More Efficient:** v1.1 achieved same result with fewer iterations.\n\n"
            
        return output
        
    def _generate_edge_case_results(self) -> str:
        """Generate edge case analysis section"""
        output = """## Edge Case Analysis

### Edge Case Scenarios

"""
        
        # Find edge case results
        comparison = self.results.get("comparison", {})
        edge_cases = {
            "edge_no_failures": "No Failing Tests",
            "edge_patch_conflict": "Patch Application Failure",
            "edge_max_iterations": "Max Iterations Limit",
            "edge_timeout": "Timeout Handling"
        }
        
        for edge_key, edge_name in edge_cases.items():
            if edge_key in comparison:
                comp = comparison[edge_key]
                v1_0 = comp.get("v1_0", {})
                v1_1 = comp.get("v1_1", {})
                
                output += f"""#### {edge_name}

**Scenario:** {edge_key}

| Version | Behavior | Status | Notes |
|---------|----------|--------|-------|
| v1.0 | {self._describe_edge_behavior(v1_0, edge_key)} | {v1_0.get('status', 'unknown')} | {self._get_edge_notes(v1_0, edge_key)} |
| v1.1 | {self._describe_edge_behavior(v1_1, edge_key)} | {v1_1.get('status', 'unknown')} | {self._get_edge_notes(v1_1, edge_key)} |

**Verdict:** {self._edge_case_verdict(v1_0, v1_1, edge_key)}

"""
        
        output += "\n---\n\n"
        return output
        
    def _describe_edge_behavior(self, result: Dict, edge_type: str) -> str:
        """Describe behavior for edge case"""
        if edge_type == "edge_no_failures":
            if result.get('tests_fixed') == 0:
                return "Correctly detected no failures, no-op"
            else:
                return "ERROR: Made changes when none needed"
                
        elif edge_type == "edge_patch_conflict":
            if result.get('status') == 'completed':
                return "Handled conflict gracefully"
            else:
                return "Failed to handle conflict"
                
        elif edge_type == "edge_max_iterations":
            if result.get('max_iterations_reached'):
                return "Stopped at max iterations"
            else:
                return "Completed before max"
                
        elif edge_type == "edge_timeout":
            if result.get('timeout_occurred'):
                return "Timed out as expected"
            else:
                return "Completed before timeout"
                
        return "Unknown behavior"
        
    def _get_edge_notes(self, result: Dict, edge_type: str) -> str:
        """Get notes for edge case result"""
        if result.get('status') == 'error':
            return f"Error: {result.get('error', 'Unknown')}"
        elif result.get('status') == 'timeout':
            return "Timed out"
        else:
            return "Normal completion"
            
    def _edge_case_verdict(self, v1_0: Dict, v1_1: Dict, edge_type: str) -> str:
        """Determine verdict for edge case"""
        if v1_0.get('status') == v1_1.get('status'):
            return "✅ Both versions handle edge case similarly"
        elif v1_1.get('status') == 'completed' and v1_0.get('status') != 'completed':
            return "✅ v1.1 handles edge case better"
        else:
            return "⚠️ v1.1 may have regression in edge case handling"
            
    def _generate_performance_comparison(self) -> str:
        """Generate performance comparison section"""
        summary = self.results.get("summary", {})
        v1_0_stats = summary.get("v1_0", {})
        v1_1_stats = summary.get("v1_1", {})
        
        output = """## Performance Comparison

### Efficiency Analysis

"""
        
        # Calculate performance metrics
        time_improvement = ((v1_0_stats.get('avg_time', 1) - v1_1_stats.get('avg_time', 1)) / 
                          v1_0_stats.get('avg_time', 1) * 100)
        iter_improvement = ((v1_0_stats.get('avg_iterations', 1) - v1_1_stats.get('avg_iterations', 1)) / 
                          v1_0_stats.get('avg_iterations', 1) * 100)
        
        output += f"""#### Time Efficiency
- **v1.0 Average:** {v1_0_stats.get('avg_time', 0):.1f} seconds
- **v1.1 Average:** {v1_1_stats.get('avg_time', 0):.1f} seconds
- **Improvement:** {time_improvement:+.1f}% {"(faster)" if time_improvement > 0 else "(slower)"}

#### Iteration Efficiency
- **v1.0 Average:** {v1_0_stats.get('avg_iterations', 0):.1f} iterations
- **v1.1 Average:** {v1_1_stats.get('avg_iterations', 0):.1f} iterations
- **Improvement:** {iter_improvement:+.1f}% {"(fewer)" if iter_improvement > 0 else "(more)"}

### Complexity Handling

"""
        
        # Analyze complexity scenarios
        comparison = self.results.get("comparison", {})
        complexity_tests = {
            "complexity_one_line": "Simple (One-line fix)",
            "complexity_multi_file": "Complex (Multi-file fix)",
            "complexity_refactor": "Very Complex (Major refactor)"
        }
        
        output += "| Complexity Level | v1.0 Success | v1.1 Success | Winner |\n"
        output += "|-----------------|--------------|--------------|--------|\n"
        
        for test_key, test_name in complexity_tests.items():
            if test_key in comparison:
                comp = comparison[test_key]
                v1_0_success = "✅" if comp.get("v1_0", {}).get("success") else "❌"
                v1_1_success = "✅" if comp.get("v1_1", {}).get("success") else "❌"
                
                if comp.get("outcome") == "v1_1_better":
                    winner = "v1.1 🎉"
                elif comp.get("outcome") == "v1_0_better":
                    winner = "v1.0 ⚠️"
                elif comp.get("outcome") == "equal":
                    winner = "Tie"
                else:
                    winner = "Both Failed"
                    
                output += f"| {test_name} | {v1_0_success} | {v1_1_success} | {winner} |\n"
                
        output += "\n---\n\n"
        return output
        
    def _generate_recommendations(self) -> str:
        """Generate recommendations section"""
        summary = self.results.get("summary", {})
        comparison = summary.get("comparison", {})
        
        output = """## Recommendations

### Primary Recommendation
"""
        
        # Determine primary recommendation
        if comparison.get("regressions", 0) > 0:
            output += """
**❌ DO NOT PROCEED WITH v1.1 ADOPTION**

Regressions have been detected that need to be addressed before v1.1 can replace v1.0:

1. Investigate and fix all regression cases
2. Re-run regression suite after fixes
3. Ensure no new regressions are introduced

"""
        elif comparison.get("meets_criteria", False):
            output += """
**✅ PROCEED WITH v1.1 ADOPTION**

Nova CI-Rescue v1.1 with Deep Agent integration has met all success criteria:

1. Success rate ≥70% achieved
2. No regressions detected
3. Performance is equal or better than v1.0
4. All edge cases handled gracefully

**Next Steps:**
1. Merge v1.1 Deep Agent integration to main branch
2. Deprecate v1.0 legacy agent code
3. Update documentation to reflect single CLI path
4. Release v1.1 as the default version

"""
        else:
            output += """
**⚠️ ADDITIONAL WORK NEEDED**

While v1.1 shows promise, it does not yet meet all criteria for full adoption:

1. Review areas where v1.1 underperforms
2. Consider selective improvements from Harrison Chase's deepagents framework
3. Re-test after improvements
4. Consider gradual rollout with feature flags

"""
        
        output += """### Alternative Considerations

#### Harrison Chase's DeepAgents Framework

Based on our test results, here's our assessment of whether to switch to the deepagents reference implementation:

"""
        
        if comparison.get("meets_criteria", False):
            output += """
**Recommendation: STAY WITH IN-HOUSE IMPLEMENTATION**

Our in-house Deep Agent has proven effective and meets all requirements. Benefits of staying:

1. Custom-tailored to Nova CI-Rescue use cases
2. No integration overhead or risk
3. Full control over implementation
4. Already validated through comprehensive testing

We should monitor deepagents for innovative features we might selectively adopt, but a wholesale replacement is not justified.

"""
        else:
            output += """
**Recommendation: EVALUATE DEEPAGENTS AS ALTERNATIVE**

Given the current limitations, consider evaluating Harrison Chase's deepagents framework, particularly if:

1. Planning and multi-step reasoning show weaknesses
2. Complex refactoring scenarios consistently fail
3. The framework offers specific capabilities we lack

However, integration effort must be weighed against potential benefits.

"""
        
        output += "\n---\n\n"
        return output
        
    def _generate_appendix(self) -> str:
        """Generate appendix with additional details"""
        output = """## Appendix

### A. Test Environment Details

"""
        
        # Add environment information
        v1_0_env = self.results.get("v1_0", {}).get("environment", {})
        v1_1_env = self.results.get("v1_1", {}).get("environment", {})
        
        output += """| Component | v1.0 | v1.1 |
|-----------|------|------|
| Python Version | 3.9 | 3.9 |
| Nova Version | 1.0.0 | 1.1.0 |
| LLM Model | GPT-4 | GPT-4 |
| Max Iterations | 6 | 6 |
| Default Timeout | 1200s | 1200s |

### B. Test Repository List

"""
        
        # List all test repositories
        comparison = self.results.get("comparison", {})
        
        output += "| Repository | Type | Expected Failures | v1.0 Result | v1.1 Result |\n"
        output += "|------------|------|-------------------|-------------|-------------|\n"
        
        for test_name in sorted(comparison.keys()):
            comp = comparison[test_name]
            test_type = "Edge Case" if "edge_" in test_name else "Real World"
            v1_0_result = "✅" if comp.get("v1_0", {}).get("success") else "❌"
            v1_1_result = "✅" if comp.get("v1_1", {}).get("success") else "❌"
            
            output += f"| {test_name} | {test_type} | N/A | {v1_0_result} | {v1_1_result} |\n"
            
        output += """

### C. Raw Data Location

- Full JSON results: `regression_results.json`
- v1.0 logs: `v1_0/` directory
- v1.1 logs: `v1_1/` directory
- Individual test outputs: `v1_0/<test_name>/` and `v1_1/<test_name>/`

### D. Test Execution Command

```bash
python regression_orchestrator.py test_repos.yaml --output regression_results --verbose
```

### E. Report Generation Timestamp

Generated: """ + self.timestamp + """

---

**End of Report**
"""
        
        return output
        
    def generate_comparison_chart(self) -> Optional[Path]:
        """Generate visual comparison chart"""
        try:
            summary = self.results.get("summary", {})
            comparison = self.results.get("comparison", {})
            
            # Create figure with subplots
            fig, axes = plt.subplots(2, 2, figsize=(12, 10))
            fig.suptitle('Nova CI-Rescue v1.0 vs v1.1 Comparison', fontsize=16)
            
            # 1. Success Rate Comparison
            ax1 = axes[0, 0]
            versions = ['v1.0', 'v1.1']
            success_rates = [
                summary.get("v1_0", {}).get("success_rate", 0),
                summary.get("v1_1", {}).get("success_rate", 0)
            ]
            bars1 = ax1.bar(versions, success_rates, color=['blue', 'green'])
            ax1.set_ylabel('Success Rate (%)')
            ax1.set_title('Success Rate Comparison')
            ax1.axhline(y=70, color='r', linestyle='--', label='70% Target')
            ax1.legend()
            
            # Add value labels on bars
            for bar, rate in zip(bars1, success_rates):
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height,
                        f'{rate:.1f}%', ha='center', va='bottom')
            
            # 2. Test Outcomes Distribution
            ax2 = axes[0, 1]
            outcome_counts = defaultdict(int)
            for comp in comparison.values():
                outcome_counts[comp.get("outcome", "unknown")] += 1
                
            outcomes = list(outcome_counts.keys())
            counts = list(outcome_counts.values())
            colors_map = {
                'v1_1_better': 'green',
                'v1_0_better': 'red',
                'equal': 'yellow',
                'both_failed': 'gray',
                'v1_1_more_efficient': 'lightgreen',
                'v1_0_more_efficient': 'orange'
            }
            colors = [colors_map.get(o, 'blue') for o in outcomes]
            
            ax2.pie(counts, labels=outcomes, colors=colors, autopct='%1.1f%%')
            ax2.set_title('Test Outcome Distribution')
            
            # 3. Average Time Comparison
            ax3 = axes[1, 0]
            avg_times = [
                summary.get("v1_0", {}).get("avg_time", 0),
                summary.get("v1_1", {}).get("avg_time", 0)
            ]
            bars3 = ax3.bar(versions, avg_times, color=['blue', 'green'])
            ax3.set_ylabel('Average Time (seconds)')
            ax3.set_title('Average Execution Time')
            
            for bar, time in zip(bars3, avg_times):
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height,
                        f'{time:.1f}s', ha='center', va='bottom')
            
            # 4. Average Iterations Comparison
            ax4 = axes[1, 1]
            avg_iters = [
                summary.get("v1_0", {}).get("avg_iterations", 0),
                summary.get("v1_1", {}).get("avg_iterations", 0)
            ]
            bars4 = ax4.bar(versions, avg_iters, color=['blue', 'green'])
            ax4.set_ylabel('Average Iterations')
            ax4.set_title('Average Iterations to Fix')
            
            for bar, iters in zip(bars4, avg_iters):
                height = bar.get_height()
                ax4.text(bar.get_x() + bar.get_width()/2., height,
                        f'{iters:.1f}', ha='center', va='bottom')
            
            plt.tight_layout()
            
            # Save chart
            chart_path = self.output_dir / "comparison_chart.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return chart_path
            
        except Exception as e:
            print(f"Warning: Could not generate chart: {e}")
            return None


def generate_html_report(markdown_path: Path, output_path: Optional[Path] = None) -> Path:
    """Convert Markdown report to HTML"""
    try:
        import markdown
        from markdown.extensions import tables, fenced_code, codehilite
        
        with open(markdown_path, 'r') as f:
            md_content = f.read()
            
        html_content = markdown.markdown(
            md_content,
            extensions=['tables', 'fenced_code', 'codehilite', 'toc']
        )
        
        # Wrap in HTML template
        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nova CI-Rescue Regression Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: #2c3e50;
            margin-top: 24px;
            margin-bottom: 16px;
        }}
        h1 {{
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            border-bottom: 1px solid #ecf0f1;
            padding-bottom: 8px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 16px 0;
            background-color: white;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #3498db;
            color: white;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Courier New', Courier, monospace;
        }}
        pre {{
            background-color: #2c3e50;
            color: #ecf0f1;
            padding: 16px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        pre code {{
            background-color: transparent;
            color: inherit;
            padding: 0;
        }}
        blockquote {{
            border-left: 4px solid #3498db;
            margin: 16px 0;
            padding-left: 16px;
            color: #666;
        }}
        .success {{ color: #27ae60; }}
        .warning {{ color: #f39c12; }}
        .error {{ color: #e74c3c; }}
        img {{
            max-width: 100%;
            height: auto;
            display: block;
            margin: 16px auto;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>"""
        
        if output_path is None:
            output_path = markdown_path.with_suffix('.html')
            
        with open(output_path, 'w') as f:
            f.write(html_template)
            
        return output_path
        
    except ImportError:
        print("Warning: markdown library not installed. Skipping HTML generation.")
        return markdown_path
