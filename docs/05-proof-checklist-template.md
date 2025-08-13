# Nova CI-Rescue — Proof Checklist Template

Use this template for every green run — in Slite and in PR comments.

```yaml
# Proof Checklist — Nova CI-Rescue Happy Path

⏱ Duration:  
🔁 Iterations:  
🧪 Tests Before → After: `X failed / Y passed` → `0 failed / Y+ passed`  
🧩 Files changed / LOC:  
📦 Artifacts path: `.nova/<run>/…`  
✅ Status: **GREEN / FAIL**

Links:
- Action run: 
- PR: 
- Artifacts download: 
- Proof wall entry:
```

## Example Filled Out

```yaml
# Proof Checklist — Nova CI-Rescue Happy Path

⏱ Duration: 2m 34s
🔁 Iterations: 3
🧪 Tests Before → After: `5 failed / 95 passed` → `0 failed / 100 passed`  
🧩 Files changed / LOC: 3 files / 42 LOC
📦 Artifacts path: `.nova/20250813T201234Z/`
✅ Status: **GREEN**

Links:
- Action run: https://github.com/org/repo/actions/runs/123456
- PR: https://github.com/org/repo/pull/456
- Artifacts download: https://github.com/org/repo/actions/runs/123456/artifacts
- Proof wall entry: https://slite.com/proof-wall#20250813
```
