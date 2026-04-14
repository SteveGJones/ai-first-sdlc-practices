#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Workforce Smoke Test — Claude Code Login ==="
echo ""
echo "This creates a credential volume with ONLY the auth file."
echo "No plugins, no settings — just the credential token."
echo ""

# Use the base image (no team plugins needed for login)
if ! docker image inspect sdlc-worker:base >/dev/null 2>&1; then
    echo "ERROR: sdlc-worker:base not found. Build it first."
    exit 1
fi

# Create or reuse a credential-only volume
CRED_VOLUME="sdlc-workforce-smoke-creds"

echo "Starting interactive login container..."
echo "Run 'claude /login' inside the container, then exit."
echo ""

docker run --rm -it \
    -v "${CRED_VOLUME}:/home/sdlc/.claude" \
    --entrypoint /bin/bash \
    sdlc-worker:base \
    -c 'claude /login && echo "" && echo "Login complete."'

# Extract only the credential file into a scoped volume
SCOPED_VOLUME="sdlc-workforce-smoke-auth"
echo ""
echo "Extracting credential file to scoped volume..."

docker volume create "$SCOPED_VOLUME" >/dev/null 2>&1 || true
docker run --rm \
    -v "${CRED_VOLUME}:/source:ro" \
    -v "${SCOPED_VOLUME}:/dest" \
    --entrypoint /bin/sh \
    alpine \
    -c 'cp /source/.credentials.json /dest/.credentials.json 2>/dev/null && chown 1001:1001 /dest/.credentials.json && chmod 600 /dest/.credentials.json && echo "OK: .credentials.json copied (owned by sdlc)" || echo "WARN: no .credentials.json found"'

echo ""
echo "Done. Scoped credential volume: $SCOPED_VOLUME"
echo "Run the acceptance test: $SCRIPT_DIR/run-acceptance.sh"
