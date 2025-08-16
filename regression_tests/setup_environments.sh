#!/bin/bash
# Setup script for Nova CI-Rescue regression test environments
# Creates isolated environments for v1.0 and v1.1

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="${SCRIPT_DIR}"
VENV_DIR="${BASE_DIR}/venvs"
REQUIREMENTS_DIR="${BASE_DIR}/requirements"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Nova CI-Rescue Regression Test Environment Setup${NC}"
echo "=================================================="

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | grep -Po '(?<=Python )\d+\.\d+')
echo "Python version: $PYTHON_VERSION"

if [ $(echo "$PYTHON_VERSION < 3.8" | bc) -eq 1 ]; then
    echo -e "${RED}Error: Python 3.8+ required${NC}"
    exit 1
fi

# Create directories
echo -e "\n${YELLOW}Creating directory structure...${NC}"
mkdir -p "$VENV_DIR"
mkdir -p "$REQUIREMENTS_DIR"
mkdir -p "${BASE_DIR}/test_repos"
mkdir -p "${BASE_DIR}/regression_results"

# Function to setup a Nova environment
setup_nova_env() {
    local VERSION=$1
    local VENV_NAME=$2
    local REQUIREMENTS_FILE=$3
    local NOVA_SOURCE=$4
    
    echo -e "\n${YELLOW}Setting up Nova ${VERSION} environment...${NC}"
    
    # Create virtual environment
    if [ -d "${VENV_DIR}/${VENV_NAME}" ]; then
        echo "Virtual environment ${VENV_NAME} already exists, removing..."
        rm -rf "${VENV_DIR}/${VENV_NAME}"
    fi
    
    echo "Creating virtual environment: ${VENV_NAME}"
    python3 -m venv "${VENV_DIR}/${VENV_NAME}"
    
    # Activate virtual environment
    source "${VENV_DIR}/${VENV_NAME}/bin/activate"
    
    # Upgrade pip
    echo "Upgrading pip..."
    pip install --upgrade pip setuptools wheel >/dev/null 2>&1
    
    # Install requirements
    if [ -f "$REQUIREMENTS_FILE" ]; then
        echo "Installing from requirements file: $REQUIREMENTS_FILE"
        pip install -r "$REQUIREMENTS_FILE" >/dev/null 2>&1
    else
        echo "Requirements file not found, installing base dependencies..."
        # Install base dependencies
        pip install pytest pytest-timeout pytest-json-report >/dev/null 2>&1
        pip install pyyaml matplotlib numpy >/dev/null 2>&1
        pip install openai anthropic >/dev/null 2>&1
    fi
    
    # Install Nova from source if provided
    if [ -n "$NOVA_SOURCE" ] && [ -d "$NOVA_SOURCE" ]; then
        echo "Installing Nova from source: $NOVA_SOURCE"
        pip install -e "$NOVA_SOURCE" >/dev/null 2>&1
    elif [ "$VERSION" == "v1.0" ]; then
        # Try to install v1.0 from release
        echo "Installing Nova v1.0 from release..."
        if [ -d "${SCRIPT_DIR}/../releases/v0.1.0-alpha" ]; then
            pip install -e "${SCRIPT_DIR}/../releases/v0.1.0-alpha" >/dev/null 2>&1
        else
            echo -e "${YELLOW}Warning: Nova v1.0 source not found${NC}"
        fi
    elif [ "$VERSION" == "v1.1" ]; then
        # Install current version (v1.1 with Deep Agent)
        echo "Installing Nova v1.1 from current source..."
        if [ -d "${SCRIPT_DIR}/../src" ]; then
            pip install -e "${SCRIPT_DIR}/.." >/dev/null 2>&1
        else
            echo -e "${YELLOW}Warning: Nova v1.1 source not found${NC}"
        fi
    fi
    
    # Create wrapper script
    WRAPPER_SCRIPT="${BASE_DIR}/nova_${VERSION}"
    echo "Creating wrapper script: $WRAPPER_SCRIPT"
    
    cat > "$WRAPPER_SCRIPT" << EOF
#!/bin/bash
# Wrapper script for Nova ${VERSION}
source "${VENV_DIR}/${VENV_NAME}/bin/activate"
export NOVA_VERSION="${VERSION}"
export NOVA_LOG_LEVEL="INFO"

# Set Deep Agent flag for v1.1
if [ "${VERSION}" == "v1.1" ]; then
    export NOVA_USE_DEEP_AGENT="true"
fi

# Execute Nova
if [ "${VERSION}" == "v1.0" ]; then
    # Use legacy CLI path
    python -m nova.cli "\$@"
else
    # Use current CLI path
    python -m nova "\$@"
fi
EOF
    
    chmod +x "$WRAPPER_SCRIPT"
    
    deactivate
    echo -e "${GREEN}✓ Nova ${VERSION} environment setup complete${NC}"
}

# Create requirements files if they don't exist
create_requirements() {
    echo -e "\n${YELLOW}Creating requirements files...${NC}"
    
    # v1.0 requirements
    cat > "${REQUIREMENTS_DIR}/nova_v1_0.txt" << 'EOF'
# Nova v1.0 (Legacy) Requirements
pytest>=7.0.0
pytest-timeout>=2.1.0
pytest-json-report>=1.5.0
pyyaml>=6.0
gitpython>=3.1.0
click>=8.0.0
rich>=13.0.0
openai>=1.0.0
anthropic>=0.5.0
tenacity>=8.0.0
jsonschema>=4.0.0
EOF
    
    # v1.1 requirements
    cat > "${REQUIREMENTS_DIR}/nova_v1_1.txt" << 'EOF'
# Nova v1.1 (Deep Agent) Requirements
pytest>=7.0.0
pytest-timeout>=2.1.0
pytest-json-report>=1.5.0
pyyaml>=6.0
gitpython>=3.1.0
click>=8.0.0
rich>=13.0.0
openai>=1.0.0
anthropic>=0.5.0
tenacity>=8.0.0
jsonschema>=4.0.0
pydantic>=2.0.0
langchain>=0.1.0
langchain-openai>=0.0.5
langchain-anthropic>=0.1.0
EOF
    
    echo -e "${GREEN}✓ Requirements files created${NC}"
}

# Setup v1.0 environment
create_requirements
setup_nova_env "v1_0" "nova_v1_0" "${REQUIREMENTS_DIR}/nova_v1_0.txt" ""

# Setup v1.1 environment
setup_nova_env "v1_1" "nova_v1_1" "${REQUIREMENTS_DIR}/nova_v1_1.txt" ""

# Create test data generator script
echo -e "\n${YELLOW}Creating test data generator...${NC}"
cat > "${BASE_DIR}/generate_test_data.py" << 'EOF'
#!/usr/bin/env python3
"""Generate test repositories for regression testing"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from edge_case_generator import EdgeCaseGenerator

if __name__ == "__main__":
    generator = EdgeCaseGenerator()
    generator.generate_all_edge_cases()
EOF

chmod +x "${BASE_DIR}/generate_test_data.py"

# Generate test repositories
echo -e "\n${YELLOW}Generating test repositories...${NC}"
python3 "${BASE_DIR}/generate_test_data.py"

# Create run script
echo -e "\n${YELLOW}Creating run script...${NC}"
cat > "${BASE_DIR}/run_regression_tests.sh" << 'EOF'
#!/bin/bash
# Run Nova CI-Rescue regression tests

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if config file exists
CONFIG_FILE="${1:-${SCRIPT_DIR}/test_repos.yaml}"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Configuration file not found: $CONFIG_FILE"
    echo "Usage: $0 [config_file]"
    exit 1
fi

# Run regression tests
echo "Starting regression tests with config: $CONFIG_FILE"
python3 "${SCRIPT_DIR}/regression_orchestrator.py" "$CONFIG_FILE" \
    --output "${SCRIPT_DIR}/regression_results" \
    --verbose

# Check exit code
if [ $? -eq 0 ]; then
    echo -e "\033[0;32m✓ Regression tests completed successfully\033[0m"
    echo "Results available in: ${SCRIPT_DIR}/regression_results/"
else
    echo -e "\033[0;31m✗ Regression tests failed or found regressions\033[0m"
    echo "Check results in: ${SCRIPT_DIR}/regression_results/"
    exit 1
fi
EOF

chmod +x "${BASE_DIR}/run_regression_tests.sh"

# Final summary
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Environment Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Created:"
echo "  - Virtual environments in: ${VENV_DIR}/"
echo "  - Wrapper scripts:"
echo "    - ${BASE_DIR}/nova_v1_0 (for v1.0 legacy)"
echo "    - ${BASE_DIR}/nova_v1_1 (for v1.1 Deep Agent)"
echo "  - Test repositories in: ${BASE_DIR}/test_repos/"
echo "  - Run script: ${BASE_DIR}/run_regression_tests.sh"
echo ""
echo "To run regression tests:"
echo "  ${BASE_DIR}/run_regression_tests.sh"
echo ""
echo "To run tests with custom config:"
echo "  ${BASE_DIR}/run_regression_tests.sh /path/to/config.yaml"
echo ""
echo -e "${YELLOW}Note: Make sure to set OPENAI_API_KEY or other LLM API keys before running tests${NC}"
