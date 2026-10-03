#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
PLUGIN_DIR="$REPO_ROOT/plugins/sdlc-workflows"
SCRIPTS_DIR="$PLUGIN_DIR/scripts"

echo "=== Phase 3 Workforce Management Smoke Test ==="
echo ""

PASS_COUNT=0
FAIL_COUNT=0
TOTAL=8

pass() { echo "  PASS: $1"; PASS_COUNT=$((PASS_COUNT + 1)); }
fail() { echo "  FAIL: $1 — $2"; FAIL_COUNT=$((FAIL_COUNT + 1)); }

# Create a self-contained temp workspace
WORK_DIR=$(mktemp -d "${TMPDIR:-/tmp}/workforce-smoke.XXXXXX")
trap 'rm -rf "$WORK_DIR"' EXIT

# ---------------------------------------------------------------------------
# Fixtures: a fake plugin environment
# ---------------------------------------------------------------------------
PLUGIN_A="$WORK_DIR/cache/mkt/plugin-alpha/1.0.0"
mkdir -p "$PLUGIN_A/agents" "$PLUGIN_A/skills/lint" "$PLUGIN_A/.claude-plugin"
cat > "$PLUGIN_A/agents/architect.md" <<'AGENT'
---
name: architect
description: System architecture design
---
Body text.
AGENT
cat > "$PLUGIN_A/agents/reviewer.md" <<'AGENT'
---
name: reviewer
description: Code review specialist
---
Body text.
AGENT
cat > "$PLUGIN_A/skills/lint/SKILL.md" <<'SKILL'
---
name: lint
description: Run linter
---
Instructions.
SKILL
echo '{}' > "$PLUGIN_A/.claude-plugin/plugin.json"

PLUGIN_B="$WORK_DIR/cache/mkt/plugin-beta/2.0.0"
mkdir -p "$PLUGIN_B/agents" "$PLUGIN_B/.claude-plugin"
cat > "$PLUGIN_B/agents/tester.md" <<'AGENT'
---
name: tester
description: Test coverage analysis
---
Body text.
AGENT
echo '{}' > "$PLUGIN_B/.claude-plugin/plugin.json"

# installed_plugins.json
cat > "$WORK_DIR/installed_plugins.json" <<JSON
{
  "plugin-alpha@mkt": {"name": "plugin-alpha", "installPath": "$PLUGIN_A"},
  "plugin-beta@mkt": {"name": "plugin-beta", "installPath": "$PLUGIN_B"}
}
JSON

# Team manifests
TEAMS_DIR="$WORK_DIR/teams"
mkdir -p "$TEAMS_DIR"
cat > "$TEAMS_DIR/dev-team.yaml" <<'YAML'
schema_version: "1.0"
name: dev-team
description: Development team for smoke test.
status: active
created: "2026-04-10T12:00:00"
updated: "2026-04-12T12:00:00"
image_built: "2026-04-10T12:00:00"
plugins:
  - plugin-alpha
agents:
  - plugin-alpha:architect
skills:
  - plugin-alpha:lint
context: []
YAML

cat > "$TEAMS_DIR/test-team.yaml" <<'YAML'
schema_version: "1.0"
name: test-team
description: Testing team for smoke test.
status: active
created: "2026-04-10T12:00:00"
updated: "2026-04-11T12:00:00"
plugins:
  - plugin-beta
agents:
  - plugin-beta:tester
skills: []
context: []
YAML

# Workflow YAML
WF_DIR="$WORK_DIR/workflows"
mkdir -p "$WF_DIR"
cat > "$WF_DIR/smoke-pipeline.yaml" <<'YAML'
name: smoke-pipeline
nodes:
  - id: implement
    command: implement
    image: sdlc-worker:dev-team
  - id: test
    command: test
    image: sdlc-worker:test-team
    team_extend:
      agents:
        - plugin-alpha:reviewer
YAML

# Override log
LOGS_DIR="$WORK_DIR/logs"
mkdir -p "$LOGS_DIR"

# ---------------------------------------------------------------------------
# Check 1: team_inventory discovers agents from plugins
# ---------------------------------------------------------------------------
echo "[1/$TOTAL] Plugin inventory discovery"
INVENTORY=$(python3 -c "
import sys, json
sys.path.insert(0, '$SCRIPTS_DIR')
from team_inventory import discover_all
from pathlib import Path
result = discover_all(Path('$WORK_DIR/installed_plugins.json'))
print(json.dumps(result))
" 2>&1) || true

if echo "$INVENTORY" | python3 -c "
import sys, json
d = json.load(sys.stdin)
assert 'plugin-alpha' in d, 'plugin-alpha missing'
assert 'plugin-beta' in d, 'plugin-beta missing'
assert len(d['plugin-alpha']['agents']) == 2, 'expected 2 agents in alpha'
assert len(d['plugin-alpha']['skills']) == 1, 'expected 1 skill in alpha'
assert len(d['plugin-beta']['agents']) == 1, 'expected 1 agent in beta'
print('OK')
" 2>/dev/null | grep -q "OK"; then
    pass "inventory discovers 3 agents and 1 skill across 2 plugins"
else
    fail "inventory discovery" "unexpected output: $INVENTORY"
fi

# ---------------------------------------------------------------------------
# Check 2: available_but_not_included finds missing agents
# ---------------------------------------------------------------------------
echo "[2/$TOTAL] Available-but-not-included detection"
AVAILABLE=$(python3 -c "
import sys, json
sys.path.insert(0, '$SCRIPTS_DIR')
from team_inventory import available_but_not_included
from pathlib import Path
result = available_but_not_included(
    installed_json=Path('$WORK_DIR/installed_plugins.json'),
    team_plugins=['plugin-alpha'],
    team_agents=['plugin-alpha:architect'],
)
print(json.dumps(result))
" 2>&1) || true

if echo "$AVAILABLE" | python3 -c "
import sys, json
d = json.load(sys.stdin)
names = {a['qualified'] for a in d['agents']}
assert 'plugin-alpha:reviewer' in names, 'reviewer should be available'
assert 'plugin-alpha:architect' not in names, 'architect should be excluded'
print('OK')
" 2>/dev/null | grep -q "OK"; then
    pass "correctly identifies reviewer as available but not included"
else
    fail "available-but-not-included" "unexpected output: $AVAILABLE"
fi

# ---------------------------------------------------------------------------
# Check 3: fleet report assembles from manifests + workflows
# ---------------------------------------------------------------------------
echo "[3/$TOTAL] Fleet status report"
REPORT=$(python3 -c "
import sys, json
sys.path.insert(0, '$SCRIPTS_DIR')
from teams_status_report import fleet_report
from pathlib import Path
result = fleet_report(Path('$TEAMS_DIR'), Path('$WF_DIR'))
print(json.dumps(result, default=str))
" 2>&1) || true

if echo "$REPORT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
assert d['team_count'] == 2, f'expected 2 teams, got {d[\"team_count\"]}'
teams = {t['name']: t for t in d['teams']}
assert teams['dev-team']['staleness'] == 'stale', 'dev-team should be stale'
assert teams['test-team']['staleness'] == 'not_built', 'test-team should be not_built'
assert teams['dev-team']['workflow_count'] == 1, 'dev-team in 1 workflow'
print('OK')
" 2>/dev/null | grep -q "OK"; then
    pass "fleet report: 2 teams, correct staleness, workflow mapping"
else
    fail "fleet report" "unexpected output: $REPORT"
fi

# ---------------------------------------------------------------------------
# Check 4: coaching signals produce correct tiers
# ---------------------------------------------------------------------------
echo "[4/$TOTAL] Coaching signal tiers"
SIGNALS=$(python3 -c "
import sys, json
sys.path.insert(0, '$SCRIPTS_DIR')
from teams_status_report import fleet_report
from coaching_signals import analyse_fleet
from pathlib import Path
report = fleet_report(Path('$TEAMS_DIR'), Path('$WF_DIR'))
result = analyse_fleet(report['teams'])
print(json.dumps(result))
" 2>&1) || true

if echo "$SIGNALS" | python3 -c "
import sys, json
d = json.load(sys.stdin)
critical_types = {s['type'] for s in d['critical']}
advisory_types = {s['type'] for s in d['advisory']}
assert 'not_built' in critical_types, 'test-team not_built should be critical'
assert 'stale_image' in advisory_types, 'dev-team stale should be advisory'
print('OK')
" 2>/dev/null | grep -q "OK"; then
    pass "signals: not_built=critical, stale_image=advisory"
else
    fail "coaching signals" "unexpected output: $SIGNALS"
fi

# ---------------------------------------------------------------------------
# Check 5: override logger writes and reads
# ---------------------------------------------------------------------------
echo "[5/$TOTAL] Override logger round-trip"
OVERRIDE_LOG="$LOGS_DIR/overrides.jsonl"
ROUND_TRIP=$(python3 -c "
import sys, json
sys.path.insert(0, '$SCRIPTS_DIR')
from override_logger import log_override, read_overrides
from pathlib import Path
log_path = Path('$OVERRIDE_LOG')
log_override(log_path, 'dev-team', 'plugin-alpha:reviewer', 'smoke-pipeline', 'test')
log_override(log_path, 'dev-team', 'plugin-alpha:reviewer', 'smoke-pipeline', 'test')
log_override(log_path, 'dev-team', 'plugin-alpha:reviewer', 'smoke-pipeline', 'test')
entries = read_overrides(log_path)
print(json.dumps({'count': len(entries), 'agents': [e['agent'] for e in entries]}))
" 2>&1) || true

if echo "$ROUND_TRIP" | python3 -c "
import sys, json
d = json.load(sys.stdin)
assert d['count'] == 3, f'expected 3 entries, got {d[\"count\"]}'
assert all(a == 'plugin-alpha:reviewer' for a in d['agents']), 'wrong agent'
print('OK')
" 2>/dev/null | grep -q "OK"; then
    pass "override logger: 3 entries written and read back"
else
    fail "override logger" "unexpected output: $ROUND_TRIP"
fi

# ---------------------------------------------------------------------------
# Check 6: override signals detect frequent overrides
# ---------------------------------------------------------------------------
echo "[6/$TOTAL] Override coaching signal detection"
OVERRIDE_SIGNALS=$(python3 -c "
import sys, json
sys.path.insert(0, '$SCRIPTS_DIR')
from coaching_signals import analyse_overrides
from pathlib import Path
result = analyse_overrides(Path('$OVERRIDE_LOG'), threshold=3)
print(json.dumps(result))
" 2>&1) || true

if echo "$OVERRIDE_SIGNALS" | python3 -c "
import sys, json
d = json.load(sys.stdin)
assert len(d) == 1, f'expected 1 signal, got {len(d)}'
assert d[0]['type'] == 'frequent_override'
assert d[0]['tier'] == 'informational'
assert d[0]['agent'] == 'plugin-alpha:reviewer'
print('OK')
" 2>/dev/null | grep -q "OK"; then
    pass "frequent override signal: plugin-alpha:reviewer at threshold 3"
else
    fail "override signals" "unexpected output: $OVERRIDE_SIGNALS"
fi

# ---------------------------------------------------------------------------
# Check 7: team_extend validation passes for valid reference
# ---------------------------------------------------------------------------
echo "[7/$TOTAL] team_extend validation (valid reference)"
EXTEND_VALID=$(python3 -c "
import sys
sys.path.insert(0, '$REPO_ROOT/tools/validation')
sys.path.insert(0, '$SCRIPTS_DIR')
from pathlib import Path
import check_workflow_teams
errors = check_workflow_teams.validate(
    workflows_dir=Path('$WF_DIR'),
    teams_dir=Path('$TEAMS_DIR'),
    installed_json=Path('$WORK_DIR/installed_plugins.json'),
)
print(f'errors={len(errors)}')
for e in errors:
    print(f'  {e}')
" 2>&1) || true

if echo "$EXTEND_VALID" | grep -q "errors=0"; then
    pass "team_extend reference to plugin-alpha:reviewer validates"
else
    fail "team_extend valid" "expected 0 errors: $EXTEND_VALID"
fi

# ---------------------------------------------------------------------------
# Check 8: team_extend validation fails for bad reference
# ---------------------------------------------------------------------------
echo "[8/$TOTAL] team_extend validation (invalid reference)"
# Create a workflow with a bad team_extend reference
cat > "$WF_DIR/bad-extend.yaml" <<'YAML'
name: bad-extend
nodes:
  - id: impl
    command: impl
    image: sdlc-worker:dev-team
    team_extend:
      agents:
        - ghost-plugin:phantom-agent
YAML

EXTEND_BAD=$(python3 -c "
import sys
sys.path.insert(0, '$REPO_ROOT/tools/validation')
sys.path.insert(0, '$SCRIPTS_DIR')
from pathlib import Path
import check_workflow_teams
errors = check_workflow_teams.validate(
    workflows_dir=Path('$WF_DIR'),
    teams_dir=Path('$TEAMS_DIR'),
    installed_json=Path('$WORK_DIR/installed_plugins.json'),
)
# Filter to only bad-extend errors
bad = [e for e in errors if 'ghost-plugin' in e]
print(f'bad_errors={len(bad)}')
for e in bad:
    print(f'  {e}')
" 2>&1) || true

# Clean up the bad workflow so it doesn't pollute
rm -f "$WF_DIR/bad-extend.yaml"

if echo "$EXTEND_BAD" | grep -q "bad_errors=1"; then
    pass "team_extend reference to ghost-plugin:phantom-agent rejected"
else
    fail "team_extend invalid" "expected 1 error: $EXTEND_BAD"
fi

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
echo ""
echo "=== Results: $PASS_COUNT pass, $FAIL_COUNT fail (of $TOTAL) ==="
if [ "$FAIL_COUNT" -eq 0 ]; then
    echo "Phase 3 workforce management smoke test: ALL PASS"
    exit 0
else
    echo "Phase 3 workforce management smoke test: FAILURES DETECTED"
    exit 1
fi
