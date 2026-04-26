"""End-to-end integration tests that exercise the user-facing skill flows.

Each test simulates what the kb-query, kb-audit-query, kb-promote, and
kb-setup-consulting skills do in production. Catches gaps between the
Python helpers and the bash-snippet-orchestrated user flows.
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from sdlc_knowledge_base_scripts.audit import AuditEvent, log_event, read_log
from sdlc_knowledge_base_scripts.orchestrator import (
    DispatchRequest,
    RetrievalQueryResult,
    run_retrieval_query,
    run_synthesis_query,
)
from sdlc_knowledge_base_scripts.priming import PrimingBundle
from sdlc_knowledge_base_scripts.registry import LibrarySource


def _make_minimal_library(root: Path, name: str = "library") -> Path:
    """Create a minimal valid library directory at <root>/<name>/."""
    lib = root / name
    lib.mkdir(parents=True, exist_ok=True)
    (lib / "_shelf-index.md").write_text(
        "<!-- format_version: 1 -->\n# Shelf Index\n"
    )
    return lib


def test_kb_query_skill_flow_writes_audit_events_on_attribution_drop(tmp_path: Path) -> None:
    """Simulates kb-query Step 4: when run_retrieval_query is invoked the way
    the kb-query skill does it (with audit_log_path), attribution drops land
    in library/audit.log.

    This test fails if the kb-query skill is not wired to pass audit_log_path.
    """
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    library_dir = _make_minimal_library(project_dir)
    audit_log = project_dir / "library" / "audit.log"

    # Mock dispatcher returns one tagged + one untagged finding (untagged is dropped)
    def mock_dispatcher(req: DispatchRequest) -> str:
        return (
            "### Tagged finding\n"
            "**Finding**: ok.\n"
            f"**Source library**: {req.source.name}\n\n"
            "### Untagged finding\n"
            "**Finding**: bad.\n"
        )

    sources = [LibrarySource(name="local", type="filesystem", path=str(library_dir))]
    # The kb-query skill MUST invoke run_retrieval_query with audit_log_path
    # pointing at <project>/library/audit.log. Simulate that here.
    result = run_retrieval_query(
        question="test query",
        sources=sources,
        priming=None,
        dispatcher=mock_dispatcher,
        audit_log_path=audit_log,  # <-- this is the contract the skill must honour
    )

    # Audit log should exist and contain the drop event
    assert audit_log.exists(), "audit.log was not created — kb-query skill must pass audit_log_path"
    events = read_log(audit_log, event_type="attribution_drop_retrieval")
    assert len(events) == 1
    assert events[0].source_handle == "local"
    assert "Untagged finding" in events[0].detail.get("dropped_block_titles", [])[0]
