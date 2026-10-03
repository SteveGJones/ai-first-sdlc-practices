#!/usr/bin/env bash
# Test harness for `extdel.sh list-backends` (issue #232, migration step 4
# — see docs/superpowers/specs/2026-07-24-sdlc-model-council-design.md
# §3.2/§4.2). Exercises list-backends entirely against MOCK `codex`/`agy`
# binaries on PATH and a FAKE $HOME/.claude/plugins/installed_plugins.json
# (via a HOME override to a throwaway test dir) — the real codex/agy CLIs
# and the real ~/.claude manifest are never touched, so this never spends
# API quota and never depends on what happens to be installed on the
# machine running the suite. Bash-3.2-safe, matching extdel.sh's own
# target shell.
#
# Run: bash plugins/sdlc-model-council/tests/test-list-backends.sh

set -u

THIS_DIR="$(cd "$(dirname "$0")" && pwd -P)"
PLUGIN_ROOT="$(cd "$THIS_DIR/.." && pwd -P)"
REPO_ROOT="$(cd "$PLUGIN_ROOT/../.." && pwd -P)"
EXTDEL="$PLUGIN_ROOT/scripts/extdel.sh"
MOCK_BIN="$THIS_DIR/fixtures/mock-bin"

# Repo rule: ./tmp, never /tmp — even for scratch test roots.
mkdir -p "$REPO_ROOT/tmp"
TESTROOT="$(mktemp -d "$REPO_ROOT/tmp/list-backends-test.XXXXXX")"
trap 'rm -rf "$TESTROOT"' EXIT

PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); printf 'PASS: %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf 'FAIL: %s\n' "$1"; }

assert_contains() {
  case "$1" in
    *"$2"*) pass "$3" ;;
    *) fail "$3 (expected to find: [$2])
--- actual output ---
$1
---------------------" ;;
  esac
}

assert_not_contains() {
  case "$1" in
    *"$2"*) fail "$3 (did NOT expect to find: [$2])
--- actual output ---
$1
---------------------" ;;
    *) pass "$3" ;;
  esac
}

run_list_backends() {
  # run_list_backends <FAKE_HOME> [extra args...]
  fh="$1"; shift
  PATH="$MOCK_BIN:$PATH" HOME="$fh" "$EXTDEL" list-backends "$@"
}

echo "=== extdel.sh list-backends test suite ==="
echo "TESTROOT=$TESTROOT"
echo

cd "$TESTROOT" || exit 1

CODEX_KEY="codex@openai-codex"
AGY_KEY="antigravity@antigravity-for-claude-code"

# ---------------------------------------------------------------------------
# 1. sibling installed — fake manifest carries BOTH sibling keys
# ---------------------------------------------------------------------------
echo "--- 1. sibling installed (both codex + agy sibling plugins present) ---"
HOME1="$TESTROOT/home-installed"
mkdir -p "$HOME1/.claude/plugins" "$HOME1/.gemini/antigravity-cli"
cat > "$HOME1/.claude/plugins/installed_plugins.json" <<EOF
{"version":2,"plugins":{"$CODEX_KEY":["1.0.0"],"$AGY_KEY":["1.0.0"]}}
EOF

OUT1=$(run_list_backends "$HOME1")
assert_contains "$OUT1" "codex" "table lists the codex backend"
assert_contains "$OUT1" "agy" "table lists the agy backend"

# codex row: installed=yes (mock codex on PATH), sibling=installed
CODEX_LINE1=$(printf '%s\n' "$OUT1" | grep '^codex ')
assert_contains "$CODEX_LINE1" "yes" "codex row shows installed=yes (mock codex on PATH)"
assert_contains "$CODEX_LINE1" "direct-cli" "codex row shows kind=direct-cli"
assert_contains "$CODEX_LINE1" "read-only:hard" "codex row shows read-only posture fidelity=hard"
assert_contains "$CODEX_LINE1" "workspace:hard" "codex row shows workspace posture fidelity=hard"
assert_contains "$CODEX_LINE1" "dangerous:none" "codex row shows dangerous posture fidelity=none"
assert_contains "$CODEX_LINE1" "installed" "codex row's sibling column reports installed"

# agy row: installed=yes (mock agy on PATH), sibling=installed
AGY_LINE1=$(printf '%s\n' "$OUT1" | grep '^agy ')
assert_contains "$AGY_LINE1" "yes" "agy row shows installed=yes (mock agy on PATH)"
assert_contains "$AGY_LINE1" "direct-cli" "agy row shows kind=direct-cli"
assert_contains "$AGY_LINE1" "read-only:allow-list" "agy row shows read-only posture fidelity=allow-list"
assert_contains "$AGY_LINE1" "workspace:allow-list" "agy row shows workspace posture fidelity=allow-list"
assert_contains "$AGY_LINE1" "dangerous:none" "agy row shows dangerous posture fidelity=none"
assert_contains "$AGY_LINE1" "installed" "agy row's sibling column reports installed"
echo

# ---------------------------------------------------------------------------
# 2. sibling absent — fake manifest exists (version 2) but has neither key
# ---------------------------------------------------------------------------
echo "--- 2. sibling absent (valid v2 manifest, no matching keys) ---"
HOME2="$TESTROOT/home-absent"
mkdir -p "$HOME2/.claude/plugins" "$HOME2/.gemini/antigravity-cli"
cat > "$HOME2/.claude/plugins/installed_plugins.json" <<EOF
{"version":2,"plugins":{"some-other-plugin@some-marketplace":["1.0.0"]}}
EOF

OUT2=$(run_list_backends "$HOME2")
CODEX_LINE2=$(printf '%s\n' "$OUT2" | grep '^codex ')
AGY_LINE2=$(printf '%s\n' "$OUT2" | grep '^agy ')
assert_contains "$CODEX_LINE2" "absent" "codex row's sibling column reports absent when the manifest is valid but lacks the key"
assert_contains "$AGY_LINE2" "absent" "agy row's sibling column reports absent when the manifest is valid but lacks the key"
assert_not_contains "$CODEX_LINE2" "unknown" "codex sibling is never 'unknown' when a valid manifest positively lacks the key"
assert_not_contains "$AGY_LINE2" "unknown" "agy sibling is never 'unknown' when a valid manifest positively lacks the key"
echo

# ---------------------------------------------------------------------------
# 3. malformed manifest -> unknown, never a confident "absent" from a
#    failed probe (and no cache-tree fallback configured in this HOME
#    either, so the fallback also cannot produce a confident answer).
# ---------------------------------------------------------------------------
echo "--- 3. malformed manifest -> unknown (never a false 'absent') ---"
HOME3="$TESTROOT/home-malformed"
mkdir -p "$HOME3/.claude/plugins" "$HOME3/.gemini/antigravity-cli"
printf 'this is not valid json{{{' > "$HOME3/.claude/plugins/installed_plugins.json"

OUT3=$(run_list_backends "$HOME3")
CODEX_LINE3=$(printf '%s\n' "$OUT3" | grep '^codex ')
AGY_LINE3=$(printf '%s\n' "$OUT3" | grep '^agy ')
assert_contains "$CODEX_LINE3" "unknown" "codex row's sibling column reports unknown for a malformed manifest"
assert_contains "$AGY_LINE3" "unknown" "agy row's sibling column reports unknown for a malformed manifest"

# Same for a manifest that parses but isn't version 2.
HOME3B="$TESTROOT/home-wrong-version"
mkdir -p "$HOME3B/.claude/plugins" "$HOME3B/.gemini/antigravity-cli"
cat > "$HOME3B/.claude/plugins/installed_plugins.json" <<EOF
{"version":1,"plugins":{"$CODEX_KEY":["1.0.0"]}}
EOF
OUT3B=$(run_list_backends "$HOME3B")
CODEX_LINE3B=$(printf '%s\n' "$OUT3B" | grep '^codex ')
assert_contains "$CODEX_LINE3B" "unknown" "a non-version-2 manifest is treated as unusable (sibling=unknown), not misread"
echo

# ---------------------------------------------------------------------------
# 4. no manifest at all, but a cache-tree fallback exists -> a confident
#    installed/absent answer from the fallback, not unknown.
# ---------------------------------------------------------------------------
echo "--- 4. cache-tree fallback (no manifest file at all) ---"
HOME4="$TESTROOT/home-cache-fallback"
mkdir -p "$HOME4/.claude/plugins/cache/openai-codex/codex/1.0.0" "$HOME4/.gemini/antigravity-cli"
# No installed_plugins.json written at all in this HOME.

OUT4=$(run_list_backends "$HOME4")
CODEX_LINE4=$(printf '%s\n' "$OUT4" | grep '^codex ')
AGY_LINE4=$(printf '%s\n' "$OUT4" | grep '^agy ')
assert_contains "$CODEX_LINE4" "installed" "codex sibling falls back to the cache-tree scan and finds it (installed)"
assert_contains "$AGY_LINE4" "absent" "agy sibling falls back to the cache-tree scan and does NOT find it (absent)"
echo

# ---------------------------------------------------------------------------
# 5. --json shape: one row per backend, descriptor + probe fields present
# ---------------------------------------------------------------------------
echo "--- 5. --json output shape ---"
JSON1=$(run_list_backends "$HOME1" --json)
if printf '%s' "$JSON1" | jq -e 'type == "array"' >/dev/null 2>&1; then
  pass "--json emits a JSON array"
else
  fail "--json did not emit a JSON array: $JSON1"
fi

CODEX_JSON_ID=$(printf '%s' "$JSON1" | jq -r '.[] | select(.descriptor.id=="codex") | .descriptor.id' 2>/dev/null)
[ "$CODEX_JSON_ID" = "codex" ] && pass "--json includes the codex descriptor" || fail "--json missing the codex descriptor entry"

CODEX_JSON_INSTALLED=$(printf '%s' "$JSON1" | jq -r '.[] | select(.descriptor.id=="codex") | .probe.installed' 2>/dev/null)
[ "$CODEX_JSON_INSTALLED" = "yes" ] && pass "--json reports codex probe.installed=yes" || fail "--json codex probe.installed was '$CODEX_JSON_INSTALLED'"

CODEX_JSON_SIBLING=$(printf '%s' "$JSON1" | jq -r '.[] | select(.descriptor.id=="codex") | .probe.sibling' 2>/dev/null)
[ "$CODEX_JSON_SIBLING" = "installed" ] && pass "--json reports codex probe.sibling=installed" || fail "--json codex probe.sibling was '$CODEX_JSON_SIBLING'"
echo

# ---------------------------------------------------------------------------
# 6. --probe-auth: codex mock always authenticates OK; agy mock has no
#    real ~/.gemini/antigravity-cli under a HOME that never created one.
# ---------------------------------------------------------------------------
echo "--- 6. --probe-auth ---"
OUT6=$(run_list_backends "$HOME1" --probe-auth)
CODEX_LINE6=$(printf '%s\n' "$OUT6" | grep '^codex ')
assert_contains "$CODEX_LINE6" "ok" "codex --probe-auth reports ok (mock codex login status exits 0)"

HOME6B="$TESTROOT/home-agy-uninitialized"
mkdir -p "$HOME6B/.claude/plugins"
cat > "$HOME6B/.claude/plugins/installed_plugins.json" <<EOF
{"version":2,"plugins":{}}
EOF
# Deliberately no ~/.gemini/antigravity-cli directory in this HOME.
OUT6B=$(run_list_backends "$HOME6B" --probe-auth)
AGY_LINE6B=$(printf '%s\n' "$OUT6B" | grep '^agy ')
assert_contains "$AGY_LINE6B" "fail" "agy --probe-auth reports fail when ~/.gemini/antigravity-cli does not exist"

# Without --probe-auth, no auth probe should run at all (auth column
# shows the not-probed marker, never ok/fail).
OUT6C=$(run_list_backends "$HOME6B")
AGY_LINE6C=$(printf '%s\n' "$OUT6C" | grep '^agy ')
assert_not_contains "$AGY_LINE6C" " fail " "without --probe-auth, agy's auth column is not 'fail' (no probe ran)"
echo

# ---------------------------------------------------------------------------
# 7. list-backends is pure read-only: no ./tmp/model-council/<handle>
#    directory is created by any of the runs above.
# ---------------------------------------------------------------------------
echo "--- 7. read-only: no handle/state created ---"
if [ -d "./tmp/model-council" ]; then
  handle_dirs=$(find "./tmp/model-council" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')
else
  handle_dirs=0
fi
[ "$handle_dirs" -eq 0 ] && pass "no handle directories were created by any list-backends invocation" || fail "list-backends created $handle_dirs handle director(ies) — expected 0"
echo

echo "=== Results: $PASS passed, $FAIL failed ==="
[ "$FAIL" -eq 0 ]
