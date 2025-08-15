# Nova CI-Rescue Quickstart Tutorial

Nova CI-Rescue is an AI-powered tool that autonomously detects and fixes failing tests in your codebase using state-of-the-art language models (e.g. OpenAI GPT-4 or Anthropic Claude). It acts as a smart CI companion: you run nova fix and Nova will analyze test failures, suggest code patches, apply them, and re-run tests iteratively until your test suite passes. This tutorial walks you through setting up Nova, configuring it, and using it to automatically turn failing tests green.

## 1. Set Up the Environment and Install Nova

**Prerequisites:** Ensure you have Python 3.10+, Git, and an API key for either OpenAI or Anthropic (at least one is required for the AI model). It's recommended to create and activate a Python virtual environment for an isolated setup (optional but good practice).

**Install Nova:** Nova CI-Rescue is distributed as a Python package. You can install it using pip:

```bash
pip install nova-ci-rescue
```

This installs Nova from PyPI along with its dependencies. (If you plan to develop or use the latest source, clone the repo and install in editable mode with `pip install -e .`, but the PyPI release is the easiest way to get started.)

**Verify the installation:** After installing, run the command below to ensure Nova is accessible and to check the version:

```bash
nova --version
```

This should display Nova's version (make sure your Python bin path is in your PATH if this command isn't found).

## 2. Configure API Access and Settings

Before using Nova, you need to provide your AI API credentials:

**Obtain an API key:** Sign up for an OpenAI API key or an Anthropic API key (you can use either or both).

**Set your API key via environment variables:** The simplest method is to export your key in the shell:

```bash
export OPENAI_API_KEY="sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXX"        # your OpenAI key
export ANTHROPIC_API_KEY="sk-ant-XXXXXXXXXXXXXXXXXXXXXXXX"     # your Anthropic key (if using Claude)
```

Nova will detect these environment variables at runtime. You can set one or both keys; Nova uses OpenAI (GPT-4) by default if both are present.

**Alternative: use a .env file:** Create a file named `.env` in the current directory and put your keys (and any Nova config overrides) there. For example:

```
OPENAI_API_KEY=sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
ANTHROPIC_API_KEY=sk-ant-XXXXXXXXXXXXXXXXXXXXXXXXX
```

Nova automatically loads this `.env` file on startup, so this is a convenient way to store your secrets and settings (just be sure not to commit this file to source control). You can also include optional settings in this file, like `NOVA_MAX_ITERS` or `NOVA_RUN_TIMEOUT_SEC`, to tweak Nova's defaults – but for a first run, defaults are fine.

**(Optional) Configuration file:** Nova supports a YAML config file for advanced options (e.g. choosing a model or adjusting safety limits). You can skip this for now, but we'll show an example in case you want to use it later. For instance, a `config.yaml` could specify:

```yaml
# config.yaml - Nova CI-Rescue configuration example
model: gpt-4 # which LLM model to use (if both keys provided)
timeout: 1800 # overall timeout in seconds (30 minutes)
max_iters: 8 # maximum fix iterations to attempt
max_changed_lines: 500 # safety limit: max lines changed per iteration
max_changed_files: 10 # safety limit: max files changed per iteration
blocked_paths: # file patterns Nova should never modify
  - "*.env"
  - ".github/workflows/*"
  - "secrets/*"
```

Save this file and run Nova with `--config config.yaml` to apply these settings. (Any CLI flags you provide will override the config file values on the fly.)

## 3. Run the Nova CI-Rescue Workflow (Fix Failing Tests)

Now you're ready to run Nova on a project and let it fix your tests. The primary command is `nova fix`, which runs Nova's autonomous agent on a target repository.

**Prepare a project with failing tests:** Navigate to a Git repository that has one or more failing tests (or introduce a failing test intentionally). Make sure all your changes are committed before running Nova – Nova will create new commits for its fixes, and having a clean commit history ensures you can revert if needed. It's also a good idea to be on a new branch for this experiment (Nova will create its own fix branch, but isolating your work is still wise).

**Run Nova to fix the tests:** Execute the `nova fix` command, pointing it at the repository. If you are already at the root of the repo, you can simply run:

```bash
nova fix .
```

This starts Nova's automated loop on the current project. By default, Nova allows up to 6 iterations of fixes and a total runtime of 20 minutes per `nova fix` run. You will see log output as Nova goes through its cycle of analyzing and fixing (to increase verbosity, you can add `--verbose`).

**Example:** If you want to adjust limits, you can specify options. For instance:

```bash
nova fix /path/to/your/repo --max-iters 3 --timeout 600
```

would limit Nova to 3 fix attempts or 10 minutes of runtime, whichever comes first. Nova will also automatically create a new Git branch (named something like `nova-fix-<timestamp>`) to apply changes, so your main branch remains untouched.

**Observe Nova's process:** Once running, Nova will autonomously cycle through a six-stage loop in each iteration. In each iteration, Nova will:

1. **Plan & Analyze:** Inspect the failing tests (parsing pytest or other test output) to understand the failure.

2. **Generate a Fix:** Propose a code change (patch) intended to fix the failure.

3. **Review (Critique) the Patch:** Evaluate the suggested patch to catch any obvious issues or irrelevant changes before applying it.

4. **Apply the Patch:** If the patch looks good, Nova applies the code changes to your repository and commits the changes to the fix branch.

5. **Run Tests:** Nova runs the test suite (by default using pytest) to see if the failures have been resolved.

6. **Reflect:** Analyze the test results. If tests are still failing and iteration limits remain, Nova will loop back to plan another fix, incorporating what it learned in the previous attempt.

Nova will print updates to the console at each step, so you can follow along with what it's doing. The logs will indicate which tests are failing, what fix is being attempted, and the outcome of each test run. By default Nova is optimized for Python projects using pytest as the test runner, so ensure your tests can be run with pytest (you can override the test command if needed, but in the happy path no extra configuration is required).

**Completion criteria:** Nova continues iterating until all tests pass ✅ or until it hits a safety limit (max iterations or timeout)⚠️. When Nova stops, it clearly logs the reason: for example, "✅ Exit Reason: SUCCESS - All tests passing!" when it fixes everything, or a timeout/message if it gave up. In a successful run, your terminal will show that all tests are now passing. If Nova reaches the iteration limit or cannot fix the issue, it will report how many tests are still failing or the reason it stopped. Either way, you will get a summary of what happened (number of iterations used, tests fixed, time taken, etc.).

**Example outcome:** In an internal demo, we seeded a project with 3 failing tests. Running `nova fix . --max-iters 3` fixed all 3 tests in under 3 minutes – Nova applied patches in 2 iterations, and the test suite went from 3 failures to 0. The final output showed a success message and summarized that 3 tests were fixed in 2 iterations. This is the ideal "happy path" result: Nova autonomously turned a red build green!

## 4. Review Outputs and Validate Success

Nova provides full transparency into what it did. After a run, inspect the outputs and artifacts to validate the fixes:

**.nova/ artifact directory:** In the root of your project, Nova creates a special directory named `.nova` containing a timestamped folder for each run (for example, `.nova/20250814T101530Z/`). This folder holds detailed logs and results from that run:

- **trace.jsonl:** A step-by-step log of Nova's internal reasoning and actions in JSON Lines format. This includes the prompts and responses from the AI, decisions made at each step, and other debug information. It's very useful for auditing or debugging the Nova run.

- **diffs/:** A subfolder with patch files for each iteration Nova performed. For instance, `step-1.patch`, `step-2.patch`, etc., each containing the unified diff of code changes that Nova applied in that iteration. You can open these files to see exactly what code was changed, or apply them with Git to review differences.

- **reports/:** A subfolder with test result files for each test run. For example, `step-1.xml` contains the test report (in JUnit XML or JSON format) after iteration 1, `step-2.xml` after the second, and so on. The final test results are also saved here (often as `final.xml` or simply the last step file), showing the state of the test suite at the end of the run.

You can quickly view the structure of the run folder. For example:

```
$ tree .nova/20250814T101530Z/
# .nova/20250814T101530Z/
# ├── trace.jsonl        # Complete execution log of Nova's agent
# ├── diffs/
# │   ├── step-1.patch   # Patch applied in iteration 1
# │   └── step-2.patch   # Patch applied in iteration 2
# └── reports/
#     ├── step-1.xml     # Test results after iteration 1
#     └── step-2.xml     # Test results after iteration 2
```

These artifacts give you a full audit trail of what happened. For instance, you can review the patch files to understand the code changes Nova made, or open the XML report of the final iteration to ensure all tests passed.

**Validate the fixes:** If Nova reported success, you should find that the last test report shows zero failures. It's a good practice to double-check by running your test suite manually as well (e.g. run `pytest` yourself) to confirm everything is green. The Nova console output and the `final.xml` report should indicate all tests are passing. If some tests are still failing (in case Nova stopped without full success), you can examine the reports to see which tests remain red and inspect the `trace.jsonl` for clues on what Nova attempted.

**Keeping or discarding the changes:** Nova's changes live on a separate Git branch that it created (by default named `nova-fix-<timestamp>`). At this point, you have options:

- **Keep the fixes:** Merge the Nova fix branch into your main branch. You might do this by opening a Pull Request or simply merging locally with Git. Review the commits that Nova made (each patch is a commit) to ensure you're satisfied, then integrate them. In CI usage, Nova can also post a summary comment on a PR for review, but locally you merge as usual.

- **Discard the changes:** If you decide not to use Nova's fixes (or it didn't manage to fix everything), simply checkout your original branch and delete the `nova-fix...` branch. Because Nova committed all its changes on that separate branch, your main branch is unchanged. In case you ran Nova on a detached HEAD or directly on your working directory, you can undo the changes with Git. For example, to reset to the original state before Nova ran, use:

```bash
git reset --hard HEAD   # resets to last committed state before Nova ran
git clean -fd           # removes any new untracked files (like the .nova/ folder)
```

This will wipe out Nova's commits and any new files, restoring the repo to the baseline state (again, this assumes you had committed your work before running Nova, as recommended).

**Next steps:** Congratulations – you have successfully run Nova CI-Rescue on your project! 🎉 Your previously failing tests should now be passing, and you've saved time by letting the AI do the heavy lifting. You can now continue development with a green test suite. Consider integrating Nova into your CI pipeline for automated usage on pull requests or failed CI runs (Nova provides a GitHub Action workflow for this purpose, see docs), so that future test failures can be fixed autonomously. For now, you have experienced the end-to-end happy path of Nova fixing a broken build and learned how to configure and inspect it along the way. Enjoy your healthier CI pipelines!
