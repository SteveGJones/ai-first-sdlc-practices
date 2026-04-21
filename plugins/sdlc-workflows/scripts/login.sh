#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Workforce Smoke Test — Claude Code Login ==="
echo ""

# TTY check
if [ ! -t 0 ] || [ ! -t 1 ]; then
    echo "ERROR: This script requires an interactive terminal."
    echo "Run it directly in a terminal, not via Claude Code or a script."
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo "ERROR: Docker not available."
    exit 1
fi

if ! docker image inspect sdlc-worker:base >/dev/null 2>&1; then
    echo "ERROR: sdlc-worker:base not found. Build it first."
    exit 1
fi

CRED_VOLUME="sdlc-login-temp"
SCOPED_VOLUME="sdlc-claude-credentials"

# Clean start
docker volume rm "$CRED_VOLUME" 2>/dev/null || true
docker volume create "$CRED_VOLUME" >/dev/null

echo "Starting interactive login container..."
echo "Authorize in your browser when prompted, then paste the code."
echo ""

docker run --rm -it \
    -v "${CRED_VOLUME}:/home/sdlc/.claude" \
    --entrypoint claude \
    sdlc-worker:base \
    auth login

echo ""
echo "Verifying credentials..."

AUTH_CHECK=$(docker run --rm \
    -v "${CRED_VOLUME}:/home/sdlc/.claude" \
    --entrypoint claude \
    sdlc-worker:base \
    -p "say OK" 2>&1 | head -1)

if echo "$AUTH_CHECK" | grep -qi "OK"; then
    echo "Auth: OK"
else
    echo "Auth check failed: $AUTH_CHECK"
    echo "Try running this script again."
    exit 1
fi

# Extract credential file into the standard scoped volume
docker volume rm "$SCOPED_VOLUME" 2>/dev/null || true
docker volume create "$SCOPED_VOLUME" >/dev/null

docker run --rm \
    -v "${CRED_VOLUME}:/source:ro" \
    -v "${SCOPED_VOLUME}:/dest" \
    --entrypoint /bin/sh \
    alpine \
    -c 'cp /source/.credentials.json /dest/.credentials.json && chown 1001:1001 /dest/.credentials.json && chmod 600 /dest/.credentials.json && echo "OK"'

# Clean up the full credential volume (only keep the scoped one)
docker volume rm "$CRED_VOLUME" 2>/dev/null || true

echo ""
echo "Done. Credentials stored in volume: $SCOPED_VOLUME"
echo "This volume is automatically detected by the credential resolver (tier 2)."
