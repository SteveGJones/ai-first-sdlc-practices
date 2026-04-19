#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Verify base image exists
if ! docker image inspect delegation-smoke-base:latest >/dev/null 2>&1; then
    echo "Smoke test image not found. Building..."
    "$SCRIPT_DIR/build.sh"
fi

# Check if the credential volume exists (reuse setup-smoke volume)
if ! docker volume inspect sdlc-smoke-claude-creds >/dev/null 2>&1; then
    echo "ERROR: Credential volume 'sdlc-smoke-claude-creds' not found."
    echo ""
    echo "First-time setup required. Run:"
    echo "  $SCRIPT_DIR/login.sh"
    echo ""
    echo "Or if you already ran the setup-smoke login:"
    echo "  The delegation smoke test reuses the same credential volume."
    exit 1
fi

unset ANTHROPIC_API_KEY

echo "=== Running SDLC Delegation Smoke Test ==="
echo "Auth: Claude Code Max subscription (from named volume)"
echo ""

# S-M-2: drop capabilities to match hardened production docker runs.
docker run --rm \
    --cap-drop ALL \
    --security-opt no-new-privileges \
    -v sdlc-smoke-claude-creds:/home/sdlc/.claude \
    delegation-smoke-base:latest

echo ""
echo "=== Delegation Smoke Test Finished ==="
