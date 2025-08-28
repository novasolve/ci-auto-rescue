# Nova CI-Rescue Telemetry Implementation

## Overview

The telemetry system for Nova CI-Rescue has been fully implemented to provide comprehensive observability and auditing capabilities. The system logs all key events during the agent loop and saves artifacts (patches and test reports) for full reconstruction of each run.

## Implementation Summary

### 1. Enhanced Telemetry Logger (`src/nova/telemetry/logger.py`)

Added new methods to the existing `JSONLLogger`:

- `save_patch(step_number, patch_content)` - Saves patch diffs as `patches/step-N.patch`
- `save_test_report(step_number, report_content, report_type)` - Saves test reports as `reports/step-N.xml`

### 2. Test Runner Updates (`src/nova/runner/test_runner.py`)

Modified `run_tests()` to return both failing tests and JUnit XML report:

```python
def run_tests(self, max_failures: int = 5) -> Tuple[List[FailingTest], Optional[str]]:
    # Returns (failing_tests, junit_xml_content)
```

### 3. Node Implementations (`src/nova/nodes/`)

Created dedicated node classes with integrated telemetry:

- `PlannerNode` - Logs `planner_start` and `planner_complete` events
- `ActorNode` - Logs `actor_start`, `actor_complete`, and saves patch artifacts
- `CriticNode` - Logs `critic_start`, `critic_approved/rejected` events
- `RunTestsNode` - Logs `run_tests_start/complete` and saves test reports
- `ReflectNode` - Logs `reflect_start/complete` with decision reasoning

### 4. CLI Integration (`src/nova/cli.py`)

Updated the main `fix` command to:

- Save initial test report (step-0.xml)
- Save patch artifacts before applying (step-N.patch)
- Save test reports after each iteration (step-N.xml)
- Log all node events with relevant metadata

## Telemetry Output Structure

After a run, the telemetry directory (`.nova/<run_id>/`) contains:

```
.nova/
└── 20250814T171658Z-88f81e32/
    ├── trace.jsonl           # Complete event log
    ├── patches/
    │   ├── step-1.patch     # Diff from iteration 1
    │   ├── step-2.patch     # Diff from iteration 2
    │   └── ...
    └── reports/
        ├── step-0.xml       # Initial test report
        ├── step-1.xml       # Test report after patch 1
        ├── step-2.xml       # Test report after patch 2
        └── ...
```

## Event Types Logged

The system logs the following events in `trace.jsonl`:

### Core Loop Events

- `start` - Run initialization with repo path and run ID
- `test_discovery` - Initial test failure discovery
- `planner_start/complete` - Planning phase with approach and steps
- `actor_start/complete` - Patch generation with size metrics
- `critic_start/approved/rejected` - Patch review with reasoning
- `patch_applied` - Successful patch application with file changes
- `run_tests_start/complete` - Test execution with before/after counts
- `reflect_start/complete` - Decision logic (continue/stop/success)
- `end` - Run completion with final summary

### Artifact Events

- `artifact` - Generic artifact saved (with path and size)
- Patches saved as `patches/step-N.patch`
- Test reports saved as `reports/step-N.xml`

## Example trace.jsonl Entry

```json
{
  "ts": "2025-08-14T17:16:58.218744+00:00",
  "event": "planner_complete",
  "data": {
    "iteration": 1,
    "plan": {
      "approach": "Fix failing assertions",
      "steps": [
        "Analyze test failures",
        "Fix assertion errors",
        "Verify fixes"
      ],
      "target_tests": [
        { "name": "test_foo", "file": "test_foo.py", "line": 10 },
        { "name": "test_bar", "file": "test_bar.py", "line": 20 }
      ]
    },
    "failing_tests": 3
  }
}
```

## Acceptance Criteria Met ✅

1. **Full loop reconstruction**: The `trace.jsonl` file contains all events needed to reconstruct the entire agent loop
2. **Per-step artifacts**: Diffs saved as `step-N.patch` and test reports as `step-N.xml`
3. **Key step logging**: All nodes (planner/actor/critic/apply/run_tests/reflect) call `logger.log_event()` at appropriate points
4. **Observability**: Complete visibility into the agent's decision-making process and actions

## Usage

The telemetry system is automatically enabled when running Nova:

```bash
nova fix /path/to/repo
```

Telemetry output will be saved to `.nova/<run_id>/` in the current directory.

To disable telemetry, set the environment variable:

```bash
NOVA_TELEMETRY_ENABLED=false nova fix /path/to/repo
```

## Benefits

- **Debugging**: Full visibility into what the agent did and why
- **Auditing**: Complete record of all patches and test results
- **Analysis**: Can replay and analyze successful and failed runs
- **Metrics**: Extract performance and success metrics from trace logs
- **Compliance**: Maintain audit trail for CI/CD pipeline changes

## Future Enhancements

- Add telemetry visualization dashboard
- Export metrics to monitoring systems (Prometheus, DataDog)
- Add telemetry compression for long-running jobs
- Implement telemetry retention policies
- Add telemetry search and query capabilities
