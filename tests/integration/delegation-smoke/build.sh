#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DOCKER_DIR="$(cd "$SCRIPT_DIR/../../../plugins/sdlc-workflows/docker" && pwd)"

# Ensure base image exists
if ! docker image inspect sdlc-worker:latest >/dev/null 2>&1; then
    echo "Base image sdlc-worker:latest not found. Building..."
    bash "$DOCKER_DIR/build.sh"
fi

echo "Building delegation-smoke-base:latest..."
docker build -t delegation-smoke-base:latest "$SCRIPT_DIR"
echo ""
echo "Done. Image: delegation-smoke-base:latest"
echo "Run the smoke test with: $SCRIPT_DIR/run.sh"
