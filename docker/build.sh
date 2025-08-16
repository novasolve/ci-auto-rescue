#!/bin/bash
# Build script for the Nova CI-Rescue sandbox Docker image

set -e

echo "Building Nova CI-Rescue sandbox Docker image..."

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Build the Docker image
docker build -t nova-ci-rescue-sandbox:latest "$SCRIPT_DIR"

echo "✅ Successfully built nova-ci-rescue-sandbox:latest image"
echo ""
echo "To test the sandbox, run:"
echo "  docker run --rm nova-ci-rescue-sandbox:latest --help"
echo ""
echo "To run tests in a project:"
echo "  docker run --rm -v \$(pwd):/workspace:ro -v \$(pwd)/.nova:/workspace/.nova:rw nova-ci-rescue-sandbox:latest --pytest"
