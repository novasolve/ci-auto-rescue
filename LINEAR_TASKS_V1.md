# Linear Task List for Nova CI-Rescue v1.0

## ✅ Completed Tasks

### Milestone C: GitHub Integration
- [x] **C2: Scorecard Check Run + PR Comment** ✅
  - GitHub API integration module
  - Check run with pass/fail status
  - PR comment with metrics table
  - Idempotent comment updates
  - JSON report generation

### Milestone D: Evaluation & Polish
- [x] **D1: Nova Eval Command** ✅
  - YAML configuration parsing
  - Multi-repository batch evaluation
  - Git clone support for remote repos
  - Summary table and JSON output
  - Non-zero exit on failure

## 🔴 Required Tasks (Blocking v1.0)

### High Priority - Complete Today
1. **[B1] Configure Quiet Test Output**
   - Make pytest run quietly by default in CI
   - Add verbose flag for detailed output
   - Estimate: 30 minutes

2. **[B3] Package Installation Verification**
   - Test clean installation in fresh virtualenv
   - Verify all dependencies are correctly specified
   - Test pip install from PyPI (when published)
   - Estimate: 1 hour

### Medium Priority - Complete Tomorrow
3. **[DOCS-1] Complete Happy Path Tutorial**
   - Step-by-step guide for first-time users
   - Include screenshots/examples
   - Cover common use cases
   - Estimate: 2 hours

4. **[DOCS-2] Update Main README**
   - Current feature list
   - Installation instructions
   - Configuration guide
   - GitHub Actions setup
   - Estimate: 1 hour

5. **[D2] Create Demo Repository**
   - Minimal Python project with failing tests
   - Various failure scenarios (syntax, logic, import errors)
   - Good for onboarding and testing
   - Estimate: 2 hours

6. **[B-DR] Telemetry Security Audit**
   - Review logged data for sensitive information
   - Check performance impact
   - Ensure GDPR compliance
   - Estimate: 1 hour

### Low Priority - This Week
7. **[DOCS-3] Update Slite Documentation (OS-847)**
   - Sync with current implementation
   - Add API documentation
   - Include troubleshooting guide
   - Estimate: 2 hours

8. **[QA-1] End-to-End Testing**
   - Test on 3+ real repositories
   - Verify GitHub integration in live PR
   - Document any issues found
   - Estimate: 3 hours

## 🟡 Optional Tasks (Nice-to-Have)

### Enhancement Tasks
9. **[ENH-1] Add --test-cmd Option**
   - Support non-pytest test runners
   - Allow custom test commands
   - Estimate: 2 hours

10. **[ENH-2] Project Config File Support**
    - .nova.yaml configuration
    - Per-project safety limits
    - Custom model selection
    - Estimate: 3 hours

11. **[ENH-3] Parallel Evaluation**
    - Run multiple repos concurrently in nova eval
    - Add progress bars for each repo
    - Estimate: 4 hours

### Marketing Tasks
12. **[MKT-1] Proof Thread Documentation (D3)**
    - Create Twitter/blog post thread
    - Show real-world usage
    - Include metrics and success stories
    - Estimate: 2 hours

13. **[MKT-2] Performance Benchmarks**
    - Measure fix speed on various repos
    - Compare with manual fixing time
    - Create comparison charts
    - Estimate: 3 hours

## 📊 Summary

### Must Complete for v1.0
- 8 tasks
- Total estimate: ~12 hours
- Can be completed in 1-2 days

### Nice-to-Have for v1.1
- 5 tasks  
- Total estimate: ~14 hours
- Can be scheduled post-release

## 🚢 Release Checklist

Before releasing v1.0, ensure:
- [ ] All required tasks complete
- [ ] Tests passing in CI
- [ ] Documentation updated
- [ ] Demo repository ready
- [ ] GitHub Actions workflow tested
- [ ] Package builds correctly
- [ ] Security audit complete
- [ ] Release notes drafted

## 📅 Suggested Timeline

### Day 1 (Today)
- Morning: B1, B3 (1.5 hours)
- Afternoon: DOCS-1, DOCS-2 (3 hours)
- Evening: D2 (2 hours)

### Day 2 (Tomorrow)
- Morning: B-DR, DOCS-3 (3 hours)
- Afternoon: QA-1 (3 hours)
- Evening: Release preparation

### Day 3 (Release)
- Morning: Final checks
- Afternoon: v1.0 release 🚀

## 🔗 Linear Integration

To import to Linear:
1. Copy each task as a new Linear issue
2. Set appropriate priorities (High/Medium/Low)
3. Add to "Nova CI-Rescue v1.0" milestone
4. Assign estimates in story points (1 point = 1 hour)
5. Link related issues with dependencies

## Status Legend
- 🔴 Required (Must have for v1.0)
- 🟡 Optional (Can wait for v1.1)
- ✅ Completed
- ⏳ In Progress
- ⬜ Not Started
