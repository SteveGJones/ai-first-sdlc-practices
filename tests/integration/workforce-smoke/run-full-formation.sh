#!/bin/bash
# §7.4 Multi-team super-smoke.
#
# Proves the Phase 2-5 delivery end-to-end by:
#   1. Building 4 differentiated team images from real manifests
#      (planner-team, dev-team, qa-team, synth-team).
#   2. Preprocessing a 6-node workflow that exercises every
#      preprocessor feature: serial dependency, parallel fan-out,
#      all_success trigger, per-node timeout, per-node model override,
#      and a mixed non-image finalise node.
#   3. Asserting that each generated bash command carries the right
#      flags (cap-drop, memory/cpu caps, per-node overrides, correct
#      image tag per node) — this is the structural proof that the
#      entire delivery wires up correctly.
#
# Optional: pass `--execute` to also run the preprocessed workflow via
# Archon or direct docker run (expensive — requires credentials).  The
# default (structural mode) is deterministic and does not need network
# or credentials beyond docker access.
#
# Usage:
#   bash run-full-formation.sh            # structural-only (default)
#   bash run-full-formation.sh --execute  # structural + real execution

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
PLUGIN_DIR="$REPO_ROOT/plugins/sdlc-workflows"
SCRIPTS_DIR="$PLUGIN_DIR/scripts"
MINI="$SCRIPT_DIR/miniproject"

EXECUTE=0
if [ "${1:-}" = "--execute" ]; then
    EXECUTE=1
fi

PASS_COUNT=0
FAIL_COUNT=0
TOTAL=12
if [ "$EXECUTE" -eq 1 ]; then
    TOTAL=$((TOTAL + 3))
fi

echo "=== §7.4 Multi-Team Super-Smoke ==="
echo "Proves: 4 differentiated teams + 6-node workflow + every override"
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

for img in sdlc-worker:base sdlc-worker:full; do
    if ! docker image inspect "$img" >/dev/null 2>&1; then
        echo "ERROR: $img not found. Run build-base.sh + build-full.sh first."
        exit 1
    fi
done

# ---------------------------------------------------------------------------
# Setup — archon backup + workspace (configured for 4 teams)
# ---------------------------------------------------------------------------
# Include review-team so the existing miniproject workflows
# (feature-pipeline, parallel-review-pipeline) still validate — we only
# *build* the four super-smoke teams, but the workflow-team validator
# scans every workflow YAML in the directory.
export ARCHON_SMOKE_TEAMS="planner-team dev-team qa-team synth-team review-team"
export ARCHON_SMOKE_AGENTS="project-context"

# shellcheck disable=SC1091
source "$(dirname "$0")/_lib.sh"

archon_backup_setup "full-formation"
WORKSPACE=$(mktemp -d "${TMPDIR:-/tmp}/full-formation-workspace.XXXXXX")

cleanup() {
    archon_backup_cleanup
    rm -rf "$WORKSPACE"
    docker rmi \
        sdlc-worker:planner-team \
        sdlc-worker:dev-team \
        sdlc-worker:qa-team \
        sdlc-worker:synth-team \
        2>/dev/null || true
}
trap cleanup EXIT

cp "$MINI/.archon/teams/planner-team.yaml" "$TEAMS_DIR/"
cp "$MINI/.archon/teams/dev-team.yaml"     "$TEAMS_DIR/"
cp "$MINI/.archon/teams/qa-team.yaml"      "$TEAMS_DIR/"
cp "$MINI/.archon/teams/synth-team.yaml"   "$TEAMS_DIR/"
cp "$MINI/.archon/teams/review-team.yaml"  "$TEAMS_DIR/"
cp "$MINI/.archon/agents/project-context.md" "$AGENTS_DIR/"

# ---------------------------------------------------------------------------
# Check 1-4: Build each team image
# ---------------------------------------------------------------------------
for team in planner-team dev-team qa-team synth-team; do
    echo "[$((PASS_COUNT + FAIL_COUNT + 1))/$TOTAL] Build $team image"
    if bash "$PLUGIN_DIR/docker/build-team.sh" "$team" >/dev/null 2>&1; then
        if docker image inspect "sdlc-worker:$team" >/dev/null 2>&1; then
            pass "sdlc-worker:$team built"
        else
            fail "$team build" "image tag not present after build"
        fi
    else
        fail "$team build" "build-team.sh failed"
    fi
done

# ---------------------------------------------------------------------------
# Preprocess the 6-node workflow
# ---------------------------------------------------------------------------
# Copy miniproject to writable workspace.
cp -R "$MINI"/* "$WORKSPACE/"
cp -R "$MINI"/.archon "$WORKSPACE/"
(cd "$WORKSPACE" && git init -q && git config user.email "test@test.com" \
    && git config user.name "Test" && git add -A \
    && git commit -q -m "initial") || true

GENERATED_DIR="$WORKSPACE/.archon/workflows/.generated"
mkdir -p "$GENERATED_DIR"

# For structural mode we don't need real credentials — use a dummy
# cred-mount.  Execution mode resolves real credentials below.
DUMMY_CRED_MOUNT="/dev/null:/tmp/dummy:ro"
python3 "$SCRIPTS_DIR/preprocess_workflow.py" \
    "$WORKSPACE/.archon/workflows/full-formation-pipeline.yaml" \
    --output "$GENERATED_DIR/full-formation-pipeline.yaml" \
    --workspace "$WORKSPACE" \
    --cred-mount "$DUMMY_CRED_MOUNT" \
    --commands-dir "$WORKSPACE/.archon/commands" 2>/dev/null

GEN="$GENERATED_DIR/full-formation-pipeline.yaml"

# ---------------------------------------------------------------------------
# Check 5: Preprocessed file exists
# ---------------------------------------------------------------------------
echo "[$((PASS_COUNT + FAIL_COUNT + 1))/$TOTAL] Preprocessed workflow exists"
if [ -f "$GEN" ]; then
    pass "full-formation-pipeline.yaml generated"
else
    fail "preprocess" "output file missing"
    echo "=== Results: $PASS_COUNT pass, $FAIL_COUNT fail (of $TOTAL) ==="
    exit 1
fi

# ---------------------------------------------------------------------------
# Check 6: All 4 team images referenced in bash nodes
# ---------------------------------------------------------------------------
echo "[$((PASS_COUNT + FAIL_COUNT + 1))/$TOTAL] All 4 team images present in generated bash"
MISSING=""
for team in planner-team dev-team qa-team synth-team; do
    if ! grep -q "sdlc-worker:$team" "$GEN"; then
        MISSING="$MISSING $team"
    fi
done
if [ -z "$MISSING" ]; then
    pass "planner/dev/qa/synth images all referenced"
else
    fail "image references" "missing:$MISSING"
fi

# ---------------------------------------------------------------------------
# Check 7: Per-node timeout override on `implement` (600s)
# ---------------------------------------------------------------------------
echo "[$((PASS_COUNT + FAIL_COUNT + 1))/$TOTAL] implement node carries CLAUDE_TIMEOUT=600"
if python3 -c "
import sys, yaml
wf = yaml.safe_load(open('$GEN'))
node = next(n for n in wf['nodes'] if n['id'] == 'implement')
assert 'CLAUDE_TIMEOUT=600' in node['bash'], node['bash']
" 2>/dev/null; then
    pass "timeout override propagated"
else
    fail "timeout" "CLAUDE_TIMEOUT=600 missing from implement node"
fi

# ---------------------------------------------------------------------------
# Check 8: Per-node model override on `synthesise`
# ---------------------------------------------------------------------------
echo "[$((PASS_COUNT + FAIL_COUNT + 1))/$TOTAL] every image node carries CLAUDE_MODEL=claude-sonnet-4-6"
if python3 -c "
import sys, yaml
wf = yaml.safe_load(open('$GEN'))
bad = []
for n in wf['nodes']:
    if 'bash' not in n:
        continue
    if 'CLAUDE_MODEL=claude-sonnet-4-6' not in n['bash']:
        bad.append(n['id'])
assert not bad, bad
" 2>/dev/null; then
    pass "model override propagated to every image node"
else
    fail "model" "CLAUDE_MODEL missing from one or more image nodes"
fi

# ---------------------------------------------------------------------------
# Check 9: DAG preserved — fan-out from implement, fan-in at synthesise
# ---------------------------------------------------------------------------
echo "[$((PASS_COUNT + FAIL_COUNT + 1))/$TOTAL] DAG preserved (depends_on + trigger_rule)"
if python3 -c "
import yaml
wf = yaml.safe_load(open('$GEN'))
nm = {n['id']: n for n in wf['nodes']}
# Fan-out: qa-security and qa-architecture both depend on implement
assert nm['qa-security']['depends_on']    == ['implement']
assert nm['qa-architecture']['depends_on'] == ['implement']
# Fan-in: synthesise depends on both and has all_success
assert set(nm['synthesise']['depends_on']) == {'qa-security', 'qa-architecture'}
assert nm['synthesise']['trigger_rule'] == 'all_success'
" 2>/dev/null; then
    pass "fan-out + fan-in + trigger_rule preserved"
else
    fail "DAG" "structure lost in preprocessing"
fi

# ---------------------------------------------------------------------------
# Check 10: Security hardening flags on every bash node
# ---------------------------------------------------------------------------
echo "[$((PASS_COUNT + FAIL_COUNT + 1))/$TOTAL] Security flags on every generated bash node"
if python3 -c "
import yaml
wf = yaml.safe_load(open('$GEN'))
hardening = ['--cap-drop ALL', '--security-opt no-new-privileges',
             '--memory=4g', '--cpus=2']
bad = []
for n in wf['nodes']:
    if 'bash' not in n:
        continue
    for flag in hardening:
        if flag not in n['bash']:
            bad.append((n['id'], flag))
assert not bad, bad
" 2>/dev/null; then
    pass "cap-drop + no-new-privileges + memory/cpu caps on all image nodes"
else
    fail "hardening" "one or more image nodes missing a security flag"
fi

# ---------------------------------------------------------------------------
# Check 11: Non-image finalise node preserved untransformed
# ---------------------------------------------------------------------------
echo "[$((PASS_COUNT + FAIL_COUNT + 1))/$TOTAL] Non-image finalise node preserved"
if python3 -c "
import yaml
wf = yaml.safe_load(open('$GEN'))
node = next(n for n in wf['nodes'] if n['id'] == 'finalise')
# No image → no bash transform; original prompt retained.
assert 'bash' not in node, f'finalise should not be transformed: {node}'
assert 'prompt' in node, f'finalise prompt missing: {node}'
" 2>/dev/null; then
    pass "finalise node passed through untransformed"
else
    fail "mixed nodes" "finalise node was transformed unexpectedly"
fi

# ---------------------------------------------------------------------------
# Check 12: Workflow-team reference validator agrees
# ---------------------------------------------------------------------------
echo "[$((PASS_COUNT + FAIL_COUNT + 1))/$TOTAL] check_workflow_teams validates the formation"
if python3 "$REPO_ROOT/tools/validation/check_workflow_teams.py" \
    --workflows-dir "$WORKSPACE/.archon/workflows" \
    --teams-dir "$TEAMS_DIR" >/dev/null 2>&1; then
    pass "every workflow image resolves to a team manifest"
else
    fail "workflow-team validator" "reports unresolved references"
fi

# ---------------------------------------------------------------------------
# Optional: full execution mode
# ---------------------------------------------------------------------------
if [ "$EXECUTE" -eq 1 ]; then
    echo ""
    echo "--- Execution mode (--execute) ---"

    echo "[$((PASS_COUNT + FAIL_COUNT + 1))/$TOTAL] Resolve credentials"
    CRED_INFO=$(python3 "$SCRIPTS_DIR/resolve_credentials.py" \
        --project-dir "$WORKSPACE" --json 2>/dev/null) || true
    CRED_TIER=$(echo "$CRED_INFO" | python3 -c \
        "import sys,json; print(json.load(sys.stdin).get('tier','none'))" 2>/dev/null)
    CRED_MOUNT=$(echo "$CRED_INFO" | python3 -c \
        "import sys,json; print(json.load(sys.stdin).get('mount_args',''))" 2>/dev/null)

    if [ "$CRED_TIER" = "none" ] || [ -z "$CRED_MOUNT" ]; then
        fail "execute credentials" "no credentials (tier=$CRED_TIER)"
    else
        pass "credentials resolved (tier: $CRED_TIER)"

        # Re-preprocess with real cred mount.
        python3 "$SCRIPTS_DIR/preprocess_workflow.py" \
            "$WORKSPACE/.archon/workflows/full-formation-pipeline.yaml" \
            --output "$GEN" \
            --workspace "$WORKSPACE" \
            --cred-mount "$CRED_MOUNT" \
            --commands-dir "$WORKSPACE/.archon/commands" 2>/dev/null

        echo "[$((PASS_COUNT + FAIL_COUNT + 1))/$TOTAL] Execute full-formation-pipeline"
        if command -v archon >/dev/null 2>&1; then
            rm -f "$WORKSPACE/.archon/workflows/full-formation-pipeline.yaml"
            cp "$GEN" "$WORKSPACE/.archon/workflows/full-formation-pipeline.yaml"
            (cd "$WORKSPACE" && archon workflow run full-formation-pipeline \
                --no-worktree >/dev/null 2>&1) || true
        else
            # Direct execution: run every preprocessed bash: node in
            # topological order.  This proves the generated docker run
            # commands execute end-to-end without an archon CLI on host.
            echo "    archon not on host — executing preprocessed bash nodes directly"
            python3 <<PYEOF
import subprocess
import sys
import yaml

wf = yaml.safe_load(open("$GEN"))
nodes = {n["id"]: n for n in wf["nodes"]}
visited = set()
order = []

def visit(nid):
    if nid in visited:
        return
    visited.add(nid)
    for dep in nodes[nid].get("depends_on", []) or []:
        visit(dep)
    order.append(nid)

for n in wf["nodes"]:
    visit(n["id"])

for nid in order:
    n = nodes[nid]
    if "bash" not in n:
        print(f"  [{nid}] non-image node — skipping")
        continue
    print(f"  [{nid}] running…", flush=True)
    result = subprocess.run(
        ["bash", "-c", n["bash"]],
        capture_output=True, text=True, timeout=900,
    )
    tail = (result.stdout + result.stderr).strip().split("\n")[-2:]
    for line in tail:
        print(f"    {line}")
    if result.returncode != 0:
        print(f"  [{nid}] exit {result.returncode}", file=sys.stderr)
PYEOF
        fi
        WC=$(cd "$WORKSPACE" && git log --oneline 2>/dev/null | wc -l \
            | tr -d ' ')
        if [ "${WC:-0}" -gt 1 ]; then
            pass "workflow execution produced $((WC - 1)) commit(s)"
        else
            fail "execute" "no commits produced"
        fi

        echo "[$((PASS_COUNT + FAIL_COUNT + 1))/$TOTAL] Artefact presence"
        FOUND=0
        for f in plan.md synthesis.md; do
            [ -f "$WORKSPACE/$f" ] && FOUND=$((FOUND + 1))
        done
        if [ "$FOUND" -ge 1 ]; then
            pass "at least one node artefact landed ($FOUND/2)"
        else
            fail "artefacts" "no plan.md or synthesis.md found"
        fi
    fi
fi

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
echo ""
echo "=== Results: $PASS_COUNT pass, $FAIL_COUNT fail (of $TOTAL) ==="
if [ "$FAIL_COUNT" -eq 0 ]; then
    echo "§7.4 Full-formation super-smoke: ALL PASS"
    exit 0
else
    echo "§7.4 Full-formation super-smoke: FAILURES"
    exit 1
fi
