#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Verify base image exists
if ! docker image inspect sdlc-smoke-base:latest >/dev/null 2>&1; then
    echo "Base image not found. Building..."
    "$SCRIPT_DIR/build.sh"
fi

echo "=== Claude Code Login (one-time setup) ==="
echo ""
echo "This will start an interactive container and run 'claude /login'."
echo ""
echo "When the URL appears:"
echo "  1. Press 'c' if it tries to open a browser (it can't)"
echo "  2. Copy the URL"
echo "  3. Paste it into your host browser"
echo "  4. Complete the Claude Code Max login"
echo "  5. Copy the authorization code"
echo "  6. Paste it back into the container"
echo ""
echo "After login, the credentials will be stored in the named volume"
echo "'sdlc-smoke-claude-creds' and persist for future smoke test runs."
echo ""
echo "Press Enter to continue..."
read

# Ensure ANTHROPIC_API_KEY is NOT set
unset ANTHROPIC_API_KEY

# Run interactive container as the sdlc user with named volume mounted at /home/sdlc/.claude
# (The Dockerfile creates the sdlc user with UID 1000. Login must run as this user
# so credentials get the right ownership for run.sh, which also runs as sdlc.)
# S-M-2: drop capabilities; OAuth flow needs no Linux caps.
docker run --rm -it \
    --cap-drop ALL \
    --security-opt no-new-privileges \
    -v sdlc-smoke-claude-creds:/home/sdlc/.claude \
    --entrypoint /bin/bash \
    sdlc-smoke-base:latest \
    -c "unset ANTHROPIC_API_KEY && claude /login && echo '' && echo 'Verifying auth...' && claude -p 'say ok' && echo '' && echo 'Login successful. You can now run ./run.sh'"
