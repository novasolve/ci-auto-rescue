# Nova CI-Rescue PR Generator Demo

## New Feature: AI-Powered Pull Request Generation 🤖

I've added a new feature to Nova CI-Rescue v0.1.0-alpha that automatically generates and creates pull requests using GPT-5 and the GitHub CLI.

### What's New

After Nova successfully fixes failing tests, it will:

1. **Use GPT-5 to generate PR content**:

   - Professional PR title (max 72 chars)
   - Detailed description with:
     - Summary of what was broken and fixed
     - List of specific changes
     - Before/after test results
     - Technical details
     - Automation credits

2. **Create the PR automatically** using `gh` CLI:
   - Preserves the fix branch
   - Links to the created PR
   - Falls back gracefully if `gh` is not available

### Files Added/Modified

1. **`src/nova/tools/pr_generator.py`** (NEW)

   - `PRGenerator` class with GPT-5 integration
   - `generate_pr_content()` - Uses AI to write PR title/description
   - `create_pr()` - Creates PR via GitHub CLI
   - `check_pr_exists()` - Prevents duplicate PRs

2. **`src/nova/agent/llm_client_fixed.py`** (NEW)

   - Fixed the patch generation to use full file replacement
   - Prevents the appending bug

3. **`src/nova/agent/llm_agent_enhanced.py`** (MODIFIED)

   - Updated to use the new full-file generation approach
   - Parses LLM responses to extract complete files

4. **`src/nova/cli.py`** (MODIFIED)
   - Added PR generation in the `finally` block after success
   - Imports subprocess and time
   - Tracks execution time for PR description
   - Preserves branch if PR is created

### How to Test

1. **Install GitHub CLI** (if not already installed):

   ```bash
   brew install gh
   gh auth login
   ```

2. **Run Nova on the demo**:

   ```bash
   cd ci-auto-rescue-v0.1.0-alpha
   PYTHONPATH=./src python -m nova.cli fix demo_workspace_clean --max-iters 2
   ```

3. **Watch the magic happen**:
   - Nova will fix the failing tests
   - Generate a PR title and description using GPT-5
   - Create the PR automatically
   - Display the PR URL

### Example Output

After successful fixes, you'll see:

```
✅ Success! Changes saved to branch: nova-fix/20250820_075742

🤖 Using GPT-5 to generate a pull request...
Generating PR title and description...

PR Title: fix: Fix calculator operations and add division by zero handling

PR Description:
## Summary
This PR fixes 3 failing calculator tests by correcting arithmetic operations...

Creating pull request...

🎉 Pull Request created successfully!
https://github.com/your-repo/pull/123
```

### Configuration

The PR generator uses:

- Your default GPT-5 model (from OPENAI_API_KEY)
- The GitHub CLI with your authenticated account
- Base branch: "main" (could be made configurable)

### Error Handling

If PR creation fails:

- Clear error messages explain why (e.g., "gh not found", "not authenticated")
- The branch is preserved so you can create the PR manually
- Nova still exits successfully

### Benefits

1. **Saves time** - No need to write PR descriptions manually
2. **Consistency** - PRs follow a professional format
3. **Context-aware** - GPT-5 understands what was fixed
4. **Automatic** - One less manual step in the workflow
5. **Preserves branches** - Branches with PRs aren't deleted

This feature makes Nova CI-Rescue a complete end-to-end solution: from detecting failing tests to creating the PR for review! 🚀
