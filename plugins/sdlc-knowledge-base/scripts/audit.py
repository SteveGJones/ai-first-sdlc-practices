"""Audit log for confidentiality-relevant events in cross-library kb-query.

Events written here are durable trails of: attribution drops, synthesis
aborts, dispatcher failures, no-evidence markers, and cross-library
promotions. The trail enables a consulting practice to answer questions
like "show me all attribution drops in the last 90 days" — questions
that today require re-running every query.

Phase D of EPIC #164 (sub-6, #172) — see spec §7.1 and the operational
maturity additions.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional


VALID_EVENT_TYPES = frozenset(
    {
        "attribution_drop_retrieval",
        "synthesis_aborted_attribution",
        "synthesis_aborted_dispatcher_error",
        "source_dispatch_failed",
        "no_evidence_marker",
        "cross_library_promotion",
    }
)


@dataclass
class AuditEvent:
    """One audit log entry. Append-only; never mutated after write."""

    timestamp: str  # ISO 8601 UTC
    event_type: str  # one of VALID_EVENT_TYPES
    query: str  # truncated to 500 chars at write
    source_handle: Optional[
        str
    ]  # the relevant library, or None for orchestrator-level events
    reason: str  # human-readable cause
    detail: dict  # event-type-specific extras


_QUERY_TRUNCATION = 500


def log_event(log_path: Path, event: AuditEvent) -> None:
    """Append an audit event to the log as a JSON line.

    Truncates the query to 500 chars to bound log size on
    pathological inputs. Creates the log file if missing.
    Does NOT lock — callers serialise writes themselves
    (kb-query is not concurrent within a single project).
    """
    record = asdict(event)
    if record["query"] and len(record["query"]) > _QUERY_TRUNCATION:
        record["query"] = record["query"][:_QUERY_TRUNCATION] + "...[truncated]"
    line = json.dumps(record, ensure_ascii=False, separators=(",", ":"))
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def read_log(
    log_path: Path,
    event_type: Optional[str] = None,
    source_handle: Optional[str] = None,
    since: Optional[str] = None,  # ISO 8601 timestamp
    until: Optional[str] = None,  # ISO 8601 timestamp
) -> list[AuditEvent]:
    """Read and filter the audit log.

    Returns matching events in append order (oldest first).
    Missing file returns []. Malformed lines are skipped.
    """
    if not log_path.exists():
        return []
    results: list[AuditEvent] = []
    with log_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            try:
                event = AuditEvent(**record)
            except TypeError:
                continue
            if event_type is not None and event.event_type != event_type:
                continue
            if source_handle is not None and event.source_handle != source_handle:
                continue
            if since is not None and event.timestamp < since:
                continue
            if until is not None and event.timestamp > until:
                continue
            results.append(event)
    return results
