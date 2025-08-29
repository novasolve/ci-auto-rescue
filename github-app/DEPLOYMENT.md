# Nova CI-Rescue GitHub App Deployment Guide

This guide covers deploying the Nova CI-Rescue GitHub App to Fly.io for production use.

## Prerequisites

- Fly.io account and CLI (`flyctl`) installed
- GitHub App created with proper permissions
- Private key and webhook secret from GitHub App
- Node.js and npm installed locally

## Quick Deployment

### 1. Clone and Setup

```bash
git clone https://github.com/ci-auto-rescue/ci-auto-rescue.git
cd ci-auto-rescue/github-app
npm install
```

### 2. Create Fly.io App

```bash
flyctl launch --name nova-ci-rescue
```

### 3. Configure Secrets

```bash
# GitHub App credentials
flyctl secrets set APP_ID=your_app_id
flyctl secrets set PRIVATE_KEY="$(cat path/to/private-key.pem)"
flyctl secrets set WEBHOOK_SECRET=your_webhook_secret

# Optional: OpenAI API key for enhanced features
flyctl secrets set OPENAI_API_KEY=your_openai_api_key
```

### 4. Create Persistent Storage

```bash
flyctl volumes create data --size 1
```

### 5. Deploy

```bash
flyctl deploy
```

## Detailed Configuration

### Fly.io Configuration

The `fly.toml` file contains the production configuration:

```toml
app = "nova-ci-rescue"
primary_region = "iad"

[build]
  dockerfile = "Dockerfile"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = false
  min_machines_running = 1

[[http_service.checks]]
  grace_period = "10s"
  interval = "30s"
  method = "GET"
  timeout = "5s"
  path = "/health"

[mounts]
  source = "data"
  destination = "/data"
```

### Environment Variables

| Variable         | Description                    | Required |
| ---------------- | ------------------------------ | -------- |
| `APP_ID`         | GitHub App ID                  | Yes      |
| `PRIVATE_KEY`    | GitHub App private key content | Yes      |
| `WEBHOOK_SECRET` | GitHub webhook secret          | Yes      |
| `OPENAI_API_KEY` | OpenAI API key for AI features | No       |
| `NODE_ENV`       | Environment (production)       | No       |
| `PORT`           | Port to listen on (8080)       | No       |

## Health Checks

The app provides several health endpoints:

- `GET /` - Basic homepage
- `GET /health` - Comprehensive health check
- `GET /probe` - Detailed diagnostics

### Health Check Response

```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00.000Z",
  "uptime": "1d 2h 30m",
  "github": {
    "auth_status": "authenticated",
    "install_flow_test": "passed",
    "app_details": {
      "id": 12345,
      "name": "Nova CI-Rescue"
    }
  }
}
```

## Monitoring

### Logs

```bash
flyctl logs
```

### Metrics

Monitor the `/health` endpoint for:

- Response time
- GitHub API connectivity
- Installation count
- Error rates

### Scaling

```bash
# Scale up
flyctl scale count 2

# Scale down
flyctl scale count 1
```

## Troubleshooting

### Common Issues

1. **Health check failures**

   ```bash
   flyctl logs | grep health
   ```

   Check GitHub App credentials and network connectivity.

2. **Webhook delivery failures**

   ```bash
   flyctl logs | grep webhook
   ```

   Verify webhook secret matches GitHub App configuration.

3. **Storage issues**
   ```bash
   flyctl volumes list
   ```
   Check if data volume is properly mounted.

### Rollback

```bash
flyctl releases
flyctl releases rollback <version>
```

## Security Considerations

- Store secrets securely using Fly.io secrets
- Regularly rotate GitHub App private keys
- Monitor webhook payloads for suspicious activity
- Use HTTPS for all communications
- Implement rate limiting (built-in)

## GitHub Marketplace

For GitHub Marketplace listing:

1. **App Manifest**: Use the provided manifest in `templates/`
2. **Setup URL**: `https://nova-ci-rescue.fly.dev/setup`
3. **Support**: Configure support email and documentation URLs
4. **Pricing**: Set up pricing plans if applicable

## Maintenance

### Updates

```bash
git pull origin main
flyctl deploy
```

### Backups

```bash
# Backup installation data
flyctl ssh sftp get /data/installations.json
```

### Monitoring

Set up monitoring for:

- Application logs
- Health endpoint status
- Resource usage
- GitHub webhook deliveries
