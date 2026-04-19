#!/usr/bin/env python3
"""Follow the Archon dashboard SSE stream and pretty-print workflow events.

Usage:
    python3 sse_stream_follow.py [--url http://localhost:3090] [--run-id <id>]

When `--run-id` is omitted, subscribes to /api/stream/__dashboard__ and shows
every run's events. When provided, subscribes to /api/stream/{runId} for a
single run's event stream.

This helper requires `archon serve` to be running (default port 3090). It is
NOT used by the default `archon workflow run` path — that CLI emits events to
stderr directly. Use this helper when you want structured monitoring (e.g.
feeding a Prometheus exporter) or when you launched workflows through the
server HTTP API and want a terminal view.

Events are printed one per line in a compact human-readable form. Parse the
raw JSON (available with --json) for programmatic consumers.

Exit codes:
    0 — clean disconnect (Ctrl-C)
    1 — network / parse error
    2 — server returned non-2xx
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime


def format_timestamp(ms: int | None) -> str:
    if ms is None:
        return "            "
    return datetime.fromtimestamp(ms / 1000).strftime("%H:%M:%S.%f")[:12]


def format_event(raw: str) -> str | None:
    """Return a one-line human summary, or None to skip (e.g. heartbeats)."""
    try:
        ev = json.loads(raw)
    except json.JSONDecodeError:
        return f"  ?? malformed JSON: {raw[:200]}"

    ev_type = ev.get("type", "?")
    ts = format_timestamp(ev.get("timestamp"))
    run = ev.get("runId", "")
    run_short = run[:8] if run else "--------"

    if ev_type == "heartbeat":
        return None

    if ev_type == "dag_node":
        status = ev.get("status", "?")
        name = ev.get("name", ev.get("nodeId", "?"))
        dur = ev.get("duration")
        dur_s = f" ({dur:.1f}s)" if isinstance(dur, (int, float)) else ""
        err = ev.get("error")
        err_s = f" — {err}" if err else ""
        return f"{ts} [{run_short}] node {name} {status}{dur_s}{err_s}"

    if ev_type == "workflow_step":
        name = ev.get("name", "?")
        status = ev.get("status", "?")
        return f"{ts} [{run_short}] step {name} {status}"

    if ev_type == "workflow_status":
        status = ev.get("status", "?")
        wf = ev.get("workflowName", "?")
        approval = ev.get("approval")
        apr = f" approval={approval.get('nodeId', '?')}" if approval else ""
        return f"{ts} [{run_short}] workflow {wf} {status}{apr}"

    if ev_type == "workflow_tool_activity":
        tool = ev.get("toolName", "?")
        step = ev.get("stepName", "?")
        status = ev.get("status", "?")
        dur_ms = ev.get("durationMs")
        dur_s = f" ({dur_ms}ms)" if dur_ms else ""
        return f"{ts} [{run_short}] tool {step}:{tool} {status}{dur_s}"

    if ev_type == "workflow_artifact":
        label = ev.get("label", "?")
        path = ev.get("path") or ev.get("url") or ""
        return f"{ts} [{run_short}] artifact {label} {path}"

    return f"{ts} [{run_short}] {ev_type} {raw[:120]}"


def follow(url: str, emit_json: bool) -> int:
    """Stream Server-Sent Events from url; print summaries until disconnect."""
    req = urllib.request.Request(url, headers={"Accept": "text/event-stream"})
    try:
        resp = urllib.request.urlopen(req, timeout=None)
    except urllib.error.HTTPError as e:
        print(f"ERROR: {url} returned HTTP {e.code}", file=sys.stderr)
        return 2
    except urllib.error.URLError as e:
        print(f"ERROR: cannot reach {url}: {e.reason}", file=sys.stderr)
        print("Is `archon serve` running on the target host?", file=sys.stderr)
        return 1

    if resp.status >= 300:
        print(f"ERROR: {url} returned HTTP {resp.status}", file=sys.stderr)
        return 2

    print(f"Connected to {url}", file=sys.stderr)
    try:
        for line_bytes in resp:
            line = line_bytes.decode("utf-8", errors="replace").rstrip("\n")
            if not line.startswith("data: "):
                continue
            data = line[len("data: ") :]
            if emit_json:
                print(data, flush=True)
                continue
            summary = format_event(data)
            if summary is not None:
                print(summary, flush=True)
    except KeyboardInterrupt:
        return 0
    except OSError as e:
        print(f"ERROR: stream read failed: {e}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument(
        "--url",
        default="http://localhost:3090",
        help="Archon server base URL (default: http://localhost:3090)",
    )
    p.add_argument(
        "--run-id",
        help="Subscribe to a specific run's stream; default is the multiplexed dashboard",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Emit raw event JSON (one per line) instead of human summaries",
    )
    args = p.parse_args()

    base = args.url.rstrip("/")
    endpoint = f"/api/stream/{args.run_id}" if args.run_id else "/api/stream/__dashboard__"
    return follow(base + endpoint, args.json)


if __name__ == "__main__":
    sys.exit(main())
