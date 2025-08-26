export default (app) => {
  app.log.info('Nova CI-Rescue GitHub App loaded');

  app.on(['pull_request.opened', 'workflow_run.completed', 'check_suite.requested'], async (context) => {
    const { owner, repo } = context.repo();

    const headSha =
      context.payload.pull_request?.head?.sha ||
      context.payload.workflow_run?.head_sha ||
      context.payload.check_suite?.head_sha;
    if (!headSha) return;

    await context.octokit.checks.create({
      owner,
      repo,
      name: 'Nova CI-Rescue',
      head_sha: headSha,
      status: 'completed',
      conclusion: 'neutral',
      output: {
        title: 'CI-Rescue ran',
        summary:
          'This is a placeholder check. Hook your logic here (e.g., detect failures, propose fixes, open PRs).',
      },
    });

    const failed = context.payload.workflow_run?.conclusion === 'failure';
    const prNumber = context.payload.pull_request?.number || context.payload.workflow_run?.pull_requests?.[0]?.number;
    if (failed && prNumber) {
      await context.octokit.issues.createComment({
        owner,
        repo,
        issue_number: prNumber,
        body: '⚠️ CI failed. Nova can open a fix branch or suggest remediation steps.',
      });
    }
  });
};


