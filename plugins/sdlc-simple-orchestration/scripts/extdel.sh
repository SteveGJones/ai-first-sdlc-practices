#!/usr/bin/env bash
# extdel.sh — external-agent delegation primitives (codex / agy)
#
# Stage 1 + Stage 2 + Stage 3 of
# docs/superpowers/specs/2026-07-23-external-agent-delegation-design.md
# (that spec's §9 is authoritative, and §9.14 — agy live-probe findings —
# supersedes §2.3/§9.6 for agy id-capture specifically). This build
# implements:
#   cli=codex, mode=resume  — submit-then-poll id-based resume.
#   cli=agy,   mode=resume  — submit-then-poll id-based resume (Stage 3).
# codex persistent (daemon) mode and agy persistent mode are later/out-of-
# scope stages and are refused with a clear ERROR status rather than
# attempted (agy persistent mode is deliberately NOT implemented as
# resume-under-the-hood here — see cmd_start's scope check — to avoid
# silently masking a caller's explicit `mode: persistent` request; ships
# as a clean ERROR per the task's own preference for Stage 3).
#
# Target shell: bash 3.2.57 (macOS system bash) / POSIX sh. No associative
# arrays, no `${var,,}`, no reliance on `setsid`/`timeout`/`gtimeout` (all
# three are absent on the target machine). Indexed bash arrays ARE used
# (supported since bash 3.1) for building argv safely.
#
# Subcommands: start | prompt | status | slice | stop | reap
#
# All state lives under ./tmp/simple-orchestration/<HANDLE>/ relative to the
# directory extdel.sh is invoked from (the project root) — never /tmp.

# Deliberately no `set -e`: this script does many conditional command
# substitutions (grep/jq lookups that legitimately return empty) and a
# single early failure must not abort a multi-step status/reap sweep.

SCRIPT_SOURCE="$0"
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_SOURCE")" && pwd -P)"
PROJECT_ROOT="$(pwd -P)"
BASE_DIR="$PROJECT_ROOT/tmp/simple-orchestration"
SUPERVISOR_PL="$SCRIPT_DIR/turn-supervisor.pl"
MAX_SLICE_CHARS=12000

# EXTDEL_ADAPTER_PATH (§4): colon-separated list of extra adapter
# directories searched BEFORE ${SCRIPT_DIR}/adapters/* (first `id` match
# wins) — see adapter_search_dirs. Third-party/local-override adapters
# need zero core changes to be picked up this way.
: "${EXTDEL_ADAPTER_PATH:=}"

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
  start   --prompt-file F | --prompt TEXT [--cli codex|agy] [--mode resume]
          [--cwd DIR] [--model M] [--effort low|medium|high]
          [--agent NAME]   (agy only; ignored for codex)
          [--posture read-only|workspace|dangerous] [--timeout-s N]
          [--add-dir DIR ...]
  prompt  <HANDLE> --prompt-file F | --prompt TEXT [--posture P] [--steal]
          [--timeout-s N]
  status  <HANDLE> [--wait-s N]
  slice   <HANDLE> [--max-chars N] [--turn N]
  stop    <HANDLE>
  reap    [--prune-closed AGE_SECONDS]
  list-backends [--json] [--probe-auth]

Stage 3 scope: cli=codex mode=resume, cli=agy mode=resume. codex persistent
and agy persistent mode are not implemented in this build (they return
Status: ERROR, not a hang).
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

is_blank_file() {
  # is_blank_file <path> — DF2: 0 (true) if the file is missing, empty, or
  # contains only whitespace; 1 (false) if it has any non-whitespace
  # content. Used by cmd_status to catch an exit-0-but-empty turn before
  # it gets reported as a false SUCCESS.
  f="$1"
  [ -f "$f" ] || return 0
  content=$(tr -d '[:space:]' < "$f" 2>/dev/null)
  [ -z "$content" ]
}

permission_denial_hint() {
  # permission_denial_hint <file> [<file> ...] — DF2: scan the given
  # stderr/CLI-log files for the CURRENTLY-SOURCED adapter's permission-
  # denial wording and print the first matching line verbatim (never
  # paraphrased — it's the external CLI's own diagnostic, and its own
  # "add an allow-rule" / "skip permissions" guidance is exactly what the
  # caller needs to act on). Prints nothing and returns 1 if no file
  # matches, OR if the adapter defines no pattern at all (§2.2:
  # adapter_permission_hint_pattern "may be empty" — an empty/undefined
  # pattern must never be treated as "match anything", which an empty
  # ERE would do in grep) — a genuinely empty-but-legitimate answer (no
  # permission problem at all) still gets caught upstream by
  # is_blank_file; this function only supplies the WHY when there is one.
  #
  # The ERE itself is adapter-owned (§2.2 ABI); this scanner stays
  # engine-owned. Both shipped adapters (codex, agy) echo the exact same
  # pattern this function used to hardcode, so behavior is unchanged for
  # either.
  pattern=""
  if [ "$(type -t adapter_permission_hint_pattern 2>/dev/null)" = "function" ]; then
    pattern=$(adapter_permission_hint_pattern)
  fi
  [ -n "$pattern" ] || return 1
  for f in "$@"; do
    [ -f "$f" ] || continue
    line=$(grep -Eim1 "$pattern" "$f" 2>/dev/null)
    if [ -n "$line" ]; then
      printf '%s' "$line"
      return 0
    fi
  done
  return 1
}

validate_handle() {
  # Reject anything that isn't the exact handle grammar (§5.1):
  # <cli>-<mode>-<UTCts>-<rand6>. Handles round-trip through the Haiku
  # wrapper agent's context, including text the delegated (external, and
  # therefore untrusted) model produced — a handle string is effectively
  # attacker-influenced input. Without this, "$BASE_DIR/$handle" lets a
  # handle like `../../..` escape the state dir entirely, and every
  # handle-taking subcommand (prompt/status/slice/stop) would then
  # rm/kill/write outside ./tmp/simple-orchestration.
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
# Generic per-turn helpers shared by ALL adapters (engine-owned — moved here
# unchanged from the old "codex-specific helpers" section they used to sit
# in; they were never actually codex-specific, see the migration's
# extraction-map notes).
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# Adapter registry & ABI (§2/§4 of the design) — resolves a `--cli <id>` /
# `meta.json.cli` value to an adapter directory, sources its adapter.sh into
# THIS shell (adapters are sourced, never exec'd, so their functions and the
# engine's are one namespace — that's what lets an adapter call meta_get,
# spawn_daemon, quote_args, $SUPERVISOR_PL etc. directly), and asserts the
# §2.2 function ABI is fully defined before any engine code calls into it.
#
# Engine-exported globals an adapter's ABI functions read (set by cmd_start/
# cmd_prompt/cmd_status immediately before each ABI call, per adapter — NOT
# passed positionally): $DIR $HANDLE $CLI $POSTURE $TURN $PROMPT_FILE
# $TIMEOUT_S $CWD $ADD_DIRS $MODEL $EFFORT, plus $AGENT (agy-only; not in
# the design's abbreviated list but required to preserve the existing
# `--agent NAME` flag behavior byte-for-byte).
# ---------------------------------------------------------------------------

adapter_search_dirs() {
  # adapter_search_dirs — print candidate adapter directories, one per
  # line, in priority order: $EXTDEL_ADAPTER_PATH entries first (colon-
  # separated, as given), then ${SCRIPT_DIR}/adapters/*. First `id` match
  # in this order wins (resolve_adapter); this same order is the dedupe
  # priority for discover_all_adapters (list-backends).
  if [ -n "${EXTDEL_ADAPTER_PATH:-}" ]; then
    old_ifs="$IFS"
    IFS=':'
    for p in $EXTDEL_ADAPTER_PATH; do
      [ -n "$p" ] && printf '%s\n' "$p"
    done
    IFS="$old_ifs"
  fi
  for p in "$SCRIPT_DIR"/adapters/*; do
    [ -d "$p" ] && printf '%s\n' "$p"
  done
}

resolve_adapter() {
  # resolve_adapter <id> — search adapter_search_dirs for the first
  # directory whose adapter.json validates (schema_version==1, id
  # present, kind=="direct-cli" — the only kind this engine build can
  # drive) and whose .id equals <id>. Sets ADAPTER_DIR/ADAPTER_JSON on
  # success (empty on failure); does not source anything itself.
  id="$1"
  ADAPTER_DIR=""; ADAPTER_JSON=""
  while IFS= read -r d; do
    [ -d "$d" ] || continue
    dj="$d/adapter.json"
    [ -f "$dj" ] || continue
    jq -e '.schema_version==1 and .id and .kind=="direct-cli"' "$dj" >/dev/null 2>&1 || continue
    did=$(jq -r '.id' "$dj" 2>/dev/null)
    if [ "$did" = "$id" ]; then
      ADAPTER_DIR="$d"; ADAPTER_JSON="$dj"
      return 0
    fi
  done < <(adapter_search_dirs)
  return 1
}

assert_adapter_abi() {
  # assert_adapter_abi — verify the currently-sourced adapter defines
  # every REQUIRED §2.2 ABI function (adapter_check_identity_drift is
  # optional and is checked for with `command -v` at each call site
  # instead). Prints a one-line reason and returns 1 if anything is
  # missing; silent + returns 0 on success.
  missing=""
  for fn in adapter_detect adapter_preflight adapter_posture_args \
            adapter_submit_turn adapter_capture_session_id \
            adapter_files_changed_summary adapter_permission_hint_pattern; do
    if [ "$(type -t "$fn" 2>/dev/null)" != "function" ]; then
      missing="$missing $fn"
    fi
  done
  if [ -n "$missing" ]; then
    printf 'adapter at %s is missing required ABI function(s):%s' "$ADAPTER_DIR" "$missing"
    return 1
  fi
  return 0
}

load_adapter() {
  # load_adapter <cli-id> — resolve_adapter + source + assert_adapter_abi.
  # MUST be called as a plain statement, never inside $(...) — sourcing
  # inside a command substitution only affects that subshell and the
  # adapter's functions would vanish the instant the substitution ends.
  # On failure sets $LOAD_ADAPTER_ERR and returns 1; on success
  # ADAPTER_DIR/ADAPTER_JSON are set and the adapter's functions are live
  # in this shell.
  cid="$1"
  LOAD_ADAPTER_ERR=""
  if ! resolve_adapter "$cid"; then
    LOAD_ADAPTER_ERR="no adapter registered for cli='$cid'"
    return 1
  fi
  # shellcheck disable=SC1090
  . "$ADAPTER_DIR/adapter.sh"
  abi_err=$(assert_adapter_abi)
  if [ $? -ne 0 ]; then
    LOAD_ADAPTER_ERR="$abi_err"
    return 1
  fi
  return 0
}

discover_all_adapters() {
  # discover_all_adapters — print "<id> <dir>" one per line for every
  # structurally-valid (schema_version==1, id present, kind present —
  # ANY kind, unlike resolve_adapter, so list-backends can still show an
  # adapter this engine build can't drive) descriptor, deduped by id in
  # adapter_search_dirs priority order (first found wins).
  seen=""
  while IFS= read -r d; do
    [ -d "$d" ] || continue
    dj="$d/adapter.json"
    [ -f "$dj" ] || continue
    jq -e '.schema_version==1 and (.id|type=="string") and (.kind|type=="string")' "$dj" >/dev/null 2>&1 || continue
    did=$(jq -r '.id' "$dj" 2>/dev/null)
    [ -n "$did" ] || continue
    case " $seen " in
      *" $did "*) continue ;;
    esac
    seen="$seen $did"
    printf '%s %s\n' "$did" "$d"
  done < <(adapter_search_dirs)
}

# ---------------------------------------------------------------------------
# Sibling-plugin detection (§3.2/§4) — advisory-only signal for
# list-backends about whether a related vendor-native plugin (e.g.
# codex-plugin-cc, antigravity-for-claude-code) is installed alongside us.
# Never gates the direct-CLI adapter path; a probe failure must never be
# reported as a confident "not installed" — see the "unknown" branches
# below.
# ---------------------------------------------------------------------------

detect_sibling_plugins() {
  # detect_sibling_plugins <plugin_match> — prints exactly one of:
  # installed | absent | unknown. <plugin_match> is a
  # "<plugin-name>@<marketplace>" key (or a prefix of one) as it appears
  # in installed_plugins.json's .plugins map.
  #
  # Primary source: $HOME/.claude/plugins/installed_plugins.json, guarded
  # by .version==2 (the only shape this reads). Overridable via $HOME so
  # tests can inject a fake manifest wholesale — never probe the real
  # ~/.claude from a test.
  #
  # Fallback (used when the manifest is absent, unparseable, or not
  # version 2): scan $HOME/.claude/plugins/cache/*/<plugin-name>/ for the
  # plugin's cache directory across any marketplace.
  #
  # If NEITHER source can produce a real answer (no manifest AND no cache
  # tree), the correct answer is "unknown", never "absent" — an absent
  # signal must come from a probe that actually completed, not from the
  # lack of one.
  match="$1"
  manifest="$HOME/.claude/plugins/installed_plugins.json"
  cache_root="$HOME/.claude/plugins/cache"

  if [ -f "$manifest" ] && jq -e '.version==2' "$manifest" >/dev/null 2>&1; then
    if jq -e --arg m "$match" '(.plugins // {}) | keys | any(startswith($m))' "$manifest" >/dev/null 2>&1; then
      printf 'installed'
    else
      printf 'absent'
    fi
    return 0
  fi

  plugin_name="${match%%@*}"
  if [ -d "$cache_root" ]; then
    found=0
    for d in "$cache_root"/*/"$plugin_name"; do
      if [ -d "$d" ]; then
        found=1
        break
      fi
    done
    if [ "$found" -eq 1 ]; then
      printf 'installed'
    else
      printf 'absent'
    fi
    return 0
  fi

  printf 'unknown'
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
  EB_ERRORS="cli='$cli' mode='$mode' is not implemented in this build (Stage 3 ships codex resume + agy resume only)."
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
  agent=""
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
      --agent) agent="$2"; shift 2 ;;
      --posture) posture="$2"; shift 2 ;;
      --timeout-s)
        validate_nonneg_int "$2" || die_usage "start: --timeout-s must be a non-negative integer"
        timeout_s="$2"; shift 2 ;;
      --add-dir) add_dirs+=("$2"); shift 2 ;;
      *) die_usage "start: unknown argument: $1" ;;
    esac
  done

  scope_ok=1
  if [ "$mode" != "resume" ]; then
    scope_ok=0
  elif ! load_adapter "$cli"; then
    scope_ok=0
  fi
  if [ "$scope_ok" -ne 1 ]; then
    EB_HANDLE="(none)"; EB_CLI="$cli"; EB_MODE="$mode"; EB_STATUS="ERROR"
    EB_TURN=0; EB_SESSION="pending"; EB_DURATION=0
    EB_ANSWERFILE="none"; EB_LOGFILE="none"; EB_FILESCHANGED="not tracked"
    EB_REPOLLABLE="no"
    EB_ERRORS="cli='$cli' mode='$mode' is not implemented in this build (Stage 3 ships codex resume + agy resume only; agy persistent mode is deliberately a clean ERROR here rather than resume-under-the-hood — see design §3.2 for the intended future behavior).${LOAD_ADAPTER_ERR:+ ($LOAD_ADAPTER_ERR)}"
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

  pre_err=$(adapter_preflight); pre_rc=$?
  if [ "$pre_rc" -ne 0 ]; then
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

  adapter_binary=$(jq -r '.binary // empty' "$ADAPTER_JSON" 2>/dev/null)
  cli_version=""
  if [ -n "$adapter_binary" ]; then
    cli_version=$("$adapter_binary" --version 2>/dev/null | head -1)
  fi
  adapter_dir_val="$ADAPTER_DIR"
  adapter_schema_version=$(jq -r '.schema_version // empty' "$ADAPTER_JSON" 2>/dev/null)
  created=$(now_iso)
  add_dirs_json=$(printf '%s\n' "${add_dirs[@]}" | jq -R . | jq -s .)

  # No `owner` field: a per-handle exclusive-adoption model (§9.8) was
  # never implemented for resume mode in this build (nothing reads it —
  # a dead field is technical debt), and cross-process adoption is out of
  # scope for Stage 1+2+3's single-caller resume flow. `agent` is agy-only
  # (codex has no equivalent flag) — always null for cli=codex.
  jq -n \
    --arg handle "$handle" --arg cli "$cli" --arg mode "$mode" \
    --arg cwd "$cwd" --arg state_root "$PROJECT_ROOT" \
    --arg model "$model" --arg effort "$effort" --arg agent "$agent" --arg posture "$posture" \
    --argjson timeout_s "$timeout_s" --arg created "$created" \
    --arg cli_version "$cli_version" --argjson add_dirs "$add_dirs_json" \
    --arg adapter_dir "$adapter_dir_val" --arg adapter_schema_version "$adapter_schema_version" \
    '{
      handle: $handle, cli: $cli, mode: $mode, cwd: $cwd, state_root: $state_root,
      model: (if ($model | length) > 0 then $model else null end),
      effort: (if ($effort | length) > 0 then $effort else null end),
      agent: (if ($agent | length) > 0 then $agent else null end),
      posture: $posture, timeout_s: $timeout_s, created: $created,
      cli_version: (if ($cli_version | length) > 0 then $cli_version else null end),
      adapter_dir: (if ($adapter_dir | length) > 0 then $adapter_dir else null end),
      adapter_schema_version: (if ($adapter_schema_version | length) > 0 then ($adapter_schema_version | tonumber) else null end),
      add_dirs: $add_dirs, turn_count: 0, session_id: null, agy_cwd_key: null, closed: null
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

  DIR="$dir"; HANDLE="$handle"; CLI="$cli"; POSTURE="$posture"; TURN=1
  PROMPT_FILE="$dir/turn-001.prompt.txt"; TIMEOUT_S="$timeout_s"; CWD="$cwd"
  ADD_DIRS=("${add_dirs[@]}"); MODEL="$model"; EFFORT="$effort"; AGENT="$agent"
  result=$(adapter_submit_turn)
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
  prompt_scope_ok=1
  if [ "$mode" != "resume" ]; then
    prompt_scope_ok=0
  elif ! load_adapter "$cli"; then
    prompt_scope_ok=0
  fi
  if [ "$prompt_scope_ok" -ne 1 ]; then
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

  # Turn N never re-passes model/effort/agent (session-time properties,
  # not per-turn ones) — see agy/adapter.sh's adapter_submit_turn header
  # note and the existing codex behavior this mirrors.
  DIR="$dir"; HANDLE="$handle"; CLI="$cli"; POSTURE="$effective_posture"; TURN="$next_turn"
  PROMPT_FILE="$dir/$tn.prompt.txt"; TIMEOUT_S="$timeout_s"; CWD="$cwd"
  ADD_DIRS=("${add_dirs[@]}"); MODEL=""; EFFORT=""; AGENT=""
  result=$(adapter_submit_turn)
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

  if ! load_adapter "$cli"; then
    EB_HANDLE="$handle"; EB_CLI="$cli"; EB_MODE="$mode"; EB_STATUS="ERROR"
    EB_TURN="$turn"; EB_SESSION="pending"; EB_DURATION=0
    EB_ANSWERFILE="none"; EB_LOGFILE="none"; EB_FILESCHANGED="not tracked"
    EB_REPOLLABLE="no"
    EB_ERRORS="$LOAD_ADAPTER_ERR"
    emit_block
    return 0
  fi

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
    posture=$(meta_get "$dir" posture)
    cwd_stored=$(meta_get "$dir" cwd)

    case "$code" in
      0) status="SUCCESS" ;;
      124) status="TIMEOUT" ;;
      *) status="FAILURE" ;;
    esac

    if [ "$cli" = "agy" ]; then
      # agy has no -o/--output-last-message equivalent (§9.14 #3): its
      # answer is plain stdout, which turn-supervisor.pl already captured
      # into eventsfile. Populate last-message.txt from it so slice/status
      # share the exact same file convention codex uses, rather than
      # forking the contract per CLI.
      cp -- "$dir/$tn.events.jsonl" "$dir/$tn.last-message.txt" 2>/dev/null

      # exit_success gates id capture below and is deliberately evaluated
      # from the ORIGINAL exit-0-derived status, before DF2's NO_OUTPUT
      # downgrade — a permission-denied turn still exits 0 and its
      # conversation still exists server-side (agy created/updated it
      # before the tool call inside was denied), so it's still worth
      # capturing as a resume target even though the answer is empty.
      exit_success=0
      [ "$status" = "SUCCESS" ] && exit_success=1

      identity_warning=""
      if [ "$turn" -eq 1 ] && [ -z "$(meta_get "$dir" session_id)" ]; then
        if [ "$exit_success" -eq 1 ]; then
          DIR="$dir"; CWD="$cwd_stored"; TURN="$turn"
          adapter_capture_session_id || status="ERROR"
        fi
      elif [ "$turn" -gt 1 ]; then
        DIR="$dir"
        if [ "$(type -t adapter_check_identity_drift 2>/dev/null)" = "function" ]; then
          identity_warning=$(adapter_check_identity_drift)
        fi
      fi

      # DF2: an exit-0 turn with an EMPTY captured answer is never
      # SUCCESS — most commonly agy's headless auto-deny (§9.15): the
      # conversation completed (exit 0) but the requested tool call was
      # denied, so nothing useful came back. Only fires off the ORIGINAL
      # exit-0 status (not if id capture above already escalated to
      # ERROR) and only once — a status of ERROR here means id capture
      # itself is the more specific, actionable problem to report.
      no_output_hint=""
      if [ "$status" = "SUCCESS" ] && is_blank_file "$dir/$tn.last-message.txt"; then
        status="NO_OUTPUT"
        hint=$(permission_denial_hint "$dir/$tn.stderr.log" "$dir/$tn.agy.log")
        if [ -n "$hint" ]; then
          no_output_hint="agy produced no output — the delegated turn's permission was auto-denied under headless mode: $hint
Add the needed rule to this handle's --gemini_dir allow-list (posture=workspace already grants write_file/edit_file + a build/test command set), or — only with explicit caller approval — resend at posture=dangerous (--dangerously-skip-permissions)."
        fi
      fi

      sid=$(meta_get "$dir" session_id)
      [ -z "$sid" ] && sid="pending"
      POSTURE="$posture"
      files_changed=$(adapter_files_changed_summary)

      status_errors=""
      case "$status" in
        FAILURE)
          if adapter_auth_backstop_matched "$dir/$tn.stderr.log" "$dir/$tn.agy.log"; then
            status="ERROR"
            status_errors="agy authentication appears to have failed: run 'agy' interactively once to sign in.
$(errors_tail "$dir/$tn.stderr.log")"
          else
            status_errors=$(errors_tail "$dir/$tn.stderr.log")
          fi
          ;;
        ERROR)
          status_errors="${AGY_CAPTURE_FAIL_REASON:-agy id capture failed for turn 1.} Session id: pending.
$(errors_tail "$dir/$tn.stderr.log")"
          ;;
        TIMEOUT)
          status_errors="turn aborted; resend the prompt to continue the conversation (agy has no repollable in-flight state once its --print process is killed — §9.7).
$(errors_tail "$dir/$tn.stderr.log")"
          ;;
        NO_OUTPUT)
          status_errors="${no_output_hint:-agy exited successfully but produced no output (empty answer) — this is not a crash; the caller got nothing useful and should decide whether to retry, escalate posture, or treat this as a legitimately empty result.}
$(errors_tail "$dir/$tn.stderr.log")"
          ;;
      esac
      if [ -n "$identity_warning" ]; then
        status_errors="${status_errors:+$status_errors
}$identity_warning"
      fi
    else
      if [ "$turn" -eq 1 ] && [ -z "$(meta_get "$dir" session_id)" ]; then
        DIR="$dir"; TURN="$turn"
        adapter_capture_session_id
      fi
      sid=$(meta_get "$dir" session_id)
      [ -z "$sid" ] && sid="pending"
      DIR="$dir"; TURN="$turn"; POSTURE="$posture"
      files_changed=$(adapter_files_changed_summary)

      # DF2: same exit-0-but-empty check as agy, kept CLI-general (a codex
      # turn can also exit 0 with an empty -o file — e.g. a sandbox denial
      # the model didn't retry around). The permission-hint match is
      # mainly an agy shape but costs nothing to also try here.
      no_output_hint=""
      if [ "$status" = "SUCCESS" ] && is_blank_file "$dir/$tn.last-message.txt"; then
        status="NO_OUTPUT"
        hint=$(permission_denial_hint "$dir/$tn.stderr.log" "$dir/$tn.events.jsonl")
        [ -n "$hint" ] && no_output_hint="codex produced no output — possible permission/sandbox denial: $hint"
      fi

      status_errors=""
      if [ "$status" = "NO_OUTPUT" ]; then
        status_errors="${no_output_hint:-codex exited successfully but produced no output (empty answer) — this is not a crash; the caller got nothing useful and should decide whether to retry, escalate posture, or treat this as a legitimately empty result.}
$(errors_tail "$dir/$tn.stderr.log")"
      elif [ "$status" != "SUCCESS" ]; then
        status_errors=$(errors_tail "$dir/$tn.stderr.log")
      fi
    fi

    EB_HANDLE="$handle"; EB_CLI="$cli"; EB_MODE="$mode"; EB_STATUS="$status"
    EB_TURN="$turn"; EB_SESSION="$sid"; EB_DURATION="$duration"
    EB_ANSWERFILE=$(display_path "$dir/$tn.last-message.txt")
    EB_LOGFILE=$(display_path "$dir/$tn.events.jsonl")
    EB_FILESCHANGED="$files_changed"
    EB_REPOLLABLE="no"
    EB_ERRORS="$status_errors"
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
    # agy has no -o equivalent (§9.14 #3) — cmd_status normally populates
    # last-message.txt from the raw stdout capture once the turn is
    # terminal, but a caller can legally reach `slice` without ever having
    # called `status` first. Self-heal here rather than forcing an extra
    # round trip: if the turn already finished (exit.code present), the
    # answer is just sitting in events.jsonl unread.
    cli_for_slice=$(meta_get "$dir" cli)
    if [ "$cli_for_slice" = "agy" ] && [ -f "$dir/$tn.exit.code" ] && [ -f "$dir/$tn.events.jsonl" ]; then
      cp -- "$dir/$tn.events.jsonl" "$answerfile" 2>/dev/null
    fi
  fi
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
        # DF3 #3: wait for the supervisor's OWN terminal signal — the
        # exit.code file — not mere process death. The supervisor's TERM
        # handler escalates to the child (up to a 5s grace) and only THEN
        # writes exit.code and exits; force-killing on a 5s liveness
        # timeout could hit it mid-escalation, skipping the exit.code
        # write and narrowly orphaning the child (whose pgid `stop` never
        # learns). Give the joint contract grace + slack (~8s), and only
        # force-kill if the supervisor never produced a terminal state.
        n=0
        while [ "$n" -lt 8 ] && [ ! -f "$exitfile" ] && kill -0 "$pid" 2>/dev/null; do
          sleep 1
          n=$((n + 1))
        done
        if [ ! -f "$exitfile" ] && kill -0 "$pid" 2>/dev/null; then
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
# list-backends (§3.2/§4.2) — pure read-only registry/probe report. No
# handle, no state directory, no external-model tokens spent: adapter_
# preflight is only invoked under --probe-auth, and even then it's the
# same cheap auth-status check `start` runs before creating a handle
# (`codex login status` / an `agy` state-dir existence check), never a
# real turn.
# ---------------------------------------------------------------------------

cmd_list_backends() {
  json_out=0
  probe_auth=0
  while [ $# -gt 0 ]; do
    case "$1" in
      --json) json_out=1; shift ;;
      --probe-auth) probe_auth=1; shift ;;
      *) die_usage "list-backends: unknown argument: $1" ;;
    esac
  done

  rows_json="[]"
  [ "$json_out" -eq 1 ] || printf '%-8s %-8s %-10s %-9s %-12s %-50s %s\n' \
    "ID" "VENDOR" "INSTALLED" "AUTH" "KIND" "POSTURES(fidelity)" "SIBLING"

  while IFS=' ' read -r id adir; do
    [ -n "$id" ] || continue
    dj="$adir/adapter.json"

    # shellcheck disable=SC1090
    . "$adir/adapter.sh" 2>/dev/null

    installed="no"
    if [ "$(type -t adapter_detect 2>/dev/null)" = "function" ] && adapter_detect; then
      installed="yes"
    fi

    auth="skipped"
    if [ "$probe_auth" -eq 1 ]; then
      if [ "$installed" != "yes" ]; then
        auth="n/a"
      elif [ "$(type -t adapter_preflight 2>/dev/null)" = "function" ]; then
        if adapter_preflight >/dev/null 2>&1; then
          auth="ok"
        else
          auth="fail"
        fi
      else
        auth="n/a"
      fi
    fi

    vendor=$(jq -r '.vendor // "unknown"' "$dj" 2>/dev/null)
    kind=$(jq -r '.kind // "unknown"' "$dj" 2>/dev/null)
    postures=$(jq -r '(.postures // {}) | to_entries | map("\(.key):\(.value.fidelity // "?")") | join(",")' "$dj" 2>/dev/null)
    [ -n "$postures" ] || postures="(none)"

    sibling_match=$(jq -r '.sibling_plugins[0].plugin_match // empty' "$dj" 2>/dev/null)
    sibling="n/a"
    if [ -n "$sibling_match" ]; then
      sibling=$(detect_sibling_plugins "$sibling_match")
    fi

    if [ "$json_out" -eq 1 ]; then
      row=$(jq -n --arg installed "$installed" --arg auth "$auth" --arg sibling "$sibling" \
        --slurpfile desc "$dj" \
        '{descriptor: $desc[0], probe: {installed: $installed, auth: $auth, sibling: $sibling}}' 2>/dev/null)
      [ -n "$row" ] && rows_json=$(printf '%s' "$rows_json" | jq --argjson r "$row" '. + [$r]' 2>/dev/null)
    else
      printf '%-8s %-8s %-10s %-9s %-12s %-50s %s\n' \
        "$id" "$vendor" "$installed" "$auth" "$kind" "$postures" "$sibling"
    fi
  done < <(discover_all_adapters)

  if [ "$json_out" -eq 1 ]; then
    printf '%s\n' "$rows_json"
  fi
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
  list-backends) cmd_list_backends "$@" ;;
  -h|--help|help) usage ;;
  *) die_usage "unknown subcommand: $subcommand" ;;
esac
