"""Unit tests for sdlc_knowledge_base_scripts.audit."""
import json
from pathlib import Path
from sdlc_knowledge_base_scripts.audit import (
    AuditEvent,
    log_event,
    read_log,
)


def test_log_event_appends_jsonline(tmp_path: Path) -> None:
    log_path = tmp_path / "audit.log"
    event = AuditEvent(
        timestamp="2026-04-26T15:30:00Z",
        event_type="attribution_drop_retrieval",
        query="what about EUV",
        source_handle="corp-semi",
        reason="finding lacked Source library tag",
        detail={"dropped_block_titles": ["Bogus finding"]},
    )
    log_event(log_path, event)
    contents = log_path.read_text()
    line = contents.strip()
    parsed = json.loads(line)
    assert parsed["timestamp"] == "2026-04-26T15:30:00Z"
    assert parsed["event_type"] == "attribution_drop_retrieval"
    assert parsed["source_handle"] == "corp-semi"


def test_log_event_appends_multiple(tmp_path: Path) -> None:
    log_path = tmp_path / "audit.log"
    for i in range(3):
        log_event(log_path, AuditEvent(
            timestamp=f"2026-04-26T15:30:0{i}Z",
            event_type="attribution_drop_retrieval",
            query=f"q{i}",
            source_handle="local",
            reason="r",
            detail={},
        ))
    lines = log_path.read_text().strip().split("\n")
    assert len(lines) == 3


def test_read_log_filter_by_event_type(tmp_path: Path) -> None:
    log_path = tmp_path / "audit.log"
    log_event(log_path, AuditEvent("2026-04-26T15:30:00Z", "attribution_drop_retrieval", "q", "local", "r", {}))
    log_event(log_path, AuditEvent("2026-04-26T15:30:01Z", "synthesis_aborted_attribution", "q", None, "r", {}))
    log_event(log_path, AuditEvent("2026-04-26T15:30:02Z", "attribution_drop_retrieval", "q", "corp", "r", {}))
    drops = read_log(log_path, event_type="attribution_drop_retrieval")
    assert len(drops) == 2
    aborts = read_log(log_path, event_type="synthesis_aborted_attribution")
    assert len(aborts) == 1


def test_read_log_filter_by_source_handle(tmp_path: Path) -> None:
    log_path = tmp_path / "audit.log"
    log_event(log_path, AuditEvent("2026-04-26T15:30:00Z", "attribution_drop_retrieval", "q", "local", "r", {}))
    log_event(log_path, AuditEvent("2026-04-26T15:30:01Z", "attribution_drop_retrieval", "q", "corp", "r", {}))
    locals_ = read_log(log_path, source_handle="local")
    assert len(locals_) == 1
    corps = read_log(log_path, source_handle="corp")
    assert len(corps) == 1


def test_read_log_filter_by_date_range(tmp_path: Path) -> None:
    log_path = tmp_path / "audit.log"
    log_event(log_path, AuditEvent("2026-01-01T00:00:00Z", "attribution_drop_retrieval", "old", "local", "r", {}))
    log_event(log_path, AuditEvent("2026-04-26T00:00:00Z", "attribution_drop_retrieval", "new", "local", "r", {}))
    recent = read_log(log_path, since="2026-04-01T00:00:00Z")
    assert len(recent) == 1
    assert recent[0].query == "new"


def test_read_log_missing_file_returns_empty(tmp_path: Path) -> None:
    log_path = tmp_path / "missing.log"
    assert read_log(log_path) == []


def test_read_log_malformed_lines_skipped(tmp_path: Path) -> None:
    log_path = tmp_path / "audit.log"
    log_event(log_path, AuditEvent("2026-04-26T15:30:00Z", "attribution_drop_retrieval", "q", "local", "r", {}))
    with log_path.open("a") as f:
        f.write("this is not json\n")
    log_event(log_path, AuditEvent("2026-04-26T15:30:01Z", "attribution_drop_retrieval", "q", "local", "r", {}))
    events = read_log(log_path)
    assert len(events) == 2  # malformed line skipped


def test_log_event_truncates_long_query(tmp_path: Path) -> None:
    log_path = tmp_path / "audit.log"
    long_query = "x" * 600
    log_event(log_path, AuditEvent(
        timestamp="2026-04-26T15:30:00Z",
        event_type="attribution_drop_retrieval",
        query=long_query,
        source_handle="local",
        reason="r",
        detail={},
    ))
    line = log_path.read_text().strip()
    parsed = json.loads(line)
    assert len(parsed["query"]) <= 520  # 500 chars + "...[truncated]" = 514
    assert "[truncated]" in parsed["query"]
