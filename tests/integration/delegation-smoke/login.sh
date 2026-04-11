#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DOCKER_DIR="$(cd "$SCRIPT_DIR/../../../plugins/sdlc-workflows/docker" && pwd)"

# Ensure base image exists
if ! docker image inspect sdlc-worker:latest >/dev/null 2>&1; then
    echo "Base image sdlc-worker:latest not found. Building..."
    bash "$DOCKER_DIR/build.sh"
fi

echo "Starting interactive login container..."
echo "Run 'claude /login' inside the container."
echo ""

docker run --rm -it \
    -v sdlc-smoke-claude-creds:/home/sdlc/.claude \
    --entrypoint /bin/bash \
    sdlc-worker:latest \
    -c 'claude /login'
