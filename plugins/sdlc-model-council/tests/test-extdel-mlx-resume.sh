#!/usr/bin/env bash
# Test harness for extdel.sh's mlx (Path B, local MLX) adapter. Exercises
# extdel.sh entirely against a MOCK `mlx-chat` client placed first on PATH —
# no real mlx_lm.server, no model weights, no Apple-Silicon hardware needed,
# and no API quota spent. Bash-3.2-safe (no associative arrays, no ${var,,}),
# matching extdel.sh's own target shell.
#
# Run: bash plugins/sdlc-model-council/tests/test-extdel-mlx-resume.sh
#
# MLX-specific behaviors covered on top of the shared engine lifecycle:
#   - the adapter resolves `mlx-chat` from PATH (where the mock lives);
#   - preflight passes with no real server (the mock --probe exits 0);
#   - the stateless server has no session id, so the adapter SYNTHESIZES a
#     deterministic `mlx-conv-<handle>` id on turn 1, and a resume turn reuses
#     it (never NO_SESSION) and is passed the history dir + turn number;
#   - DF2: an exit-0-but-empty answer reports NO_OUTPUT, never a false SUCCESS.

set -u

THIS_DIR="$(cd "$(dirname "$0")" && pwd -P)"
PLUGIN_ROOT="$(cd "$THIS_DIR/.." && pwd -P)"
REPO_ROOT="$(cd "$PLUGIN_ROOT/../.." && pwd -P)"
EXTDEL="$PLUGIN_ROOT/scripts/extdel.sh"
MOCK_BIN="$THIS_DIR/fixtures/mock-bin"

mkdir -p "$REPO_ROOT/tmp"
TESTROOT="$(mktemp -d "$REPO_ROOT/tmp/extdel-mlx-test.XXXXXX")"
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
extract_field() {
  printf '%s\n' "$1" | grep -m1 "^- $2:" | sed -E "s/^- $2:[[:space:]]*//" | awk '{print $1}'
}
run_extdel() { PATH="$MOCK_BIN:$PATH" "$EXTDEL" "$@"; }
poll_until_terminal() {
  handle="$1"; max="$2"; n=0
  while [ "$n" -lt "$max" ]; do
    out=$(run_extdel status "$handle" --wait-s 2)
    st=$(extract_field "$out" "Status")
    case "$st" in
      RUNNING) ;;
      *) printf '%s' "$out"; return 0 ;;
    esac
    n=$((n + 2))
  done
  printf '%s' "$out"; return 0
}

echo "=== extdel.sh mlx (Path B) adapter test suite ==="
echo "TESTROOT=$TESTROOT"
echo
cd "$TESTROOT" || exit 1

# ---------------------------------------------------------------------------
# 1. Fresh start -> SUCCESS, answer captured, synthesized session id.
# ---------------------------------------------------------------------------
echo "--- 1. fresh start -> SUCCESS + synthesized session id ---"
OUT1=$(run_extdel start --cli mlx --model mlx-community/Qwen2.5-Coder-7B-Instruct-4bit --prompt "hello mlx" --posture read-only)
assert_contains "$OUT1" "Status: RUNNING" "start returns RUNNING immediately"
HANDLE1=$(extract_field "$OUT1" "Handle")
if [ -n "$HANDLE1" ] && [ -d "./tmp/model-council/$HANDLE1" ]; then
  pass "handle directory created: $HANDLE1"
else
  fail "handle directory NOT created (handle='$HANDLE1')"
fi
META_CLI=$(jq -r '.cli' "./tmp/model-council/$HANDLE1/meta.json" 2>/dev/null)
[ "$META_CLI" = "mlx" ] && pass "meta.json cli=mlx" || fail "meta.json cli was '$META_CLI'"

FINAL1=$(poll_until_terminal "$HANDLE1" 12)
assert_contains "$FINAL1" "Status: SUCCESS" "turn 1 reaches SUCCESS"
SLICE1=$(run_extdel slice "$HANDLE1")
assert_contains "$SLICE1" "mock answer for: hello mlx (turn 1)" "answer captured from the mock client"

CAPTURED_SID=$(jq -r '.session_id' "./tmp/model-council/$HANDLE1/meta.json" 2>/dev/null)
[ "$CAPTURED_SID" = "mlx-conv-$HANDLE1" ] && pass "synthesized session id = mlx-conv-<handle>" || fail "session_id was '$CAPTURED_SID' (expected mlx-conv-$HANDLE1)"
[ -f "./tmp/model-council/$HANDLE1/session.id" ] && pass "session.id file written" || fail "session.id file missing"
echo

# ---------------------------------------------------------------------------
# 2. Resume reuses the synthesized session id (never NO_SESSION) and passes
#    the history dir + turn number to the client (mock echoes the turn).
# ---------------------------------------------------------------------------
echo "--- 2. resume (turn 2) reuses session, passes history/turn ---"
OUT2=$(run_extdel prompt "$HANDLE1" --prompt "second mlx turn")
assert_contains "$OUT2" "Status: RUNNING" "resume turn 2 submitted (not NO_SESSION)"
assert_not_contains "$OUT2" "NO_SESSION" "resume did not fail with NO_SESSION"
FINAL2=$(poll_until_terminal "$HANDLE1" 12)
assert_contains "$FINAL2" "Status: SUCCESS" "resume turn 2 completes"
assert_contains "$FINAL2" "Turn: 2" "resume reports turn 2"
SLICE2=$(run_extdel slice "$HANDLE1")
assert_contains "$SLICE2" "mock answer for: second mlx turn (turn 2)" "turn-2 client received --turn 2"
SID_AFTER=$(jq -r '.session_id' "./tmp/model-council/$HANDLE1/meta.json" 2>/dev/null)
[ "$SID_AFTER" = "mlx-conv-$HANDLE1" ] && pass "session id unchanged across resume" || fail "session id changed to '$SID_AFTER'"
echo

# ---------------------------------------------------------------------------
# 3. Pinned-posture refusal (engine-level, backend-agnostic).
# ---------------------------------------------------------------------------
echo "--- 3. pinned-posture refusal ---"
REFUSED=$(run_extdel prompt "$HANDLE1" --prompt "turn3 attempt" --posture workspace)
assert_contains "$REFUSED" "Status: ERROR" "posture mismatch without --steal is refused"
assert_contains "$REFUSED" "differs from this handle's pinned posture" "refusal explains the pinned-posture mismatch"
POSTURE_AFTER=$(jq -r '.posture' "./tmp/model-council/$HANDLE1/meta.json" 2>/dev/null)
[ "$POSTURE_AFTER" = "read-only" ] && pass "pinned posture unchanged after refusal" || fail "pinned posture mutated to '$POSTURE_AFTER'"
echo

# ---------------------------------------------------------------------------
# 4. DF2: exit-0-but-empty answer -> NO_OUTPUT, never a false SUCCESS.
# ---------------------------------------------------------------------------
echo "--- 4. DF2: exit-0-but-empty -> NO_OUTPUT ---"
OUT4=$(MOCK_MLX_EMPTY=1 run_extdel start --cli mlx --model m --prompt "will produce nothing" --posture read-only)
HANDLE4=$(extract_field "$OUT4" "Handle")
FINAL4=$(poll_until_terminal "$HANDLE4" 12)
assert_contains "$FINAL4" "Status: NO_OUTPUT" "exit-0 with empty answer reports NO_OUTPUT"
assert_not_contains "$FINAL4" "Status: SUCCESS" "exit-0-but-empty is never SUCCESS"
echo

# ---------------------------------------------------------------------------
# 5. MOCK_MLX_FAIL -> FAILURE, never SUCCESS.
# ---------------------------------------------------------------------------
echo "--- 5. induced failure -> FAILURE ---"
OUT5=$(MOCK_MLX_FAIL=1 run_extdel start --cli mlx --model m --prompt "boom" --posture read-only)
HANDLE5=$(extract_field "$OUT5" "Handle")
FINAL5=$(poll_until_terminal "$HANDLE5" 12)
assert_contains "$FINAL5" "Status: FAILURE" "MOCK_MLX_FAIL=1 reports FAILURE"
assert_not_contains "$FINAL5" "Status: SUCCESS" "failed turn does not report SUCCESS"
echo

# ---------------------------------------------------------------------------
# 6. Timeout path -> TIMEOUT, exit 124, lock released.
# ---------------------------------------------------------------------------
echo "--- 6. timeout path ---"
OUT6=$(MOCK_MLX_SLEEP=8 run_extdel start --cli mlx --model m --prompt "slow" --posture read-only --timeout-s 2)
HANDLE6=$(extract_field "$OUT6" "Handle")
FINAL6=$(poll_until_terminal "$HANDLE6" 15)
assert_contains "$FINAL6" "Status: TIMEOUT" "a turn exceeding --timeout-s reports TIMEOUT"
CODE6=$(cat "./tmp/model-council/$HANDLE6/turn-001.exit.code" 2>/dev/null | tr -d '[:space:]')
[ "$CODE6" = "124" ] && pass "timeout exit code is 124" || fail "timeout exit code was '$CODE6'"
[ -d "./tmp/model-council/$HANDLE6/.turn-lock" ] && fail "turn-lock present after timeout" || pass "turn-lock released after timeout"
echo

# ---------------------------------------------------------------------------
# 7. stop cleans up.
# ---------------------------------------------------------------------------
echo "--- 7. stop ---"
STOP_OUT=$(run_extdel stop "$HANDLE1")
assert_contains "$STOP_OUT" "STOPPED: $HANDLE1" "stop reports the handle as stopped"
CLOSED=$(jq -r '.closed' "./tmp/model-council/$HANDLE1/meta.json" 2>/dev/null)
[ "$CLOSED" != "null" ] && [ -n "$CLOSED" ] && pass "meta.json.closed timestamp set" || fail "meta.json.closed was '$CLOSED'"
echo

echo "=== Results: $PASS passed, $FAIL failed ==="
[ "$FAIL" -eq 0 ]
