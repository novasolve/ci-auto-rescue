#!/bin/bash

# Nova CI-Rescue Full End-to-End Smoke Test
# This script sets up everything automatically and runs a complete test

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
GITHUB_APP_PORT=3000
TEST_REPO_PATH="./test-end-to-end-repo"
NOVA_CLI_PATH="./src"

echo -e "${BLUE}🚀 Nova CI-Rescue Full End-to-End Smoke Test${NC}"
echo "==============================================="
echo ""

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${RED}❌ Port $port is already in use${NC}"
        return 1
    else
        echo -e "${GREEN}✅ Port $port is available${NC}"
        return 0
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local max_attempts=30
    local attempt=1
    
    echo -e "${YELLOW}⏳ Waiting for service at $url...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s --max-time 5 "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Service is ready!${NC}"
            return 0
        fi
        echo "Attempt $attempt/$max_attempts..."
        sleep 2
        ((attempt++))
    done
    
    echo -e "${RED}❌ Service failed to start within expected time${NC}"
    return 1
}

# Function to run tests
run_tests() {
    local test_path=$1
    echo -e "${BLUE}🧪 Running tests in $test_path${NC}"
    
    if [ -d "$test_path" ]; then
        cd "$test_path"
        
        # Install dependencies
        echo -e "${YELLOW}📦 Installing test dependencies...${NC}"
        pip install -e . > /dev/null 2>&1 || {
            echo -e "${RED}❌ Failed to install dependencies${NC}"
            return 1
        }
        
        # Run initial tests (expect failures)
        echo -e "${YELLOW}🧪 Running initial tests (expecting failures)...${NC}"
        python -m pytest --tb=short --maxfail=5 2>/dev/null || {
            echo -e "${GREEN}✅ Tests failed as expected (this is normal for the test repo)${NC}"
        }
        
        cd ..
        return 0
    else
        echo -e "${RED}❌ Test repository not found at $test_path${NC}"
        return 1
    fi
}

# Function to validate Nova CLI
validate_nova_cli() {
    echo -e "${BLUE}🔧 Validating Nova CLI...${NC}"
    
    if [ -d "$NOVA_CLI_PATH" ]; then
        # Check if CLI can be imported
        python -c "
import sys
sys.path.insert(0, '$NOVA_CLI_PATH')
try:
    from nova.cli import app
    print('✅ Nova CLI loaded successfully')
except Exception as e:
    print(f'❌ Failed to load Nova CLI: {e}')
    exit(1)
"
        return $?
    else
        echo -e "${RED}❌ Nova CLI path not found at $NOVA_CLI_PATH${NC}"
        return 1
    fi
}

# Function to run Nova validation
run_nova_validation() {
    echo -e "${BLUE}🔍 Running Nova installation validation...${NC}"
    
    if [ -d "$NOVA_CLI_PATH" ]; then
        python -c "
import sys
sys.path.insert(0, '$NOVA_CLI_PATH')
from nova.cli import validate_installation
try:
    validate_installation('http://localhost:$GITHUB_APP_PORT')
    print('✅ Nova validation completed')
except Exception as e:
    print(f'⚠️  Nova validation failed (expected if GitHub App not running): {e}')
"
        return 0  # Don't fail if validation fails - it's expected without the app
    fi
}

# Function to show summary
show_summary() {
    echo ""
    echo -e "${GREEN}🎉 Smoke Test Summary${NC}"
    echo "======================"
    echo ""
    echo -e "${GREEN}✅ Environment setup${NC}"
    echo -e "${GREEN}✅ Port availability checked${NC}"
    echo -e "${GREEN}✅ Test repository validation${NC}"
    echo -e "${GREEN}✅ Nova CLI validation${NC}"
    echo -e "${GREEN}✅ Test execution${NC}"
    echo ""
    echo -e "${BLUE}📋 Next Steps:${NC}"
    echo "1. Start GitHub App: cd github-app && npm start"
    echo "2. Run validation: python -c 'from src.nova.cli import validate_installation; validate_installation()'"
    echo "3. Test Nova CI-Rescue: nova fix $TEST_REPO_PATH"
    echo ""
    echo -e "${YELLOW}💡 The test repository contains intentional bugs that Nova CI-Rescue will fix!${NC}"
    echo ""
}

# Main execution
echo -e "${YELLOW}🔧 Step 1: Checking environment...${NC}"

# Check if required tools are available
command -v node >/dev/null 2>&1 || { echo -e "${RED}❌ Node.js is not installed${NC}"; exit 1; }
command -v python >/dev/null 2>&1 || { echo -e "${RED}❌ Python is not installed${NC}"; exit 1; }
command -v pip >/dev/null 2>&1 || { echo -e "${RED}❌ pip is not installed${NC}"; exit 1; }

echo -e "${GREEN}✅ Required tools are available${NC}"

# Check port availability
check_port $GITHUB_APP_PORT

echo ""
echo -e "${YELLOW}🔧 Step 2: Validating test repository...${NC}"

# Check if test repository exists
if [ -d "$TEST_REPO_PATH" ]; then
    echo -e "${GREEN}✅ Test repository found${NC}"
    
    # Validate repository structure
    if [ -f "$TEST_REPO_PATH/pyproject.toml" ] && [ -f "$TEST_REPO_PATH/requirements.txt" ]; then
        echo -e "${GREEN}✅ Repository structure is valid${NC}"
    else
        echo -e "${RED}❌ Repository structure is invalid${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ Test repository not found at $TEST_REPO_PATH${NC}"
    echo -e "${YELLOW}💡 Run this script from the nova-ci-rescue root directory${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}🔧 Step 3: Validating Nova CLI...${NC}"
validate_nova_cli

echo ""
echo -e "${YELLOW}🔧 Step 4: Running test suite...${NC}"
run_tests "$TEST_REPO_PATH"

echo ""
echo -e "${YELLOW}🔧 Step 5: Testing Nova validation...${NC}"
run_nova_validation

echo ""
echo -e "${YELLOW}🔧 Step 6: Preparing for GitHub App startup...${NC}"

# Check if GitHub App directory exists
if [ -d "github-app" ]; then
    echo -e "${GREEN}✅ GitHub App directory found${NC}"
    
    # Check if package.json exists
    if [ -f "github-app/package.json" ]; then
        echo -e "${GREEN}✅ GitHub App package.json found${NC}"
        echo -e "${BLUE}💡 To start the GitHub App, run: cd github-app && npm start${NC}"
    else
        echo -e "${RED}❌ GitHub App package.json not found${NC}"
    fi
else
    echo -e "${RED}❌ GitHub App directory not found${NC}"
fi

# Show final summary
show_summary

echo ""
echo -e "${GREEN}🎯 Smoke test completed successfully!${NC}"
echo -e "${BLUE}Press Enter to continue...${NC}"
read -r

echo -e "${YELLOW}🚀 Starting GitHub App (if available)...${NC}"

# Try to start GitHub App if possible
if [ -d "github-app" ] && [ -f "github-app/package.json" ]; then
    echo -e "${BLUE}Starting GitHub App on port $GITHUB_APP_PORT...${NC}"
    echo -e "${YELLOW}This will run in the background. Press Ctrl+C to stop.${NC}"
    echo ""
    
    cd github-app
    
    # Start the app in background
    npm start &
    APP_PID=$!
    
    # Wait for it to start
    wait_for_service "http://localhost:$GITHUB_APP_PORT/health"
    
    echo ""
    echo -e "${GREEN}🎉 GitHub App is running!${NC}"
    echo -e "${BLUE}🌐 Health Check: http://localhost:$GITHUB_APP_PORT/health${NC}"
    echo -e "${BLUE}🔍 Installation Validation: http://localhost:$GITHUB_APP_PORT/health/installation${NC}"
    echo ""
    echo -e "${YELLOW}💡 Test the validation by running:${NC}"
    echo -e "${BLUE}   python -c 'from src.nova.cli import validate_installation; validate_installation()'"
    echo ""
    echo -e "${YELLOW}Press Enter to stop the GitHub App and exit...${NC}"
    read -r
    
    # Stop the app
    kill $APP_PID 2>/dev/null || true
    echo -e "${GREEN}✅ GitHub App stopped${NC}"
else
    echo -e "${YELLOW}⚠️  GitHub App not available for automatic startup${NC}"
    echo -e "${BLUE}💡 To start manually: cd github-app && npm start${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Smoke test fully completed!${NC}"
echo -e "${BLUE}The environment is ready for Nova CI-Rescue end-to-end testing.${NC}"
