#!/usr/bin/env bash
# Test harness for extdel.sh's opencode-resume path (issue #232, F2 — the
# "adding a backend = one directory, zero engine edits" acceptance test;
# see docs/superpowers/specs/2026-07-24-sdlc-simple-orchestration-design.md
# §4). Exercises extdel.sh entirely against a MOCK `opencode` binary placed
# first on PATH, with HOME redirected to a throwaway directory — the real
# opencode CLI is never invoked here (see this build's separately-recorded
# P-OC2b live probe for the only real-CLI call this task made). Bash-3.2-
# safe, matching extdel.sh's own target shell, and structured to mirror
# test-extdel-codex-resume.sh / test-extdel-agy-resume.sh exactly: every
# assertion drives the real `start`/`prompt`/`status`/`slice`/`stop`
# subcommands, never a workaround.
#
# Run: bash plugins/sdlc-simple-orchestration/tests/test-extdel-opencode-resume.sh

set -u

THIS_DIR="$(cd "$(dirname "$0")" && pwd -P)"
PLUGIN_ROOT="$(cd "$THIS_DIR/.." && pwd -P)"
REPO_ROOT="$(cd "$PLUGIN_ROOT/../.." && pwd -P)"
EXTDEL="$PLUGIN_ROOT/scripts/extdel.sh"
MOCK_BIN="$THIS_DIR/fixtures/mock-bin"

# Repo rule: ./tmp, never /tmp — even for scratch test roots.
mkdir -p "$REPO_ROOT/tmp"
TESTROOT="$(mktemp -d "$REPO_ROOT/tmp/extdel-opencode-test.XXXXXX")"
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
  # extract_field <block> <label>   — pulls "- <label>: VALUE" (first match)
  printf '%s\n' "$1" | grep -m1 "^- $2:" | sed -E "s/^- $2:[[:space:]]*//" | awk '{print $1}'
}

FAKE_HOME="$TESTROOT/fake-home"
mkdir -p "$FAKE_HOME"
export HOME="$FAKE_HOME"

run_extdel_oc() {
  PATH="$MOCK_BIN:$PATH" "$EXTDEL" "$@"
}

poll_until_terminal() {
  # poll_until_terminal <handle> <max_seconds> -> prints final status block
  handle="$1"; max="$2"
  n=0
  while [ "$n" -lt "$max" ]; do
    out=$(run_extdel_oc status "$handle" --wait-s 2)
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

echo "=== extdel.sh opencode-resume test suite ==="
echo "TESTROOT=$TESTROOT"
echo "FAKE_HOME=$FAKE_HOME"
echo

cd "$TESTROOT" || exit 1

# ---------------------------------------------------------------------------
# 1. Handle creation
# ---------------------------------------------------------------------------
echo "--- 1. handle creation ---"
OUT1=$(MOCK_OPENCODE_SESSION_ID="ses_11111111aaaa" run_extdel_oc start --cli opencode --prompt "hello opencode" --posture read-only)
assert_contains "$OUT1" "Status: RUNNING" "start returns RUNNING immediately"
assert_contains "$OUT1" "CLI: opencode" "return block reports CLI: opencode"
HANDLE1=$(extract_field "$OUT1" "Handle")
if [ -n "$HANDLE1" ] && [ -d "./tmp/simple-orchestration/$HANDLE1" ]; then
  pass "handle directory created: $HANDLE1"
else
  fail "handle directory NOT created (handle='$HANDLE1')"
fi
if [ -f "./tmp/simple-orchestration/$HANDLE1/meta.json" ] && [ -f "./tmp/simple-orchestration/$HANDLE1/turn-001.prompt.txt" ]; then
  pass "meta.json and turn-001.prompt.txt exist"
else
  fail "meta.json or turn-001.prompt.txt missing"
fi
META_CLI=$(jq -r '.cli' "./tmp/simple-orchestration/$HANDLE1/meta.json" 2>/dev/null)
META_POSTURE=$(jq -r '.posture' "./tmp/simple-orchestration/$HANDLE1/meta.json" 2>/dev/null)
PROMPT_CONTENT=$(cat "./tmp/simple-orchestration/$HANDLE1/turn-001.prompt.txt" 2>/dev/null)
[ "$META_CLI" = "opencode" ] && pass "meta.json cli=opencode" || fail "meta.json cli was '$META_CLI'"
[ "$META_POSTURE" = "read-only" ] && pass "meta.json posture=read-only" || fail "meta.json posture was '$META_POSTURE'"
[ "$PROMPT_CONTENT" = "hello opencode" ] && pass "turn-001.prompt.txt has the exact prompt text" || fail "prompt file content was '$PROMPT_CONTENT'"
echo

# ---------------------------------------------------------------------------
# 2. id capture from the sessionID carried on every --format json event
#    (§4.4 P-OC5b) — real `status` call, real turn-supervisor.pl lifecycle.
# ---------------------------------------------------------------------------
echo "--- 2. id capture from sessionID ---"
FINAL1=$(poll_until_terminal "$HANDLE1" 15)
assert_contains "$FINAL1" "Status: SUCCESS" "handle1 turn 1 reaches SUCCESS"
assert_contains "$FINAL1" "ses_11111111aaaa" "captured session id matches the mock's minted sessionID"
CAPTURED_SID=$(jq -r '.session_id' "./tmp/simple-orchestration/$HANDLE1/meta.json" 2>/dev/null)
[ "$CAPTURED_SID" = "ses_11111111aaaa" ] && pass "meta.json.session_id persisted" || fail "meta.json.session_id was '$CAPTURED_SID'"
[ -f "./tmp/simple-orchestration/$HANDLE1/session.id" ] && pass "session.id file written" || fail "session.id file missing"
echo

# ---------------------------------------------------------------------------
# 3. Submit-then-poll lifecycle + RUNNING -> SUCCESS transition
# ---------------------------------------------------------------------------
echo "--- 3. submit-then-poll lifecycle / RUNNING -> SUCCESS ---"
OUT2=$(MOCK_OPENCODE_SESSION_ID="ses_22222222bbbb" MOCK_OPENCODE_SLEEP=2 run_extdel_oc start --cli opencode --prompt "slow first turn" --posture read-only)
HANDLE2=$(extract_field "$OUT2" "Handle")
assert_contains "$OUT2" "Status: RUNNING" "turn2 handle starts RUNNING"

IMMEDIATE=$(run_extdel_oc status "$HANDLE2" --wait-s 0)
assert_contains "$IMMEDIATE" "Status: RUNNING" "immediate zero-wait status still RUNNING (mock is sleeping)"

sleep 3
FINAL2=$(run_extdel_oc status "$HANDLE2" --wait-s 5)
assert_contains "$FINAL2" "Status: SUCCESS" "status transitions to SUCCESS once the mock finishes"
assert_contains "$FINAL2" "Turn: 1" "SUCCESS report shows turn 1"
echo

# ---------------------------------------------------------------------------
# 4. Multi-turn resume via --session (never bare --continue, §4.4) — real
#    `prompt` call.
# ---------------------------------------------------------------------------
echo "--- 4. multi-turn resume via --session ---"
TURN2_OUT=$(MOCK_OPENCODE_SESSION_ID="ses_should_be_ignored" run_extdel_oc prompt "$HANDLE1" --prompt "turn 2 prompt")
assert_contains "$TURN2_OUT" "Status: RUNNING" "turn 2 submitted"
FINAL_T2=$(poll_until_terminal "$HANDLE1" 15)
assert_contains "$FINAL_T2" "Status: SUCCESS" "turn 2 reaches SUCCESS"
assert_contains "$FINAL_T2" "Turn: 2" "SUCCESS report shows turn 2"
assert_contains "$FINAL_T2" "ses_11111111aaaa" "turn 2's report still carries the ORIGINAL captured session id (resumed, not re-minted)"
RUNSCRIPT2="./tmp/simple-orchestration/$HANDLE1/turn-002.run.sh"
if [ -f "$RUNSCRIPT2" ]; then
  assert_contains "$(cat "$RUNSCRIPT2")" "--session ses_11111111aaaa" "turn 2's composed command resumes via --session with the CAPTURED id"
  assert_not_contains "$(cat "$RUNSCRIPT2")" " -m " "turn 2 does NOT re-pass -m (model is a session-time property, per turn 1 only)"
  assert_not_contains "$(cat "$RUNSCRIPT2")" "--variant" "turn 2 does NOT re-pass --variant"
else
  fail "turn-002.run.sh was not written"
fi
SLICE_T2=$(run_extdel_oc slice "$HANDLE1")
assert_contains "$SLICE_T2" "mock opencode answer for: turn 2 prompt" "slice returns turn 2's own answer, not turn 1's"
echo

# ---------------------------------------------------------------------------
# 5. slice + truncation
# ---------------------------------------------------------------------------
echo "--- 5. slice ---"
SLICE_TRUNC=$(run_extdel_oc slice "$HANDLE1" --max-chars 5)
assert_contains "$SLICE_TRUNC" "truncated" "slice --max-chars 5 truncates the answer"
FIRST_LINE_LEN=$(printf '%s' "$SLICE_TRUNC" | head -1 | awk '{print length}')
if [ "$FIRST_LINE_LEN" -le 5 ]; then
  pass "truncated first line is <= max-chars (was $FIRST_LINE_LEN)"
else
  fail "truncated first line exceeded max-chars (was $FIRST_LINE_LEN)"
fi
echo

# ---------------------------------------------------------------------------
# 6. Pinned-posture refusal
# ---------------------------------------------------------------------------
echo "--- 6. pinned-posture refusal ---"
REFUSED=$(run_extdel_oc prompt "$HANDLE1" --prompt "turn3 attempt" --posture workspace)
assert_contains "$REFUSED" "Status: ERROR" "posture mismatch without --steal is refused"
assert_contains "$REFUSED" "differs from this handle's pinned posture" "refusal message explains the pinned-posture mismatch"
POSTURE_AFTER_REFUSAL=$(jq -r '.posture' "./tmp/simple-orchestration/$HANDLE1/meta.json" 2>/dev/null)
[ "$POSTURE_AFTER_REFUSAL" = "read-only" ] && pass "pinned posture unchanged after refused attempt" || fail "pinned posture mutated to '$POSTURE_AFTER_REFUSAL'"

STOLEN=$(run_extdel_oc prompt "$HANDLE1" --prompt "turn3 with steal" --posture workspace --steal)
assert_contains "$STOLEN" "Status: RUNNING" "posture escalation succeeds with --steal"
STOLEN_FINAL=$(poll_until_terminal "$HANDLE1" 15)
assert_contains "$STOLEN_FINAL" "Status: SUCCESS" "stolen turn 3 completes"
assert_contains "$STOLEN_FINAL" "Turn: 3" "stolen turn reports turn 3"
POSTURE_AFTER_STEAL=$(jq -r '.posture' "./tmp/simple-orchestration/$HANDLE1/meta.json" 2>/dev/null)
[ "$POSTURE_AFTER_STEAL" = "workspace" ] && pass "pinned posture updated after --steal" || fail "pinned posture after steal was '$POSTURE_AFTER_STEAL'"
SETTINGS_AFTER_STEAL="./tmp/simple-orchestration/$HANDLE1/opencode-cfg/opencode.json"
if jq -e '.permission.edit=="allow" and .permission.bash=="allow"' "$SETTINGS_AFTER_STEAL" >/dev/null 2>&1; then
  pass "OPENCODE_CONFIG was refreshed to the escalated (workspace) posture on the stolen turn"
else
  fail "OPENCODE_CONFIG was not refreshed after --steal: $(cat "$SETTINGS_AFTER_STEAL" 2>/dev/null)"
fi
echo

# ---------------------------------------------------------------------------
# 7. Per-handle OPENCODE_CONFIG content matches the posture, by posture —
#    read-only denies edit/bash/webfetch; workspace allows edit/bash but
#    still denies webfetch; dangerous allows all three (content — --auto
#    is what actually drives the mock/real CLI for dangerous).
# ---------------------------------------------------------------------------
echo "--- 7. per-handle OPENCODE_CONFIG matches the posture ---"
OUT7RO=$(MOCK_OPENCODE_SESSION_ID="ses_ro00000001" run_extdel_oc start --cli opencode --prompt "ro config check" --posture read-only)
H7RO=$(extract_field "$OUT7RO" "Handle")
poll_until_terminal "$H7RO" 15 >/dev/null
CFG7RO="./tmp/simple-orchestration/$H7RO/opencode-cfg/opencode.json"
if [ -f "$CFG7RO" ]; then
  pass "read-only handle's opencode.json exists"
else
  fail "read-only handle's opencode.json missing"
fi
if jq -e '.permission.edit=="deny" and .permission.bash=="deny" and .permission.webfetch=="deny"' "$CFG7RO" >/dev/null 2>&1; then
  pass "read-only config denies edit/bash/webfetch"
else
  fail "read-only config did not deny edit/bash/webfetch: $(cat "$CFG7RO" 2>/dev/null)"
fi

OUT7WS=$(MOCK_OPENCODE_SESSION_ID="ses_ws00000001" run_extdel_oc start --cli opencode --prompt "ws config check" --posture workspace)
H7WS=$(extract_field "$OUT7WS" "Handle")
poll_until_terminal "$H7WS" 15 >/dev/null
CFG7WS="./tmp/simple-orchestration/$H7WS/opencode-cfg/opencode.json"
if jq -e '.permission.edit=="allow" and .permission.bash=="allow" and .permission.webfetch=="deny"' "$CFG7WS" >/dev/null 2>&1; then
  pass "workspace config allows edit/bash but still denies webfetch"
else
  fail "workspace config did not match expected allow/deny shape: $(cat "$CFG7WS" 2>/dev/null)"
fi

OUT7DG=$(MOCK_OPENCODE_SESSION_ID="ses_dg00000001" MOCK_OPENCODE_ACTION=webfetch run_extdel_oc start --cli opencode --prompt "dangerous config check" --posture dangerous)
H7DG=$(extract_field "$OUT7DG" "Handle")
FINAL7DG=$(poll_until_terminal "$H7DG" 15)
assert_contains "$FINAL7DG" "Status: SUCCESS" "dangerous posture succeeds a webfetch-needing task via --auto, not the config alone"
CFG7DG="./tmp/simple-orchestration/$H7DG/opencode-cfg/opencode.json"
if jq -e '.permission.edit=="allow" and .permission.bash=="allow" and .permission.webfetch=="allow"' "$CFG7DG" >/dev/null 2>&1; then
  pass "dangerous config allows edit/bash/webfetch"
else
  fail "dangerous config did not match expected all-allow shape: $(cat "$CFG7DG" 2>/dev/null)"
fi
echo

# ---------------------------------------------------------------------------
# 8. DF2-shaped NO_OUTPUT: a genuinely empty exit-0 answer, and a
#    permission-denied write attempt under read-only — both must report
#    NO_OUTPUT, never a false SUCCESS; only the latter gets a hint.
# ---------------------------------------------------------------------------
echo "--- 8. NO_OUTPUT on empty / permission-denied answers ---"
OUT8A=$(MOCK_OPENCODE_SESSION_ID="ses_empty0001" MOCK_OPENCODE_EMPTY=1 run_extdel_oc start --cli opencode --prompt "will produce nothing" --posture read-only)
HANDLE8A=$(extract_field "$OUT8A" "Handle")
FINAL8A=$(poll_until_terminal "$HANDLE8A" 15)
assert_contains "$FINAL8A" "Status: NO_OUTPUT" "a genuinely empty exit-0 answer reports NO_OUTPUT"
assert_not_contains "$FINAL8A" "Status: SUCCESS" "a genuinely empty exit-0 answer is never SUCCESS"
assert_contains "$FINAL8A" "produced no output" "generic NO_OUTPUT explanation is present"

OUT8B=$(MOCK_OPENCODE_SESSION_ID="ses_denied001" MOCK_OPENCODE_ACTION=edit run_extdel_oc start --cli opencode --prompt "write task under read-only" --posture read-only)
HANDLE8B=$(extract_field "$OUT8B" "Handle")
FINAL8B=$(poll_until_terminal "$HANDLE8B" 15)
assert_contains "$FINAL8B" "Status: NO_OUTPUT" "a read-only-posture write attempt reports NO_OUTPUT, not a false SUCCESS"
assert_not_contains "$FINAL8B" "Status: SUCCESS" "a read-only-posture write attempt is never SUCCESS"
assert_contains "$FINAL8B" "edit" "NO_OUTPUT error names the specific denied permission ('edit')"

OUT8C=$(MOCK_OPENCODE_SESSION_ID="ses_wsok00001" MOCK_OPENCODE_ACTION=edit run_extdel_oc start --cli opencode --prompt "write task under workspace" --posture workspace)
HANDLE8C=$(extract_field "$OUT8C" "Handle")
FINAL8C=$(poll_until_terminal "$HANDLE8C" 15)
assert_contains "$FINAL8C" "Status: SUCCESS" "workspace posture allows the same write task to succeed"
SLICE8C=$(run_extdel_oc slice "$HANDLE8C")
assert_contains "$SLICE8C" "mock opencode answer for: write task under workspace" "slice returns the workspace write task's answer"
echo

# ---------------------------------------------------------------------------
# 9. Leading-dash prompt refused (§4.4: prompt is a positional; mirrors
#    agy's §9.12 m3 guard rather than gambling on an unconfirmed `--`).
# ---------------------------------------------------------------------------
echo "--- 9. leading-dash prompt refused ---"
OUT9=$(run_extdel_oc start --cli opencode --prompt "-oops this looks like a flag" --posture read-only 2>&1)
assert_contains "$OUT9" "Status: ERROR" "a leading-dash prompt is refused, not silently misparsed"
assert_contains "$OUT9" "BAD_PROMPT" "refusal is the BAD_PROMPT code, not a generic failure"
echo

# ---------------------------------------------------------------------------
# 10. Missing-CLI / uninitialized-auth ERRORs
# ---------------------------------------------------------------------------
echo "--- 10. missing opencode CLI / no models -> ERROR ---"
MINIMAL_PATH="/usr/bin:/bin"
OUT10A=$(PATH="$MINIMAL_PATH" HOME="$TESTROOT/no-opencode-home" "$EXTDEL" start --cli opencode --prompt "no opencode anywhere" --posture read-only 2>&1)
assert_contains "$OUT10A" "Status: ERROR" "missing opencode binary is reported as ERROR"
assert_contains "$OUT10A" "opencode not found" "missing-CLI message names the missing binary"

OUT10B=$(MOCK_OPENCODE_NO_MODELS=1 run_extdel_oc start --cli opencode --prompt "no models available" --posture read-only 2>&1)
assert_contains "$OUT10B" "Status: ERROR" "an empty 'opencode models' list is reported as ERROR"
assert_contains "$OUT10B" "not authenticated" "the no-models case is explained as an auth/availability problem"
echo

# ---------------------------------------------------------------------------
# 11. stop
# ---------------------------------------------------------------------------
echo "--- 11. stop ---"
STOP_OUT=$(run_extdel_oc stop "$HANDLE1")
assert_contains "$STOP_OUT" "STOPPED: $HANDLE1" "stop reports the handle as stopped"
CLOSED=$(jq -r '.closed' "./tmp/simple-orchestration/$HANDLE1/meta.json" 2>/dev/null)
[ "$CLOSED" != "null" ] && [ -n "$CLOSED" ] && pass "meta.json.closed timestamp set" || fail "meta.json.closed was '$CLOSED'"
echo

# ---------------------------------------------------------------------------
# 12. stop kills a genuinely mid-flight turn — no orphan, exit.code
#     written, lock released, signal-aware exit code (128+SIGTERM).
# ---------------------------------------------------------------------------
echo "--- 12. stop on a genuinely mid-flight turn ---"
OUT12=$(MOCK_OPENCODE_SESSION_ID="ses_stop00001" MOCK_OPENCODE_SLEEP=6 run_extdel_oc start --cli opencode --prompt "will be stopped mid-flight" --posture read-only)
HANDLE12=$(extract_field "$OUT12" "Handle")
assert_contains "$OUT12" "Status: RUNNING" "handle12 starts RUNNING (mid-flight stop target)"

sleep 1
STOP_OUT12=$(run_extdel_oc stop "$HANDLE12")
assert_contains "$STOP_OUT12" "STOPPED: $HANDLE12" "stop reports the mid-flight handle as stopped"

CODE12=$(cat "./tmp/simple-orchestration/$HANDLE12/turn-001.exit.code" 2>/dev/null | tr -d '[:space:]')
if [ "$CODE12" = "143" ]; then
  pass "TERM-killed turn's exit code is 128+SIGTERM=143, not misreported as 0"
else
  fail "expected exit code 143 (128+SIGTERM) for a TERM-killed turn, got '$CODE12'"
fi
if [ -d "./tmp/simple-orchestration/$HANDLE12/.turn-lock" ]; then
  fail "turn-lock still present after stop"
else
  pass "turn-lock released after stop"
fi
STATUS12=$(run_extdel_oc status "$HANDLE12" --wait-s 2)
assert_contains "$STATUS12" "Status: FAILURE" "stopped mid-flight turn reports a terminal non-SUCCESS status, not RUNNING"
echo

# ---------------------------------------------------------------------------
# 13. Turn mutex — concurrent prompt refused
# ---------------------------------------------------------------------------
echo "--- 13. turn mutex (concurrent prompt refused) ---"
OUT13=$(MOCK_OPENCODE_SESSION_ID="ses_mutex0001" run_extdel_oc start --cli opencode --prompt "mutex turn 1" --posture read-only)
HANDLE13=$(extract_field "$OUT13" "Handle")
poll_until_terminal "$HANDLE13" 15 >/dev/null

SLOW=$(MOCK_OPENCODE_SLEEP=4 run_extdel_oc prompt "$HANDLE13" --prompt "mutex turn 2 (slow)")
assert_contains "$SLOW" "Status: RUNNING" "slow turn 2 submitted"

CONCURRENT=$(run_extdel_oc prompt "$HANDLE13" --prompt "mutex turn 3 (should be refused)")
assert_contains "$CONCURRENT" "Status: ERROR" "concurrent prompt while turn 2 in flight is refused"
assert_contains "$CONCURRENT" "already in progress" "refusal message names the in-flight turn"

SLOW_FINAL=$(poll_until_terminal "$HANDLE13" 15)
assert_contains "$SLOW_FINAL" "Status: SUCCESS" "slow turn 2 eventually completes"
assert_contains "$SLOW_FINAL" "Turn: 2" "completed turn is turn 2 (turn 3 was never accepted)"
echo

# ---------------------------------------------------------------------------
# 14. Path-traversal handle rejected by every handle-taking subcommand.
# ---------------------------------------------------------------------------
echo "--- 14. path-traversal handle rejected everywhere ---"
BAD_HANDLE="../../../etc"
STATUS_BAD=$(run_extdel_oc status "$BAD_HANDLE" 2>&1)
assert_contains "$STATUS_BAD" "Status: ERROR" "status rejects a path-traversal handle"
SLICE_BAD=$(run_extdel_oc slice "$BAD_HANDLE" 2>&1)
assert_contains "$SLICE_BAD" "ERROR" "slice rejects a path-traversal handle"
STOP_BAD=$(run_extdel_oc stop "$BAD_HANDLE" 2>&1)
assert_contains "$STOP_BAD" "ERROR" "stop rejects a path-traversal handle"
PROMPT_BAD=$(run_extdel_oc prompt "$BAD_HANDLE" --prompt "x" 2>&1)
assert_contains "$PROMPT_BAD" "Status: ERROR" "prompt rejects a path-traversal handle"
if [ -e "$TESTROOT/../etc" ] || [ -e "/etc/.turn-lock" ]; then
  fail "a path-traversal handle touched something outside the state dir"
else
  pass "no path-traversal side effects observed outside the state dir"
fi
echo

echo "=== Results: $PASS passed, $FAIL failed ==="
if [ "$FAIL" -gt 0 ]; then
  exit 1
fi
exit 0
