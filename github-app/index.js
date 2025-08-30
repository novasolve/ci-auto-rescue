import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default (app, { getRouter }) => {
  app.log.info('Nova CI-Rescue GitHub App loaded');

  // Track active installations with persistent storage
  const installations = new Map();
  const dataDir = process.env.FLY_VOLUME_PATH || '/data';
  const installationsFile = path.join(dataDir, 'installations.json');

  // Load installations from persistent storage if available
  try {
    if (fs.existsSync(installationsFile)) {
      const data = JSON.parse(fs.readFileSync(installationsFile, 'utf8'));
      data.forEach(install => installations.set(install.id, install));
      app.log.info(`Loaded ${installations.size} installations from storage`);
    }
  } catch (error) {
    app.log.error('Failed to load installations from storage', error);
  }

  // Helper to persist installations
  function saveInstallations() {
    try {
      if (!fs.existsSync(dataDir)) {
        fs.mkdirSync(dataDir, { recursive: true });
      }
      fs.writeFileSync(installationsFile, JSON.stringify([...installations.values()], null, 2));
    } catch (error) {
      app.log.error('Failed to save installations', error);
    }
  }

  // Graceful shutdown handling
  process.on('SIGTERM', () => {
    app.log.info('SIGTERM received, saving data and shutting down gracefully');
    saveInstallations();
    process.exit(0);
  });

  // Rate limiting tracking
  const rateLimits = new Map();
  const RATE_LIMIT_WINDOW = 60000; // 1 minute
  const RATE_LIMIT_MAX_REQUESTS = 30; // 30 requests per minute per installation

  // Check rate limit
  function checkRateLimit(installationId) {
    const now = Date.now();
    const key = `install-${installationId}`;

    if (!rateLimits.has(key)) {
      rateLimits.set(key, { count: 1, resetAt: now + RATE_LIMIT_WINDOW });
      return true;
    }

    const limit = rateLimits.get(key);
    if (now > limit.resetAt) {
      limit.count = 1;
      limit.resetAt = now + RATE_LIMIT_WINDOW;
      return true;
    }

    if (limit.count >= RATE_LIMIT_MAX_REQUESTS) {
      return false;
    }

    limit.count++;
    return true;
  }

  // Add custom routes using getRouter
  if (getRouter) {
    const router = getRouter('/');

    // Enhanced health endpoint with installation and end-to-end validation
    router.get('/health', async (req, res) => {
      const memoryUsage = process.memoryUsage();

      // Test GitHub authentication and installation flow
      let githubAuth = 'unchecked';
      let githubError = null;
      let installFlowTest = 'unchecked';
      let installFlowError = null;
      let appDetails = null;

      // Installation validation
      let installationValidation = 'unchecked';
      let installValidationError = null;
      let oneClickPathTest = 'unchecked';
      let oneClickPathError = null;

      // End-to-end testing capability
      let endToEndTest = 'unchecked';
      let endToEndError = null;

      try {
        // Check if we have the required credentials
        if (process.env.APP_ID && process.env.PRIVATE_KEY && process.env.WEBHOOK_SECRET) {
          // Step 1: Test basic app authentication
          try {
            const auth = await app.auth();
            // app.auth() returns an Octokit instance if successful
            githubAuth = 'authenticated';

            // Step 2: Test installation flow capabilities
            try {
              // Test 2a: Get app details
              const appInfo = await app.octokit.apps.getAuthenticated();
              appDetails = {
                name: appInfo.data.name,
                slug: appInfo.data.slug,
                permissions: appInfo.data.permissions,
                events: appInfo.data.events
              };

              // Test 2b: List installations (this tests the app's ability to see installations)
              const installations = await app.octokit.apps.listInstallations();
              installFlowTest = 'passed';

              // Test 2c: If there are installations, test installation authentication
              if (installations.data.length > 0) {
                const firstInstall = installations.data[0];
                const installAuth = await app.auth(firstInstall.id);
                if (installAuth) {
                  installFlowTest = 'installation_auth_passed';
                }
              }

            } catch (installError) {
              installFlowTest = 'partial';
              installFlowError = `Installation flow test failed: ${installError.message}`;
            }

          } catch (authError) {
            githubAuth = 'auth_failed';
            githubError = `Authentication failed: ${authError.message}`;
          }
        } else {
          githubAuth = 'missing_credentials';
          githubError = 'Missing APP_ID, PRIVATE_KEY, or WEBHOOK_SECRET';
        }
      } catch (error) {
        githubAuth = 'failed';
        githubError = error.message;
        installFlowTest = 'failed';
        installFlowError = error.message;
      }

      // Determine overall health status
      let overallStatus = 'healthy';
      let overallError = null;

      if (githubAuth !== 'authenticated') {
        overallStatus = 'unhealthy';
        overallError = githubError || 'GitHub authentication failed';
      } else if (installFlowTest === 'failed') {
        overallStatus = 'degraded';
        overallError = installFlowError || 'Installation flow test failed';
      } else if (installFlowTest === 'partial') {
        overallStatus = 'degraded';
        overallError = installFlowError || 'Installation flow partially working';
      }

      const healthStatus = {
        status: overallStatus,
        service: 'nova-ci-rescue',
        timestamp: new Date().toISOString(),
        version: process.env.APP_VERSION || '1.0.0',
        installations_count: installations.size,
        error: overallError,
        github: {
          auth_status: githubAuth,
          error: githubError,
          app_id: process.env.APP_ID ? 'configured' : 'missing',
          private_key: process.env.PRIVATE_KEY ? 'configured' : 'missing',
          webhook_secret: process.env.WEBHOOK_SECRET ? 'configured' : 'missing',
          install_flow_test: installFlowTest,
          install_flow_error: installFlowError,
          app_details: appDetails
        },
        memory: {
          used_mb: Math.round(memoryUsage.heapUsed / 1024 / 1024),
          total_mb: Math.round(memoryUsage.heapTotal / 1024 / 1024)
        },
        uptime_seconds: Math.floor(process.uptime())
      };

      // Return appropriate HTTP status
      const httpStatus = overallStatus === 'healthy' ? 200 :
                        overallStatus === 'degraded' ? 200 : 503;

      res.status(httpStatus).json(healthStatus);
    });

    // Root endpoint for basic checks
    router.get('/', (req, res) => {
      res.status(200).send(`
        <!DOCTYPE html>
        <html>
        <head>
          <title>Nova CI-Rescue</title>
          <style>
            body {
              font-family: -apple-system, system-ui, sans-serif;
              max-width: 600px;
              margin: 100px auto;
              padding: 20px;
              text-align: center;
            }
            h1 { font-size: 48px; margin: 0; }
            .logo { font-size: 72px; margin-bottom: 20px; }
            .links { margin-top: 30px; }
            a {
              color: #0366d6;
              text-decoration: none;
              margin: 0 10px;
            }
            a:hover { text-decoration: underline; }
            .status {
              background: #d1f5d3;
              padding: 10px 20px;
              border-radius: 6px;
              display: inline-block;
              margin-top: 20px;
            }
          </style>
        </head>
        <body>
          <div class="logo">🤖</div>
          <h1>Nova CI-Rescue</h1>
          <p>GitHub App is running! 🚀</p>
          <div class="status">✅ Healthy - ${installations.size} active installations</div>
          <div class="links">
            <a href="/setup">Setup Guide</a> •
            <a href="/health">Health Status</a> •
            <a href="https://github.com/marketplace/nova-ci-rescue">Marketplace</a>
          </div>
        </body>
        </html>
      `);
    });

    // Setup guide endpoint
    router.get('/setup', (req, res) => {
      const setupPath = path.join(__dirname, 'templates', 'setup.html');

      fs.readFile(setupPath, 'utf8', (err, data) => {
        if (err) {
          app.log.error('Failed to read setup guide', err);
          res.status(500).send('Setup guide not found');
          return;
        }
        res.status(200).send(data);
      });
    });

    // Detailed probe endpoint for monitoring
    router.get('/probe', async (req, res) => {
      try {
        // Check if we can authenticate with GitHub
        const authenticated = app.state?.id ? true : false;

        res.status(200).json({
          status: 'healthy',
          service: 'nova-ci-rescue',
          timestamp: new Date().toISOString(),
          version: process.env.APP_VERSION || '1.0.0',
          checks: {
            github_auth: authenticated ? 'connected' : 'pending',
            app_id: process.env.APP_ID ? 'configured' : 'missing',
            webhook_secret: process.env.WEBHOOK_SECRET ? 'configured' : 'missing'
          },
          stats: {
            active_installations: installations.size,
            uptime: process.uptime()
          }
        });
      } catch (error) {
        res.status(503).json({
          status: 'unhealthy',
          error: error.message
        });
      }
    });
  }

  // Handle new installations
  app.on('installation.created', async (context) => {
    const { installation, sender } = context.payload;
    const installationId = installation.id;
    const account = installation.account;

    // Track installation
    installations.set(installationId, {
      id: installationId,
      account: account.login,
      type: account.type,
      created_at: new Date().toISOString(),
      repositories: installation.repository_selection === 'all' ? 'all' : installation.repositories
    });

    // Persist to storage
    saveInstallations();

    context.log.info('New installation created', {
      installation_id: installationId,
      account: account.login,
      account_type: account.type,
      repository_selection: installation.repository_selection
    });

    // Create a welcome issue in each repository
    if (installation.repositories && installation.repository_selection === 'selected') {
      for (const repo of installation.repositories) {
        try {
          await createWelcomeIssue(context, account.login, repo.name);
        } catch (error) {
          context.log.error('Failed to create welcome issue', {
            repo: repo.name,
            error: error.message
          });
        }
      }
    }
  });

  // Handle installation deletions
  app.on('installation.deleted', async (context) => {
    const { installation } = context.payload;
    const installationId = installation.id;

    installations.delete(installationId);

    // Persist to storage
    saveInstallations();

    context.log.info('Installation deleted', {
      installation_id: installationId,
      account: installation.account.login
    });
  });

  // Handle repository additions to installation
  app.on('installation_repositories.added', async (context) => {
    const { installation, repositories_added, sender } = context.payload;

    context.log.info('Repositories added to installation', {
      installation_id: installation.id,
      account: installation.account.login,
      repos_added: repositories_added.map(r => r.name)
    });

    // Create welcome issues in newly added repositories
    for (const repo of repositories_added) {
      try {
        await createWelcomeIssue(context, installation.account.login, repo.name);
      } catch (error) {
        context.log.error('Failed to create welcome issue', {
          repo: repo.name,
          error: error.message
        });
      }
    }
  });

  // Handle repository removals from installation
  app.on('installation_repositories.removed', async (context) => {
    const { installation, repositories_removed } = context.payload;

    context.log.info('Repositories removed from installation', {
      installation_id: installation.id,
      account: installation.account.login,
      repos_removed: repositories_removed.map(r => r.name)
    });
  });

  // Main CI rescue logic
  app.on(['pull_request.opened', 'workflow_run.completed', 'check_suite.requested'], async (context) => {
    const { owner, repo } = context.repo();
    const installationId = context.payload.installation?.id;

    // Check rate limit
    if (installationId && !checkRateLimit(installationId)) {
      context.log.warn('Rate limit exceeded', {
        installation_id: installationId,
        owner,
        repo
      });
      return;
    }

    // Log event with installation context
    context.log.info(`Event: ${context.name}`, {
      installation_id: installationId,
      owner,
      repo,
      event_action: context.payload.action
    });

    const headSha =
      context.payload.pull_request?.head?.sha ||
      context.payload.workflow_run?.head_sha ||
      context.payload.check_suite?.head_sha;

    if (!headSha) {
      context.log.warn('No head SHA found for event', { event: context.name });
      return;
    }

    let checkSummary = 'Nova CI-Rescue is monitoring your CI. Waiting for results...';
    let checkConclusion = 'neutral';

    // Handle new PR opened
    if (context.name === 'pull_request' && context.payload.action === 'opened') {
      try {
        await context.octokit.checks.create({
          owner,
          repo,
          name: 'Nova CI-Rescue',
          head_sha: headSha,
          status: 'completed',
          conclusion: 'neutral',
          output: {
            title: 'CI-Rescue Ready',
            summary: '🤖 Nova CI-Rescue is monitoring this PR. If your CI fails, I\'ll attempt to fix it automatically!',
          },
        });
      } catch (error) {
        context.log.error('Failed to create initial check', { error: error.message });
      }
      return;
    }

    // Handle workflow run completion
    if (context.name === 'workflow_run' && context.payload.action === 'completed') {
      const workflowRun = context.payload.workflow_run;
      const failed = workflowRun?.conclusion === 'failure';
      const pr = workflowRun?.pull_requests?.[0];
      const headBranch = workflowRun?.head_branch || pr?.head?.ref;

      if (failed && pr) {
        context.log.info('CI failure detected on PR', {
          pr_number: pr.number,
          workflow_name: workflowRun.name,
          branch: headBranch
        });

        try {
          // Check if Nova workflow exists
          const { data } = await context.octokit.actions.listRepoWorkflows({ owner, repo });
          const novaWf = data.workflows.find(
            (wf) => wf?.name === 'Nova CI-Rescue Auto-Fix' ||
                    (wf?.path || '').endsWith('/nova-ci-rescue.yml') ||
                    (wf?.path || '').endsWith('/nova-ci-rescue.yaml')
          );

          if (novaWf) {
            // Trigger Nova workflow
            await context.octokit.actions.createWorkflowDispatch({
              owner,
              repo,
              workflow_id: novaWf.id,
              ref: headBranch || 'main',
              inputs: {
                pr_number: String(pr.number),
                triggered_by: 'github-app'
              },
            });

            const actionsLink = `https://github.com/${owner}/${repo}/actions/workflows/${encodeURIComponent(
              novaWf.path.split('/').pop() || 'nova-ci-rescue.yml'
            )}`;

            checkSummary = `🔧 CI failed on PR #${pr.number}. I've triggered Nova CI-Rescue to attempt automatic fixes!\n\n` +
                          `**Branch:** \`${headBranch}\`\n` +
                          `**Failed Workflow:** ${workflowRun.name}\n` +
                          `**Nova Progress:** [View in Actions](${actionsLink})\n\n` +
                          `I'll analyze the failures and try to fix them automatically. This may take a few minutes.`;

            checkConclusion = 'success';

            // Leave a comment on the PR
            await context.octokit.issues.createComment({
              owner,
              repo,
              issue_number: pr.number,
              body: `## 🤖 Nova CI-Rescue Activated!\n\n` +
                    `I detected that your CI failed and I'm now attempting to fix it automatically.\n\n` +
                    `**What I'm doing:**\n` +
                    `- 🔍 Analyzing the test failures\n` +
                    `- 🛠️ Generating fixes for the failing tests\n` +
                    `- 📝 Creating a commit with the fixes\n\n` +
                    `**Track progress:** [View in GitHub Actions](${actionsLink})\n\n` +
                    `If I can fix the issues, I'll push a commit to your branch. Otherwise, I'll provide details about what went wrong.`,
            });

            context.log.info('Nova workflow triggered successfully', {
              pr_number: pr.number,
              workflow_id: novaWf.id
            });
          } else {
            checkSummary = `⚠️ CI failed on PR #${pr.number}, but Nova CI-Rescue workflow not found.\n\n` +
                          `**To enable automatic fixes:**\n` +
                          `1. Add \`.github/workflows/nova-ci-rescue.yml\` to your repository\n` +
                          `2. Configure the workflow with your Nova API key\n` +
                          `3. Push the changes\n\n` +
                          `[Learn more about Nova CI-Rescue](https://github.com/nova-ci-rescue/docs)`;

            checkConclusion = 'neutral';

            // Provide setup instructions
            await context.octokit.issues.createComment({
              owner,
              repo,
              issue_number: pr.number,
              body: `## ⚠️ CI Failed - Nova CI-Rescue Not Configured\n\n` +
                    `I noticed your CI failed, but I can't help yet because the Nova workflow isn't set up.\n\n` +
                    `**Quick Setup:**\n` +
                    `\`\`\`bash\n` +
                    `# Add Nova workflow to your repo\n` +
                    `curl -L https://raw.githubusercontent.com/nova-ci-rescue/templates/main/nova-ci-rescue.yml > .github/workflows/nova-ci-rescue.yml\n` +
                    `\n` +
                    `# Set your Nova API key as a repository secret\n` +
                    `# Go to Settings > Secrets > Actions > New repository secret\n` +
                    `# Name: NOVA_API_KEY\n` +
                    `# Value: your-nova-api-key\n` +
                    `\`\`\`\n\n` +
                    `Once configured, I'll automatically fix failing tests on your PRs! 🚀`,
            });
          }
        } catch (err) {
          const message = err?.message || 'unknown error';
          checkSummary = `❌ Error: Failed to trigger Nova CI-Rescue: ${message}`;
          checkConclusion = 'failure';

          context.log.error('Failed to handle CI failure', {
            error: message,
            pr_number: pr?.number
          });
        }

        // Update check status
        await context.octokit.checks.create({
          owner,
          repo,
          name: 'Nova CI-Rescue',
          head_sha: headSha,
          status: 'completed',
          conclusion: checkConclusion,
          output: {
            title: checkConclusion === 'success' ? 'CI-Rescue Triggered' : 'CI-Rescue Status',
            summary: checkSummary,
          },
        });
      }
    }
  });

  // Helper function to create welcome issue
  async function createWelcomeIssue(context, owner, repo) {
    const issueBody = `# 🎉 Welcome to Nova CI-Rescue!\n\n` +
      `Thank you for installing Nova CI-Rescue! This GitHub App will automatically attempt to fix failing tests in your pull requests.\n\n` +
      `## 🚀 Quick Setup\n\n` +
      `To complete the setup, you need to add the Nova workflow to your repository:\n\n` +
      `### 1. Create the workflow file\n` +
      `Create \`.github/workflows/nova-ci-rescue.yml\` with the following content:\n\n` +
      `\`\`\`yaml\n` +
      `name: Nova CI-Rescue Auto-Fix\n` +
      `on:\n` +
      `  workflow_dispatch:\n` +
      `    inputs:\n` +
      `      pr_number:\n` +
      `        description: 'Pull request number to fix'\n` +
      `        required: true\n` +
      `        type: string\n\n` +
      `jobs:\n` +
      `  auto-fix:\n` +
      `    runs-on: ubuntu-latest\n` +
      `    steps:\n` +
      `      - uses: actions/checkout@v4\n` +
      `        with:\n` +
      `          token: \${{ secrets.GITHUB_TOKEN }}\n` +
      `          fetch-depth: 0\n\n` +
      `      - name: Run Nova CI-Rescue\n` +
      `        uses: nova-ci-rescue/action@v1\n` +
      `        with:\n` +
      `          pr_number: \${{ inputs.pr_number }}\n` +
      `          nova_api_key: \${{ secrets.NOVA_API_KEY }}\n` +
      `\`\`\`\n\n` +
      `### 2. Add your Nova API key\n` +
      `1. Go to **Settings** → **Secrets and variables** → **Actions**\n` +
      `2. Click **New repository secret**\n` +
      `3. Name: \`NOVA_API_KEY\`\n` +
      `4. Value: Your Nova API key (get one at [nova-ci.com](https://nova-ci.com))\n\n` +
      `## ✅ That's it!\n\n` +
      `Once configured, Nova CI-Rescue will:\n` +
      `- Monitor all pull requests for CI failures\n` +
      `- Automatically attempt to fix failing tests\n` +
      `- Push fixes directly to the PR branch\n` +
      `- Comment with the results\n\n` +
      `## 📚 Resources\n` +
      `- [Documentation](https://github.com/nova-ci-rescue/docs)\n` +
      `- [Example repositories](https://github.com/nova-ci-rescue/examples)\n` +
      `- [Support](https://github.com/nova-ci-rescue/support)\n\n` +
      `---\n` +
      `*This issue was created automatically by Nova CI-Rescue. Feel free to close it once you've completed the setup!*`;

    await context.octokit.issues.create({
      owner,
      repo,
      title: '🤖 Nova CI-Rescue Setup Instructions',
      body: issueBody,
      labels: ['nova-ci-rescue', 'setup']
    });
  }
};
      let githubError = null;
      let installFlowTest = 'unchecked';
      let installFlowError = null;
      let appDetails = null;

      try {
        // Check if we have the required credentials
        if (process.env.APP_ID && process.env.PRIVATE_KEY && process.env.WEBHOOK_SECRET) {
          // Step 1: Test basic app authentication
          try {
            const auth = await app.auth();
            // app.auth() returns an Octokit instance if successful
            githubAuth = 'authenticated';

            // Step 2: Test installation flow capabilities
            try {
              // Test 2a: Get app details
              const appInfo = await app.octokit.apps.getAuthenticated();
              appDetails = {
                name: appInfo.data.name,
                slug: appInfo.data.slug,
                permissions: appInfo.data.permissions,
                events: appInfo.data.events
              };

              // Test 2b: List installations (this tests the app's ability to see installations)
              const installations = await app.octokit.apps.listInstallations();
              installFlowTest = 'passed';

              // Test 2c: If there are installations, test installation authentication
              if (installations.data.length > 0) {
                const firstInstall = installations.data[0];
                const installAuth = await app.auth(firstInstall.id);
                if (installAuth) {
                  installFlowTest = 'installation_auth_passed';
                }
              }

            } catch (installError) {
              installFlowTest = 'partial';
              installFlowError = `Installation flow test failed: ${installError.message}`;
            }

          } catch (authError) {
            githubAuth = 'auth_failed';
            githubError = `Authentication failed: ${authError.message}`;
          }
        } else {
          githubAuth = 'missing_credentials';
          githubError = 'Missing APP_ID, PRIVATE_KEY, or WEBHOOK_SECRET';
        }
      } catch (error) {
        githubAuth = 'failed';
        githubError = error.message;
        installFlowTest = 'failed';
        installFlowError = error.message;
      }

      // Determine overall health status
      let overallStatus = 'healthy';
      let overallError = null;

      if (githubAuth !== 'authenticated') {
        overallStatus = 'unhealthy';
        overallError = githubError || 'GitHub authentication failed';
      } else if (installFlowTest === 'failed') {
        overallStatus = 'degraded';
        overallError = installFlowError || 'Installation flow test failed';
      } else if (installFlowTest === 'partial') {
        overallStatus = 'degraded';
        overallError = installFlowError || 'Installation flow partially working';
      }

      const healthStatus = {
        status: overallStatus,
        service: 'nova-ci-rescue',
        timestamp: new Date().toISOString(),
        version: process.env.APP_VERSION || '1.0.0',
        installations_count: installations.size,
        error: overallError,
        github: {
          auth_status: githubAuth,
          error: githubError,
          app_id: process.env.APP_ID ? 'configured' : 'missing',
          private_key: process.env.PRIVATE_KEY ? 'configured' : 'missing',
          webhook_secret: process.env.WEBHOOK_SECRET ? 'configured' : 'missing',
          install_flow_test: installFlowTest,
          install_flow_error: installFlowError,
          app_details: appDetails
        },
        memory: {
          used_mb: Math.round(memoryUsage.heapUsed / 1024 / 1024),
          total_mb: Math.round(memoryUsage.heapTotal / 1024 / 1024)
        },
        uptime_seconds: Math.floor(process.uptime())
      };

      // Return appropriate HTTP status
      const httpStatus = overallStatus === 'healthy' ? 200 :
                        overallStatus === 'degraded' ? 200 : 503;

      res.status(httpStatus).json(healthStatus);
    });

    // Root endpoint for basic checks
    router.get('/', (req, res) => {
      res.status(200).send(`
        <!DOCTYPE html>
        <html>
        <head>
          <title>Nova CI-Rescue</title>
          <style>
            body {
              font-family: -apple-system, system-ui, sans-serif;
              max-width: 600px;
              margin: 100px auto;
              padding: 20px;
              text-align: center;
            }
            h1 { font-size: 48px; margin: 0; }
            .logo { font-size: 72px; margin-bottom: 20px; }
            .links { margin-top: 30px; }
            a {
              color: #0366d6;
              text-decoration: none;
              margin: 0 10px;
            }
            a:hover { text-decoration: underline; }
            .status {
              background: #d1f5d3;
              padding: 10px 20px;
              border-radius: 6px;
              display: inline-block;
              margin-top: 20px;
            }
          </style>
        </head>
        <body>
          <div class="logo">🤖</div>
          <h1>Nova CI-Rescue</h1>
          <p>GitHub App is running! 🚀</p>
          <div class="status">✅ Healthy - ${installations.size} active installations</div>
          <div class="links">
            <a href="/setup">Setup Guide</a> •
            <a href="/health">Health Status</a> •
            <a href="https://github.com/marketplace/nova-ci-rescue">Marketplace</a>
          </div>
        </body>
        </html>
      `);
    });

    // Setup guide endpoint
    router.get('/setup', (req, res) => {
      const setupPath = path.join(__dirname, 'templates', 'setup.html');

      fs.readFile(setupPath, 'utf8', (err, data) => {
        if (err) {
          app.log.error('Failed to read setup guide', err);
          res.status(500).send('Setup guide not found');
          return;
        }
        res.status(200).send(data);
      });
    });

    // Detailed probe endpoint for monitoring
    router.get('/probe', async (req, res) => {
      try {
        // Check if we can authenticate with GitHub
        const authenticated = app.state?.id ? true : false;

        res.status(200).json({
          status: 'healthy',
          service: 'nova-ci-rescue',
          timestamp: new Date().toISOString(),
          version: process.env.APP_VERSION || '1.0.0',
          checks: {
            github_auth: authenticated ? 'connected' : 'pending',
            app_id: process.env.APP_ID ? 'configured' : 'missing',
            webhook_secret: process.env.WEBHOOK_SECRET ? 'configured' : 'missing'
          },
          stats: {
            active_installations: installations.size,
            uptime: process.uptime()
          }
        });
      } catch (error) {
        res.status(503).json({
          status: 'unhealthy',
          error: error.message
        });
      }
    });
  }

  // Handle new installations
  app.on('installation.created', async (context) => {
    const { installation, sender } = context.payload;
    const installationId = installation.id;
    const account = installation.account;

    // Track installation
    installations.set(installationId, {
      id: installationId,
      account: account.login,
      type: account.type,
      created_at: new Date().toISOString(),
      repositories: installation.repository_selection === 'all' ? 'all' : installation.repositories
    });

    // Persist to storage
    saveInstallations();

    context.log.info('New installation created', {
      installation_id: installationId,
      account: account.login,
      account_type: account.type,
      repository_selection: installation.repository_selection
    });

    // Create a welcome issue in each repository
    if (installation.repositories && installation.repository_selection === 'selected') {
      for (const repo of installation.repositories) {
        try {
          await createWelcomeIssue(context, account.login, repo.name);
        } catch (error) {
          context.log.error('Failed to create welcome issue', {
            repo: repo.name,
            error: error.message
          });
        }
      }
    }
  });

  // Handle installation deletions
  app.on('installation.deleted', async (context) => {
    const { installation } = context.payload;
    const installationId = installation.id;

    installations.delete(installationId);

    // Persist to storage
    saveInstallations();

    context.log.info('Installation deleted', {
      installation_id: installationId,
      account: installation.account.login
    });
  });

  // Handle repository additions to installation
  app.on('installation_repositories.added', async (context) => {
    const { installation, repositories_added, sender } = context.payload;

    context.log.info('Repositories added to installation', {
      installation_id: installation.id,
      account: installation.account.login,
      repos_added: repositories_added.map(r => r.name)
    });

    // Create welcome issues in newly added repositories
    for (const repo of repositories_added) {
      try {
        await createWelcomeIssue(context, installation.account.login, repo.name);
      } catch (error) {
        context.log.error('Failed to create welcome issue', {
          repo: repo.name,
          error: error.message
        });
      }
    }
  });

  // Handle repository removals from installation
  app.on('installation_repositories.removed', async (context) => {
    const { installation, repositories_removed } = context.payload;

    context.log.info('Repositories removed from installation', {
      installation_id: installation.id,
      account: installation.account.login,
      repos_removed: repositories_removed.map(r => r.name)
    });
  });

  // Main CI rescue logic
  app.on(['pull_request.opened', 'workflow_run.completed', 'check_suite.requested'], async (context) => {
    const { owner, repo } = context.repo();
    const installationId = context.payload.installation?.id;

    // Check rate limit
    if (installationId && !checkRateLimit(installationId)) {
      context.log.warn('Rate limit exceeded', {
        installation_id: installationId,
        owner,
        repo
      });
      return;
    }

    // Log event with installation context
    context.log.info(`Event: ${context.name}`, {
      installation_id: installationId,
      owner,
      repo,
      event_action: context.payload.action
    });

    const headSha =
      context.payload.pull_request?.head?.sha ||
      context.payload.workflow_run?.head_sha ||
      context.payload.check_suite?.head_sha;

    if (!headSha) {
      context.log.warn('No head SHA found for event', { event: context.name });
      return;
    }

    let checkSummary = 'Nova CI-Rescue is monitoring your CI. Waiting for results...';
    let checkConclusion = 'neutral';

    // Handle new PR opened
    if (context.name === 'pull_request' && context.payload.action === 'opened') {
      try {
        await context.octokit.checks.create({
          owner,
          repo,
          name: 'Nova CI-Rescue',
          head_sha: headSha,
          status: 'completed',
          conclusion: 'neutral',
          output: {
            title: 'CI-Rescue Ready',
            summary: '🤖 Nova CI-Rescue is monitoring this PR. If your CI fails, I\'ll attempt to fix it automatically!',
          },
        });
      } catch (error) {
        context.log.error('Failed to create initial check', { error: error.message });
      }
      return;
    }

    // Handle workflow run completion
    if (context.name === 'workflow_run' && context.payload.action === 'completed') {
      const workflowRun = context.payload.workflow_run;
      const failed = workflowRun?.conclusion === 'failure';
      const pr = workflowRun?.pull_requests?.[0];
      const headBranch = workflowRun?.head_branch || pr?.head?.ref;

      if (failed && pr) {
        context.log.info('CI failure detected on PR', {
          pr_number: pr.number,
          workflow_name: workflowRun.name,
          branch: headBranch
        });

        try {
          // Check if Nova workflow exists
          const { data } = await context.octokit.actions.listRepoWorkflows({ owner, repo });
          const novaWf = data.workflows.find(
            (wf) => wf?.name === 'Nova CI-Rescue Auto-Fix' ||
                    (wf?.path || '').endsWith('/nova-ci-rescue.yml') ||
                    (wf?.path || '').endsWith('/nova-ci-rescue.yaml')
          );

          if (novaWf) {
            // Trigger Nova workflow
            await context.octokit.actions.createWorkflowDispatch({
              owner,
              repo,
              workflow_id: novaWf.id,
              ref: headBranch || 'main',
              inputs: {
                pr_number: String(pr.number),
                triggered_by: 'github-app'
              },
            });

            const actionsLink = `https://github.com/${owner}/${repo}/actions/workflows/${encodeURIComponent(
              novaWf.path.split('/').pop() || 'nova-ci-rescue.yml'
            )}`;

            checkSummary = `🔧 CI failed on PR #${pr.number}. I've triggered Nova CI-Rescue to attempt automatic fixes!\n\n` +
                          `**Branch:** \`${headBranch}\`\n` +
                          `**Failed Workflow:** ${workflowRun.name}\n` +
                          `**Nova Progress:** [View in Actions](${actionsLink})\n\n` +
                          `I'll analyze the failures and try to fix them automatically. This may take a few minutes.`;

            checkConclusion = 'success';

            // Leave a comment on the PR
            await context.octokit.issues.createComment({
              owner,
              repo,
              issue_number: pr.number,
              body: `## 🤖 Nova CI-Rescue Activated!\n\n` +
                    `I detected that your CI failed and I'm now attempting to fix it automatically.\n\n` +
                    `**What I'm doing:**\n` +
                    `- 🔍 Analyzing the test failures\n` +
                    `- 🛠️ Generating fixes for the failing tests\n` +
                    `- 📝 Creating a commit with the fixes\n\n` +
                    `**Track progress:** [View in GitHub Actions](${actionsLink})\n\n` +
                    `If I can fix the issues, I'll push a commit to your branch. Otherwise, I'll provide details about what went wrong.`,
            });

            context.log.info('Nova workflow triggered successfully', {
              pr_number: pr.number,
              workflow_id: novaWf.id
            });
          } else {
            checkSummary = `⚠️ CI failed on PR #${pr.number}, but Nova CI-Rescue workflow not found.\n\n` +
                          `**To enable automatic fixes:**\n` +
                          `1. Add \`.github/workflows/nova-ci-rescue.yml\` to your repository\n` +
                          `2. Configure the workflow with your Nova API key\n` +
                          `3. Push the changes\n\n` +
                          `[Learn more about Nova CI-Rescue](https://github.com/nova-ci-rescue/docs)`;

            checkConclusion = 'neutral';

            // Provide setup instructions
            await context.octokit.issues.createComment({
              owner,
              repo,
              issue_number: pr.number,
              body: `## ⚠️ CI Failed - Nova CI-Rescue Not Configured\n\n` +
                    `I noticed your CI failed, but I can't help yet because the Nova workflow isn't set up.\n\n` +
                    `**Quick Setup:**\n` +
                    `\`\`\`bash\n` +
                    `# Add Nova workflow to your repo\n` +
                    `curl -L https://raw.githubusercontent.com/nova-ci-rescue/templates/main/nova-ci-rescue.yml > .github/workflows/nova-ci-rescue.yml\n` +
                    `\n` +
                    `# Set your Nova API key as a repository secret\n` +
                    `# Go to Settings > Secrets > Actions > New repository secret\n` +
                    `# Name: NOVA_API_KEY\n` +
                    `# Value: your-nova-api-key\n` +
                    `\`\`\`\n\n` +
                    `Once configured, I'll automatically fix failing tests on your PRs! 🚀`,
            });
          }
        } catch (err) {
          const message = err?.message || 'unknown error';
          checkSummary = `❌ Error: Failed to trigger Nova CI-Rescue: ${message}`;
          checkConclusion = 'failure';

          context.log.error('Failed to handle CI failure', {
            error: message,
            pr_number: pr?.number
          });
        }

        // Update check status
        await context.octokit.checks.create({
          owner,
          repo,
          name: 'Nova CI-Rescue',
          head_sha: headSha,
          status: 'completed',
          conclusion: checkConclusion,
          output: {
            title: checkConclusion === 'success' ? 'CI-Rescue Triggered' : 'CI-Rescue Status',
            summary: checkSummary,
          },
        });
      }
    }
  });

  // Helper function to create welcome issue
  async function createWelcomeIssue(context, owner, repo) {
    const issueBody = `# 🎉 Welcome to Nova CI-Rescue!\n\n` +
      `Thank you for installing Nova CI-Rescue! This GitHub App will automatically attempt to fix failing tests in your pull requests.\n\n` +
      `## 🚀 Quick Setup\n\n` +
      `To complete the setup, you need to add the Nova workflow to your repository:\n\n` +
      `### 1. Create the workflow file\n` +
      `Create \`.github/workflows/nova-ci-rescue.yml\` with the following content:\n\n` +
      `\`\`\`yaml\n` +
      `name: Nova CI-Rescue Auto-Fix\n` +
      `on:\n` +
      `  workflow_dispatch:\n` +
      `    inputs:\n` +
      `      pr_number:\n` +
      `        description: 'Pull request number to fix'\n` +
      `        required: true\n` +
      `        type: string\n\n` +
      `jobs:\n` +
      `  auto-fix:\n` +
      `    runs-on: ubuntu-latest\n` +
      `    steps:\n` +
      `      - uses: actions/checkout@v4\n` +
      `        with:\n` +
      `          token: \${{ secrets.GITHUB_TOKEN }}\n` +
      `          fetch-depth: 0\n\n` +
      `      - name: Run Nova CI-Rescue\n` +
      `        uses: nova-ci-rescue/action@v1\n` +
      `        with:\n` +
      `          pr_number: \${{ inputs.pr_number }}\n` +
      `          nova_api_key: \${{ secrets.NOVA_API_KEY }}\n` +
      `\`\`\`\n\n` +
      `### 2. Add your Nova API key\n` +
      `1. Go to **Settings** → **Secrets and variables** → **Actions**\n` +
      `2. Click **New repository secret**\n` +
      `3. Name: \`NOVA_API_KEY\`\n` +
      `4. Value: Your Nova API key (get one at [nova-ci.com](https://nova-ci.com))\n\n` +
      `## ✅ That's it!\n\n` +
      `Once configured, Nova CI-Rescue will:\n` +
      `- Monitor all pull requests for CI failures\n` +
      `- Automatically attempt to fix failing tests\n` +
      `- Push fixes directly to the PR branch\n` +
      `- Comment with the results\n\n` +
      `## 📚 Resources\n` +
      `- [Documentation](https://github.com/nova-ci-rescue/docs)\n` +
      `- [Example repositories](https://github.com/nova-ci-rescue/examples)\n` +
      `- [Support](https://github.com/nova-ci-rescue/support)\n\n` +
      `---\n` +
      `*This issue was created automatically by Nova CI-Rescue. Feel free to close it once you've completed the setup!*`;

    await context.octokit.issues.create({
      owner,
      repo,
      title: '🤖 Nova CI-Rescue Setup Instructions',
      body: issueBody,
      labels: ['nova-ci-rescue', 'setup']
    });
  }
};
      let githubError = null;
      let installFlowTest = 'unchecked';
      let installFlowError = null;
      let appDetails = null;

      try {
        // Check if we have the required credentials
        if (process.env.APP_ID && process.env.PRIVATE_KEY && process.env.WEBHOOK_SECRET) {
          // Step 1: Test basic app authentication
          try {
            const auth = await app.auth();
            // app.auth() returns an Octokit instance if successful
            githubAuth = 'authenticated';

            // Step 2: Test installation flow capabilities
            try {
              // Test 2a: Get app details
              const appInfo = await app.octokit.apps.getAuthenticated();
              appDetails = {
                name: appInfo.data.name,
                slug: appInfo.data.slug,
                permissions: appInfo.data.permissions,
                events: appInfo.data.events
              };

              // Test 2b: List installations (this tests the app's ability to see installations)
              const installations = await app.octokit.apps.listInstallations();
              installFlowTest = 'passed';

              // Test 2c: If there are installations, test installation authentication
              if (installations.data.length > 0) {
                const firstInstall = installations.data[0];
                const installAuth = await app.auth(firstInstall.id);
                if (installAuth) {
                  installFlowTest = 'installation_auth_passed';
                }
              }

            } catch (installError) {
              installFlowTest = 'partial';
              installFlowError = `Installation flow test failed: ${installError.message}`;
            }

          } catch (authError) {
            githubAuth = 'auth_failed';
            githubError = `Authentication failed: ${authError.message}`;
          }
        } else {
          githubAuth = 'missing_credentials';
          githubError = 'Missing APP_ID, PRIVATE_KEY, or WEBHOOK_SECRET';
        }
      } catch (error) {
        githubAuth = 'failed';
        githubError = error.message;
        installFlowTest = 'failed';
        installFlowError = error.message;
      }

      // Determine overall health status
      let overallStatus = 'healthy';
      let overallError = null;

      if (githubAuth !== 'authenticated') {
        overallStatus = 'unhealthy';
        overallError = githubError || 'GitHub authentication failed';
      } else if (installFlowTest === 'failed') {
        overallStatus = 'degraded';
        overallError = installFlowError || 'Installation flow test failed';
      } else if (installFlowTest === 'partial') {
        overallStatus = 'degraded';
        overallError = installFlowError || 'Installation flow partially working';
      }

      const healthStatus = {
        status: overallStatus,
        service: 'nova-ci-rescue',
        timestamp: new Date().toISOString(),
        version: process.env.APP_VERSION || '1.0.0',
        installations_count: installations.size,
        error: overallError,
        github: {
          auth_status: githubAuth,
          error: githubError,
          app_id: process.env.APP_ID ? 'configured' : 'missing',
          private_key: process.env.PRIVATE_KEY ? 'configured' : 'missing',
          webhook_secret: process.env.WEBHOOK_SECRET ? 'configured' : 'missing',
          install_flow_test: installFlowTest,
          install_flow_error: installFlowError,
          app_details: appDetails
        },
        memory: {
          used_mb: Math.round(memoryUsage.heapUsed / 1024 / 1024),
          total_mb: Math.round(memoryUsage.heapTotal / 1024 / 1024)
        },
        uptime_seconds: Math.floor(process.uptime())
      };

      // Return appropriate HTTP status
      const httpStatus = overallStatus === 'healthy' ? 200 :
                        overallStatus === 'degraded' ? 200 : 503;

      res.status(httpStatus).json(healthStatus);
    });

    // Root endpoint for basic checks
    router.get('/', (req, res) => {
      res.status(200).send(`
        <!DOCTYPE html>
        <html>
        <head>
          <title>Nova CI-Rescue</title>
          <style>
            body {
              font-family: -apple-system, system-ui, sans-serif;
              max-width: 600px;
              margin: 100px auto;
              padding: 20px;
              text-align: center;
            }
            h1 { font-size: 48px; margin: 0; }
            .logo { font-size: 72px; margin-bottom: 20px; }
            .links { margin-top: 30px; }
            a {
              color: #0366d6;
              text-decoration: none;
              margin: 0 10px;
            }
            a:hover { text-decoration: underline; }
            .status {
              background: #d1f5d3;
              padding: 10px 20px;
              border-radius: 6px;
              display: inline-block;
              margin-top: 20px;
            }
          </style>
        </head>
        <body>
          <div class="logo">🤖</div>
          <h1>Nova CI-Rescue</h1>
          <p>GitHub App is running! 🚀</p>
          <div class="status">✅ Healthy - ${installations.size} active installations</div>
          <div class="links">
            <a href="/setup">Setup Guide</a> •
            <a href="/health">Health Status</a> •
            <a href="https://github.com/marketplace/nova-ci-rescue">Marketplace</a>
          </div>
        </body>
        </html>
      `);
    });

    // Setup guide endpoint
    router.get('/setup', (req, res) => {
      const setupPath = path.join(__dirname, 'templates', 'setup.html');

      fs.readFile(setupPath, 'utf8', (err, data) => {
        if (err) {
          app.log.error('Failed to read setup guide', err);
          res.status(500).send('Setup guide not found');
          return;
        }
        res.status(200).send(data);
      });
    });

    // Detailed probe endpoint for monitoring
    router.get('/probe', async (req, res) => {
      try {
        // Check if we can authenticate with GitHub
        const authenticated = app.state?.id ? true : false;

        res.status(200).json({
          status: 'healthy',
          service: 'nova-ci-rescue',
          timestamp: new Date().toISOString(),
          version: process.env.APP_VERSION || '1.0.0',
          checks: {
            github_auth: authenticated ? 'connected' : 'pending',
            app_id: process.env.APP_ID ? 'configured' : 'missing',
            webhook_secret: process.env.WEBHOOK_SECRET ? 'configured' : 'missing'
          },
          stats: {
            active_installations: installations.size,
            uptime: process.uptime()
          }
        });
      } catch (error) {
        res.status(503).json({
          status: 'unhealthy',
          error: error.message
        });
      }
    });
  }

  // Handle new installations
  app.on('installation.created', async (context) => {
    const { installation, sender } = context.payload;
    const installationId = installation.id;
    const account = installation.account;

    // Track installation
    installations.set(installationId, {
      id: installationId,
      account: account.login,
      type: account.type,
      created_at: new Date().toISOString(),
      repositories: installation.repository_selection === 'all' ? 'all' : installation.repositories
    });

    // Persist to storage
    saveInstallations();

    context.log.info('New installation created', {
      installation_id: installationId,
      account: account.login,
      account_type: account.type,
      repository_selection: installation.repository_selection
    });

    // Create a welcome issue in each repository
    if (installation.repositories && installation.repository_selection === 'selected') {
      for (const repo of installation.repositories) {
        try {
          await createWelcomeIssue(context, account.login, repo.name);
        } catch (error) {
          context.log.error('Failed to create welcome issue', {
            repo: repo.name,
            error: error.message
          });
        }
      }
    }
  });

  // Handle installation deletions
  app.on('installation.deleted', async (context) => {
    const { installation } = context.payload;
    const installationId = installation.id;

    installations.delete(installationId);

    // Persist to storage
    saveInstallations();

    context.log.info('Installation deleted', {
      installation_id: installationId,
      account: installation.account.login
    });
  });

  // Handle repository additions to installation
  app.on('installation_repositories.added', async (context) => {
    const { installation, repositories_added, sender } = context.payload;

    context.log.info('Repositories added to installation', {
      installation_id: installation.id,
      account: installation.account.login,
      repos_added: repositories_added.map(r => r.name)
    });

    // Create welcome issues in newly added repositories
    for (const repo of repositories_added) {
      try {
        await createWelcomeIssue(context, installation.account.login, repo.name);
      } catch (error) {
        context.log.error('Failed to create welcome issue', {
          repo: repo.name,
          error: error.message
        });
      }
    }
  });

  // Handle repository removals from installation
  app.on('installation_repositories.removed', async (context) => {
    const { installation, repositories_removed } = context.payload;

    context.log.info('Repositories removed from installation', {
      installation_id: installation.id,
      account: installation.account.login,
      repos_removed: repositories_removed.map(r => r.name)
    });
  });

  // Main CI rescue logic
  app.on(['pull_request.opened', 'workflow_run.completed', 'check_suite.requested'], async (context) => {
    const { owner, repo } = context.repo();
    const installationId = context.payload.installation?.id;

    // Check rate limit
    if (installationId && !checkRateLimit(installationId)) {
      context.log.warn('Rate limit exceeded', {
        installation_id: installationId,
        owner,
        repo
      });
      return;
    }

    // Log event with installation context
    context.log.info(`Event: ${context.name}`, {
      installation_id: installationId,
      owner,
      repo,
      event_action: context.payload.action
    });

    const headSha =
      context.payload.pull_request?.head?.sha ||
      context.payload.workflow_run?.head_sha ||
      context.payload.check_suite?.head_sha;

    if (!headSha) {
      context.log.warn('No head SHA found for event', { event: context.name });
      return;
    }

    let checkSummary = 'Nova CI-Rescue is monitoring your CI. Waiting for results...';
    let checkConclusion = 'neutral';

    // Handle new PR opened
    if (context.name === 'pull_request' && context.payload.action === 'opened') {
      try {
        await context.octokit.checks.create({
          owner,
          repo,
          name: 'Nova CI-Rescue',
          head_sha: headSha,
          status: 'completed',
          conclusion: 'neutral',
          output: {
            title: 'CI-Rescue Ready',
            summary: '🤖 Nova CI-Rescue is monitoring this PR. If your CI fails, I\'ll attempt to fix it automatically!',
          },
        });
      } catch (error) {
        context.log.error('Failed to create initial check', { error: error.message });
      }
      return;
    }

    // Handle workflow run completion
    if (context.name === 'workflow_run' && context.payload.action === 'completed') {
      const workflowRun = context.payload.workflow_run;
      const failed = workflowRun?.conclusion === 'failure';
      const pr = workflowRun?.pull_requests?.[0];
      const headBranch = workflowRun?.head_branch || pr?.head?.ref;

      if (failed && pr) {
        context.log.info('CI failure detected on PR', {
          pr_number: pr.number,
          workflow_name: workflowRun.name,
          branch: headBranch
        });

        try {
          // Check if Nova workflow exists
          const { data } = await context.octokit.actions.listRepoWorkflows({ owner, repo });
          const novaWf = data.workflows.find(
            (wf) => wf?.name === 'Nova CI-Rescue Auto-Fix' ||
                    (wf?.path || '').endsWith('/nova-ci-rescue.yml') ||
                    (wf?.path || '').endsWith('/nova-ci-rescue.yaml')
          );

          if (novaWf) {
            // Trigger Nova workflow
            await context.octokit.actions.createWorkflowDispatch({
              owner,
              repo,
              workflow_id: novaWf.id,
              ref: headBranch || 'main',
              inputs: {
                pr_number: String(pr.number),
                triggered_by: 'github-app'
              },
            });

            const actionsLink = `https://github.com/${owner}/${repo}/actions/workflows/${encodeURIComponent(
              novaWf.path.split('/').pop() || 'nova-ci-rescue.yml'
            )}`;

            checkSummary = `🔧 CI failed on PR #${pr.number}. I've triggered Nova CI-Rescue to attempt automatic fixes!\n\n` +
                          `**Branch:** \`${headBranch}\`\n` +
                          `**Failed Workflow:** ${workflowRun.name}\n` +
                          `**Nova Progress:** [View in Actions](${actionsLink})\n\n` +
                          `I'll analyze the failures and try to fix them automatically. This may take a few minutes.`;

            checkConclusion = 'success';

            // Leave a comment on the PR
            await context.octokit.issues.createComment({
              owner,
              repo,
              issue_number: pr.number,
              body: `## 🤖 Nova CI-Rescue Activated!\n\n` +
                    `I detected that your CI failed and I'm now attempting to fix it automatically.\n\n` +
                    `**What I'm doing:**\n` +
                    `- 🔍 Analyzing the test failures\n` +
                    `- 🛠️ Generating fixes for the failing tests\n` +
                    `- 📝 Creating a commit with the fixes\n\n` +
                    `**Track progress:** [View in GitHub Actions](${actionsLink})\n\n` +
                    `If I can fix the issues, I'll push a commit to your branch. Otherwise, I'll provide details about what went wrong.`,
            });

            context.log.info('Nova workflow triggered successfully', {
              pr_number: pr.number,
              workflow_id: novaWf.id
            });
          } else {
            checkSummary = `⚠️ CI failed on PR #${pr.number}, but Nova CI-Rescue workflow not found.\n\n` +
                          `**To enable automatic fixes:**\n` +
                          `1. Add \`.github/workflows/nova-ci-rescue.yml\` to your repository\n` +
                          `2. Configure the workflow with your Nova API key\n` +
                          `3. Push the changes\n\n` +
                          `[Learn more about Nova CI-Rescue](https://github.com/nova-ci-rescue/docs)`;

            checkConclusion = 'neutral';

            // Provide setup instructions
            await context.octokit.issues.createComment({
              owner,
              repo,
              issue_number: pr.number,
              body: `## ⚠️ CI Failed - Nova CI-Rescue Not Configured\n\n` +
                    `I noticed your CI failed, but I can't help yet because the Nova workflow isn't set up.\n\n` +
                    `**Quick Setup:**\n` +
                    `\`\`\`bash\n` +
                    `# Add Nova workflow to your repo\n` +
                    `curl -L https://raw.githubusercontent.com/nova-ci-rescue/templates/main/nova-ci-rescue.yml > .github/workflows/nova-ci-rescue.yml\n` +
                    `\n` +
                    `# Set your Nova API key as a repository secret\n` +
                    `# Go to Settings > Secrets > Actions > New repository secret\n` +
                    `# Name: NOVA_API_KEY\n` +
                    `# Value: your-nova-api-key\n` +
                    `\`\`\`\n\n` +
                    `Once configured, I'll automatically fix failing tests on your PRs! 🚀`,
            });
          }
        } catch (err) {
          const message = err?.message || 'unknown error';
          checkSummary = `❌ Error: Failed to trigger Nova CI-Rescue: ${message}`;
          checkConclusion = 'failure';

          context.log.error('Failed to handle CI failure', {
            error: message,
            pr_number: pr?.number
          });
        }

        // Update check status
        await context.octokit.checks.create({
          owner,
          repo,
          name: 'Nova CI-Rescue',
          head_sha: headSha,
          status: 'completed',
          conclusion: checkConclusion,
          output: {
            title: checkConclusion === 'success' ? 'CI-Rescue Triggered' : 'CI-Rescue Status',
            summary: checkSummary,
          },
        });
      }
    }
  });

  // Helper function to create welcome issue
  async function createWelcomeIssue(context, owner, repo) {
    const issueBody = `# 🎉 Welcome to Nova CI-Rescue!\n\n` +
      `Thank you for installing Nova CI-Rescue! This GitHub App will automatically attempt to fix failing tests in your pull requests.\n\n` +
      `## 🚀 Quick Setup\n\n` +
      `To complete the setup, you need to add the Nova workflow to your repository:\n\n` +
      `### 1. Create the workflow file\n` +
      `Create \`.github/workflows/nova-ci-rescue.yml\` with the following content:\n\n` +
      `\`\`\`yaml\n` +
      `name: Nova CI-Rescue Auto-Fix\n` +
      `on:\n` +
      `  workflow_dispatch:\n` +
      `    inputs:\n` +
      `      pr_number:\n` +
      `        description: 'Pull request number to fix'\n` +
      `        required: true\n` +
      `        type: string\n\n` +
      `jobs:\n` +
      `  auto-fix:\n` +
      `    runs-on: ubuntu-latest\n` +
      `    steps:\n` +
      `      - uses: actions/checkout@v4\n` +
      `        with:\n` +
      `          token: \${{ secrets.GITHUB_TOKEN }}\n` +
      `          fetch-depth: 0\n\n` +
      `      - name: Run Nova CI-Rescue\n` +
      `        uses: nova-ci-rescue/action@v1\n` +
      `        with:\n` +
      `          pr_number: \${{ inputs.pr_number }}\n` +
      `          nova_api_key: \${{ secrets.NOVA_API_KEY }}\n` +
      `\`\`\`\n\n` +
      `### 2. Add your Nova API key\n` +
      `1. Go to **Settings** → **Secrets and variables** → **Actions**\n` +
      `2. Click **New repository secret**\n` +
      `3. Name: \`NOVA_API_KEY\`\n` +
      `4. Value: Your Nova API key (get one at [nova-ci.com](https://nova-ci.com))\n\n` +
      `## ✅ That's it!\n\n` +
      `Once configured, Nova CI-Rescue will:\n` +
      `- Monitor all pull requests for CI failures\n` +
      `- Automatically attempt to fix failing tests\n` +
      `- Push fixes directly to the PR branch\n` +
      `- Comment with the results\n\n` +
      `## 📚 Resources\n` +
      `- [Documentation](https://github.com/nova-ci-rescue/docs)\n` +
      `- [Example repositories](https://github.com/nova-ci-rescue/examples)\n` +
      `- [Support](https://github.com/nova-ci-rescue/support)\n\n` +
      `---\n` +
      `*This issue was created automatically by Nova CI-Rescue. Feel free to close it once you've completed the setup!*`;

    await context.octokit.issues.create({
      owner,
      repo,
      title: '🤖 Nova CI-Rescue Setup Instructions',
      body: issueBody,
      labels: ['nova-ci-rescue', 'setup']
    });
  }
};
      let githubError = null;
      let installFlowTest = 'unchecked';
      let installFlowError = null;
      let appDetails = null;

      try {
        // Check if we have the required credentials
        if (process.env.APP_ID && process.env.PRIVATE_KEY && process.env.WEBHOOK_SECRET) {
          // Step 1: Test basic app authentication
          try {
            const auth = await app.auth();
            // app.auth() returns an Octokit instance if successful
            githubAuth = 'authenticated';

            // Step 2: Test installation flow capabilities
            try {
              // Test 2a: Get app details
              const appInfo = await app.octokit.apps.getAuthenticated();
              appDetails = {
                name: appInfo.data.name,
                slug: appInfo.data.slug,
                permissions: appInfo.data.permissions,
                events: appInfo.data.events
              };

              // Test 2b: List installations (this tests the app's ability to see installations)
              const installations = await app.octokit.apps.listInstallations();
              installFlowTest = 'passed';

              // Test 2c: If there are installations, test installation authentication
              if (installations.data.length > 0) {
                const firstInstall = installations.data[0];
                const installAuth = await app.auth(firstInstall.id);
                if (installAuth) {
                  installFlowTest = 'installation_auth_passed';
                }
              }

            } catch (installError) {
              installFlowTest = 'partial';
              installFlowError = `Installation flow test failed: ${installError.message}`;
            }

          } catch (authError) {
            githubAuth = 'auth_failed';
            githubError = `Authentication failed: ${authError.message}`;
          }
        } else {
          githubAuth = 'missing_credentials';
          githubError = 'Missing APP_ID, PRIVATE_KEY, or WEBHOOK_SECRET';
        }
      } catch (error) {
        githubAuth = 'failed';
        githubError = error.message;
        installFlowTest = 'failed';
        installFlowError = error.message;
      }

      // Determine overall health status
      let overallStatus = 'healthy';
      let overallError = null;

      if (githubAuth !== 'authenticated') {
        overallStatus = 'unhealthy';
        overallError = githubError || 'GitHub authentication failed';
      } else if (installFlowTest === 'failed') {
        overallStatus = 'degraded';
        overallError = installFlowError || 'Installation flow test failed';
      } else if (installFlowTest === 'partial') {
        overallStatus = 'degraded';
        overallError = installFlowError || 'Installation flow partially working';
      }

      const healthStatus = {
        status: overallStatus,
        service: 'nova-ci-rescue',
        timestamp: new Date().toISOString(),
        version: process.env.APP_VERSION || '1.0.0',
        installations_count: installations.size,
        error: overallError,
        github: {
          auth_status: githubAuth,
          error: githubError,
          app_id: process.env.APP_ID ? 'configured' : 'missing',
          private_key: process.env.PRIVATE_KEY ? 'configured' : 'missing',
          webhook_secret: process.env.WEBHOOK_SECRET ? 'configured' : 'missing',
          install_flow_test: installFlowTest,
          install_flow_error: installFlowError,
          app_details: appDetails
        },
        memory: {
          used_mb: Math.round(memoryUsage.heapUsed / 1024 / 1024),
          total_mb: Math.round(memoryUsage.heapTotal / 1024 / 1024)
        },
        uptime_seconds: Math.floor(process.uptime())
      };

      // Return appropriate HTTP status
      const httpStatus = overallStatus === 'healthy' ? 200 :
                        overallStatus === 'degraded' ? 200 : 503;

      res.status(httpStatus).json(healthStatus);
    });

    // Root endpoint for basic checks
    router.get('/', (req, res) => {
      res.status(200).send(`
        <!DOCTYPE html>
        <html>
        <head>
          <title>Nova CI-Rescue</title>
          <style>
            body {
              font-family: -apple-system, system-ui, sans-serif;
              max-width: 600px;
              margin: 100px auto;
              padding: 20px;
              text-align: center;
            }
            h1 { font-size: 48px; margin: 0; }
            .logo { font-size: 72px; margin-bottom: 20px; }
            .links { margin-top: 30px; }
            a {
              color: #0366d6;
              text-decoration: none;
              margin: 0 10px;
            }
            a:hover { text-decoration: underline; }
            .status {
              background: #d1f5d3;
              padding: 10px 20px;
              border-radius: 6px;
              display: inline-block;
              margin-top: 20px;
            }
          </style>
        </head>
        <body>
          <div class="logo">🤖</div>
          <h1>Nova CI-Rescue</h1>
          <p>GitHub App is running! 🚀</p>
          <div class="status">✅ Healthy - ${installations.size} active installations</div>
          <div class="links">
            <a href="/setup">Setup Guide</a> •
            <a href="/health">Health Status</a> •
            <a href="https://github.com/marketplace/nova-ci-rescue">Marketplace</a>
          </div>
        </body>
        </html>
      `);
    });

    // Setup guide endpoint
    router.get('/setup', (req, res) => {
      const setupPath = path.join(__dirname, 'templates', 'setup.html');

      fs.readFile(setupPath, 'utf8', (err, data) => {
        if (err) {
          app.log.error('Failed to read setup guide', err);
          res.status(500).send('Setup guide not found');
          return;
        }
        res.status(200).send(data);
      });
    });

    // Detailed probe endpoint for monitoring
    router.get('/probe', async (req, res) => {
      try {
        // Check if we can authenticate with GitHub
        const authenticated = app.state?.id ? true : false;

        res.status(200).json({
          status: 'healthy',
          service: 'nova-ci-rescue',
          timestamp: new Date().toISOString(),
          version: process.env.APP_VERSION || '1.0.0',
          checks: {
            github_auth: authenticated ? 'connected' : 'pending',
            app_id: process.env.APP_ID ? 'configured' : 'missing',
            webhook_secret: process.env.WEBHOOK_SECRET ? 'configured' : 'missing'
          },
          stats: {
            active_installations: installations.size,
            uptime: process.uptime()
          }
        });
      } catch (error) {
        res.status(503).json({
          status: 'unhealthy',
          error: error.message
        });
      }
    });
  }

  // Handle new installations
  app.on('installation.created', async (context) => {
    const { installation, sender } = context.payload;
    const installationId = installation.id;
    const account = installation.account;

    // Track installation
    installations.set(installationId, {
      id: installationId,
      account: account.login,
      type: account.type,
      created_at: new Date().toISOString(),
      repositories: installation.repository_selection === 'all' ? 'all' : installation.repositories
    });

    // Persist to storage
    saveInstallations();

    context.log.info('New installation created', {
      installation_id: installationId,
      account: account.login,
      account_type: account.type,
      repository_selection: installation.repository_selection
    });

    // Create a welcome issue in each repository
    if (installation.repositories && installation.repository_selection === 'selected') {
      for (const repo of installation.repositories) {
        try {
          await createWelcomeIssue(context, account.login, repo.name);
        } catch (error) {
          context.log.error('Failed to create welcome issue', {
            repo: repo.name,
            error: error.message
          });
        }
      }
    }
  });

  // Handle installation deletions
  app.on('installation.deleted', async (context) => {
    const { installation } = context.payload;
    const installationId = installation.id;

    installations.delete(installationId);

    // Persist to storage
    saveInstallations();

    context.log.info('Installation deleted', {
      installation_id: installationId,
      account: installation.account.login
    });
  });

  // Handle repository additions to installation
  app.on('installation_repositories.added', async (context) => {
    const { installation, repositories_added, sender } = context.payload;

    context.log.info('Repositories added to installation', {
      installation_id: installation.id,
      account: installation.account.login,
      repos_added: repositories_added.map(r => r.name)
    });

    // Create welcome issues in newly added repositories
    for (const repo of repositories_added) {
      try {
        await createWelcomeIssue(context, installation.account.login, repo.name);
      } catch (error) {
        context.log.error('Failed to create welcome issue', {
          repo: repo.name,
          error: error.message
        });
      }
    }
  });

  // Handle repository removals from installation
  app.on('installation_repositories.removed', async (context) => {
    const { installation, repositories_removed } = context.payload;

    context.log.info('Repositories removed from installation', {
      installation_id: installation.id,
      account: installation.account.login,
      repos_removed: repositories_removed.map(r => r.name)
    });
  });

  // Main CI rescue logic
  app.on(['pull_request.opened', 'workflow_run.completed', 'check_suite.requested'], async (context) => {
    const { owner, repo } = context.repo();
    const installationId = context.payload.installation?.id;

    // Check rate limit
    if (installationId && !checkRateLimit(installationId)) {
      context.log.warn('Rate limit exceeded', {
        installation_id: installationId,
        owner,
        repo
      });
      return;
    }

    // Log event with installation context
    context.log.info(`Event: ${context.name}`, {
      installation_id: installationId,
      owner,
      repo,
      event_action: context.payload.action
    });

    const headSha =
      context.payload.pull_request?.head?.sha ||
      context.payload.workflow_run?.head_sha ||
      context.payload.check_suite?.head_sha;

    if (!headSha) {
      context.log.warn('No head SHA found for event', { event: context.name });
      return;
    }

    let checkSummary = 'Nova CI-Rescue is monitoring your CI. Waiting for results...';
    let checkConclusion = 'neutral';

    // Handle new PR opened
    if (context.name === 'pull_request' && context.payload.action === 'opened') {
      try {
        await context.octokit.checks.create({
          owner,
          repo,
          name: 'Nova CI-Rescue',
          head_sha: headSha,
          status: 'completed',
          conclusion: 'neutral',
          output: {
            title: 'CI-Rescue Ready',
            summary: '🤖 Nova CI-Rescue is monitoring this PR. If your CI fails, I\'ll attempt to fix it automatically!',
          },
        });
      } catch (error) {
        context.log.error('Failed to create initial check', { error: error.message });
      }
      return;
    }

    // Handle workflow run completion
    if (context.name === 'workflow_run' && context.payload.action === 'completed') {
      const workflowRun = context.payload.workflow_run;
      const failed = workflowRun?.conclusion === 'failure';
      const pr = workflowRun?.pull_requests?.[0];
      const headBranch = workflowRun?.head_branch || pr?.head?.ref;

      if (failed && pr) {
        context.log.info('CI failure detected on PR', {
          pr_number: pr.number,
          workflow_name: workflowRun.name,
          branch: headBranch
        });

        try {
          // Check if Nova workflow exists
          const { data } = await context.octokit.actions.listRepoWorkflows({ owner, repo });
          const novaWf = data.workflows.find(
            (wf) => wf?.name === 'Nova CI-Rescue Auto-Fix' ||
                    (wf?.path || '').endsWith('/nova-ci-rescue.yml') ||
                    (wf?.path || '').endsWith('/nova-ci-rescue.yaml')
          );

          if (novaWf) {
            // Trigger Nova workflow
            await context.octokit.actions.createWorkflowDispatch({
              owner,
              repo,
              workflow_id: novaWf.id,
              ref: headBranch || 'main',
              inputs: {
                pr_number: String(pr.number),
                triggered_by: 'github-app'
              },
            });

            const actionsLink = `https://github.com/${owner}/${repo}/actions/workflows/${encodeURIComponent(
              novaWf.path.split('/').pop() || 'nova-ci-rescue.yml'
            )}`;

            checkSummary = `🔧 CI failed on PR #${pr.number}. I've triggered Nova CI-Rescue to attempt automatic fixes!\n\n` +
                          `**Branch:** \`${headBranch}\`\n` +
                          `**Failed Workflow:** ${workflowRun.name}\n` +
                          `**Nova Progress:** [View in Actions](${actionsLink})\n\n` +
                          `I'll analyze the failures and try to fix them automatically. This may take a few minutes.`;

            checkConclusion = 'success';

            // Leave a comment on the PR
            await context.octokit.issues.createComment({
              owner,
              repo,
              issue_number: pr.number,
              body: `## 🤖 Nova CI-Rescue Activated!\n\n` +
                    `I detected that your CI failed and I'm now attempting to fix it automatically.\n\n` +
                    `**What I'm doing:**\n` +
                    `- 🔍 Analyzing the test failures\n` +
                    `- 🛠️ Generating fixes for the failing tests\n` +
                    `- 📝 Creating a commit with the fixes\n\n` +
                    `**Track progress:** [View in GitHub Actions](${actionsLink})\n\n` +
                    `If I can fix the issues, I'll push a commit to your branch. Otherwise, I'll provide details about what went wrong.`,
            });

            context.log.info('Nova workflow triggered successfully', {
              pr_number: pr.number,
              workflow_id: novaWf.id
            });
          } else {
            checkSummary = `⚠️ CI failed on PR #${pr.number}, but Nova CI-Rescue workflow not found.\n\n` +
                          `**To enable automatic fixes:**\n` +
                          `1. Add \`.github/workflows/nova-ci-rescue.yml\` to your repository\n` +
                          `2. Configure the workflow with your Nova API key\n` +
                          `3. Push the changes\n\n` +
                          `[Learn more about Nova CI-Rescue](https://github.com/nova-ci-rescue/docs)`;

            checkConclusion = 'neutral';

            // Provide setup instructions
            await context.octokit.issues.createComment({
              owner,
              repo,
              issue_number: pr.number,
              body: `## ⚠️ CI Failed - Nova CI-Rescue Not Configured\n\n` +
                    `I noticed your CI failed, but I can't help yet because the Nova workflow isn't set up.\n\n` +
                    `**Quick Setup:**\n` +
                    `\`\`\`bash\n` +
                    `# Add Nova workflow to your repo\n` +
                    `curl -L https://raw.githubusercontent.com/nova-ci-rescue/templates/main/nova-ci-rescue.yml > .github/workflows/nova-ci-rescue.yml\n` +
                    `\n` +
                    `# Set your Nova API key as a repository secret\n` +
                    `# Go to Settings > Secrets > Actions > New repository secret\n` +
                    `# Name: NOVA_API_KEY\n` +
                    `# Value: your-nova-api-key\n` +
                    `\`\`\`\n\n` +
                    `Once configured, I'll automatically fix failing tests on your PRs! 🚀`,
            });
          }
        } catch (err) {
          const message = err?.message || 'unknown error';
          checkSummary = `❌ Error: Failed to trigger Nova CI-Rescue: ${message}`;
          checkConclusion = 'failure';

          context.log.error('Failed to handle CI failure', {
            error: message,
            pr_number: pr?.number
          });
        }

        // Update check status
        await context.octokit.checks.create({
          owner,
          repo,
          name: 'Nova CI-Rescue',
          head_sha: headSha,
          status: 'completed',
          conclusion: checkConclusion,
          output: {
            title: checkConclusion === 'success' ? 'CI-Rescue Triggered' : 'CI-Rescue Status',
            summary: checkSummary,
          },
        });
      }
    }
  });

  // Helper function to create welcome issue
  async function createWelcomeIssue(context, owner, repo) {
    const issueBody = `# 🎉 Welcome to Nova CI-Rescue!\n\n` +
      `Thank you for installing Nova CI-Rescue! This GitHub App will automatically attempt to fix failing tests in your pull requests.\n\n` +
      `## 🚀 Quick Setup\n\n` +
      `To complete the setup, you need to add the Nova workflow to your repository:\n\n` +
      `### 1. Create the workflow file\n` +
      `Create \`.github/workflows/nova-ci-rescue.yml\` with the following content:\n\n` +
      `\`\`\`yaml\n` +
      `name: Nova CI-Rescue Auto-Fix\n` +
      `on:\n` +
      `  workflow_dispatch:\n` +
      `    inputs:\n` +
      `      pr_number:\n` +
      `        description: 'Pull request number to fix'\n` +
      `        required: true\n` +
      `        type: string\n\n` +
      `jobs:\n` +
      `  auto-fix:\n` +
      `    runs-on: ubuntu-latest\n` +
      `    steps:\n` +
      `      - uses: actions/checkout@v4\n` +
      `        with:\n` +
      `          token: \${{ secrets.GITHUB_TOKEN }}\n` +
      `          fetch-depth: 0\n\n` +
      `      - name: Run Nova CI-Rescue\n` +
      `        uses: nova-ci-rescue/action@v1\n` +
      `        with:\n` +
      `          pr_number: \${{ inputs.pr_number }}\n` +
      `          nova_api_key: \${{ secrets.NOVA_API_KEY }}\n` +
      `\`\`\`\n\n` +
      `### 2. Add your Nova API key\n` +
      `1. Go to **Settings** → **Secrets and variables** → **Actions**\n` +
      `2. Click **New repository secret**\n` +
      `3. Name: \`NOVA_API_KEY\`\n` +
      `4. Value: Your Nova API key (get one at [nova-ci.com](https://nova-ci.com))\n\n` +
      `## ✅ That's it!\n\n` +
      `Once configured, Nova CI-Rescue will:\n` +
      `- Monitor all pull requests for CI failures\n` +
      `- Automatically attempt to fix failing tests\n` +
      `- Push fixes directly to the PR branch\n` +
      `- Comment with the results\n\n` +
      `## 📚 Resources\n` +
      `- [Documentation](https://github.com/nova-ci-rescue/docs)\n` +
      `- [Example repositories](https://github.com/nova-ci-rescue/examples)\n` +
      `- [Support](https://github.com/nova-ci-rescue/support)\n\n` +
      `---\n` +
      `*This issue was created automatically by Nova CI-Rescue. Feel free to close it once you've completed the setup!*`;

    await context.octokit.issues.create({
      owner,
      repo,
      title: '🤖 Nova CI-Rescue Setup Instructions',
      body: issueBody,
      labels: ['nova-ci-rescue', 'setup']
    });
  }
};
      let githubError = null;
      let installFlowTest = 'unchecked';
      let installFlowError = null;
      let appDetails = null;

      try {
        // Check if we have the required credentials
        if (process.env.APP_ID && process.env.PRIVATE_KEY && process.env.WEBHOOK_SECRET) {
          // Step 1: Test basic app authentication
          try {
            const auth = await app.auth();
            // app.auth() returns an Octokit instance if successful
            githubAuth = 'authenticated';

            // Step 2: Test installation flow capabilities
            try {
              // Test 2a: Get app details
              const appInfo = await app.octokit.apps.getAuthenticated();
              appDetails = {
                name: appInfo.data.name,
                slug: appInfo.data.slug,
                permissions: appInfo.data.permissions,
                events: appInfo.data.events
              };

              // Test 2b: List installations (this tests the app's ability to see installations)
              const installations = await app.octokit.apps.listInstallations();
              installFlowTest = 'passed';

              // Test 2c: If there are installations, test installation authentication
              if (installations.data.length > 0) {
                const firstInstall = installations.data[0];
                const installAuth = await app.auth(firstInstall.id);
                if (installAuth) {
                  installFlowTest = 'installation_auth_passed';
                }
              }

            } catch (installError) {
              installFlowTest = 'partial';
              installFlowError = `Installation flow test failed: ${installError.message}`;
            }

          } catch (authError) {
            githubAuth = 'auth_failed';
            githubError = `Authentication failed: ${authError.message}`;
          }
        } else {
          githubAuth = 'missing_credentials';
          githubError = 'Missing APP_ID, PRIVATE_KEY, or WEBHOOK_SECRET';
        }
      } catch (error) {
        githubAuth = 'failed';
        githubError = error.message;
        installFlowTest = 'failed';
        installFlowError = error.message;
      }

      // Determine overall health status
      let overallStatus = 'healthy';
      let overallError = null;

      if (githubAuth !== 'authenticated') {
        overallStatus = 'unhealthy';
        overallError = githubError || 'GitHub authentication failed';
      } else if (installFlowTest === 'failed') {
        overallStatus = 'degraded';
        overallError = installFlowError || 'Installation flow test failed';
      } else if (installFlowTest === 'partial') {
        overallStatus = 'degraded';
        overallError = installFlowError || 'Installation flow partially working';
      }

      const healthStatus = {
        status: overallStatus,
        service: 'nova-ci-rescue',
        timestamp: new Date().toISOString(),
        version: process.env.APP_VERSION || '1.0.0',
        installations_count: installations.size,
        error: overallError,
        github: {
          auth_status: githubAuth,
          error: githubError,
          app_id: process.env.APP_ID ? 'configured' : 'missing',
          private_key: process.env.PRIVATE_KEY ? 'configured' : 'missing',
          webhook_secret: process.env.WEBHOOK_SECRET ? 'configured' : 'missing',
          install_flow_test: installFlowTest,
          install_flow_error: installFlowError,
          app_details: appDetails
        },
        memory: {
          used_mb: Math.round(memoryUsage.heapUsed / 1024 / 1024),
          total_mb: Math.round(memoryUsage.heapTotal / 1024 / 1024)
        },
        uptime_seconds: Math.floor(process.uptime())
      };

      // Return appropriate HTTP status
      const httpStatus = overallStatus === 'healthy' ? 200 :
                        overallStatus === 'degraded' ? 200 : 503;

      res.status(httpStatus).json(healthStatus);
    });

    // Root endpoint for basic checks
    router.get('/', (req, res) => {
      res.status(200).send(`
        <!DOCTYPE html>
        <html>
        <head>
          <title>Nova CI-Rescue</title>
          <style>
            body {
              font-family: -apple-system, system-ui, sans-serif;
              max-width: 600px;
              margin: 100px auto;
              padding: 20px;
              text-align: center;
            }
            h1 { font-size: 48px; margin: 0; }
            .logo { font-size: 72px; margin-bottom: 20px; }
            .links { margin-top: 30px; }
            a {
              color: #0366d6;
              text-decoration: none;
              margin: 0 10px;
            }
            a:hover { text-decoration: underline; }
            .status {
              background: #d1f5d3;
              padding: 10px 20px;
              border-radius: 6px;
              display: inline-block;
              margin-top: 20px;
            }
          </style>
        </head>
        <body>
          <div class="logo">🤖</div>
          <h1>Nova CI-Rescue</h1>
          <p>GitHub App is running! 🚀</p>
          <div class="status">✅ Healthy - ${installations.size} active installations</div>
          <div class="links">
            <a href="/setup">Setup Guide</a> •
            <a href="/health">Health Status</a> •
            <a href="https://github.com/marketplace/nova-ci-rescue">Marketplace</a>
          </div>
        </body>
        </html>
      `);
    });

    // Setup guide endpoint
    router.get('/setup', (req, res) => {
      const setupPath = path.join(__dirname, 'templates', 'setup.html');

      fs.readFile(setupPath, 'utf8', (err, data) => {
        if (err) {
          app.log.error('Failed to read setup guide', err);
          res.status(500).send('Setup guide not found');
          return;
        }
        res.status(200).send(data);
      });
    });

    // Detailed probe endpoint for monitoring
    router.get('/probe', async (req, res) => {
      try {
        // Check if we can authenticate with GitHub
        const authenticated = app.state?.id ? true : false;

        res.status(200).json({
          status: 'healthy',
          service: 'nova-ci-rescue',
          timestamp: new Date().toISOString(),
          version: process.env.APP_VERSION || '1.0.0',
          checks: {
            github_auth: authenticated ? 'connected' : 'pending',
            app_id: process.env.APP_ID ? 'configured' : 'missing',
            webhook_secret: process.env.WEBHOOK_SECRET ? 'configured' : 'missing'
          },
          stats: {
            active_installations: installations.size,
            uptime: process.uptime()
          }
        });
      } catch (error) {
        res.status(503).json({
          status: 'unhealthy',
          error: error.message
        });
      }
    });
  }

  // Handle new installations
  app.on('installation.created', async (context) => {
    const { installation, sender } = context.payload;
    const installationId = installation.id;
    const account = installation.account;

    // Track installation
    installations.set(installationId, {
      id: installationId,
      account: account.login,
      type: account.type,
      created_at: new Date().toISOString(),
      repositories: installation.repository_selection === 'all' ? 'all' : installation.repositories
    });

    // Persist to storage
    saveInstallations();

    context.log.info('New installation created', {
      installation_id: installationId,
      account: account.login,
      account_type: account.type,
      repository_selection: installation.repository_selection
    });

    // Create a welcome issue in each repository
    if (installation.repositories && installation.repository_selection === 'selected') {
      for (const repo of installation.repositories) {
        try {
          await createWelcomeIssue(context, account.login, repo.name);
        } catch (error) {
          context.log.error('Failed to create welcome issue', {
            repo: repo.name,
            error: error.message
          });
        }
      }
    }
  });

  // Handle installation deletions
  app.on('installation.deleted', async (context) => {
    const { installation } = context.payload;
    const installationId = installation.id;

    installations.delete(installationId);

    // Persist to storage
    saveInstallations();

    context.log.info('Installation deleted', {
      installation_id: installationId,
      account: installation.account.login
    });
  });

  // Handle repository additions to installation
  app.on('installation_repositories.added', async (context) => {
    const { installation, repositories_added, sender } = context.payload;

    context.log.info('Repositories added to installation', {
      installation_id: installation.id,
      account: installation.account.login,
      repos_added: repositories_added.map(r => r.name)
    });

    // Create welcome issues in newly added repositories
    for (const repo of repositories_added) {
      try {
        await createWelcomeIssue(context, installation.account.login, repo.name);
      } catch (error) {
        context.log.error('Failed to create welcome issue', {
          repo: repo.name,
          error: error.message
        });
      }
    }
  });

  // Handle repository removals from installation
  app.on('installation_repositories.removed', async (context) => {
    const { installation, repositories_removed } = context.payload;

    context.log.info('Repositories removed from installation', {
      installation_id: installation.id,
      account: installation.account.login,
      repos_removed: repositories_removed.map(r => r.name)
    });
  });

  // Main CI rescue logic
  app.on(['pull_request.opened', 'workflow_run.completed', 'check_suite.requested'], async (context) => {
    const { owner, repo } = context.repo();
    const installationId = context.payload.installation?.id;

    // Check rate limit
    if (installationId && !checkRateLimit(installationId)) {
      context.log.warn('Rate limit exceeded', {
        installation_id: installationId,
        owner,
        repo
      });
      return;
    }

    // Log event with installation context
    context.log.info(`Event: ${context.name}`, {
      installation_id: installationId,
      owner,
      repo,
      event_action: context.payload.action
    });

    const headSha =
      context.payload.pull_request?.head?.sha ||
      context.payload.workflow_run?.head_sha ||
      context.payload.check_suite?.head_sha;

    if (!headSha) {
      context.log.warn('No head SHA found for event', { event: context.name });
      return;
    }

    let checkSummary = 'Nova CI-Rescue is monitoring your CI. Waiting for results...';
    let checkConclusion = 'neutral';

    // Handle new PR opened
    if (context.name === 'pull_request' && context.payload.action === 'opened') {
      try {
        await context.octokit.checks.create({
          owner,
          repo,
          name: 'Nova CI-Rescue',
          head_sha: headSha,
          status: 'completed',
          conclusion: 'neutral',
          output: {
            title: 'CI-Rescue Ready',
            summary: '🤖 Nova CI-Rescue is monitoring this PR. If your CI fails, I\'ll attempt to fix it automatically!',
          },
        });
      } catch (error) {
        context.log.error('Failed to create initial check', { error: error.message });
      }
      return;
    }

    // Handle workflow run completion
    if (context.name === 'workflow_run' && context.payload.action === 'completed') {
      const workflowRun = context.payload.workflow_run;
      const failed = workflowRun?.conclusion === 'failure';
      const pr = workflowRun?.pull_requests?.[0];
      const headBranch = workflowRun?.head_branch || pr?.head?.ref;

      if (failed && pr) {
        context.log.info('CI failure detected on PR', {
          pr_number: pr.number,
          workflow_name: workflowRun.name,
          branch: headBranch
        });

        try {
          // Check if Nova workflow exists
          const { data } = await context.octokit.actions.listRepoWorkflows({ owner, repo });
          const novaWf = data.workflows.find(
            (wf) => wf?.name === 'Nova CI-Rescue Auto-Fix' ||
                    (wf?.path || '').endsWith('/nova-ci-rescue.yml') ||
                    (wf?.path || '').endsWith('/nova-ci-rescue.yaml')
          );

          if (novaWf) {
            // Trigger Nova workflow
            await context.octokit.actions.createWorkflowDispatch({
              owner,
              repo,
              workflow_id: novaWf.id,
              ref: headBranch || 'main',
              inputs: {
                pr_number: String(pr.number),
                triggered_by: 'github-app'
              },
            });

            const actionsLink = `https://github.com/${owner}/${repo}/actions/workflows/${encodeURIComponent(
              novaWf.path.split('/').pop() || 'nova-ci-rescue.yml'
            )}`;

            checkSummary = `🔧 CI failed on PR #${pr.number}. I've triggered Nova CI-Rescue to attempt automatic fixes!\n\n` +
                          `**Branch:** \`${headBranch}\`\n` +
                          `**Failed Workflow:** ${workflowRun.name}\n` +
                          `**Nova Progress:** [View in Actions](${actionsLink})\n\n` +
                          `I'll analyze the failures and try to fix them automatically. This may take a few minutes.`;

            checkConclusion = 'success';

            // Leave a comment on the PR
            await context.octokit.issues.createComment({
              owner,
              repo,
              issue_number: pr.number,
              body: `## 🤖 Nova CI-Rescue Activated!\n\n` +
                    `I detected that your CI failed and I'm now attempting to fix it automatically.\n\n` +
                    `**What I'm doing:**\n` +
                    `- 🔍 Analyzing the test failures\n` +
                    `- 🛠️ Generating fixes for the failing tests\n` +
                    `- 📝 Creating a commit with the fixes\n\n` +
                    `**Track progress:** [View in GitHub Actions](${actionsLink})\n\n` +
                    `If I can fix the issues, I'll push a commit to your branch. Otherwise, I'll provide details about what went wrong.`,
            });

            context.log.info('Nova workflow triggered successfully', {
              pr_number: pr.number,
              workflow_id: novaWf.id
            });
          } else {
            checkSummary = `⚠️ CI failed on PR #${pr.number}, but Nova CI-Rescue workflow not found.\n\n` +
                          `**To enable automatic fixes:**\n` +
                          `1. Add \`.github/workflows/nova-ci-rescue.yml\` to your repository\n` +
                          `2. Configure the workflow with your Nova API key\n` +
                          `3. Push the changes\n\n` +
                          `[Learn more about Nova CI-Rescue](https://github.com/nova-ci-rescue/docs)`;

            checkConclusion = 'neutral';

            // Provide setup instructions
            await context.octokit.issues.createComment({
              owner,
              repo,
              issue_number: pr.number,
              body: `## ⚠️ CI Failed - Nova CI-Rescue Not Configured\n\n` +
                    `I noticed your CI failed, but I can't help yet because the Nova workflow isn't set up.\n\n` +
                    `**Quick Setup:**\n` +
                    `\`\`\`bash\n` +
                    `# Add Nova workflow to your repo\n` +
                    `curl -L https://raw.githubusercontent.com/nova-ci-rescue/templates/main/nova-ci-rescue.yml > .github/workflows/nova-ci-rescue.yml\n` +
                    `\n` +
                    `# Set your Nova API key as a repository secret\n` +
                    `# Go to Settings > Secrets > Actions > New repository secret\n` +
                    `# Name: NOVA_API_KEY\n` +
                    `# Value: your-nova-api-key\n` +
                    `\`\`\`\n\n` +
                    `Once configured, I'll automatically fix failing tests on your PRs! 🚀`,
            });
          }
        } catch (err) {
          const message = err?.message || 'unknown error';
          checkSummary = `❌ Error: Failed to trigger Nova CI-Rescue: ${message}`;
          checkConclusion = 'failure';

          context.log.error('Failed to handle CI failure', {
            error: message,
            pr_number: pr?.number
          });
        }

        // Update check status
        await context.octokit.checks.create({
          owner,
          repo,
          name: 'Nova CI-Rescue',
          head_sha: headSha,
          status: 'completed',
          conclusion: checkConclusion,
          output: {
            title: checkConclusion === 'success' ? 'CI-Rescue Triggered' : 'CI-Rescue Status',
            summary: checkSummary,
          },
        });
      }
    }
  });

  // Helper function to create welcome issue
  async function createWelcomeIssue(context, owner, repo) {
    const issueBody = `# 🎉 Welcome to Nova CI-Rescue!\n\n` +
      `Thank you for installing Nova CI-Rescue! This GitHub App will automatically attempt to fix failing tests in your pull requests.\n\n` +
      `## 🚀 Quick Setup\n\n` +
      `To complete the setup, you need to add the Nova workflow to your repository:\n\n` +
      `### 1. Create the workflow file\n` +
      `Create \`.github/workflows/nova-ci-rescue.yml\` with the following content:\n\n` +
      `\`\`\`yaml\n` +
      `name: Nova CI-Rescue Auto-Fix\n` +
      `on:\n` +
      `  workflow_dispatch:\n` +
      `    inputs:\n` +
      `      pr_number:\n` +
      `        description: 'Pull request number to fix'\n` +
      `        required: true\n` +
      `        type: string\n\n` +
      `jobs:\n` +
      `  auto-fix:\n` +
      `    runs-on: ubuntu-latest\n` +
      `    steps:\n` +
      `      - uses: actions/checkout@v4\n` +
      `        with:\n` +
      `          token: \${{ secrets.GITHUB_TOKEN }}\n` +
      `          fetch-depth: 0\n\n` +
      `      - name: Run Nova CI-Rescue\n` +
      `        uses: nova-ci-rescue/action@v1\n` +
      `        with:\n` +
      `          pr_number: \${{ inputs.pr_number }}\n` +
      `          nova_api_key: \${{ secrets.NOVA_API_KEY }}\n` +
      `\`\`\`\n\n` +
      `### 2. Add your Nova API key\n` +
      `1. Go to **Settings** → **Secrets and variables** → **Actions**\n` +
      `2. Click **New repository secret**\n` +
      `3. Name: \`NOVA_API_KEY\`\n` +
      `4. Value: Your Nova API key (get one at [nova-ci.com](https://nova-ci.com))\n\n` +
      `## ✅ That's it!\n\n` +
      `Once configured, Nova CI-Rescue will:\n` +
      `- Monitor all pull requests for CI failures\n` +
      `- Automatically attempt to fix failing tests\n` +
      `- Push fixes directly to the PR branch\n` +
      `- Comment with the results\n\n` +
      `## 📚 Resources\n` +
      `- [Documentation](https://github.com/nova-ci-rescue/docs)\n` +
      `- [Example repositories](https://github.com/nova-ci-rescue/examples)\n` +
      `- [Support](https://github.com/nova-ci-rescue/support)\n\n` +
      `---\n` +
      `*This issue was created automatically by Nova CI-Rescue. Feel free to close it once you've completed the setup!*`;

    await context.octokit.issues.create({
      owner,
      repo,
      title: '🤖 Nova CI-Rescue Setup Instructions',
      body: issueBody,
      labels: ['nova-ci-rescue', 'setup']
    });
  }
};
      let githubError = null;
      let installFlowTest = 'unchecked';
      let installFlowError = null;
      let appDetails = null;

      try {
        // Check if we have the required credentials
        if (process.env.APP_ID && process.env.PRIVATE_KEY && process.env.WEBHOOK_SECRET) {
          // Step 1: Test basic app authentication
          try {
            const auth = await app.auth();
            // app.auth() returns an Octokit instance if successful
            githubAuth = 'authenticated';

            // Step 2: Test installation flow capabilities
            try {
              // Test 2a: Get app details
              const appInfo = await app.octokit.apps.getAuthenticated();
              appDetails = {
                name: appInfo.data.name,
                slug: appInfo.data.slug,
                permissions: appInfo.data.permissions,
                events: appInfo.data.events
              };

              // Test 2b: List installations (this tests the app's ability to see installations)
              const installations = await app.octokit.apps.listInstallations();
              installFlowTest = 'passed';

              // Test 2c: If there are installations, test installation authentication
              if (installations.data.length > 0) {
                const firstInstall = installations.data[0];
                const installAuth = await app.auth(firstInstall.id);
                if (installAuth) {
                  installFlowTest = 'installation_auth_passed';
                }
              }

            } catch (installError) {
              installFlowTest = 'partial';
              installFlowError = `Installation flow test failed: ${installError.message}`;
            }

          } catch (authError) {
            githubAuth = 'auth_failed';
            githubError = `Authentication failed: ${authError.message}`;
          }
        } else {
          githubAuth = 'missing_credentials';
          githubError = 'Missing APP_ID, PRIVATE_KEY, or WEBHOOK_SECRET';
        }
      } catch (error) {
        githubAuth = 'failed';
        githubError = error.message;
        installFlowTest = 'failed';
        installFlowError = error.message;
      }

      // Determine overall health status
      let overallStatus = 'healthy';
      let overallError = null;

      if (githubAuth !== 'authenticated') {
        overallStatus = 'unhealthy';
        overallError = githubError || 'GitHub authentication failed';
      } else if (installFlowTest === 'failed') {
        overallStatus = 'degraded';
        overallError = installFlowError || 'Installation flow test failed';
      } else if (installFlowTest === 'partial') {
        overallStatus = 'degraded';
        overallError = installFlowError || 'Installation flow partially working';
      }

      const healthStatus = {
        status: overallStatus,
        service: 'nova-ci-rescue',
        timestamp: new Date().toISOString(),
        version: process.env.APP_VERSION || '1.0.0',
        installations_count: installations.size,
        error: overallError,
        github: {
          auth_status: githubAuth,
          error: githubError,
          app_id: process.env.APP_ID ? 'configured' : 'missing',
          private_key: process.env.PRIVATE_KEY ? 'configured' : 'missing',
          webhook_secret: process.env.WEBHOOK_SECRET ? 'configured' : 'missing',
          install_flow_test: installFlowTest,
          install_flow_error: installFlowError,
          app_details: appDetails
        },
        memory: {
          used_mb: Math.round(memoryUsage.heapUsed / 1024 / 1024),
          total_mb: Math.round(memoryUsage.heapTotal / 1024 / 1024)
        },
        uptime_seconds: Math.floor(process.uptime())
      };

      // Return appropriate HTTP status
      const httpStatus = overallStatus === 'healthy' ? 200 :
                        overallStatus === 'degraded' ? 200 : 503;

      res.status(httpStatus).json(healthStatus);
    });

    // Root endpoint for basic checks
    router.get('/', (req, res) => {
      res.status(200).send(`
        <!DOCTYPE html>
        <html>
        <head>
          <title>Nova CI-Rescue</title>
          <style>
            body {
              font-family: -apple-system, system-ui, sans-serif;
              max-width: 600px;
              margin: 100px auto;
              padding: 20px;
              text-align: center;
            }
            h1 { font-size: 48px; margin: 0; }
            .logo { font-size: 72px; margin-bottom: 20px; }
            .links { margin-top: 30px; }
            a {
              color: #0366d6;
              text-decoration: none;
              margin: 0 10px;
            }
            a:hover { text-decoration: underline; }
            .status {
              background: #d1f5d3;
              padding: 10px 20px;
              border-radius: 6px;
              display: inline-block;
              margin-top: 20px;
            }
          </style>
        </head>
        <body>
          <div class="logo">🤖</div>
          <h1>Nova CI-Rescue</h1>
          <p>GitHub App is running! 🚀</p>
          <div class="status">✅ Healthy - ${installations.size} active installations</div>
          <div class="links">
            <a href="/setup">Setup Guide</a> •
            <a href="/health">Health Status</a> •
            <a href="https://github.com/marketplace/nova-ci-rescue">Marketplace</a>
          </div>
        </body>
        </html>
      `);
    });

    // Setup guide endpoint
    router.get('/setup', (req, res) => {
      const setupPath = path.join(__dirname, 'templates', 'setup.html');

      fs.readFile(setupPath, 'utf8', (err, data) => {
        if (err) {
          app.log.error('Failed to read setup guide', err);
          res.status(500).send('Setup guide not found');
          return;
        }
        res.status(200).send(data);
      });
    });

    // Detailed probe endpoint for monitoring
    router.get('/probe', async (req, res) => {
      try {
        // Check if we can authenticate with GitHub
        const authenticated = app.state?.id ? true : false;

        res.status(200).json({
          status: 'healthy',
          service: 'nova-ci-rescue',
          timestamp: new Date().toISOString(),
          version: process.env.APP_VERSION || '1.0.0',
          checks: {
            github_auth: authenticated ? 'connected' : 'pending',
            app_id: process.env.APP_ID ? 'configured' : 'missing',
            webhook_secret: process.env.WEBHOOK_SECRET ? 'configured' : 'missing'
          },
          stats: {
            active_installations: installations.size,
            uptime: process.uptime()
          }
        });
      } catch (error) {
        res.status(503).json({
          status: 'unhealthy',
          error: error.message
        });
      }
    });
  }

  // Handle new installations
  app.on('installation.created', async (context) => {
    const { installation, sender } = context.payload;
    const installationId = installation.id;
    const account = installation.account;

    // Track installation
    installations.set(installationId, {
      id: installationId,
      account: account.login,
      type: account.type,
      created_at: new Date().toISOString(),
      repositories: installation.repository_selection === 'all' ? 'all' : installation.repositories
    });

    // Persist to storage
    saveInstallations();

    context.log.info('New installation created', {
      installation_id: installationId,
      account: account.login,
      account_type: account.type,
      repository_selection: installation.repository_selection
    });

    // Create a welcome issue in each repository
    if (installation.repositories && installation.repository_selection === 'selected') {
      for (const repo of installation.repositories) {
        try {
          await createWelcomeIssue(context, account.login, repo.name);
        } catch (error) {
          context.log.error('Failed to create welcome issue', {
            repo: repo.name,
            error: error.message
          });
        }
      }
    }
  });

  // Handle installation deletions
  app.on('installation.deleted', async (context) => {
    const { installation } = context.payload;
    const installationId = installation.id;

    installations.delete(installationId);

    // Persist to storage
    saveInstallations();

    context.log.info('Installation deleted', {
      installation_id: installationId,
      account: installation.account.login
    });
  });

  // Handle repository additions to installation
  app.on('installation_repositories.added', async (context) => {
    const { installation, repositories_added, sender } = context.payload;

    context.log.info('Repositories added to installation', {
      installation_id: installation.id,
      account: installation.account.login,
      repos_added: repositories_added.map(r => r.name)
    });

    // Create welcome issues in newly added repositories
    for (const repo of repositories_added) {
      try {
        await createWelcomeIssue(context, installation.account.login, repo.name);
      } catch (error) {
        context.log.error('Failed to create welcome issue', {
          repo: repo.name,
          error: error.message
        });
      }
    }
  });

  // Handle repository removals from installation
  app.on('installation_repositories.removed', async (context) => {
    const { installation, repositories_removed } = context.payload;

    context.log.info('Repositories removed from installation', {
      installation_id: installation.id,
      account: installation.account.login,
      repos_removed: repositories_removed.map(r => r.name)
    });
  });

  // Main CI rescue logic
  app.on(['pull_request.opened', 'workflow_run.completed', 'check_suite.requested'], async (context) => {
    const { owner, repo } = context.repo();
    const installationId = context.payload.installation?.id;

    // Check rate limit
    if (installationId && !checkRateLimit(installationId)) {
      context.log.warn('Rate limit exceeded', {
        installation_id: installationId,
        owner,
        repo
      });
      return;
    }

    // Log event with installation context
    context.log.info(`Event: ${context.name}`, {
      installation_id: installationId,
      owner,
      repo,
      event_action: context.payload.action
    });

    const headSha =
      context.payload.pull_request?.head?.sha ||
      context.payload.workflow_run?.head_sha ||
      context.payload.check_suite?.head_sha;

    if (!headSha) {
      context.log.warn('No head SHA found for event', { event: context.name });
      return;
    }

    let checkSummary = 'Nova CI-Rescue is monitoring your CI. Waiting for results...';
    let checkConclusion = 'neutral';

    // Handle new PR opened
    if (context.name === 'pull_request' && context.payload.action === 'opened') {
      try {
        await context.octokit.checks.create({
          owner,
          repo,
          name: 'Nova CI-Rescue',
          head_sha: headSha,
          status: 'completed',
          conclusion: 'neutral',
          output: {
            title: 'CI-Rescue Ready',
            summary: '🤖 Nova CI-Rescue is monitoring this PR. If your CI fails, I\'ll attempt to fix it automatically!',
          },
        });
      } catch (error) {
        context.log.error('Failed to create initial check', { error: error.message });
      }
      return;
    }

    // Handle workflow run completion
    if (context.name === 'workflow_run' && context.payload.action === 'completed') {
      const workflowRun = context.payload.workflow_run;
      const failed = workflowRun?.conclusion === 'failure';
      const pr = workflowRun?.pull_requests?.[0];
      const headBranch = workflowRun?.head_branch || pr?.head?.ref;

      if (failed && pr) {
        context.log.info('CI failure detected on PR', {
          pr_number: pr.number,
          workflow_name: workflowRun.name,
          branch: headBranch
        });

        try {
          // Check if Nova workflow exists
          const { data } = await context.octokit.actions.listRepoWorkflows({ owner, repo });
          const novaWf = data.workflows.find(
            (wf) => wf?.name === 'Nova CI-Rescue Auto-Fix' ||
                    (wf?.path || '').endsWith('/nova-ci-rescue.yml') ||
                    (wf?.path || '').endsWith('/nova-ci-rescue.yaml')
          );

          if (novaWf) {
            // Trigger Nova workflow
            await context.octokit.actions.createWorkflowDispatch({
              owner,
              repo,
              workflow_id: novaWf.id,
              ref: headBranch || 'main',
              inputs: {
                pr_number: String(pr.number),
                triggered_by: 'github-app'
              },
            });

            const actionsLink = `https://github.com/${owner}/${repo}/actions/workflows/${encodeURIComponent(
              novaWf.path.split('/').pop() || 'nova-ci-rescue.yml'
            )}`;

            checkSummary = `🔧 CI failed on PR #${pr.number}. I've triggered Nova CI-Rescue to attempt automatic fixes!\n\n` +
                          `**Branch:** \`${headBranch}\`\n` +
                          `**Failed Workflow:** ${workflowRun.name}\n` +
                          `**Nova Progress:** [View in Actions](${actionsLink})\n\n` +
                          `I'll analyze the failures and try to fix them automatically. This may take a few minutes.`;

            checkConclusion = 'success';

            // Leave a comment on the PR
            await context.octokit.issues.createComment({
              owner,
              repo,
              issue_number: pr.number,
              body: `## 🤖 Nova CI-Rescue Activated!\n\n` +
                    `I detected that your CI failed and I'm now attempting to fix it automatically.\n\n` +
                    `**What I'm doing:**\n` +
                    `- 🔍 Analyzing the test failures\n` +
                    `- 🛠️ Generating fixes for the failing tests\n` +
                    `- 📝 Creating a commit with the fixes\n\n` +
                    `**Track progress:** [View in GitHub Actions](${actionsLink})\n\n` +
                    `If I can fix the issues, I'll push a commit to your branch. Otherwise, I'll provide details about what went wrong.`,
            });

            context.log.info('Nova workflow triggered successfully', {
              pr_number: pr.number,
              workflow_id: novaWf.id
            });
          } else {
            checkSummary = `⚠️ CI failed on PR #${pr.number}, but Nova CI-Rescue workflow not found.\n\n` +
                          `**To enable automatic fixes:**\n` +
                          `1. Add \`.github/workflows/nova-ci-rescue.yml\` to your repository\n` +
                          `2. Configure the workflow with your Nova API key\n` +
                          `3. Push the changes\n\n` +
                          `[Learn more about Nova CI-Rescue](https://github.com/nova-ci-rescue/docs)`;

            checkConclusion = 'neutral';

            // Provide setup instructions
            await context.octokit.issues.createComment({
              owner,
              repo,
              issue_number: pr.number,
              body: `## ⚠️ CI Failed - Nova CI-Rescue Not Configured\n\n` +
                    `I noticed your CI failed, but I can't help yet because the Nova workflow isn't set up.\n\n` +
                    `**Quick Setup:**\n` +
                    `\`\`\`bash\n` +
                    `# Add Nova workflow to your repo\n` +
                    `curl -L https://raw.githubusercontent.com/nova-ci-rescue/templates/main/nova-ci-rescue.yml > .github/workflows/nova-ci-rescue.yml\n` +
                    `\n` +
                    `# Set your Nova API key as a repository secret\n` +
                    `# Go to Settings > Secrets > Actions > New repository secret\n` +
                    `# Name: NOVA_API_KEY\n` +
                    `# Value: your-nova-api-key\n` +
                    `\`\`\`\n\n` +
                    `Once configured, I'll automatically fix failing tests on your PRs! 🚀`,
            });
          }
        } catch (err) {
          const message = err?.message || 'unknown error';
          checkSummary = `❌ Error: Failed to trigger Nova CI-Rescue: ${message}`;
          checkConclusion = 'failure';

          context.log.error('Failed to handle CI failure', {
            error: message,
            pr_number: pr?.number
          });
        }

        // Update check status
        await context.octokit.checks.create({
          owner,
          repo,
          name: 'Nova CI-Rescue',
          head_sha: headSha,
          status: 'completed',
          conclusion: checkConclusion,
          output: {
            title: checkConclusion === 'success' ? 'CI-Rescue Triggered' : 'CI-Rescue Status',
            summary: checkSummary,
          },
        });
      }
    }
  });

  // Helper function to create welcome issue
  async function createWelcomeIssue(context, owner, repo) {
    const issueBody = `# 🎉 Welcome to Nova CI-Rescue!\n\n` +
      `Thank you for installing Nova CI-Rescue! This GitHub App will automatically attempt to fix failing tests in your pull requests.\n\n` +
      `## 🚀 Quick Setup\n\n` +
      `To complete the setup, you need to add the Nova workflow to your repository:\n\n` +
      `### 1. Create the workflow file\n` +
      `Create \`.github/workflows/nova-ci-rescue.yml\` with the following content:\n\n` +
      `\`\`\`yaml\n` +
      `name: Nova CI-Rescue Auto-Fix\n` +
      `on:\n` +
      `  workflow_dispatch:\n` +
      `    inputs:\n` +
      `      pr_number:\n` +
      `        description: 'Pull request number to fix'\n` +
      `        required: true\n` +
      `        type: string\n\n` +
      `jobs:\n` +
      `  auto-fix:\n` +
      `    runs-on: ubuntu-latest\n` +
      `    steps:\n` +
      `      - uses: actions/checkout@v4\n` +
      `        with:\n` +
      `          token: \${{ secrets.GITHUB_TOKEN }}\n` +
      `          fetch-depth: 0\n\n` +
      `      - name: Run Nova CI-Rescue\n` +
      `        uses: nova-ci-rescue/action@v1\n` +
      `        with:\n` +
      `          pr_number: \${{ inputs.pr_number }}\n` +
      `          nova_api_key: \${{ secrets.NOVA_API_KEY }}\n` +
      `\`\`\`\n\n` +
      `### 2. Add your Nova API key\n` +
      `1. Go to **Settings** → **Secrets and variables** → **Actions**\n` +
      `2. Click **New repository secret**\n` +
      `3. Name: \`NOVA_API_KEY\`\n` +
      `4. Value: Your Nova API key (get one at [nova-ci.com](https://nova-ci.com))\n\n` +
      `## ✅ That's it!\n\n` +
      `Once configured, Nova CI-Rescue will:\n` +
      `- Monitor all pull requests for CI failures\n` +
      `- Automatically attempt to fix failing tests\n` +
      `- Push fixes directly to the PR branch\n` +
      `- Comment with the results\n\n` +
      `## 📚 Resources\n` +
      `- [Documentation](https://github.com/nova-ci-rescue/docs)\n` +
      `- [Example repositories](https://github.com/nova-ci-rescue/examples)\n` +
      `- [Support](https://github.com/nova-ci-rescue/support)\n\n` +
      `---\n` +
      `*This issue was created automatically by Nova CI-Rescue. Feel free to close it once you've completed the setup!*`;

    await context.octokit.issues.create({
      owner,
      repo,
      title: '🤖 Nova CI-Rescue Setup Instructions',
      body: issueBody,
      labels: ['nova-ci-rescue', 'setup']
    });
  }
};
