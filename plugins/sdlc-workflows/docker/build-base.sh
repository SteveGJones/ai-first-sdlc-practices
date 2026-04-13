#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Building sdlc-worker:base..."
docker build -t sdlc-worker:base -f "$SCRIPT_DIR/Dockerfile.base" "$SCRIPT_DIR"
echo "Done. Image: sdlc-worker:base"
