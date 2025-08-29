# Deployment Guide for Nova CI-Rescue GitHub App

This guide covers deploying the Nova CI-Rescue GitHub App to Fly.io for production use.

## Prerequisites

1. **GitHub App Created**

   - Go to GitHub Settings > Developer settings > GitHub Apps
   - Create a new GitHub App with these permissions:
     - **Repository**: Contents (read/write), Issues (write), Pull requests (write), Actions (write), Checks (write)
     - **Organization**: Members (read)
   - Subscribe to webhooks: `pull_request`, `workflow_run`, `check_suite`, `installation`, `installation_repositories`

2. **Fly.io Account**
   - Sign up at https://fly.io
   - Install Fly CLI: `brew install flyctl` or `curl -L https://fly.io/install.sh | sh`

## Deployment Steps

### 1. Initial Setup

```bash
# Clone the repository
git clone https://github.com/novasolve/nova-ci-rescue.git
cd nova-ci-rescue

# Authenticate with Fly
flyctl auth login

# Create the Fly app (first time only)
flyctl apps create nova-ci-rescue --org personal
```

### 2. Create Persistent Volume (Optional but Recommended)

```bash
# Create a 1GB volume for storing installation data
flyctl volumes create nova_data --size 1 --region sjc
```

### 3. Set Secrets

```bash
# GitHub App credentials
flyctl secrets set APP_ID=your_github_app_id
flyctl secrets set PRIVATE_KEY="$(cat path/to/private-key.pem)"
flyctl secrets set WEBHOOK_SECRET=your_webhook_secret

# Optional: Set app version
flyctl secrets set APP_VERSION=1.0.0

# Optional: Nova API key if using the action
flyctl secrets set NOVA_API_KEY=your_nova_api_key
```

### 4. Deploy

```bash
# Deploy the app
flyctl deploy

# Check deployment status
flyctl status

# View logs
flyctl logs
```

### 5. Verify Health

```bash
# Check health endpoint
curl https://nova-ci-rescue.fly.dev/health

# Expected response:
# {
#   "status": "healthy",
#   "service": "nova-ci-rescue",
#   "timestamp": "2024-01-15T10:30:00.000Z",
#   "version": "1.0.0",
#   "installations_count": 0,
#   "memory": {
#     "used_mb": 45,
#     "total_mb": 128
#   },
#   "uptime_seconds": 3600
# }
```

## Configuration Options

### Basic Configuration (Current)

The default `fly.toml` provides:

- 1 machine always running
- 256MB RAM (sufficient for most cases)
- Auto-scaling up to 3 machines
- Health checks every 15 seconds

### Advanced Configuration

For high-traffic apps, use `fly.toml.production`:

- 512MB RAM per machine
- Scale up to 5 machines
- Multi-region deployment
- Persistent storage volume
- Prometheus metrics endpoint

To use advanced configuration:

```bash
cp fly.toml.production fly.toml
flyctl deploy
```

## Monitoring

### View Metrics

```bash
# Real-time metrics
flyctl dashboard metrics

# Application logs
flyctl logs --tail

# SSH into running instance
flyctl ssh console
```

### Health Endpoints

- `/` - Human-friendly status page
- `/health` - JSON health check
- `/probe` - Detailed diagnostics
- `/setup` - Installation guide for users

## Scaling

### Manual Scaling

```bash
# Scale to specific count
flyctl scale count 2

# Check current scale
flyctl scale show
```

### Auto-scaling

The app automatically scales based on load:

- Minimum: 1 machine (always ready)
- Maximum: 3 machines (or 5 with advanced config)
- Scales at 80% connection capacity

## Troubleshooting

### Check Logs

```bash
flyctl logs --tail
```

### Common Issues

1. **Health checks failing**

   - Ensure PORT environment variable is not set
   - Check internal_port matches Dockerfile EXPOSE

2. **Webhooks not received**

   - Verify webhook URL in GitHub App settings
   - Check webhook secret matches

3. **Out of memory**
   - Scale up memory: `flyctl scale memory 512`
   - Check for memory leaks in logs

### Restart App

```bash
flyctl apps restart
```

## Updates

### Deploy Updates

```bash
git pull
flyctl deploy
```

### Zero-downtime Deployment

The rolling deployment strategy ensures:

- New version deployed to new machines
- Health checks pass before switching traffic
- Old machines terminated after success

## Backup

### Export Installation Data

```bash
flyctl ssh console -C "cat /data/installations.json" > installations-backup.json
```

### Restore Installation Data

```bash
cat installations-backup.json | flyctl ssh console -C "cat > /data/installations.json"
```

## GitHub Marketplace

Once deployed and tested:

1. Update GitHub App settings:

   - Homepage URL: `https://nova-ci-rescue.fly.dev`
   - Webhook URL: `https://nova-ci-rescue.fly.dev/api/github/webhooks`
   - Setup URL: `https://nova-ci-rescue.fly.dev/setup`

2. Submit to Marketplace:
   - Go to your GitHub App settings
   - Click "List in Marketplace"
   - Follow the submission process

## Support

For issues or questions:

- GitHub Issues: https://github.com/novasolve/nova-ci-rescue/issues
- Documentation: https://nova-ci-rescue.fly.dev/setup
