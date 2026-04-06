#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Building sdlc-smoke-base:latest..."
docker build -t sdlc-smoke-base:latest "$SCRIPT_DIR"
echo ""
echo "Done. Image: sdlc-smoke-base:latest"
echo "Run the smoke test with: $SCRIPT_DIR/run.sh"
