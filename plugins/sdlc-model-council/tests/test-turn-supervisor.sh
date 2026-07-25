#!/usr/bin/env bash
# Direct regression tests for turn-supervisor.pl's DF3 signal/fork/alarm
# hardening (issue #232). Invokes the supervisor directly against tiny
# mock commands — no extdel.sh, no codex/agy, no API quota — so these
# tests probe the supervisor's own signal-handling contract in isolation
# from the handle/lock/status machinery already covered by
# test-extdel-{codex,agy}-resume.sh (which exercise this SAME
# turn-supervisor.pl through extdel.sh's spawn_daemon, including their
# own "stop kills a mid-flight turn" and "signal-aware exit code" cases —
# those give the child a full 1s head start before signalling, so they
# don't probe the tight startup window this suite adds).
#
# TIMING NOTE (read before "fixing" a flaky run): precise fork/signal
# races are inherently hard to force from an external shell script.
# During development this suite's timings were checked empirically
# against both the pre-fix and post-fix turn-supervisor.pl on this
# platform (perl 5.34, macOS):
#   - Sending TERM with NO delay at all after backgrounding perl almost
#     always lands before the perl interpreter has finished loading
#     (module compile time alone is ~10-20ms here) — i.e. before ANY
#     script code, fixed or not, has run. That's a real but DIFFERENT
#     and unfixable race (no process-level fix can protect code that
#     hasn't started executing yet), so test (a) below uses a short
#     (50ms) delay, empirically 10/10 reliable, chosen to land after
#     interpreter startup but still far earlier than every existing
#     mid-flight-stop test's 1s head start.
#   - The literal historic fork-to-handler-install gap the DF3 #1 fix
#     closes (see turn-supervisor.pl's own header) is on the order of a
#     handful of Perl statements — empirically too narrow to reliably
#     land an externally-timed signal inside it on an otherwise-idle
#     dev machine (both pre-fix and post-fix code passed a 1-30ms delay
#     sweep cleanly in testing). That the fix is structurally correct —
#     SIGTERM/SIGINT/SIGALRM are blocked via sigprocmask as the very
#     first executable statement, before fork() — is therefore verified
#     by code inspection, not by a timing race in this suite. Test (a)'s
#     real job is the observable regression guard: TERM delivered as
#     early as this harness can reliably manage still tears down
#     cleanly, every time.
#   - Test (d)'s "second TERM during cleanup" needs the FIRST
#     escalation to still be in flight when the second TERM arrives.
#     Against a child that dies immediately on TERM (the default mock),
#     escalate_and_reap() usually completes in well under 100ms, too
#     fast to reliably land a second signal inside — so test (d) uses a
#     second mock (mock-sleep-notrap) that ignores SIGTERM, forcing the
#     full ~5s TERM-then-grace-then-KILL path and giving a wide,
#     reliable window.
#
# Run: bash plugins/sdlc-model-council/tests/test-turn-supervisor.sh

set -u

THIS_DIR="$(cd "$(dirname "$0")" && pwd -P)"
PLUGIN_ROOT="$(cd "$THIS_DIR/.." && pwd -P)"
REPO_ROOT="$(cd "$PLUGIN_ROOT/../.." && pwd -P)"
SUPERVISOR_PL="$PLUGIN_ROOT/scripts/turn-supervisor.pl"
MOCK_SLEEP="$THIS_DIR/fixtures/mock-sleep"
MOCK_SLEEP_NOTRAP="$THIS_DIR/fixtures/mock-sleep-notrap"

# Repo rule: ./tmp, never /tmp — even for scratch test roots.
mkdir -p "$REPO_ROOT/tmp"
TESTROOT="$(mktemp -d "$REPO_ROOT/tmp/turn-supervisor-test.XXXXXX")"
trap 'rm -rf "$TESTROOT"' EXIT

PASS=0
FAIL=0
pass() { PASS=$((PASS + 1)); printf 'PASS: %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf 'FAIL: %s\n' "$1"; }

assert_eq() {
  # assert_eq <actual> <expected> <description>
  if [ "$1" = "$2" ]; then pass "$3"; else fail "$3 (expected '$2', got '$1')"; fi
}

alive() {
  # alive <pid> -> success if a process with that pid exists
  [ -n "$1" ] && kill -0 "$1" 2>/dev/null
}

wait_for_file() {
  # wait_for_file <path> <max_seconds> — polls until the file is
  # non-empty or the budget runs out.
  f="$1"; max="$2"; n=0
  while [ "$n" -lt "$max" ]; do
    [ -s "$f" ] && return 0
    sleep 1
    n=$((n + 1))
  done
  [ -s "$f" ]
}

wait_for_child_pidfile() {
  # wait_for_child_pidfile <path> — the mock writes its own pid almost
  # immediately; bounded short poll, not a full wait_for_file budget.
  f="$1"; n=0
  while [ "$n" -lt 50 ] && [ ! -s "$f" ]; do sleep 0.1; n=$((n + 1)); done
  [ -s "$f" ]
}

# new_turn_dir <name> -> prints a fresh directory with a pre-created
# turn-lock (mimicking extdel.sh's acquire_turn_lock precondition: the
# lock dir must already exist, with an owner.pid, before the supervisor
# is spawned) and the empty prompt/events/stderr files the supervisor
# expects to be able to open for redirection.
new_turn_dir() {
  d="$TESTROOT/$1"
  mkdir -p "$d"
  mkdir "$d/.turn-lock"
  printf '%s' "$$" > "$d/.turn-lock/owner.pid"   # acquiring-shell stand-in
  : > "$d/prompt.txt"
  : > "$d/events.jsonl"
  : > "$d/stderr.log"
  printf '%s' "$d"
}

echo "=== turn-supervisor.pl direct regression suite (DF3) ==="
echo "TESTROOT=$TESTROOT"
echo

# ---------------------------------------------------------------------------
# (a) Stop signal delivered VERY EARLY — right after submit, well before
# the existing suites' 1s head start — still kills the child, writes an
# exit code, and releases the lock (no orphan). See the TIMING NOTE above
# for what this test can and cannot prove about the exact DF3 #1/#2
# race window.
# ---------------------------------------------------------------------------
echo "--- (a) stop signal delivered very early ---"
DIR_A=$(new_turn_dir "a")
CHILD_PIDFILE_A="$DIR_A/child.pid"

perl "$SUPERVISOR_PL" 30 "$DIR_A/prompt.txt" "$DIR_A/events.jsonl" "$DIR_A/stderr.log" \
  "$DIR_A/exit.code" "$DIR_A/.turn-lock" -- "$MOCK_SLEEP" "$CHILD_PIDFILE_A" 20 &
SUP_PID_A=$!

perl -e 'select(undef, undef, undef, 0.05)'   # ~50ms — see TIMING NOTE
kill -TERM "$SUP_PID_A" 2>/dev/null

wait_for_file "$DIR_A/exit.code" 10
if [ -s "$DIR_A/exit.code" ]; then
  pass "exit.code was written after a very-early TERM"
else
  fail "exit.code was NOT written after a very-early TERM"
fi
CODE_A=$(cat "$DIR_A/exit.code" 2>/dev/null | tr -d '[:space:]')
assert_eq "$CODE_A" "143" "very-early TERM yields exit code 143 (128+SIGTERM)"

wait_for_child_pidfile "$CHILD_PIDFILE_A"
CHILD_PID_A=$(cat "$CHILD_PIDFILE_A" 2>/dev/null)
if alive "$CHILD_PID_A"; then
  fail "mock child (pid $CHILD_PID_A) is still alive after a very-early TERM (orphan)"
else
  pass "mock child is gone after a very-early TERM (no orphan)"
fi

if alive "$SUP_PID_A"; then
  fail "supervisor pid $SUP_PID_A is still alive after TERM"
else
  pass "supervisor process is gone after a very-early TERM"
fi

if [ -d "$DIR_A/.turn-lock" ]; then
  fail "turn-lock still present after a very-early TERM"
else
  pass "turn-lock released after a very-early TERM"
fi
wait "$SUP_PID_A" 2>/dev/null
echo

# ---------------------------------------------------------------------------
# (b) A genuine timeout still yields 124 and a killed child.
# ---------------------------------------------------------------------------
echo "--- (b) genuine timeout ---"
DIR_B=$(new_turn_dir "b")
CHILD_PIDFILE_B="$DIR_B/child.pid"

perl "$SUPERVISOR_PL" 2 "$DIR_B/prompt.txt" "$DIR_B/events.jsonl" "$DIR_B/stderr.log" \
  "$DIR_B/exit.code" "$DIR_B/.turn-lock" -- "$MOCK_SLEEP" "$CHILD_PIDFILE_B" 20 &
SUP_PID_B=$!

wait_for_file "$DIR_B/exit.code" 15
CODE_B=$(cat "$DIR_B/exit.code" 2>/dev/null | tr -d '[:space:]')
assert_eq "$CODE_B" "124" "a real timeout yields exit code 124"

wait_for_child_pidfile "$CHILD_PIDFILE_B"
CHILD_PID_B=$(cat "$CHILD_PIDFILE_B" 2>/dev/null)
if alive "$CHILD_PID_B"; then
  fail "mock child (pid $CHILD_PID_B) is still alive after a timeout"
else
  pass "mock child is gone after a timeout"
fi
if [ -d "$DIR_B/.turn-lock" ]; then
  fail "turn-lock still present after a timeout"
else
  pass "turn-lock released after a timeout"
fi
wait "$SUP_PID_B" 2>/dev/null
echo

# ---------------------------------------------------------------------------
# (c) Signal-death of the CHILD ITSELF (not a stop signal to the
# supervisor) yields 128+signum, never a false 0 — exercises
# compute_exit_code's plain (non-escalation) waitpid path in the main
# eval, distinct from (a)'s escalate_and_reap path.
# ---------------------------------------------------------------------------
echo "--- (c) signal-death of the child (plain waitpid path) ---"
DIR_C=$(new_turn_dir "c")
CHILD_PIDFILE_C="$DIR_C/child.pid"

perl "$SUPERVISOR_PL" 30 "$DIR_C/prompt.txt" "$DIR_C/events.jsonl" "$DIR_C/stderr.log" \
  "$DIR_C/exit.code" "$DIR_C/.turn-lock" -- "$MOCK_SLEEP" "$CHILD_PIDFILE_C" 20 &
SUP_PID_C=$!

if wait_for_child_pidfile "$CHILD_PIDFILE_C"; then
  CHILD_PID_C=$(cat "$CHILD_PIDFILE_C" 2>/dev/null)
  kill -KILL "$CHILD_PID_C" 2>/dev/null
  pass "sent SIGKILL directly to the mock child (pid $CHILD_PID_C)"
else
  fail "never observed the mock child's pid — cannot exercise this test"
fi

wait_for_file "$DIR_C/exit.code" 10
CODE_C=$(cat "$DIR_C/exit.code" 2>/dev/null | tr -d '[:space:]')
assert_eq "$CODE_C" "137" "a directly-signal-killed child (SIGKILL) reports 137 (128+9), not 0"
if [ -d "$DIR_C/.turn-lock" ]; then
  fail "turn-lock still present after a direct child kill"
else
  pass "turn-lock released after a direct child kill"
fi
wait "$SUP_PID_C" 2>/dev/null
echo

# ---------------------------------------------------------------------------
# (d) A second TERM arriving while the first is still mid-escalation does
# not corrupt or abandon the outcome: exit.code still ends up holding
# exactly one valid, correct value and the lock is still cleanly
# released (DF3 #4 — the old `exit 0 if $terminating` guard could bail
# out on the SECOND signal before exit.code was written). Uses
# mock-sleep-notrap (ignores SIGTERM) so escalate_and_reap()'s ~5s
# grace window is wide enough to reliably land a second signal inside
# it — see the TIMING NOTE.
# ---------------------------------------------------------------------------
echo "--- (d) second TERM during cleanup ---"
DIR_D=$(new_turn_dir "d")
CHILD_PIDFILE_D="$DIR_D/child.pid"

perl "$SUPERVISOR_PL" 30 "$DIR_D/prompt.txt" "$DIR_D/events.jsonl" "$DIR_D/stderr.log" \
  "$DIR_D/exit.code" "$DIR_D/.turn-lock" -- "$MOCK_SLEEP_NOTRAP" "$CHILD_PIDFILE_D" 20 &
SUP_PID_D=$!

wait_for_child_pidfile "$CHILD_PIDFILE_D"
kill -TERM "$SUP_PID_D" 2>/dev/null
sleep 1   # comfortably inside the ~5s TERM-then-grace escalation window
kill -TERM "$SUP_PID_D" 2>/dev/null

wait_for_file "$DIR_D/exit.code" 10
CODE_D=$(cat "$DIR_D/exit.code" 2>/dev/null | tr -d '[:space:]')
assert_eq "$CODE_D" "137" "a second TERM during cleanup still ends in a clean 137 (escalated to KILL), not a corrupted/empty value"

CHILD_PID_D=$(cat "$CHILD_PIDFILE_D" 2>/dev/null)
if alive "$CHILD_PID_D"; then
  fail "mock child (pid $CHILD_PID_D) is still alive after a double TERM (orphan)"
else
  pass "mock child is gone after a double TERM (no orphan)"
fi
if [ -d "$DIR_D/.turn-lock" ]; then
  fail "turn-lock still present after a double TERM"
else
  pass "turn-lock released after a double TERM"
fi
wait "$SUP_PID_D" 2>/dev/null
echo

echo "=== Results: $PASS passed, $FAIL failed ==="
if [ "$FAIL" -gt 0 ]; then
  exit 1
fi
exit 0
