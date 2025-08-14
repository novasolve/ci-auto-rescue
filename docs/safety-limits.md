# Nova CI-Rescue Safety Limits

## Overview

Nova CI-Rescue includes built-in safety limits to prevent potentially dangerous auto-modifications from being applied to your codebase. These limits ensure that automated fixes remain within safe boundaries and that critical files require manual review.

## Safety Limits

### Default Limits

| Limit              | Default Value | Description                                                    |
| ------------------ | ------------- | -------------------------------------------------------------- |
| Max Lines Changed  | 200           | Maximum total lines that can be added or removed               |
| Max Files Modified | 10            | Maximum number of files that can be modified in a single patch |

### Restricted Paths

The following paths are automatically blocked from modification:

#### CI/CD Configuration

- `.github/workflows/*` - GitHub Actions workflows
- `.gitlab-ci.yml` - GitLab CI configuration
- `.travis.yml` - Travis CI configuration
- `.circleci/*` - CircleCI configuration
- `Jenkinsfile` - Jenkins pipeline
- `azure-pipelines.yml` - Azure DevOps pipelines
- `bitbucket-pipelines.yml` - Bitbucket pipelines
- `.buildkite/*` - Buildkite configuration

#### Deployment & Infrastructure

- `deploy/*` - Deployment configurations
- `deployment/*` - Deployment scripts
- `k8s/*`, `kubernetes/*` - Kubernetes manifests
- `helm/*` - Helm charts
- `terraform/*` - Terraform configurations
- `ansible/*` - Ansible playbooks
- `docker-compose*.yml` - Docker Compose files
- `Dockerfile*` - Docker images

#### Security-Sensitive Files

- `**/secrets/*` - Secret storage directories
- `**/credentials/*` - Credential files
- `**/.env*` - Environment configuration files
- `**/config/prod*` - Production configurations
- `**/*.pem`, `**/*.key`, `**/*.crt` - Certificates and keys
- `**/*.p12`, `**/*.pfx` - Certificate stores

#### Package Management

- `package-lock.json` - NPM lock file
- `yarn.lock` - Yarn lock file
- `Gemfile.lock` - Ruby Bundler lock file
- `poetry.lock` - Poetry lock file
- `Pipfile.lock` - Pipenv lock file
- `go.sum` - Go modules checksum
- `composer.lock` - PHP Composer lock file
- `Cargo.lock` - Rust Cargo lock file

#### Other Protected Files

- Version files (`VERSION`, `version.txt`)
- Changelog files (`CHANGELOG.md`, `RELEASES.md`)
- Database migrations (`**/migrations/*`, `**/db/migrate/*`)
- Build artifacts (`dist/*`, `build/*`, `*.whl`, `*.jar`)
- Git configuration (`.git/*`, `.gitignore`, `.gitmodules`)

## Usage

### Command Line

When running Nova CI-Rescue, safety checks are automatically applied:

```bash
# Safety checks are enabled by default
nova fix /path/to/repo

# The patch will be rejected if it violates limits
# You'll see a clear error message explaining why
```

### Programmatic Usage

```python
from nova.tools.safety_limits import SafetyLimits, SafetyConfig

# Use default configuration
safety = SafetyLimits()

# Or customize limits
config = SafetyConfig(
    max_lines_changed=100,  # Stricter line limit
    max_files_modified=5,    # Stricter file limit
    denied_paths=["custom/*"]  # Additional restricted paths
)
safety = SafetyLimits(config=config)

# Validate a patch
is_safe, violations = safety.validate_patch(patch_text)
if not is_safe:
    print(f"Patch rejected: {violations}")
```

### GitHub Actions Integration

Add the Nova safety check to your CI pipeline:

```yaml
name: PR Safety Check

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  safety-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Nova Safety Check
        uses: nova-ci-rescue/safety-check@v1
        with:
          max_lines: 200
          max_files: 10
```

## Configuration

### Environment Variables

You can override default limits using environment variables:

```bash
export NOVA_MAX_LINES_CHANGED=100
export NOVA_MAX_FILES_MODIFIED=5
export NOVA_DENIED_PATHS="custom/*,internal/*"
```

### Configuration File

Create a `.nova-safety.yml` file in your repository root:

```yaml
# .nova-safety.yml
limits:
  max_lines_changed: 150
  max_files_modified: 8

denied_paths:
  - "internal/*"
  - "config/production/*"
  - "*.prod.yml"

denied_patterns:
  - ".*\\.min\\.js$" # Minified JavaScript
  - ".*\\.min\\.css$" # Minified CSS
```

## Error Messages

When a patch violates safety limits, you'll see clear error messages:

### Example: Line Limit Exceeded

```
🛡️ Safety Check Failed

The proposed patch violates safety limits and cannot be automatically applied:

1. Exceeds maximum lines changed: 350 > 200

Why these limits?
These safety limits help prevent:
• Accidental breaking changes to critical infrastructure
• Unintended modifications to security-sensitive files
• Large-scale changes that should undergo manual review

What to do next?
• Review the patch manually to ensure changes are safe
• Consider breaking large changes into smaller, focused patches
```

### Example: Restricted File

```
🛡️ Safety Check Failed

The proposed patch violates safety limits and cannot be automatically applied:

1. Attempts to modify restricted files: .github/workflows/deploy.yml

Why these limits?
These safety limits help prevent:
• Accidental breaking changes to critical infrastructure
• Unintended modifications to security-sensitive files

What to do next?
• For CI/CD or deployment changes, follow your organization's change management process
• Apply these changes manually after proper review
```

## Testing Safety Limits

Run the demonstration script to see safety limits in action:

```bash
python demo_safety_limits.py
```

Run the test suite:

```bash
pytest tests/test_safety_limits.py -v
```

## Best Practices

1. **Start with default limits** - The defaults (200 lines, 10 files) work well for most projects

2. **Customize for your needs** - Adjust limits based on your team's comfort level

3. **Add project-specific restrictions** - Protect critical paths unique to your architecture

4. **Review rejected patches** - Patches that violate limits may still be valid; apply manually after review

5. **Use in CI/CD** - Integrate safety checks into your PR workflow for additional protection

6. **Monitor and adjust** - Track how often limits are hit and adjust if needed

## Troubleshooting

### Q: A legitimate fix is being rejected. What should I do?

**A:** You have several options:

1. Apply the patch manually after review
2. Break the change into smaller patches
3. Temporarily increase limits for this specific case
4. Add an exception for specific files if appropriate

### Q: Can I disable safety checks entirely?

**A:** Yes, but it's not recommended. If absolutely necessary:

```python
# In code
result = apply_patch(state, patch_text, skip_safety_check=True)
```

### Q: How do I allow modifications to a normally restricted file?

**A:** Create a custom configuration that excludes that specific path:

```python
config = SafetyConfig(
    denied_paths=[p for p in SafetyConfig().denied_paths
                  if not p.startswith("specific/path")]
)
```

## Security Considerations

- Safety limits are a defense-in-depth measure, not a complete security solution
- Always review patches before deploying to production
- Consider additional controls for sensitive environments
- Regularly audit and update your denied paths list

## Support

For issues or questions about safety limits:

- Open an issue on GitHub
- Check the documentation at docs/safety-limits.md
- Run `nova config` to verify your configuration
