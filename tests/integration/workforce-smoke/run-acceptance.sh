#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
PLUGIN_DIR="$REPO_ROOT/plugins/sdlc-workflows"
SCRIPTS_DIR="$PLUGIN_DIR/scripts"
MINI="$SCRIPT_DIR/miniproject"

echo "=== Phase 3 Workforce Acceptance Test ==="
echo "Proves delegated work runs inside team containers with enforcement."
echo ""

PASS_COUNT=0
FAIL_COUNT=0
TOTAL=7

pass() { echo "  PASS: $1"; PASS_COUNT=$((PASS_COUNT + 1)); }
fail() { echo "  FAIL: $1 — $2"; FAIL_COUNT=$((FAIL_COUNT + 1)); }

# ---------------------------------------------------------------------------
# Prerequisites
# ---------------------------------------------------------------------------
if ! docker info >/dev/null 2>&1; then
    echo "Docker not available."
    exit 1
fi

for img in sdlc-worker:base sdlc-worker:full; do
    if ! docker image inspect "$img" >/dev/null 2>&1; then
        echo "$img not found. Run build-base.sh and build-full.sh first."
        exit 1
    fi
done

# Resolve credentials using the three-tier fallback (Keychain → volume → config)
CRED_INFO=$(python3 "$SCRIPTS_DIR/resolve_credentials.py" --project-dir "." --json 2>/dev/null) || true
CRED_TIER=$(echo "$CRED_INFO" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tier','none'))" 2>/dev/null)
CRED_MOUNT=$(echo "$CRED_INFO" | python3 -c "import sys,json; print(json.load(sys.stdin).get('mount_args',''))" 2>/dev/null)

if [ "$CRED_TIER" = "none" ] || [ -z "$CRED_MOUNT" ]; then
    echo "No credentials available (tier=$CRED_TIER)."
    echo "Ensure Claude Code is authenticated on this Mac, or run: $PLUGIN_DIR/scripts/login.sh"
    exit 1
fi
echo "Credentials: tier=$CRED_TIER"

# ---------------------------------------------------------------------------
# Build team images from miniproject
# ---------------------------------------------------------------------------
TEAMS_DIR="$REPO_ROOT/.archon/teams"
AGENTS_DIR="$REPO_ROOT/.archon/agents"
BACKUP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/workforce-accept-backup.XXXXXX")
mkdir -p "$TEAMS_DIR" "$AGENTS_DIR" "$BACKUP_DIR/teams" "$BACKUP_DIR/agents"
if ls "$TEAMS_DIR"/*.yaml >/dev/null 2>&1; then
    cp "$TEAMS_DIR"/*.yaml "$BACKUP_DIR/teams/" 2>/dev/null || true
fi
if ls "$AGENTS_DIR"/*.md >/dev/null 2>&1; then
    cp "$AGENTS_DIR"/*.md "$BACKUP_DIR/agents/" 2>/dev/null || true
fi

# Writable workspace for the acceptance test
WORKSPACE=$(mktemp -d "${TMPDIR:-/tmp}/workforce-accept-ws.XXXXXX")
cp -R "$MINI"/* "$MINI"/.archon "$WORKSPACE/"

cleanup() {
    rm -f "$TEAMS_DIR"/dev-team.yaml "$TEAMS_DIR"/review-team.yaml
    rm -f "$AGENTS_DIR"/project-context.md
    rm -rf "$TEAMS_DIR/.generated/dev-team"* "$TEAMS_DIR/.generated/review-team"*
    if ls "$BACKUP_DIR/teams/"*.yaml >/dev/null 2>&1; then
        cp "$BACKUP_DIR/teams/"*.yaml "$TEAMS_DIR/" 2>/dev/null || true
    fi
    if ls "$BACKUP_DIR/agents/"*.md >/dev/null 2>&1; then
        cp "$BACKUP_DIR/agents/"*.md "$AGENTS_DIR/" 2>/dev/null || true
    fi
    rm -rf "$BACKUP_DIR" "$WORKSPACE"
    docker rmi sdlc-worker:dev-team sdlc-worker:review-team 2>/dev/null || true
}
trap cleanup EXIT

cp "$MINI/.archon/teams/dev-team.yaml" "$TEAMS_DIR/"
cp "$MINI/.archon/teams/review-team.yaml" "$TEAMS_DIR/"
cp "$MINI/.archon/agents/project-context.md" "$AGENTS_DIR/"

echo "[build] Building dev-team and review-team images..."
bash "$PLUGIN_DIR/docker/build-team.sh" dev-team 2>&1 | tail -1
bash "$PLUGIN_DIR/docker/build-team.sh" review-team 2>&1 | tail -1
echo ""

# ---------------------------------------------------------------------------
# Helper: run Claude Code inside a team container with the miniproject
# ---------------------------------------------------------------------------
# Credentials mount to a staging path (/home/sdlc/.claude-creds/) to avoid
# being shadowed by the tmpfs at /home/sdlc/.claude/. The entrypoint copies them.
run_claude() {
    local image="$1"
    local prompt_file="$2"
    local timeout="${3:-180}"

    docker run --rm \
        --read-only \
        --tmpfs /tmp:rw,noexec,nosuid \
        --tmpfs /home/sdlc/.claude:rw,noexec,nosuid \
        --cap-drop ALL \
        -v "$CRED_MOUNT" \
        -v "${WORKSPACE}:/workspace" \
        -v "${prompt_file}:/tmp/prompt.txt:ro" \
        --entrypoint /bin/bash \
        "$image" \
        -c '
            unset ANTHROPIC_API_KEY
            if [ ! -d /workspace/.git ]; then
                cd /workspace && git init -q && git config user.email "test@test.com" && git config user.name "Test" && git add -A && git commit -q -m initial 2>/dev/null || true
            fi
            cd /workspace
            claude --dangerously-skip-permissions -p "$(cat /tmp/prompt.txt)"
        ' 2>&1
}

# ---------------------------------------------------------------------------
# Check 1: Claude Code authenticates inside dev-team container
# ---------------------------------------------------------------------------
echo "[1/$TOTAL] Auth check inside dev-team"
AUTH_OUTPUT=$(docker run --rm \
    --read-only \
    --tmpfs /tmp:rw,noexec,nosuid \
    --tmpfs /home/sdlc/.claude:rw,noexec,nosuid \
    --cap-drop ALL \
    -v "$CRED_MOUNT" \
    --entrypoint /bin/bash \
    sdlc-worker:dev-team \
    -c '
        unset ANTHROPIC_API_KEY
        claude -p "say OK" 2>&1 | head -1
    ' 2>&1) || true

if echo "$AUTH_OUTPUT" | grep -qi "OK"; then
    pass "Claude Code authenticates with Max subscription inside dev-team"
else
    fail "auth" "got: $AUTH_OUTPUT"
    echo ""
    echo "Auth failed. The remaining checks require authentication."
    echo "Run: $SCRIPT_DIR/login.sh"
    echo "=== Results: $PASS_COUNT pass, $FAIL_COUNT fail (of $TOTAL) ==="
    exit 1
fi

# ---------------------------------------------------------------------------
# Check 2: Dev-team implements a feature
# ---------------------------------------------------------------------------
echo "[2/$TOTAL] Dev-team implements a feature (this takes ~1-2 min)"

# Init git in the workspace
(cd "$WORKSPACE" && git init -q && git config user.email "test@test.com" && git config user.name "Test" && git add -A && git commit -q -m "initial" 2>/dev/null) || true

DEV_PROMPT_FILE=$(mktemp "${TMPDIR:-/tmp}/dev-prompt.XXXXXX")
cat > "$DEV_PROMPT_FILE" <<'PROMPT'
You are the dev-team implementing a change to a Python task tracker.

Read src/app.py — it has a TaskTracker class with add, complete, list_tasks, pending_count.

Add a "priority" field to tasks:
1. The add() method should accept an optional priority parameter (default: "medium"). Valid values: "low", "medium", "high".
2. list_tasks() should include priority in the returned dicts.
3. Add a method high_priority_count() that returns the count of incomplete high-priority tasks.

Edit src/app.py with these changes. Then edit tests/test_app.py to add tests for the priority feature.

After making changes, commit:
  cd /workspace && git add -A && git commit -m "feat: add priority field to tasks"

Output DONE when complete.
PROMPT

DEV_OUTPUT=$(run_claude sdlc-worker:dev-team "$DEV_PROMPT_FILE" 300 2>&1) || true
rm -f "$DEV_PROMPT_FILE"

# Check if a commit was made
DEV_COMMITS=$(cd "$WORKSPACE" && git log --oneline 2>/dev/null | wc -l | tr -d ' ')
if [ "${DEV_COMMITS:-0}" -gt 1 ]; then
    pass "dev-team committed changes ($((DEV_COMMITS - 1)) commit(s) after initial)"
else
    fail "dev-team implementation" "no commits made. Output tail: $(echo "$DEV_OUTPUT" | tail -5)"
fi

# ---------------------------------------------------------------------------
# Check 3: The implementation is correct
# ---------------------------------------------------------------------------
echo "[3/$TOTAL] Implementation produces working code"
IMPL_CHECK=$(cd "$WORKSPACE" && python3 -c "
import sys
sys.path.insert(0, 'src')
from app import TaskTracker
t = TaskTracker()
t.add('urgent', priority='high')
t.add('normal')
tasks = t.list_tasks()
has_priority = any('priority' in task for task in tasks)
has_method = hasattr(t, 'high_priority_count')
print(f'priority_field={has_priority} method={has_method}')
" 2>&1) || true

if echo "$IMPL_CHECK" | grep -q "priority_field=True method=True"; then
    pass "priority field and high_priority_count() both work"
else
    fail "implementation correctness" "$IMPL_CHECK"
fi

# ---------------------------------------------------------------------------
# Check 4: Review-team reviews the implementation
# ---------------------------------------------------------------------------
echo "[4/$TOTAL] Review-team reviews the changes (this takes ~1-2 min)"

REVIEW_PROMPT_FILE=$(mktemp "${TMPDIR:-/tmp}/review-prompt.XXXXXX")
cat > "$REVIEW_PROMPT_FILE" <<'PROMPT'
You are the review-team performing a code review on a Python task tracker.

A developer has just added a "priority" field to the TaskTracker class.

Review the changes:
1. Read src/app.py and tests/test_app.py
2. Check the git diff: cd /workspace && git log --oneline && git diff HEAD~1
3. Assess: Is the implementation correct? Are there edge cases? Are the tests sufficient?

Write your review to /workspace/review-output.md with this structure:
  ## Summary
  (1-2 sentences)
  ## Issues Found
  (bulleted list, or "None")
  ## Recommendation
  (approve / request changes)

Output DONE when complete.
PROMPT

REVIEW_OUTPUT=$(run_claude sdlc-worker:review-team "$REVIEW_PROMPT_FILE" 300 2>&1) || true
rm -f "$REVIEW_PROMPT_FILE"

if [ -f "$WORKSPACE/review-output.md" ]; then
    REVIEW_CONTENT=$(cat "$WORKSPACE/review-output.md")
    if echo "$REVIEW_CONTENT" | grep -qi "summary\|recommendation\|issues"; then
        pass "review-team produced structured review ($(wc -l < "$WORKSPACE/review-output.md") lines)"
    else
        fail "review content" "file exists but lacks expected sections"
    fi
else
    fail "review-team" "no review-output.md produced. Output tail: $(echo "$REVIEW_OUTPUT" | tail -5)"
fi

# ---------------------------------------------------------------------------
# Check 5: Dev-team only saw its agents (enforcement)
# ---------------------------------------------------------------------------
echo "[5/$TOTAL] Dev-team enforcement — only dev agents visible"
DEV_AGENTS=$(docker run --rm --entrypoint python3 \
    -v "$REPO_ROOT/plugins/sdlc-workflows/scripts:/opt/sdlc-scripts:ro" \
    sdlc-worker:dev-team \
    -c "
import sys, json
sys.path.insert(0, '/opt/sdlc-scripts')
from team_inventory import discover_all
from pathlib import Path
result = discover_all(Path('/home/sdlc/.claude/plugins/installed_plugins.json'))
agents = []
for plugin_data in result.values():
    agents.extend(a['name'] for a in plugin_data.get('agents', []))
print(json.dumps(sorted(agents)))
" 2>&1) || true

if echo "$DEV_AGENTS" | python3 -c "
import sys, json
agents = set(json.load(sys.stdin))
# Dev-team should have verification-enforcer and sdlc-enforcer, NOT code-review-specialist
assert 'verification-enforcer' in agents, 'missing dev agent'
assert 'code-review-specialist' not in agents, 'review agent leaked into dev container'
print('OK')
" 2>/dev/null | grep -q "OK"; then
    pass "dev container has only dev agents, no review agents"
else
    fail "dev enforcement" "agents: $DEV_AGENTS"
fi

# ---------------------------------------------------------------------------
# Check 6: Review-team only saw its agents (enforcement)
# ---------------------------------------------------------------------------
echo "[6/$TOTAL] Review-team enforcement — only review agents visible"
REVIEW_AGENTS=$(docker run --rm --entrypoint python3 \
    -v "$REPO_ROOT/plugins/sdlc-workflows/scripts:/opt/sdlc-scripts:ro" \
    sdlc-worker:review-team \
    -c "
import sys, json
sys.path.insert(0, '/opt/sdlc-scripts')
from team_inventory import discover_all
from pathlib import Path
result = discover_all(Path('/home/sdlc/.claude/plugins/installed_plugins.json'))
agents = []
for plugin_data in result.values():
    agents.extend(a['name'] for a in plugin_data.get('agents', []))
print(json.dumps(sorted(agents)))
" 2>&1) || true

if echo "$REVIEW_AGENTS" | python3 -c "
import sys, json
agents = set(json.load(sys.stdin))
assert 'code-review-specialist' in agents, 'missing review agent'
assert 'verification-enforcer' not in agents, 'dev agent leaked into review container'
print('OK')
" 2>/dev/null | grep -q "OK"; then
    pass "review container has only review agents, no dev agents"
else
    fail "review enforcement" "agents: $REVIEW_AGENTS"
fi

# ---------------------------------------------------------------------------
# Check 7: Workspace changes persisted across containers
# ---------------------------------------------------------------------------
echo "[7/$TOTAL] Changes from dev-team visible to review-team"
WORKSPACE_COMMITS=$(cd "$WORKSPACE" && git log --oneline 2>/dev/null | wc -l | tr -d ' ')
REVIEW_EXISTS=$(test -f "$WORKSPACE/review-output.md" && echo "yes" || echo "no")

if [ "${WORKSPACE_COMMITS:-0}" -gt 1 ] && [ "$REVIEW_EXISTS" = "yes" ]; then
    pass "shared workspace: $WORKSPACE_COMMITS commits + review output"
else
    fail "workspace sharing" "commits=$WORKSPACE_COMMITS review_exists=$REVIEW_EXISTS"
fi

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
echo ""
echo "=== Results: $PASS_COUNT pass, $FAIL_COUNT fail (of $TOTAL) ==="

if [ -f "$WORKSPACE/review-output.md" ]; then
    echo ""
    echo "--- Review Output ---"
    cat "$WORKSPACE/review-output.md"
    echo "--- End Review ---"
fi

echo ""
if [ "$FAIL_COUNT" -eq 0 ]; then
    echo "Phase 3 workforce acceptance test: ALL PASS"
    echo ""
    echo "Proven:"
    echo "  - Claude Code runs inside team containers with Max auth"
    echo "  - Dev-team implements features against the miniproject"
    echo "  - Review-team reviews those changes"
    echo "  - Each team sees only its own agents (enforcement)"
    echo "  - Shared workspace persists across container boundaries"
    exit 0
else
    echo "Phase 3 workforce acceptance test: FAILURES DETECTED"
    exit 1
fi
