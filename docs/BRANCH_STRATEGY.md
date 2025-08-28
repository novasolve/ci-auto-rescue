# Branch Strategy: Trunk-Based Development

## Overview

This repository follows a **trunk-based development** model designed to:
- Simplify the mental model for contributors
- Enable faster integration cycles
- Reduce merge conflicts
- Provide a clear release process
- Support automated cleanup of ephemeral branches

## Branch Structure

### Core Branches

#### `main`
- **Purpose**: Releasable trunk containing production-ready code
- **Protection**: PR-only (no direct pushes), requires reviews and status checks
- **Deployment**: Automatically deployed to staging/production environments
- **Lifetime**: Permanent

#### `release/*` (Optional)
- **Purpose**: Frozen patch lines for hotfixes to specific versions
- **Pattern**: `release/v1.2`, `release/v2.0`
- **Usage**: Only when you need to patch an older version while main has moved forward
- **Lifetime**: Long-lived (until version EOL)

### Development Branches

All development work happens on short-lived branches that merge back to `main` via Pull Requests.

#### Feature Branches
- **`feat/<slug>`** - New features and enhancements
- **`fix/<slug>`** - Bug fixes and corrections
- **`docs/<slug>`** - Documentation updates
- **`chore/<slug>`** - Maintenance, refactoring, dependency updates
- **`ci/<slug>`** - CI/CD pipeline improvements
- **`perf/<slug>`** - Performance optimizations

#### Automation Branches
- **`bot/<tool>/<date>-<slug>`** - Ephemeral branches created by automation tools
- **Auto-cleanup**: These branches are automatically deleted after merge/close
- **Examples**:
  - `bot/nova-auto-fix/2025-08-28-memory-leak`
  - `bot/dependabot/2025-08-28-update-pytest`

## Migration from Previous Model

### What Changed
- **Retired**: `development` branch (merged final changes to `main`)
- **Converted**: Demo branches → Tags (`demo-2025-08-28`, `demo-v0.1`)
- **Standardized**: All feature branches follow new naming convention

### Benefits
1. **Simplified workflow**: One main branch to target
2. **Faster feedback**: Changes integrate quickly
3. **Reduced conflicts**: Shorter-lived branches = fewer merge conflicts
4. **Clear history**: Linear progression on main branch
5. **Automated cleanup**: Bot branches self-delete

## Workflow Examples

### Creating a Feature Branch
```bash
# Start from latest main
git checkout main
git pull origin main

# Create feature branch
git checkout -b feat/add-retry-logic

# Work on your feature
git add .
git commit -m "feat: add exponential backoff retry logic"

# Push and create PR
git push origin feat/add-retry-logic
```

### Hotfix Workflow
```bash
# For urgent fixes to current version
git checkout main
git checkout -b fix/critical-security-patch

# For fixes to older versions
git checkout release/v1.2
git checkout -b fix/v1.2-security-patch
```

### Demo/Example Workflow
```bash
# Instead of demo branches, use tags
git tag demo-new-feature
git push origin demo-new-feature

# Or create ephemeral demo branches that get cleaned up
git checkout -b demo/feature-showcase-2025-08-28
# ... after demo, delete the branch
```

## Branch Lifecycle

### Short-lived Branches (feat/fix/docs/chore/ci/perf)
1. **Created** from latest `main`
2. **Developed** with focused commits
3. **PR Created** targeting `main`
4. **Reviewed** by team members
5. **Merged** via squash or merge commit
6. **Deleted** automatically after merge

### Bot Branches
1. **Auto-created** by automation tools
2. **Auto-updated** with fixes/changes
3. **Auto-merged** when tests pass (if configured)
4. **Auto-deleted** after merge or timeout

### Release Branches
1. **Created** when hotfix needed for older version
2. **Patched** with minimal, targeted fixes
3. **Tagged** when patch is ready
4. **Maintained** until version EOL

## Best Practices

### Branch Naming
- Use descriptive slugs: `feat/llm-integration` not `feat/new-feature`
- Keep slugs short but clear: `fix/timeout-error` not `fix/fix-the-timeout-error-in-the-test-runner`
- Use kebab-case: `feat/add-retry-logic` not `feat/add_retry_logic`

### Commit Messages
Follow conventional commits:
```
feat: add exponential backoff to API calls
fix: handle timeout errors in test runner
docs: update installation guide for Python 3.12
chore: bump pytest to v8.0
ci: add security scanning to workflow
perf: optimize test collection algorithm
```

### Pull Requests
- Keep PRs small and focused
- Target `main` branch (unless hotfixing)
- Include clear description and testing notes
- Link to relevant issues
- Ensure CI passes before requesting review

## Automation Support

### Branch Protection Rules
- `main` requires PR reviews
- Status checks must pass
- No direct pushes allowed
- Merge commits allowed for feature integration

### Auto-cleanup
- Bot branches auto-delete after 7 days of inactivity
- Merged feature branches can be auto-deleted
- Stale branches get notifications before cleanup

### CI/CD Integration
- All branches run full test suite
- `main` deploys to staging automatically
- Release tags trigger production deployment
- Bot branches run lightweight validation

## Migration Checklist

- [x] Merge `development` branch to `main`
- [x] Convert demo branches to tags
- [x] Update branch protection rules
- [x] Update CONTRIBUTING.md with new conventions
- [x] Create branch strategy documentation
- [ ] Clean up old merged feature branches
- [ ] Configure auto-cleanup for bot branches
- [ ] Update CI workflows if needed
- [ ] Train team on new workflow

## FAQ

**Q: What happened to the `development` branch?**
A: It was merged into `main` and retired. All development now targets `main` directly via PRs.

**Q: How do I create demo branches?**
A: Use tags instead: `git tag demo-feature-name`. For temporary demos, create ephemeral branches that you delete after use.

**Q: Can I still create long-lived feature branches?**
A: We strongly discourage this. Break large features into smaller, incremental PRs that can merge quickly.

**Q: What about experimental work?**
A: Use `bot/experiment/<date>-<description>` branches that auto-cleanup, or work in personal forks.

**Q: How do hotfixes work?**
A: For current version: branch from `main`. For older versions: branch from the appropriate `release/*` branch.
