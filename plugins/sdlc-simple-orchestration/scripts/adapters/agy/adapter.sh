#!/usr/bin/env bash
# adapter.sh — agy (Antigravity CLI) direct-CLI adapter (§2.2 ABI,
# authoritative for id-capture: design §9.14/§9.15). Sourced by extdel.sh
# (never executed directly) into the SAME shell, so it may call engine
# helpers (meta_get/meta_set, now_iso/now_epoch, is_blank_file,
# quote_args, spawn_daemon, wait_for_file, $SUPERVISOR_PL) directly.
#
# This is a mechanical, behavior-preserving extraction of the agy-
# specific functions that used to live inline in extdel.sh (pre-
# extraction: preflight_agy ~587, agy_posture_args ~603,
# agy_write_gemini_config ~624, agy_auth_backstop_matched ~671,
# agy_gemini_dir_cache_file ~683, agy_read_last_conversations_id ~693,
# capture_agy_session_id ~736, agy_check_identity_drift ~769,
# agy_files_changed_summary ~792, submit_agy_turn ~805 — see
# docs/superpowers/specs/2026-07-24-sdlc-simple-orchestration-design.md
# §2.2). Only the §2.2-ABI function NAMES and the calling convention
# (engine-set globals: $DIR $HANDLE $CLI $POSTURE $TURN $PROMPT_FILE
# $TIMEOUT_S $CWD $ADD_DIRS $MODEL $EFFORT, plus $AGENT — agy-only,
# not in the design's abbreviated env-var list but required to preserve
# the `--agent NAME` flag's existing behavior byte-for-byte — set by
# extdel.sh immediately before each call, in place of the old
# positional-argument calls) changed. Non-ABI internal helpers
# (agy_auth_backstop_matched, agy_gemini_dir_cache_file,
# agy_read_last_conversations_id, adapter_write_gemini_config) keep
# their original bodies verbatim and are private to this adapter.

# agy state (§9.14/§9.15): read from $HOME so tests can redirect it
# wholesale by overriding HOME before invoking extdel.sh — never touch the
# real ~/.gemini/antigravity-cli/ from a test. AGY_STATE_DIR is used ONLY
# by adapter_preflight's initialized-check (DF1, §9.15): auth/credentials
# live in the REAL ~/.gemini/antigravity-cli/ (on disk and/or keychain),
# not in the per-handle --gemini_dir this build creates, which carries
# only a posture-graded permissions.allow and inherits auth from outside
# itself (confirmed live).
AGY_STATE_DIR="$HOME/.gemini/antigravity-cli"

adapter_detect() {
  command -v agy >/dev/null 2>&1
}

adapter_preflight() {
  if ! command -v agy >/dev/null 2>&1; then
    printf 'agy not found on PATH — install per Antigravity docs'
    return 1
  fi
  # agy has no `login status` verb (§6.1/§6.2) — the best available
  # sanity check is that the state directory exists at all. A first-ever
  # `agy` run creates it; its absence means agy has literally never been
  # signed into on this machine.
  if [ ! -d "$AGY_STATE_DIR" ]; then
    printf "agy not initialized — run 'agy' interactively once to sign in"
    return 1
  fi
  return 0
}

adapter_write_gemini_config() {
  # adapter_write_gemini_config <dir> <posture> — DF1 (§9.15): write a
  # per-handle agy config dir (<dir>/agy-cfg/antigravity-cli/settings.json)
  # carrying a posture-graded `permissions.allow` list, read via
  # `agy --gemini_dir`. Confirmed live: --gemini_dir is honored, auth is
  # inherited from OUTSIDE the dir (a minimal dir containing only
  # settings.json works — no credentials copied), and its permissions.allow
  # takes effect. Rule formats verified: `read_file(<glob>)` (we use
  # `read_file(*)`) and `command(<prefix>)` (bare prefix, e.g.
  # `command(git)` — NOT `command(git *)`).
  #
  # Called on every adapter_posture_args invocation (start turn 1 AND
  # every resume turn, via adapter_submit_turn), so it also picks up a
  # --steal posture escalation mid-conversation — rewriting is idempotent
  # and cheap (one small JSON file). Private helper (not in the §2.2 ABI
  # table) called from adapter_posture_args below.
  dir="$1"; posture="$2"
  cfg_root="$dir/agy-cfg/antigravity-cli"
  mkdir -p "$cfg_root" 2>/dev/null || return 1

  read_cmds='"command(cat)","command(head)","command(tail)","command(sed)","command(grep)","command(rg)","command(ls)","command(find)","command(wc)","command(git)"'
  case "$posture" in
    read-only)
      # Reads + review only. No write_file/edit_file rule at all — the
      # confirmed-working read-only config from the live probe.
      allow="[\"read_file(*)\",$read_cmds]"
      ;;
    workspace)
      # Read-only's list PLUS writes/edits and a broader build/test
      # command set, so the delegated model can make and verify changes
      # within cwd.
      write_cmds='"command(python)","command(python3)","command(node)","command(npm)","command(pytest)","command(go)","command(cargo)","command(make)","command(bash)","command(sh)"'
      allow="[\"read_file(*)\",\"write_file(*)\",\"edit_file(*)\",$read_cmds,$write_cmds]"
      ;;
    dangerous)
      # --dangerously-skip-permissions (adapter_posture_args's native argv)
      # supersedes this allow-list entirely, but --gemini_dir is still
      # passed on every invocation uniformly (see adapter_submit_turn)
      # rather than special-cased per posture, so a config file is
      # written here regardless — content is inert once the skip flag is
      # present.
      allow="[\"read_file(*)\",\"write_file(*)\",\"edit_file(*)\",$read_cmds]"
      ;;
    *) return 1 ;;
  esac

  printf '{"enableTelemetry":false,"permissions":{"allow":%s}}' "$allow" > "$cfg_root/settings.json" 2>/dev/null || return 1
  return 0
}

adapter_posture_args() {
  # adapter_posture_args — echo native argv (one element per line — safe
  # here since agy's only posture-driven flag, --dangerously-skip-
  # permissions, has no internal whitespace) for $POSTURE, AND write/
  # refresh this handle's per-turn --gemini_dir config under $DIR (§2.2:
  # "MAY write per-handle config under $DIR"). Merges the pre-extraction
  # agy_posture_args (native flag selection) + agy_write_gemini_config
  # (config write) — both were called together on every submit_agy_turn
  # invocation, so merging them into one ABI call preserves that pairing
  # exactly.
  #
  # Distinct failure codes so adapter_submit_turn can reproduce the two
  # separate pre-extraction error tokens: 1 = BAD_POSTURE (unrecognized
  # posture name), 2 = CONFIG_FAIL (config write failed for a recognized
  # posture, e.g. an unwritable state dir).
  args_out=""
  case "$POSTURE" in
    read-only) ;;
    workspace) ;;
    dangerous) args_out="--dangerously-skip-permissions" ;;
    *) return 1 ;;
  esac

  if ! adapter_write_gemini_config "$DIR" "$POSTURE"; then
    return 2
  fi

  [ -n "$args_out" ] && printf '%s\n' "$args_out"
  return 0
}

adapter_auth_backstop_matched() {
  # Runtime auth backstop (§6.2): a first-turn failure whose stderr/CLI-log
  # matches an auth-shaped pattern is ERROR(auth), distinct from a
  # model-level FAILURE (e.g. the delegated model correctly refusing a
  # request, or a sandbox denial) which is not an auth problem at all.
  for f in "$@"; do
    [ -f "$f" ] || continue
    grep -Eiq '(auth|sign.?in|login|unauthorized|credential)' "$f" 2>/dev/null && return 0
  done
  return 1
}

adapter_gemini_dir_cache_file() {
  # adapter_gemini_dir_cache_file <dir> — prints the per-handle, isolated
  # last_conversations.json path under this handle's own --gemini_dir
  # (DF1, §9.15 ground truth #3: a per-handle --gemini_dir isolates that
  # delegation's conversation store, so id-capture reads from HERE, not a
  # global cwd-keyed cache shared with every other agy user on the
  # machine).
  printf '%s/agy-cfg/antigravity-cli/cache/last_conversations.json' "$1"
}

adapter_read_last_conversations_id() {
  # adapter_read_last_conversations_id <cwd_norm> <cache_file>
  # §9.14 (authoritative for shape/retry) as adapted by DF1/§9.15: the
  # cache file is now the per-handle isolated one (see
  # adapter_gemini_dir_cache_file), not a global path under the real HOME
  # — each handle gets its own conversation store, so cross-handle/cross-
  # project same-cwd races that used to require a first-call mkdir lock
  # (§5.2/§9.6) no longer apply to id capture: there is nothing shared to
  # race over. (A same-cwd race against the user's OWN interactive agy —
  # which still uses the real ~/.gemini — remains structurally impossible
  # to observe here since that agy never writes into our --gemini_dir at
  # all.) The flat {"<abs cwd>": "<uuid>"} shape and the 3x/500ms
  # parse-retry (both cache files are rewritten wholesale by agy, a
  # TOCTOU hazard) are unchanged from §9.14.
  #
  # Return codes distinguish WHY capture failed, so the caller can tell a
  # "never initialized" signal from a benign "not this cwd yet":
  #   0 = success, uuid printed on stdout
  #   1 = the cache file was missing or never parsed as a JSON object in
  #       any of the 3 tries (agy-not-initialized-shaped failure)
  #   2 = the file parsed fine at least once, but this cwd's key was never
  #       present (id capture failed for this specific delegation)
  cwd_key="$1"; cache_file="$2"
  n=0
  parsed_ok=0
  while [ "$n" -lt 3 ]; do
    if [ -f "$cache_file" ]; then
      if jq -e 'type=="object"' "$cache_file" >/dev/null 2>&1; then
        parsed_ok=1
        sid_candidate=$(jq -r --arg k "$cwd_key" '.[$k] // empty' "$cache_file" 2>/dev/null)
        if printf '%s' "$sid_candidate" | grep -Eq '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'; then
          printf '%s' "$sid_candidate"
          return 0
        fi
      fi
    fi
    n=$((n + 1))
    [ "$n" -lt 3 ] && sleep 0.5
  done
  [ "$parsed_ok" -eq 1 ] && return 2
  return 1
}

adapter_capture_session_id() {
  # capture_agy_session_id, extracted — turn-1-only, called from
  # cmd_status once the turn reaches terminal SUCCESS (or, per DF2, an
  # exit-0 turn that is about to be downgraded to NO_OUTPUT — capture
  # still runs first: the conversation exists server-side even when the
  # requested tool call inside it was permission-denied, so it's still a
  # valid resume target under a broader posture). Reads $DIR/$CWD (the
  # engine sets $CWD to the handle's stored cwd before calling this from
  # cmd_status). Sets $AGY_CAPTURE_FAIL_REASON on failure so cmd_status
  # can surface a precise message without re-deriving the reason.
  dir="$DIR"; cwd="$CWD"
  AGY_CAPTURE_FAIL_REASON=""
  cwd_norm=$(cd "$cwd" 2>/dev/null && pwd -P)
  [ -n "$cwd_norm" ] || cwd_norm="$cwd"

  cache_file=$(adapter_gemini_dir_cache_file "$dir")
  sid=$(adapter_read_last_conversations_id "$cwd_norm" "$cache_file")
  rc=$?

  if [ "$rc" -eq 0 ] && [ -n "$sid" ]; then
    printf '%s' "$sid" > "$dir/session.id"
    meta_set "$dir" session_id str "$sid"
    meta_set "$dir" agy_cwd_key str "$cwd_norm"
    return 0
  fi

  if [ "$rc" -eq 1 ]; then
    AGY_CAPTURE_FAIL_REASON="agy state file $(display_path "$cache_file") is missing or unparseable after 3 retries — is agy initialized? Run 'agy' interactively once to sign in."
  else
    AGY_CAPTURE_FAIL_REASON="no entry for this cwd in $(display_path "$cache_file") after 3 retries — id capture failed."
  fi
  return 1
}

adapter_check_identity_drift() {
  # agy_check_identity_drift, extracted (optional §2.2 ABI function) —
  # turn N>1 check: has this handle's OWN isolated last_conversations.
  # json[cwd] moved to a different conversation since we captured
  # session.id at turn 1? (§9.14: "if it changed identity, surface a
  # warning in the return rather than silently resuming wrong.") We
  # never act on this — only warn; the next turn still resumes OUR
  # recorded session.id via --conversation, never whatever the cache
  # currently says. Reads $DIR (engine-set before this call).
  dir="$DIR"
  stored_sid=$(meta_get "$dir" session_id)
  cwd_key=$(meta_get "$dir" agy_cwd_key)
  [ -n "$stored_sid" ] && [ -n "$cwd_key" ] || return 0
  cache_file=$(adapter_gemini_dir_cache_file "$dir")
  current_sid=$(adapter_read_last_conversations_id "$cwd_key" "$cache_file")
  if [ -n "$current_sid" ] && [ "$current_sid" != "$stored_sid" ]; then
    printf 'WARNING: last_conversations.json for this cwd now points to a different agy conversation (%s) than this handle'\''s session (%s) — NOT auto-resuming the new one; another agy process may be running in the same cwd. Verify before continuing if this is unexpected.' "$current_sid" "$stored_sid"
  fi
}

adapter_files_changed_summary() {
  posture="$POSTURE"
  if [ "$posture" = "read-only" ]; then
    printf 'not tracked (read-only posture)'
    return
  fi
  # agy's --log-file format for edit records has not been verified against
  # a real agy release (open item per the design doc's §4.2) — report
  # plainly rather than fabricate a heuristic parse that would misreport
  # confidence we don't actually have.
  printf 'not tracked (edit detection not implemented for agy in this build)'
}

adapter_permission_hint_pattern() {
  printf '%s' '(no output produced|auto-denied|required the .*permission|permission.*denied)'
}

adapter_submit_turn() {
  # adapter_submit_turn — same submit-then-poll contract as codex's
  # (precondition: the caller already holds $DIR's turn lock, acquired
  # BEFORE this turn's prompt file was written). agy differs from codex
  # in ways that shape this function:
  #   1. agy has no -C/--cd flag — it runs in the PROCESS cwd (§9.14 #2),
  #      so the actual invocation is wrapped in a `cd "$cwd" && exec agy
  #      ...` inner shell rather than exec'd directly.
  #   2. agy's --print takes the prompt as its FLAG VALUE, and --print MUST
  #      be the LAST flag with the prompt immediately after it (§9.14 #2)
  #      — never interleave flags between --print and the prompt. Getting
  #      this wrong silently drops the real prompt (observed live).
  #   3. agy has no -o/--output-last-message equivalent: its answer is
  #      plain stdout, which turn-supervisor.pl already redirects to
  #      eventsfile — cmd_status copies that into last-message.txt once
  #      the turn is terminal, so this function does NOT write a
  #      last-message file itself.
  #   4. Turn N never re-passes --model/--effort/--agent (mirrors codex
  #      resume, which never re-passes -m/-c on `exec resume` either —
  #      those are session-time properties, not per-turn ones); the
  #      caller (cmd_prompt) sets $MODEL/$EFFORT/$AGENT to empty strings
  #      on turn N.
  dir="$DIR"; turnnum="$TURN"; cwd="$CWD"; posture="$POSTURE"
  model="$MODEL"; effort="$EFFORT"; agent="$AGENT"; timeout_s="$TIMEOUT_S"

  tn=$(printf 'turn-%03d' "$turnnum")
  promptfile="$dir/$tn.prompt.txt"
  eventsfile="$dir/$tn.events.jsonl"
  stderrfile="$dir/$tn.stderr.log"
  agylogfile="$dir/$tn.agy.log"
  exitfile="$dir/$tn.exit.code"
  pidfile="$dir/$tn.pid"
  startedfile="$dir/$tn.started"
  bootlog="$dir/$tn.spawn.log"
  lockdir="$dir/.turn-lock"

  : > "$eventsfile"
  : > "$stderrfile"
  rm -f "$exitfile"

  posture_args=()
  posture_lines=$(adapter_posture_args)
  posture_rc=$?
  if [ "$posture_rc" -eq 1 ]; then
    rm -rf "$lockdir"
    printf 'BAD_POSTURE'
    return 1
  elif [ "$posture_rc" -eq 2 ]; then
    rm -rf "$lockdir"
    printf 'CONFIG_FAIL'
    return 1
  fi
  while IFS= read -r pl; do
    [ -n "$pl" ] && posture_args+=("$pl")
  done <<< "$posture_lines"

  prompt_text=$(cat "$promptfile" 2>/dev/null)
  case "$prompt_text" in
    -*)
      # §9.12 m3: agy's flag parser (Go-style) would treat a leading-dash
      # prompt VALUE as an option rather than data. Refuse rather than
      # risk the prompt silently misparsing — the same failure shape as
      # the flag-ordering bug in §9.14 finding #2, just triggered by the
      # value instead of the ordering.
      rm -rf "$lockdir"
      printf 'BAD_PROMPT'
      return 1
      ;;
  esac

  agy_args=()
  if [ "$turnnum" -gt 1 ]; then
    sid=$(cat "$dir/session.id" 2>/dev/null)
    if [ -z "$sid" ]; then
      rm -rf "$lockdir"
      printf 'NO_SESSION'
      return 1
    fi
    # Never --continue (§2.3/§9.14): --continue races under fan-out the
    # same way codex's `resume --last` does. Always resume by explicit id.
    agy_args+=(--conversation "$sid")
  fi
  [ -n "$model" ] && agy_args+=(--model "$model")
  [ -n "$effort" ] && agy_args+=(--effort "$effort")
  [ -n "$agent" ] && agy_args+=(--agent "$agent")
  agy_args+=("${posture_args[@]}")
  # DF1 (§9.15): the per-handle config dir just written by
  # adapter_write_gemini_config (via adapter_posture_args above), carrying
  # this handle's posture-graded permissions.allow list — passed on EVERY
  # invocation (start turn 1 AND every resume turn), not just turn 1.
  agy_args+=(--gemini_dir "$dir/agy-cfg")
  for d in "${ADD_DIRS[@]}"; do
    [ -n "$d" ] && agy_args+=(--add-dir "$d")
  done
  agy_args+=(--print-timeout "${timeout_s}s" --log-file "$agylogfile")
  # --print MUST be last, prompt immediately after it (§9.14 #2) — nothing
  # may be appended to agy_args below this line.
  agy_args+=(--print "$prompt_text")

  # agy has no -C flag, so the real invocation must run inside a `cd`
  # shell. This is a SECOND, independent quoting pass from the outer
  # supcmd/quote_args layer below: printf %q here escapes $cwd and each
  # arg so THIS inner `sh -c` parses them back exactly, and quote_args
  # then escapes the resulting single string as one opaque argv element
  # for the outer spawn_daemon shell to hand to perl unchanged. Multi-line
  # prompts survive both passes because printf %q round-trips newlines.
  inner="cd $(printf '%q' "$cwd") && exec agy"
  for a in "${agy_args[@]}"; do
    inner="$inner $(printf '%q' "$a")"
  done
  cmd=(sh -c "$inner")

  cmdstr=$(quote_args "${cmd[@]}")
  # Timeout: agy's own --print-timeout is the primary, native deadline
  # (verified non-hanging for the read-only posture — §9.14 #1); the
  # supervisor's perl-alarm is kept only as a hard backstop in case
  # --print-timeout itself fails to fire, so it's set comfortably past the
  # native one (timeout_s + 30) rather than racing it.
  alarm_timeout=$((timeout_s + 30))
  supcmd="perl $(printf '%q' "$SUPERVISOR_PL") $(printf '%q' "$alarm_timeout") $(printf '%q' "$promptfile") $(printf '%q' "$eventsfile") $(printf '%q' "$stderrfile") $(printf '%q' "$exitfile") $(printf '%q' "$lockdir") --$cmdstr"

  now_epoch > "$startedfile"
  spawn_daemon "$pidfile" "$supcmd" "$bootlog"
  wait_for_file "$pidfile" 3

  if [ ! -f "$pidfile" ] || [ ! -s "$pidfile" ]; then
    rm -rf "$lockdir"
    printf 'SPAWN_FAIL'
    return 1
  fi

  printf 'OK'
  return 0
}
