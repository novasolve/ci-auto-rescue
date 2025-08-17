#!/bin/bash
# Script to run Nova on a specific file
# Usage: ./run-nova-on-file.sh broken.py

if [ $# -eq 0 ]; then
    echo "Usage: $0 <filename>"
    echo "Example: $0 broken.py"
    exit 1
fi

FILE_PATH="$1"
FILE_NAME=$(basename "$FILE_PATH")
FILE_DIR=$(dirname "$FILE_PATH")

# Check if file exists
if [ ! -f "$FILE_PATH" ]; then
    echo "Error: File '$FILE_PATH' not found"
    exit 1
fi

# Create a temporary directory for the mini-repo
TEMP_DIR=$(mktemp -d)
echo "Creating temporary repository in: $TEMP_DIR"

# Copy the file to temp directory
cp "$FILE_PATH" "$TEMP_DIR/"

# Look for corresponding test file
TEST_FILE=""
if [ -f "${FILE_DIR}/test_${FILE_NAME}" ]; then
    TEST_FILE="${FILE_DIR}/test_${FILE_NAME}"
elif [ -f "${FILE_DIR}/tests/test_${FILE_NAME}" ]; then
    TEST_FILE="${FILE_DIR}/tests/test_${FILE_NAME}"
elif [ -f "${FILE_DIR}/${FILE_NAME%.py}_test.py" ]; then
    TEST_FILE="${FILE_DIR}/${FILE_NAME%.py}_test.py"
fi

if [ -n "$TEST_FILE" ]; then
    echo "Found test file: $TEST_FILE"
    mkdir -p "$TEMP_DIR/tests"
    cp "$TEST_FILE" "$TEMP_DIR/tests/"
else
    echo "Warning: No test file found for $FILE_NAME"
    echo "Nova needs failing tests to fix. Please provide a test file."
    exit 1
fi

# Initialize git repo
cd "$TEMP_DIR"
git init
git add .
git commit -m "Initial commit with $FILE_NAME"

# Create nova config if GPT-5 is desired
if [ "$USE_GPT5" = "true" ]; then
    echo "model: gpt-5" > nova.config.yml
    echo "Using GPT-5 model"
fi

# Run Nova
echo ""
echo "Running Nova fix on $FILE_NAME..."
echo "Command: nova fix ."
nova fix . "$@"

# Show the results
echo ""
echo "Nova execution completed."
echo "Modified files:"
git diff --name-only

echo ""
echo "To see the changes:"
echo "cd $TEMP_DIR && git diff"
