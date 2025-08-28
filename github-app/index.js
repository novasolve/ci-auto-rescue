export default (app, { getRouter }) => {
  app.log.info('Nova CI-Rescue GitHub App loaded');

  // Health check route
  const router = getRouter('/');
  router.get('/health', (req, res) => {
    res.status(200).json({
      status: 'ok',
      timestamp: new Date().toISOString(),
      service: 'nova-ci-rescue-github-app',
      version: process.env.npm_package_version || '1.0.0'
    });
  });

  // Nova CI-Rescue auto-trigger functionality disabled
  // Uncomment the block below to re-enable automatic CI rescue
  /*
  app.on(['pull_request.opened', 'workflow_run.completed', 'check_suite.requested'], async (context) => {
    const { owner, repo } = context.repo();

    const headSha =
      context.payload.pull_request?.head?.sha ||
      context.payload.workflow_run?.head_sha ||
      context.payload.check_suite?.head_sha;
    if (!headSha) return;

    let checkSummary = 'Nova CI-Rescue is installed. Waiting for CI results...';
    let checkConclusion = 'neutral';

    // If a workflow run just finished and failed on a PR, try to trigger Nova workflow
    if (context.name === 'workflow_run' && context.payload.action === 'completed') {
      const workflowRun = context.payload.workflow_run;
      const failed = workflowRun?.conclusion === 'failure';
      const pr = workflowRun?.pull_requests?.[0];
      const headBranch = workflowRun?.head_branch || pr?.head?.ref;

      if (failed && pr) {
        try {
          // Find the Nova workflow in the repository by name or file path
          const { data } = await context.octokit.actions.listRepoWorkflows({ owner, repo });
          const novaWf = data.workflows.find(
            (wf) => wf?.name === 'Nova CI-Rescue Auto-Fix' || (wf?.path || '').endsWith('/nova-ci-rescue.yml')
          );

          if (novaWf) {
            await context.octokit.actions.createWorkflowDispatch({
              owner,
              repo,
              workflow_id: novaWf.id,
              ref: headBranch || 'main',
              inputs: { pr_number: String(pr.number) },
            });

            const actionsLink = `https://github.com/${owner}/${repo}/actions/workflows/${encodeURIComponent(
              novaWf.path.split('/').pop() || 'nova-ci-rescue.yml'
            )}`;

            checkSummary = `CI failed on PR #${pr.number}. Triggered 'Nova CI-Rescue Auto-Fix' for branch \`${headBranch}\`. View progress in Actions: ${actionsLink}`;
          } else {
            checkSummary =
              "CI failed on this PR, but the 'Nova CI-Rescue Auto-Fix' workflow was not found. Add .github/workflows/nova-ci-rescue.yml to enable auto-fix.";
          }
        } catch (err) {
          const message = err && err.message ? err.message : 'unknown error';
          checkSummary = `Attempted to trigger Nova CI-Rescue but encountered an error: ${message}`;
        }

        // Leave a lightweight comment on the PR for visibility
        try {
          await context.octokit.issues.createComment({
            owner,
            repo,
            issue_number: pr.number,
            body: checkSummary,
          });
        } catch (_) {
          // Best-effort: do not fail the handler if commenting fails
        }
      }
    }

    await context.octokit.checks.create({
      owner,
      repo,
      name: 'Nova CI-Rescue',
      head_sha: headSha,
      status: 'completed',
      conclusion: checkConclusion,
      output: {
        title: 'CI-Rescue',
        summary: checkSummary,
      },
    });
  });
  */

  // Basic ping handler for testing
  app.on('ping', async (context) => {
    context.log.info('Received webhook ping - Nova CI auto-trigger is disabled');
  });
};
