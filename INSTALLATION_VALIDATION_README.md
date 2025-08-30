
# Nova CI-Rescue Installation Validation

## New Features Added

### 1. Installation Validation Endpoint
- **URL**: `/health/installation`
- **Purpose**: Comprehensive validation of Nova CI-Rescue installation
- **Validates**:
  - GitHub App authentication
  - Installation permissions (contents, pull_requests, issues)
  - Repository access capabilities
  - Webhook and event handling setup
  - End-to-end functionality

### 2. CLI Validation Command
- **Command**: `nova validate-installation [--url BASE_URL]`
- **Purpose**: Test installation from command line
- **Features**:
  - Connects to health endpoint
  - Displays detailed validation results
  - Provides actionable recommendations
  - Works with custom base URLs

### 3. Enhanced Health Monitoring
- **Updated**: Root page includes link to installation validation
- **Status Levels**:
  - ✅ **Healthy**: Fully validated and operational
  - ⚠️ **Degraded**: Working but with some issues
  - ❌ **Unhealthy**: Critical issues need attention

## Usage Examples

### Web Interface
1. Start the GitHub App: `npm start`
2. Visit: `http://localhost:3000/health/installation`
3. Check overall status and detailed validation results

### CLI Interface
```bash
# Test local installation
nova validate-installation

# Test remote installation
nova validate-installation --url https://your-app.fly.dev
```

### API Usage
```bash
curl http://localhost:3000/health/installation
```

## Validation Checks

1. **Installation Validation**
   - App authentication status
   - Required permissions check
   - Installation count verification

2. **One-Click Path Validation**
   - Repository access testing
   - Account information validation
   - Access token functionality

3. **End-to-End Capability Test**
   - Webhook handling verification
   - Event processing validation
   - Application logging check

This provides a comprehensive one-click validation path for ensuring Nova CI-Rescue is properly installed and fully operational!

