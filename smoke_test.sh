#!/bin/bash

# Nova CI-Rescue Smoke Test Script
# Tests the deployed GitHub App on Fly.io

set -e

APP_URL="https://nova-ci-rescue.fly.dev"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🚀 Starting Nova CI-Rescue smoke tests..."
echo "📍 Testing app at: $APP_URL"
echo

# Function to test endpoint
test_endpoint() {
    local url="$1"
    local expected_status="${2:-200}"
    local description="$3"

    echo -n "Testing $description ($url)... "

    if response=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null); then
        status_code=$(echo "$response" | tail -n1)
        body=$(echo "$response" | head -n -1)

        if [ "$status_code" -eq "$expected_status" ]; then
            echo -e "${GREEN}✅ PASS${NC} (Status: $status_code)"

            # Special handling for health endpoint
            if [[ "$url" == *"/health" ]]; then
                # Check if response contains expected fields
                if echo "$body" | grep -q '"status"'; then
                    echo "   📊 Health check response validated"
                else
                    echo -e "   ${YELLOW}⚠️  Warning: Health response may be malformed${NC}"
                fi
            fi
        else
            echo -e "${RED}❌ FAIL${NC} (Status: $status_code, Expected: $expected_status)"
            echo "   Response: $body"
            return 1
        fi
    else
        echo -e "${RED}❌ FAIL${NC} (Connection failed)"
        return 1
    fi
}

# Track test results
PASSED=0
FAILED=0

# Test homepage
if test_endpoint "$APP_URL/" 200 "Homepage"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Test health endpoint
if test_endpoint "$APP_URL/health" 200 "Health Check"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Test probe endpoint (may not exist yet)
if test_endpoint "$APP_URL/probe" 200 "Probe Endpoint"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Test non-existent endpoint (should return 404)
if test_endpoint "$APP_URL/nonexistent" 404 "404 Handling"; then
    ((PASSED++))
else
    ((FAILED++))
fi

echo
echo "📊 Test Results:"
echo "   ✅ Passed: $PASSED"
echo "   ❌ Failed: $FAILED"
echo "   📈 Total: $((PASSED + FAILED))"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All smoke tests passed!${NC}"
    exit 0
else
    echo -e "${RED}💥 Some tests failed. Check the output above.${NC}"
    exit 1
fi
# Nova CI-Rescue Smoke Test Script
# Tests the deployed GitHub App on Fly.io

set -e

APP_URL="https://nova-ci-rescue.fly.dev"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🚀 Starting Nova CI-Rescue smoke tests..."
echo "📍 Testing app at: $APP_URL"
echo

# Function to test endpoint
test_endpoint() {
    local url="$1"
    local expected_status="${2:-200}"
    local description="$3"

    echo -n "Testing $description ($url)... "

    if response=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null); then
        status_code=$(echo "$response" | tail -n1)
        body=$(echo "$response" | head -n -1)

        if [ "$status_code" -eq "$expected_status" ]; then
            echo -e "${GREEN}✅ PASS${NC} (Status: $status_code)"

            # Special handling for health endpoint
            if [[ "$url" == *"/health" ]]; then
                # Check if response contains expected fields
                if echo "$body" | grep -q '"status"'; then
                    echo "   📊 Health check response validated"
                else
                    echo -e "   ${YELLOW}⚠️  Warning: Health response may be malformed${NC}"
                fi
            fi
        else
            echo -e "${RED}❌ FAIL${NC} (Status: $status_code, Expected: $expected_status)"
            echo "   Response: $body"
            return 1
        fi
    else
        echo -e "${RED}❌ FAIL${NC} (Connection failed)"
        return 1
    fi
}

# Track test results
PASSED=0
FAILED=0

# Test homepage
if test_endpoint "$APP_URL/" 200 "Homepage"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Test health endpoint
if test_endpoint "$APP_URL/health" 200 "Health Check"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Test probe endpoint (may not exist yet)
if test_endpoint "$APP_URL/probe" 200 "Probe Endpoint"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Test non-existent endpoint (should return 404)
if test_endpoint "$APP_URL/nonexistent" 404 "404 Handling"; then
    ((PASSED++))
else
    ((FAILED++))
fi

echo
echo "📊 Test Results:"
echo "   ✅ Passed: $PASSED"
echo "   ❌ Failed: $FAILED"
echo "   📈 Total: $((PASSED + FAILED))"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All smoke tests passed!${NC}"
    exit 0
else
    echo -e "${RED}💥 Some tests failed. Check the output above.${NC}"
    exit 1
fi
# Nova CI-Rescue Smoke Test Script
# Tests the deployed GitHub App on Fly.io

set -e

APP_URL="https://nova-ci-rescue.fly.dev"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🚀 Starting Nova CI-Rescue smoke tests..."
echo "📍 Testing app at: $APP_URL"
echo

# Function to test endpoint
test_endpoint() {
    local url="$1"
    local expected_status="${2:-200}"
    local description="$3"

    echo -n "Testing $description ($url)... "

    if response=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null); then
        status_code=$(echo "$response" | tail -n1)
        body=$(echo "$response" | head -n -1)

        if [ "$status_code" -eq "$expected_status" ]; then
            echo -e "${GREEN}✅ PASS${NC} (Status: $status_code)"

            # Special handling for health endpoint
            if [[ "$url" == *"/health" ]]; then
                # Check if response contains expected fields
                if echo "$body" | grep -q '"status"'; then
                    echo "   📊 Health check response validated"
                else
                    echo -e "   ${YELLOW}⚠️  Warning: Health response may be malformed${NC}"
                fi
            fi
        else
            echo -e "${RED}❌ FAIL${NC} (Status: $status_code, Expected: $expected_status)"
            echo "   Response: $body"
            return 1
        fi
    else
        echo -e "${RED}❌ FAIL${NC} (Connection failed)"
        return 1
    fi
}

# Track test results
PASSED=0
FAILED=0

# Test homepage
if test_endpoint "$APP_URL/" 200 "Homepage"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Test health endpoint
if test_endpoint "$APP_URL/health" 200 "Health Check"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Test probe endpoint (may not exist yet)
if test_endpoint "$APP_URL/probe" 200 "Probe Endpoint"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Test non-existent endpoint (should return 404)
if test_endpoint "$APP_URL/nonexistent" 404 "404 Handling"; then
    ((PASSED++))
else
    ((FAILED++))
fi

echo
echo "📊 Test Results:"
echo "   ✅ Passed: $PASSED"
echo "   ❌ Failed: $FAILED"
echo "   📈 Total: $((PASSED + FAILED))"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All smoke tests passed!${NC}"
    exit 0
else
    echo -e "${RED}💥 Some tests failed. Check the output above.${NC}"
    exit 1
fi
# Nova CI-Rescue Smoke Test Script
# Tests the deployed GitHub App on Fly.io

set -e

APP_URL="https://nova-ci-rescue.fly.dev"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🚀 Starting Nova CI-Rescue smoke tests..."
echo "📍 Testing app at: $APP_URL"
echo

# Function to test endpoint
test_endpoint() {
    local url="$1"
    local expected_status="${2:-200}"
    local description="$3"

    echo -n "Testing $description ($url)... "

    if response=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null); then
        status_code=$(echo "$response" | tail -n1)
        body=$(echo "$response" | head -n -1)

        if [ "$status_code" -eq "$expected_status" ]; then
            echo -e "${GREEN}✅ PASS${NC} (Status: $status_code)"

            # Special handling for health endpoint
            if [[ "$url" == *"/health" ]]; then
                # Check if response contains expected fields
                if echo "$body" | grep -q '"status"'; then
                    echo "   📊 Health check response validated"
                else
                    echo -e "   ${YELLOW}⚠️  Warning: Health response may be malformed${NC}"
                fi
            fi
        else
            echo -e "${RED}❌ FAIL${NC} (Status: $status_code, Expected: $expected_status)"
            echo "   Response: $body"
            return 1
        fi
    else
        echo -e "${RED}❌ FAIL${NC} (Connection failed)"
        return 1
    fi
}

# Track test results
PASSED=0
FAILED=0

# Test homepage
if test_endpoint "$APP_URL/" 200 "Homepage"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Test health endpoint
if test_endpoint "$APP_URL/health" 200 "Health Check"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Test probe endpoint (may not exist yet)
if test_endpoint "$APP_URL/probe" 200 "Probe Endpoint"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Test non-existent endpoint (should return 404)
if test_endpoint "$APP_URL/nonexistent" 404 "404 Handling"; then
    ((PASSED++))
else
    ((FAILED++))
fi

echo
echo "📊 Test Results:"
echo "   ✅ Passed: $PASSED"
echo "   ❌ Failed: $FAILED"
echo "   📈 Total: $((PASSED + FAILED))"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All smoke tests passed!${NC}"
    exit 0
else
    echo -e "${RED}💥 Some tests failed. Check the output above.${NC}"
    exit 1
fi
# Nova CI-Rescue Smoke Test Script
# Tests the deployed GitHub App on Fly.io

set -e

APP_URL="https://nova-ci-rescue.fly.dev"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🚀 Starting Nova CI-Rescue smoke tests..."
echo "📍 Testing app at: $APP_URL"
echo

# Function to test endpoint
test_endpoint() {
    local url="$1"
    local expected_status="${2:-200}"
    local description="$3"

    echo -n "Testing $description ($url)... "

    if response=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null); then
        status_code=$(echo "$response" | tail -n1)
        body=$(echo "$response" | head -n -1)

        if [ "$status_code" -eq "$expected_status" ]; then
            echo -e "${GREEN}✅ PASS${NC} (Status: $status_code)"

            # Special handling for health endpoint
            if [[ "$url" == *"/health" ]]; then
                # Check if response contains expected fields
                if echo "$body" | grep -q '"status"'; then
                    echo "   📊 Health check response validated"
                else
                    echo -e "   ${YELLOW}⚠️  Warning: Health response may be malformed${NC}"
                fi
            fi
        else
            echo -e "${RED}❌ FAIL${NC} (Status: $status_code, Expected: $expected_status)"
            echo "   Response: $body"
            return 1
        fi
    else
        echo -e "${RED}❌ FAIL${NC} (Connection failed)"
        return 1
    fi
}

# Track test results
PASSED=0
FAILED=0

# Test homepage
if test_endpoint "$APP_URL/" 200 "Homepage"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Test health endpoint
if test_endpoint "$APP_URL/health" 200 "Health Check"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Test probe endpoint (may not exist yet)
if test_endpoint "$APP_URL/probe" 200 "Probe Endpoint"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Test non-existent endpoint (should return 404)
if test_endpoint "$APP_URL/nonexistent" 404 "404 Handling"; then
    ((PASSED++))
else
    ((FAILED++))
fi

echo
echo "📊 Test Results:"
echo "   ✅ Passed: $PASSED"
echo "   ❌ Failed: $FAILED"
echo "   📈 Total: $((PASSED + FAILED))"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All smoke tests passed!${NC}"
    exit 0
else
    echo -e "${RED}💥 Some tests failed. Check the output above.${NC}"
    exit 1
fi
# Nova CI-Rescue Smoke Test Script
# Tests the deployed GitHub App on Fly.io

set -e

APP_URL="https://nova-ci-rescue.fly.dev"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🚀 Starting Nova CI-Rescue smoke tests..."
echo "📍 Testing app at: $APP_URL"
echo

# Function to test endpoint
test_endpoint() {
    local url="$1"
    local expected_status="${2:-200}"
    local description="$3"

    echo -n "Testing $description ($url)... "

    if response=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null); then
        status_code=$(echo "$response" | tail -n1)
        body=$(echo "$response" | head -n -1)

        if [ "$status_code" -eq "$expected_status" ]; then
            echo -e "${GREEN}✅ PASS${NC} (Status: $status_code)"

            # Special handling for health endpoint
            if [[ "$url" == *"/health" ]]; then
                # Check if response contains expected fields
                if echo "$body" | grep -q '"status"'; then
                    echo "   📊 Health check response validated"
                else
                    echo -e "   ${YELLOW}⚠️  Warning: Health response may be malformed${NC}"
                fi
            fi
        else
            echo -e "${RED}❌ FAIL${NC} (Status: $status_code, Expected: $expected_status)"
            echo "   Response: $body"
            return 1
        fi
    else
        echo -e "${RED}❌ FAIL${NC} (Connection failed)"
        return 1
    fi
}

# Track test results
PASSED=0
FAILED=0

# Test homepage
if test_endpoint "$APP_URL/" 200 "Homepage"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Test health endpoint
if test_endpoint "$APP_URL/health" 200 "Health Check"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Test probe endpoint (may not exist yet)
if test_endpoint "$APP_URL/probe" 200 "Probe Endpoint"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Test non-existent endpoint (should return 404)
if test_endpoint "$APP_URL/nonexistent" 404 "404 Handling"; then
    ((PASSED++))
else
    ((FAILED++))
fi

echo
echo "📊 Test Results:"
echo "   ✅ Passed: $PASSED"
echo "   ❌ Failed: $FAILED"
echo "   📈 Total: $((PASSED + FAILED))"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All smoke tests passed!${NC}"
    exit 0
else
    echo -e "${RED}💥 Some tests failed. Check the output above.${NC}"
    exit 1
fi