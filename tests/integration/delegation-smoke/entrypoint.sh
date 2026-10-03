#!/bin/bash
set -e

echo "=== SDLC Delegation Smoke Test ==="
echo ""

# Step 1: Ensure no API key overrides Max subscription
unset ANTHROPIC_API_KEY

# Step 2: Verify Claude Code is available
echo "Claude Code: $(claude --version 2>/dev/null || echo 'NOT FOUND')"
echo "Ralph: $(ralph --version 2>/dev/null || echo 'NOT FOUND')"
echo "Python: $(python --version 2>/dev/null || echo 'NOT FOUND')"
echo ""

# Step 3: Check Claude Code authentication
AUTH_CHECK=$(claude -p "say ok" 2>&1 | head -1)
if echo "$AUTH_CHECK" | grep -qi "not logged in\|please run /login"; then
    echo "ERROR: Claude Code not authenticated. Run login.sh first."
    exit 1
fi
echo "Auth: OK"
echo ""

# Step 4: Init git repo (Archon requires a git repo)
if [ ! -d .git ]; then
    git init
    git config user.email "smoke-test@example.com"
    git config user.name "Delegation Smoke Test"
    git add -A
    git commit -m "initial"
fi

# Step 5: Verify Archon (must come after git init)
echo "Archon: $(archon version 2>/dev/null || echo 'NOT FOUND')"
echo ""

# Step 6: Verify Archon sees our workflows
echo "Archon workflow discovery:"
archon workflow list 2>&1 | grep -i "smoke\|sdlc" || echo "WARNING: no SDLC/smoke workflows found"
echo ""

# Step 7: Install SDLC plugins
echo "Installing SDLC plugins..."
claude --bare -p "/plugin marketplace add SteveGJones/ai-first-sdlc-practices && /plugin install sdlc-core@ai-first-sdlc" 2>&1 | tail -3
echo ""

# Step 8: Run the smoke test via Ralph
echo "Starting Ralph loop..."
ralph run

echo ""
echo "=== Delegation Smoke Test Complete ==="
