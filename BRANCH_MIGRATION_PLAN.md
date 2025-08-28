# Branch Migration Plan: Trunk-Based Development

## Current State Analysis

- **Main branch**: `origin/main` - appears to be the primary release branch
- **Development branch**: `origin/development` - has newer commits that should be merged to main
- **Demo branches**: `demo/2025-08-28`, `demo/latest` - should become tags
- **Feature branches**: Multiple active feat/fix branches
- **Bot branches**: `nova-auto-fix/*`, `open-swe/*` - ephemeral automation branches

## Target State: Trunk-Based Development

### Branch Structure

1. **main** - Releasable trunk (PR-only, no direct pushes)
2. **release/\*** - Optional frozen patch lines for hotfixes
3. **Short-lived branches**:
   - `feat/<slug>` - New features
   - `fix/<slug>` - Bug fixes
   - `docs/<slug>` - Documentation updates
   - `chore/<slug>` - Maintenance tasks
   - `ci/<slug>` - CI/CD improvements
   - `perf/<slug>` - Performance improvements
4. **Bot/experiment branches**: `bot/<tool>/<date>-<slug>` (ephemeral, auto-deleted)

### Migration Steps

#### Phase 1: Merge Development to Main

- [x] Analyze commits in development vs main
- [ ] Create PR to merge development → main
- [ ] Retire development branch after merge

#### Phase 2: Convert Demo Branches to Tags

- [ ] Create tags: `demo-v0.1`, `demo-2025-08-28`
- [ ] Delete demo branches after tagging

#### Phase 3: Clean Up Feature Branches

- [ ] Review merged feature branches and delete
- [ ] Rename any active branches to follow new convention

#### Phase 4: Set Up Branch Protection

- [ ] Configure main branch protection rules
- [ ] Require PR reviews for main
- [ ] Enable status checks

#### Phase 5: Documentation

- [ ] Update CONTRIBUTING.md with new branch strategy
- [ ] Create branch naming guidelines
- [ ] Update CI/CD workflows if needed

## Benefits

- Simplified mental model for contributors
- Faster integration cycles
- Reduced merge conflicts
- Clear release process
- Automated cleanup of ephemeral branches
