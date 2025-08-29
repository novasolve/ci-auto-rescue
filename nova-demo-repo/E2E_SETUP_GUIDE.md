# End-to-End Setup Guide: From Local to GitHub PR with Nova

This guide walks you through setting up the nova-demo-repo from scratch, pushing to GitHub, creating a breaking PR, and watching Nova automatically fix it.

## Prerequisites

- Git installed locally
- GitHub account
- Python 3.10+ installed
- (Optional) GitHub CLI (`gh`) for easier repo creation

## Step 1: Initialize Local Repository

```bash
# Navigate to the nova-demo-repo directory
cd nova-demo-repo

# Initialize Git repository
git init -b main

# Add all files
git add .

# Make initial commit
git commit -m "Initial commit: Calculator with comprehensive tests"
```

## Step 2: Create GitHub Repository

### Option A: Using GitHub Website
1. Go to github.com and click "New repository"
2. Name it `nova-ci-rescue-demo`
3. Leave it empty (no README, .gitignore, or license)
4. Choose public or private
5. Create repository

### Option B: Using GitHub CLI (Recommended)
```bash
# One command to create repo, add remote, and push
gh repo create nova-ci-rescue-demo --public --source=. --remote=origin --push
```

If using Option A, link and push manually:
```bash
# Add GitHub as remote
git remote add origin https://github.com/YOUR_USERNAME/nova-ci-rescue-demo.git

# Push to GitHub
git push -u origin main
```

## Step 3: Verify CI Integration

1. Go to your GitHub repository
2. Click on "Actions" tab
3. You should see the workflow is ready (from `.github/workflows/ci.yml`)

## Step 4: Create the Breaking Change Branch

```bash
# Create and switch to new branch
git checkout -b bugfix/wrong-subtraction

# Apply the breaking changes
git apply breaking-changes.patch

# Commit the "bad" changes
git add -A
git commit -m "fix: optimize calculator performance

- Improved addition performance
- Simplified subtraction logic
- Removed unnecessary error checks for speed"

# Push the branch
git push -u origin bugfix/wrong-subtraction
```

## Step 5: Open Pull Request

### Using GitHub Website:
1. Go to your repository on GitHub
2. You'll see a banner: "bugfix/wrong-subtraction had recent pushes"
3. Click "Compare & pull request"
4. Set title: "Fix: Optimize calculator performance"
5. Add description:
   ```
   This PR optimizes the calculator for better performance:
   - Faster addition algorithm
   - Simplified subtraction
   - Removed redundant checks

   All changes are backward compatible.
   ```
6. Click "Create pull request"

### Using GitHub CLI:
```bash
gh pr create --title "Fix: Optimize calculator performance" \
  --body "This PR optimizes the calculator for better performance." \
  --base main --head bugfix/wrong-subtraction
```

## Step 6: Watch CI Fail

1. Go to the PR page
2. You'll see GitHub Actions running
3. After ~30 seconds, you'll see: ❌ "All checks have failed"
4. Click "Details" to see which tests failed:
   ```
   FAILED tests/test_calculator.py::test_subtraction
   FAILED tests/test_calculator.py::test_division_by_zero
   FAILED tests/test_calculator.py::test_square_root_negative
   FAILED tests/test_calculator.py::test_average_empty_list
   ```

## Step 7: Nova Auto-Fix in Action

If Nova is configured in your GitHub Actions (with API keys), it will:

1. **Automatically trigger** when tests fail
2. **Analyze** the failures
3. **Generate** fixes
4. **Create** a new branch `nova-fix-[timestamp]`
5. **Push** the fixes
6. **Open** a new PR with the corrections

You'll see in the Actions log:
```
🤖 Nova CI-Rescue: Attempting to fix failing tests...
[Nova] ❌ Detected 4 failing tests
[Nova] 🔍 Analyzing failures...
[Nova] 🔧 Applying fixes...
[Nova] ✅ All tests passed after fix!
[Nova] 📤 Pushing fixes to nova-fix-20250820-083945
[Nova] 🎯 Creating pull request...
```

## Step 8: Review Nova's Fix PR

1. Go to "Pull requests" tab
2. You'll see a new PR from Nova
3. Title: "Nova Fix: Correct calculator logic errors"
4. The PR will have:
   - ✅ All checks passing
   - Clear description of what was fixed
   - Minimal, targeted changes
   - Link to the original failing PR

## Step 9: Merge the Fix

1. Review Nova's changes
2. Approve the PR
3. Merge it to main
4. The calculator is now working correctly!

## Local Testing (Alternative)

If you want to test Nova locally before GitHub:

```bash
# Make sure you're on the broken branch
git checkout bugfix/wrong-subtraction

# Run tests to see failures
pytest -v

# Run Nova locally
cd ..  # Go to parent directory with Nova
PYTHONPATH=./src python -m nova.cli fix nova-demo-repo --max-iters 3

# Nova will create a fix branch and show the results
```

## Key Observations

1. **Branch Isolation**: Nova never modifies your branch directly
2. **Atomic Commits**: Each fix is a separate commit
3. **Full Transparency**: All changes are reviewable
4. **CI Integration**: Works seamlessly with GitHub Actions
5. **Safety First**: Requires human approval before merge

## Troubleshooting

- **No Nova action?** Check GitHub Secrets for API keys
- **Nova can't push?** Ensure Actions have write permissions
- **Tests still failing?** Nova will iterate up to max attempts
- **PR not created?** Check if `gh` CLI is available in Actions

## Success Metrics

- ⏱️ Time from failure to fix: ~2-3 minutes
- 🎯 Fix accuracy: High for logical errors
- 👥 Developer time saved: 15-30 minutes per issue
- 🔄 Iteration capability: Up to 6 attempts

This E2E flow demonstrates Nova's value: turning red builds green automatically!
