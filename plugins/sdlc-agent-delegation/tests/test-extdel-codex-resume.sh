#!/usr/bin/env bash
# Test harness for extdel.sh's codex-resume path (Stage 1 + Stage 2 of
# issue #232). Exercises extdel.sh entirely against a MOCK `codex` binary
# placed first on PATH — the real codex/agy CLIs are never invoked here,
# so this test never spends API quota. Bash-3.2-safe (no associative
# arrays, no `${var,,}`), matching extdel.sh's own target shell.
#
# Run: bash plugins/sdlc-agent-delegation/tests/test-extdel-codex-resume.sh
#
# A single real-CLI smoke test can be added later behind
# `if [ "${EXTDEL_LIVE:-0}" = "1" ]; then ... fi` — off by default, and
# none is included here per the task instructions (don't spend quota).

set -u

THIS_DIR="$(cd "$(dirname "$0")" && pwd -P)"
PLUGIN_ROOT="$(cd "$THIS_DIR/.." && pwd -P)"
REPO_ROOT="$(cd "$PLUGIN_ROOT/../.." && pwd -P)"
EXTDEL="$PLUGIN_ROOT/scripts/extdel.sh"
MOCK_BIN="$THIS_DIR/fixtures/mock-bin"

# Repo rule: ./tmp, never /tmp — even for scratch test roots.
mkdir -p "$REPO_ROOT/tmp"
TESTROOT="$(mktemp -d "$REPO_ROOT/tmp/extdel-test.XXXXXX")"
trap 'rm -rf "$TESTROOT"' EXIT

PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); printf 'PASS: %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf 'FAIL: %s\n' "$1"; }

backdate() {
  # backdate <path> — set mtime far enough in the past to clear
  # extdel.sh's lock-age reaper grace window (30s), portably across BSD
  # (macOS) and GNU touch.
  case "$(uname -s)" in
    Darwin|*BSD) touch -t "$(date -v-1H +%Y%m%d%H%M.%S)" "$1" ;;
    *) touch -d '1 hour ago' "$1" ;;
  esac
}

assert_contains() {
  # assert_contains <haystack> <needle> <description>
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
  # extract_field <block> <label>   — pulls "- <label>: VALUE" (first match)
  printf '%s\n' "$1" | grep -m1 "^- $2:" | sed -E "s/^- $2:[[:space:]]*//" | awk '{print $1}'
}

run_extdel() {
  PATH="$MOCK_BIN:$PATH" "$EXTDEL" "$@"
}

poll_until_terminal() {
  # poll_until_terminal <handle> <max_seconds> -> prints final status block
  handle="$1"; max="$2"
  n=0
  while [ "$n" -lt "$max" ]; do
    out=$(run_extdel status "$handle" --wait-s 2)
    st=$(extract_field "$out" "Status")
    case "$st" in
      RUNNING) ;;
      *) printf '%s' "$out"; return 0 ;;
    esac
    n=$((n + 2))
  done
  printf '%s' "$out"
  return 0
}

echo "=== extdel.sh codex-resume test suite ==="
echo "TESTROOT=$TESTROOT"
echo

cd "$TESTROOT" || exit 1

# ---------------------------------------------------------------------------
# 1. Handle creation
# ---------------------------------------------------------------------------
echo "--- 1. handle creation ---"
OUT1=$(MOCK_CODEX_SESSION_ID="11111111-1111-4111-8111-111111111111" run_extdel start --prompt "hello world" --posture read-only)
assert_contains "$OUT1" "Status: RUNNING" "start returns RUNNING immediately"
HANDLE1=$(extract_field "$OUT1" "Handle")
if [ -n "$HANDLE1" ] && [ -d "./tmp/agent-delegation/$HANDLE1" ]; then
  pass "handle directory created: $HANDLE1"
else
  fail "handle directory NOT created (handle='$HANDLE1')"
fi
if [ -f "./tmp/agent-delegation/$HANDLE1/meta.json" ] && [ -f "./tmp/agent-delegation/$HANDLE1/turn-001.prompt.txt" ]; then
  pass "meta.json and turn-001.prompt.txt exist"
else
  fail "meta.json or turn-001.prompt.txt missing"
fi
META_CLI=$(jq -r '.cli' "./tmp/agent-delegation/$HANDLE1/meta.json" 2>/dev/null)
META_POSTURE=$(jq -r '.posture' "./tmp/agent-delegation/$HANDLE1/meta.json" 2>/dev/null)
PROMPT_CONTENT=$(cat "./tmp/agent-delegation/$HANDLE1/turn-001.prompt.txt" 2>/dev/null)
[ "$META_CLI" = "codex" ] && pass "meta.json cli=codex" || fail "meta.json cli was '$META_CLI'"
[ "$META_POSTURE" = "read-only" ] && pass "meta.json posture=read-only" || fail "meta.json posture was '$META_POSTURE'"
[ "$PROMPT_CONTENT" = "hello world" ] && pass "turn-001.prompt.txt has the exact prompt text" || fail "prompt file content was '$PROMPT_CONTENT'"
echo

# ---------------------------------------------------------------------------
# 2. Submit-then-poll lifecycle + RUNNING -> SUCCESS transition
# ---------------------------------------------------------------------------
echo "--- 2. submit-then-poll lifecycle / RUNNING -> SUCCESS ---"
OUT2=$(MOCK_CODEX_SESSION_ID="22222222-2222-4222-8222-222222222222" MOCK_CODEX_SLEEP=2 run_extdel start --prompt "slow first turn" --posture read-only)
HANDLE2=$(extract_field "$OUT2" "Handle")
assert_contains "$OUT2" "Status: RUNNING" "turn2 handle starts RUNNING"

IMMEDIATE=$(run_extdel status "$HANDLE2" --wait-s 0)
assert_contains "$IMMEDIATE" "Status: RUNNING" "immediate zero-wait status still RUNNING (mock is sleeping)"

sleep 3
FINAL2=$(run_extdel status "$HANDLE2" --wait-s 5)
assert_contains "$FINAL2" "Status: SUCCESS" "status transitions to SUCCESS once the mock finishes"
assert_contains "$FINAL2" "Turn: 1" "SUCCESS report shows turn 1"
echo

# ---------------------------------------------------------------------------
# 3. Session-id capture from the mock event stream
# ---------------------------------------------------------------------------
echo "--- 3. session-id capture from event stream ---"
FINAL1=$(poll_until_terminal "$HANDLE1" 10)
assert_contains "$FINAL1" "Status: SUCCESS" "handle1 turn 1 reaches SUCCESS"
assert_contains "$FINAL1" "11111111-1111-4111-8111-111111111111" "captured session id matches the mock's session_id event"
CAPTURED_SID=$(jq -r '.session_id' "./tmp/agent-delegation/$HANDLE1/meta.json" 2>/dev/null)
[ "$CAPTURED_SID" = "11111111-1111-4111-8111-111111111111" ] && pass "meta.json.session_id persisted" || fail "meta.json.session_id was '$CAPTURED_SID'"
[ -f "./tmp/agent-delegation/$HANDLE1/session.id" ] && pass "session.id file written" || fail "session.id file missing"
echo

# ---------------------------------------------------------------------------
# 4. slice + truncation
# ---------------------------------------------------------------------------
echo "--- 4. slice ---"
SLICE_FULL=$(run_extdel slice "$HANDLE1")
assert_contains "$SLICE_FULL" "mock answer for: hello world" "slice returns the mock's last-message content"

SLICE_TRUNC=$(run_extdel slice "$HANDLE1" --max-chars 5)
assert_contains "$SLICE_TRUNC" "truncated" "slice --max-chars 5 truncates the answer"
FIRST_LINE_LEN=$(printf '%s' "$SLICE_TRUNC" | head -1 | awk '{print length}')
if [ "$FIRST_LINE_LEN" -le 5 ]; then
  pass "truncated first line is <= max-chars (was $FIRST_LINE_LEN)"
else
  fail "truncated first line exceeded max-chars (was $FIRST_LINE_LEN)"
fi
echo

# ---------------------------------------------------------------------------
# 5. Pinned-posture refusal
# ---------------------------------------------------------------------------
echo "--- 5. pinned-posture refusal ---"
REFUSED=$(run_extdel prompt "$HANDLE1" --prompt "turn2 attempt" --posture workspace)
assert_contains "$REFUSED" "Status: ERROR" "posture mismatch without --steal is refused"
assert_contains "$REFUSED" "differs from this handle's pinned posture" "refusal message explains the pinned-posture mismatch"
POSTURE_AFTER_REFUSAL=$(jq -r '.posture' "./tmp/agent-delegation/$HANDLE1/meta.json" 2>/dev/null)
[ "$POSTURE_AFTER_REFUSAL" = "read-only" ] && pass "pinned posture unchanged after refused attempt" || fail "pinned posture mutated to '$POSTURE_AFTER_REFUSAL'"

STOLEN=$(run_extdel prompt "$HANDLE1" --prompt "turn2 with steal" --posture workspace --steal)
assert_contains "$STOLEN" "Status: RUNNING" "posture escalation succeeds with --steal"
STOLEN_FINAL=$(poll_until_terminal "$HANDLE1" 10)
assert_contains "$STOLEN_FINAL" "Status: SUCCESS" "stolen turn 2 completes"
assert_contains "$STOLEN_FINAL" "Turn: 2" "stolen turn reports turn 2"
POSTURE_AFTER_STEAL=$(jq -r '.posture' "./tmp/agent-delegation/$HANDLE1/meta.json" 2>/dev/null)
[ "$POSTURE_AFTER_STEAL" = "workspace" ] && pass "pinned posture updated after --steal" || fail "pinned posture after steal was '$POSTURE_AFTER_STEAL'"
echo

# ---------------------------------------------------------------------------
# 6. Turn mutex — concurrent prompt refused
# ---------------------------------------------------------------------------
echo "--- 6. turn mutex (concurrent prompt refused) ---"
OUT3=$(MOCK_CODEX_SESSION_ID="33333333-3333-4333-8333-333333333333" run_extdel start --prompt "mutex turn 1" --posture read-only)
HANDLE3=$(extract_field "$OUT3" "Handle")
poll_until_terminal "$HANDLE3" 10 >/dev/null

SLOW=$(MOCK_CODEX_SLEEP=4 run_extdel prompt "$HANDLE3" --prompt "mutex turn 2 (slow)")
assert_contains "$SLOW" "Status: RUNNING" "slow turn 2 submitted"

CONCURRENT=$(run_extdel prompt "$HANDLE3" --prompt "mutex turn 3 (should be refused)")
assert_contains "$CONCURRENT" "Status: ERROR" "concurrent prompt while turn 2 in flight is refused"
assert_contains "$CONCURRENT" "already in progress" "refusal message names the in-flight turn"

SLOW_FINAL=$(poll_until_terminal "$HANDLE3" 10)
assert_contains "$SLOW_FINAL" "Status: SUCCESS" "slow turn 2 eventually completes"
assert_contains "$SLOW_FINAL" "Turn: 2" "completed turn is turn 2 (turn 3 was never accepted)"
echo

# ---------------------------------------------------------------------------
# 7. stop
# ---------------------------------------------------------------------------
echo "--- 7. stop ---"
STOP_OUT=$(run_extdel stop "$HANDLE1")
assert_contains "$STOP_OUT" "STOPPED: $HANDLE1" "stop reports the handle as stopped"
CLOSED=$(jq -r '.closed' "./tmp/agent-delegation/$HANDLE1/meta.json" 2>/dev/null)
[ "$CLOSED" != "null" ] && [ -n "$CLOSED" ] && pass "meta.json.closed timestamp set" || fail "meta.json.closed was '$CLOSED'"
echo

# ---------------------------------------------------------------------------
# 8. reap — stale lock cleanup
# ---------------------------------------------------------------------------
echo "--- 8. reap ---"
mkdir -p "./tmp/agent-delegation/$HANDLE3/.turn-lock"
echo "999999" > "./tmp/agent-delegation/$HANDLE3/.turn-lock/owner.pid"
# lock_is_stale() (M4a) never reaps a lock younger than its 30s grace
# window regardless of owner.pid liveness, to avoid racing the window
# between mkdir and submit_codex_turn overwriting owner.pid with the
# real supervisor pid. Backdate the lock dir so this fixture actually
# exercises the "genuinely old and dead" reap path instead of the grace
# window.
backdate "./tmp/agent-delegation/$HANDLE3/.turn-lock"
REAP_OUT=$(run_extdel reap)
assert_contains "$REAP_OUT" "reaped stale lock: $HANDLE3" "reap clears a lock whose recorded turn pid is dead"
[ -d "./tmp/agent-delegation/$HANDLE3/.turn-lock" ] && fail "stale lock directory still present after reap" || pass "stale lock directory removed"
echo

# ---------------------------------------------------------------------------
# 8b. reap does NOT touch a lock inside its grace window, even with a dead
# owner.pid (M4a regression guard — this is exactly the race that used to
# let a reaper delete a lock for a turn that had just started).
# ---------------------------------------------------------------------------
echo "--- 8b. reap respects the lock-age grace window ---"
OUT8B=$(MOCK_CODEX_SESSION_ID="88888888-8888-4888-8888-888888888888" run_extdel start --prompt "grace window target" --posture read-only)
HANDLE8B=$(extract_field "$OUT8B" "Handle")
poll_until_terminal "$HANDLE8B" 10 >/dev/null
mkdir -p "./tmp/agent-delegation/$HANDLE8B/.turn-lock"
echo "999999" > "./tmp/agent-delegation/$HANDLE8B/.turn-lock/owner.pid"
# Freshly created — well inside the 30s grace window, no backdate.
REAP_OUT8B=$(run_extdel reap)
if [ -d "./tmp/agent-delegation/$HANDLE8B/.turn-lock" ]; then
  pass "reap left a fresh (in-grace-window) lock alone despite a dead owner.pid"
else
  fail "reap removed a lock inside its grace window (M4a regression)"
fi
rm -rf "./tmp/agent-delegation/$HANDLE8B/.turn-lock"
echo

# ---------------------------------------------------------------------------
# 9. stop kills a genuinely mid-flight turn — no orphan, exit.code written,
#    lock released, and a follow-up prompt is accepted cleanly (B1).
# ---------------------------------------------------------------------------
echo "--- 9. stop on a genuinely mid-flight turn (B1 regression guard) ---"
OUT9=$(MOCK_CODEX_SESSION_ID="99999999-9999-4999-8999-999999999999" MOCK_CODEX_SLEEP=6 run_extdel start --prompt "will be stopped mid-flight" --posture read-only)
HANDLE9=$(extract_field "$OUT9" "Handle")
assert_contains "$OUT9" "Status: RUNNING" "handle9 starts RUNNING (mid-flight stop target)"

sleep 1
SUP_PID9=$(cat "./tmp/agent-delegation/$HANDLE9/turn-001.pid" 2>/dev/null)

STOP_OUT9=$(run_extdel stop "$HANDLE9")
assert_contains "$STOP_OUT9" "STOPPED: $HANDLE9" "stop reports the mid-flight handle as stopped"

if [ -n "$SUP_PID9" ] && kill -0 "$SUP_PID9" 2>/dev/null; then
  fail "supervisor pid $SUP_PID9 for handle9 is still alive after stop (orphaned)"
else
  pass "supervisor process is gone after stop (no orphan)"
fi

if [ -f "./tmp/agent-delegation/$HANDLE9/turn-001.exit.code" ]; then
  pass "exit.code was written for the stopped mid-flight turn"
else
  fail "exit.code was NOT written for the stopped mid-flight turn"
fi

if [ -d "./tmp/agent-delegation/$HANDLE9/.turn-lock" ]; then
  fail "turn-lock still present after stop"
else
  pass "turn-lock released after stop"
fi

STATUS9=$(run_extdel status "$HANDLE9" --wait-s 2)
assert_contains "$STATUS9" "Status: FAILURE" "stopped mid-flight turn reports a terminal non-SUCCESS status, not RUNNING"

FOLLOWUP9=$(run_extdel prompt "$HANDLE9" --prompt "follow-up after stop")
assert_contains "$FOLLOWUP9" "Status: RUNNING" "a follow-up prompt after stop is accepted cleanly, not blocked or double-driven"
FOLLOWUP9_FINAL=$(poll_until_terminal "$HANDLE9" 10)
assert_contains "$FOLLOWUP9_FINAL" "Status: SUCCESS" "follow-up turn after a mid-flight stop completes normally"
echo

# ---------------------------------------------------------------------------
# 10. MOCK_CODEX_FAIL -> FAILURE, never a false SUCCESS.
# ---------------------------------------------------------------------------
echo "--- 10. MOCK_CODEX_FAIL reports FAILURE, not SUCCESS ---"
OUT10=$(MOCK_CODEX_SESSION_ID="a0a0a0a0-0000-4000-8000-00000000000a" MOCK_CODEX_FAIL=1 run_extdel start --prompt "induced failure" --posture read-only)
HANDLE10=$(extract_field "$OUT10" "Handle")
FINAL10=$(poll_until_terminal "$HANDLE10" 10)
assert_contains "$FINAL10" "Status: FAILURE" "MOCK_CODEX_FAIL=1 turn reports FAILURE"
assert_not_contains "$FINAL10" "Status: SUCCESS" "MOCK_CODEX_FAIL=1 turn does NOT report SUCCESS"
echo

# ---------------------------------------------------------------------------
# 11. Signal-aware exit code (M1): a TERM-killed turn's exit code is
#     128+SIGTERM, never the misleading `$status >> 8` which reads as 0.
# ---------------------------------------------------------------------------
echo "--- 11. signal-aware exit code (M1) ---"
OUT11=$(MOCK_CODEX_SESSION_ID="b0b0b0b0-0000-4000-8000-00000000000b" MOCK_CODEX_SLEEP=6 run_extdel start --prompt "will be signaled directly" --posture read-only)
HANDLE11=$(extract_field "$OUT11" "Handle")
sleep 1
SUP_PID11=$(cat "./tmp/agent-delegation/$HANDLE11/turn-001.pid" 2>/dev/null)
[ -n "$SUP_PID11" ] && kill -TERM "-$SUP_PID11" 2>/dev/null

n=0
while [ "$n" -lt 10 ] && [ ! -f "./tmp/agent-delegation/$HANDLE11/turn-001.exit.code" ]; do
  sleep 1
  n=$((n + 1))
done
CODE11=$(cat "./tmp/agent-delegation/$HANDLE11/turn-001.exit.code" 2>/dev/null | tr -d '[:space:]')
if [ "$CODE11" = "143" ]; then
  pass "TERM-killed turn's exit code is 128+SIGTERM=143, not misreported as 0"
else
  fail "expected exit code 143 (128+SIGTERM) for a TERM-killed turn, got '$CODE11'"
fi
STATUS11=$(run_extdel status "$HANDLE11" --wait-s 2)
assert_contains "$STATUS11" "Status: FAILURE" "TERM-killed turn reports FAILURE, not SUCCESS"
if [ -d "./tmp/agent-delegation/$HANDLE11/.turn-lock" ]; then
  fail "turn-lock still present after a direct signal kill"
else
  pass "turn-lock released after a direct signal kill"
fi
echo

# ---------------------------------------------------------------------------
# 12. Timeout path: TIMEOUT status, exit code 124, process killed, lock
#     released — automated (was previously, at best, hand-tested).
# ---------------------------------------------------------------------------
echo "--- 12. timeout path ---"
OUT12=$(MOCK_CODEX_SESSION_ID="c0c0c0c0-0000-4000-8000-00000000000c" MOCK_CODEX_SLEEP=8 run_extdel start --prompt "will time out" --posture read-only --timeout-s 2)
HANDLE12=$(extract_field "$OUT12" "Handle")
FINAL12=$(poll_until_terminal "$HANDLE12" 15)
assert_contains "$FINAL12" "Status: TIMEOUT" "a turn exceeding --timeout-s reports TIMEOUT"
CODE12=$(cat "./tmp/agent-delegation/$HANDLE12/turn-001.exit.code" 2>/dev/null | tr -d '[:space:]')
[ "$CODE12" = "124" ] && pass "timeout exit code is 124" || fail "timeout exit code was '$CODE12', expected 124"
if [ -d "./tmp/agent-delegation/$HANDLE12/.turn-lock" ]; then
  fail "turn-lock still present after a timeout"
else
  pass "turn-lock released after a timeout"
fi
echo

# ---------------------------------------------------------------------------
# 13. Path-traversal handle rejected by every handle-taking subcommand (M2).
# ---------------------------------------------------------------------------
echo "--- 13. path-traversal handle rejected everywhere (M2) ---"
BAD_HANDLE="../../../etc"
STATUS_BAD=$(run_extdel status "$BAD_HANDLE" 2>&1)
assert_contains "$STATUS_BAD" "Status: ERROR" "status rejects a path-traversal handle"
SLICE_BAD=$(run_extdel slice "$BAD_HANDLE" 2>&1)
assert_contains "$SLICE_BAD" "ERROR" "slice rejects a path-traversal handle"
STOP_BAD=$(run_extdel stop "$BAD_HANDLE" 2>&1)
assert_contains "$STOP_BAD" "ERROR" "stop rejects a path-traversal handle"
PROMPT_BAD=$(run_extdel prompt "$BAD_HANDLE" --prompt "x" 2>&1)
assert_contains "$PROMPT_BAD" "Status: ERROR" "prompt rejects a path-traversal handle"
if [ -e "$TESTROOT/../etc" ] || [ -e "/etc/.turn-lock" ]; then
  fail "a path-traversal handle touched something outside the state dir"
else
  pass "no path-traversal side effects observed outside the state dir"
fi
echo

# ---------------------------------------------------------------------------
# 14. Spawn failure (perl unavailable via a PATH shim) -> SPAWN_FAIL,
#     never RUNNING forever, lock released (M6).
# ---------------------------------------------------------------------------
echo "--- 14. spawn failure -> SPAWN_FAIL, not RUNNING forever (M6) ---"
FAKE_PERL_DIR="$TESTROOT/fake-bin-no-perl"
mkdir -p "$FAKE_PERL_DIR"
cat > "$FAKE_PERL_DIR/perl" <<'PERLSTUB'
#!/bin/sh
exit 127
PERLSTUB
chmod +x "$FAKE_PERL_DIR/perl"

OUT14=$(PATH="$FAKE_PERL_DIR:$MOCK_BIN:$PATH" "$EXTDEL" start --prompt "spawn should fail" --posture read-only)
assert_contains "$OUT14" "Status: ERROR" "spawn failure is reported as ERROR, not RUNNING"
assert_contains "$OUT14" "spawn failed" "spawn failure error explains the supervisor never started"
assert_not_contains "$OUT14" "Status: RUNNING" "spawn failure never reports RUNNING"
HANDLE14=$(extract_field "$OUT14" "Handle")
if [ -n "$HANDLE14" ] && [ "$HANDLE14" != "(none)" ] && [ -d "./tmp/agent-delegation/$HANDLE14" ]; then
  if [ -d "./tmp/agent-delegation/$HANDLE14/.turn-lock" ]; then
    fail "turn-lock leaked after a spawn failure"
  else
    pass "turn-lock released after a spawn failure"
  fi
else
  pass "spawn-failure handle housekeeping not applicable (no handle dir to check)"
fi
echo

# ---------------------------------------------------------------------------
# 15. Numeric-option validation rejects garbage without corrupting state (M8).
# ---------------------------------------------------------------------------
echo "--- 15. numeric option validation (M8) ---"
BAD_TIMEOUT=$(run_extdel start --prompt "x" --timeout-s abc 2>&1)
assert_contains "$BAD_TIMEOUT" "--timeout-s must be a non-negative integer" "start rejects non-numeric --timeout-s"

OUT15=$(MOCK_CODEX_SESSION_ID="d0d0d0d0-0000-4000-8000-00000000000d" run_extdel start --prompt "for numeric validation" --posture read-only)
HANDLE15=$(extract_field "$OUT15" "Handle")
poll_until_terminal "$HANDLE15" 10 >/dev/null
META_BEFORE=$(cat "./tmp/agent-delegation/$HANDLE15/meta.json" 2>/dev/null)

BAD_PROMPT_TIMEOUT=$(run_extdel prompt "$HANDLE15" --prompt "y" --timeout-s notanumber 2>&1)
assert_contains "$BAD_PROMPT_TIMEOUT" "--timeout-s must be a non-negative integer" "prompt rejects non-numeric --timeout-s"

BAD_SLICE=$(run_extdel slice "$HANDLE15" --max-chars notanumber 2>&1)
assert_contains "$BAD_SLICE" "--max-chars must be a non-negative integer" "slice rejects non-numeric --max-chars"

META_AFTER=$(cat "./tmp/agent-delegation/$HANDLE15/meta.json" 2>/dev/null)
if [ "$META_BEFORE" = "$META_AFTER" ]; then
  pass "meta.json is untouched by rejected numeric options"
else
  fail "meta.json changed after rejected numeric options"
fi

BAD_REAP=$(run_extdel reap --prune-closed notanumber 2>&1)
assert_contains "$BAD_REAP" "--prune-closed must be a non-negative integer" "reap rejects non-numeric --prune-closed"
echo

echo "=== Results: $PASS passed, $FAIL failed ==="
if [ "$FAIL" -gt 0 ]; then
  exit 1
fi
exit 0
