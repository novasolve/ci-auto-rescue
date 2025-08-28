# Publishing to GitHub Packages

This guide explains how to publish `nova-ci-rescue` to GitHub Packages.

## Quick Start

### Automatic Publishing (via GitHub Actions)

1. Create a new release on GitHub
2. The workflow will automatically build and publish to both PyPI and GitHub Packages

### Manual Publishing

1. Build the package:

   ```bash
   ./scripts/build_package.sh
   ```

2. Set up authentication:

   ```bash
   export GITHUB_TOKEN=your_github_personal_access_token
   ```

3. Upload to GitHub Packages:
   ```bash
   python -m twine upload \
     --repository-url https://maven.pkg.github.com/novasolve/ci-auto-rescue \
     --username YOUR_GITHUB_USERNAME \
     --password $GITHUB_TOKEN \
     dist/*
   ```

## Installing from GitHub Packages

To install `nova-ci-rescue` from GitHub Packages:

```bash
# First, authenticate with GitHub Packages
echo "//npm.pkg.github.com/:_authToken=$GITHUB_TOKEN" >> ~/.npmrc

# Install the package
pip install nova-ci-rescue \
  --index-url https://pypi.org/simple \
  --extra-index-url https://maven.pkg.github.com/novasolve/ci-auto-rescue
```

## Notes

- GitHub Packages for Python is not as mature as PyPI
- The package will still be primarily distributed via PyPI
- GitHub Packages can serve as a backup or for private/pre-release versions
- You need a GitHub Personal Access Token with `write:packages` scope

## Troubleshooting

If you see "GitHub Packages upload failed", this is expected. GitHub Packages has limited Python support compared to npm/Maven packages.

For the best experience, continue using PyPI as the primary distribution channel:

```bash
pip install nova-ci-rescue
```
