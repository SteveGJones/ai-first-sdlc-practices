#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Verify auth exists on host
if [ ! -f "$HOME/.claude.json" ]; then
    echo "ERROR: ~/.claude.json not found."
    echo "Authenticate Claude Code on your host first: run 'claude' and log in."
    exit 1
fi

if [ ! -d "$HOME/.claude" ]; then
    echo "ERROR: ~/.claude/ directory not found."
    echo "Authenticate Claude Code on your host first: run 'claude' and log in."
    exit 1
fi

# Verify base image exists
if ! docker image inspect sdlc-smoke-base:latest >/dev/null 2>&1; then
    echo "Base image not found. Building..."
    "$SCRIPT_DIR/build.sh"
fi

# Ensure ANTHROPIC_API_KEY is NOT set (would override Max subscription)
unset ANTHROPIC_API_KEY

echo "=== Running SDLC Setup Smoke Test ==="
echo "Auth: Claude Code Max subscription (from host)"
echo "Plugins: installed from public GitHub during test"
echo ""

docker run --rm \
    -v "$HOME/.claude:/host-claude:ro" \
    -v "$HOME/.claude.json:/host-claude.json:ro" \
    -v "$SCRIPT_DIR/PROMPT.md:/workspace/PROMPT.md:ro" \
    -v "$SCRIPT_DIR/ralph.yml:/workspace/ralph.yml:ro" \
    -v "$SCRIPT_DIR/fixtures/eventflow/README.md:/workspace/README.md:ro" \
    sdlc-smoke-base:latest

echo ""
echo "=== Smoke Test Finished ==="
