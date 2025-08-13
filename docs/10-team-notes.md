# Nova CI-Rescue — Team Notes & Updates

## Latest Updates

### 2025-08-13
- ✅ Linear project created with all 15 issues
- ✅ Labels applied to all issues (must-have, nice-to-have, functional areas)
- ✅ All issues assigned to Sebastian Heyneman
- ✅ Documentation organized into separate files in /docs folder
- ✅ OS-847 created for Slite documentation update

### Upcoming
- [ ] Review ChatGPT refined version: https://chatgpt.com/c/689cf09e-0be4-832c-8736-6dbe2f74b478
- [ ] Update Linear issues with refined descriptions
- [ ] Create GitHub Action workflow file
- [ ] Set up demo repository

## Key Decisions

### Technical
- **Model Strategy:** Start with GPT-4o-mini for cost efficiency
- **Scope:** Focus on single-file fixes for v1.0
- **Testing:** Use pytest as primary framework
- **Telemetry:** JSONL format for trace logs

### Product
- **MVP Focus:** Happy path with seeded failures only
- **Defer to v2.0:** Multi-repo orchestration, complex failure patterns
- **Safety First:** Hard caps on LOC and file changes

### Go-to-Market
- **Free Tier:** First 100 solves free for early adopters
- **Proof Strategy:** Document every successful run with artifacts
- **Distribution:** CLI-first, GitHub Action second

## Open Questions

1. **GitHub Permissions:** How to handle PR comment permissions across different org setups?
2. **Model Fallback:** When exactly should we switch from GPT-4o-mini to GPT-4o?
3. **Test Determinism:** How to ensure seeded tests fail consistently?
4. **Metrics Collection:** What telemetry is essential vs nice-to-have?

## Meeting Notes

### Sprint Planning (Date TBD)
- Review milestone A completion
- Assign milestone B tasks
- Demo A5 smoke run results

### Investor Update (Date TBD)
- Prepare proof wall entries
- Record demo video
- Update pitch deck with latest metrics

## Resource Links

### Internal Docs
- [Original action plan](ACTION_PLAN.md)
- [Implementation guide](IMPLEMENTATION_GUIDE.md)
- [Environment setup](env.example)

### External References
- [ChatGPT conversation](https://chatgpt.com/c/689cf09e-0be4-832c-8736-6dbe2f74b478)
- [Linear project](https://linear.app/nova-solve/project/ci-rescue-v10-happy-path-536aaf0d73d7)

## Blockers Log

### Current Blockers
- None

### Resolved Blockers
- ✅ Slite API key configuration (resolved 2025-08-13)
- ✅ Linear label creation permissions (resolved 2025-08-13)

## Success Metrics

### Week 1 Goals
- [ ] 5 successful test fixes on demo repos
- [ ] < 3 iterations average to green
- [ ] < 5 minute average runtime

### Month 1 Goals
- [ ] 100 successful fixes across 20 repos
- [ ] 90% success rate on seeded failures
- [ ] GitHub Action running on 5 real projects

## Code Review Checklist

Before merging any PR:
- [ ] Tests pass locally
- [ ] Telemetry logging in place
- [ ] Safety caps enforced
- [ ] Documentation updated
- [ ] Linear issue updated

## Communication Guidelines

### Daily Updates
- Post in #ci-rescue Slack channel
- Update Linear issue status
- Commit code by EOD

### Weekly Sync
- Monday: Sprint planning
- Wednesday: Progress check
- Friday: Demo & retrospective

## Definition of Done Checklist

For each Linear issue:
- [ ] Code complete and tested
- [ ] Documentation updated
- [ ] Telemetry verified
- [ ] PR reviewed and merged
- [ ] Linear issue closed
- [ ] Proof artifact generated
