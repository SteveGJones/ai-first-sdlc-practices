"""Integration tests: workflows_status_query.py end-to-end against a fixture SQLite DB.

These tests spin up a temporary ``archon.db`` that matches Archon 1.x's schema,
invoke the status-query script as a subprocess (how the skill actually calls
it), and assert observable output. They close the loop that the unit tests
leave open — the unit tests exercise individual functions with mocked data,
these prove the script end-to-end against a real sqlite file under an
isolated ``ARCHON_HOME``.

Paired with ``tests/integration/workforce-smoke/run-e2e.sh`` ``--monitoring``
block, which exercises the REST + ``archon serve`` paths that require the
archon CLI on PATH.
"""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "plugins/sdlc-workflows/scripts/workflows_status_query.py"

# Matches the Archon 1.x schema captured via
# `sqlite3 ~/.archon/archon.db ".schema remote_agent_workflow_runs"`
# on 2026-04-19. If Archon bumps the schema, this fixture must track it —
# that drift is exactly what the script's status banner is meant to surface.
SCHEMA_SQL = """
CREATE TABLE remote_agent_conversations (
    id TEXT PRIMARY KEY,
    platform_type TEXT NOT NULL,
    platform_conversation_id TEXT NOT NULL,
    ai_assistant_type TEXT DEFAULT 'claude',
    title TEXT,
    created_at TEXT,
    updated_at TEXT,
    last_activity_at TEXT,
    hidden INTEGER DEFAULT 0
);

CREATE TABLE remote_agent_workflow_runs (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    codebase_id TEXT,
    workflow_name TEXT NOT NULL,
    user_message TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    current_step_index INTEGER,
    metadata TEXT DEFAULT '{}',
    parent_conversation_id TEXT,
    started_at TEXT,
    completed_at TEXT,
    last_activity_at TEXT,
    working_path TEXT
);

CREATE TABLE remote_agent_workflow_events (
    id TEXT PRIMARY KEY,
    workflow_run_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    step_index INTEGER,
    step_name TEXT,
    data TEXT DEFAULT '{}',
    created_at TEXT
);
"""


@pytest.fixture
def archon_home(tmp_path: Path) -> Path:
    """Build an ``ARCHON_HOME`` with a seeded ``archon.db``.

    Rows chosen to exercise the realistic UX:
    - one ``completed`` (most common first-time user case — looking back at
      what ran),
    - one ``running`` (to confirm ``--running`` filters),
    - one ``failed`` (to confirm failed-run hinting),
    - each with a handful of events to make detail output meaningful.

    IDs share an 8-char prefix boundary (``aaaa0001`` vs ``aaaa0002``) so the
    prefix-matching tests have to paste more chars to disambiguate.
    """
    db_path = tmp_path / "archon.db"
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA_SQL)
        conn.execute(
            "INSERT INTO remote_agent_conversations (id, platform_type, "
            "platform_conversation_id) VALUES (?, 'cli', 'test-conv')",
            ("conv-1",),
        )
        # Completed run
        conn.execute(
            """INSERT INTO remote_agent_workflow_runs
               (id, conversation_id, workflow_name, user_message, status,
                started_at, completed_at, current_step_index, working_path)
               VALUES (?, 'conv-1', 'feature-pipeline', 'run it', 'completed',
                       '2026-04-19 12:00:00', '2026-04-19 12:05:00', 2, '/tmp/ws-1')""",
            ("aaaa0001ffffffffffffffffffffffff",),
        )
        # Running run — shares 8-char prefix 'aaaa0002' with failed below only if
        # we pick different prefixes. Make the ambiguity collision explicit
        # elsewhere; keep these unique.
        conn.execute(
            """INSERT INTO remote_agent_workflow_runs
               (id, conversation_id, workflow_name, user_message, status,
                started_at, current_step_index, working_path)
               VALUES (?, 'conv-1', 'parallel-review-pipeline', 'review', 'running',
                       '2026-04-19 13:00:00', 1, '/tmp/ws-2')""",
            ("bbbb0001ffffffffffffffffffffffff",),
        )
        # Failed run — for the failure-hint assertion
        conn.execute(
            """INSERT INTO remote_agent_workflow_runs
               (id, conversation_id, workflow_name, user_message, status,
                started_at, completed_at, current_step_index, working_path)
               VALUES (?, 'conv-1', 'feature-pipeline', 'try', 'failed',
                       '2026-04-19 14:00:00', '2026-04-19 14:02:00', 0, '/tmp/ws-3')""",
            ("cccc0001ffffffffffffffffffffffff",),
        )
        # Events for the completed run — two nodes, started + completed each
        for ev_id, run_id, etype, idx, name, ts in [
            ("e1", "aaaa0001ffffffffffffffffffffffff", "node_started", 0, "implement", "2026-04-19 12:00:05"),
            ("e2", "aaaa0001ffffffffffffffffffffffff", "node_completed", 0, "implement", "2026-04-19 12:02:00"),
            ("e3", "aaaa0001ffffffffffffffffffffffff", "node_started", 1, "review", "2026-04-19 12:02:10"),
            ("e4", "aaaa0001ffffffffffffffffffffffff", "node_completed", 1, "review", "2026-04-19 12:05:00"),
        ]:
            conn.execute(
                """INSERT INTO remote_agent_workflow_events
                   (id, workflow_run_id, event_type, step_index, step_name, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (ev_id, run_id, etype, idx, name, ts),
            )
        # Ambiguous prefix pair — two runs both starting with 'dupe1234'
        conn.execute(
            """INSERT INTO remote_agent_workflow_runs
               (id, conversation_id, workflow_name, user_message, status,
                started_at, current_step_index)
               VALUES (?, 'conv-1', 'wf-x', 'x', 'completed',
                       '2026-04-19 10:00:00', 0)""",
            ("dupe1234aaaaaaaaaaaaaaaaaaaaaaaa",),
        )
        conn.execute(
            """INSERT INTO remote_agent_workflow_runs
               (id, conversation_id, workflow_name, user_message, status,
                started_at, current_step_index)
               VALUES (?, 'conv-1', 'wf-y', 'y', 'completed',
                       '2026-04-19 10:30:00', 0)""",
            ("dupe1234bbbbbbbbbbbbbbbbbbbbbbbb",),
        )
        conn.commit()
    finally:
        conn.close()
    return tmp_path


def _run(archon_home: Path, *args: str) -> subprocess.CompletedProcess:
    """Invoke the status-query script with ARCHON_HOME isolated to the fixture."""
    env = {**os.environ, "ARCHON_HOME": str(archon_home)}
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--no-rest", *args],
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )


def test_recent_table_lists_seeded_runs(archon_home: Path) -> None:
    """`--recent 10` returns every seeded run with the expected columns.

    This is the default user-facing surface ("what ran recently?"). It also
    verifies the status banner reports SQLite as the source when `--no-rest`
    is set, which is the tier the documented CLAUDE-CONTEXT-workflows.md
    flow promises works "on a fresh machine with no server running".
    """
    r = _run(archon_home, "--recent", "10")
    assert r.returncode == 0, r.stderr
    assert "Source: sqlite" in r.stdout
    assert "feature-pipeline" in r.stdout
    assert "parallel-review-pipeline" in r.stdout
    assert "running" in r.stdout
    assert "completed" in r.stdout
    assert "failed" in r.stdout
    # Columns
    for col in ("RUN ID", "WORKFLOW", "STATUS", "STARTED", "STEP"):
        assert col in r.stdout


def test_recent_output_carries_b1_footer(archon_home: Path) -> None:
    """The --run-id footer hint (observability review B1) is always present."""
    r = _run(archon_home, "--recent", "5")
    assert r.returncode == 0, r.stderr
    assert "--run-id" in r.stdout
    assert "prefix" in r.stdout.lower()


def test_running_only_filters_to_active_runs(archon_home: Path) -> None:
    r = _run(archon_home, "--running")
    assert r.returncode == 0, r.stderr
    assert "parallel-review-pipeline" in r.stdout  # running
    # The completed and failed rows must not appear
    assert "completed" not in r.stdout.split("\n")[-3]  # footer mentions it? no
    # Be strict: only runs with status=running should be in the body rows.
    # The footer line is fixed text; drop it for the inclusion check.
    body = "\n".join(ln for ln in r.stdout.splitlines() if "feature-pipeline" in ln)
    assert body == ""  # feature-pipeline rows were completed/failed


def test_run_id_full_uuid_returns_detail_with_events(archon_home: Path) -> None:
    full_id = "aaaa0001ffffffffffffffffffffffff"
    r = _run(archon_home, "--run-id", full_id)
    assert r.returncode == 0, r.stderr
    assert f"Run:      {full_id}" in r.stdout
    assert "feature-pipeline" in r.stdout
    assert "Events:" in r.stdout
    # All four seeded events present, in order
    for event_name in ("[implement] node_started", "[implement] node_completed",
                       "[review] node_started", "[review] node_completed"):
        assert event_name in r.stdout


def test_run_id_prefix_resolves_uniquely(archon_home: Path) -> None:
    """8-char prefix (what --recent prints) resolves cleanly to the full run."""
    r = _run(archon_home, "--run-id", "aaaa0001")
    assert r.returncode == 0, r.stderr
    assert "aaaa0001ffffffffffffffffffffffff" in r.stdout
    assert "feature-pipeline" in r.stdout


def test_run_id_ambiguous_prefix_errors_clearly(archon_home: Path) -> None:
    """Ambiguous prefixes must not silently pick one — they must tell the user."""
    r = _run(archon_home, "--run-id", "dupe1234")
    assert r.returncode != 0
    assert "ambiguous" in (r.stderr + r.stdout).lower()


def test_run_id_unknown_prefix_reports_not_found(archon_home: Path) -> None:
    """Unknown prefix → non-zero exit + clear 'not found' message on stderr."""
    r = _run(archon_home, "--run-id", "zzzzzzzz")
    assert r.returncode != 0
    assert "not found" in (r.stderr + r.stdout).lower()


def test_json_output_is_valid_json_with_runs(archon_home: Path) -> None:
    """``--json`` emits ``{"source": ..., "runs": [...]}`` — the shape the
    Prometheus exporter follow-up depends on."""
    r = _run(archon_home, "--recent", "10", "--json")
    assert r.returncode == 0, r.stderr
    payload = json.loads(r.stdout)
    assert isinstance(payload, dict)
    assert payload["source"] == "sqlite"
    workflow_names = {row["workflow_name"] for row in payload["runs"]}
    assert "feature-pipeline" in workflow_names
    assert "parallel-review-pipeline" in workflow_names


def test_missing_db_reports_no_runs_cleanly(tmp_path: Path) -> None:
    """Fresh machine (no archon.db) — exit 0, no crash, empty-result message."""
    empty_home = tmp_path / "empty"
    empty_home.mkdir()
    env = {**os.environ, "ARCHON_HOME": str(empty_home)}
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--no-rest", "--recent", "5"],
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert r.returncode == 0, r.stderr
    assert "no workflow runs" in r.stdout.lower()


class TestSchemaProbe:
    """Schema probe — PRAGMA table_info guard against Archon migration drift."""

    def test_valid_schema_emits_no_warning(self, archon_home: Path) -> None:
        """Normal Archon schema → no schema warning on stderr."""
        r = _run(archon_home, "--recent", "5")
        assert r.returncode == 0
        assert "schema" not in r.stderr.lower()

    def test_missing_column_emits_warning(self, tmp_path: Path) -> None:
        """Drop a column from the runs table → script emits a diagnostic warning
        on stderr but does NOT crash — graceful degradation, not hard failure."""
        db_path = tmp_path / "archon.db"
        conn = sqlite3.connect(db_path)
        # Create a runs table missing 'working_path'
        conn.executescript("""
            CREATE TABLE remote_agent_workflow_runs (
                id TEXT PRIMARY KEY,
                conversation_id TEXT,
                workflow_name TEXT,
                status TEXT,
                current_step_index INTEGER,
                started_at TEXT,
                completed_at TEXT,
                last_activity_at TEXT
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
        """)
        conn.close()
        r = _run(tmp_path, "--recent", "5")
        # Must be our diagnostic, not a raw traceback
        assert r.returncode == 0, f"should not crash: {r.stderr}"
        assert "schema" in r.stderr.lower()
        assert "working_path" in r.stderr.lower()
        assert "Traceback" not in r.stderr

    def test_missing_table_emits_warning(self, tmp_path: Path) -> None:
        """Database exists but table is entirely absent → diagnostic, not crash."""
        db_path = tmp_path / "archon.db"
        conn = sqlite3.connect(db_path)
        # Only create the events table
        conn.executescript("""
            CREATE TABLE remote_agent_workflow_events (
                id TEXT PRIMARY KEY,
                workflow_run_id TEXT,
                event_type TEXT,
                step_index INTEGER,
                step_name TEXT,
                data TEXT,
                created_at TEXT
            );
        """)
        conn.close()
        r = _run(tmp_path, "--recent", "5")
        # Must be our diagnostic, not a raw crash
        assert r.returncode == 0, f"should not crash: {r.stderr}"
        assert "remote_agent_workflow_runs" in r.stderr
        assert "Traceback" not in r.stderr
