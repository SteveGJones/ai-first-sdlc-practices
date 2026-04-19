#!/usr/bin/env python3
"""Query workflow run status from Archon — REST API first, SQLite fallback.

The `archon` CLI offers only `archon workflow status` (active runs only) and
`archon workflow list` (available workflows, not runs). Neither shows a
historical list of runs with their per-node status, which is what
`/sdlc-workflows:workflows-status --recent` promises. This script fills that
gap by going to the two real sources:

1. `GET /api/workflows/runs` on `archon serve` — richest source (joined run
   + event data, formatted exactly like the web UI). Used when reachable.
2. `~/.archon/archon.db` (SQLite) — direct read of the `remote_agent_workflow_runs`
   and `remote_agent_workflow_events` tables. Used when the HTTP server is not
   running. Read-only: no writes, no schema assumptions beyond columns present
   in this repo's Archon pin.

Output modes:
- Default: human-readable table.
- `--json`: one JSON object per line (runs + inline node events).

Filters (mutually exclusive):
- `--running` — only status='running'.
- `--recent N` — latest N by started_at (default 20).
- `--run-id <id>` — full detail for one run, including per-node events.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import urllib.error
import urllib.request
from pathlib import Path


ARCHON_DEFAULT_URL = "http://localhost:3090"
ARCHON_DB_PATH = Path(os.environ.get("ARCHON_HOME", Path.home() / ".archon")) / "archon.db"


# ---------------------------------------------------------------------------
# REST API path
# ---------------------------------------------------------------------------


def _http_get_json(url: str, timeout: float) -> object | None:
    """Return parsed JSON from url, or None if the server is not reachable.

    Raises for HTTP 5xx (genuine server error) but silently returns None for
    connection failure — that's the signal to fall back to SQLite.
    """
    try:
        resp = urllib.request.urlopen(url, timeout=timeout)
    except urllib.error.URLError:
        return None
    if resp.status >= 500:
        raise RuntimeError(f"Archon server error: {resp.status} from {url}")
    if resp.status >= 400:
        return None
    return json.loads(resp.read().decode("utf-8"))


def fetch_via_rest(base_url: str, timeout: float) -> list[dict] | None:
    """Fetch all runs via REST; return None if the server is unreachable."""
    data = _http_get_json(base_url.rstrip("/") + "/api/workflows/runs", timeout=timeout)
    if data is None:
        return None
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "runs" in data:
        return data["runs"]
    raise RuntimeError(f"Unexpected REST response shape from {base_url}: {type(data)!r}")


def fetch_run_detail_via_rest(
    base_url: str, run_id: str, timeout: float
) -> dict | None:
    """Fetch one run's detail via REST; None if unreachable.

    Normalises Archon's wrapped response shape (``{"run": {...}, "events":
    [...]}``) into a single flat dict with ``events`` merged in, matching the
    ``fetch_run_detail_via_sqlite`` contract expected by ``format_run_detail``.
    """
    url = f"{base_url.rstrip('/')}/api/workflows/runs/{run_id}"
    data = _http_get_json(url, timeout=timeout)
    if data is None:
        return None
    # Wrapper shape: {"run": {...}, "events": [...]}. Disambiguate from a
    # (hypothetical) flat payload that happens to contain a "run" field by
    # also checking that "id" is absent at the top level — format_run_detail
    # requires id at the top level, so this is the clean discriminator.
    if (
        isinstance(data, dict)
        and "run" in data
        and "id" not in data
        and isinstance(data["run"], dict)
    ):
        merged = dict(data["run"])
        merged["events"] = data.get("events", [])
        return merged
    return data  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# SQLite fallback path
# ---------------------------------------------------------------------------


def _open_db() -> sqlite3.Connection | None:
    if not ARCHON_DB_PATH.exists():
        return None
    # URI + mode=ro keeps this strictly read-only even if the DB lock slips.
    uri = f"file:{ARCHON_DB_PATH}?mode=ro"
    return sqlite3.connect(uri, uri=True, timeout=2.0)


def fetch_via_sqlite(running_only: bool, limit: int | None) -> list[dict]:
    conn = _open_db()
    if conn is None:
        return []
    try:
        conn.row_factory = sqlite3.Row
        where = "WHERE status = 'running'" if running_only else ""
        sql = f"""
            SELECT id, conversation_id, workflow_name, status,
                   current_step_index, started_at, completed_at,
                   last_activity_at, working_path
            FROM remote_agent_workflow_runs
            {where}
            ORDER BY started_at DESC
        """
        if limit is not None:
            sql += f" LIMIT {int(limit)}"
        rows = conn.execute(sql).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def fetch_run_detail_via_sqlite(run_id: str) -> dict | None:
    conn = _open_db()
    if conn is None:
        return None
    try:
        conn.row_factory = sqlite3.Row
        run = conn.execute(
            """SELECT id, conversation_id, workflow_name, status,
                      current_step_index, started_at, completed_at,
                      last_activity_at, working_path
               FROM remote_agent_workflow_runs WHERE id = ?""",
            (run_id,),
        ).fetchone()
        if run is None:
            return None
        events = conn.execute(
            """SELECT event_type, step_index, step_name, data, created_at
               FROM remote_agent_workflow_events
               WHERE workflow_run_id = ?
               ORDER BY created_at ASC""",
            (run_id,),
        ).fetchall()
        result = dict(run)
        result["events"] = [dict(e) for e in events]
        return result
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------


def _short(val: str | None, n: int = 8) -> str:
    if not val:
        return ""
    return val[:n]


def format_table(runs: list[dict]) -> str:
    if not runs:
        return "(no workflow runs found)"
    header = f"{'RUN ID':<10} {'WORKFLOW':<30} {'STATUS':<12} {'STARTED':<20} {'STEP':<5}"
    lines = [header, "-" * len(header)]
    for r in runs:
        lines.append(
            f"{_short(r.get('id')):<10} "
            f"{(r.get('workflow_name') or '')[:30]:<30} "
            f"{(r.get('status') or ''):<12} "
            f"{(r.get('started_at') or '')[:19]:<20} "
            f"{str(r.get('current_step_index') if r.get('current_step_index') is not None else ''):<5}"
        )
    return "\n".join(lines)


def format_run_detail(run: dict) -> str:
    out: list[str] = []
    out.append(f"Run:      {run.get('id')}")
    out.append(f"Workflow: {run.get('workflow_name')}")
    out.append(f"Status:   {run.get('status')}")
    out.append(f"Started:  {run.get('started_at')}")
    if run.get("completed_at"):
        out.append(f"Ended:    {run['completed_at']}")
    if run.get("working_path"):
        out.append(f"Workdir:  {run['working_path']}")
    out.append("")
    out.append("Events:")
    for e in run.get("events", []):
        out.append(
            f"  {e.get('created_at', '')[:19]} "
            f"[{e.get('step_name') or e.get('step_index') or '-'}] "
            f"{e.get('event_type')}"
        )
    return "\n".join(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    group = p.add_mutually_exclusive_group()
    group.add_argument("--running", action="store_true", help="Only active runs")
    group.add_argument("--recent", type=int, metavar="N", help="Latest N runs (default 20)")
    group.add_argument("--run-id", help="Detail for one run")
    p.add_argument(
        "--url",
        default=ARCHON_DEFAULT_URL,
        help=f"Archon server base URL (default: {ARCHON_DEFAULT_URL})",
    )
    p.add_argument(
        "--no-rest", action="store_true", help="Skip REST API; go straight to SQLite"
    )
    p.add_argument("--json", action="store_true", help="Emit JSON instead of a table")
    p.add_argument(
        "--timeout",
        type=float,
        default=1.0,
        help="REST API timeout in seconds before falling back to SQLite (default 1.0)",
    )
    args = p.parse_args()

    # Single-run detail path.
    if args.run_id:
        detail = None
        source = "sqlite"
        if not args.no_rest:
            detail = fetch_run_detail_via_rest(args.url, args.run_id, args.timeout)
            if detail is not None:
                source = "rest"
        if detail is None:
            detail = fetch_run_detail_via_sqlite(args.run_id)
        if detail is None:
            print(f"Run {args.run_id} not found.", file=sys.stderr)
            return 1
        if args.json:
            print(json.dumps({"source": source, "run": detail}, indent=2, default=str))
        else:
            print(f"Source: {source}")
            print(format_run_detail(detail))
        return 0

    # List path.
    running_only = args.running
    limit = args.recent if args.recent is not None else (None if running_only else 20)

    runs: list[dict] | None = None
    source = "sqlite"
    if not args.no_rest:
        try:
            runs = fetch_via_rest(args.url, args.timeout)
        except RuntimeError as e:
            print(f"WARNING: {e}", file=sys.stderr)
            runs = None
        if runs is not None:
            source = "rest"
            # REST returns everything; apply local filters for parity.
            if running_only:
                runs = [r for r in runs if r.get("status") == "running"]
            if limit is not None:
                # REST payload is usually newest-first but don't assume.
                runs.sort(key=lambda r: r.get("started_at", ""), reverse=True)
                runs = runs[:limit]
    if runs is None:
        runs = fetch_via_sqlite(running_only=running_only, limit=limit)

    if args.json:
        print(json.dumps({"source": source, "runs": runs}, indent=2, default=str))
    else:
        print(f"Source: {source}  ({'archon serve' if source == 'rest' else str(ARCHON_DB_PATH)})")
        print(format_table(runs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
