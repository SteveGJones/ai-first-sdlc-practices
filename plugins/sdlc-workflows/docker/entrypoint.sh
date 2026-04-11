#!/bin/bash
set -e

echo "=== SDLC Worker Container ==="

# Step 1: Ensure no API key overrides Max subscription
unset ANTHROPIC_API_KEY

# Step 2: Verify Claude Code is available
echo "Claude Code version: $(claude --version 2>/dev/null || echo 'NOT FOUND')"
echo "Archon version: $(archon --version 2>/dev/null || echo 'NOT FOUND')"
echo "Python version: $(python --version 2>/dev/null || echo 'NOT FOUND')"
echo ""

# Step 3: Check Claude Code authentication
AUTH_CHECK=$(claude -p "say ok" 2>&1 | head -1)
if echo "$AUTH_CHECK" | grep -qi "not logged in\|please run /login"; then
    echo "ERROR: Claude Code is not authenticated."
    echo ""
    echo "Run the login script first to populate the credential volume:"
    echo "  ./login.sh"
    exit 1
fi
echo "Auth: OK"
echo ""

# Step 4: Initialize git repo if needed (Archon needs a git repo)
if [ ! -d .git ]; then
    git init
    git config user.email "sdlc-worker@example.com"
    git config user.name "SDLC Worker"
    git add -A 2>/dev/null || true
    git commit -m "initial" --allow-empty 2>/dev/null || true
fi

# Step 5: Execute the assigned work
# If ARCHON_WORKFLOW is set, run an Archon workflow
# Otherwise, pass through to Claude Code
if [ -n "$ARCHON_WORKFLOW" ]; then
    echo "Running Archon workflow: $ARCHON_WORKFLOW"
    echo "Arguments: ${ARCHON_ARGS:-<none>}"
    echo ""
    archon run "$ARCHON_WORKFLOW" ${ARCHON_ARGS:+"$ARCHON_ARGS"}
elif [ -n "$CLAUDE_PROMPT" ]; then
    echo "Running Claude Code with prompt..."
    claude --dangerously-skip-permissions -p "$CLAUDE_PROMPT"
else
    echo "No ARCHON_WORKFLOW or CLAUDE_PROMPT set."
    echo "Usage:"
    echo "  ARCHON_WORKFLOW=sdlc-parallel-review  — run an Archon workflow"
    echo "  CLAUDE_PROMPT='fix the bug in app.py'  — run a direct Claude prompt"
    exit 1
fi

echo ""
echo "=== SDLC Worker Complete ==="
