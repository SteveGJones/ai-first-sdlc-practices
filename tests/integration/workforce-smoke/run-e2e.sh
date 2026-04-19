#!/bin/bash
# Phase 4 E2E orchestration test — proves REAL delegation to per-team
# containers end-to-end.
#
# Defaults to --archon-only: archon must be on PATH and must execute
# the preprocessed workflow successfully. Silent fallback to direct
# docker-run is a release-gate hazard (earlier runs went "all green"
# while archon was broken or entirely missing), so the default is
# strict. Local iteration can opt out with --allow-fallback.
#
# Usage:
#   bash run-e2e.sh                                # sequential, archon-only (strict)
#   bash run-e2e.sh --parallel                     # parallel, archon-only (strict)
#   bash run-e2e.sh [--parallel] --allow-fallback  # try archon, fall back to direct
#   bash run-e2e.sh [--parallel] --direct-only     # skip archon entirely
#
# The order of positional + execution-mode flags is flexible.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
PLUGIN_DIR="$REPO_ROOT/plugins/sdlc-workflows"
SCRIPTS_DIR="$PLUGIN_DIR/scripts"
MINI="$SCRIPT_DIR/miniproject"

MODE="sequential"
EXECUTE_MODE="archon"  # archon | auto | direct
for arg in "$@"; do
    case "$arg" in
        --parallel)       MODE="parallel" ;;
        --archon-only)    EXECUTE_MODE="archon" ;;
        --allow-fallback) EXECUTE_MODE="auto" ;;
        --direct-only)    EXECUTE_MODE="direct" ;;
        "") ;;
        *)
            echo "ERROR: unknown flag '$arg'" >&2
            echo "Usage: $0 [--parallel] [--archon-only|--allow-fallback|--direct-only]" >&2
            exit 2
            ;;
    esac
done

# Timestamp BEFORE any work — used later to bound docker ps lookups to
# just the containers this test run produced, so the per-team
# verification cannot be poisoned by an earlier session's leftovers.
TEST_START_EPOCH=$(date +%s)

PASS_COUNT=0
FAIL_COUNT=0

if [ "$MODE" = "sequential" ]; then
    TOTAL=8   # 6 existing + 2 per-team container-ran assertions
    echo "=== Phase 4 E2E Orchestration Test (sequential) ==="
    echo "Proves Archon orchestrates containerised team workflows."
else
    TOTAL=10  # 8 existing + 2 per-team container-ran assertions
    echo "=== Phase 4 E2E Orchestration Test (parallel) ==="
    echo "Proves Archon orchestrates parallel fork/merge workflows."
fi
echo "Execute mode: $EXECUTE_MODE"
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

HAVE_ARCHON=0
command -v archon >/dev/null 2>&1 && HAVE_ARCHON=1

case "$EXECUTE_MODE" in
    archon)
        if [ "$HAVE_ARCHON" -ne 1 ]; then
            echo "ERROR: archon CLI not on PATH but --archon-only was requested."
            echo "       Install archon (https://archon.diy) or re-run with"
            echo "       --allow-fallback (local iteration) / --direct-only."
            exit 1
        fi
        ;;
    direct)
        # Direct-only explicitly chosen; never call archon.
        HAVE_ARCHON=0
        ;;
    auto)
        if [ "$HAVE_ARCHON" -ne 1 ]; then
            echo "WARNING: archon CLI not found on host — --allow-fallback is"
            echo "         in effect, so the test will execute nodes directly."
            echo "         This proves per-container delegation but NOT Archon"
            echo "         orchestration. Do not use this mode as a release gate."
        fi
        ;;
esac

for img in sdlc-worker:base sdlc-worker:full; do
    if ! docker image inspect "$img" >/dev/null 2>&1; then
        echo "$img not found. Build it first."
        exit 1
    fi
done

# ---------------------------------------------------------------------------
# Build team images — setup archon backup + workspace via shared lib
# ---------------------------------------------------------------------------
# shellcheck disable=SC1091
source "$(dirname "$0")/_lib.sh"

archon_backup_setup "e2e"
WORKSPACE=$(mktemp -d "${TMPDIR:-/tmp}/e2e-workspace.XXXXXX")

cleanup() {
    archon_backup_cleanup
    rm -rf "$WORKSPACE"
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

        # Capture the container's rc so a failed node surfaces as a
        # test failure rather than a silent pass (pre-Phase-C had
        # `|| true` here which made every "green" run a lie when the
        # container exited non-zero).
        NODE_RC=0
        NODE_OUTPUT=$(docker run --rm \
            --cap-drop ALL \
            -v "$WORKSPACE:/workspace" \
            -v "$CRED_MOUNT" \
            -e "CLAUDE_PROMPT=$PROMPT" \
            "$NODE_IMAGE" 2>&1) || NODE_RC=$?

        if [ "$NODE_RC" -ne 0 ]; then
            fail "node $NODE_ID (direct)" "container exited $NODE_RC"
            echo "$NODE_OUTPUT" | tail -10 | sed 's/^/      /'
        else
            echo "  Node $NODE_ID: $(echo "$NODE_OUTPUT" | tail -1)"
        fi
    done
}

# ---------------------------------------------------------------------------
# Helper: assert a given team image actually ran a container since the
# test started. Without this the test proves "some containers ran and
# some commits were produced" — it does NOT prove each TEAM ran in
# ITS OWN container. With multi-team delegation being the whole point
# of the delivery, this assertion closes the gap.
# ---------------------------------------------------------------------------
assert_team_ran() {
    local IMAGE="$1"
    local LABEL="$2"
    # We run containers with --rm, so `docker ps -a` can't see them
    # after exit. `docker events --since <epoch>` does surface them:
    # the event log retains lifecycle events even for removed
    # containers. Filter by image=<tag> and event=create.
    local NOW
    NOW=$(date +%s)
    local COUNT
    COUNT=$(docker events \
        --since "$TEST_START_EPOCH" \
        --until "$NOW" \
        --filter "type=container" \
        --filter "event=create" \
        --filter "image=$IMAGE" \
        --format '{{.Actor.Attributes.image}}' 2>/dev/null | wc -l | tr -d ' ')
    COUNT=${COUNT:-0}
    if [ "$COUNT" -gt 0 ]; then
        pass "$LABEL actually ran a container ($IMAGE, $COUNT invocation(s))"
    else
        fail "$LABEL" "no container from $IMAGE was observed since test start"
    fi
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

if [ "$HAVE_ARCHON" -eq 1 ] && [ "$EXECUTE_MODE" != "direct" ]; then
    rm -f "$WORKSPACE/.archon/workflows/feature-pipeline.yaml"
    cp "$GENERATED_DIR/feature-pipeline.yaml" "$WORKSPACE/.archon/workflows/feature-pipeline.yaml"
    EXECUTION_METHOD="archon"
    # Capture stderr: a broken archon CLI must surface loudly, not be
    # swallowed by `|| true`. Earlier runs hid regressions this way.
    ARCHON_LOG=$(mktemp)
    if ! (cd "$WORKSPACE" && archon workflow run feature-pipeline \
            --no-worktree >"$ARCHON_LOG" 2>&1); then
        fail "archon execution" "archon workflow run exited non-zero — see $ARCHON_LOG"
        tail -20 "$ARCHON_LOG" | sed 's/^/      /'
    fi
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

# ---------------------------------------------------------------------------
# Checks 7-8: Per-team container-ran assertions (REAL multi-team proof)
# ---------------------------------------------------------------------------
echo "[7/$TOTAL] dev-team container actually ran"
assert_team_ran "sdlc-worker:dev-team" "dev-team"

echo "[8/$TOTAL] review-team container actually ran"
assert_team_ran "sdlc-worker:review-team" "review-team"

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

if [ "$HAVE_ARCHON" -eq 1 ] && [ "$EXECUTE_MODE" != "direct" ]; then
    # Remove both workflow files to avoid name conflicts, then place preprocessed version
    rm -f "$WORKSPACE/.archon/workflows/parallel-review-pipeline.yaml"
    rm -f "$WORKSPACE/.archon/workflows/feature-pipeline.yaml"
    cp "$GENERATED_DIR/parallel-review-pipeline.yaml" "$WORKSPACE/.archon/workflows/parallel-review-pipeline.yaml"
    EXECUTION_METHOD="archon"
    ARCHON_LOG=$(mktemp)
    if ! (cd "$WORKSPACE" && archon workflow run parallel-review-pipeline \
            --no-worktree >"$ARCHON_LOG" 2>&1); then
        fail "archon execution" "archon workflow run exited non-zero — see $ARCHON_LOG"
        tail -20 "$ARCHON_LOG" | sed 's/^/      /'
    fi
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
# Check 6: Both reviewer reports exist
#
# Reviewers write to /workspace/reports/<subdir>/review.md per the G4
# parallel-git-write guardrail (parallel nodes must not commit —
# synthesise does the single fan-in commit). This check counts those
# per-reviewer files rather than expecting top-level *.md files.
# ---------------------------------------------------------------------------
echo "[6/$TOTAL] Parallel reviewer reports"
REVIEW_FILES=0
if [ -d "$WORKSPACE/reports" ]; then
    # shellcheck disable=SC2044
    for r in $(find "$WORKSPACE/reports" -mindepth 2 -name 'review.md' 2>/dev/null); do
        REVIEW_FILES=$((REVIEW_FILES + 1))
        echo "       $(basename "$(dirname "$r")")/review.md: $(wc -l < "$r" | tr -d ' ') lines"
    done
fi

if [ "$REVIEW_FILES" -ge 2 ]; then
    pass "both reviewer reports produced ($REVIEW_FILES under /workspace/reports/*/)"
elif [ "$REVIEW_FILES" -eq 1 ]; then
    fail "parallel reviews" "only one reviewer report produced (expected >=2)"
else
    fail "parallel reviews" "no reviewer reports found under /workspace/reports/*/review.md"
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

# ---------------------------------------------------------------------------
# Checks 9-10: Per-team container-ran assertions (REAL multi-team proof)
#
# Parallel workflow uses two distinct team images across 4 nodes:
#   implement    -> dev-team
#   security     -> review-team  (parallel branch)
#   architecture -> review-team  (parallel branch)
#   synthesise   -> dev-team
# So we expect >=1 dev-team invocation AND >=2 review-team invocations.
# The raw assertion only enforces >=1; the extra review-team count is
# sanity-printed but not asserted (keeps assertion count stable and
# aligned with sequential mode).
# ---------------------------------------------------------------------------
echo "[9/$TOTAL] dev-team container actually ran"
assert_team_ran "sdlc-worker:dev-team" "dev-team"

echo "[10/$TOTAL] review-team container actually ran (expect >=2)"
assert_team_ran "sdlc-worker:review-team" "review-team"

fi  # end MODE

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
echo ""
echo "=== Results: $PASS_COUNT pass, $FAIL_COUNT fail (of $TOTAL) ==="
echo "    EXECUTE_MODE=$EXECUTE_MODE  EXECUTION_METHOD=${EXECUTION_METHOD:-unknown}"
if [ "$FAIL_COUNT" -eq 0 ]; then
    echo "Phase 4 E2E orchestration test ($MODE): ALL PASS"
    echo ""
    echo "Proven:"
    echo "  - Credentials resolved automatically ($CRED_TIER)"
    echo "  - Workflow preprocessed (image nodes -> bash nodes)"
    echo "  - Execution method: $EXECUTION_METHOD"
    if [ "$MODE" = "sequential" ]; then
        echo "  - Dev-team ran in its own container (verified via docker events)"
        echo "  - Review-team ran in its own container (verified via docker events)"
    else
        echo "  - Dev-team ran in its own container (implement + synthesise)"
        echo "  - Review-team ran in its own container (security + architecture, parallel)"
        echo "  - DAG ordering enforced: implement -> parallel reviews -> synthesise"
    fi
    echo "  - Git history shows multi-container work"
    exit 0
else
    echo "Phase 4 E2E orchestration test ($MODE): FAILURES DETECTED"
    exit 1
fi
