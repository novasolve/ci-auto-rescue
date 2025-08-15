#!/bin/bash

# Simple test for o4 model
# Usage: ./test_o4.sh YOUR_API_KEY

API_KEY="${1}"

if [ -z "$API_KEY" ]; then
    echo "Please provide your OpenAI API key as an argument:"
    echo "./test_o4.sh sk-..."
    exit 1
fi

echo "Testing o4 model..."
echo "===================="

curl -s https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "model": "o4",
    "messages": [{"role": "user", "content": "Say hello"}],
    "max_tokens": 10
  }' | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'error' in data:
        print(f'❌ Error: {data[\"error\"][\"message\"]}')
        if 'does not exist' in data['error']['message']:
            print('→ The o4 model is NOT available')
    else:
        print('✅ Success! o4 model is available')
        if 'choices' in data and data['choices']:
            print(f'Response: {data[\"choices\"][0][\"message\"][\"content\"]}')
except Exception as e:
    print(f'Failed to parse response: {e}')
    print('Raw response:', sys.stdin.read())
"
