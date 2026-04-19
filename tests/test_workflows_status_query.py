"""Unit tests for workflows_status_query.py — REST + SQLite fallback + formatters.

These tests exercise the SQLite path via a synthetic in-memory schema, and the
REST path by monkey-patching urlopen. Real Archon server behaviour is covered
by integration tests (workforce-smoke).
"""
from __future__ import annotations

import io
import json
import sqlite3
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent.parent / "plugins" / "sdlc-workflows" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import workflows_status_query as wsq  # noqa: E402


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------


def test_format_table_empty():
    assert "no workflow runs" in wsq.format_table([])


def test_format_table_renders_columns():
    runs = [
        {
            "id": "abc123deadbeef",
            "workflow_name": "parallel-review",
            "status": "running",
            "current_step_index": 2,
            "started_at": "2026-04-19 12:34:56",
        }
    ]
    out = wsq.format_table(runs)
    assert "abc123de" in out
    assert "parallel-review" in out
    assert "running" in out
    assert "2026-04-19 12:34:56" in out


def test_format_run_detail_includes_events():
    run = {
        "id": "r1",
        "workflow_name": "wf",
        "status": "completed",
        "started_at": "2026-04-19",
        "completed_at": "2026-04-19",
        "working_path": "/tmp/x",
        "events": [
            {
                "event_type": "node_started",
                "step_name": "impl",
                "created_at": "2026-04-19 12:00:00",
            },
            {
                "event_type": "node_completed",
                "step_name": "impl",
                "created_at": "2026-04-19 12:01:00",
            },
        ],
    }
    out = wsq.format_run_detail(run)
    assert "Workflow: wf" in out
    assert "[impl] node_started" in out
    assert "[impl] node_completed" in out


def test_short_truncates():
    assert wsq._short("abcdef1234567890") == "abcdef12"
    assert wsq._short(None) == ""


# ---------------------------------------------------------------------------
# SQLite path
# ---------------------------------------------------------------------------


def _build_test_db(tmp_path: Path) -> Path:
    """Create a minimal Archon-schema-compatible SQLite DB for testing."""
    db = tmp_path / "archon.db"
    conn = sqlite3.connect(db)
    conn.executescript(
        """
        CREATE TABLE remote_agent_workflow_runs (
            id TEXT PRIMARY KEY,
            conversation_id TEXT,
            codebase_id TEXT,
            workflow_name TEXT,
            user_message TEXT,
            status TEXT,
            current_step_index INTEGER,
            metadata TEXT,
            parent_conversation_id TEXT,
            started_at TEXT,
            completed_at TEXT,
            last_activity_at TEXT,
            working_path TEXT
        );
        CREATE TABLE remote_agent_workflow_events (
            id TEXT PRIMARY KEY,
            workflow_run_id TEXT,
            event_type TEXT,
            step_index INTEGER,
            step_name TEXT,
            data TEXT,
            created_at TEXT
        );
        INSERT INTO remote_agent_workflow_runs
            (id, conversation_id, workflow_name, user_message, status,
             current_step_index, started_at, last_activity_at)
        VALUES
            ('run-a', 'conv-1', 'wf-a', '', 'completed', 3,
             '2026-04-19 12:00:00', '2026-04-19 12:05:00'),
            ('run-b', 'conv-2', 'wf-b', '', 'running',   1,
             '2026-04-19 12:10:00', '2026-04-19 12:11:00'),
            ('run-c', 'conv-3', 'wf-a', '', 'completed', 2,
             '2026-04-18 09:00:00', '2026-04-18 09:04:00'),
            ('abcd1234deadbeefcafe5678feedface', 'conv-4', 'wf-a', '',
             'completed', 4, '2026-04-19 13:00:00', '2026-04-19 13:10:00');
        INSERT INTO remote_agent_workflow_events
            (id, workflow_run_id, event_type, step_index, step_name, created_at)
        VALUES
            ('e1', 'run-a', 'node_started',   0, 'impl',   '2026-04-19 12:00:10'),
            ('e2', 'run-a', 'node_completed', 0, 'impl',   '2026-04-19 12:03:00'),
            ('e3', 'run-a', 'node_started',   1, 'review', '2026-04-19 12:03:10');
        """
    )
    conn.commit()
    conn.close()
    return db


def test_sqlite_fetch_all_sorted_by_started(tmp_path, monkeypatch):
    db = _build_test_db(tmp_path)
    monkeypatch.setattr(wsq, "ARCHON_DB_PATH", db)
    runs = wsq.fetch_via_sqlite(running_only=False, limit=None)
    ids = [r["id"] for r in runs]
    # The 'abcd…' row has started_at '2026-04-19 13:00:00', newest.
    assert ids == [
        "abcd1234deadbeefcafe5678feedface",
        "run-b",
        "run-a",
        "run-c",
    ]


def test_sqlite_running_only_filters(tmp_path, monkeypatch):
    db = _build_test_db(tmp_path)
    monkeypatch.setattr(wsq, "ARCHON_DB_PATH", db)
    runs = wsq.fetch_via_sqlite(running_only=True, limit=None)
    assert [r["id"] for r in runs] == ["run-b"]


def test_sqlite_limit_applies(tmp_path, monkeypatch):
    db = _build_test_db(tmp_path)
    monkeypatch.setattr(wsq, "ARCHON_DB_PATH", db)
    runs = wsq.fetch_via_sqlite(running_only=False, limit=2)
    assert len(runs) == 2
    assert runs[0]["id"] == "abcd1234deadbeefcafe5678feedface"


def test_sqlite_run_detail_includes_events(tmp_path, monkeypatch):
    db = _build_test_db(tmp_path)
    monkeypatch.setattr(wsq, "ARCHON_DB_PATH", db)
    detail = wsq.fetch_run_detail_via_sqlite("run-a")
    assert detail is not None
    assert detail["workflow_name"] == "wf-a"
    assert len(detail["events"]) == 3
    assert detail["events"][0]["event_type"] == "node_started"


def test_sqlite_missing_db_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(wsq, "ARCHON_DB_PATH", tmp_path / "does-not-exist.db")
    assert wsq.fetch_via_sqlite(running_only=False, limit=None) == []
    assert wsq.fetch_run_detail_via_sqlite("x") is None


def test_sqlite_unknown_run_returns_none(tmp_path, monkeypatch):
    db = _build_test_db(tmp_path)
    monkeypatch.setattr(wsq, "ARCHON_DB_PATH", db)
    assert wsq.fetch_run_detail_via_sqlite("nonexistent") is None


def test_resolve_run_id_prefix_unique_match(tmp_path, monkeypatch):
    # The fixture has a 32-char hex id 'abcd1234deadbeefcafe5678feedface'.
    # An 8-char prefix 'abcd1234' uniquely matches it — the common case:
    # user sees 8-char id in --recent and wants to paste into --run-id.
    db = _build_test_db(tmp_path)
    monkeypatch.setattr(wsq, "ARCHON_DB_PATH", db)
    full_id, err = wsq.resolve_run_id_prefix("abcd1234")
    assert err is None
    assert full_id == "abcd1234deadbeefcafe5678feedface"


def test_resolve_run_id_prefix_ambiguous(tmp_path, monkeypatch):
    # Prefix 'run-' matches run-a, run-b, run-c.
    db = _build_test_db(tmp_path)
    monkeypatch.setattr(wsq, "ARCHON_DB_PATH", db)
    full_id, err = wsq.resolve_run_id_prefix("run-")
    assert full_id is None
    assert err is not None
    assert "ambiguous" in err.lower() or "matches" in err.lower()


def test_resolve_run_id_prefix_no_match(tmp_path, monkeypatch):
    db = _build_test_db(tmp_path)
    monkeypatch.setattr(wsq, "ARCHON_DB_PATH", db)
    full_id, err = wsq.resolve_run_id_prefix("zzz")
    assert full_id is None
    assert err is not None


def test_main_run_id_prefix_resolves_to_full_id(tmp_path, monkeypatch, capsys):
    # Integration: --run-id with a prefix argument should resolve to a
    # full id before fetching detail. Without prefix resolution main()
    # would print "Run nope not found" and exit 1; with it, main() must
    # find 'run-a' from the 5-char prefix 'run-a' and print detail.
    db = _build_test_db(tmp_path)
    monkeypatch.setattr(wsq, "ARCHON_DB_PATH", db)
    monkeypatch.setattr(sys, "argv", ["prog", "--run-id", "run-a", "--no-rest"])
    rc = wsq.main()
    assert rc == 0
    out = capsys.readouterr().out
    assert "run-a" in out
    assert "node_started" in out


# ---------------------------------------------------------------------------
# REST path
# ---------------------------------------------------------------------------


class _FakeResp:
    def __init__(self, status: int, body: bytes):
        self.status = status
        self._body = body

    def read(self) -> bytes:
        return self._body


def test_rest_fetch_list(monkeypatch):
    payload = json.dumps([{"id": "r1", "workflow_name": "x", "status": "running"}])
    with patch.object(
        wsq.urllib.request,
        "urlopen",
        return_value=_FakeResp(200, payload.encode()),
    ):
        runs = wsq.fetch_via_rest("http://localhost:3090", timeout=1.0)
    assert runs == [{"id": "r1", "workflow_name": "x", "status": "running"}]


def test_rest_fetch_list_wrapped_in_runs_key(monkeypatch):
    payload = json.dumps({"runs": [{"id": "r1"}]})
    with patch.object(
        wsq.urllib.request,
        "urlopen",
        return_value=_FakeResp(200, payload.encode()),
    ):
        runs = wsq.fetch_via_rest("http://localhost:3090", timeout=1.0)
    assert runs == [{"id": "r1"}]


def test_rest_fetch_unreachable_returns_none():
    import urllib.error

    with patch.object(
        wsq.urllib.request,
        "urlopen",
        side_effect=urllib.error.URLError("connection refused"),
    ):
        assert wsq.fetch_via_rest("http://localhost:3090", timeout=0.1) is None


def test_rest_fetch_5xx_raises():
    with patch.object(
        wsq.urllib.request,
        "urlopen",
        return_value=_FakeResp(503, b""),
    ):
        with pytest.raises(RuntimeError, match="server error"):
            wsq.fetch_via_rest("http://localhost:3090", timeout=1.0)


def test_rest_run_detail(monkeypatch):
    payload = json.dumps({"id": "r1", "workflow_name": "x", "status": "running", "events": []})
    with patch.object(
        wsq.urllib.request,
        "urlopen",
        return_value=_FakeResp(200, payload.encode()),
    ):
        detail = wsq.fetch_run_detail_via_rest(
            "http://localhost:3090", "r1", timeout=1.0
        )
    assert detail["id"] == "r1"


def test_rest_run_detail_wrapped_in_run_key(monkeypatch):
    # Real Archon API shape: {"run": {...}, "events": [...]}. The script must
    # unwrap so format_run_detail sees a flat dict with events merged in.
    payload = json.dumps(
        {
            "run": {
                "id": "r2",
                "workflow_name": "feature-pipeline",
                "status": "completed",
                "started_at": "2026-04-19 23:29:01",
                "completed_at": "2026-04-19 23:30:37",
                "working_path": "/tmp/ws",
            },
            "events": [
                {"event_type": "workflow_started", "created_at": "2026-04-19 23:29:01"},
                {"event_type": "node_started", "step_name": "implement", "created_at": "2026-04-19 23:29:01"},
            ],
        }
    )
    with patch.object(
        wsq.urllib.request,
        "urlopen",
        return_value=_FakeResp(200, payload.encode()),
    ):
        detail = wsq.fetch_run_detail_via_rest(
            "http://localhost:3090", "r2", timeout=1.0
        )
    assert detail is not None
    assert detail["id"] == "r2"
    assert detail["workflow_name"] == "feature-pipeline"
    assert detail["status"] == "completed"
    assert len(detail["events"]) == 2
    assert detail["events"][0]["event_type"] == "workflow_started"


# ---------------------------------------------------------------------------
# CLI entry: main() dispatches correctly
# ---------------------------------------------------------------------------


def test_main_json_output_running_only(tmp_path, monkeypatch, capsys):
    db = _build_test_db(tmp_path)
    monkeypatch.setattr(wsq, "ARCHON_DB_PATH", db)
    monkeypatch.setattr(sys, "argv", ["prog", "--running", "--json", "--no-rest"])
    rc = wsq.main()
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["source"] == "sqlite"
    assert len(data["runs"]) == 1
    assert data["runs"][0]["id"] == "run-b"


def test_main_table_output(tmp_path, monkeypatch, capsys):
    db = _build_test_db(tmp_path)
    monkeypatch.setattr(wsq, "ARCHON_DB_PATH", db)
    monkeypatch.setattr(sys, "argv", ["prog", "--recent", "10", "--no-rest"])
    rc = wsq.main()
    assert rc == 0
    out = capsys.readouterr().out
    assert "run-a" in out or "run-b" in out
    assert "RUN ID" in out


def test_main_run_id_not_found(tmp_path, monkeypatch, capsys):
    db = _build_test_db(tmp_path)
    monkeypatch.setattr(wsq, "ARCHON_DB_PATH", db)
    monkeypatch.setattr(sys, "argv", ["prog", "--run-id", "nope", "--no-rest"])
    rc = wsq.main()
    assert rc == 1
    err = capsys.readouterr().err
    assert "not found" in err


def test_main_run_id_detail(tmp_path, monkeypatch, capsys):
    db = _build_test_db(tmp_path)
    monkeypatch.setattr(wsq, "ARCHON_DB_PATH", db)
    monkeypatch.setattr(sys, "argv", ["prog", "--run-id", "run-a", "--no-rest"])
    rc = wsq.main()
    assert rc == 0
    out = capsys.readouterr().out
    assert "run-a" in out
    assert "node_started" in out


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
