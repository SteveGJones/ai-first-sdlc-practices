#!/usr/bin/env bash
# adapter.sh — OpenCode CLI direct-CLI adapter (§2.2 ABI). Sourced by
# extdel.sh (never executed directly) into the SAME shell, so it may call
# engine helpers (meta_get/meta_set, now_iso/now_epoch, is_blank_file,
# quote_args, spawn_daemon, wait_for_file, $SUPERVISOR_PL) directly.
#
# This is the F2 "worked example" adapter from docs/superpowers/specs/
# 2026-07-24-sdlc-simple-orchestration-design.md §4 — the architecture's
# own acceptance test ("adding a backend = one directory, zero engine
# edits"). Built to the §4.4 "OpenCode probe results — CONFIRMED LIVE"
# block, not to guesses; every non-obvious choice below cites the fact it
# implements.
#
# THREE ways OpenCode differs from codex/agy that shape this file:
#   1. Binary location (§4.4 "Install/detect"): real opencode installs to
#      ~/.opencode/bin/opencode and is NOT on the non-interactive Bash
#      PATH — command -v alone is insufficient. opencode_resolve_bin (a
#      private helper, not part of the §2.2 ABI) checks PATH, then
#      ~/.opencode/bin, then an $OPENCODE_BIN override, in that order, and
#      every ABI function that needs to invoke the binary calls it first.
#   2. No native answer file (§4.4 "answer extraction"): opencode has no
#      -o/--output-last-message equivalent the way codex does. Unlike agy
#      (which gets away with plain-stdout-as-answer because cmd_status's
#      HARDCODED `if [ "$cli" = "agy" ]` branch in extdel.sh copies
#      events.jsonl -> last-message.txt itself), any OTHER cli — opencode
#      included — falls through cmd_status's generic (codex-shaped) `else`
#      branch, which expects last-message.txt to already exist and be
#      populated by the time the turn is terminal, and never performs that
#      copy. Since extdel.sh is off-limits to edit, adapter_submit_turn
#      composes a per-turn helper script (turn-NNN.run.sh, written under
#      $DIR — the ABI explicitly allows adapters to write per-handle state
#      there) that runs opencode with its stdout inherited from
#      turn-supervisor.pl's own redirection (so events.jsonl needs no
#      separate raw copy), THEN re-reads that same now-closed file with
#      jq to extract the final text event(s) into last-message.txt, all
#      BEFORE the script exits — no trailing `exec` (unlike codex/agy),
#      because post-processing must run AFTER the opencode child exits.
#      The wrapper script remains killable as a unit: turn-supervisor.pl's
#      forked child calls setpgrp(0,0) on the shell that runs this script,
#      and opencode — spawned as this script's own child, not exec'd —
#      inherits that same process group automatically, so `stop`'s
#      group-directed TERM still reaches it.
#   3. Config-file postures, not sandbox/allow-list flags (§4.4
#      "Postures/permissions", P-OC2/P-OC3): OPENCODE_CONFIG=<per-handle
#      JSON> carries a `permission:{edit,bash,webfetch}=allow|ask|deny`
#      block — "the agy --gemini_dir pattern generalized" per the design.
#      adapter_posture_args writes it fresh every turn (start AND every
#      resume), exactly mirroring agy_write_gemini_config's own
#      idempotent-refresh contract, so a --steal posture escalation
#      mid-conversation is picked up the same way.

OPENCODE_DEFAULT_FREE_MODEL="opencode/deepseek-v4-flash-free"

opencode_resolve_bin() {
  # opencode_resolve_bin — private helper (not §2.2 ABI). Sets
  # OPENCODE_RESOLVED_BIN and returns 0 on success, else returns 1 with
  # OPENCODE_RESOLVED_BIN empty. Order: OPENCODE_BIN override (explicit,
  # wins even if something else is also on PATH) -> PATH -> the confirmed
  # real install location (§4.4).
  if [ -n "${OPENCODE_BIN:-}" ] && [ -x "${OPENCODE_BIN:-}" ]; then
    OPENCODE_RESOLVED_BIN="$OPENCODE_BIN"
    return 0
  fi
  if command -v opencode >/dev/null 2>&1; then
    OPENCODE_RESOLVED_BIN="$(command -v opencode)"
    return 0
  fi
  if [ -x "$HOME/.opencode/bin/opencode" ]; then
    OPENCODE_RESOLVED_BIN="$HOME/.opencode/bin/opencode"
    return 0
  fi
  OPENCODE_RESOLVED_BIN=""
  return 1
}

adapter_detect() {
  opencode_resolve_bin >/dev/null 2>&1
}

adapter_preflight() {
  if ! opencode_resolve_bin; then
    printf 'opencode not found on PATH or ~/.opencode/bin — install per OpenCode docs (or set OPENCODE_BIN to an explicit path)'
    return 1
  fi
  # §4.4 P-OC1: `opencode models` returns a non-empty provider/model list
  # when authed — the cheapest available auth signal (no turn spent).
  models_out=$("$OPENCODE_RESOLVED_BIN" models 2>/dev/null)
  if [ -z "$(printf '%s' "$models_out" | tr -d '[:space:]')" ]; then
    printf "opencode not authenticated (or no models available) — sign in per OpenCode docs, then verify with 'opencode models'"
    return 1
  fi
  return 0
}

adapter_write_opencode_config() {
  # adapter_write_opencode_config <dir> <posture> — private helper (not
  # §2.2 ABI), called from adapter_posture_args below. Writes
  # <dir>/opencode-cfg/opencode.json carrying a posture-graded
  # `permission` block, read via OPENCODE_CONFIG (§4.4 P-OC2/P-OC3). The
  # dangerous posture still gets a config written (content becomes inert
  # once --auto is also passed) so every posture is handled uniformly —
  # mirrors agy's adapter_write_gemini_config exactly on this point.
  dir="$1"; posture="$2"
  cfg_dir="$dir/opencode-cfg"
  mkdir -p "$cfg_dir" 2>/dev/null || return 1
  case "$posture" in
    read-only) perm='{"edit":"deny","bash":"deny","webfetch":"deny"}' ;;
    workspace) perm='{"edit":"allow","bash":"allow","webfetch":"deny"}' ;;
    dangerous) perm='{"edit":"allow","bash":"allow","webfetch":"allow"}' ;;
    *) return 1 ;;
  esac
  printf '{"$schema":"https://opencode.ai/config.json","permission":%s}' "$perm" > "$cfg_dir/opencode.json" 2>/dev/null || return 1
  return 0
}

adapter_posture_args() {
  # adapter_posture_args — echo native argv (one per line) for $POSTURE
  # AND write/refresh this handle's OPENCODE_CONFIG file under $DIR.
  # Return codes mirror agy's contract exactly: 1 = BAD_POSTURE, 2 =
  # CONFIG_FAIL — so adapter_submit_turn can reproduce the same two
  # distinct failure tokens.
  args_out=""
  case "$POSTURE" in
    read-only) ;;
    workspace) ;;
    dangerous) args_out="--auto" ;;
    *) return 1 ;;
  esac

  if ! adapter_write_opencode_config "$DIR" "$POSTURE"; then
    return 2
  fi

  [ -n "$args_out" ] && printf '%s\n' "$args_out"
  return 0
}

adapter_capture_session_id() {
  # Structural, typed capture (same security rationale as codex's own
  # adapter_capture_session_id: never a raw string-grep over the
  # delegated, untrusted model's own output). §4.4 P-OC5b: EVERY event
  # line in a turn's --format json stream carries a top-level
  # "sessionID":"ses_..." field, so scanning all of turn 1's events (not
  # just the first line — real opencode's very first emitted event type
  # is not itself part of the confirmed contract) for the first value
  # matching the real shape is both correct and still restricted to
  # THIS turn's own typed events.
  dir="$DIR"; tn=$(printf 'turn-%03d' "$TURN")
  events="$dir/$tn.events.jsonl"
  sid=""
  if [ -f "$events" ]; then
    sid=$(jq -rs '
      [ .[] | select(type=="object")
            | (.sessionID? // empty)
            | select(type=="string")
            | select(test("^ses_[A-Za-z0-9]+$")) ]
      | if length > 0 then .[0] else empty end
    ' "$events" 2>/dev/null)
  fi
  if [ -n "$sid" ]; then
    printf '%s' "$sid" > "$dir/session.id"
    meta_set "$dir" session_id str "$sid"
  fi
}

adapter_files_changed_summary() {
  # opencode's --format json step_finish events carry token/cost usage
  # (§4.4) but no confirmed structured file-edit record — report plainly
  # rather than fabricate a heuristic parse we don't actually have
  # confidence in (same honesty rule agy's equivalent function follows).
  posture="$POSTURE"
  if [ "$posture" = "read-only" ]; then
    printf 'not tracked (read-only posture)'
    return
  fi
  printf 'not tracked (edit detection not implemented for opencode in this build)'
}

adapter_permission_hint_pattern() {
  # ERE the NO_OUTPUT downgrade greps stderr/events for. P-OC2b's live
  # probe (this build; see adapter.json's notes.posture_caveats for the
  # full transcript summary) confirmed a denied permission under headless
  # `opencode run` auto-denies at the TOOL-AVAILABILITY level ("Model
  # tried to call unavailable tool 'bash'. Available tools: ...") rather
  # than hanging or emitting classic "permission denied" wording — and
  # usually still produces a non-empty explanatory text answer, so this
  # pattern only fires in the narrower case where a denied turn ends with
  # NO text part at all (is_blank_file already true). Kept broad (also
  # covers the config-driven "ask"/"deny" wording OpenCode's own CLI/log
  # output could plausibly use elsewhere) rather than narrowed to only
  # the one exact phrase observed live.
  printf '%s' '(tried to call unavailable tool|permission.*(denied|deny)|denied by (config|policy)|not allowed|requires (the )?permission|no output produced)'
}

adapter_submit_turn() {
  # adapter_submit_turn — same submit-then-poll contract as codex's/agy's
  # (precondition: the caller already holds $DIR's turn lock, acquired
  # BEFORE this turn's prompt file was written).
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
  runscript="$dir/$tn.run.sh"

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
      # Prompt is a positional arg (§4.4); guard a leading-dash value the
      # same way agy does (§9.12 m3-shaped risk) rather than gamble on an
      # unconfirmed `--` separator.
      rm -rf "$lockdir"
      printf 'BAD_PROMPT'
      return 1
      ;;
  esac

  if ! opencode_resolve_bin; then
    rm -rf "$lockdir"
    printf 'SPAWN_FAIL'
    return 1
  fi
  opencode_bin="$OPENCODE_RESOLVED_BIN"

  oc_args=()
  if [ "$turnnum" -gt 1 ]; then
    sid=$(cat "$dir/session.id" 2>/dev/null)
    if [ -z "$sid" ]; then
      rm -rf "$lockdir"
      printf 'NO_SESSION'
      return 1
    fi
    # Never bare --continue (§4.4: "last-session fan-out race") — always
    # resume by explicit id, exactly like codex/agy.
    oc_args+=(--session "$sid")
  else
    # Turn N never re-passes model/effort (session-time properties, not
    # per-turn ones — cmd_prompt already sets $MODEL/$EFFORT to empty
    # strings on turn N, mirrored here by only setting these on turn 1).
    eff_model="$model"
    [ -n "$eff_model" ] || eff_model="$OPENCODE_DEFAULT_FREE_MODEL"
    oc_args+=(-m "$eff_model")
    [ -n "$effort" ] && oc_args+=(--variant "$effort")
  fi
  oc_args+=("${posture_args[@]}")
  oc_args+=(--dir "$cwd" --format json)

  cfgfile="$dir/opencode-cfg/opencode.json"

  # Per-turn helper script (see file header point 2 for the full
  # rationale): reads the prompt from its OWN stdin (turn-supervisor.pl
  # redirects this script's stdin to $promptfile, exactly like codex/agy),
  # runs opencode with stdout left on the inherited fd (-> $eventsfile),
  # then re-reads that file to extract the answer into $lastmsgfile, and
  # only THEN exits with opencode's real exit code — no trailing `exec`.
  {
    printf '#!/bin/sh\n'
    printf 'prompt=$(cat)\n'
    printf 'export OPENCODE_CONFIG=%s\n' "$(printf '%q' "$cfgfile")"
    printf '%s run' "$(printf '%q' "$opencode_bin")"
    for a in "${oc_args[@]}"; do
      printf ' %s' "$(printf '%q' "$a")"
    done
    printf ' "$prompt"\n'
    printf 'rc=$?\n'
    printf 'jq -rs %s %s > %s 2>/dev/null\n' \
      "$(printf '%q' '[.[] | select(type=="object" and .type=="text" and (.part.type? == "text")) | .part.text] | if length>0 then .[-1] else "" end')" \
      "$(printf '%q' "$eventsfile")" "$(printf '%q' "$lastmsgfile")"
    printf 'exit "$rc"\n'
  } > "$runscript" 2>/dev/null
  chmod +x "$runscript" 2>/dev/null

  cmd=(sh "$runscript")
  cmdstr=$(quote_args "${cmd[@]}")
  supcmd="perl $(printf '%q' "$SUPERVISOR_PL") $(printf '%q' "$timeout_s") $(printf '%q' "$promptfile") $(printf '%q' "$eventsfile") $(printf '%q' "$stderrfile") $(printf '%q' "$exitfile") $(printf '%q' "$lockdir") --$cmdstr"

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
