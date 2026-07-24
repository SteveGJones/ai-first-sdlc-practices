#!/usr/bin/env bash
# extdel.sh — external-agent delegation primitives (codex / agy)
#
# Stage 1 + Stage 2 of docs/superpowers/specs/2026-07-23-external-agent-delegation-design.md
# (that spec's §9 is authoritative). This build implements ONLY:
#   cli=codex, mode=resume  — submit-then-poll id-based resume.
# agy support and codex persistent (daemon) mode are later stages and are
# refused with a clear ERROR status rather than attempted.
#
# Target shell: bash 3.2.57 (macOS system bash) / POSIX sh. No associative
# arrays, no `${var,,}`, no reliance on `setsid`/`timeout`/`gtimeout` (all
# three are absent on the target machine). Indexed bash arrays ARE used
# (supported since bash 3.1) for building argv safely.
#
# Subcommands: start | prompt | status | slice | stop | reap
#
# All state lives under ./tmp/agent-delegation/<HANDLE>/ relative to the
# directory extdel.sh is invoked from (the project root) — never /tmp.

# Deliberately no `set -e`: this script does many conditional command
# substitutions (grep/jq lookups that legitimately return empty) and a
# single early failure must not abort a multi-step status/reap sweep.

SCRIPT_SOURCE="$0"
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_SOURCE")" && pwd -P)"
PROJECT_ROOT="$(pwd -P)"
BASE_DIR="$PROJECT_ROOT/tmp/agent-delegation"
SUPERVISOR_PL="$SCRIPT_DIR/turn-supervisor.pl"
MAX_SLICE_CHARS=12000

# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

now_iso() { date -u +%Y-%m-%dT%H:%M:%SZ; }
now_ts_label() { date -u +%Y-%m-%dT%H-%M-%SZ; }
now_epoch() { date +%s; }

rand6() {
  od -An -N3 -tx1 /dev/urandom | tr -d ' \n'
}

display_path() {
  # Render an absolute path under PROJECT_ROOT as ./tmp/... for the
  # caller-facing contract; pass through anything else unchanged.
  case "$1" in
    "$PROJECT_ROOT"/*) printf './%s' "${1#"$PROJECT_ROOT"/}" ;;
    *) printf '%s' "$1" ;;
  esac
}

stat_mtime() {
  case "$(uname -s)" in
    Darwin|*BSD)
      stat -f %m "$1" 2>/dev/null || now_epoch
      ;;
    *)
      stat -c %Y "$1" 2>/dev/null || now_epoch
      ;;
  esac
}

iso_to_epoch() {
  case "$(uname -s)" in
    Darwin|*BSD)
      date -j -u -f "%Y-%m-%dT%H:%M:%SZ" "$1" +%s 2>/dev/null
      ;;
    *)
      date -u -d "$1" +%s 2>/dev/null
      ;;
  esac
}

usage() {
  cat <<'EOF'
Usage: extdel.sh <subcommand> [options]

Subcommands:
  start   --prompt-file F | --prompt TEXT [--cli codex] [--mode resume]
          [--cwd DIR] [--model M] [--effort low|medium|high]
          [--posture read-only|workspace|dangerous] [--timeout-s N]
          [--add-dir DIR ...]
  prompt  <HANDLE> --prompt-file F | --prompt TEXT [--posture P] [--steal]
          [--timeout-s N]
  status  <HANDLE> [--wait-s N]
  slice   <HANDLE> [--max-chars N] [--turn N]
  stop    <HANDLE>
  reap    [--prune-closed AGE_SECONDS]

Stage 2 scope: cli=codex, mode=resume only. agy and codex persistent mode
are not implemented in this build (they return Status: ERROR, not a hang).
EOF
}

die_usage() {
  echo "extdel.sh: $1" >&2
  usage >&2
  exit 1
}

wait_for_file() {
  f="$1"; t="$2"; n=0
  while [ ! -f "$f" ] && [ "$n" -lt "$t" ]; do
    sleep 1
    n=$((n + 1))
  done
}

validate_nonneg_int() {
  case "$1" in
    ''|*[!0-9]*) return 1 ;;
    *) return 0 ;;
  esac
}

validate_handle() {
  # Reject anything that isn't the exact handle grammar (§5.1):
  # <cli>-<mode>-<UTCts>-<rand6>. Handles round-trip through the Haiku
  # wrapper agent's context, including text the delegated (external, and
  # therefore untrusted) model produced — a handle string is effectively
  # attacker-influenced input. Without this, "$BASE_DIR/$handle" lets a
  # handle like `../../..` escape the state dir entirely, and every
  # handle-taking subcommand (prompt/status/slice/stop) would then
  # rm/kill/write outside ./tmp/agent-delegation.
  case "$1" in
    '') return 1 ;;
  esac
  printf '%s' "$1" | grep -Eq '^(codex|agy)-[a-z]+-[0-9TZ:-]+-[0-9a-f]{6}$'
}

# ---------------------------------------------------------------------------
# meta.json helpers (jq-backed, atomic write, serialized against concurrent
# writers). Known concurrent call sites: `status` writes session_id while
# `prompt`/`start` (a separate process) writes turn_count/posture/timeout_s/
# stolen_*. jq's read-modify-write-then-mv is otherwise a last-writer-wins
# race that can silently drop one side's update.
# ---------------------------------------------------------------------------

meta_get() {
  jq -r --arg k "$2" '.[$k] // empty' "$1/meta.json" 2>/dev/null
}

meta_get_array() {
  jq -r --arg k "$2" '.[$k] // [] | .[]' "$1/meta.json" 2>/dev/null
}

meta_lock_acquire() {
  dir="$1"
  ml="$dir/.meta-lock"
  n=0
  while [ "$n" -lt 25 ]; do
    mkdir "$ml" 2>/dev/null && return 0
    n=$((n + 1))
    [ "$n" -gt 20 ] && sleep 1
  done
  return 1
}

meta_lock_release() {
  rmdir "$1/.meta-lock" 2>/dev/null
}

meta_set() {
  # meta_set <dir> <key> str|raw <value>
  dir="$1"; key="$2"; kind="$3"; val="$4"
  mf="$dir/meta.json"
  tmp="$mf.tmp.$$"
  meta_lock_acquire "$dir" || return 1
  if [ "$kind" = "raw" ]; then
    jq --arg k "$key" --argjson v "$val" '.[$k] = $v' "$mf" > "$tmp" 2>/dev/null && mv "$tmp" "$mf"
  else
    jq --arg k "$key" --arg v "$val" '.[$k] = $v' "$mf" > "$tmp" 2>/dev/null && mv "$tmp" "$mf"
  fi
  meta_lock_release "$dir"
}

# ---------------------------------------------------------------------------
# Per-handle turn mutex (§9.8) — mkdir-based, stale-broken at timeout_s+60s.
# The caller MUST hold this lock before writing the turn's prompt file (see
# submit_codex_turn) — acquiring it here, ahead of that write, is what
# prevents two concurrent submitters both computing turn N and racing to
# write turn-00N.prompt.txt, where the loser's write silently overwrites
# the winner's prompt and the winner's detached supervisor executes the
# wrong text.
# ---------------------------------------------------------------------------

acquire_turn_lock() {
  dir="$1"
  lockdir="$dir/.turn-lock"
  if mkdir "$lockdir" 2>/dev/null; then
    printf '%s' "$$" > "$lockdir/owner.pid" 2>/dev/null
    return 0
  fi

  timeout_s=$(meta_get "$dir" timeout_s)
  case "$timeout_s" in ''|*[!0-9]*) timeout_s=600 ;; esac
  stale_after=$((timeout_s + 60))
  mt=$(stat_mtime "$lockdir")
  age=$(( $(now_epoch) - mt ))
  if [ "$age" -gt "$stale_after" ]; then
    # Rename-then-remove, not rm-then-mkdir: two acquirers racing this
    # same stale-break branch could otherwise both `rm -rf` + `mkdir`,
    # with the SECOND one's freshly created lock deleted by the FIRST
    # one's still-in-flight `rm -rf` of the (by-then-recreated) same
    # path. `mv` is atomic — only one racer's rename can succeed; the
    # loser's `mv` fails and it falls through to `return 1` (LOCKED),
    # never touching what the winner just created.
    if mv "$lockdir" "$lockdir.stale.$$" 2>/dev/null; then
      rm -rf "$lockdir.stale.$$"
      if mkdir "$lockdir" 2>/dev/null; then
        printf '%s' "$$" > "$lockdir/owner.pid" 2>/dev/null
        return 0
      fi
    fi
  fi
  return 1
}

lock_is_stale() {
  # lock_is_stale <handle-dir>  -> 0 (stale, safe to reap) | 1 (still live
  # or too young to safely tell). Shared by the sweep-on-entry reaper and
  # `reap`.
  d="$1"
  lockdir="$d/.turn-lock"
  [ -d "$lockdir" ] || return 1

  # Grace window: between mkdir (in acquire_turn_lock, called from
  # cmd_start/cmd_prompt) and submit_codex_turn overwriting owner.pid with
  # the supervisor's own pid (bounded by wait_for_file's 3s cap),
  # owner.pid still holds the ACQUIRING SHELL's pid — and that shell
  # legitimately exits once cmd_prompt/cmd_start returns (submit-then-
  # poll design) even though the turn itself is still running. A reaper
  # racing this window must not treat that as staleness.
  age=$(( $(now_epoch) - $(stat_mtime "$lockdir") ))
  [ "$age" -lt 30 ] && return 1

  # owner.pid — previously written but never read by any reaper; made
  # load-bearing here. Past the grace window, submit_codex_turn has
  # overwritten it with the supervisor's own pid, so its liveness IS the
  # turn's liveness — independent of meta.json.turn_count, which is
  # bumped only AFTER submission returns and is therefore the wrong thing
  # to race against (checking the PREVIOUS turn's already-dead pid during
  # that bump window is exactly how a live lock got reaped before this
  # fix).
  opid=$(cat "$lockdir/owner.pid" 2>/dev/null)
  if [ -n "$opid" ] && kill -0 "$opid" 2>/dev/null; then
    return 1
  fi
  return 0
}

steal_break_lock() {
  d="$1"
  lockdir="$d/.turn-lock"
  # Rename-then-remove (see acquire_turn_lock) so a concurrent reaper
  # racing the same handle can never rm -rf a path a third party just
  # recreated underneath it.
  mv "$lockdir" "$lockdir.stale.$$" 2>/dev/null && rm -rf "$lockdir.stale.$$"
}

# ---------------------------------------------------------------------------
# Portable daemonizer (§9.1) — perl POSIX::setsid double-fork; the child
# writes its OWN pid to the pidfile after setsid, then execs the real
# command. Works on macOS/Linux without setsid(1), which is absent here.
# ---------------------------------------------------------------------------

spawn_daemon() {
  # spawn_daemon <pidfile> <shell-command-string> <bootstrap-log-or-empty>
  pidfile="$1"; cmdstring="$2"; bootlog="$3"
  nohup perl -e '
    use POSIX qw(setsid);
    my ($pidfile, $cmdstring, $bootlog) = @ARGV;
    open(STDIN, "<", "/dev/null");
    if (defined $bootlog && length $bootlog) {
      open(STDOUT, ">>", $bootlog) or open(STDOUT, ">", "/dev/null");
      open(STDERR, ">>", $bootlog) or open(STDERR, ">", "/dev/null");
    } else {
      open(STDOUT, ">", "/dev/null");
      open(STDERR, ">", "/dev/null");
    }
    my $pid = fork();
    if (!defined $pid) { exit 1; }
    if ($pid) { exit 0; }             # parent leg: exits immediately
    POSIX::setsid();                  # child leg: new session, detached
    open(my $pf, ">", $pidfile) or exit 1;
    print $pf $$;                     # child writes its OWN pid — correct
    close $pf;                        # on macOS unlike the naive
                                       # nohup setsid ...; echo $! recipe.
    exec("/bin/sh", "-c", $cmdstring) or exit 127;
  ' "$pidfile" "$cmdstring" "$bootlog" >/dev/null 2>&1 &
  disown $! 2>/dev/null || :
}

# ---------------------------------------------------------------------------
# codex-specific helpers
# ---------------------------------------------------------------------------

preflight_codex() {
  if ! command -v codex >/dev/null 2>&1; then
    printf 'codex not found on PATH — install: npm i -g @openai/codex (or brew install codex)'
    return 1
  fi
  if ! codex login status >/dev/null 2>&1; then
    printf "codex not authenticated — run 'codex login' in a terminal"
    return 1
  fi
  return 0
}

codex_sandbox_args() {
  CODEX_SANDBOX_ARGS=()
  case "$1" in
    read-only) CODEX_SANDBOX_ARGS=(-s read-only) ;;
    workspace) CODEX_SANDBOX_ARGS=(-s workspace-write) ;;
    dangerous) CODEX_SANDBOX_ARGS=(--dangerously-bypass-approvals-and-sandbox) ;;
    *) return 1 ;;
  esac
  return 0
}

capture_session_id() {
  # Structural, typed capture — NOT a text grep over the whole transcript.
  # `--json` events are the delegated (untrusted) external model's own
  # output stream; a naive `grep -oE '[0-9a-fA-F-]{36}'` over the whole
  # file can match a uuid-shaped string the MODEL printed in its answer
  # (e.g. a `"conversation_id":"..."` it echoes back), or 36 hyphens,
  # letting a poisoned model answer redirect every future resume to an
  # attacker-chosen id. Restrict to a real UUID shape, and — per the
  # design's "belt and braces, in order" — only the FIRST event line,
  # parsed as JSON rather than string-matched, and only from typed
  # session-establishing events.
  dir="$1"; tn="$2"
  events="$dir/$tn.events.jsonl"
  sid=""
  if [ -f "$events" ]; then
    first_line=$(head -1 "$events" 2>/dev/null)
    if [ -n "$first_line" ]; then
      sid=$(printf '%s\n' "$first_line" | jq -r '
        select(type=="object")
        | select(.type=="session_meta" or has("session_id") or has("thread_id") or has("conversation_id"))
        | (.session_id // .thread_id // .conversation_id // (.payload.id? // empty))
        | select(type=="string")
        | select(test("^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$";"i"))
      ' 2>/dev/null)
    fi
  fi
  if [ -z "$sid" ]; then
    # Date-agnostic fallback (§9.3): codex session dirs are LOCAL-date, so
    # scan by mtime-newer-than-prompt rather than assuming a UTC/local path.
    cwd=$(meta_get "$dir" cwd)
    promptfile="$dir/$tn.prompt.txt"
    candidate=""
    if [ -d "$HOME/.codex/sessions" ] && [ -f "$promptfile" ]; then
      prompt_text_for_match=$(cat "$promptfile" 2>/dev/null)
      candidate=$(
        find "$HOME/.codex/sessions" -name 'rollout-*.jsonl' -newer "$promptfile" 2>/dev/null \
        | while IFS= read -r f; do
            c=$(head -1 "$f" 2>/dev/null | jq -r '.payload.cwd // empty' 2>/dev/null)
            [ "$c" = "$cwd" ] || continue
            # mtime-newer + cwd match alone can still pick a DIFFERENT
            # concurrent turn-1's rollout in the same cwd (mtime is
            # whole-second granularity, and two `start`s in the same
            # second race). Require this turn's own prompt text to
            # actually appear in the candidate rollout as the real guard
            # before accepting it.
            if [ -n "$prompt_text_for_match" ] && ! grep -qF -- "$prompt_text_for_match" "$f" 2>/dev/null; then
              continue
            fi
            printf '%s %s\n' "$(stat_mtime "$f")" "$f"
          done | sort -n | tail -1 | awk '{print $2}'
      )
    fi
    if [ -n "$candidate" ] && [ -f "$candidate" ]; then
      sid=$(head -1 "$candidate" | jq -r '
        select(type=="object")
        | (.payload.id? // empty)
        | select(type=="string")
        | select(test("^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$";"i"))
      ' 2>/dev/null)
    fi
  fi
  if [ -n "$sid" ]; then
    printf '%s' "$sid" > "$dir/session.id"
    meta_set "$dir" session_id str "$sid"
  fi
}

files_changed_summary() {
  events="$1"; posture="$2"
  if [ "$posture" = "read-only" ]; then
    printf 'not tracked (read-only posture)'
    return
  fi
  if [ ! -f "$events" ]; then
    printf 'none detected'
    return
  fi
  count=$(grep -oE '"type":"(patch_apply_(begin|end)|apply_patch)"' "$events" 2>/dev/null | wc -l | tr -d ' ')
  case "$count" in
    ''|0) printf 'none detected' ;;
    *) printf '%s patch event(s) detected (see full log)' "$count" ;;
  esac
}

errors_tail() {
  [ -f "$1" ] && tail -n 20 "$1" 2>/dev/null
}

spawn_boot_tail() {
  # Surface the spawn bootstrap log on a SPAWN_FAIL so the caller sees
  # *why* the supervisor never started, not just that it didn't.
  dir="$1"; turnnum="$2"
  tn=$(printf 'turn-%03d' "$turnnum")
  bootlog="$dir/$tn.spawn.log"
  if [ -s "$bootlog" ]; then
    printf ' spawn log (%s):\n%s' "$(display_path "$bootlog")" "$(tail -n 20 "$bootlog" 2>/dev/null)"
  fi
}

# Build a shell-quoted string of "$@" safe to hand to `/bin/sh -c`.
quote_args() {
  out=""
  for a in "$@"; do
    out="$out $(printf '%q' "$a")"
  done
  printf '%s' "$out"
}

submit_codex_turn() {
  # submit_codex_turn <dir> <turnnum> <cwd> <posture> <model> <effort> <timeout_s> [add_dir ...]
  #
  # Precondition: the caller already holds dir's turn lock, acquired
  # BEFORE the turn's prompt file was written (see cmd_start/cmd_prompt).
  # This function does not itself acquire the lock — only releases it on
  # a failure that happens before the supervisor takes over ownership.
  dir="$1"; turnnum="$2"; cwd="$3"; posture="$4"; model="$5"; effort="$6"; timeout_s="$7"
  shift 7
  add_dirs=("$@")

  tn=$(printf 'turn-%03d' "$turnnum")
  promptfile="$dir/$tn.prompt.txt"
  eventsfile="$dir/$tn.events.jsonl"
  lastmsgfile="$dir/$tn.last-message.txt"
  stderrfile="$dir/$tn.stderr.log"
  exitfile="$dir/$tn.exit.code"
  pidfile="$dir/$tn.pid"
  startedfile="$dir/$tn.started"
  bootlog="$dir/$tn.spawn.log"
  lockdir="$dir/.turn-lock"

  : > "$eventsfile"
  : > "$stderrfile"
  rm -f "$exitfile"

  if ! codex_sandbox_args "$posture"; then
    rm -rf "$lockdir"
    printf 'BAD_POSTURE'
    return 1
  fi

  cmd=(codex)
  if [ "$turnnum" -eq 1 ]; then
    cmd+=(exec --json -o "$lastmsgfile" -C "$cwd")
    for d in "${add_dirs[@]}"; do
      [ -n "$d" ] && cmd+=(--add-dir "$d")
    done
    cmd+=("${CODEX_SANDBOX_ARGS[@]}")
    [ -n "$model" ] && cmd+=(-m "$model")
    [ -n "$effort" ] && cmd+=(-c "model_reasoning_effort=\"$effort\"")
    cmd+=(--color never --skip-git-repo-check -)
  else
    sid=$(cat "$dir/session.id" 2>/dev/null)
    if [ -z "$sid" ]; then
      rm -rf "$lockdir"
      printf 'NO_SESSION'
      return 1
    fi
    # -C/--add-dir on resume: the §2.2 spike recipe omits them, but that
    # leaves a resumed turn's process cwd at PROJECT_ROOT instead of the
    # session's own cwd (already fetched into $cwd above and, until this
    # fix, silently dropped) — a real behavioral bug, not a style choice.
    # This could not be confirmed against `codex exec resume --help`
    # without invoking the real CLI (out of scope here), so per the
    # documented fallback we pass them; if a future verification shows
    # `resume` rejects -C, drop it here with that citation.
    cmd+=(exec resume "$sid" --json -o "$lastmsgfile" -C "$cwd")
    for d in "${add_dirs[@]}"; do
      [ -n "$d" ] && cmd+=(--add-dir "$d")
    done
    cmd+=("${CODEX_SANDBOX_ARGS[@]}")
    cmd+=(--color never --skip-git-repo-check -)
  fi

  cmdstr=$(quote_args "${cmd[@]}")
  supcmd="perl $(printf '%q' "$SUPERVISOR_PL") $(printf '%q' "$timeout_s") $(printf '%q' "$promptfile") $(printf '%q' "$eventsfile") $(printf '%q' "$stderrfile") $(printf '%q' "$exitfile") $(printf '%q' "$lockdir") --$cmdstr"

  now_epoch > "$startedfile"
  spawn_daemon "$pidfile" "$supcmd" "$bootlog"
  wait_for_file "$pidfile" 3

  if [ ! -f "$pidfile" ] || [ ! -s "$pidfile" ]; then
    # Spawn failure: the supervisor never started (perl missing, exec
    # failed, etc). Without this check, `submit_codex_turn` would print
    # OK unconditionally and `status` would then see an empty pid and no
    # exit file forever — RUNNING with no process behind it. Release the
    # lock ourselves since no supervisor exists to do it.
    rm -rf "$lockdir"
    printf 'SPAWN_FAIL'
    return 1
  fi

  # NOTE: ownership of the lock's owner.pid marker is claimed by
  # turn-supervisor.pl ITSELF, synchronously, immediately after its own
  # fork — not handed off from here. Until then owner.pid still holds the
  # ACQUIRING SHELL's pid (this process, which is about to return);
  # after, it's the supervisor's own pid, which is what lets
  # lock_is_stale() and the supervisor's own end-of-turn ownership check
  # work without racing meta.json.turn_count. Doing the handoff from
  # THIS side (after wait_for_file returns) was tried and is a real race:
  # a fast-finishing turn's supervisor can reach its own release check
  # before this shell gets a chance to write, see the stale acquiring-
  # shell pid, conclude the lock isn't its to release, and leave it
  # stuck. Only the supervisor itself can close that race by construction.

  printf 'OK'
  return 0
}

# ---------------------------------------------------------------------------
# Compact-return block (§4.2) — emitted by start/prompt (RUNNING) and status
# (terminal or RUNNING). Callers set the EB_* globals then call emit_block.
# ---------------------------------------------------------------------------

emit_block() {
  printf '## External Delegation\n'
  printf -- '- CLI: %s            Mode: %s\n' "$EB_CLI" "$EB_MODE"
  printf -- '- Status: %s\n' "$EB_STATUS"
  printf -- '- Handle: %s\n' "$EB_HANDLE"
  printf -- '- Session id: %s\n' "$EB_SESSION"
  printf -- '- Turn: %s    Held process: no    Duration: %ss\n' "$EB_TURN" "$EB_DURATION"
  printf -- '- Answer file: %s\n' "${EB_ANSWERFILE:-none}"
  printf -- '- Full log:    %s\n' "${EB_LOGFILE:-none}"
  printf -- '- Files changed: %s\n' "${EB_FILESCHANGED:-not tracked}"
  printf -- '- runtime.repollable: %s\n' "$EB_REPOLLABLE"
  if [ -n "$EB_ERRORS" ]; then
    printf '\n## Errors\n%s\n' "$EB_ERRORS"
  fi
}

report_running() {
  dir="$1"; turn="$2"
  tn=$(printf 'turn-%03d' "$turn")
  started=$(cat "$dir/$tn.started" 2>/dev/null)
  case "$started" in ''|*[!0-9]*) started=$(now_epoch) ;; esac

  EB_HANDLE=$(basename "$dir")
  EB_CLI=$(meta_get "$dir" cli)
  EB_MODE=$(meta_get "$dir" mode)
  EB_STATUS="RUNNING"
  EB_TURN="$turn"
  EB_SESSION=$(meta_get "$dir" session_id)
  [ -z "$EB_SESSION" ] && EB_SESSION="pending"
  EB_DURATION=$(( $(now_epoch) - started ))
  EB_ANSWERFILE=$(display_path "$dir/$tn.last-message.txt")
  EB_LOGFILE=$(display_path "$dir/$tn.events.jsonl")
  EB_FILESCHANGED="pending"
  EB_REPOLLABLE="yes"
  EB_ERRORS=""
  emit_block
}

emit_error_for_missing_handle() {
  EB_HANDLE="$1"; EB_CLI="unknown"; EB_MODE="unknown"; EB_STATUS="ERROR"
  EB_TURN=0; EB_SESSION="pending"; EB_DURATION=0
  EB_ANSWERFILE="none"; EB_LOGFILE="none"; EB_FILESCHANGED="not tracked"
  EB_REPOLLABLE="no"
  EB_ERRORS="no such handle: $1 (looked in $(display_path "$BASE_DIR/$1"))"
  emit_block
}

emit_scope_error() {
  handle="$1"; cli="$2"; mode="$3"
  EB_HANDLE="$handle"; EB_CLI="$cli"; EB_MODE="$mode"; EB_STATUS="ERROR"
  EB_TURN=$(meta_get "$BASE_DIR/$handle" turn_count)
  [ -z "$EB_TURN" ] && EB_TURN=0
  EB_SESSION="pending"; EB_DURATION=0
  EB_ANSWERFILE="none"; EB_LOGFILE="none"; EB_FILESCHANGED="not tracked"
  EB_REPOLLABLE="no"
  EB_ERRORS="cli='$cli' mode='$mode' is not implemented in this build (Stage 2 ships codex resume mode only)."
  emit_block
}

# ---------------------------------------------------------------------------
# start
# ---------------------------------------------------------------------------

cmd_start() {
  cli="codex"
  mode="resume"
  prompt_file=""
  prompt_text=""
  cwd="$PROJECT_ROOT"
  model=""
  effort=""
  posture="read-only"
  timeout_s=600
  add_dirs=()

  while [ $# -gt 0 ]; do
    case "$1" in
      --cli) cli="$2"; shift 2 ;;
      --mode) mode="$2"; shift 2 ;;
      --prompt-file) prompt_file="$2"; shift 2 ;;
      --prompt) prompt_text="$2"; shift 2 ;;
      --cwd) cwd="$2"; shift 2 ;;
      --model) model="$2"; shift 2 ;;
      --effort)
        case "$2" in
          low|medium|high) ;;
          *) die_usage "start: --effort must be low|medium|high" ;;
        esac
        effort="$2"; shift 2 ;;
      --posture) posture="$2"; shift 2 ;;
      --timeout-s)
        validate_nonneg_int "$2" || die_usage "start: --timeout-s must be a non-negative integer"
        timeout_s="$2"; shift 2 ;;
      --add-dir) add_dirs+=("$2"); shift 2 ;;
      *) die_usage "start: unknown argument: $1" ;;
    esac
  done

  if [ "$cli" != "codex" ] || [ "$mode" != "resume" ]; then
    EB_HANDLE="(none)"; EB_CLI="$cli"; EB_MODE="$mode"; EB_STATUS="ERROR"
    EB_TURN=0; EB_SESSION="pending"; EB_DURATION=0
    EB_ANSWERFILE="none"; EB_LOGFILE="none"; EB_FILESCHANGED="not tracked"
    EB_REPOLLABLE="no"
    EB_ERRORS="cli='$cli' mode='$mode' is not implemented in this build (Stage 2 ships codex resume mode only)."
    emit_block
    return 0
  fi
  if [ -z "$prompt_file" ] && [ -z "$prompt_text" ]; then
    die_usage "start: --prompt-file or --prompt is required"
  fi
  case "$posture" in
    read-only|workspace|dangerous) ;;
    *) die_usage "start: --posture must be read-only|workspace|dangerous" ;;
  esac

  reap_stale_locks_quiet

  pre_err=$(preflight_codex)
  if [ $? -ne 0 ]; then
    EB_HANDLE="(none)"; EB_CLI="$cli"; EB_MODE="$mode"; EB_STATUS="ERROR"
    EB_TURN=0; EB_SESSION="pending"; EB_DURATION=0
    EB_ANSWERFILE="none"; EB_LOGFILE="none"; EB_FILESCHANGED="not tracked"
    EB_REPOLLABLE="no"
    EB_ERRORS="$pre_err"
    emit_block
    return 0
  fi

  handle="${cli}-${mode}-$(now_ts_label)-$(rand6)"
  dir="$BASE_DIR/$handle"
  mkdir -p "$dir" || die_usage "start: could not create $dir"

  codex_version=$(codex --version 2>/dev/null | head -1)
  created=$(now_iso)
  add_dirs_json=$(printf '%s\n' "${add_dirs[@]}" | jq -R . | jq -s .)

  # No `owner` field: a per-handle exclusive-adoption model (§9.8) was
  # never implemented for resume mode in this build (nothing reads it —
  # a dead field is technical debt), and cross-process adoption is out of
  # scope for Stage 1+2's single-caller resume flow.
  jq -n \
    --arg handle "$handle" --arg cli "$cli" --arg mode "$mode" \
    --arg cwd "$cwd" --arg state_root "$PROJECT_ROOT" \
    --arg model "$model" --arg effort "$effort" --arg posture "$posture" \
    --argjson timeout_s "$timeout_s" --arg created "$created" \
    --arg codex_version "$codex_version" --argjson add_dirs "$add_dirs_json" \
    '{
      handle: $handle, cli: $cli, mode: $mode, cwd: $cwd, state_root: $state_root,
      model: (if ($model | length) > 0 then $model else null end),
      effort: (if ($effort | length) > 0 then $effort else null end),
      posture: $posture, timeout_s: $timeout_s, created: $created,
      codex_version: (if ($codex_version | length) > 0 then $codex_version else null end),
      add_dirs: $add_dirs, turn_count: 0, session_id: null, closed: null
    }' > "$dir/meta.json"

  # Lock BEFORE the prompt file write (M3): start's handle is fresh so
  # this specific acquire cannot itself contend, but writing the prompt
  # file only after taking the lock keeps start and prompt symmetric and
  # means the lock is always held for the full lifetime of "prompt file
  # exists but its turn hasn't been submitted yet".
  if ! acquire_turn_lock "$dir"; then
    EB_HANDLE="$handle"; EB_CLI="$cli"; EB_MODE="$mode"; EB_STATUS="ERROR"
    EB_TURN=0; EB_SESSION="pending"; EB_DURATION=0
    EB_ANSWERFILE="none"; EB_LOGFILE="none"; EB_FILESCHANGED="not tracked"
    EB_REPOLLABLE="no"
    EB_ERRORS="could not acquire turn lock for a freshly created handle (unexpected)"
    emit_block
    return 0
  fi

  if [ -n "$prompt_file" ]; then
    cp -- "$prompt_file" "$dir/turn-001.prompt.txt" || { rm -rf "$dir/.turn-lock"; die_usage "start: could not read prompt file $prompt_file"; }
  else
    printf '%s' "$prompt_text" > "$dir/turn-001.prompt.txt"
  fi

  result=$(submit_codex_turn "$dir" 1 "$cwd" "$posture" "$model" "$effort" "$timeout_s" "${add_dirs[@]}")
  case "$result" in
    OK)
      meta_set "$dir" turn_count raw 1
      report_running "$dir" 1
      ;;
    SPAWN_FAIL)
      EB_HANDLE="$handle"; EB_CLI="$cli"; EB_MODE="$mode"; EB_STATUS="ERROR"
      EB_TURN=0; EB_SESSION="pending"; EB_DURATION=0
      EB_ANSWERFILE="none"; EB_LOGFILE="none"; EB_FILESCHANGED="not tracked"
      EB_REPOLLABLE="no"
      EB_ERRORS="could not submit turn 1: spawn failed (supervisor did not start).$(spawn_boot_tail "$dir" 1)"
      emit_block
      ;;
    *)
      EB_HANDLE="$handle"; EB_CLI="$cli"; EB_MODE="$mode"; EB_STATUS="ERROR"
      EB_TURN=0; EB_SESSION="pending"; EB_DURATION=0
      EB_ANSWERFILE="none"; EB_LOGFILE="none"; EB_FILESCHANGED="not tracked"
      EB_REPOLLABLE="no"
      EB_ERRORS="could not submit turn 1: $result"
      emit_block
      ;;
  esac
}

# ---------------------------------------------------------------------------
# prompt
# ---------------------------------------------------------------------------

cmd_prompt() {
  handle="$1"
  [ -z "$handle" ] && die_usage "prompt: HANDLE is required"
  shift
  if ! validate_handle "$handle"; then
    emit_error_for_missing_handle "$handle"
    return 0
  fi
  dir="$BASE_DIR/$handle"
  if [ ! -d "$dir" ]; then
    emit_error_for_missing_handle "$handle"
    return 0
  fi

  prompt_file=""
  prompt_text=""
  posture=""
  steal=0
  timeout_s=""

  while [ $# -gt 0 ]; do
    case "$1" in
      --prompt-file) prompt_file="$2"; shift 2 ;;
      --prompt) prompt_text="$2"; shift 2 ;;
      --posture) posture="$2"; shift 2 ;;
      --steal) steal=1; shift ;;
      --timeout-s)
        validate_nonneg_int "$2" || die_usage "prompt: --timeout-s must be a non-negative integer"
        timeout_s="$2"; shift 2 ;;
      *) die_usage "prompt: unknown argument: $1" ;;
    esac
  done
  if [ -z "$prompt_file" ] && [ -z "$prompt_text" ]; then
    die_usage "prompt: --prompt-file or --prompt is required"
  fi

  cli=$(meta_get "$dir" cli)
  mode=$(meta_get "$dir" mode)
  if [ "$cli" != "codex" ] || [ "$mode" != "resume" ]; then
    emit_scope_error "$handle" "$cli" "$mode"
    return 0
  fi

  pinned_posture=$(meta_get "$dir" posture)
  cur_timeout=$(meta_get "$dir" timeout_s)
  [ -n "$timeout_s" ] || timeout_s="$cur_timeout"
  if [ "$timeout_s" != "$cur_timeout" ]; then
    # Persist the EFFECTIVE per-turn timeout into meta (rather than
    # leaving meta.timeout_s at the handle's original creation-time
    # default) so acquire_turn_lock's staleness math matches reality: a
    # deliberately longer turn (--timeout-s greater than the handle
    # default) must not be stale-broken by a racing acquirer mid-turn,
    # and a shorter one must not stay lockable long after it's actually
    # dead.
    meta_set "$dir" timeout_s raw "$timeout_s"
  fi

  stealing=0
  effective_posture="$pinned_posture"
  if [ -n "$posture" ] && [ "$posture" != "$pinned_posture" ]; then
    if [ "$steal" -ne 1 ]; then
      turn=$(meta_get "$dir" turn_count)
      EB_HANDLE="$handle"; EB_CLI="$cli"; EB_MODE="$mode"; EB_STATUS="ERROR"
      EB_TURN="$turn"; EB_SESSION=$(meta_get "$dir" session_id)
      [ -z "$EB_SESSION" ] && EB_SESSION="pending"
      EB_DURATION=0; EB_ANSWERFILE="none"; EB_LOGFILE="none"; EB_FILESCHANGED="not tracked"
      EB_REPOLLABLE="no"
      EB_ERRORS="posture '$posture' differs from this handle's pinned posture '$pinned_posture'. Escalation requires a new handle, or pass --steal to override explicitly (read-only != read-nothing — the delegated model can still READ anything the caller could, even under read-only)."
      emit_block
      return 0
    fi
    # --steal (M7): do NOT escalate meta.posture here. Escalating before
    # the turn is even submitted means a caller who then gets LOCKED/
    # NO_SESSION/SPAWN_FAIL back believes nothing changed while the pin
    # is already escalated — every future *plain* prompt (no --steal)
    # then silently runs at the escalated posture with no audit trail.
    # The pin (and stolen_from/stolen_at) is written only after submit
    # returns OK, below.
    effective_posture="$posture"
    stealing=1
  fi

  sid=$(cat "$dir/session.id" 2>/dev/null)
  if [ -z "$sid" ]; then
    turn=$(meta_get "$dir" turn_count)
    EB_HANDLE="$handle"; EB_CLI="$cli"; EB_MODE="$mode"; EB_STATUS="ERROR"
    EB_TURN="$turn"; EB_SESSION="pending"; EB_DURATION=0
    EB_ANSWERFILE="none"; EB_LOGFILE="none"; EB_FILESCHANGED="not tracked"
    EB_REPOLLABLE="no"
    EB_ERRORS="no session id captured yet — turn 1 has not completed. Call 'status $handle' first."
    emit_block
    return 0
  fi

  next_turn=$(( $(meta_get "$dir" turn_count) + 1 ))
  tn=$(printf 'turn-%03d' "$next_turn")

  # Lock BEFORE the prompt file write (M3): two concurrent `prompt` calls
  # can both compute the same next_turn and both reach this point; without
  # the lock held first, both would write turn-00N.prompt.txt and the
  # loser's write would silently overwrite the winner's, with the
  # winner's detached supervisor then executing the wrong prompt.
  if ! acquire_turn_lock "$dir"; then
    EB_HANDLE="$handle"; EB_CLI="$cli"; EB_MODE="$mode"; EB_STATUS="ERROR"
    EB_TURN=$((next_turn - 1)); EB_SESSION="$sid"; EB_DURATION=0
    EB_ANSWERFILE="none"; EB_LOGFILE="none"; EB_FILESCHANGED="not tracked"
    EB_REPOLLABLE="no"
    EB_ERRORS="a turn is already in progress for this handle; call 'status $handle' and retry once it completes."
    emit_block
    return 0
  fi

  if [ -n "$prompt_file" ]; then
    cp -- "$prompt_file" "$dir/$tn.prompt.txt" || { rm -rf "$dir/.turn-lock"; die_usage "prompt: could not read prompt file $prompt_file"; }
  else
    printf '%s' "$prompt_text" > "$dir/$tn.prompt.txt"
  fi

  cwd=$(meta_get "$dir" cwd)
  add_dirs=()
  while IFS= read -r ad; do
    [ -n "$ad" ] && add_dirs+=("$ad")
  done < <(meta_get_array "$dir" add_dirs)

  result=$(submit_codex_turn "$dir" "$next_turn" "$cwd" "$effective_posture" "" "" "$timeout_s" "${add_dirs[@]}")
  case "$result" in
    OK)
      meta_set "$dir" turn_count raw "$next_turn"
      if [ "$stealing" -eq 1 ]; then
        meta_set "$dir" posture str "$posture"
        meta_set "$dir" stolen_from str "$pinned_posture"
        meta_set "$dir" stolen_at str "$(now_iso)"
      fi
      report_running "$dir" "$next_turn"
      ;;
    SPAWN_FAIL)
      EB_HANDLE="$handle"; EB_CLI="$cli"; EB_MODE="$mode"; EB_STATUS="ERROR"
      EB_TURN=$((next_turn - 1)); EB_SESSION="$sid"; EB_DURATION=0
      EB_ANSWERFILE="none"; EB_LOGFILE="none"; EB_FILESCHANGED="not tracked"
      EB_REPOLLABLE="no"
      EB_ERRORS="could not submit turn $next_turn: spawn failed (supervisor did not start).$(spawn_boot_tail "$dir" "$next_turn")"
      emit_block
      ;;
    *)
      EB_HANDLE="$handle"; EB_CLI="$cli"; EB_MODE="$mode"; EB_STATUS="ERROR"
      EB_TURN=$((next_turn - 1)); EB_SESSION="$sid"; EB_DURATION=0
      EB_ANSWERFILE="none"; EB_LOGFILE="none"; EB_FILESCHANGED="not tracked"
      EB_REPOLLABLE="no"
      EB_ERRORS="could not submit turn $next_turn: $result"
      emit_block
      ;;
  esac
}

# ---------------------------------------------------------------------------
# status — bounded poll (default wait 5s, hard cap 90s per §9.2)
# ---------------------------------------------------------------------------

cmd_status() {
  handle="$1"
  [ -z "$handle" ] && die_usage "status: HANDLE is required"
  shift
  if ! validate_handle "$handle"; then
    emit_error_for_missing_handle "$handle"
    return 0
  fi
  dir="$BASE_DIR/$handle"
  if [ ! -d "$dir" ]; then
    emit_error_for_missing_handle "$handle"
    return 0
  fi

  wait_s=5
  while [ $# -gt 0 ]; do
    case "$1" in
      --wait-s) wait_s="$2"; shift 2 ;;
      *) die_usage "status: unknown argument: $1" ;;
    esac
  done
  case "$wait_s" in ''|*[!0-9]*) wait_s=5 ;; esac
  [ "$wait_s" -gt 90 ] && wait_s=90

  cli=$(meta_get "$dir" cli)
  mode=$(meta_get "$dir" mode)
  turn=$(meta_get "$dir" turn_count)
  case "$turn" in ''|*[!0-9]*) turn=0 ;; esac

  if [ "$turn" -eq 0 ]; then
    EB_HANDLE="$handle"; EB_CLI="$cli"; EB_MODE="$mode"; EB_STATUS="ERROR"
    EB_TURN=0; EB_SESSION="pending"; EB_DURATION=0
    EB_ANSWERFILE="none"; EB_LOGFILE="none"; EB_FILESCHANGED="not tracked"
    EB_REPOLLABLE="no"
    EB_ERRORS="handle has no submitted turns"
    emit_block
    return 0
  fi

  tn=$(printf 'turn-%03d' "$turn")
  exitfile="$dir/$tn.exit.code"
  pidfile="$dir/$tn.pid"
  startedfile="$dir/$tn.started"

  vanished=0
  deadline=$(( $(now_epoch) + wait_s ))
  while :; do
    [ -f "$exitfile" ] && break
    pid=$(cat "$pidfile" 2>/dev/null)
    if [ -n "$pid" ]; then
      if ! kill -0 "$pid" 2>/dev/null; then
        sleep 1
        [ -f "$exitfile" ] && break
        vanished=1
        break
      fi
    else
      # No pid recorded yet. Normal for the first few seconds — bounded
      # by submit_codex_turn's own wait_for_file cap (3s) — but past that
      # the supervisor never started at all (a spawn race/failure that
      # slipped past submit_codex_turn's own SPAWN_FAIL check). Without
      # this, an empty pidfile + no exitfile polls RUNNING forever.
      started_chk=$(cat "$startedfile" 2>/dev/null)
      case "$started_chk" in ''|*[!0-9]*) started_chk=$(now_epoch) ;; esac
      if [ $(( $(now_epoch) - started_chk )) -gt 5 ]; then
        vanished=1
        break
      fi
    fi
    [ "$(now_epoch)" -ge "$deadline" ] && break
    sleep 2
  done

  started=$(cat "$startedfile" 2>/dev/null)
  case "$started" in ''|*[!0-9]*) started=$(now_epoch) ;; esac

  if [ -f "$exitfile" ]; then
    code=$(tr -d '[:space:]' < "$exitfile" 2>/dev/null)
    ended=$(stat_mtime "$exitfile")
    duration=$((ended - started))
    [ "$duration" -lt 0 ] && duration=0

    if [ "$turn" -eq 1 ] && [ -z "$(meta_get "$dir" session_id)" ]; then
      capture_session_id "$dir" "$tn"
    fi
    sid=$(meta_get "$dir" session_id)
    [ -z "$sid" ] && sid="pending"

    case "$code" in
      0) status="SUCCESS" ;;
      124) status="TIMEOUT" ;;
      *) status="FAILURE" ;;
    esac

    posture=$(meta_get "$dir" posture)
    EB_HANDLE="$handle"; EB_CLI="$cli"; EB_MODE="$mode"; EB_STATUS="$status"
    EB_TURN="$turn"; EB_SESSION="$sid"; EB_DURATION="$duration"
    EB_ANSWERFILE=$(display_path "$dir/$tn.last-message.txt")
    EB_LOGFILE=$(display_path "$dir/$tn.events.jsonl")
    EB_FILESCHANGED=$(files_changed_summary "$dir/$tn.events.jsonl" "$posture")
    EB_REPOLLABLE="no"
    if [ "$status" != "SUCCESS" ]; then
      EB_ERRORS=$(errors_tail "$dir/$tn.stderr.log")
    else
      EB_ERRORS=""
    fi
    emit_block
  elif [ "$vanished" -eq 1 ]; then
    sid=$(meta_get "$dir" session_id)
    [ -z "$sid" ] && sid="pending"
    EB_HANDLE="$handle"; EB_CLI="$cli"; EB_MODE="$mode"; EB_STATUS="ERROR"
    EB_TURN="$turn"; EB_SESSION="$sid"
    EB_DURATION=$(( $(now_epoch) - started ))
    EB_ANSWERFILE="none"
    EB_LOGFILE=$(display_path "$dir/$tn.events.jsonl")
    EB_FILESCHANGED="not tracked"
    EB_REPOLLABLE="no"
    EB_ERRORS="the turn process vanished without completing (harness-dependent: a future sandboxed-Bash process-group kill on tool-call exit could end a detached process early). See $(display_path "$dir/$tn.stderr.log") and $(display_path "$dir/$tn.spawn.log")."
    emit_block
  else
    report_running "$dir" "$turn"
  fi
}

# ---------------------------------------------------------------------------
# slice — capped answer text only (§9.10), so the caller handles less raw
# external output than it would by reading turn-NNN.last-message.txt itself.
# ---------------------------------------------------------------------------

cmd_slice() {
  handle="$1"
  [ -z "$handle" ] && die_usage "slice: HANDLE is required"
  shift
  if ! validate_handle "$handle"; then
    echo "ERROR: invalid handle: $handle" >&2
    return 0
  fi
  dir="$BASE_DIR/$handle"
  if [ ! -d "$dir" ]; then
    echo "ERROR: no such handle: $handle" >&2
    return 0
  fi

  max_chars="$MAX_SLICE_CHARS"
  turn=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --max-chars)
        validate_nonneg_int "$2" || die_usage "slice: --max-chars must be a non-negative integer"
        max_chars="$2"; shift 2 ;;
      --turn) turn="$2"; shift 2 ;;
      *) die_usage "slice: unknown argument: $1" ;;
    esac
  done
  [ -z "$turn" ] && turn=$(meta_get "$dir" turn_count)
  case "$turn" in ''|*[!0-9]*) turn=0 ;; esac
  if [ "$turn" -eq 0 ]; then
    echo "ERROR: handle has no submitted turns" >&2
    return 0
  fi

  tn=$(printf 'turn-%03d' "$turn")
  answerfile="$dir/$tn.last-message.txt"
  if [ ! -f "$answerfile" ]; then
    echo "ERROR: no answer file yet for turn $turn (still RUNNING? call status first): $(display_path "$answerfile")" >&2
    return 0
  fi

  content=$(cat "$answerfile")
  len=${#content}
  if [ "$len" -gt "$max_chars" ]; then
    printf '%s' "${content:0:$max_chars}"
    printf '\n…[truncated — full text in %s]\n' "$(display_path "$answerfile")"
  else
    printf '%s\n' "$content"
  fi
}

# ---------------------------------------------------------------------------
# stop — kills any in-flight turn process group, marks meta.json closed.
# Persistent-mode artefacts (daemon/holder/watchdog pid, in.fifo) are Stage
# 4 concerns but are cleaned defensively here if ever present.
# ---------------------------------------------------------------------------

cmd_stop() {
  handle="$1"
  [ -z "$handle" ] && die_usage "stop: HANDLE is required"
  if ! validate_handle "$handle"; then
    echo "ERROR: invalid handle: $handle" >&2
    return 0
  fi
  dir="$BASE_DIR/$handle"
  if [ ! -d "$dir" ]; then
    echo "ERROR: no such handle: $handle" >&2
    return 0
  fi

  turn=$(meta_get "$dir" turn_count)
  case "$turn" in ''|*[!0-9]*) turn=0 ;; esac
  if [ "$turn" -gt 0 ]; then
    tn=$(printf 'turn-%03d' "$turn")
    pidfile="$dir/$tn.pid"
    exitfile="$dir/$tn.exit.code"
    if [ ! -f "$exitfile" ] && [ -f "$pidfile" ]; then
      pid=$(cat "$pidfile" 2>/dev/null)
      if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        kill -TERM "-$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null
        n=0
        while [ "$n" -lt 5 ] && kill -0 "$pid" 2>/dev/null; do
          sleep 1
          n=$((n + 1))
        done
        if kill -0 "$pid" 2>/dev/null; then
          kill -KILL "-$pid" 2>/dev/null || kill -KILL "$pid" 2>/dev/null
        fi
      fi
    fi
  fi

  for pf in daemon.pid watchdog.pid holder.pid; do
    if [ -f "$dir/$pf" ]; then
      p=$(cat "$dir/$pf" 2>/dev/null)
      [ -n "$p" ] && kill "$p" 2>/dev/null
      rm -f "$dir/$pf"
    fi
  done
  [ -e "$dir/in.fifo" ] && rm -f "$dir/in.fifo"

  rm -rf "$dir/.turn-lock"
  meta_set "$dir" closed str "$(now_iso)"
  echo "STOPPED: $handle"
}

# ---------------------------------------------------------------------------
# reap — sweep-on-entry (§5.3 layer 3): clears stale turn-locks whose owning
# process is dead; optionally prunes closed handles older than an age.
# ---------------------------------------------------------------------------

reap_stale_locks_quiet() {
  [ -d "$BASE_DIR" ] || return 0
  for d in "$BASE_DIR"/*/; do
    [ -d "$d" ] || continue
    d="${d%/}"
    [ -d "$d/.turn-lock" ] || continue
    lock_is_stale "$d" && steal_break_lock "$d"
  done
}

cmd_reap() {
  prune_age=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --prune-closed)
        validate_nonneg_int "$2" || die_usage "reap: --prune-closed must be a non-negative integer"
        prune_age="$2"; shift 2 ;;
      *) die_usage "reap: unknown argument: $1" ;;
    esac
  done

  if [ ! -d "$BASE_DIR" ]; then
    echo "nothing to reap ($(display_path "$BASE_DIR") does not exist)"
    return 0
  fi

  reaped=0
  for d in "$BASE_DIR"/*/; do
    [ -d "$d" ] || continue
    d="${d%/}"
    if [ -d "$d/.turn-lock" ] && lock_is_stale "$d"; then
      steal_break_lock "$d"
      reaped=$((reaped + 1))
      echo "reaped stale lock: $(basename "$d")"
    fi

    if [ -n "$prune_age" ]; then
      closed=$(meta_get "$d" closed)
      if [ -n "$closed" ]; then
        cepoch=$(iso_to_epoch "$closed")
        if [ -n "$cepoch" ]; then
          age=$(( $(now_epoch) - cepoch ))
          if [ "$age" -gt "$prune_age" ]; then
            rm -rf "$d"
            echo "pruned closed handle: $(basename "$d") (age ${age}s)"
          fi
        fi
      fi
    fi
  done
  echo "reap complete (${reaped} stale lock(s) cleared)"
}

# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

subcommand="${1:-}"
[ -n "$subcommand" ] || die_usage "missing subcommand"
shift

mkdir -p "$BASE_DIR" 2>/dev/null

case "$subcommand" in
  start) cmd_start "$@" ;;
  prompt) cmd_prompt "$@" ;;
  status) cmd_status "$@" ;;
  slice) cmd_slice "$@" ;;
  stop) cmd_stop "$@" ;;
  reap) cmd_reap "$@" ;;
  -h|--help|help) usage ;;
  *) die_usage "unknown subcommand: $subcommand" ;;
esac
