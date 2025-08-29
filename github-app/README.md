# Nova CI-Rescue GitHub App

A GitHub App that automatically fixes failing CI tests using AI-powered analysis and patch generation.

## Features

- **Automatic CI Test Fixing**: Monitors your repositories and automatically creates fixes for failing tests
- **Multi-tenant Support**: Handles multiple installations securely with rate limiting
- **Health Monitoring**: Comprehensive health endpoints for Fly.io and GitHub Marketplace compliance
- **Persistent Storage**: Installation data stored in mounted volume
- **Rate Limiting**: Prevents abuse with configurable request limits per installation

## Installation

### Option 1: One-Click Install (Recommended)

Visit the [GitHub Marketplace](https://github.com/marketplace/nova-ci-rescue) and click "Install" to add the app to your repositories.

### Option 2: Manual Setup

1. Go to your repository's Settings → Developer settings → GitHub Apps
2. Click "New GitHub App"
3. Configure with the following settings:
   - **Name**: Nova CI-Rescue
   - **Homepage URL**: `https://nova-ci-rescue.fly.dev`
   - **Webhook URL**: `https://nova-ci-rescue.fly.dev/webhooks`
   - **Webhook Secret**: Generate a random secret
   - **Repository permissions**:
     - Repository contents: Read & Write
     - Pull requests: Read & Write
     - Issues: Read & Write
     - Commit statuses: Read & Write
   - **Subscribe to events**: Pull request, Status

## Configuration

Create a `.nova-ci-rescue.yml` file in your repository root:

```yaml
max_iters: 3
timeout: 300
paths:
  include:
    - "**/*.py"
    - "**/*.js"
    - "**/*.ts"
  exclude:
    - "**/node_modules/**"
    - "**/__pycache__/**"
triggers:
  - "ci-failure"
language: "python"
safety:
  max_file_size: 1000000
  allow_network: false
```

## Health Endpoints

- `GET /` - Basic homepage
- `GET /health` - Comprehensive health check with GitHub API testing
- `GET /probe` - Detailed diagnostics for monitoring

## Development

### Local Development

```bash
npm install
npm run dev
```

### Docker

```bash
docker build -t nova-ci-rescue .
docker run -p 8080:8080 nova-ci-rescue
```

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions to Fly.io.

## Support

- [Documentation](https://nova-ci-rescue.fly.dev/docs)
- [Troubleshooting Guide](https://nova-ci-rescue.fly.dev/troubleshooting)
- [GitHub Issues](https://github.com/ci-auto-rescue/ci-auto-rescue/issues)

A GitHub App that automatically fixes failing CI tests using AI-powered analysis and patch generation.

## Features

- **Automatic CI Test Fixing**: Monitors your repositories and automatically creates fixes for failing tests
- **Multi-tenant Support**: Handles multiple installations securely with rate limiting
- **Health Monitoring**: Comprehensive health endpoints for Fly.io and GitHub Marketplace compliance
- **Persistent Storage**: Installation data stored in mounted volume
- **Rate Limiting**: Prevents abuse with configurable request limits per installation

## Installation

### Option 1: One-Click Install (Recommended)

Visit the [GitHub Marketplace](https://github.com/marketplace/nova-ci-rescue) and click "Install" to add the app to your repositories.

### Option 2: Manual Setup

1. Go to your repository's Settings → Developer settings → GitHub Apps
2. Click "New GitHub App"
3. Configure with the following settings:
   - **Name**: Nova CI-Rescue
   - **Homepage URL**: `https://nova-ci-rescue.fly.dev`
   - **Webhook URL**: `https://nova-ci-rescue.fly.dev/webhooks`
   - **Webhook Secret**: Generate a random secret
   - **Repository permissions**:
     - Repository contents: Read & Write
     - Pull requests: Read & Write
     - Issues: Read & Write
     - Commit statuses: Read & Write
   - **Subscribe to events**: Pull request, Status

## Configuration

Create a `.nova-ci-rescue.yml` file in your repository root:

```yaml
max_iters: 3
timeout: 300
paths:
  include:
    - "**/*.py"
    - "**/*.js"
    - "**/*.ts"
  exclude:
    - "**/node_modules/**"
    - "**/__pycache__/**"
triggers:
  - "ci-failure"
language: "python"
safety:
  max_file_size: 1000000
  allow_network: false
```

## Health Endpoints

- `GET /` - Basic homepage
- `GET /health` - Comprehensive health check with GitHub API testing
- `GET /probe` - Detailed diagnostics for monitoring

## Development

### Local Development

```bash
npm install
npm run dev
```

### Docker

```bash
docker build -t nova-ci-rescue .
docker run -p 8080:8080 nova-ci-rescue
```

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions to Fly.io.

## Support

- [Documentation](https://nova-ci-rescue.fly.dev/docs)
- [Troubleshooting Guide](https://nova-ci-rescue.fly.dev/troubleshooting)
- [GitHub Issues](https://github.com/ci-auto-rescue/ci-auto-rescue/issues)

A GitHub App that automatically fixes failing CI tests using AI-powered analysis and patch generation.

## Features

- **Automatic CI Test Fixing**: Monitors your repositories and automatically creates fixes for failing tests
- **Multi-tenant Support**: Handles multiple installations securely with rate limiting
- **Health Monitoring**: Comprehensive health endpoints for Fly.io and GitHub Marketplace compliance
- **Persistent Storage**: Installation data stored in mounted volume
- **Rate Limiting**: Prevents abuse with configurable request limits per installation

## Installation

### Option 1: One-Click Install (Recommended)

Visit the [GitHub Marketplace](https://github.com/marketplace/nova-ci-rescue) and click "Install" to add the app to your repositories.

### Option 2: Manual Setup

1. Go to your repository's Settings → Developer settings → GitHub Apps
2. Click "New GitHub App"
3. Configure with the following settings:
   - **Name**: Nova CI-Rescue
   - **Homepage URL**: `https://nova-ci-rescue.fly.dev`
   - **Webhook URL**: `https://nova-ci-rescue.fly.dev/webhooks`
   - **Webhook Secret**: Generate a random secret
   - **Repository permissions**:
     - Repository contents: Read & Write
     - Pull requests: Read & Write
     - Issues: Read & Write
     - Commit statuses: Read & Write
   - **Subscribe to events**: Pull request, Status

## Configuration

Create a `.nova-ci-rescue.yml` file in your repository root:

```yaml
max_iters: 3
timeout: 300
paths:
  include:
    - "**/*.py"
    - "**/*.js"
    - "**/*.ts"
  exclude:
    - "**/node_modules/**"
    - "**/__pycache__/**"
triggers:
  - "ci-failure"
language: "python"
safety:
  max_file_size: 1000000
  allow_network: false
```

## Health Endpoints

- `GET /` - Basic homepage
- `GET /health` - Comprehensive health check with GitHub API testing
- `GET /probe` - Detailed diagnostics for monitoring

## Development

### Local Development

```bash
npm install
npm run dev
```

### Docker

```bash
docker build -t nova-ci-rescue .
docker run -p 8080:8080 nova-ci-rescue
```

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions to Fly.io.

## Support

- [Documentation](https://nova-ci-rescue.fly.dev/docs)
- [Troubleshooting Guide](https://nova-ci-rescue.fly.dev/troubleshooting)
- [GitHub Issues](https://github.com/ci-auto-rescue/ci-auto-rescue/issues)

A GitHub App that automatically fixes failing CI tests using AI-powered analysis and patch generation.

## Features

- **Automatic CI Test Fixing**: Monitors your repositories and automatically creates fixes for failing tests
- **Multi-tenant Support**: Handles multiple installations securely with rate limiting
- **Health Monitoring**: Comprehensive health endpoints for Fly.io and GitHub Marketplace compliance
- **Persistent Storage**: Installation data stored in mounted volume
- **Rate Limiting**: Prevents abuse with configurable request limits per installation

## Installation

### Option 1: One-Click Install (Recommended)

Visit the [GitHub Marketplace](https://github.com/marketplace/nova-ci-rescue) and click "Install" to add the app to your repositories.

### Option 2: Manual Setup

1. Go to your repository's Settings → Developer settings → GitHub Apps
2. Click "New GitHub App"
3. Configure with the following settings:
   - **Name**: Nova CI-Rescue
   - **Homepage URL**: `https://nova-ci-rescue.fly.dev`
   - **Webhook URL**: `https://nova-ci-rescue.fly.dev/webhooks`
   - **Webhook Secret**: Generate a random secret
   - **Repository permissions**:
     - Repository contents: Read & Write
     - Pull requests: Read & Write
     - Issues: Read & Write
     - Commit statuses: Read & Write
   - **Subscribe to events**: Pull request, Status

## Configuration

Create a `.nova-ci-rescue.yml` file in your repository root:

```yaml
max_iters: 3
timeout: 300
paths:
  include:
    - "**/*.py"
    - "**/*.js"
    - "**/*.ts"
  exclude:
    - "**/node_modules/**"
    - "**/__pycache__/**"
triggers:
  - "ci-failure"
language: "python"
safety:
  max_file_size: 1000000
  allow_network: false
```

## Health Endpoints

- `GET /` - Basic homepage
- `GET /health` - Comprehensive health check with GitHub API testing
- `GET /probe` - Detailed diagnostics for monitoring

## Development

### Local Development

```bash
npm install
npm run dev
```

### Docker

```bash
docker build -t nova-ci-rescue .
docker run -p 8080:8080 nova-ci-rescue
```

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions to Fly.io.

## Support

- [Documentation](https://nova-ci-rescue.fly.dev/docs)
- [Troubleshooting Guide](https://nova-ci-rescue.fly.dev/troubleshooting)
- [GitHub Issues](https://github.com/ci-auto-rescue/ci-auto-rescue/issues)

A GitHub App that automatically fixes failing CI tests using AI-powered analysis and patch generation.

## Features

- **Automatic CI Test Fixing**: Monitors your repositories and automatically creates fixes for failing tests
- **Multi-tenant Support**: Handles multiple installations securely with rate limiting
- **Health Monitoring**: Comprehensive health endpoints for Fly.io and GitHub Marketplace compliance
- **Persistent Storage**: Installation data stored in mounted volume
- **Rate Limiting**: Prevents abuse with configurable request limits per installation

## Installation

### Option 1: One-Click Install (Recommended)

Visit the [GitHub Marketplace](https://github.com/marketplace/nova-ci-rescue) and click "Install" to add the app to your repositories.

### Option 2: Manual Setup

1. Go to your repository's Settings → Developer settings → GitHub Apps
2. Click "New GitHub App"
3. Configure with the following settings:
   - **Name**: Nova CI-Rescue
   - **Homepage URL**: `https://nova-ci-rescue.fly.dev`
   - **Webhook URL**: `https://nova-ci-rescue.fly.dev/webhooks`
   - **Webhook Secret**: Generate a random secret
   - **Repository permissions**:
     - Repository contents: Read & Write
     - Pull requests: Read & Write
     - Issues: Read & Write
     - Commit statuses: Read & Write
   - **Subscribe to events**: Pull request, Status

## Configuration

Create a `.nova-ci-rescue.yml` file in your repository root:

```yaml
max_iters: 3
timeout: 300
paths:
  include:
    - "**/*.py"
    - "**/*.js"
    - "**/*.ts"
  exclude:
    - "**/node_modules/**"
    - "**/__pycache__/**"
triggers:
  - "ci-failure"
language: "python"
safety:
  max_file_size: 1000000
  allow_network: false
```

## Health Endpoints

- `GET /` - Basic homepage
- `GET /health` - Comprehensive health check with GitHub API testing
- `GET /probe` - Detailed diagnostics for monitoring

## Development

### Local Development

```bash
npm install
npm run dev
```

### Docker

```bash
docker build -t nova-ci-rescue .
docker run -p 8080:8080 nova-ci-rescue
```

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions to Fly.io.

## Support

- [Documentation](https://nova-ci-rescue.fly.dev/docs)
- [Troubleshooting Guide](https://nova-ci-rescue.fly.dev/troubleshooting)
- [GitHub Issues](https://github.com/ci-auto-rescue/ci-auto-rescue/issues)

A GitHub App that automatically fixes failing CI tests using AI-powered analysis and patch generation.

## Features

- **Automatic CI Test Fixing**: Monitors your repositories and automatically creates fixes for failing tests
- **Multi-tenant Support**: Handles multiple installations securely with rate limiting
- **Health Monitoring**: Comprehensive health endpoints for Fly.io and GitHub Marketplace compliance
- **Persistent Storage**: Installation data stored in mounted volume
- **Rate Limiting**: Prevents abuse with configurable request limits per installation

## Installation

### Option 1: One-Click Install (Recommended)

Visit the [GitHub Marketplace](https://github.com/marketplace/nova-ci-rescue) and click "Install" to add the app to your repositories.

### Option 2: Manual Setup

1. Go to your repository's Settings → Developer settings → GitHub Apps
2. Click "New GitHub App"
3. Configure with the following settings:
   - **Name**: Nova CI-Rescue
   - **Homepage URL**: `https://nova-ci-rescue.fly.dev`
   - **Webhook URL**: `https://nova-ci-rescue.fly.dev/webhooks`
   - **Webhook Secret**: Generate a random secret
   - **Repository permissions**:
     - Repository contents: Read & Write
     - Pull requests: Read & Write
     - Issues: Read & Write
     - Commit statuses: Read & Write
   - **Subscribe to events**: Pull request, Status

## Configuration

Create a `.nova-ci-rescue.yml` file in your repository root:

```yaml
max_iters: 3
timeout: 300
paths:
  include:
    - "**/*.py"
    - "**/*.js"
    - "**/*.ts"
  exclude:
    - "**/node_modules/**"
    - "**/__pycache__/**"
triggers:
  - "ci-failure"
language: "python"
safety:
  max_file_size: 1000000
  allow_network: false
```

## Health Endpoints

- `GET /` - Basic homepage
- `GET /health` - Comprehensive health check with GitHub API testing
- `GET /probe` - Detailed diagnostics for monitoring

## Development

### Local Development

```bash
npm install
npm run dev
```

### Docker

```bash
docker build -t nova-ci-rescue .
docker run -p 8080:8080 nova-ci-rescue
```

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions to Fly.io.

## Support

- [Documentation](https://nova-ci-rescue.fly.dev/docs)
- [Troubleshooting Guide](https://nova-ci-rescue.fly.dev/troubleshooting)
- [GitHub Issues](https://github.com/ci-auto-rescue/ci-auto-rescue/issues)
