#!/usr/bin/env bash
# mlx-server-run.sh — start `mlx_lm.server` with durable, unbuffered logging
# and a resource heartbeat, for local MLX assessment runs (Path A via
# mlx-stop-proxy.py, or Path B via mlx-chat).
#
# Why this exists: the actual generation for BOTH Path A and Path B happens
# inside this server process, on-device via Metal — and local MLX runs have
# been observed taking the whole machine down with a kernel panic (reboot),
# which destroys anything the server only held in memory or an unflushed
# stdout buffer. Ad hoc `... > log.txt 2>&1 &` one-liners lose exactly the
# tail of output that would explain a crash. This wrapper instead:
#   - runs the server with PYTHONUNBUFFERED=1 so log lines hit disk as
#     they're produced, not when a buffer fills
#   - timestamps every server log line at the moment it's written
#   - samples memory (vm_stat) and this process's RSS every --heartbeat-s
#     seconds to a companion log, fsync'd each write — rising memory/swap
#     pressure right up to the last heartbeat is the strongest available
#     signal for "why", since Apple Silicon kernel panics under local-LLM
#     load are typically GPU/unified-memory pressure related
#   - writes server-info.json (pid, model, port, started-at) so a post-mortem
#     can correlate the model with the log/heartbeat files without having to
#     grep the command line out of `ps` history that a reboot may have lost
#
# Known risk: on a 32GB unified-memory machine, a 32B-parameter dense model
# (e.g. Qwen2.5-Coder-32B-Instruct-4bit) has panicked the kernel outright
# under GPU memory pressure, especially on long-context items — twice during
# council-tool-use-assessment work (#235). See adapter.json's "hardware_risk"
# note. This heartbeat/log wrapper helps diagnose it after the fact; it does
# not prevent it. Prefer smaller/MoE models (7B/14B/30B-A3B) for unattended
# fleet runs; run 32B in isolation if you must.
#
# Usage:
#   mlx-server-run.sh --model <hf-id-or-path> [--port 8082] \
#     [--log-dir tmp/model-council/mlx-server] [--heartbeat-s 5] [-- extra mlx_lm.server args]
#
# Runs mlx_lm.server in the FOREGROUND (like the ad hoc scripts it replaces);
# background it yourself with `&` if you want the shell back. Ctrl-C stops
# both the server and the heartbeat sampler.
set -u

die() { echo "mlx-server-run.sh: $1" >&2; exit 1; }

MODEL=""; PORT=8082; LOG_DIR=""; HEARTBEAT_S=5
EXTRA_ARGS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --model) MODEL="$2"; shift 2 ;;
    --port) PORT="$2"; shift 2 ;;
    --log-dir) LOG_DIR="$2"; shift 2 ;;
    --heartbeat-s) HEARTBEAT_S="$2"; shift 2 ;;
    --) shift; EXTRA_ARGS=("$@"); break ;;
    *) die "unknown option: $1" ;;
  esac
done
[ -n "$MODEL" ] || die "--model is required"

RUN_CWD="$(pwd -P)"
[ -n "$LOG_DIR" ] || LOG_DIR="$RUN_CWD/tmp/model-council/mlx-server"
mkdir -p "$LOG_DIR" || die "cannot create log dir $LOG_DIR"

TS_LABEL="$(date -u +%Y%m%dT%H%M%SZ)"
SERVER_LOG="$LOG_DIR/$TS_LABEL.server.log"
HEARTBEAT_LOG="$LOG_DIR/$TS_LABEL.heartbeat.jsonl"
INFO_FILE="$LOG_DIR/$TS_LABEL.server-info.json"

: > "$SERVER_LOG"
: > "$HEARTBEAT_LOG"

log_line() { printf '[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$1"; }

log_line "starting mlx_lm.server model=$MODEL port=$PORT log_dir=$LOG_DIR" >> "$SERVER_LOG"

PYTHONUNBUFFERED=1 uv run mlx_lm.server --model "$MODEL" --port "$PORT" \
  ${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"} \
  2>&1 | while IFS= read -r line; do
    printf '[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$line" >> "$SERVER_LOG"
  done &
SERVER_PID=$!

python3 - "$INFO_FILE" "$MODEL" "$PORT" "$SERVER_PID" "$SERVER_LOG" "$HEARTBEAT_LOG" <<'PY'
import json, sys, time
path, model, port, pid, server_log, heartbeat_log = sys.argv[1:7]
json.dump({
    "model": model, "port": int(port), "server_pid": int(pid),
    "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "server_log": server_log, "heartbeat_log": heartbeat_log,
}, open(path, "w", encoding="utf-8"))
PY

heartbeat_loop() {
  while kill -0 "$SERVER_PID" 2>/dev/null; do
    python3 - "$HEARTBEAT_LOG" "$SERVER_PID" <<'PY'
import json, os, subprocess, sys, time

log_path, pid = sys.argv[1], sys.argv[2]

def vm_stat():
    out = {}
    try:
        text = subprocess.run(["vm_stat"], capture_output=True, text=True, timeout=5).stdout
        for line in text.splitlines():
            if ":" not in line:
                continue
            k, v = line.split(":", 1)
            v = v.strip().rstrip(".")
            if v.isdigit():
                out[k.strip()] = int(v)
    except Exception:
        pass
    return out

def rss_kb(pid):
    try:
        out = subprocess.run(["ps", "-o", "rss=", "-p", pid], capture_output=True, text=True, timeout=5).stdout
        return int(out.strip()) if out.strip() else None
    except Exception:
        return None

rec = {
    "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "server_rss_kb": rss_kb(pid),
    "vm_stat": vm_stat(),
}
with open(log_path, "a", encoding="utf-8") as fh:
    fh.write(json.dumps(rec, separators=(",", ":")) + "\n")
    fh.flush()
    os.fsync(fh.fileno())
PY
    sleep "$HEARTBEAT_S"
  done
}
heartbeat_loop &
HEARTBEAT_PID=$!

cleanup() {
  kill "$SERVER_PID" 2>/dev/null || true
  kill "$HEARTBEAT_PID" 2>/dev/null || true
}
trap cleanup INT TERM EXIT

echo "mlx-server-run.sh: model=$MODEL port=$PORT pid=$SERVER_PID"
echo "  server log:    $SERVER_LOG"
echo "  heartbeat log: $HEARTBEAT_LOG"
echo "  info file:     $INFO_FILE"

wait "$SERVER_PID"
