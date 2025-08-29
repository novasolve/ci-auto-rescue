# Nova CI-Rescue GitHub App

A Probot-powered GitHub App that automatically triggers CI rescue workflows when tests fail on pull requests. Ready for GitHub Marketplace one-click installations and multi-tenant deployments.

## Features

- 🔍 **Automatic CI Failure Detection**: Monitors all PRs for failing tests
- 🛠️ **Smart Auto-Fix**: Triggers Nova AI to fix failing tests automatically
- 💬 **PR Comments & Status Checks**: Keeps developers informed of fix progress
- 🏢 **Multi-Tenant Ready**: Handles unlimited installations across organizations
- 🎯 **GitHub Marketplace Compatible**: One-click installation support
- 📊 **Health Monitoring**: Built-in health endpoints for Fly.io and monitoring
- 🚀 **Zero Configuration**: Works out of the box with sensible defaults
- 📝 **Automatic Onboarding**: Creates setup instructions when installed

## How It Works

### 1. Installation

When someone installs the app from GitHub Marketplace:

- The app receives an `installation.created` webhook
- A welcome issue is automatically created with setup instructions
- The installation is tracked for monitoring

### 2. PR Monitoring

For each pull request:

- Creates a "Nova CI-Rescue" check run
- Monitors workflow runs for failures
- Automatically triggers fixes when CI fails

### 3. Auto-Fix Process

When CI fails on a PR:

- Detects the failure via `workflow_run.completed` webhook
- Checks if Nova workflow exists in the repository
- Triggers the workflow with the PR number
- Comments on the PR with progress updates
- Updates the check run with results

### 4. Multi-Tenant Support

The app handles multiple installations seamlessly:

- Tracks each installation separately
- Isolates webhook events by installation
- Provides per-installation monitoring
- Handles repository additions/removals dynamically

## Health Endpoints

The app provides several health endpoints for monitoring and GitHub Marketplace requirements:

### `/` - Home Page

- **Method**: GET
- **Response**: HTML page with app status and links
- **Use**: Human-friendly landing page showing installation count

### `/health` - Health Check Endpoint

- **Method**: GET
- **Response**: JSON with health status
- **Use**: Primary health check for Fly.io and monitoring services

```json
{
  "status": "healthy",
  "service": "nova-ci-rescue",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "version": "1.0.0",
  "installations_count": 42
}
```

### `/setup` - Setup Guide

- **Method**: GET
- **Response**: Interactive HTML setup guide
- **Use**: Help users configure Nova in their repositories

### `/probe` - Detailed Probe Endpoint

- **Method**: GET
- **Response**: Detailed health information including configuration status
- **Use**: Debugging and detailed monitoring

```json
{
  "status": "healthy",
  "service": "nova-ci-rescue",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "version": "1.0.0",
  "checks": {
    "github_auth": "connected",
    "app_id": "configured",
    "webhook_secret": "configured"
  },
  "stats": {
    "active_installations": 42,
    "uptime": 3600
  }
}
```

## Deployment on Fly.io

### Prerequisites

1. Install Fly CLI: `brew install flyctl` (macOS) or see [fly.io/docs/getting-started/installing-flyctl/](https://fly.io/docs/getting-started/installing-flyctl/)
2. Authenticate: `flyctl auth login`

### Environment Variables (Fly Secrets)

Set the following secrets for your Fly app:

```bash
flyctl secrets set APP_ID=your_github_app_id
flyctl secrets set PRIVATE_KEY="$(cat path/to/private-key.pem)"
flyctl secrets set WEBHOOK_SECRET=your_webhook_secret
```

Optional:

```bash
flyctl secrets set APP_VERSION=1.0.0
```

### Deploy

From the repository root:

```bash
flyctl deploy
```

### Monitoring

Check app status:

```bash
flyctl status
flyctl logs
```

Test health endpoint:

```bash
curl https://ci-auto-rescue.fly.dev/health
```

## GitHub Marketplace Requirements

This app is configured to meet GitHub Marketplace requirements:

1. **Health Check Endpoint**: `/health` returns 200 OK when the app is healthy
2. **HTTPS**: Enforced via Fly.io configuration
3. **Auto-scaling**: Configured with min_machines_running = 0 for cost efficiency
4. **Monitoring**: Health checks run every 10 seconds with a 30-second grace period

## Local Development

1. Clone the repository
2. Install dependencies:

   ```bash
   cd github-app
   npm install
   ```

3. Set environment variables:

   ```bash
   export APP_ID=your_app_id
   export PRIVATE_KEY="$(cat path/to/private-key.pem)"
   export WEBHOOK_SECRET=your_webhook_secret
   export PORT=3000
   ```

4. Run the app:

   ```bash
   npm start
   ```

5. Use ngrok or similar for webhook testing:
   ```bash
   ngrok http 3000
   ```

## Events Handled

### Installation Events

- `installation.created` - When app is installed (creates welcome issue)
- `installation.deleted` - When app is uninstalled (cleanup)
- `installation_repositories.added` - When repos are added to installation
- `installation_repositories.removed` - When repos are removed from installation

### CI/PR Events

- `pull_request.opened` - When a new PR is created (adds initial check)
- `workflow_run.completed` - When a workflow finishes (triggers fixes if failed)
- `check_suite.requested` - When checks are requested (monitoring)

## License

See the main repository LICENSE file.
