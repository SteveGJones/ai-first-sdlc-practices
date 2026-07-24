#!/usr/bin/env bash
# Test harness for extdel.sh's agy-resume path (Stage 3 of issue #232).
# Exercises extdel.sh entirely against a MOCK `agy` binary placed first on
# PATH, with HOME redirected to a throwaway directory so
# ~/.gemini/antigravity-cli/ is NEVER touched — the real codex/agy CLIs
# are never invoked here, so this test never spends API quota. Bash-3.2-
# safe (no associative arrays, no `${var,,}`), matching extdel.sh's own
# target shell.
#
# Run: bash plugins/sdlc-agent-delegation/tests/test-extdel-agy-resume.sh
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
TESTROOT="$(mktemp -d "$REPO_ROOT/tmp/extdel-agy-test.XXXXXX")"
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

# All agy tests share one HOME (redirects ~/.gemini/antigravity-cli/ to a
# throwaway dir) with the state dir PRE-created — simulates "agy has been
# signed into interactively at least once" so preflight_agy's directory
# check passes for the happy-path tests. The two preflight-failure tests
# override HOME/PATH locally per call.
FAKE_HOME="$TESTROOT/fake-home"
mkdir -p "$FAKE_HOME/.gemini/antigravity-cli/cache"
export HOME="$FAKE_HOME"

run_extdel_agy() {
  PATH="$MOCK_BIN:$PATH" "$EXTDEL" "$@"
}

poll_until_terminal() {
  # poll_until_terminal <handle> <max_seconds> -> prints final status block
  handle="$1"; max="$2"
  n=0
  while [ "$n" -lt "$max" ]; do
    out=$(run_extdel_agy status "$handle" --wait-s 2)
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

handle_cache_file() {
  # handle_cache_file <handle> — DF1 (§9.15): id-capture now reads a
  # per-HANDLE isolated cache under that handle's own --gemini_dir, not a
  # single machine-global $FAKE_HOME/.gemini/... path. There is no longer
  # one shared cache file to inspect across handles/tests.
  printf './tmp/agent-delegation/%s/agy-cfg/antigravity-cli/cache/last_conversations.json' "$1"
}

echo "=== extdel.sh agy-resume test suite ==="
echo "TESTROOT=$TESTROOT"
echo "FAKE_HOME=$FAKE_HOME"
echo

cd "$TESTROOT" || exit 1

# ---------------------------------------------------------------------------
# 1. Handle creation
# ---------------------------------------------------------------------------
echo "--- 1. handle creation ---"
OUT1=$(MOCK_AGY_SESSION_ID="11111111-1111-4111-8111-111111111111" run_extdel_agy start --cli agy --prompt "hello world" --posture read-only)
assert_contains "$OUT1" "Status: RUNNING" "start returns RUNNING immediately"
assert_contains "$OUT1" "CLI: agy" "return block reports CLI: agy"
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
META_AGENT=$(jq -r '.agent' "./tmp/agent-delegation/$HANDLE1/meta.json" 2>/dev/null)
PROMPT_CONTENT=$(cat "./tmp/agent-delegation/$HANDLE1/turn-001.prompt.txt" 2>/dev/null)
[ "$META_CLI" = "agy" ] && pass "meta.json cli=agy" || fail "meta.json cli was '$META_CLI'"
[ "$META_POSTURE" = "read-only" ] && pass "meta.json posture=read-only" || fail "meta.json posture was '$META_POSTURE'"
[ "$META_AGENT" = "null" ] && pass "meta.json agent=null when not given" || fail "meta.json agent was '$META_AGENT'"
[ "$PROMPT_CONTENT" = "hello world" ] && pass "turn-001.prompt.txt has the exact prompt text" || fail "prompt file content was '$PROMPT_CONTENT'"
echo

# ---------------------------------------------------------------------------
# 2. id capture from last_conversations.json (§9.14, authoritative).
#
# MUST run right after handle1's own `start` — every agy test in this
# suite shares one cwd (TESTROOT), and therefore one shared
# last_conversations.json[cwd] cache key. Capture happens lazily, on the
# first `status` call that observes turn 1 as terminal (per the task
# spec: "after the turn reaches terminal SUCCESS"), so if we deferred
# handle1's first status poll until AFTER some other handle's own turn
# had already run to completion in the same cwd, we'd capture THAT
# handle's id instead of handle1's own — not a bug in extdel.sh, but a
# real characteristic of lazy, cwd-keyed capture that §9.14 already
# documents as a residual same-cwd race. Poll immediately, exactly like
# the real agy-runner agent's procedure does (step 4 follows step 3
# without any intervening delegation), to keep this test representative
# rather than accidentally proving the residual race instead of the
# happy path.
# ---------------------------------------------------------------------------
echo "--- 2. id capture from last_conversations.json ---"
FINAL1=$(poll_until_terminal "$HANDLE1" 10)
assert_contains "$FINAL1" "Status: SUCCESS" "handle1 turn 1 reaches SUCCESS"
assert_contains "$FINAL1" "11111111-1111-4111-8111-111111111111" "captured session id matches the mock's minted conversation id"
CAPTURED_SID=$(jq -r '.session_id' "./tmp/agent-delegation/$HANDLE1/meta.json" 2>/dev/null)
[ "$CAPTURED_SID" = "11111111-1111-4111-8111-111111111111" ] && pass "meta.json.session_id persisted" || fail "meta.json.session_id was '$CAPTURED_SID'"
[ -f "./tmp/agent-delegation/$HANDLE1/session.id" ] && pass "session.id file written" || fail "session.id file missing"
CAPTURED_CWD_KEY=$(jq -r '.agy_cwd_key' "./tmp/agent-delegation/$HANDLE1/meta.json" 2>/dev/null)
[ "$CAPTURED_CWD_KEY" = "$(pwd -P)" ] && pass "meta.json.agy_cwd_key is the pwd -P normalized cwd" || fail "meta.json.agy_cwd_key was '$CAPTURED_CWD_KEY'"
if jq -e --arg k "$(pwd -P)" '.[$k] == "11111111-1111-4111-8111-111111111111"' "$(handle_cache_file "$HANDLE1")" >/dev/null 2>&1; then
  pass "mock correctly wrote HANDLE1's isolated last_conversations.json[cwd] = the minted id"
else
  fail "handle1's isolated last_conversations.json does not have the expected cwd -> id mapping"
fi
if [ -d "./tmp/agent-delegation/$HANDLE1/agy-cfg/antigravity-cli" ]; then
  pass "per-handle --gemini_dir config dir created (DF1)"
else
  fail "per-handle --gemini_dir config dir NOT created"
fi
echo

# ---------------------------------------------------------------------------
# 3. Submit-then-poll lifecycle + RUNNING -> SUCCESS transition
# ---------------------------------------------------------------------------
echo "--- 3. submit-then-poll lifecycle / RUNNING -> SUCCESS ---"
OUT2=$(MOCK_AGY_SESSION_ID="22222222-2222-4222-8222-222222222222" MOCK_AGY_SLEEP=2 run_extdel_agy start --cli agy --prompt "slow first turn" --posture read-only)
HANDLE2=$(extract_field "$OUT2" "Handle")
assert_contains "$OUT2" "Status: RUNNING" "turn2 handle starts RUNNING"

IMMEDIATE=$(run_extdel_agy status "$HANDLE2" --wait-s 0)
assert_contains "$IMMEDIATE" "Status: RUNNING" "immediate zero-wait status still RUNNING (mock is sleeping)"

sleep 3
FINAL2=$(run_extdel_agy status "$HANDLE2" --wait-s 5)
assert_contains "$FINAL2" "Status: SUCCESS" "status transitions to SUCCESS once the mock finishes"
assert_contains "$FINAL2" "Turn: 1" "SUCCESS report shows turn 1"
echo

# ---------------------------------------------------------------------------
# 4. slice + truncation + self-heal (answer file populated from stdout
#    capture even if `slice` is called before `status` ever ran — agy has
#    no -o file the way codex does, §9.14 #3).
# ---------------------------------------------------------------------------
echo "--- 4. slice ---"
SLICE_FULL=$(run_extdel_agy slice "$HANDLE1")
assert_contains "$SLICE_FULL" "mock agy answer for: hello world" "slice returns the mock's stdout-captured answer"

SLICE_TRUNC=$(run_extdel_agy slice "$HANDLE1" --max-chars 5)
assert_contains "$SLICE_TRUNC" "truncated" "slice --max-chars 5 truncates the answer"
FIRST_LINE_LEN=$(printf '%s' "$SLICE_TRUNC" | head -1 | awk '{print length}')
if [ "$FIRST_LINE_LEN" -le 5 ]; then
  pass "truncated first line is <= max-chars (was $FIRST_LINE_LEN)"
else
  fail "truncated first line exceeded max-chars (was $FIRST_LINE_LEN)"
fi

rm -f "./tmp/agent-delegation/$HANDLE1/turn-001.last-message.txt"
SLICE_SELF_HEAL=$(run_extdel_agy slice "$HANDLE1")
assert_contains "$SLICE_SELF_HEAL" "mock agy answer for: hello world" "slice self-heals last-message.txt from events.jsonl when called before status"
echo

# ---------------------------------------------------------------------------
# 5. Pinned-posture refusal
# ---------------------------------------------------------------------------
echo "--- 5. pinned-posture refusal ---"
REFUSED=$(run_extdel_agy prompt "$HANDLE1" --prompt "turn2 attempt" --posture workspace)
assert_contains "$REFUSED" "Status: ERROR" "posture mismatch without --steal is refused"
assert_contains "$REFUSED" "differs from this handle's pinned posture" "refusal message explains the pinned-posture mismatch"
POSTURE_AFTER_REFUSAL=$(jq -r '.posture' "./tmp/agent-delegation/$HANDLE1/meta.json" 2>/dev/null)
[ "$POSTURE_AFTER_REFUSAL" = "read-only" ] && pass "pinned posture unchanged after refused attempt" || fail "pinned posture mutated to '$POSTURE_AFTER_REFUSAL'"

STOLEN=$(run_extdel_agy prompt "$HANDLE1" --prompt "turn2 with steal" --posture workspace --steal)
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
OUT3=$(MOCK_AGY_SESSION_ID="33333333-3333-4333-8333-333333333333" run_extdel_agy start --cli agy --prompt "mutex turn 1" --posture read-only)
HANDLE3=$(extract_field "$OUT3" "Handle")
poll_until_terminal "$HANDLE3" 10 >/dev/null

SLOW=$(MOCK_AGY_SLEEP=4 run_extdel_agy prompt "$HANDLE3" --prompt "mutex turn 2 (slow)")
assert_contains "$SLOW" "Status: RUNNING" "slow turn 2 submitted"

CONCURRENT=$(run_extdel_agy prompt "$HANDLE3" --prompt "mutex turn 3 (should be refused)")
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
STOP_OUT=$(run_extdel_agy stop "$HANDLE1")
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
backdate "./tmp/agent-delegation/$HANDLE3/.turn-lock"
REAP_OUT=$(run_extdel_agy reap)
assert_contains "$REAP_OUT" "reaped stale lock: $HANDLE3" "reap clears a lock whose recorded turn pid is dead"
[ -d "./tmp/agent-delegation/$HANDLE3/.turn-lock" ] && fail "stale lock directory still present after reap" || pass "stale lock directory removed"
echo

# ---------------------------------------------------------------------------
# 8b. reap does NOT touch a lock inside its grace window.
# ---------------------------------------------------------------------------
echo "--- 8b. reap respects the lock-age grace window ---"
OUT8B=$(MOCK_AGY_SESSION_ID="88888888-8888-4888-8888-888888888888" run_extdel_agy start --cli agy --prompt "grace window target" --posture read-only)
HANDLE8B=$(extract_field "$OUT8B" "Handle")
poll_until_terminal "$HANDLE8B" 10 >/dev/null
mkdir -p "./tmp/agent-delegation/$HANDLE8B/.turn-lock"
echo "999999" > "./tmp/agent-delegation/$HANDLE8B/.turn-lock/owner.pid"
REAP_OUT8B=$(run_extdel_agy reap)
if [ -d "./tmp/agent-delegation/$HANDLE8B/.turn-lock" ]; then
  pass "reap left a fresh (in-grace-window) lock alone despite a dead owner.pid"
else
  fail "reap removed a lock inside its grace window"
fi
rm -rf "./tmp/agent-delegation/$HANDLE8B/.turn-lock"
echo

# ---------------------------------------------------------------------------
# 9. stop kills a genuinely mid-flight turn — no orphan, exit.code written,
#    lock released. UNLIKE codex, a killed agy turn 1 that never reached
#    SUCCESS has NOT captured a session id (agy's capture is deliberately
#    gated on terminal SUCCESS — the task spec: "after the turn reaches
#    terminal SUCCESS" — since agy's only id source is a cache file, not a
#    partial event stream codex can still mine after a kill). So a
#    follow-up `prompt` on this handle correctly ERRORs asking for a fresh
#    handle instead, rather than resuming — that's the right behavior to
#    assert here, not a bug.
# ---------------------------------------------------------------------------
echo "--- 9. stop on a genuinely mid-flight turn ---"
OUT9=$(MOCK_AGY_SESSION_ID="99999999-9999-4999-8999-999999999999" MOCK_AGY_SLEEP=6 run_extdel_agy start --cli agy --prompt "will be stopped mid-flight" --posture read-only)
HANDLE9=$(extract_field "$OUT9" "Handle")
assert_contains "$OUT9" "Status: RUNNING" "handle9 starts RUNNING (mid-flight stop target)"

sleep 1
SUP_PID9=$(cat "./tmp/agent-delegation/$HANDLE9/turn-001.pid" 2>/dev/null)

STOP_OUT9=$(run_extdel_agy stop "$HANDLE9")
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

STATUS9=$(run_extdel_agy status "$HANDLE9" --wait-s 2)
assert_contains "$STATUS9" "Status: FAILURE" "stopped mid-flight turn reports a terminal non-SUCCESS status, not RUNNING"
assert_contains "$STATUS9" "Session id: pending" "a killed turn 1 (never SUCCESS) never captured a session id"

FOLLOWUP9=$(run_extdel_agy prompt "$HANDLE9" --prompt "follow-up after stop")
assert_contains "$FOLLOWUP9" "Status: ERROR" "a follow-up prompt against a handle with no captured session id is refused, not silently accepted"
assert_contains "$FOLLOWUP9" "no session id captured yet" "refusal explains that turn 1 never completed/captured a session"
echo

# ---------------------------------------------------------------------------
# 10. MOCK_AGY_FAIL -> FAILURE, never a false SUCCESS, and distinct from
#     the auth-backstop ERROR path tested next.
# ---------------------------------------------------------------------------
echo "--- 10. MOCK_AGY_FAIL reports FAILURE, not SUCCESS ---"
OUT10=$(MOCK_AGY_SESSION_ID="a0a0a0a0-0000-4000-8000-00000000000a" MOCK_AGY_FAIL=1 run_extdel_agy start --cli agy --prompt "induced failure" --posture read-only)
HANDLE10=$(extract_field "$OUT10" "Handle")
FINAL10=$(poll_until_terminal "$HANDLE10" 10)
assert_contains "$FINAL10" "Status: FAILURE" "MOCK_AGY_FAIL=1 turn reports FAILURE"
assert_not_contains "$FINAL10" "Status: SUCCESS" "MOCK_AGY_FAIL=1 turn does NOT report SUCCESS"
echo

# ---------------------------------------------------------------------------
# 10b. Auth backstop: a failure whose stderr matches an auth-shaped
#      pattern is ERROR, distinct from a plain model-level FAILURE (§6.2).
# ---------------------------------------------------------------------------
echo "--- 10b. auth backstop reports ERROR, not FAILURE ---"
OUT10B=$(MOCK_AGY_SESSION_ID="a1a1a1a1-0000-4000-8000-00000000000a" MOCK_AGY_AUTH_FAIL=1 run_extdel_agy start --cli agy --prompt "auth should fail" --posture read-only)
HANDLE10B=$(extract_field "$OUT10B" "Handle")
FINAL10B=$(poll_until_terminal "$HANDLE10B" 10)
assert_contains "$FINAL10B" "Status: ERROR" "auth-shaped stderr is reported as ERROR"
assert_not_contains "$FINAL10B" "Status: FAILURE" "auth-shaped stderr is NOT reported as a plain FAILURE"
assert_contains "$FINAL10B" "authentication appears to have failed" "ERROR message names authentication distinctly"
echo

# ---------------------------------------------------------------------------
# 11. Signal-aware exit code: a TERM-killed turn's exit code is
#     128+SIGTERM, never the misleading `$status >> 8` which reads as 0.
#     (Shared turn-supervisor.pl logic — already the engine codex uses —
#     re-verified here because submit_agy_turn is a separate call site.)
# ---------------------------------------------------------------------------
echo "--- 11. signal-aware exit code ---"
OUT11=$(MOCK_AGY_SESSION_ID="b0b0b0b0-0000-4000-8000-00000000000b" MOCK_AGY_SLEEP=6 run_extdel_agy start --cli agy --prompt "will be signaled directly" --posture read-only)
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
STATUS11=$(run_extdel_agy status "$HANDLE11" --wait-s 2)
assert_contains "$STATUS11" "Status: FAILURE" "TERM-killed turn reports FAILURE, not SUCCESS"
if [ -d "./tmp/agent-delegation/$HANDLE11/.turn-lock" ]; then
  fail "turn-lock still present after a direct signal kill"
else
  pass "turn-lock released after a direct signal kill"
fi
echo

# ---------------------------------------------------------------------------
# 12. Timeout arithmetic: agy's supervisor alarm is timeout_s+30 (a hard
#     backstop PAST the native --print-timeout), not timeout_s directly
#     (codex has no native timeout, so ITS alarm IS timeout_s — see §6.4).
#     Differential test: with --timeout-s 2 and a 5s mock sleep, a turn
#     that used the CORRECT +30s backstop finishes SUCCESS (32s budget);
#     a turn that wrongly reused codex's bare-timeout_s math would instead
#     report TIMEOUT at 2s. This proves the arithmetic without waiting out
#     a real 30s alarm — the alarm-fires-at-all mechanism (perl alarm ->
#     SIGTERM -> exit 124) is already covered by the codex suite's own
#     timeout test against the SAME shared turn-supervisor.pl engine.
# ---------------------------------------------------------------------------
echo "--- 12. timeout arithmetic (native + backstop, not bare timeout_s) ---"
OUT12=$(MOCK_AGY_SESSION_ID="c0c0c0c0-0000-4000-8000-00000000000c" MOCK_AGY_SLEEP=5 run_extdel_agy start --cli agy --prompt "should NOT hit the bare timeout_s" --posture read-only --timeout-s 2)
HANDLE12=$(extract_field "$OUT12" "Handle")
FINAL12=$(poll_until_terminal "$HANDLE12" 15)
assert_contains "$FINAL12" "Status: SUCCESS" "a 5s mock turn survives --timeout-s 2 (backstop is timeout_s+30=32s, not 2s)"
echo

# ---------------------------------------------------------------------------
# 13. Path-traversal handle rejected by every handle-taking subcommand.
# ---------------------------------------------------------------------------
echo "--- 13. path-traversal handle rejected everywhere ---"
BAD_HANDLE="../../../etc"
STATUS_BAD=$(run_extdel_agy status "$BAD_HANDLE" 2>&1)
assert_contains "$STATUS_BAD" "Status: ERROR" "status rejects a path-traversal handle"
SLICE_BAD=$(run_extdel_agy slice "$BAD_HANDLE" 2>&1)
assert_contains "$SLICE_BAD" "ERROR" "slice rejects a path-traversal handle"
STOP_BAD=$(run_extdel_agy stop "$BAD_HANDLE" 2>&1)
assert_contains "$STOP_BAD" "ERROR" "stop rejects a path-traversal handle"
PROMPT_BAD=$(run_extdel_agy prompt "$BAD_HANDLE" --prompt "x" 2>&1)
assert_contains "$PROMPT_BAD" "Status: ERROR" "prompt rejects a path-traversal handle"
if [ -e "$TESTROOT/../etc" ] || [ -e "/etc/.turn-lock" ]; then
  fail "a path-traversal handle touched something outside the state dir"
else
  pass "no path-traversal side effects observed outside the state dir"
fi
echo

# ---------------------------------------------------------------------------
# 14. Spawn failure (perl unavailable via a PATH shim) -> SPAWN_FAIL,
#     never RUNNING forever, lock released.
# ---------------------------------------------------------------------------
echo "--- 14. spawn failure -> SPAWN_FAIL, not RUNNING forever ---"
FAKE_PERL_DIR="$TESTROOT/fake-bin-no-perl"
mkdir -p "$FAKE_PERL_DIR"
cat > "$FAKE_PERL_DIR/perl" <<'PERLSTUB'
#!/bin/sh
exit 127
PERLSTUB
chmod +x "$FAKE_PERL_DIR/perl"

OUT14=$(PATH="$FAKE_PERL_DIR:$MOCK_BIN:$PATH" "$EXTDEL" start --cli agy --prompt "spawn should fail" --posture read-only)
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
# 15. Numeric-option validation rejects garbage without corrupting state.
# ---------------------------------------------------------------------------
echo "--- 15. numeric option validation ---"
BAD_TIMEOUT=$(run_extdel_agy start --cli agy --prompt "x" --timeout-s abc 2>&1)
assert_contains "$BAD_TIMEOUT" "--timeout-s must be a non-negative integer" "start rejects non-numeric --timeout-s"

OUT15=$(MOCK_AGY_SESSION_ID="d0d0d0d0-0000-4000-8000-00000000000d" run_extdel_agy start --cli agy --prompt "for numeric validation" --posture read-only)
HANDLE15=$(extract_field "$OUT15" "Handle")
poll_until_terminal "$HANDLE15" 10 >/dev/null
META_BEFORE=$(cat "./tmp/agent-delegation/$HANDLE15/meta.json" 2>/dev/null)

BAD_PROMPT_TIMEOUT=$(run_extdel_agy prompt "$HANDLE15" --prompt "y" --timeout-s notanumber 2>&1)
assert_contains "$BAD_PROMPT_TIMEOUT" "--timeout-s must be a non-negative integer" "prompt rejects non-numeric --timeout-s"

BAD_SLICE=$(run_extdel_agy slice "$HANDLE15" --max-chars notanumber 2>&1)
assert_contains "$BAD_SLICE" "--max-chars must be a non-negative integer" "slice rejects non-numeric --max-chars"

META_AFTER=$(cat "./tmp/agent-delegation/$HANDLE15/meta.json" 2>/dev/null)
if [ "$META_BEFORE" = "$META_AFTER" ]; then
  pass "meta.json is untouched by rejected numeric options"
else
  fail "meta.json changed after rejected numeric options"
fi
echo

# ---------------------------------------------------------------------------
# 16. Missing-CLI ERROR: `command -v agy` fails -> Status ERROR, no hang.
# ---------------------------------------------------------------------------
echo "--- 16. missing agy CLI -> ERROR ---"
MINIMAL_PATH="/usr/bin:/bin"
OUT16=$(PATH="$MINIMAL_PATH" "$EXTDEL" start --cli agy --prompt "no agy on PATH" --posture read-only 2>&1)
assert_contains "$OUT16" "Status: ERROR" "missing agy binary is reported as ERROR"
assert_contains "$OUT16" "agy not found on PATH" "missing-CLI message names the missing binary and install guidance"
echo

# ---------------------------------------------------------------------------
# 17. Uninitialized-auth ERROR: agy state dir absent -> Status ERROR,
#     distinct message from the missing-binary case.
# ---------------------------------------------------------------------------
echo "--- 17. agy never initialized -> ERROR ---"
UNINIT_HOME="$TESTROOT/fake-home-uninit"
mkdir -p "$UNINIT_HOME"
OUT17=$(HOME="$UNINIT_HOME" run_extdel_agy start --cli agy --prompt "agy never signed in" --posture read-only 2>&1)
assert_contains "$OUT17" "Status: ERROR" "uninitialized agy state dir is reported as ERROR"
assert_contains "$OUT17" "agy not initialized" "uninitialized message says so distinctly from the missing-binary case"
echo

# ---------------------------------------------------------------------------
# 18. Leading-dash prompt is refused (agy's flag parser would otherwise
#     treat it as an option, per §9.12 m3).
# ---------------------------------------------------------------------------
echo "--- 18. leading-dash prompt refused ---"
OUT18=$(run_extdel_agy start --cli agy --prompt "-oops this looks like a flag" --posture read-only 2>&1)
assert_contains "$OUT18" "Status: ERROR" "a leading-dash prompt is refused, not silently misparsed"
assert_contains "$OUT18" "BAD_PROMPT" "refusal is the BAD_PROMPT code, not a generic failure"
echo

# ---------------------------------------------------------------------------
# 19. id-capture failure: last_conversations.json has no entry for this
#     cwd after retries -> Status ERROR, Session id: pending (§9.14,
#     supersedes §9.6's metadata cross-check, which is moot for --print
#     turns). Uses a DEDICATED cwd — belt and braces; not strictly required
#     any more since DF1 isolates each handle's cache anyway, but keeps
#     this test's intent obvious on its own.
# ---------------------------------------------------------------------------
echo "--- 19. id capture failure (no cache entry after retries) -> ERROR ---"
NO_ID_CWD="$TESTROOT/no-id-capture-cwd"
mkdir -p "$NO_ID_CWD"
OUT19=$(MOCK_AGY_NO_ID_WRITE=1 run_extdel_agy start --cli agy --cwd "$NO_ID_CWD" --prompt "id capture will fail" --posture read-only)
HANDLE19=$(extract_field "$OUT19" "Handle")
FINAL19=$(poll_until_terminal "$HANDLE19" 10)
assert_contains "$FINAL19" "Status: ERROR" "a cwd with no last_conversations.json entry after retries reports ERROR"
assert_contains "$FINAL19" "Session id: pending" "session id stays pending when capture fails"
assert_contains "$FINAL19" "id capture failed" "error message explains id capture failed"
echo

# ---------------------------------------------------------------------------
# 20. Identity-drift warning: this HANDLE'S OWN isolated
#     last_conversations.json[cwd] changes to a different conversation
#     between turns -> surfaced as a WARNING on the next status call,
#     WITHOUT silently resuming the new one (§9.14, adapted for DF1's
#     per-handle --gemini_dir isolation).
#
#     DF1 note: before DF1, id-capture read a single machine-global cache
#     shared by every agy invocation on the box, so drift could come from
#     genuinely ANY other process (another Claude project, the user's own
#     interactive agy) touching the same cwd. After DF1, each handle gets
#     its own isolated --gemini_dir cache, so that specific cross-process
#     race is closed — see the comment on agy_read_last_conversations_id
#     in extdel.sh. What agy_check_identity_drift still guards against is
#     narrower but not vacuous: THIS handle's own cache entry getting
#     rewritten out-of-band between our submit and our status poll (e.g. a
#     bug, or something else writing into this handle's state dir) — we
#     tamper with the handle's own isolated cache file directly to
#     exercise that remaining path, rather than the old global one (which
#     the isolated capture code no longer even reads).
# ---------------------------------------------------------------------------
echo "--- 20. identity drift between turns surfaces a warning ---"
OUT20=$(MOCK_AGY_SESSION_ID="e0e0e0e0-0000-4000-8000-00000000000e" run_extdel_agy start --cli agy --prompt "drift turn 1" --posture read-only)
HANDLE20=$(extract_field "$OUT20" "Handle")
FINAL20T1=$(poll_until_terminal "$HANDLE20" 10)
assert_contains "$FINAL20T1" "Status: SUCCESS" "drift-test handle turn 1 succeeds"
ORIGINAL_SID20=$(jq -r '.session_id' "./tmp/agent-delegation/$HANDLE20/meta.json" 2>/dev/null)
[ "$ORIGINAL_SID20" = "e0e0e0e0-0000-4000-8000-00000000000e" ] && pass "drift-test handle captured its own session id" || fail "drift-test handle captured '$ORIGINAL_SID20'"

TURN2_OUT20=$(run_extdel_agy prompt "$HANDLE20" --prompt "drift turn 2")
assert_contains "$TURN2_OUT20" "Status: RUNNING" "drift-test turn 2 submitted"

# Wait for turn 2's OWN mock invocation to fully finish (it will re-write
# HANDLE20's isolated last_conversations.json[cwd] back to the CORRECT
# resumed id) BEFORE we tamper — tampering earlier would just get
# clobbered by the mock's own write and the drift would never be
# observable.
n=0
while [ "$n" -lt 10 ] && [ ! -f "./tmp/agent-delegation/$HANDLE20/turn-002.exit.code" ]; do
  sleep 1
  n=$((n + 1))
done

# Simulate something writing out-of-band into THIS HANDLE's own isolated
# cache after our turn 2 finished but before we've polled status for it.
HANDLE20_CACHE=$(handle_cache_file "$HANDLE20")
FAKE_OTHER_ID="deadbeef-dead-4eef-8eef-deadbeefdead"
jq --arg k "$(pwd -P)" --arg v "$FAKE_OTHER_ID" '.[$k] = $v' "$HANDLE20_CACHE" > "$HANDLE20_CACHE.drift-tmp" \
  && mv "$HANDLE20_CACHE.drift-tmp" "$HANDLE20_CACHE"

STATUS20T2=$(run_extdel_agy status "$HANDLE20" --wait-s 2)
assert_contains "$STATUS20T2" "Status: SUCCESS" "turn 2 still reports SUCCESS despite the drift"
assert_contains "$STATUS20T2" "$ORIGINAL_SID20" "Session id in the return is still OUR original session, not the drifted one"
assert_contains "$STATUS20T2" "WARNING" "a WARNING is surfaced when the cwd's recorded conversation identity changed"
assert_contains "$STATUS20T2" "$FAKE_OTHER_ID" "the warning names the drifted-to id"
echo

# ---------------------------------------------------------------------------
# 21. DF1: per-handle --gemini_dir config is written with the correct
#     permissions.allow list per posture — read-only has NO write_file/
#     edit_file rule at all; workspace has both plus a build/test command
#     set; dangerous still gets a config dir (content is inert once
#     --dangerously-skip-permissions is passed, but --gemini_dir is always
#     passed uniformly).
# ---------------------------------------------------------------------------
echo "--- 21. per-handle gemini_dir config matches the posture (DF1) ---"
OUT21RO=$(MOCK_AGY_SESSION_ID="21210000-0000-4000-8000-000000000021" run_extdel_agy start --cli agy --prompt "ro config check" --posture read-only)
HANDLE21RO=$(extract_field "$OUT21RO" "Handle")
poll_until_terminal "$HANDLE21RO" 10 >/dev/null
SETTINGS_RO="./tmp/agent-delegation/$HANDLE21RO/agy-cfg/antigravity-cli/settings.json"
if [ -f "$SETTINGS_RO" ]; then
  pass "read-only handle's settings.json exists"
else
  fail "read-only handle's settings.json missing"
fi
if jq -e '.permissions.allow | index("read_file(*)") != null' "$SETTINGS_RO" >/dev/null 2>&1; then
  pass "read-only settings.json grants read_file(*)"
else
  fail "read-only settings.json does not grant read_file(*)"
fi
if jq -e '.permissions.allow | (index("write_file(*)") == null) and (index("edit_file(*)") == null)' "$SETTINGS_RO" >/dev/null 2>&1; then
  pass "read-only settings.json grants NO write_file(*)/edit_file(*)"
else
  fail "read-only settings.json unexpectedly grants a write/edit rule"
fi

OUT21WS=$(MOCK_AGY_SESSION_ID="21210000-0000-4000-8000-000000000022" run_extdel_agy start --cli agy --prompt "ws config check" --posture workspace)
HANDLE21WS=$(extract_field "$OUT21WS" "Handle")
poll_until_terminal "$HANDLE21WS" 10 >/dev/null
SETTINGS_WS="./tmp/agent-delegation/$HANDLE21WS/agy-cfg/antigravity-cli/settings.json"
if jq -e '.permissions.allow | (index("write_file(*)") != null) and (index("edit_file(*)") != null) and (index("command(pytest)") != null)' "$SETTINGS_WS" >/dev/null 2>&1; then
  pass "workspace settings.json grants write_file(*)/edit_file(*) + build/test commands"
else
  fail "workspace settings.json missing expected write/build-test rules"
fi

OUT21DG=$(MOCK_AGY_SESSION_ID="21210000-0000-4000-8000-000000000023" MOCK_AGY_ACTION=write run_extdel_agy start --cli agy --prompt "dangerous config check" --posture dangerous)
HANDLE21DG=$(extract_field "$OUT21DG" "Handle")
FINAL21DG=$(poll_until_terminal "$HANDLE21DG" 10)
assert_contains "$FINAL21DG" "Status: SUCCESS" "dangerous posture succeeds a write task via --dangerously-skip-permissions, not the allow-list"
if [ -d "./tmp/agent-delegation/$HANDLE21DG/agy-cfg/antigravity-cli" ]; then
  pass "dangerous posture still gets a --gemini_dir config dir (uniform invocation)"
else
  fail "dangerous posture's --gemini_dir config dir missing"
fi
echo

# ---------------------------------------------------------------------------
# 22. DF1/DF2: read-only posture read task succeeds; read-only posture
#     WRITE attempt is auto-denied by the allow-list -> NO_OUTPUT with the
#     permission hint surfaced verbatim.
# ---------------------------------------------------------------------------
echo "--- 22. read-only reads succeed, read-only writes -> NO_OUTPUT with hint ---"
OUT22R=$(MOCK_AGY_SESSION_ID="22220000-0000-4000-8000-000000000001" MOCK_AGY_ACTION=read run_extdel_agy start --cli agy --prompt "read task" --posture read-only)
HANDLE22R=$(extract_field "$OUT22R" "Handle")
FINAL22R=$(poll_until_terminal "$HANDLE22R" 10)
assert_contains "$FINAL22R" "Status: SUCCESS" "read-only posture allows a read task"

OUT22W=$(MOCK_AGY_SESSION_ID="22220000-0000-4000-8000-000000000002" MOCK_AGY_ACTION=write run_extdel_agy start --cli agy --prompt "write task" --posture read-only)
HANDLE22W=$(extract_field "$OUT22W" "Handle")
FINAL22W=$(poll_until_terminal "$HANDLE22W" 10)
assert_contains "$FINAL22W" "Status: NO_OUTPUT" "read-only posture write attempt reports NO_OUTPUT, not a false SUCCESS"
assert_not_contains "$FINAL22W" "Status: SUCCESS" "read-only posture write attempt is never SUCCESS"
assert_contains "$FINAL22W" "auto-denied" "NO_OUTPUT error names the auto-deny"
assert_contains "$FINAL22W" "write_file(*)" "NO_OUTPUT error names the specific denied permission"
assert_contains "$FINAL22W" "gemini_dir allow-list" "NO_OUTPUT error tells the caller how to fix it (allow-list or dangerous posture)"
echo

# ---------------------------------------------------------------------------
# 23. DF1: workspace posture grants the write task -> SUCCESS.
# ---------------------------------------------------------------------------
echo "--- 23. workspace posture write -> SUCCESS ---"
OUT23=$(MOCK_AGY_SESSION_ID="23230000-0000-4000-8000-000000000001" MOCK_AGY_ACTION=write run_extdel_agy start --cli agy --prompt "write task under workspace" --posture workspace)
HANDLE23=$(extract_field "$OUT23" "Handle")
FINAL23=$(poll_until_terminal "$HANDLE23" 10)
assert_contains "$FINAL23" "Status: SUCCESS" "workspace posture allows a write task"
SLICE23=$(run_extdel_agy slice "$HANDLE23")
assert_contains "$SLICE23" "mock agy answer for: write task under workspace" "slice returns the workspace write task's answer"
echo

# ---------------------------------------------------------------------------
# 24. DF2: a genuinely empty-but-legitimate answer (exit 0, blank stdout,
#     NO permission-shaped stderr at all) is STILL reported as NO_OUTPUT —
#     not a crash, not a silently-accepted empty SUCCESS — but WITHOUT a
#     fabricated permission hint, since there isn't one.
# ---------------------------------------------------------------------------
echo "--- 24. NO_OUTPUT on a genuinely empty exit-0 answer (no permission hint) ---"
OUT24=$(MOCK_AGY_SESSION_ID="24240000-0000-4000-8000-000000000001" MOCK_AGY_EMPTY_LEGIT=1 run_extdel_agy start --cli agy --prompt "will produce nothing" --posture read-only)
HANDLE24=$(extract_field "$OUT24" "Handle")
FINAL24=$(poll_until_terminal "$HANDLE24" 10)
assert_contains "$FINAL24" "Status: NO_OUTPUT" "a genuinely empty exit-0 answer reports NO_OUTPUT"
assert_not_contains "$FINAL24" "auto-denied" "no fabricated permission hint when there was no permission problem"
assert_contains "$FINAL24" "produced no output" "generic NO_OUTPUT explanation is present"
echo

echo "=== Results: $PASS passed, $FAIL failed ==="
if [ "$FAIL" -gt 0 ]; then
  exit 1
fi
exit 0
