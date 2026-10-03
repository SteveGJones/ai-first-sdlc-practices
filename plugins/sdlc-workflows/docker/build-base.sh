#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Building sdlc-worker:base..."
PLUGIN_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
docker build -t sdlc-worker:base -f "$SCRIPT_DIR/Dockerfile.base" "$PLUGIN_DIR"
echo "Done. Image: sdlc-worker:base"
