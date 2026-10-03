#!/bin/bash
# Fresh-user-flow validation — simulate a brand-new user going from
# zero to a completed workflow, and enforce the "trivially easy" bar.
#
# Budget (the "trivially easy" contract):
#   elapsed  ≤ 15 min  (cold — nothing cached)
#   attention ≤ 5 min  (sum of user-required steps; the rest is unattended
#                       while images/containers build and run)
#
# The script plays the role of "user" by running the exact commands a
# user would run (plugin-provided build scripts, skill-equivalent shell
# steps, archon CLI). It annotates each step as attention (user has to
# paste / read / decide) or unattended (download / build / container
# execution) so the two budgets can be measured independently.
#
# Attention time is the *design* budget — each step's annotation
# reflects how long a competent user needs to read a prompt / paste a
# command / choose an option. If the UX regresses (adds prompts,
# requires credentials mid-flow), bump the annotation and the script
# will fail the 5-min budget, surfacing the regression.
#
# Usage:
#   bash run-fresh-user-flow.sh           # warm — reuse cached images
#   bash run-fresh-user-flow.sh --cold    # rebuild base + full from scratch
#   bash run-fresh-user-flow.sh --no-run  # setup only, skip workflow run
#
# The script never uninstalls Archon (that requires user credentials to
# reinstall). Use --cold for image rebuilds only.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
PLUGIN_DIR="$REPO_ROOT/plugins/sdlc-workflows"
MINI="$SCRIPT_DIR/miniproject"

# Log directory — repo-scoped per CLAUDE.md house rule (./tmp/, not /tmp/).
LOG_DIR="$REPO_ROOT/tmp"
mkdir -p "$LOG_DIR"

COLD=0
RUN_WORKFLOW=1
for arg in "$@"; do
    case "$arg" in
        --cold)   COLD=1 ;;
        --no-run) RUN_WORKFLOW=0 ;;
        "") ;;
        *) echo "ERROR: unknown flag '$arg'" >&2; exit 2 ;;
    esac
done

START_EPOCH=$(date +%s)
ATTENTION_SEC=0
PASS_COUNT=0
FAIL_COUNT=0
STEPS_JSON=""

elapsed_min() {
    local now=$(date +%s)
    printf "%.1f" "$(echo "($now - $START_EPOCH) / 60" | bc -l)"
}

step_attention() {
    local budget=$1; shift
    local label=$*
    ATTENTION_SEC=$((ATTENTION_SEC + budget))
    echo ""
    echo "-- [attention ${budget}s] $label"
    STEPS_JSON="$STEPS_JSON{\"kind\":\"attention\",\"budget\":$budget,\"label\":\"$label\"}"
}

step_unattended() {
    local label=$*
    echo ""
    echo "-- [unattended] $label"
}

pass() { echo "   PASS: $*"; PASS_COUNT=$((PASS_COUNT + 1)); }
fail() { echo "   FAIL: $*"; FAIL_COUNT=$((FAIL_COUNT + 1)); }

echo "=== Fresh-User-Flow Validation ==="
echo "Budget: ≤15 min elapsed, ≤5 min attention"
if [ "$COLD" -eq 1 ]; then
    echo "Mode: COLD (will rebuild base + full images)"
else
    echo "Mode: WARM (reuse cached images if present)"
fi
echo ""

# ---------------------------------------------------------------
# Step 0 — Prerequisite: repo/plugin is discoverable
# ---------------------------------------------------------------
step_unattended "0. Verify plugin layout is discoverable"
if [ -d "$PLUGIN_DIR/skills/workflows-setup" ] \
   && [ -x "$PLUGIN_DIR/docker/build-base.sh" ] \
   && [ -x "$PLUGIN_DIR/docker/build-full.sh" ] \
   && [ -x "$PLUGIN_DIR/docker/build-team.sh" ]; then
    pass "plugin skills + build scripts present"
else
    fail "plugin layout incomplete — user would be blocked here"
    exit 1
fi

# ---------------------------------------------------------------
# Step 1 — Plugin install (simulated)
#
# A real user runs:
#   /plugin marketplace add SteveGJones/ai-first-sdlc-practices
#   /plugin install sdlc-workflows@ai-first-sdlc
#
# We can't invoke the claude CLI from this script, but we CAN verify
# the marketplace entry and plugin manifest exist so a fresh user
# wouldn't hit "plugin not found".
# ---------------------------------------------------------------
step_attention 20 "1. /plugin marketplace add + /plugin install sdlc-workflows"
if [ -f "$REPO_ROOT/.claude-plugin/marketplace.json" ]; then
    if grep -q '"sdlc-workflows"' "$REPO_ROOT/.claude-plugin/marketplace.json"; then
        pass "sdlc-workflows listed in marketplace.json"
    else
        fail "sdlc-workflows NOT listed in marketplace.json"
    fi
else
    fail "marketplace.json missing from repo root"
fi
if [ -f "$PLUGIN_DIR/.claude-plugin/plugin.json" ]; then
    pass "plugin manifest present"
else
    fail "plugin manifest missing"
fi

# ---------------------------------------------------------------
# Step 2 — /sdlc-workflows:workflows-setup (Archon presence)
#
# The skill checks for archon on PATH, offering the install command
# if absent. We verify archon is reachable one way or another.
# ---------------------------------------------------------------
step_attention 30 "2. /sdlc-workflows:workflows-setup — check Archon"
ARCHON_BIN=""
if command -v archon >/dev/null 2>&1; then
    ARCHON_BIN=$(command -v archon)
    pass "archon on PATH: $ARCHON_BIN"
elif [ -x "$HOME/.bun/bin/archon" ]; then
    ARCHON_BIN="$HOME/.bun/bin/archon"
    echo "   WARN: archon at $ARCHON_BIN but not on PATH — skill would"
    echo "         tell the user to add ~/.bun/bin to PATH."
    pass "archon installed (not on PATH — skill handles this)"
else
    fail "archon not installed — a fresh user would need to run the curl|bash one-liner"
    echo "   (see workflows-setup step 2 for the installer command)"
fi
if [ -n "$ARCHON_BIN" ]; then
    ARCHON_VER=$("$ARCHON_BIN" --version 2>/dev/null | head -1 || echo "unknown")
    echo "   archon version: $ARCHON_VER"
fi

# ---------------------------------------------------------------
# Step 3 — /sdlc-workflows:workflows-setup (build base + full images)
#
# Cold: both builds run (~5-7min total).
# Warm: both skipped in seconds.
# ---------------------------------------------------------------
step_unattended "3. Build sdlc-worker:base + sdlc-worker:full"
BUILD_BASE=1
BUILD_FULL=1
if [ "$COLD" -eq 0 ]; then
    docker image inspect sdlc-worker:base >/dev/null 2>&1 && BUILD_BASE=0
    docker image inspect sdlc-worker:full >/dev/null 2>&1 && BUILD_FULL=0
fi
if [ "$BUILD_BASE" -eq 1 ]; then
    echo "   building sdlc-worker:base..."
    if bash "$PLUGIN_DIR/docker/build-base.sh" >${LOG_DIR}/fresh-build-base.log 2>&1; then
        pass "sdlc-worker:base built"
    else
        fail "sdlc-worker:base build failed — see ${LOG_DIR}/fresh-build-base.log"
        tail -10 ${LOG_DIR}/fresh-build-base.log | sed 's/^/      /'
    fi
else
    pass "sdlc-worker:base already cached (warm run)"
fi
if [ "$BUILD_FULL" -eq 1 ]; then
    echo "   building sdlc-worker:full..."
    if bash "$PLUGIN_DIR/docker/build-full.sh" >${LOG_DIR}/fresh-build-full.log 2>&1; then
        pass "sdlc-worker:full built"
    else
        fail "sdlc-worker:full build failed — see ${LOG_DIR}/fresh-build-full.log"
        tail -10 ${LOG_DIR}/fresh-build-full.log | sed 's/^/      /'
    fi
else
    pass "sdlc-worker:full already cached (warm run)"
fi

# ---------------------------------------------------------------
# Step 4 — Set up project directory
#
# Simulate a fresh user dropping into their repo. We copy the
# miniproject fixture to a scratch dir so every run starts from the
# same baseline.
# ---------------------------------------------------------------
step_unattended "4. Prepare scratch project directory"
SCRATCH=$(mktemp -d "${LOG_DIR}/fresh-user-flow-XXXXXX")
trap 'rm -rf "$SCRATCH"' EXIT INT TERM
cp -R "$MINI/." "$SCRATCH/"
# Fresh-user projects start without a .git — init one so the workflow
# can commit.
(cd "$SCRATCH" && git init -q && git add -A && git -c user.email=fresh@test -c user.name=fresh commit -q -m "initial" 2>/dev/null || true)
pass "scratch project ready at $SCRATCH"

# ---------------------------------------------------------------
# Step 5 — Author / copy a team manifest
#
# A user either writes their own or copies from docs. We verify the
# example manifest is valid YAML and has the required fields.
# ---------------------------------------------------------------
step_attention 60 "5. Author team manifest (.archon/teams/dev-team.yaml)"
if [ -f "$SCRATCH/.archon/teams/dev-team.yaml" ]; then
    if python3 -c "
import yaml, sys
m = yaml.safe_load(open('$SCRATCH/.archon/teams/dev-team.yaml'))
assert 'schema_version' in m
assert 'name' in m
assert 'agents' in m
print('valid manifest: name=' + m['name'])
" 2>&1; then
        pass "dev-team manifest valid"
    else
        fail "dev-team manifest invalid"
    fi
else
    fail "no dev-team manifest in scratch project"
fi

# ---------------------------------------------------------------
# Step 6 — /sdlc-workflows:deploy-team --name dev-team
#
# Builds the team image. First time: ~1-2min. Subsequent: seconds.
# ---------------------------------------------------------------
step_attention 10 "6. /sdlc-workflows:deploy-team (launch, once per team)"
step_unattended "6b. Team image builds (unattended)"
# The deploy-team skill generates CLAUDE.md then runs build-team.sh.
# A real user would deploy every team referenced by their workflow;
# our miniproject workflow references dev-team + review-team.
GEN_DIR="$SCRATCH/.archon/teams/.generated"
mkdir -p "$GEN_DIR"
for team in dev-team review-team; do
    MANIFEST="$SCRATCH/.archon/teams/${team}.yaml"
    if [ ! -f "$MANIFEST" ]; then
        fail "manifest missing for $team — workflow would fail to run"
        continue
    fi
    if python3 "$PLUGIN_DIR/scripts/generate_team_claude_md.py" \
            "$MANIFEST" \
            --output "$GEN_DIR/${team}.CLAUDE.md" \
            --project-claude "$SCRATCH/CLAUDE.md" >${LOG_DIR}/fresh-gen-${team}.log 2>&1; then
        pass "$team CLAUDE.md generated"
    else
        fail "$team CLAUDE.md generation failed — see ${LOG_DIR}/fresh-gen-${team}.log"
        tail -5 ${LOG_DIR}/fresh-gen-${team}.log | sed 's/^/      /'
        continue
    fi
    if (cd "$SCRATCH" && bash "$PLUGIN_DIR/docker/build-team.sh" "$team") >${LOG_DIR}/fresh-build-${team}.log 2>&1; then
        pass "sdlc-worker:${team} built"
    else
        fail "$team image build failed — see ${LOG_DIR}/fresh-build-${team}.log"
        tail -10 ${LOG_DIR}/fresh-build-${team}.log | sed 's/^/      /'
    fi
done

# ---------------------------------------------------------------
# Step 7 — Author / copy a workflow
#
# A fresh user copies feature-pipeline.yaml (or writes their own).
# Verify it is valid + references teams that exist.
# ---------------------------------------------------------------
step_attention 60 "7. Author workflow (.archon/workflows/feature-pipeline.yaml)"
WF="$SCRATCH/.archon/workflows/feature-pipeline.yaml"
if [ -f "$WF" ]; then
    if python3 -c "
import yaml
wf = yaml.safe_load(open('$WF'))
assert 'name' in wf
assert 'nodes' in wf
imgs = {n.get('image') for n in wf['nodes'] if n.get('image')}
print('workflow valid: nodes=' + str(len(wf['nodes'])) + ' images=' + str(sorted(imgs)))
" 2>&1; then
        pass "feature-pipeline workflow valid"
    else
        fail "feature-pipeline workflow invalid"
    fi
else
    fail "no feature-pipeline workflow in scratch project"
fi

if [ "$RUN_WORKFLOW" -eq 0 ]; then
    echo ""
    echo "--- Skipping workflow run (--no-run) ---"
else
# ---------------------------------------------------------------
# Step 8 — /sdlc-workflows:workflows-run feature-pipeline
#
# The expensive step. Cold or warm, this is where a fresh user sees
# their first actual delegated workflow execute. Credentials resolve,
# preprocessor compiles image nodes, archon runs.
# ---------------------------------------------------------------
step_attention 15 "8. /sdlc-workflows:workflows-run feature-pipeline (launch)"
step_unattended "8b. Workflow execution (unattended ≈2-3min)"

# Resolve credentials (same path the skill takes)
CRED_INFO=$(python3 "$PLUGIN_DIR/scripts/resolve_credentials.py" --project-dir "$SCRATCH" --json 2>&1)
CRED_TIER=$(echo "$CRED_INFO" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tier','none'))" 2>/dev/null || echo "none")
if [ "$CRED_TIER" = "none" ]; then
    fail "no Claude credentials resolvable — fresh user would need to run claude login"
    echo "$CRED_INFO" | sed 's/^/      /'
else
    pass "credentials resolved (tier: $CRED_TIER)"
fi

# Preprocess and run
if [ -n "$ARCHON_BIN" ] && [ "$CRED_TIER" != "none" ]; then
    GEN_WF_DIR="$SCRATCH/.archon/workflows/.generated"
    mkdir -p "$GEN_WF_DIR"
    CRED_MOUNT=$(echo "$CRED_INFO" | python3 -c "import sys,json; print(json.load(sys.stdin).get('mount_args',''))")
    if python3 "$PLUGIN_DIR/scripts/preprocess_workflow.py" \
            "$WF" \
            --output "$GEN_WF_DIR/feature-pipeline.yaml" \
            --workspace "$SCRATCH" \
            --cred-mount "$CRED_MOUNT" \
            --commands-dir "$SCRATCH/.archon/commands" \
            >${LOG_DIR}/fresh-preprocess.log 2>&1; then
        pass "workflow preprocessed"
    else
        fail "preprocessing failed — see ${LOG_DIR}/fresh-preprocess.log"
        tail -10 ${LOG_DIR}/fresh-preprocess.log | sed 's/^/      /'
    fi

    # Drop CLAUDECODE env vars (archon #1067)
    if (cd "$SCRATCH" && env -u CLAUDECODE -u CLAUDE_CODE_SSE_PORT -u CLAUDE_CODE_IPC_FD \
            "$ARCHON_BIN" workflow run feature-pipeline --no-worktree >${LOG_DIR}/fresh-archon-run.log 2>&1); then
        pass "workflow execution complete"
    else
        fail "workflow execution failed — see ${LOG_DIR}/fresh-archon-run.log"
        tail -15 ${LOG_DIR}/fresh-archon-run.log | sed 's/^/      /'
    fi
else
    echo "   (skipping workflow run — archon unavailable or no credentials)"
fi

# Verify workflow produced something
if (cd "$SCRATCH" && git log --oneline 2>/dev/null | head -5 | grep -qE "(feat|review|implement|synthesise)"); then
    pass "workflow produced commits in the scratch project"
else
    echo "   (no workflow commits detected — may not be a failure if run was skipped)"
fi

# ---------------------------------------------------------------
# Step 9 — Review results
# ---------------------------------------------------------------
step_attention 30 "9. Review workflow results (cherry-pick menu / inspect)"
pass "results review is a user decision — scratch workspace preserved at $SCRATCH"
fi

# ---------------------------------------------------------------
# Summary — enforce the budgets
# ---------------------------------------------------------------
END_EPOCH=$(date +%s)
ELAPSED_SEC=$((END_EPOCH - START_EPOCH))
ELAPSED_MIN=$(printf "%.1f" "$(echo "$ELAPSED_SEC / 60" | bc -l)")
ATTENTION_MIN=$(printf "%.1f" "$(echo "$ATTENTION_SEC / 60" | bc -l)")

echo ""
echo "=== Fresh-User-Flow Summary ==="
echo "Checks:     $PASS_COUNT pass / $FAIL_COUNT fail"
echo "Elapsed:    ${ELAPSED_MIN} min (budget: 15 min)"
echo "Attention:  ${ATTENTION_MIN} min (budget:  5 min — sum of user-facing steps)"
echo ""

BUDGET_FAIL=0
if [ "$ELAPSED_SEC" -gt 900 ]; then
    echo "BUDGET FAIL: elapsed ${ELAPSED_MIN} min > 15 min"
    BUDGET_FAIL=1
fi
if [ "$ATTENTION_SEC" -gt 300 ]; then
    echo "BUDGET FAIL: attention ${ATTENTION_MIN} min > 5 min"
    BUDGET_FAIL=1
fi

if [ "$FAIL_COUNT" -gt 0 ] || [ "$BUDGET_FAIL" -eq 1 ]; then
    echo "FRESH-USER-FLOW: FAIL"
    exit 1
fi

echo "FRESH-USER-FLOW: PASS — the 'trivially easy' bar still holds."
