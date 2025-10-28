#!/bin/bash

# Ensure the GOOGLE_API_KEY environment variable is set
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "Error: GOOGLE_API_KEY environment variable is not set." >&2
    exit 1
fi

# Define the target directory and file
TARGET_DIR="reforestAI-agent"
ENV_FILE="$TARGET_DIR/.env"

# Create the directory if it doesn't exist
mkdir -p "$TARGET_DIR"

# Create the .env file with the Google API key
echo "GOOGLE_API_KEY=$GOOGLE_API_KEY" > "$ENV_FILE"

echo ".env file created in $TARGET_DIR"

adk api_server --host 0.0.0.0