#!/usr/bin/env bash
# mlx-panic-report.sh — after an unexplained reboot during a local MLX
# assessment run, answer "which model, which test condition". Reads the
# durable breadcrumb trails written by mlx-chat (Path B) and
# mlx-stop-proxy.py (Path A), the mlx-server-run.sh heartbeat/server logs,
# and macOS's own panic diagnostic reports, then prints the most recent
# in-flight request from each source plus the newest panic report on disk
# for manual timestamp correlation. Read-only — never deletes anything.
#
# Usage: mlx-panic-report.sh [--breadcrumb PATH] [--server-log-dir DIR]
set -u

BREADCRUMB="${MLX_CHAT_BREADCRUMB:-$HOME/.sdlc/model-council/mlx-chat-panic-breadcrumb.jsonl}"
STOP_PROXY_BREADCRUMB="$HOME/.sdlc/model-council/mlx-stop-proxy-panic-breadcrumb.jsonl"
SERVER_LOG_DIR=""
RUN_CWD="$(pwd -P)"
[ -n "$SERVER_LOG_DIR" ] || SERVER_LOG_DIR="$RUN_CWD/tmp/model-council/mlx-server"

while [ $# -gt 0 ]; do
  case "$1" in
    --breadcrumb) BREADCRUMB="$2"; shift 2 ;;
    --server-log-dir) SERVER_LOG_DIR="$2"; shift 2 ;;
    *) echo "mlx-panic-report.sh: unknown option: $1" >&2; exit 1 ;;
  esac
done

section() { printf '\n=== %s ===\n' "$1"; }

last_inflight() { # last_inflight <breadcrumb-file> <label>
  local f="$1" label="$2"
  if [ ! -f "$f" ]; then
    echo "  (no breadcrumb file at $f — this path was never instrumented/run here)"
    return
  fi
  python3 - "$f" <<'PY'
import json, sys
path = sys.argv[1]
by_req = {}
order = []
for line in open(path, encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    try:
        rec = json.loads(line)
    except Exception:
        continue
    rid = rec.get("req_id")
    if rid is None:
        continue
    if rid not in by_req:
        order.append(rid)
    by_req[rid] = rec  # last event per req_id wins (START gets overwritten by WAITING/DONE)

TERMINAL = {"REQUEST_DONE", "REQUEST_HTTP_ERROR", "REQUEST_UNREACHABLE",
            "REQUEST_BAD_RESPONSE", "REQUEST_WRITE_ERROR"}
inflight = [by_req[rid] for rid in order if by_req[rid].get("event") not in TERMINAL]
if not inflight:
    print("  no in-flight (unterminated) request found — last run exited cleanly")
else:
    inflight.sort(key=lambda r: r.get("ts", ""))
    victim = inflight[-1]
    print("  SUSPECT (never reached a terminal event):")
    for k in ("ts", "event", "model", "history_dir", "path", "fingerprint", "waited_s", "req_id"):
        if k in victim and victim[k] not in (None, ""):
            print("    %s: %s" % (k, victim[k]))
    if len(inflight) > 1:
        print("  (%d other unterminated requests also present — file may be from multiple runs)" % (len(inflight) - 1))
PY
}

section "Path B (mlx-chat) breadcrumbs — $BREADCRUMB"
last_inflight "$BREADCRUMB" "mlx-chat"

section "Path A (mlx-stop-proxy) breadcrumbs — $STOP_PROXY_BREADCRUMB"
last_inflight "$STOP_PROXY_BREADCRUMB" "mlx-stop-proxy"

section "assess.sh orchestrator breadcrumbs (if assess.sh was the driver)"
LATEST_RUN_PTR="$RUN_CWD/tmp/model-council/latest-run.txt"
if [ -f "$LATEST_RUN_PTR" ]; then
  RUN_DIR="$(cat "$LATEST_RUN_PTR")"
  echo "  latest run dir: $RUN_DIR"
  if [ -f "$RUN_DIR/panic-breadcrumb.jsonl" ]; then
    last_inflight "$RUN_DIR/panic-breadcrumb.jsonl" "assess.sh"
  else
    echo "  (no panic-breadcrumb.jsonl in that run dir)"
  fi
  if ls "$RUN_DIR"/active/*.pair >/dev/null 2>&1; then
    echo "  STALE active/*.pair files still present (dispatch that never reached a terminal status):"
    for pf in "$RUN_DIR"/active/*.pair; do
      echo "    $(basename "$pf"): $(cat "$pf")"
    done
  fi
else
  echo "  (no $LATEST_RUN_PTR — assess.sh has not been run from this cwd)"
fi

section "mlx_lm.server resource heartbeat (tail of most recent log)"
if [ -d "$SERVER_LOG_DIR" ]; then
  LATEST_HB="$(ls -t "$SERVER_LOG_DIR"/*.heartbeat.jsonl 2>/dev/null | head -1)"
  LATEST_SRVLOG="$(ls -t "$SERVER_LOG_DIR"/*.server.log 2>/dev/null | head -1)"
  if [ -n "$LATEST_HB" ]; then
    echo "  $LATEST_HB (last 5 samples — watch server_rss_kb / Pages free for a squeeze):"
    tail -5 "$LATEST_HB" | sed 's/^/    /'
  else
    echo "  (no heartbeat log found under $SERVER_LOG_DIR — server wasn't started via mlx-server-run.sh)"
  fi
  if [ -n "$LATEST_SRVLOG" ]; then
    echo "  $LATEST_SRVLOG (last 10 lines):"
    tail -10 "$LATEST_SRVLOG" | sed 's/^/    /'
  fi
else
  echo "  (no $SERVER_LOG_DIR directory)"
fi

section "macOS panic / crash reports (for timestamp correlation with the SUSPECT above)"
FOUND=0
for dir in /Library/Logs/DiagnosticReports ~/Library/Logs/DiagnosticReports; do
  [ -d "$dir" ] || continue
  RECENT="$(ls -t "$dir" 2>/dev/null | grep -iE 'panic|kernel' | head -3)"
  if [ -n "$RECENT" ]; then
    FOUND=1
    echo "  $dir:"
    while IFS= read -r fname; do
      [ -n "$fname" ] || continue
      echo "    $fname"
      python3 - "$dir/$fname" <<'PY' 2>/dev/null
import json, sys
path = sys.argv[1]
try:
    with open(path, encoding="utf-8", errors="replace") as fh:
        fh.readline()          # small preamble line: bug_type/timestamp/os_version
        rest = fh.read()
    # The main object is often followed by trailing non-JSON sections in
    # these reports; raw_decode() parses just the leading object and
    # ignores whatever comes after it instead of erroring on "Extra data".
    d, _ = json.JSONDecoder().raw_decode(rest)
    ts = d.get("timestamp") or d.get("date")
    reason = (d.get("panicString") or "").splitlines()[0]
    if ts:
        print("      timestamp: %s" % ts)
    if reason:
        print("      reason:    %s" % reason)
except Exception:
    pass
PY
    done <<EOF_LIST
$RECENT
EOF_LIST
  fi
done
if [ "$FOUND" -eq 0 ]; then
  echo "  no panic/kernel report found in DiagnosticReports (may require sudo, or the panic log"
  echo "  hasn't been written back from NVRAM yet — try again after the machine has been up a"
  echo "  few minutes, or check: nvram -p | grep -i panic"
fi
