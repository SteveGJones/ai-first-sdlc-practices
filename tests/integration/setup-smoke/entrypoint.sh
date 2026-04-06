#!/bin/bash
set -e

echo "=== SDLC Setup Smoke Test ==="
echo ""

# Step 1: Ensure no API key set (use Max subscription)
unset ANTHROPIC_API_KEY

# Step 2: Verify Claude Code is available
echo "Claude Code version: $(claude --version 2>/dev/null || echo 'NOT FOUND')"
echo "Ralph version: $(ralph --version 2>/dev/null || echo 'NOT FOUND')"
echo "Python version: $(python --version 2>/dev/null || echo 'NOT FOUND')"
echo ""

# Step 3: Check Claude Code authentication
# The /root/.claude directory should be a persistent named volume
# First-time setup requires interactive login (see README)
AUTH_CHECK=$(claude -p "say ok" 2>&1 | head -1)
if echo "$AUTH_CHECK" | grep -qi "not logged in\|please run /login"; then
    echo "ERROR: Claude Code is not authenticated."
    echo ""
    echo "First-time setup required. Run this command interactively:"
    echo ""
    echo "  docker run --rm -it \\"
    echo "    -v sdlc-smoke-claude-creds:/root/.claude \\"
    echo "    --entrypoint /bin/bash \\"
    echo "    sdlc-smoke-base:latest \\"
    echo "    -c 'claude /login'"
    echo ""
    echo "Then paste the URL into your host browser, complete login,"
    echo "and paste the code back into the container."
    echo ""
    echo "After that, the named volume 'sdlc-smoke-claude-creds' will"
    echo "persist the credentials and the smoke test will work."
    exit 1
fi
echo "Auth: OK"
echo ""

# Step 4: Initialize git repo (Ralph needs a git repo)
if [ ! -d .git ]; then
    git init
    git config user.email "smoke-test@example.com"
    git config user.name "Smoke Test"
    git add -A
    git commit -m "initial" --allow-empty
fi

# Step 5: Run the smoke test via Ralph
echo "Starting Ralph loop..."
ralph run

echo ""
echo "=== Smoke Test Complete ==="

# Step 6: Report results
if [ -f .sdlc/team-config.json ]; then
    echo "PASS: .sdlc/team-config.json exists"
    echo "Contents:"
    cat .sdlc/team-config.json | python -m json.tool
else
    echo "FAIL: .sdlc/team-config.json not found"
    exit 1
fi

echo ""

if [ -f .sdlc/recommended-plugins.json ]; then
    echo "PASS: .sdlc/recommended-plugins.json exists"
    echo "Plugins found: $(python -c "import json; d=json.load(open('.sdlc/recommended-plugins.json')); print(len(d.get('plugins',[])))")"
else
    echo "FAIL: .sdlc/recommended-plugins.json not found"
    exit 1
fi
