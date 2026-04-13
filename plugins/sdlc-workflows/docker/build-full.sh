#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGINS_DIR="${CLAUDE_PLUGINS_DIR:-$HOME/.claude/plugins}"

if [ ! -d "$PLUGINS_DIR" ]; then
    echo "ERROR: Plugin directory not found: $PLUGINS_DIR"
    echo "Set CLAUDE_PLUGINS_DIR if plugins are in a non-standard location."
    exit 1
fi

if ! docker image inspect sdlc-worker:base >/dev/null 2>&1; then
    echo "Base image not found. Building it first..."
    bash "$SCRIPT_DIR/build-base.sh"
fi

echo "Building sdlc-worker:full from $PLUGINS_DIR..."
docker build -t sdlc-worker:full --build-arg "PLUGINS_DIR=$PLUGINS_DIR" -f "$SCRIPT_DIR/Dockerfile.full" "$PLUGINS_DIR/.."
echo "Done. Image: sdlc-worker:full"
