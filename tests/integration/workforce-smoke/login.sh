#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Workforce Smoke Test — Claude Code Login ==="
echo ""
echo "This must be run from an interactive terminal (not from Claude Code)."
echo "It creates a credential volume for the acceptance test."
echo ""

if ! docker info >/dev/null 2>&1; then
    echo "ERROR: Docker not available."
    exit 1
fi

if ! docker image inspect sdlc-worker:base >/dev/null 2>&1; then
    echo "ERROR: sdlc-worker:base not found. Build it first."
    exit 1
fi

CRED_VOLUME="sdlc-workforce-smoke-creds"
SCOPED_VOLUME="sdlc-workforce-smoke-auth"

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

# Quick auth check
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

# Extract only the credential file into a scoped volume with correct ownership
docker volume rm "$SCOPED_VOLUME" 2>/dev/null || true
docker volume create "$SCOPED_VOLUME" >/dev/null

docker run --rm \
    -v "${CRED_VOLUME}:/source:ro" \
    -v "${SCOPED_VOLUME}:/dest" \
    --entrypoint /bin/sh \
    alpine \
    -c 'cp /source/.credentials.json /dest/.credentials.json && chown 1001:1001 /dest/.credentials.json && chmod 600 /dest/.credentials.json && echo "OK"'

echo ""
echo "Done. Credentials stored in volume: $SCOPED_VOLUME"
echo "Run the acceptance test: $SCRIPT_DIR/run-acceptance.sh"
