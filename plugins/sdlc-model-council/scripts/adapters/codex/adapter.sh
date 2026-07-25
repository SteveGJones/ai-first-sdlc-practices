#!/usr/bin/env bash
# adapter.sh — codex direct-CLI adapter (§2.2 ABI). Sourced by extdel.sh
# (never executed directly) into the SAME shell, so it may call engine
# helpers (meta_get/meta_set, now_iso/now_epoch, is_blank_file,
# quote_args, spawn_daemon, wait_for_file, $SUPERVISOR_PL) directly.
#
# This is a mechanical, behavior-preserving extraction of the codex-
# specific functions that used to live inline in extdel.sh (pre-
# extraction: preflight_codex ~352, codex_sandbox_args ~364,
# capture_session_id ~375, files_changed_summary ~442,
# submit_codex_turn ~483 — see docs/superpowers/specs/
# 2026-07-24-sdlc-model-council-design.md §2.2). Only the
# function NAMES (to the §2.2 ABI) and the calling convention (engine-
# set globals: $DIR $HANDLE $CLI $POSTURE $TURN $PROMPT_FILE $TIMEOUT_S
# $CWD $ADD_DIRS $MODEL $EFFORT, set by extdel.sh immediately before
# each call, in place of the old positional-argument calls) changed —
# the function BODIES are byte-for-byte the same logic as before.

adapter_detect() {
  command -v codex >/dev/null 2>&1
}

adapter_preflight() {
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

adapter_posture_args() {
  # adapter_posture_args — echo native argv (one element per line — safe
  # here since none of codex's posture flags contain internal whitespace)
  # for $POSTURE. Extracted from codex_sandbox_args.
  case "$POSTURE" in
    read-only) printf '%s\n' -s read-only ;;
    workspace) printf '%s\n' -s workspace-write ;;
    dangerous) printf '%s\n' --dangerously-bypass-approvals-and-sandbox ;;
    *) return 1 ;;
  esac
  return 0
}

adapter_capture_session_id() {
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
  dir="$DIR"; tn=$(printf 'turn-%03d' "$TURN")
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

adapter_files_changed_summary() {
  dir="$DIR"; tn=$(printf 'turn-%03d' "$TURN"); posture="$POSTURE"
  events="$dir/$tn.events.jsonl"
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

adapter_permission_hint_pattern() {
  printf '%s' '(no output produced|auto-denied|required the .*permission|permission.*denied)'
}

adapter_submit_turn() {
  # adapter_submit_turn — compose full codex argv for turn $TURN (start if
  # 1 & no session.id, else resume) and launch via spawn_daemon +
  # turn-supervisor.pl (engine helpers, available since this file is
  # sourced into extdel.sh's own shell — see the file header decision
  # note on NOT factoring a separate engine_spawn_turn).
  #
  # Precondition (unchanged from pre-extraction submit_codex_turn): the
  # caller already holds $DIR's turn lock, acquired BEFORE this turn's
  # prompt file was written. This function does not itself acquire the
  # lock — only releases it on a failure that happens before the
  # supervisor takes over ownership.
  dir="$DIR"; turnnum="$TURN"; cwd="$CWD"; posture="$POSTURE"
  model="$MODEL"; effort="$EFFORT"; timeout_s="$TIMEOUT_S"

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

  posture_args=()
  posture_lines=$(adapter_posture_args)
  posture_rc=$?
  if [ "$posture_rc" -ne 0 ]; then
    rm -rf "$lockdir"
    printf 'BAD_POSTURE'
    return 1
  fi
  while IFS= read -r pl; do
    [ -n "$pl" ] && posture_args+=("$pl")
  done <<< "$posture_lines"

  cmd=(codex)
  if [ "$turnnum" -eq 1 ]; then
    cmd+=(exec --json -o "$lastmsgfile" -C "$cwd")
    for d in "${ADD_DIRS[@]}"; do
      [ -n "$d" ] && cmd+=(--add-dir "$d")
    done
    cmd+=("${posture_args[@]}")
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
    for d in "${ADD_DIRS[@]}"; do
      [ -n "$d" ] && cmd+=(--add-dir "$d")
    done
    cmd+=("${posture_args[@]}")
    cmd+=(--color never --skip-git-repo-check -)
  fi

  cmdstr=$(quote_args "${cmd[@]}")
  supcmd="perl $(printf '%q' "$SUPERVISOR_PL") $(printf '%q' "$timeout_s") $(printf '%q' "$promptfile") $(printf '%q' "$eventsfile") $(printf '%q' "$stderrfile") $(printf '%q' "$exitfile") $(printf '%q' "$lockdir") --$cmdstr"

  now_epoch > "$startedfile"
  spawn_daemon "$pidfile" "$supcmd" "$bootlog"
  wait_for_file "$pidfile" 3

  if [ ! -f "$pidfile" ] || [ ! -s "$pidfile" ]; then
    # Spawn failure: the supervisor never started (perl missing, exec
    # failed, etc). Without this check, adapter_submit_turn would print
    # OK unconditionally and `status` would then see an empty pid and no
    # exit file forever — RUNNING with no process behind it. Release the
    # lock ourselves since no supervisor exists to do it.
    rm -rf "$lockdir"
    printf 'SPAWN_FAIL'
    return 1
  fi

  # NOTE: ownership of the lock's owner.pid marker is claimed by
  # turn-supervisor.pl ITSELF, synchronously, immediately after its own
  # fork — not handed off from here (see lock_is_stale/acquire_turn_lock
  # in extdel.sh for the full race-avoidance rationale, unchanged by this
  # extraction).

  printf 'OK'
  return 0
}
