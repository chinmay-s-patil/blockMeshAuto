#!/bin/bash

# clone_repo.sh
REPO_URL="https://github.com/chinmay-s-patil/blockMeshAuto.git"
TARGET_DIR="./Git/"

# Create directory if needed
mkdir -p "$TARGET_DIR"

# Clone the repository
git clone "$REPO_URL" "$TARGET_DIR"

# Check if clone succeeded
if [ $? -eq 0 ]; then
    echo "Clone successful"
else
    echo "Clone failed" >&2
    exit 1
fi
