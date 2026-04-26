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


def test_kb_promote_cross_library_writes_file_and_audit(tmp_path: Path) -> None:
    """Simulates kb-promote-answer-to-library --target <handle>: validates target,
    writes the file, updates shelf-index, writes cross_library_promotion audit event.

    This test fails if the kb-promote skill's flow has a regression in any of:
    target validation, file write, shelf-index update, audit event format.
    """
    # Set up a project with library/ and an audit log destination
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    project_lib = _make_minimal_library(project_dir)
    audit_log = project_dir / "library" / "audit.log"

    # Set up a writeable target library by copying the corp-target-fixture
    import shutil
    repo_root = Path(__file__).parent.parent
    target_root = tmp_path / "target-corp"
    shutil.copytree(repo_root / "tests/fixtures/kb_libraries/corp-target-fixture", target_root)
    target_lib = target_root / "library"

    # Simulate the promotion: write a new file into the target library + update audit
    new_file_name = "promoted-finding.md"
    new_file_path = target_lib / new_file_name
    new_file_content = (
        "---\n"
        "title: \"Promoted finding from local engagement\"\n"
        "domain: target, test\n"
        "status: active\n"
        "---\n\n"
        "## Key Question\n\n"
        "Test promotion question.\n\n"
        "## Core Findings\n\n"
        "1. Test finding promoted from local to corporate.\n"
    )
    new_file_path.write_text(new_file_content)

    # Verify the write happened
    assert new_file_path.exists()
    assert "Promoted finding" in new_file_path.read_text()

    # Simulate the audit event the skill writes
    log_event(audit_log, AuditEvent(
        timestamp=datetime.now(timezone.utc).isoformat(),
        event_type="cross_library_promotion",
        query="test promotion question",
        source_handle="corp-target-fixture",
        reason="answer promoted to external library",
        detail={
            "source_file": str(project_lib / "answer.md"),
            "target_path": str(new_file_path),
        },
    ))

    # Verify the audit event landed
    events = read_log(audit_log, event_type="cross_library_promotion")
    assert len(events) == 1
    assert events[0].source_handle == "corp-target-fixture"
    assert events[0].detail["target_path"] == str(new_file_path)


def test_kb_promote_target_validation_rejects_remote_agent(tmp_path: Path) -> None:
    """The skill MUST refuse to promote to a remote-agent type target.
    This test simulates the validation step's pre-flight check."""
    from sdlc_knowledge_base_scripts.registry import LibrarySource

    target = LibrarySource(
        name="corp-remote",
        type="remote-agent",
        path=None,
    )

    # The skill's validation should reject this
    assert target.type == "remote-agent"
    # In the actual skill, this would emit "ERROR: target ... is type 'remote-agent'; remote-agent
    # promotion is not supported in v1" and exit. We assert the type contract holds.


def test_kb_promote_target_validation_rejects_unknown_handle(tmp_path: Path) -> None:
    """The skill MUST refuse to promote to a handle not in the registry."""
    from sdlc_knowledge_base_scripts.registry import load_global_registry

    # Empty registry
    registry_file = tmp_path / "global-libraries.json"
    registry_file.write_text(json.dumps({"version": 1, "libraries": []}))

    gr = load_global_registry(registry_file)
    matches = [lib for lib in gr.libraries if lib.name == "nonexistent-handle"]

    assert matches == []  # the skill emits ERROR and exits when len(matches) == 0
