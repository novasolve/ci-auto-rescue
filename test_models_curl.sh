#!/bin/bash

# Test OpenAI Models via cURL
# Usage: ./test_models_curl.sh YOUR_API_KEY
# Or set OPENAI_API_KEY environment variable

API_KEY="${1:-$OPENAI_API_KEY}"

if [ -z "$API_KEY" ]; then
    echo "Error: Please provide API key as argument or set OPENAI_API_KEY environment variable"
    echo "Usage: ./test_models_curl.sh YOUR_API_KEY"
    echo "Or: export OPENAI_API_KEY='your-key-here' && ./test_models_curl.sh"
    exit 1
fi

# Models to test
MODELS=(
    "gpt-5-mini"
    "gpt-5-nano"
    "gpt-5"
    "o4"
    "o4-mini"
    "o3"
    "o3-mini"
    "gpt-4o"
    "gpt-4o-mini"
    "gpt-4-turbo"
    "gpt-3.5-turbo"
)

echo "============================================"
echo "Testing OpenAI Model Availability"
echo "============================================"
echo ""

# Function to test a model
test_model() {
    local model=$1
    echo -n "Testing $model... "
    
    response=$(curl -s -w "\n%{http_code}" https://api.openai.com/v1/chat/completions \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $API_KEY" \
        -d "{
            \"model\": \"$model\",
            \"messages\": [{\"role\": \"user\", \"content\": \"Say hello\"}],
            \"max_tokens\": 5
        }")
    
    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$http_code" = "200" ]; then
        echo "✅ AVAILABLE"
    else
        # Extract error message if available
        error_msg=$(echo "$body" | grep -o '"message":"[^"]*"' | sed 's/"message":"//;s/"//')
        if [[ "$error_msg" == *"model"* ]] && [[ "$error_msg" == *"does not exist"* ]]; then
            echo "❌ MODEL NOT FOUND"
        elif [[ "$error_msg" == *"quota"* ]] || [[ "$error_msg" == *"rate"* ]]; then
            echo "⏱️  RATE LIMITED"
        else
            echo "❌ ERROR: ${error_msg:-HTTP $http_code}"
        fi
    fi
}

# Test each model
for model in "${MODELS[@]}"; do
    test_model "$model"
    sleep 0.5  # Small delay to avoid rate limiting
done

echo ""
echo "============================================"
echo "Listing All Available Models"
echo "============================================"
echo ""

# List all available models
echo "Fetching complete model list..."
models_response=$(curl -s https://api.openai.com/v1/models \
    -H "Authorization: Bearer $API_KEY")

if [ $? -eq 0 ]; then
    # Extract and format model IDs
    echo "$models_response" | grep -o '"id":"[^"]*"' | sed 's/"id":"//;s/"//' | sort | while read -r model; do
        # Highlight models of interest
        if [[ "$model" == *"gpt-5"* ]] || [[ "$model" == *"o3"* ]] || [[ "$model" == *"o4"* ]]; then
            echo "  - $model ⭐"
        else
            echo "  - $model"
        fi
    done
else
    echo "Failed to fetch model list"
fi

echo ""
echo "Test complete!"
