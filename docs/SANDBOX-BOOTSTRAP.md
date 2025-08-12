# Daytona Sandbox — Bootstrap & Troubleshooting

Nova expects a minimal toolchain. First run executes an **idempotent** bootstrap.

## One-liner (runs as root inside sandbox)
```bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y git tree ripgrep ca-certificates curl unzip tar less openssh-client xauth
update-ca-certificates || true
git config --global http.sslCAInfo /etc/ssl/certs/ca-certificates.crt
git --version && tree --version && rg --version && curl --version
```

## Common issues
1) git: not found, tree: not found

Cause: fresh Ubuntu image without base tools.

Fix: run the one-liner above (Nova will do this automatically on first contact).

2) TLS error pushing to GitHub

"tls: failed to verify certificate: x509: certificate signed by unknown authority"

Ensure ca-certificates installed and update-ca-certificates ran.

Pin CA file for git:

```bash
git config --global http.sslCAInfo /etc/ssl/certs/ca-certificates.crt
```

3) Missing Python/Node for test runs

Nova only installs base tools. Language runtimes come from the repo’s own setup (lockfiles, venv, etc.). Add a project-local setup script or GH Action to build the env.

## Snapshots & Volumes
- Snapshots: create a clean Ubuntu snapshot (e.g. ubuntu:22.04) and let bootstrap handle tools; don’t bake language runtimes unless needed.
- Volumes: optional; good for large caches (pip/poetry/npm). Not required for correctness.

## Health check script (Nova calls this)
```bash
command -v git && command -v rg && command -v tree && command -v curl
```
