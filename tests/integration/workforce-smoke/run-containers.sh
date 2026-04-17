#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
PLUGIN_DIR="$REPO_ROOT/plugins/sdlc-workflows"
SCRIPTS_DIR="$PLUGIN_DIR/scripts"
MINI="$SCRIPT_DIR/miniproject"

echo "=== Phase 3 Container Integration Smoke Test ==="
echo "Miniproject: $MINI"
echo ""

PASS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0
TOTAL=16

pass() { echo "  PASS: $1"; PASS_COUNT=$((PASS_COUNT + 1)); }
fail() { echo "  FAIL: $1 — $2"; FAIL_COUNT=$((FAIL_COUNT + 1)); }
skip() { echo "  SKIP: $1"; SKIP_COUNT=$((SKIP_COUNT + 1)); }

# ---------------------------------------------------------------------------
# Prerequisites
# ---------------------------------------------------------------------------
if ! docker info >/dev/null 2>&1; then
    echo "Docker not available. Skipping all container checks."
    echo "=== Results: 0 pass, 0 fail, $TOTAL skip (of $TOTAL) ==="
    exit 0
fi

for img in sdlc-worker:base sdlc-worker:full; do
    if ! docker image inspect "$img" >/dev/null 2>&1; then
        echo "$img not found. Run build-base.sh and build-full.sh first."
        echo "=== Results: 0 pass, 0 fail, $TOTAL skip (of $TOTAL) ==="
        exit 0
    fi
done

echo "[pre] Verifying PyYAML in base image"
if ! docker run --rm --entrypoint python3 sdlc-worker:base -c "import yaml" 2>/dev/null; then
    echo "FATAL: PyYAML not installed in sdlc-worker:base. Rebuild the base image."
    exit 1
fi
echo "  OK"

echo "[pre] Verifying miniproject structure"
for f in CLAUDE.md CONSTITUTION.md src/app.py tests/test_app.py \
         .archon/teams/dev-team.yaml .archon/teams/review-team.yaml \
         .archon/workflows/feature-pipeline.yaml .archon/agents/project-context.md; do
    if [ ! -f "$MINI/$f" ]; then
        echo "FATAL: Missing miniproject file: $f"
        exit 1
    fi
done
echo "  OK"

echo "[pre] Running miniproject tests on host"
if ! python3 -m pytest "$MINI/tests" -q 2>/dev/null; then
    echo "FATAL: Miniproject tests fail on host"
    exit 1
fi
echo "  OK"
echo ""

# ---------------------------------------------------------------------------
# Build team images from miniproject (using the real deploy-team pipeline)
# ---------------------------------------------------------------------------

# Save existing .archon state and install miniproject manifests + local agents
ARCHON_DIR="$REPO_ROOT/.archon"
TEAMS_DIR="$ARCHON_DIR/teams"
AGENTS_DIR="$ARCHON_DIR/agents"
BACKUP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/workforce-smoke-backup.XXXXXX")
mkdir -p "$TEAMS_DIR" "$AGENTS_DIR" "$BACKUP_DIR/teams" "$BACKUP_DIR/agents"
if ls "$TEAMS_DIR"/*.yaml >/dev/null 2>&1; then
    cp "$TEAMS_DIR"/*.yaml "$BACKUP_DIR/teams/" 2>/dev/null || true
fi
if ls "$AGENTS_DIR"/*.md >/dev/null 2>&1; then
    cp "$AGENTS_DIR"/*.md "$BACKUP_DIR/agents/" 2>/dev/null || true
fi

cleanup() {
    # Restore original state
    rm -f "$TEAMS_DIR"/dev-team.yaml "$TEAMS_DIR"/review-team.yaml
    rm -f "$AGENTS_DIR"/project-context.md
    rm -rf "$TEAMS_DIR/.generated/dev-team"* "$TEAMS_DIR/.generated/review-team"*
    if ls "$BACKUP_DIR/teams/"*.yaml >/dev/null 2>&1; then
        cp "$BACKUP_DIR/teams/"*.yaml "$TEAMS_DIR/" 2>/dev/null || true
    fi
    if ls "$BACKUP_DIR/agents/"*.md >/dev/null 2>&1; then
        cp "$BACKUP_DIR/agents/"*.md "$AGENTS_DIR/" 2>/dev/null || true
    fi
    rm -rf "$BACKUP_DIR"
    docker rmi sdlc-worker:dev-team sdlc-worker:review-team 2>/dev/null || true
}
trap cleanup EXIT

# Copy miniproject manifests and local agents into the repo's .archon/
cp "$MINI/.archon/teams/dev-team.yaml" "$TEAMS_DIR/"
cp "$MINI/.archon/teams/review-team.yaml" "$TEAMS_DIR/"
cp "$MINI/.archon/agents/project-context.md" "$AGENTS_DIR/"

echo "=== BUILD PHASE ==="
echo ""

echo "[1/$TOTAL] Validate dev-team manifest"
if python3 "$PLUGIN_DIR/scripts/validate_team_manifest.py" \
    "$TEAMS_DIR/dev-team.yaml" \
    --project-root "$MINI" 2>&1 | grep -q "OK"; then
    pass "dev-team manifest valid"
else
    fail "dev-team manifest" "validation failed"
fi

echo "[2/$TOTAL] Validate review-team manifest"
if python3 "$PLUGIN_DIR/scripts/validate_team_manifest.py" \
    "$TEAMS_DIR/review-team.yaml" \
    --project-root "$MINI" 2>&1 | grep -q "OK"; then
    pass "review-team manifest valid"
else
    fail "review-team manifest" "validation failed"
fi

echo "[3/$TOTAL] Build dev-team image"
if bash "$PLUGIN_DIR/docker/build-team.sh" dev-team 2>&1 | tail -3; then
    if docker image inspect sdlc-worker:dev-team >/dev/null 2>&1; then
        pass "sdlc-worker:dev-team built"
    else
        fail "dev-team build" "image not found after build"
    fi
else
    fail "dev-team build" "build-team.sh failed"
fi

echo "[4/$TOTAL] Build review-team image"
if bash "$PLUGIN_DIR/docker/build-team.sh" review-team 2>&1 | tail -3; then
    if docker image inspect sdlc-worker:review-team >/dev/null 2>&1; then
        pass "sdlc-worker:review-team built"
    else
        fail "review-team build" "image not found after build"
    fi
else
    fail "review-team build" "build-team.sh failed"
fi

# ---------------------------------------------------------------------------
# Helper: run Python inside a team container with miniproject as workspace
# ---------------------------------------------------------------------------
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

echo ""
echo "=== ENFORCEMENT PHASE ==="
echo ""

# ---------------------------------------------------------------------------
# Check 5-6: team_inventory inside each container sees different agents
# ---------------------------------------------------------------------------
echo "[5/$TOTAL] Plugin inventory inside dev-team"
DEV_INVENTORY=$(run_in sdlc-worker:dev-team \
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

DEV_AGENTS=$(echo "$DEV_INVENTORY" | python3 -c "import sys,json; print(','.join(json.load(sys.stdin)['agents']))" 2>/dev/null)
DEV_AGENT_COUNT=$(echo "$DEV_INVENTORY" | python3 -c "import sys,json; print(json.load(sys.stdin)['agent_count'])" 2>/dev/null)

if [ "${DEV_AGENT_COUNT:-0}" -gt 0 ] 2>/dev/null; then
    pass "dev-team sees $DEV_AGENT_COUNT agents: $DEV_AGENTS"
else
    fail "dev-team inventory" "$DEV_INVENTORY"
fi

echo "[6/$TOTAL] Plugin inventory inside review-team"
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

REVIEW_AGENTS=$(echo "$REVIEW_INVENTORY" | python3 -c "import sys,json; print(','.join(json.load(sys.stdin)['agents']))" 2>/dev/null)
REVIEW_AGENT_COUNT=$(echo "$REVIEW_INVENTORY" | python3 -c "import sys,json; print(json.load(sys.stdin)['agent_count'])" 2>/dev/null)

if [ "${REVIEW_AGENT_COUNT:-0}" -gt 0 ] 2>/dev/null; then
    pass "review-team sees $REVIEW_AGENT_COUNT agents: $REVIEW_AGENTS"
else
    fail "review-team inventory" "$REVIEW_INVENTORY"
fi

echo "[7/$TOTAL] Teams see different agent sets"
ENFORCEMENT=$(python3 -c "
import json
dev = json.loads('''$DEV_INVENTORY''')
rev = json.loads('''$REVIEW_INVENTORY''')
if set(dev['agents']) != set(rev['agents']):
    print('DIFFERENT')
else:
    print('SAME')
" 2>&1) || true

if [ "$ENFORCEMENT" = "DIFFERENT" ]; then
    pass "agent enforcement: containers have different agent sets"
else
    fail "enforcement" "both containers see the same agents"
fi

echo "[8/$TOTAL] Local agent accessible inside dev-team"
LOCAL_AGENT=$(run_in sdlc-worker:dev-team \
    -c "
from pathlib import Path
p = Path('/workspace/.archon/agents/project-context.md')
if p.exists() and 'TaskTracker' in p.read_text():
    print('FOUND')
else:
    print('MISSING')
" 2>&1) || true

if [ "$LOCAL_AGENT" = "FOUND" ]; then
    pass "local agent project-context.md accessible with project content"
else
    fail "local agent" "$LOCAL_AGENT"
fi

echo ""
echo "=== MANAGEMENT SCRIPTS PHASE ==="
echo ""

# ---------------------------------------------------------------------------
# Fleet report and coaching signals inside containers
# ---------------------------------------------------------------------------
echo "[9/$TOTAL] Fleet report inside dev-team"
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

FLEET_CHECK=$(echo "$FLEET" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    teams = {t['name'] for t in d['teams']}
    assert d['team_count'] == 2, f'expected 2 teams, got {d[\"team_count\"]}'
    assert 'dev-team' in teams, 'dev-team missing'
    assert 'review-team' in teams, 'review-team missing'
    assert d['workflow_count'] == 2, f'expected 2 workflows, got {d[\"workflow_count\"]}'
    print('OK')
except Exception as e:
    print(f'FAIL: {e}')
" 2>/dev/null)

if [ "$FLEET_CHECK" = "OK" ]; then
    pass "fleet report: 2 teams, 2 workflows from miniproject"
else
    fail "fleet report" "$FLEET_CHECK"
fi

echo "[10/$TOTAL] Coaching signals inside review-team"
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
types = []
for tier in ('critical', 'advisory', 'informational'):
    for s in result[tier]:
        types.append(f\"{tier}:{s['type']}\")
print(json.dumps({'signal_count': len(types), 'signals': types}))
" 2>&1) || true

SIGNAL_CHECK=$(echo "$SIGNALS" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    assert d['signal_count'] > 0, 'expected at least 1 signal'
    # dev-team is stale (updated > image_built), review-team has no image_built
    types = set(d['signals'])
    assert any('stale' in s for s in types) or any('not_built' in s for s in types), \
        f'expected stale or not_built signal, got {types}'
    print(f\"OK: {d['signal_count']} signals\")
except Exception as e:
    print(f'FAIL: {e}')
" 2>/dev/null)

if echo "$SIGNAL_CHECK" | grep -q "OK"; then
    pass "coaching signals: $SIGNAL_CHECK"
else
    fail "coaching signals" "$SIGNAL_CHECK"
fi

echo "[11/$TOTAL] Override logger inside dev-team"
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
log_override(log_path, 'dev-team', 'sdlc-core:reviewer', 'pipeline', 'review')
entries = read_overrides(log_path)
print(json.dumps({'count': len(entries)}))
" 2>&1) || true

if echo "$OVERRIDE" | python3 -c "import sys,json; assert json.load(sys.stdin)['count']==2; print('OK')" 2>/dev/null | grep -q "OK"; then
    pass "override logger: write + read round-trip inside container"
else
    fail "override logger" "$OVERRIDE"
fi

echo "[12/$TOTAL] Available-but-not-included inside review-team"
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
names = [a['qualified'] for a in result['agents']]
print(json.dumps({'available': names}))
" 2>&1) || true

AVAIL_CHECK=$(echo "$AVAIL" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    names = set(d['available'])
    assert 'sdlc-core:code-review-specialist' not in names, 'included agent leaked'
    assert 'sdlc-core:critical-goal-reviewer' not in names, 'included agent leaked'
    print(f\"OK: {len(names)} available\")
except Exception as e:
    print(f'FAIL: {e}')
" 2>/dev/null)

if echo "$AVAIL_CHECK" | grep -q "OK"; then
    pass "available-but-not-included: $AVAIL_CHECK"
else
    fail "available-but-not-included" "$AVAIL_CHECK"
fi

echo ""
echo "=== INTEGRATION PHASE ==="
echo ""

# ---------------------------------------------------------------------------
# Generated CLAUDE.md, context files, workflow validation
# ---------------------------------------------------------------------------
echo "[13/$TOTAL] Baked team CLAUDE.md has team identity"
# Check the baked-in CLAUDE.md WITHOUT the workspace mount — this is what
# deploy-team produces. At runtime, Archon mounts the project workspace which
# shadows this file; the entrypoint or session init merges them.
BAKED_MD=$(docker run --rm --entrypoint python3 sdlc-worker:dev-team \
    -c "
from pathlib import Path
content = Path('/workspace/CLAUDE.md').read_text()
has_team = 'dev-team' in content
has_role = 'delegation team' in content.lower() or 'your team' in content.lower()
has_agents = 'verification-enforcer' in content
print(f'team={has_team} role={has_role} agents={has_agents}')
" 2>&1) || true

if echo "$BAKED_MD" | grep -q "team=True role=True agents=True"; then
    pass "baked CLAUDE.md has team name, role framing, and agent list"
else
    fail "baked CLAUDE.md" "$BAKED_MD"
fi

echo "[14/$TOTAL] Context file CONSTITUTION.md accessible in workspace"
CONTEXT=$(run_in sdlc-worker:dev-team \
    -c "
from pathlib import Path
p = Path('/workspace/CONSTITUTION.md')
if p.exists() and 'Code Quality' in p.read_text():
    print('FOUND')
else:
    print('MISSING')
" 2>&1) || true

if [ "$CONTEXT" = "FOUND" ]; then
    pass "CONSTITUTION.md accessible as team context"
else
    fail "context file" "$CONTEXT"
fi

echo "[15/$TOTAL] Miniproject self-test runs inside dev-team"
# Use the app's built-in --self-test (no pytest dependency needed)
TESTS=$(run_in sdlc-worker:dev-team \
    -c "
import subprocess, sys
result = subprocess.run(
    [sys.executable, '/workspace/src/app.py', '--self-test'],
    capture_output=True, text=True
)
if result.returncode == 0 and 'Self-test passed' in result.stdout:
    print('PASS')
else:
    print(f'FAIL: rc={result.returncode} out={result.stdout} err={result.stderr}')
" 2>&1) || true

if echo "$TESTS" | grep -q "^PASS"; then
    pass "miniproject self-test passes inside container"
else
    fail "miniproject self-test" "$TESTS"
fi

echo "[16/$TOTAL] Workflow-team validation from host"
if python3 "$REPO_ROOT/tools/validation/check_workflow_teams.py" \
    --workflows-dir "$MINI/.archon/workflows" \
    --teams-dir "$TEAMS_DIR" 2>&1 | grep -q "passed"; then
    pass "workflow references valid against miniproject teams"
else
    fail "workflow-team validation" "references invalid"
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
