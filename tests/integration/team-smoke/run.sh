#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
PLUGIN_DIR="$REPO_ROOT/plugins/sdlc-workflows"

echo "=== Phase 2 Team Smoke Test ==="
echo ""

PASS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0
TOTAL=7

pass() { echo "  PASS: $1"; PASS_COUNT=$((PASS_COUNT + 1)); }
fail() { echo "  FAIL: $1"; FAIL_COUNT=$((FAIL_COUNT + 1)); }
skip() { echo "  SKIP: $1"; SKIP_COUNT=$((SKIP_COUNT + 1)); }

# Check 1: Manifest validates
echo "[1/$TOTAL] Manifest validation"
if python3 "$PLUGIN_DIR/scripts/validate_team_manifest.py" \
    "$SCRIPT_DIR/manifest.yaml" 2>/dev/null; then
    pass "manifest validates"
else
    fail "manifest validation failed"
fi

# Check 2: CLAUDE.md generator works
echo "[2/$TOTAL] CLAUDE.md generation"
CLAUDE_MD_OUTPUT="$SCRIPT_DIR/.generated-claude.md"
if python3 -c "
import sys, yaml
sys.path.insert(0, '$PLUGIN_DIR/scripts')
from generate_team_claude_md import generate
with open('$SCRIPT_DIR/manifest.yaml') as f:
    manifest = yaml.safe_load(f)
result = generate(manifest, {}, {})
with open('$CLAUDE_MD_OUTPUT', 'w') as f:
    f.write(result)
print('OK')
" 2>/dev/null | grep -q "OK"; then
    if grep -q "smoke-review-team" "$CLAUDE_MD_OUTPUT" 2>/dev/null; then
        pass "CLAUDE.md generated with team name"
    else
        fail "CLAUDE.md missing team name"
    fi
    rm -f "$CLAUDE_MD_OUTPUT"
else
    fail "CLAUDE.md generation script failed"
fi

# Check 3: Workflow-team validator works
echo "[3/$TOTAL] Workflow-team validation"
if python3 "$REPO_ROOT/tools/validation/check_workflow_teams.py" \
    --workflows-dir "$SCRIPT_DIR" \
    --teams-dir "$SCRIPT_DIR" 2>/dev/null; then
    pass "workflow-team references valid"
else
    fail "workflow-team validation failed"
fi

# Docker-dependent checks (4-7)
DOCKER_AVAILABLE=false
if docker info >/dev/null 2>&1; then
    DOCKER_AVAILABLE=true
fi

# Check 4: Base image exists
echo "[4/$TOTAL] Base image exists"
if [ "$DOCKER_AVAILABLE" = "true" ]; then
    if docker image inspect sdlc-worker:base >/dev/null 2>&1; then
        pass "sdlc-worker:base exists"
    else
        skip "sdlc-worker:base not found (run build-base.sh to enable)"
    fi
else
    skip "Docker not available"
fi

# Check 5: Full image exists
echo "[5/$TOTAL] Full image exists"
if [ "$DOCKER_AVAILABLE" = "true" ]; then
    if docker image inspect sdlc-worker:full >/dev/null 2>&1; then
        pass "sdlc-worker:full exists"
    else
        skip "sdlc-worker:full not found (run build-full.sh to enable)"
    fi
else
    skip "Docker not available"
fi

# Check 6: Team image builds (requires base + full)
echo "[6/$TOTAL] Team image builds from manifest"
if [ "$DOCKER_AVAILABLE" = "true" ] && \
   docker image inspect sdlc-worker:base >/dev/null 2>&1 && \
   docker image inspect sdlc-worker:full >/dev/null 2>&1; then
    mkdir -p "$REPO_ROOT/.archon/teams"
    cp "$SCRIPT_DIR/manifest.yaml" "$REPO_ROOT/.archon/teams/smoke-review-team.yaml"
    if bash "$PLUGIN_DIR/docker/build-team.sh" smoke-review-team 2>/dev/null; then
        pass "sdlc-worker:smoke-review-team built"
    else
        fail "team image build failed"
    fi
    rm -f "$REPO_ROOT/.archon/teams/smoke-review-team.yaml"
    rmdir "$REPO_ROOT/.archon/teams" 2>/dev/null || true
    rmdir "$REPO_ROOT/.archon" 2>/dev/null || true
else
    skip "base/full images not available"
fi

# Check 7: Plugins directory is read-only in team image
echo "[7/$TOTAL] Plugins directory is read-only"
if [ "$DOCKER_AVAILABLE" = "true" ] && \
   docker image inspect sdlc-worker:smoke-review-team >/dev/null 2>&1; then
    # S-M-2: --cap-drop + no-new-privileges match hardened production docker runs.
    RO_CHECK=$(docker run --rm \
        --cap-drop ALL --security-opt no-new-privileges \
        --entrypoint /bin/bash sdlc-worker:smoke-review-team \
        -c "touch /home/sdlc/.claude/plugins/test-write" 2>&1 || true)
    if echo "$RO_CHECK" | grep -qi "read-only\|permission denied\|cannot touch"; then
        pass "plugins directory is read-only"
    else
        fail "plugins directory is writable — runtime install bypass possible"
    fi
else
    skip "team image not available"
fi

# Report
echo ""
echo "=== Results: $PASS_COUNT pass, $FAIL_COUNT fail, $SKIP_COUNT skip (of $TOTAL) ==="
if [ "$FAIL_COUNT" -eq 0 ]; then
    echo "Phase 2 smoke test: ALL PASS (${SKIP_COUNT} skipped — build Docker images to enable)"
    exit 0
else
    echo "Phase 2 smoke test: FAILURES DETECTED"
    exit 1
fi
