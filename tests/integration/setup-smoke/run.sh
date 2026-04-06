#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Verify base image exists
if ! docker image inspect sdlc-smoke-base:latest >/dev/null 2>&1; then
    echo "Base image not found. Building..."
    "$SCRIPT_DIR/build.sh"
fi

# Check if the credential volume exists
if ! docker volume inspect sdlc-smoke-claude-creds >/dev/null 2>&1; then
    echo "ERROR: Credential volume 'sdlc-smoke-claude-creds' not found."
    echo ""
    echo "First-time setup required. Run this command interactively:"
    echo ""
    echo "  $SCRIPT_DIR/login.sh"
    echo ""
    echo "This starts an interactive container, runs 'claude /login',"
    echo "and stores the credentials in a named Docker volume that"
    echo "persists between smoke test runs."
    exit 1
fi

# Ensure ANTHROPIC_API_KEY is NOT set (would override Max subscription)
unset ANTHROPIC_API_KEY

echo "=== Running SDLC Setup Smoke Test ==="
echo "Auth: Claude Code Max subscription (from named volume)"
echo "Plugins: installed from public GitHub during test"
echo ""

docker run --rm \
    -v sdlc-smoke-claude-creds:/home/sdlc/.claude \
    -v "$SCRIPT_DIR/PROMPT.md:/workspace/PROMPT.md:ro" \
    -v "$SCRIPT_DIR/ralph.yml:/workspace/ralph.yml:ro" \
    -v "$SCRIPT_DIR/fixtures/eventflow/README.md:/workspace/README.md:ro" \
    sdlc-smoke-base:latest

echo ""
echo "=== Smoke Test Finished ==="
