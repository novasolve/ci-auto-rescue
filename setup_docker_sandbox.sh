#!/bin/bash
# Setup script for Nova CI-Rescue Docker sandbox

set -e

echo "🚀 Nova CI-Rescue Docker Sandbox Setup"
echo "====================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first:"
    echo "   - macOS: https://docs.docker.com/desktop/mac/install/"
    echo "   - Linux: https://docs.docker.com/engine/install/"
    echo "   - Windows: https://docs.docker.com/desktop/windows/install/"
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo "❌ Docker daemon is not running."
    echo "   - macOS: Start Docker Desktop from Applications"
    echo "   - Linux: Run 'sudo systemctl start docker'"
    echo "   - Windows: Start Docker Desktop"
    exit 1
fi

echo "✅ Docker is installed and running"

# Check if image already exists
if docker images | grep -q "nova-ci-rescue-sandbox"; then
    echo "🔍 Docker image 'nova-ci-rescue-sandbox:latest' already exists"
    read -p "Do you want to rebuild it? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "✅ Using existing image"
        exit 0
    fi
fi

# Build the Docker image
echo "🔨 Building Docker image..."
cd "$(dirname "$0")/docker"
./build.sh

echo ""
echo "✅ Setup complete! Nova will now use Docker sandbox for test execution."
echo ""
echo "Test it with:"
echo "  nova fix examples/demos/demo_broken_project/"
