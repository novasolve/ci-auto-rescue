# Nova PR Safety Check Testing Guide

## Overview

The `test_safety_pr_checks.py` script automates testing of Nova CI-Rescue's safety mechanisms by creating pull requests that intentionally violate safety limits. This ensures that the safety guardrails are working correctly and blocking potentially dangerous automated changes.

## Safety Limits Being Tested

Nova CI-Rescue enforces the following safety limits by default:

1. **Maximum Lines Changed**: 200 lines (configurable via `NOVA_MAX_LINES_CHANGED`)
2. **Maximum Files Modified**: 10 files (configurable via `NOVA_MAX_FILES_MODIFIED`)
3. **Restricted File Patterns**: Critical files that should not be auto-modified
   - CI/CD configuration files (`**/.github/workflows/*`)
   - Secret files (`**/secrets/*`, `**/.env*`, `**/credentials/*`)
   - Deployment configurations (`**/deploy/*`, `**/deployment/*`)
   - And other sensitive patterns

## Test Scenarios

The script creates four test PRs, each violating a specific safety rule:

### 1. CI Configuration Change (`test-ci-config`)

- **What it does**: Creates/modifies a file in `.github/workflows/`
- **Expected result**: Safety check fails for modifying restricted CI/CD files
- **Error message**: "Attempts to modify restricted files: .github/workflows/..."

### 2. Large Patch (`test-line-limit`)

- **What it does**: Creates a file with 250 lines of changes
- **Expected result**: Safety check fails for exceeding line limit
- **Error message**: "Exceeds maximum lines changed: 250 > 200"

### 3. Many Files (`test-many-files`)

- **What it does**: Creates 11 new files in a single commit
- **Expected result**: Safety check fails for too many files modified
- **Error message**: "Exceeds maximum files modified: 11 > 10"

### 4. Sensitive Files (`test-sensitive-files`)

- **What it does**: Creates files in `secrets/` and `deploy/` directories
- **Expected result**: Safety check fails for modifying sensitive paths
- **Error message**: "Attempts to modify restricted files: secrets/..., deploy/..."

## Prerequisites

Before running the test script:

1. **Install GitHub CLI**:

   ```bash
   # macOS
   brew install gh

   # Linux
   curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
   echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
   sudo apt update
   sudo apt install gh
   ```

2. **Authenticate GitHub CLI**:

   ```bash
   gh auth login
   ```

3. **Ensure Nova Safety Check Workflow is Configured**:

   - The repository should have `.github/workflows/nova-pr-check.yml` or similar
   - The workflow should be configured to run on pull request events

4. **Have Push Access**:
   - You need permission to create branches and pull requests in the repository

## Running the Test

1. **Navigate to repository root**:

   ```bash
   cd /path/to/ci-auto-rescue
   ```

2. **Run the test script**:

   ```bash
   python tests/test_safety_pr_checks.py
   ```

   Or make it executable and run directly:

   ```bash
   chmod +x tests/test_safety_pr_checks.py
   ./tests/test_safety_pr_checks.py
   ```

3. **Monitor output**:
   The script will show progress for each test scenario:
   ```
   🧪 Testing scenario: Modify a CI workflow file...
   ✅ PR created: https://github.com/your-org/repo/pull/123
   ```

## Verifying Results

After running the script:

1. **Check PR Links**: The script outputs URLs for each created PR
2. **Wait for Actions**: GitHub Actions may take 1-2 minutes to run
3. **Verify Each PR Shows**:
   - ❌ Failed safety check status
   - 💬 Comment from Nova bot explaining the violation
   - 🚫 PR is blocked from merging

### Expected PR Comment Format

Each PR should receive a comment like:

```markdown
## 🛡️ Nova CI-Rescue Safety Check

❌ Safety check failed

### Violations Detected:

- Exceeds maximum lines changed: 250 > 200

This PR exceeds the configured safety limits for automated changes.
Manual review is required before merging.
```

## Cleanup

After verification:

1. **Close Test PRs**: Close each test PR without merging
2. **Delete Test Branches** (optional):
   ```bash
   git push origin --delete test-ci-config
   git push origin --delete test-line-limit
   git push origin --delete test-many-files
   git push origin --delete test-sensitive-files
   ```

## Customizing Safety Limits

To test custom limits, set environment variables before running Nova:

```bash
export NOVA_MAX_LINES_CHANGED=100
export NOVA_MAX_FILES_MODIFIED=5
```

Or create `.nova-safety.yml` in the repository root:

```yaml
max_lines_changed: 100
max_files_modified: 5
denied_paths:
  - "**/.github/**"
  - "**/secrets/**"
  - "**/deploy/**"
  - "**/*.key"
  - "**/*.pem"
```

## Troubleshooting

### GitHub CLI Authentication Issues

```bash
# Check authentication status
gh auth status

# Re-authenticate if needed
gh auth refresh
```

### Permission Denied Errors

- Ensure you have write access to the repository
- Check if branch protection rules allow PR creation

### No Safety Check Running

- Verify the workflow file exists in the default branch
- Check if the workflow is enabled in GitHub Actions settings
- Ensure the workflow triggers on `pull_request` events

### Script Fails to Push

- Check if you have the latest changes: `git pull origin main`
- Ensure no conflicting branch names exist
- Verify network connectivity to GitHub

## Additional Testing

For more comprehensive testing:

1. **Test Bypass Mechanism**: Some repos may have override flags for emergencies
2. **Test Edge Cases**: Exactly 200 lines or exactly 10 files
3. **Test Configuration**: Modify `.nova-safety.yml` and verify new limits
4. **Test Different File Types**: Binary files, symlinks, submodules

## Support

For issues or questions about the safety check system:

- Review the Nova CI-Rescue documentation
- Check the workflow logs in GitHub Actions
- Open an issue in the repository

---

**Note**: This test script is designed for development and validation purposes. Always review the actual safety check implementation to ensure it matches your security requirements.
