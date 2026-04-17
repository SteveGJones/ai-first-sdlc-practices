#!/bin/bash
set -e

echo "=== SDLC Worker Container ==="

cleanup() {
    echo ""
    echo "=== Cleanup ==="
    rm -f /home/sdlc/.claude/.credentials.json
    kill -- -$$ 2>/dev/null || true
}
trap cleanup SIGTERM SIGINT EXIT

# Step 1: Ensure no API key overrides Max subscription
unset ANTHROPIC_API_KEY

# Step 1b: Link scoped credential mount to where Claude Code expects it
if [ -d /home/sdlc/.claude-auth ] && [ "$(ls -A /home/sdlc/.claude-auth 2>/dev/null)" ]; then
    for auth_file in /home/sdlc/.claude-auth/*; do
        if [ -f "$auth_file" ]; then
            cp "$auth_file" /home/sdlc/.claude/"$(basename "$auth_file")"
            chmod 600 /home/sdlc/.claude/"$(basename "$auth_file")"
        fi
    done
    echo "Auth: credentials loaded from scoped mount"
fi

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

# Step 4.5: Activate loop signal workaround if needed
# Conditional — same pattern as the ARM64 fix. Self-deactivating when
# Archon fixes bug #1126.
LOOP_WORKAROUND_ACTIVE=false
if [ -f /opt/sdlc-scripts/detect-loop-bug.sh ]; then
    if bash /opt/sdlc-scripts/detect-loop-bug.sh >/dev/null 2>&1; then
        if [ -f /opt/sdlc-scripts/loop-workaround.sh ]; then
            source /opt/sdlc-scripts/loop-workaround.sh
            LOOP_WORKAROUND_ACTIVE=true
            echo "Loop workaround: active"
            cleanup_sentinel
        fi
    else
        echo "Loop workaround: not needed (bug not detected)"
    fi
fi

# Step 5: Execute the assigned work
# If ARCHON_WORKFLOW is set, run an Archon workflow
# Otherwise, pass through to Claude Code
TIMEOUT="${CLAUDE_TIMEOUT:-300}"
if [ -n "$ARCHON_WORKFLOW" ]; then
    echo "Running Archon workflow: $ARCHON_WORKFLOW"
    echo "Arguments: ${ARCHON_ARGS:-<none>}"
    echo ""
    timeout "$TIMEOUT" archon run "$ARCHON_WORKFLOW" ${ARCHON_ARGS:+"$ARCHON_ARGS"}
elif [ -n "$CLAUDE_PROMPT" ]; then
    echo "Running Claude Code with prompt..."
    timeout "$TIMEOUT" claude --dangerously-skip-permissions -p "$CLAUDE_PROMPT"
else
    echo "No ARCHON_WORKFLOW or CLAUDE_PROMPT set."
    echo "Usage:"
    echo "  ARCHON_WORKFLOW=sdlc-parallel-review  — run an Archon workflow"
    echo "  CLAUDE_PROMPT='fix the bug in app.py'  — run a direct Claude prompt"
    exit 1
fi

echo ""
echo "=== SDLC Worker Complete ==="
