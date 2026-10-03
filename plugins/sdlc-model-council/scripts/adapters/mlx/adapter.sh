#!/usr/bin/env bash
# adapter.sh — MLX local direct-CLI adapter (§2.2 ABI). Sourced by
# extdel.sh (never executed directly) into the SAME shell, so it may call
# engine helpers (meta_get/meta_set, now_iso/now_epoch, is_blank_file,
# quote_args, spawn_daemon, wait_for_file, $SUPERVISOR_PL) directly. Must
# stay bash-3.2-safe (no associative arrays, no ${var,,}).
#
# This is the "Path B" adapter for local Apple-Silicon MLX models: it drives
# a running `mlx_lm.server` OpenAI-compatible endpoint via the small
# `mlx-chat` client shipped alongside this file. The deliberate design point
# (see docs/ADAPTER-AUTHORING.md and retrospectives/232-external-agent-
# delegation.md) is that a turn sends ONLY the delegated item prompt as a
# single user message — NO agentic system prompt — because OpenCode's
# tool-schema-heavy system prompt (Path A, opencode:mlx/*) induced small
# local models to escape quotes in reproduced code, corrupting file-block
# answers; the raw server does not. `mlx-chat` also always sends an explicit
# stop sequence, working around mlx_lm.server's known eos-in-content leak.
#
# THREE ways MLX differs from codex/agy/opencode that shape this file:
#   1. The "binary" (mlx-chat) is shipped IN this adapter directory, not
#      installed on PATH — mlx_resolve_bin checks $MLX_CHAT_BIN, then PATH
#      (where the test mock lives), then $ADAPTER_DIR/mlx-chat.
#   2. No permission surface at all: mlx_lm.server only generates text and
#      this adapter wires no tools, so every posture is structurally
#      read-only. adapter_posture_args writes no config and emits no argv.
#   3. Stateless server (no session ids): resume replays prior turns from the
#      engine's own per-turn files (mlx-chat --history-dir/--turn), and
#      adapter_capture_session_id synthesizes a deterministic local id so the
#      engine's resume gate is satisfied.

MLX_DEFAULT_BASE_URL="http://127.0.0.1:8080/v1"
MLX_DEFAULT_STOP="<|im_end|>"

mlx_base_url() {
  printf '%s' "${MLX_BASE_URL:-$MLX_DEFAULT_BASE_URL}"
}

mlx_own_dir() {
  # Directory this adapter.sh lives in, resolved from BASH_SOURCE so it works
  # even where the engine has not set its $ADAPTER_DIR global (e.g. the
  # list-backends detect loop, which sources adapter.sh with only a local
  # var). Falls back to $ADAPTER_DIR if BASH_SOURCE is somehow unavailable.
  d=""
  if [ -n "${BASH_SOURCE:-}" ]; then
    # ${BASH_SOURCE[0]:-} (not ${BASH_SOURCE[0]}) so this stays safe even if the
    # engine sources adapters under `set -u` — a council-panel review of this
    # very adapter (2026-07-26 Diff+Synthesis) flagged the un-defaulted form.
    d="$(cd "$(dirname "${BASH_SOURCE[0]:-}")" 2>/dev/null && pwd -P)"
  fi
  [ -n "$d" ] || d="${ADAPTER_DIR:-}"
  printf '%s' "$d"
}

mlx_resolve_bin() {
  # Sets MLX_RESOLVED_BIN and returns 0 on success, else 1 with it empty.
  # Order: explicit $MLX_CHAT_BIN override -> PATH (mock lives here in tests)
  # -> the client shipped in this adapter's own directory (resolved from
  # BASH_SOURCE, so detect works in the list-backends loop too).
  if [ -n "${MLX_CHAT_BIN:-}" ] && [ -x "${MLX_CHAT_BIN:-}" ]; then
    MLX_RESOLVED_BIN="$MLX_CHAT_BIN"
    return 0
  fi
  if command -v mlx-chat >/dev/null 2>&1; then
    MLX_RESOLVED_BIN="$(command -v mlx-chat)"
    return 0
  fi
  own_dir="$(mlx_own_dir)"
  if [ -n "$own_dir" ] && [ -x "$own_dir/mlx-chat" ]; then
    MLX_RESOLVED_BIN="$own_dir/mlx-chat"
    return 0
  fi
  MLX_RESOLVED_BIN=""
  return 1
}

adapter_detect() {
  mlx_resolve_bin >/dev/null 2>&1 || return 1
  "$MLX_RESOLVED_BIN" --version >/dev/null 2>&1
}

adapter_preflight() {
  if ! mlx_resolve_bin; then
    printf 'mlx-chat client not found — expected in the adapter directory (or set MLX_CHAT_BIN)'
    return 1
  fi
  # Cheap server reachability probe via the client (the mock satisfies this
  # without a real server, so behavioral tests need no weights). Never a real
  # turn's worth of work.
  if ! "$MLX_RESOLVED_BIN" --probe --base-url "$(mlx_base_url)" >/dev/null 2>&1; then
    printf 'mlx_lm.server not reachable at %s — start it: uv run mlx_lm.server --model <hf-id> --port 8080 (or set MLX_BASE_URL)' "$(mlx_base_url)"
    return 1
  fi
  return 0
}

adapter_posture_args() {
  # MLX has no permission surface — text generation only, no tools wired — so
  # every valid posture yields no native argv and writes no config. Still
  # validate the posture so an unrecognized one is a clean BAD_POSTURE.
  case "$POSTURE" in
    read-only|workspace|dangerous) ;;
    *) return 1 ;;
  esac
  return 0
}

adapter_capture_session_id() {
  # mlx_lm.server is stateless — there is no backend session id to capture.
  # Synthesize a deterministic local id from the handle (basename of $DIR) so
  # the engine's resume gate (meta.session_id non-null) is satisfied and
  # resume turns can replay history from the per-turn files. Never crashes.
  dir="$DIR"
  [ -n "$dir" ] || return 0
  sid="mlx-conv-$(basename "$dir")"
  printf '%s' "$sid" > "$dir/session.id" 2>/dev/null || return 0
  meta_set "$dir" session_id str "$sid"
  return 0
}

adapter_files_changed_summary() {
  # MLX cannot touch the filesystem under any posture.
  printf 'not tracked (MLX has no filesystem surface)'
}

adapter_permission_hint_pattern() {
  # MLX has no permission-denial signature — an empty answer is a genuine
  # empty generation, not a denied tool call. Empty pattern is the honest
  # answer.
  printf '%s' ''
}

adapter_submit_turn() {
  # Compose the mlx-chat argv for turn $TURN and launch it via spawn_daemon +
  # turn-supervisor.pl, exactly like codex's adapter. Precondition: the caller
  # already holds $DIR's turn lock. The prompt is delivered on stdin (the
  # supervisor redirects this process's stdin to the prompt file), so — unlike
  # codex/opencode's positional prompt — a leading-dash prompt needs no guard.
  dir="$DIR"; turnnum="$TURN"; model="$MODEL"; timeout_s="$TIMEOUT_S"

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

  posture_lines=$(adapter_posture_args)
  if [ $? -ne 0 ]; then
    rm -rf "$lockdir"
    printf 'BAD_POSTURE'
    return 1
  fi
  # (posture_lines is intentionally empty for MLX — no native argv.)

  if ! mlx_resolve_bin; then
    rm -rf "$lockdir"
    printf 'SPAWN_FAIL'
    return 1
  fi
  client="$MLX_RESOLVED_BIN"

  if [ "$turnnum" -gt 1 ]; then
    sid=$(cat "$dir/session.id" 2>/dev/null)
    if [ -z "$sid" ]; then
      rm -rf "$lockdir"
      printf 'NO_SESSION'
      return 1
    fi
  fi

  cmd=("$client" --base-url "$(mlx_base_url)" --stop "${MLX_STOP:-$MLX_DEFAULT_STOP}" \
       --history-dir "$dir" --turn "$turnnum" -o "$lastmsgfile")
  # Model is a turn-1 (session-time) property; the engine sets $MODEL empty on
  # resume. The stateless server serves one loaded model regardless, so this
  # only labels the request's `model` field.
  [ -n "$model" ] && cmd+=(--model "$model")

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
