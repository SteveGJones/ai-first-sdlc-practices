#!/bin/bash
set -e

echo "=== SDLC Delegation Smoke Test ==="
echo ""

# Step 1: Verify tools
unset ANTHROPIC_API_KEY
echo "Claude Code: $(claude --version 2>/dev/null || echo 'NOT FOUND')"
echo "Archon: $(archon --version 2>/dev/null || echo 'NOT FOUND')"
echo ""

# Step 2: Check auth
AUTH_CHECK=$(claude -p "say ok" 2>&1 | head -1)
if echo "$AUTH_CHECK" | grep -qi "not logged in\|please run /login"; then
    echo "ERROR: Claude Code not authenticated. Run login.sh first."
    exit 1
fi
echo "Auth: OK"
echo ""

# Step 3: Init git repo
if [ ! -d .git ]; then
    git init
    git config user.email "smoke-test@example.com"
    git config user.name "Delegation Smoke Test"
    git add -A
    git commit -m "initial"
fi

# Step 4: Install SDLC plugins
echo "Installing SDLC plugins..."
claude --bare -p "/plugin marketplace add SteveGJones/ai-first-sdlc-practices && /plugin install sdlc-core@ai-first-sdlc" 2>&1 | tail -3
echo ""

# Step 5: Verify Archon sees workflows
echo "Archon workflows:"
archon workflow list 2>/dev/null || echo "WARNING: archon workflow list failed"
echo ""

# Step 6: Run the smoke test via Ralph (Ralph drives the overall test)
echo "Starting Ralph loop..."
ralph run

echo ""
echo "=== Delegation Smoke Test Complete ==="
