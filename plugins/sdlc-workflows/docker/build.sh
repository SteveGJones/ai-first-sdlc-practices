#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Building sdlc-worker:latest..."
docker build -t sdlc-worker:latest "$SCRIPT_DIR"
echo ""
echo "Done. Image: sdlc-worker:latest"
echo ""
echo "To build with pre-installed plugins (faster startup, larger image):"
echo "  docker build --build-arg INSTALL_PLUGINS_AT_BUILD=true -t sdlc-worker:latest $SCRIPT_DIR"
