'use strict';

/**
 * Minimal Probot App
 * - Listens for ping and basic events
 * - Ready for production deployment on Fly.io
 *
 * Required env vars (set as Fly secrets):
 * - APP_ID
 * - PRIVATE_KEY (PEM contents)
 * - WEBHOOK_SECRET
 * Optional:
 * - PORT (default 3000)
 */

module.exports = (app) => {
  app.log.info('ci-auto-rescue GitHub App loaded');

  app.on('ping', async (context) => {
    context.log.info('Received webhook ping');
  });

  app.on('installation.created', async (context) => {
    context.log.info('App installed', {
      account: context.payload.installation?.account?.login,
    });
  });

  app.on('issues.opened', async (context) => {
    const issueComment = context.issue({
      body: 'Thanks for opening this issue! The app is running on Fly.io ✅',
    });
    await context.octokit.issues.createComment(issueComment);
  });
};


