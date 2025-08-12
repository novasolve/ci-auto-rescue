# Evidence: Scorecard & Ledger

Every run must produce **proof** (human summary) and an **audit trail** (machine log).

## Scorecard (JSON)
```json
{
  "repo": "owner/name",
  "branch": "nova/ci-rescue-123",
  "tests_before": ["tests/api/test_users.py::test_get_user"],
  "tests_after": [],
  "attempts": 2,
  "duration_s": 2147,
  "diff": { "files_changed": 2, "lines_added": 27, "lines_deleted": 3 },
  "coverage_delta": "+0.3%",
  "policy": { "within_caps": true, "denied_paths_touched": false },
  "budget": { "time_s": 2147, "cost_usd": 1.12, "attempts": 2 },
  "artifact_urls": {
    "pr": "https://github.com/…/pull/123",
    "logs": "…/artifacts/ledger.jsonl"
  }
}
```

## Ledger (JSON Lines)
Each line is a step the agent/system took.

```json
{"ts":"2025-08-11T20:02:01Z","kind":"tool","name":"pytest","args":"-q -k 'failed_tests'","exit_code":1}
{"ts":"2025-08-11T20:05:12Z","kind":"edit","path":"src/user.py","summary":"Add None-guard on email"}
{"ts":"2025-08-11T20:08:44Z","kind":"policy_check","result":"pass","details":{"diff_lines":27}}
{"ts":"2025-08-11T20:10:08Z","kind":"pytest","exit_code":0}
```

### Redaction rules
- Hash prompts/responses if stored; never persist secrets or full credential strings.
- Apply `evidence.redact_patterns` from OrgSpec before upload.

### CI checks
Fail the PR check if Scorecard missing, Ledger missing, or `policy.within_caps=false`.
