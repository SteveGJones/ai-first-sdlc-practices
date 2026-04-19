"""Unit tests for the SSE event formatter used by sse_stream_follow.py.

The network plumbing (urllib.request.urlopen, stream iteration) is not covered
here — it is exercised by the monitoring soak test. These tests pin the
one-line summary format so a Prometheus exporter or UI consumer can rely on
structured event type detection and common fields.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent.parent / "plugins" / "sdlc-workflows" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import sse_stream_follow  # noqa: E402


def fmt(event: dict) -> str | None:
    return sse_stream_follow.format_event(json.dumps(event))


def test_heartbeat_is_skipped():
    assert fmt({"type": "heartbeat", "timestamp": 1700000000000}) is None


def test_dag_node_started_renders_status_and_name():
    line = fmt(
        {
            "type": "dag_node",
            "runId": "abcdef1234567890",
            "nodeId": "n1",
            "name": "review",
            "status": "running",
            "timestamp": 1700000000000,
        }
    )
    assert "[abcdef12]" in line
    assert "node review running" in line


def test_dag_node_completed_includes_duration():
    line = fmt(
        {
            "type": "dag_node",
            "runId": "r1",
            "name": "impl",
            "status": "completed",
            "duration": 12.5,
            "timestamp": 1700000000000,
        }
    )
    assert "node impl completed (12.5s)" in line


def test_dag_node_failed_includes_error():
    line = fmt(
        {
            "type": "dag_node",
            "runId": "r1",
            "name": "build",
            "status": "failed",
            "error": "exit 1",
            "timestamp": 1700000000000,
        }
    )
    assert "failed" in line
    assert "exit 1" in line


def test_workflow_status_cancelled():
    line = fmt(
        {
            "type": "workflow_status",
            "runId": "r1",
            "workflowName": "parallel-review",
            "status": "cancelled",
            "timestamp": 1700000000000,
        }
    )
    assert "workflow parallel-review cancelled" in line


def test_workflow_status_approval_carries_node_id():
    line = fmt(
        {
            "type": "workflow_status",
            "runId": "r1",
            "workflowName": "",
            "status": "paused",
            "approval": {"nodeId": "gate", "message": "please review"},
            "timestamp": 1700000000000,
        }
    )
    assert "approval=gate" in line


def test_workflow_step_iteration():
    line = fmt(
        {
            "type": "workflow_step",
            "runId": "r1",
            "name": "iteration-3",
            "status": "started",
            "timestamp": 1700000000000,
        }
    )
    assert "step iteration-3 started" in line


def test_tool_activity_includes_duration_when_completed():
    line = fmt(
        {
            "type": "workflow_tool_activity",
            "runId": "r1",
            "toolName": "Write",
            "stepName": "implement",
            "status": "completed",
            "durationMs": 123,
            "timestamp": 1700000000000,
        }
    )
    assert "tool implement:Write completed" in line
    assert "(123ms)" in line


def test_artifact_prints_path():
    line = fmt(
        {
            "type": "workflow_artifact",
            "runId": "r1",
            "label": "review.md",
            "path": "/workspace/reports/review.md",
            "timestamp": 1700000000000,
        }
    )
    assert "artifact review.md" in line
    assert "/workspace/reports/review.md" in line


def test_unknown_event_type_still_renders_truncated_payload():
    line = fmt(
        {
            "type": "future_event_type",
            "runId": "r1",
            "timestamp": 1700000000000,
            "payload": "x" * 300,
        }
    )
    assert "future_event_type" in line
    # Truncated to keep lines manageable.
    assert len(line) < 300


def test_malformed_json_returns_diagnostic_line():
    line = sse_stream_follow.format_event("this is not json")
    assert "malformed JSON" in line


def test_missing_timestamp_still_renders():
    line = fmt({"type": "dag_node", "runId": "r1", "name": "n", "status": "running"})
    assert "node n running" in line


def test_empty_run_id_produces_placeholder():
    line = fmt(
        {"type": "dag_node", "runId": "", "name": "n", "status": "running", "timestamp": 0}
    )
    assert "[--------]" in line


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
