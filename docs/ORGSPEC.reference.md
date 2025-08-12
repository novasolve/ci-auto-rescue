# OrgSpec — Reference & Examples

Nova’s guardrails are declared in YAML and live in the repo (e.g. `.nova/orgspec.yml`).

## Schema (stable subset)
```yaml
org: nova-solve
repo:
  allow_paths:
    - "src/**"
    - "tests/**"
  deny_paths:
    - ".github/workflows/**"
    - "deploy/**"
diff_caps:
  max_files: 10
  max_lines: 200
budgets:
  wall_time_s: 3600
  max_attempts: 6
  cost_usd: 5.00
sandbox:
  base_image: "ubuntu:22.04"
  tools_required: ["git","tree","rg","curl","ca-certificates"]
  network_allowed: false  # test runs offline by default
ci:
  test_cmd: "pytest -q"
  reproduce_flags: "-k '{{FAILED_TESTS}}' --maxfail=1"
pr:
  auto_draft: true
  reviewers: ["@team/owning-service"]
evidence:
  include_coverage_delta: true
  redact_patterns: ["SECRET_*", "API_KEY", "(?i)password"]
flake_policy:
  reruns: 3
  quarantine_label: "flaky"
```

### Example (Python repo)
```yaml
repo:
  allow_paths: ["app/**","tests/**"]
ci:
  test_cmd: "pytest -q --disable-warnings -rA"
```

> Notes
>
> - `network_allowed: true` required for e2e tests hitting external services.
> - If OrgSpec is missing, Nova uses conservative defaults (tiny diffs, offline tests).
