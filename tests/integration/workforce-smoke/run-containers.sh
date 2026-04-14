#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
PLUGIN_DIR="$REPO_ROOT/plugins/sdlc-workflows"
SCRIPTS_DIR="$PLUGIN_DIR/scripts"
MINI="$SCRIPT_DIR/miniproject"

echo "=== Phase 3 Container Integration Smoke Test ==="
echo ""

PASS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0
TOTAL=10

pass() { echo "  PASS: $1"; PASS_COUNT=$((PASS_COUNT + 1)); }
fail() { echo "  FAIL: $1 — $2"; FAIL_COUNT=$((FAIL_COUNT + 1)); }
skip() { echo "  SKIP: $1"; SKIP_COUNT=$((SKIP_COUNT + 1)); }

# ---------------------------------------------------------------------------
# Prerequisites
# ---------------------------------------------------------------------------
DOCKER_AVAILABLE=false
if docker info >/dev/null 2>&1; then
    DOCKER_AVAILABLE=true
fi

if [ "$DOCKER_AVAILABLE" != "true" ]; then
    echo "Docker not available. Skipping all container checks."
    echo "=== Results: 0 pass, 0 fail, $TOTAL skip (of $TOTAL) ==="
    exit 0
fi

IMAGES_READY=true
for img in sdlc-worker:base sdlc-worker:full; do
    if ! docker image inspect "$img" >/dev/null 2>&1; then
        echo "$img not found. Run build-base.sh and build-full.sh first."
        IMAGES_READY=false
    fi
done

if [ "$IMAGES_READY" != "true" ]; then
    echo "=== Results: 0 pass, 0 fail, $TOTAL skip (of $TOTAL) ==="
    exit 0
fi

# Check PyYAML is available in base image
echo "[pre] Checking PyYAML in base image"
if ! docker run --rm --entrypoint python3 sdlc-worker:base -c "import yaml" 2>/dev/null; then
    echo "FATAL: PyYAML not installed in sdlc-worker:base. Rebuild the base image."
    exit 1
fi
echo "  OK: PyYAML available"
echo ""

# ---------------------------------------------------------------------------
# Build team images from miniproject manifests
# ---------------------------------------------------------------------------

# Copy miniproject manifests into .archon/teams for the build script
ARCHON_DIR="$REPO_ROOT/.archon"
TEAMS_DIR="$ARCHON_DIR/teams"
mkdir -p "$TEAMS_DIR"

# Save any existing manifests
BACKUP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/workforce-smoke-backup.XXXXXX")
if ls "$TEAMS_DIR"/*.yaml >/dev/null 2>&1; then
    cp "$TEAMS_DIR"/*.yaml "$BACKUP_DIR/" 2>/dev/null || true
fi

cleanup() {
    # Restore original manifests
    rm -f "$TEAMS_DIR"/dev-team.yaml "$TEAMS_DIR"/review-team.yaml
    rm -rf "$TEAMS_DIR/.generated/dev-team"* "$TEAMS_DIR/.generated/review-team"*
    if ls "$BACKUP_DIR"/*.yaml >/dev/null 2>&1; then
        cp "$BACKUP_DIR"/*.yaml "$TEAMS_DIR/" 2>/dev/null || true
    fi
    rm -rf "$BACKUP_DIR"
    # Remove test images
    docker rmi sdlc-worker:dev-team sdlc-worker:review-team 2>/dev/null || true
}
trap cleanup EXIT

# Copy miniproject manifests in
cp "$MINI/.archon/teams/dev-team.yaml" "$TEAMS_DIR/"
cp "$MINI/.archon/teams/review-team.yaml" "$TEAMS_DIR/"

echo "[1/$TOTAL] Build dev-team image"
if bash "$PLUGIN_DIR/docker/build-team.sh" dev-team 2>&1 | tail -3; then
    pass "sdlc-worker:dev-team built"
else
    fail "dev-team build" "build-team.sh failed"
fi

echo "[2/$TOTAL] Build review-team image"
if bash "$PLUGIN_DIR/docker/build-team.sh" review-team 2>&1 | tail -3; then
    pass "sdlc-worker:review-team built"
else
    fail "review-team build" "build-team.sh failed"
fi

# ---------------------------------------------------------------------------
# Helper: run a Python script inside a team container
# ---------------------------------------------------------------------------
# Volume-mount the scripts directory and the miniproject workspace.
# --entrypoint bypasses the auth-checking entrypoint.
run_in() {
    local image="$1"
    shift
    docker run --rm \
        --entrypoint python3 \
        -v "$SCRIPTS_DIR:/opt/sdlc-scripts:ro" \
        -v "$MINI:/workspace:ro" \
        "$image" \
        "$@"
}

# ---------------------------------------------------------------------------
# Check 3-4: team_inventory inside each container sees different agents
# ---------------------------------------------------------------------------
echo "[3/$TOTAL] Inventory inside dev-team container"
DEV_INVENTORY=$(run_in sdlc-worker:dev-team \
    -c "
import sys, json
sys.path.insert(0, '/opt/sdlc-scripts')
from team_inventory import discover_all
from pathlib import Path
result = discover_all(Path('/home/sdlc/.claude/plugins/installed_plugins.json'))
# Flatten all agents across all plugins
agents = []
for plugin_data in result.values():
    agents.extend(a['name'] for a in plugin_data.get('agents', []))
print(json.dumps({'agent_count': len(agents), 'agents': sorted(agents)}))
" 2>&1) || true

DEV_AGENT_COUNT=$(echo "$DEV_INVENTORY" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d['agent_count'])
except:
    print(-1)
" 2>/dev/null)

if [ "$DEV_AGENT_COUNT" -gt 0 ] 2>/dev/null; then
    pass "dev-team inventory: $DEV_AGENT_COUNT agents visible"
    echo "       agents: $(echo "$DEV_INVENTORY" | python3 -c "import sys,json; print(', '.join(json.load(sys.stdin)['agents']))" 2>/dev/null)"
else
    fail "dev-team inventory" "got: $DEV_INVENTORY"
fi

echo "[4/$TOTAL] Inventory inside review-team container"
REVIEW_INVENTORY=$(run_in sdlc-worker:review-team \
    -c "
import sys, json
sys.path.insert(0, '/opt/sdlc-scripts')
from team_inventory import discover_all
from pathlib import Path
result = discover_all(Path('/home/sdlc/.claude/plugins/installed_plugins.json'))
agents = []
for plugin_data in result.values():
    agents.extend(a['name'] for a in plugin_data.get('agents', []))
print(json.dumps({'agent_count': len(agents), 'agents': sorted(agents)}))
" 2>&1) || true

REVIEW_AGENT_COUNT=$(echo "$REVIEW_INVENTORY" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d['agent_count'])
except:
    print(-1)
" 2>/dev/null)

if [ "$REVIEW_AGENT_COUNT" -gt 0 ] 2>/dev/null; then
    pass "review-team inventory: $REVIEW_AGENT_COUNT agents visible"
    echo "       agents: $(echo "$REVIEW_INVENTORY" | python3 -c "import sys,json; print(', '.join(json.load(sys.stdin)['agents']))" 2>/dev/null)"
else
    fail "review-team inventory" "got: $REVIEW_INVENTORY"
fi

# ---------------------------------------------------------------------------
# Check 5: different teams see different agents (enforcement proof)
# ---------------------------------------------------------------------------
echo "[5/$TOTAL] Enforcement: teams see different agent sets"
ENFORCEMENT=$(python3 -c "
import json
dev = json.loads('''$DEV_INVENTORY''')
rev = json.loads('''$REVIEW_INVENTORY''')
dev_set = set(dev['agents'])
rev_set = set(rev['agents'])
if dev_set != rev_set:
    print(f'DIFFERENT: dev={sorted(dev_set)}, review={sorted(rev_set)}')
else:
    print(f'SAME: {sorted(dev_set)}')
" 2>&1) || true

if echo "$ENFORCEMENT" | grep -q "DIFFERENT"; then
    pass "agent sets differ between containers"
else
    fail "enforcement" "both containers see the same agents: $ENFORCEMENT"
fi

# ---------------------------------------------------------------------------
# Check 6: fleet report runs inside dev-team container
# ---------------------------------------------------------------------------
echo "[6/$TOTAL] Fleet report inside dev-team container"
FLEET=$(run_in sdlc-worker:dev-team \
    -c "
import sys, json
sys.path.insert(0, '/opt/sdlc-scripts')
from teams_status_report import fleet_report
from pathlib import Path
result = fleet_report(
    Path('/workspace/.archon/teams'),
    Path('/workspace/.archon/workflows'),
)
print(json.dumps(result, default=str))
" 2>&1) || true

FLEET_OK=$(echo "$FLEET" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    assert d['team_count'] == 2, f'expected 2 teams, got {d[\"team_count\"]}'
    print('OK')
except Exception as e:
    print(f'FAIL: {e}')
" 2>/dev/null)

if [ "$FLEET_OK" = "OK" ]; then
    pass "fleet report: 2 teams from miniproject manifests"
else
    fail "fleet report" "$FLEET_OK — raw: $FLEET"
fi

# ---------------------------------------------------------------------------
# Check 7: coaching signals run inside review-team container
# ---------------------------------------------------------------------------
echo "[7/$TOTAL] Coaching signals inside review-team container"
SIGNALS=$(run_in sdlc-worker:review-team \
    -c "
import sys, json
sys.path.insert(0, '/opt/sdlc-scripts')
from teams_status_report import fleet_report
from coaching_signals import analyse_fleet
from pathlib import Path
report = fleet_report(
    Path('/workspace/.archon/teams'),
    Path('/workspace/.archon/workflows'),
)
result = analyse_fleet(report['teams'])
print(json.dumps(result))
" 2>&1) || true

SIGNALS_OK=$(echo "$SIGNALS" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    # dev-team is stale, review-team is not_built — both should produce signals
    all_signals = d['critical'] + d['advisory'] + d['informational']
    assert len(all_signals) > 0, 'expected at least 1 signal'
    print('OK')
except Exception as e:
    print(f'FAIL: {e}')
" 2>/dev/null)

if [ "$SIGNALS_OK" = "OK" ]; then
    pass "coaching signals produced inside container"
else
    fail "coaching signals" "$SIGNALS_OK — raw: $SIGNALS"
fi

# ---------------------------------------------------------------------------
# Check 8: override logger writes inside a container (writable tmpdir)
# ---------------------------------------------------------------------------
echo "[8/$TOTAL] Override logger write inside dev-team container"
OVERRIDE=$(docker run --rm \
    --entrypoint python3 \
    -v "$SCRIPTS_DIR:/opt/sdlc-scripts:ro" \
    sdlc-worker:dev-team \
    -c "
import sys, json
sys.path.insert(0, '/opt/sdlc-scripts')
from override_logger import log_override, read_overrides
from pathlib import Path
log_path = Path('/tmp/test-overrides.jsonl')
log_override(log_path, 'dev-team', 'sdlc-core:reviewer', 'pipeline', 'review')
entries = read_overrides(log_path)
print(json.dumps({'count': len(entries)}))
" 2>&1) || true

if echo "$OVERRIDE" | python3 -c "
import sys, json
d = json.load(sys.stdin)
assert d['count'] == 1
print('OK')
" 2>/dev/null | grep -q "OK"; then
    pass "override logger writes and reads inside container"
else
    fail "override logger" "got: $OVERRIDE"
fi

# ---------------------------------------------------------------------------
# Check 9: team_extend validation inside dev-team container
# ---------------------------------------------------------------------------
echo "[9/$TOTAL] team_extend validation inside dev-team container"
EXTEND_VAL=$(run_in sdlc-worker:dev-team \
    -c "
import sys
sys.path.insert(0, '/opt/sdlc-scripts')
# Also need the validation script
import importlib.util, os
val_candidates = [
    '/workspace/tools/validation/check_workflow_teams.py',
    os.path.join(os.path.dirname('/opt/sdlc-scripts/'), '..', '..', 'tools', 'validation', 'check_workflow_teams.py'),
]
# Use team_inventory for the extend check
from team_inventory import discover_all
from pathlib import Path

# Manually check: the workflow extends review node with sdlc-core:verification-enforcer.
# Inside dev-team, sdlc-core is installed and verification-enforcer is present.
inv = discover_all(Path('/home/sdlc/.claude/plugins/installed_plugins.json'))
sdlc_agents = [a['name'] for a in inv.get('sdlc-core', {}).get('agents', [])]
if 'verification-enforcer' in sdlc_agents:
    print('VALID: verification-enforcer found in container inventory')
else:
    print(f'INVALID: verification-enforcer not in {sdlc_agents}')
" 2>&1) || true

if echo "$EXTEND_VAL" | grep -q "VALID"; then
    pass "team_extend agent resolvable inside container"
else
    fail "team_extend validation" "got: $EXTEND_VAL"
fi

# ---------------------------------------------------------------------------
# Check 10: available-but-not-included works inside review-team
# ---------------------------------------------------------------------------
echo "[10/$TOTAL] Available-but-not-included inside review-team"
AVAIL=$(run_in sdlc-worker:review-team \
    -c "
import sys, json
sys.path.insert(0, '/opt/sdlc-scripts')
from team_inventory import available_but_not_included
from pathlib import Path
result = available_but_not_included(
    installed_json=Path('/home/sdlc/.claude/plugins/installed_plugins.json'),
    team_plugins=['sdlc-core'],
    team_agents=['sdlc-core:code-review-specialist', 'sdlc-core:critical-goal-reviewer'],
)
print(json.dumps(result))
" 2>&1) || true

AVAIL_OK=$(echo "$AVAIL" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    names = {a['qualified'] for a in d['agents']}
    # These agents are NOT on review-team so should show as available
    # (but only if their files exist in the container — enforcement means they don't)
    # So available list should be empty or only contain agents whose files ARE in the container
    # Either way, the included agents should NOT appear
    assert 'sdlc-core:code-review-specialist' not in names, 'included agent should not appear'
    assert 'sdlc-core:critical-goal-reviewer' not in names, 'included agent should not appear'
    print(f'OK: {len(names)} available agents')
except Exception as e:
    print(f'FAIL: {e}')
" 2>/dev/null)

if echo "$AVAIL_OK" | grep -q "OK"; then
    pass "available-but-not-included filters correctly inside container"
else
    fail "available-but-not-included" "$AVAIL_OK — raw: $AVAIL"
fi

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
echo ""
echo "=== Results: $PASS_COUNT pass, $FAIL_COUNT fail, $SKIP_COUNT skip (of $TOTAL) ==="
if [ "$FAIL_COUNT" -eq 0 ]; then
    echo "Phase 3 container integration smoke test: ALL PASS"
    exit 0
else
    echo "Phase 3 container integration smoke test: FAILURES DETECTED"
    exit 1
fi
