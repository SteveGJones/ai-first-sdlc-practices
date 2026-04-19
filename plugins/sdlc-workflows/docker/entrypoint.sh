#!/bin/bash
set -e

echo "=== SDLC Worker Container ==="

cleanup() {
    echo ""
    echo "=== Cleanup ==="
    rm -f /home/sdlc/.claude/.credentials.json
    # Signal the entire process group (PGID == this script's PID, because
    # bash is PID 1 under docker's default init). This catches claude,
    # archon, python, and any grandchildren they spawned — a plain
    # `kill $pid` would leave them orphaned and block container exit.
    # `|| true` swallows "No such process" on the race where children
    # already exited cleanly.
    kill -- -$$ 2>/dev/null || true
}
trap cleanup SIGTERM SIGINT EXIT

# Step 1: Ensure no API key overrides Max subscription
unset ANTHROPIC_API_KEY

# Step 1b: Copy credentials from staging mount to where Claude Code expects them.
# Credentials mount to /home/sdlc/.claude-creds/ (read-only) to avoid being
# shadowed by the tmpfs at /home/sdlc/.claude/ (writable for runtime state).
if [ -f /home/sdlc/.claude-creds/.credentials.json ]; then
    cp /home/sdlc/.claude-creds/.credentials.json /home/sdlc/.claude/.credentials.json
    chmod 600 /home/sdlc/.claude/.credentials.json
    echo "Auth: credentials loaded from creds mount"
fi

# Legacy: .claude-auth directory mount.
# S-I-7: copy ONLY .credentials.json, never arbitrary files from the
# auth mount.  The older volume layout sometimes contained shell rc
# files and configuration that should not be trusted wholesale.
if [ -f /home/sdlc/.claude-auth/.credentials.json ]; then
    cp /home/sdlc/.claude-auth/.credentials.json /home/sdlc/.claude/.credentials.json
    chmod 600 /home/sdlc/.claude/.credentials.json
    echo "Auth: credentials loaded from auth mount"
fi

# Step 1c: Credential freshness probe (S-M-6 / AC-I-8).
# Parse the credentials file and emit a specific diagnostic if the
# OAuth token is already expired or within five minutes of expiry.
# Doing this before `claude -p "say ok"` means the failure message is
# precise ("token expired at X") instead of a generic
# "authentication_error" that surfaces much later.
if [ -f /home/sdlc/.claude/.credentials.json ]; then
    python3 - <<'PY'
import json, sys, time
from pathlib import Path
p = Path("/home/sdlc/.claude/.credentials.json")
try:
    data = json.loads(p.read_text())
except Exception:
    sys.exit(0)
oauth = data.get("claudeAiOauth") or {}
expires_at = oauth.get("expiresAt")
if not isinstance(expires_at, (int, float)):
    sys.exit(0)
remaining = expires_at / 1000.0 - time.time()
if remaining <= 0:
    print(f"Auth: CREDENTIALS EXPIRED — token lifetime ended {-int(remaining)}s ago.",
          file=sys.stderr)
    print("      Run `claude /login` on the host and retry.", file=sys.stderr)
    sys.exit(2)
if remaining < 300:
    print(f"Auth: credentials expire in {int(remaining)}s — consider `claude /login` now.",
          file=sys.stderr)
PY
    freshness_rc=$?
    if [ "$freshness_rc" -eq 2 ]; then
        exit 2
    fi
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

# If CLAUDE_MODEL is set by the workflow node, forward it to Claude as --model.
MODEL_ARGS=()
if [ -n "$CLAUDE_MODEL" ]; then
    MODEL_ARGS=(--model "$CLAUDE_MODEL")
    echo "Model override: $CLAUDE_MODEL"
fi

if [ -n "$ARCHON_WORKFLOW" ]; then
    echo "Running Archon workflow: $ARCHON_WORKFLOW"
    echo "Arguments: ${ARCHON_ARGS:-<none>}"
    echo ""
    # ARCHON_ARGS contract (D-M-4): a whitespace-separated string that
    # gets word-split once into argv. The unquoted expansion below is
    # intentional — the workflow author is responsible for keeping
    # arguments simple (no embedded spaces or shell metachars). If a
    # multi-token arg with embedded whitespace is ever needed, it must
    # be passed via the workflow YAML's `env:` block as a dedicated
    # single-purpose variable, not overloaded into ARCHON_ARGS.
    #
    # shellcheck disable=SC2086 # intentional word-splitting
    timeout "$TIMEOUT" archon run "$ARCHON_WORKFLOW" ${ARCHON_ARGS}
elif [ -n "$CLAUDE_PROMPT" ]; then
    echo "Running Claude Code with prompt..."
    timeout "$TIMEOUT" claude --dangerously-skip-permissions "${MODEL_ARGS[@]}" -p "$CLAUDE_PROMPT"
else
    echo "No ARCHON_WORKFLOW or CLAUDE_PROMPT set."
    echo "Usage:"
    echo "  ARCHON_WORKFLOW=sdlc-parallel-review  — run an Archon workflow"
    echo "  CLAUDE_PROMPT='fix the bug in app.py'  — run a direct Claude prompt"
    exit 1
fi

echo ""
echo "=== SDLC Worker Complete ==="
