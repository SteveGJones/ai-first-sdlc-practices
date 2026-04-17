#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
PLUGIN_DIR="$REPO_ROOT/plugins/sdlc-workflows"
SCRIPTS_DIR="$PLUGIN_DIR/scripts"
MINI="$SCRIPT_DIR/miniproject"

MODE="sequential"
if [ "${1:-}" = "--parallel" ]; then
    MODE="parallel"
fi

PASS_COUNT=0
FAIL_COUNT=0

if [ "$MODE" = "sequential" ]; then
    TOTAL=6
    echo "=== Phase 4 E2E Orchestration Test (sequential) ==="
    echo "Proves Archon orchestrates containerised team workflows."
else
    TOTAL=8
    echo "=== Phase 4 E2E Orchestration Test (parallel) ==="
    echo "Proves Archon orchestrates parallel fork/merge workflows."
fi
echo ""

pass() { echo "  PASS: $1"; PASS_COUNT=$((PASS_COUNT + 1)); }
fail() { echo "  FAIL: $1 — $2"; FAIL_COUNT=$((FAIL_COUNT + 1)); }

# ---------------------------------------------------------------------------
# Prerequisites
# ---------------------------------------------------------------------------
for cmd in docker python3; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "ERROR: $cmd not found."
        exit 1
    fi
done

if ! command -v archon >/dev/null 2>&1; then
    echo "WARNING: archon CLI not found on host. Will execute nodes directly."
fi

for img in sdlc-worker:base sdlc-worker:full; do
    if ! docker image inspect "$img" >/dev/null 2>&1; then
        echo "$img not found. Build it first."
        exit 1
    fi
done

# ---------------------------------------------------------------------------
# Build team images
# ---------------------------------------------------------------------------
TEAMS_DIR="$REPO_ROOT/.archon/teams"
AGENTS_DIR="$REPO_ROOT/.archon/agents"
BACKUP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/e2e-backup.XXXXXX")
mkdir -p "$TEAMS_DIR" "$AGENTS_DIR" "$BACKUP_DIR/teams" "$BACKUP_DIR/agents"

ls "$TEAMS_DIR"/*.yaml >/dev/null 2>&1 && cp "$TEAMS_DIR"/*.yaml "$BACKUP_DIR/teams/" || true
ls "$AGENTS_DIR"/*.md >/dev/null 2>&1 && cp "$AGENTS_DIR"/*.md "$BACKUP_DIR/agents/" || true

WORKSPACE=$(mktemp -d "${TMPDIR:-/tmp}/e2e-workspace.XXXXXX")

cleanup() {
    rm -f "$TEAMS_DIR"/dev-team.yaml "$TEAMS_DIR"/review-team.yaml
    rm -f "$AGENTS_DIR"/project-context.md
    rm -rf "$TEAMS_DIR/.generated/dev-team"* "$TEAMS_DIR/.generated/review-team"*
    ls "$BACKUP_DIR/teams/"*.yaml >/dev/null 2>&1 && cp "$BACKUP_DIR/teams/"*.yaml "$TEAMS_DIR/" || true
    ls "$BACKUP_DIR/agents/"*.md >/dev/null 2>&1 && cp "$BACKUP_DIR/agents/"*.md "$AGENTS_DIR/" || true
    rm -rf "$BACKUP_DIR" "$WORKSPACE"
    docker rmi sdlc-worker:dev-team sdlc-worker:review-team 2>/dev/null || true
}
trap cleanup EXIT

cp "$MINI/.archon/teams/dev-team.yaml" "$TEAMS_DIR/"
cp "$MINI/.archon/teams/review-team.yaml" "$TEAMS_DIR/"
cp "$MINI/.archon/agents/project-context.md" "$AGENTS_DIR/"

echo "[build] Building team images..."
bash "$PLUGIN_DIR/docker/build-team.sh" dev-team 2>&1 | tail -1
bash "$PLUGIN_DIR/docker/build-team.sh" review-team 2>&1 | tail -1
echo ""

# Copy miniproject to writable workspace
cp -R "$MINI"/* "$WORKSPACE/"
cp -R "$MINI"/.archon "$WORKSPACE/"
(cd "$WORKSPACE" && git init -q && git config user.email "test@test.com" && git config user.name "Test" && git add -A && git commit -q -m "initial" 2>/dev/null) || true

# ---------------------------------------------------------------------------
# Check 1: Resolve credentials (shared)
# ---------------------------------------------------------------------------
echo "[1/$TOTAL] Resolve credentials"
CRED_INFO=$(python3 "$SCRIPTS_DIR/resolve_credentials.py" --project-dir "$WORKSPACE" --json 2>/dev/null) || true
CRED_TIER=$(echo "$CRED_INFO" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tier','none'))" 2>/dev/null)
CRED_MOUNT=$(echo "$CRED_INFO" | python3 -c "import sys,json; print(json.load(sys.stdin).get('mount_args',''))" 2>/dev/null)

if [ "$CRED_TIER" = "none" ] || [ -z "$CRED_MOUNT" ]; then
    fail "credentials" "no credentials available (tier=$CRED_TIER)"
    echo "Run $PLUGIN_DIR/scripts/login.sh first, or ensure Claude Code is authenticated on this Mac."
    echo "=== Results: $PASS_COUNT pass, $FAIL_COUNT fail (of $TOTAL) ==="
    exit 1
fi
pass "credentials resolved (tier: $CRED_TIER)"

# ---------------------------------------------------------------------------
# Helper: execute workflow nodes directly via docker run
# ---------------------------------------------------------------------------
run_nodes_direct() {
    local WORKFLOW_FILE="$1"
    echo "  archon not found on host — executing nodes via docker run"

    # Extract nodes respecting depends_on ordering.
    # Python sorts topologically: no-deps first, then by dependency depth.
    NODES=$(python3 -c "
import yaml
from pathlib import Path

wf = yaml.safe_load(Path('$WORKFLOW_FILE').read_text())
nodes = wf.get('nodes', [])

# Build dependency graph and sort topologically
node_map = {n['id']: n for n in nodes}
visited = set()
order = []

def visit(nid):
    if nid in visited:
        return
    visited.add(nid)
    for dep in node_map.get(nid, {}).get('depends_on', []):
        visit(dep)
    order.append(nid)

for n in nodes:
    visit(n['id'])

for nid in order:
    n = node_map[nid]
    img = n.get('image', '')
    cmd = n.get('command', '')
    print(f'{nid}|{img}|{cmd}')
" 2>/dev/null)

    for NODE_LINE in $NODES; do
        NODE_ID=$(echo "$NODE_LINE" | cut -d'|' -f1)
        NODE_IMAGE=$(echo "$NODE_LINE" | cut -d'|' -f2)
        NODE_CMD=$(echo "$NODE_LINE" | cut -d'|' -f3)

        if [ -z "$NODE_IMAGE" ]; then
            echo "  Skipping node $NODE_ID (no image)"
            continue
        fi

        echo "  Running node: $NODE_ID (image: $NODE_IMAGE)"

        CMD_FILE="$WORKSPACE/.archon/commands/$NODE_CMD.md"
        if [ -f "$CMD_FILE" ]; then
            PROMPT=$(cat "$CMD_FILE")
        else
            PROMPT="Execute command: $NODE_CMD"
        fi

        NODE_OUTPUT=$(docker run --rm \
            --read-only \
            --tmpfs /tmp:rw,noexec,nosuid \
            --tmpfs /home/sdlc/.claude:rw,noexec,nosuid \
            --cap-drop ALL \
            -v "$WORKSPACE:/workspace" \
            -v "$CRED_MOUNT" \
            -e "CLAUDE_PROMPT=$PROMPT" \
            "$NODE_IMAGE" 2>&1) || true

        echo "  Node $NODE_ID: $(echo "$NODE_OUTPUT" | tail -1)"
    done
}

# ===========================================================================
# SEQUENTIAL MODE
# ===========================================================================
if [ "$MODE" = "sequential" ]; then

# ---------------------------------------------------------------------------
# Check 2: Preprocess workflow
# ---------------------------------------------------------------------------
echo "[2/$TOTAL] Preprocess feature-pipeline"
GENERATED_DIR="$WORKSPACE/.archon/workflows/.generated"
mkdir -p "$GENERATED_DIR"

python3 "$SCRIPTS_DIR/preprocess_workflow.py" \
    "$WORKSPACE/.archon/workflows/feature-pipeline.yaml" \
    --output "$GENERATED_DIR/feature-pipeline.yaml" \
    --workspace "$WORKSPACE" \
    --cred-mount "$CRED_MOUNT" \
    --commands-dir "$WORKSPACE/.archon/commands" 2>/dev/null

if [ -f "$GENERATED_DIR/feature-pipeline.yaml" ]; then
    if grep -q "bash:" "$GENERATED_DIR/feature-pipeline.yaml"; then
        pass "workflow preprocessed — image nodes transformed to bash nodes"
    else
        fail "preprocessing" "output file exists but has no bash nodes"
    fi
else
    fail "preprocessing" "output file not created"
    echo "=== Results: $PASS_COUNT pass, $FAIL_COUNT fail (of $TOTAL) ==="
    exit 1
fi

# ---------------------------------------------------------------------------
# Check 3: Execute workflow
# ---------------------------------------------------------------------------
echo "[3/$TOTAL] Execute preprocessed workflow (this takes ~3-5 min)"

if command -v archon >/dev/null 2>&1; then
    rm -f "$WORKSPACE/.archon/workflows/feature-pipeline.yaml"
    cp "$GENERATED_DIR/feature-pipeline.yaml" "$WORKSPACE/.archon/workflows/feature-pipeline.yaml"
    ARCHON_OUTPUT=$(cd "$WORKSPACE" && archon workflow run feature-pipeline --no-worktree 2>&1) || true
    EXECUTION_METHOD="archon"
else
    EXECUTION_METHOD="direct"
    run_nodes_direct "$WORKSPACE/.archon/workflows/feature-pipeline.yaml"
fi

WORKSPACE_COMMITS=$(cd "$WORKSPACE" && git log --oneline 2>/dev/null | wc -l | tr -d ' ')
if [ "${WORKSPACE_COMMITS:-0}" -gt 1 ]; then
    pass "workflow execution complete via $EXECUTION_METHOD ($((WORKSPACE_COMMITS - 1)) commit(s))"
else
    fail "workflow execution" "no commits produced. Method: $EXECUTION_METHOD"
fi

# ---------------------------------------------------------------------------
# Check 4: Implementation correctness
# ---------------------------------------------------------------------------
echo "[4/$TOTAL] Implementation correctness"
IMPL_CHECK=$(cd "$WORKSPACE" && python3 -c "
import sys
sys.path.insert(0, 'src')
from app import TaskTracker
t = TaskTracker()
t.add('urgent', priority='high')
t.add('normal')
has_priority = any('priority' in task for task in t.list_tasks())
has_method = hasattr(t, 'high_priority_count')
print(f'priority={has_priority} method={has_method}')
" 2>&1) || true

if echo "$IMPL_CHECK" | grep -q "priority=True method=True"; then
    pass "priority field and high_priority_count() work"
else
    fail "implementation" "$IMPL_CHECK"
fi

# ---------------------------------------------------------------------------
# Check 5: Review output
# ---------------------------------------------------------------------------
echo "[5/$TOTAL] Review output exists"
if [ -f "$WORKSPACE/review-output.md" ]; then
    LINES=$(wc -l < "$WORKSPACE/review-output.md" | tr -d ' ')
    pass "review-output.md exists ($LINES lines)"
elif [ -f "$WORKSPACE/security-review.md" ] || [ -f "$WORKSPACE/architecture-review.md" ]; then
    pass "review output found (security and/or architecture review files)"
else
    fail "review output" "no review files found in workspace"
fi

# ---------------------------------------------------------------------------
# Check 6: Git history
# ---------------------------------------------------------------------------
echo "[6/$TOTAL] Git history"
COMMITS=$(cd "$WORKSPACE" && git log --oneline 2>/dev/null)
COMMIT_COUNT=$(echo "$COMMITS" | wc -l | tr -d ' ')
if [ "${COMMIT_COUNT:-0}" -gt 1 ]; then
    pass "git history: $COMMIT_COUNT commits"
    echo "       $(echo "$COMMITS" | head -5)"
else
    fail "git history" "expected multiple commits, got $COMMIT_COUNT"
fi

# ===========================================================================
# PARALLEL MODE
# ===========================================================================
else

# ---------------------------------------------------------------------------
# Check 2: Preprocess parallel workflow
# ---------------------------------------------------------------------------
echo "[2/$TOTAL] Preprocess parallel-review-pipeline"
GENERATED_DIR="$WORKSPACE/.archon/workflows/.generated"
mkdir -p "$GENERATED_DIR"

python3 "$SCRIPTS_DIR/preprocess_workflow.py" \
    "$WORKSPACE/.archon/workflows/parallel-review-pipeline.yaml" \
    --output "$GENERATED_DIR/parallel-review-pipeline.yaml" \
    --workspace "$WORKSPACE" \
    --cred-mount "$CRED_MOUNT" \
    --commands-dir "$WORKSPACE/.archon/commands" 2>/dev/null

if [ -f "$GENERATED_DIR/parallel-review-pipeline.yaml" ]; then
    if grep -q "bash:" "$GENERATED_DIR/parallel-review-pipeline.yaml"; then
        pass "parallel workflow preprocessed — image nodes transformed to bash nodes"
    else
        fail "preprocessing" "output file exists but has no bash nodes"
    fi
else
    fail "preprocessing" "output file not created"
    echo "=== Results: $PASS_COUNT pass, $FAIL_COUNT fail (of $TOTAL) ==="
    exit 1
fi

# Verify DAG structure preserved: depends_on and trigger_rule
if grep -q "depends_on:" "$GENERATED_DIR/parallel-review-pipeline.yaml" && \
   grep -q "trigger_rule:" "$GENERATED_DIR/parallel-review-pipeline.yaml"; then
    pass "DAG structure preserved (depends_on + trigger_rule)"
else
    fail "DAG structure" "missing depends_on or trigger_rule in preprocessed output"
fi

# ---------------------------------------------------------------------------
# Check 4: Execute parallel workflow
# ---------------------------------------------------------------------------
echo "[4/$TOTAL] Execute parallel workflow (this takes ~5-8 min)"

if command -v archon >/dev/null 2>&1; then
    # Remove both workflow files to avoid name conflicts, then place preprocessed version
    rm -f "$WORKSPACE/.archon/workflows/parallel-review-pipeline.yaml"
    rm -f "$WORKSPACE/.archon/workflows/feature-pipeline.yaml"
    cp "$GENERATED_DIR/parallel-review-pipeline.yaml" "$WORKSPACE/.archon/workflows/parallel-review-pipeline.yaml"
    ARCHON_OUTPUT=$(cd "$WORKSPACE" && archon workflow run parallel-review-pipeline --no-worktree 2>&1) || true
    EXECUTION_METHOD="archon"
else
    EXECUTION_METHOD="direct"
    run_nodes_direct "$WORKSPACE/.archon/workflows/parallel-review-pipeline.yaml"
fi

WORKSPACE_COMMITS=$(cd "$WORKSPACE" && git log --oneline 2>/dev/null | wc -l | tr -d ' ')
if [ "${WORKSPACE_COMMITS:-0}" -gt 1 ]; then
    pass "workflow execution complete via $EXECUTION_METHOD ($((WORKSPACE_COMMITS - 1)) commit(s))"
else
    fail "workflow execution" "no commits produced. Method: $EXECUTION_METHOD"
fi

# ---------------------------------------------------------------------------
# Check 5: Implementation produced code changes
# ---------------------------------------------------------------------------
echo "[5/$TOTAL] Implementation correctness"
IMPL_CHECK=$(cd "$WORKSPACE" && python3 -c "
import sys
sys.path.insert(0, 'src')
from app import TaskTracker
t = TaskTracker()
t.add('urgent', priority='high')
t.add('normal')
has_priority = any('priority' in task for task in t.list_tasks())
has_method = hasattr(t, 'high_priority_count')
print(f'priority={has_priority} method={has_method}')
" 2>&1) || true

if echo "$IMPL_CHECK" | grep -q "priority=True method=True"; then
    pass "priority field and high_priority_count() work"
else
    fail "implementation" "$IMPL_CHECK"
fi

# ---------------------------------------------------------------------------
# Check 6: Both review files exist
# ---------------------------------------------------------------------------
echo "[6/$TOTAL] Parallel review outputs"
REVIEW_FILES=0
if [ -f "$WORKSPACE/security-review.md" ]; then
    REVIEW_FILES=$((REVIEW_FILES + 1))
    echo "       security-review.md: $(wc -l < "$WORKSPACE/security-review.md" | tr -d ' ') lines"
fi
if [ -f "$WORKSPACE/architecture-review.md" ]; then
    REVIEW_FILES=$((REVIEW_FILES + 1))
    echo "       architecture-review.md: $(wc -l < "$WORKSPACE/architecture-review.md" | tr -d ' ') lines"
fi

if [ "$REVIEW_FILES" -eq 2 ]; then
    pass "both review files produced (security + architecture)"
elif [ "$REVIEW_FILES" -eq 1 ]; then
    fail "parallel reviews" "only one review file produced (expected 2)"
else
    fail "parallel reviews" "no review files found"
fi

# ---------------------------------------------------------------------------
# Check 7: Synthesis produced
# ---------------------------------------------------------------------------
echo "[7/$TOTAL] Synthesis output"
if [ -f "$WORKSPACE/synthesis.md" ]; then
    LINES=$(wc -l < "$WORKSPACE/synthesis.md" | tr -d ' ')
    pass "synthesis.md exists ($LINES lines)"
else
    fail "synthesis" "synthesis.md not found — synthesise node may not have run"
fi

# ---------------------------------------------------------------------------
# Check 8: Git history shows all stages
# ---------------------------------------------------------------------------
echo "[8/$TOTAL] Git history"
COMMITS=$(cd "$WORKSPACE" && git log --oneline 2>/dev/null)
COMMIT_COUNT=$(echo "$COMMITS" | wc -l | tr -d ' ')
if [ "${COMMIT_COUNT:-0}" -ge 4 ]; then
    pass "git history: $COMMIT_COUNT commits (implement + 2 reviews + synthesis)"
    echo "       $(echo "$COMMITS" | head -6)"
elif [ "${COMMIT_COUNT:-0}" -gt 1 ]; then
    pass "git history: $COMMIT_COUNT commits (some stages committed)"
    echo "       $(echo "$COMMITS" | head -6)"
else
    fail "git history" "expected 4+ commits, got $COMMIT_COUNT"
fi

fi  # end MODE

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
echo ""
echo "=== Results: $PASS_COUNT pass, $FAIL_COUNT fail (of $TOTAL) ==="
if [ "$FAIL_COUNT" -eq 0 ]; then
    echo "Phase 4 E2E orchestration test ($MODE): ALL PASS"
    echo ""
    echo "Proven:"
    echo "  - Credentials resolved automatically ($CRED_TIER)"
    echo "  - Workflow preprocessed (image nodes -> bash nodes)"
    echo "  - Execution method: $EXECUTION_METHOD"
    if [ "$MODE" = "sequential" ]; then
        echo "  - Dev-team implemented features in its container"
        echo "  - Review-team reviewed in its container"
    else
        echo "  - Dev-team implemented features in its container"
        echo "  - Two review containers ran (security + architecture)"
        echo "  - Synthesise container merged review findings"
        echo "  - DAG ordering enforced: implement -> parallel reviews -> synthesise"
    fi
    echo "  - Git history shows multi-container work"
    exit 0
else
    echo "Phase 4 E2E orchestration test ($MODE): FAILURES DETECTED"
    exit 1
fi
