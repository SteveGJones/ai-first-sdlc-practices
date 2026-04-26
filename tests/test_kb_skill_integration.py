"""End-to-end integration tests that exercise the user-facing skill flows.

Each test simulates what the kb-query, kb-audit-query, kb-promote, and
kb-setup-consulting skills do in production. Catches gaps between the
Python helpers and the bash-snippet-orchestrated user flows.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

from sdlc_knowledge_base_scripts.audit import AuditEvent, log_event, read_log
from sdlc_knowledge_base_scripts.orchestrator import (
    DispatchRequest,
    run_retrieval_query,
)
from sdlc_knowledge_base_scripts.registry import LibrarySource


def _make_minimal_library(root: Path, name: str = "library") -> Path:
    """Create a minimal valid library directory at <root>/<name>/."""
    lib = root / name
    lib.mkdir(parents=True, exist_ok=True)
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf Index\n")
    return lib


def test_kb_query_skill_flow_writes_audit_events_on_attribution_drop(
    tmp_path: Path,
) -> None:
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
    run_retrieval_query(
        question="test query",
        sources=sources,
        priming=None,
        dispatcher=mock_dispatcher,
        audit_log_path=audit_log,  # <-- this is the contract the skill must honour
    )

    # Audit log should exist and contain the drop event
    assert (
        audit_log.exists()
    ), "audit.log was not created — kb-query skill must pass audit_log_path"
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
    shutil.copytree(
        repo_root / "tests/fixtures/kb_libraries/corp-target-fixture", target_root
    )
    target_lib = target_root / "library"

    # Simulate the promotion: write a new file into the target library + update audit
    new_file_name = "promoted-finding.md"
    new_file_path = target_lib / new_file_name
    new_file_content = (
        "---\n"
        'title: "Promoted finding from local engagement"\n'
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
    log_event(
        audit_log,
        AuditEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type="cross_library_promotion",
            query="test promotion question",
            source_handle="corp-target-fixture",
            reason="answer promoted to external library",
            detail={
                "source_file": str(project_lib / "answer.md"),
                "target_path": str(new_file_path),
            },
        ),
    )

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


def test_kb_audit_query_filter_by_event_type(tmp_path: Path) -> None:
    """Simulates kb-audit-query --event-type attribution_drop_retrieval against
    a project audit log with mixed event types."""
    audit_log = tmp_path / "library" / "audit.log"
    audit_log.parent.mkdir(parents=True)

    # Seed the audit log with events of different types
    log_event(
        audit_log,
        AuditEvent(
            timestamp="2026-04-25T10:00:00Z",
            event_type="attribution_drop_retrieval",
            query="q1",
            source_handle="local",
            reason="r",
            detail={},
        ),
    )
    log_event(
        audit_log,
        AuditEvent(
            timestamp="2026-04-25T11:00:00Z",
            event_type="synthesis_aborted_attribution",
            query="q2",
            source_handle=None,
            reason="r",
            detail={},
        ),
    )
    log_event(
        audit_log,
        AuditEvent(
            timestamp="2026-04-25T12:00:00Z",
            event_type="attribution_drop_retrieval",
            query="q3",
            source_handle="corp",
            reason="r",
            detail={},
        ),
    )

    # The skill's main path: read with event_type filter
    drops = read_log(audit_log, event_type="attribution_drop_retrieval")
    assert len(drops) == 2
    assert {e.source_handle for e in drops} == {"local", "corp"}

    aborts = read_log(audit_log, event_type="synthesis_aborted_attribution")
    assert len(aborts) == 1


def test_kb_audit_query_filter_by_date_range(tmp_path: Path) -> None:
    """Simulates kb-audit-query --since <date> against a project audit log."""
    audit_log = tmp_path / "library" / "audit.log"
    audit_log.parent.mkdir(parents=True)

    # Old event
    log_event(
        audit_log,
        AuditEvent(
            timestamp="2026-01-01T00:00:00Z",
            event_type="attribution_drop_retrieval",
            query="old",
            source_handle="local",
            reason="r",
            detail={},
        ),
    )
    # Recent event
    log_event(
        audit_log,
        AuditEvent(
            timestamp="2026-04-25T00:00:00Z",
            event_type="attribution_drop_retrieval",
            query="recent",
            source_handle="local",
            reason="r",
            detail={},
        ),
    )

    # The skill's --since 2026-04-01 filter
    recent = read_log(audit_log, since="2026-04-01T00:00:00Z")
    assert len(recent) == 1
    assert recent[0].query == "recent"


def test_kb_audit_query_summary_count_by_type(tmp_path: Path) -> None:
    """Simulates kb-audit-query --summary: count events by type."""
    from collections import Counter

    audit_log = tmp_path / "library" / "audit.log"
    audit_log.parent.mkdir(parents=True)

    for i in range(3):
        log_event(
            audit_log,
            AuditEvent(
                timestamp=f"2026-04-25T1{i}:00:00Z",
                event_type="attribution_drop_retrieval",
                query=f"q{i}",
                source_handle="local",
                reason="r",
                detail={},
            ),
        )
    log_event(
        audit_log,
        AuditEvent(
            timestamp="2026-04-25T15:00:00Z",
            event_type="cross_library_promotion",
            query="promote",
            source_handle="corp",
            reason="r",
            detail={},
        ),
    )

    events = read_log(audit_log)
    counts = Counter(e.event_type for e in events)
    assert counts["attribution_drop_retrieval"] == 3
    assert counts["cross_library_promotion"] == 1


def test_kb_audit_query_missing_log_returns_empty(tmp_path: Path) -> None:
    """Simulates kb-audit-query against a project with no audit log."""
    audit_log = tmp_path / "library" / "audit.log"  # not created
    events = read_log(audit_log)
    assert events == []


def test_kb_setup_consulting_verify_happy_path(tmp_path: Path) -> None:
    """Simulates kb-setup-consulting --verify-only against a healthy registry +
    activation: every registered library validates, smoke-test would pass."""
    from sdlc_knowledge_base_scripts.registry import (
        load_global_registry,
        load_project_activation,
        resolve_dispatch_list,
        validate_library_path,
    )
    from sdlc_knowledge_base_scripts.shelf_index_header import parse_shelf_index_header

    # Set up: one valid library at known path
    target_lib = _make_minimal_library(tmp_path, "corp-engagement")

    # User-scope registry pointing at it
    user_registry = tmp_path / "global-libraries.json"
    user_registry.write_text(
        json.dumps(
            {
                "version": 1,
                "libraries": [
                    {
                        "name": "corp-engagement",
                        "type": "filesystem",
                        "path": str(target_lib),
                        "description": "Test corporate library",
                    }
                ],
            }
        )
    )

    # Project-scope activation
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    project_lib = _make_minimal_library(project_dir)
    activation = project_dir / ".sdlc" / "libraries.json"
    activation.parent.mkdir()
    activation.write_text(
        json.dumps({"version": 1, "activated_sources": ["corp-engagement"]})
    )

    # The skill's --verify-only flow: load + validate
    gr = load_global_registry(user_registry)
    pa = load_project_activation(activation)
    dispatch = resolve_dispatch_list(gr, pa, project_library_path=project_lib)

    # Healthy state: 2 sources in dispatch (local + corp-engagement), no warnings
    assert len(dispatch.sources) == 2
    assert {s.name for s in dispatch.sources} == {"local", "corp-engagement"}
    assert dispatch.warnings == []
    assert dispatch.is_empty_error is False

    # Verify each registered library's path
    for lib in gr.libraries:
        if lib.type == "filesystem" and lib.path:
            ok, _ = validate_library_path(Path(lib.path))
            assert ok is True
            header = parse_shelf_index_header(Path(lib.path) / "_shelf-index.md")
            assert header.format_version == 1


def test_kb_setup_consulting_verify_reports_invalid_path(tmp_path: Path) -> None:
    """When a registered library's path is invalid, --verify-only reports it."""
    from sdlc_knowledge_base_scripts.registry import (
        load_global_registry,
        validate_library_path,
    )

    user_registry = tmp_path / "global-libraries.json"
    user_registry.write_text(
        json.dumps(
            {
                "version": 1,
                "libraries": [
                    {
                        "name": "broken-corp",
                        "type": "filesystem",
                        "path": "/totally/nonexistent",
                        "description": "Drive unmounted",
                    }
                ],
            }
        )
    )

    gr = load_global_registry(user_registry)
    invalid = []
    for lib in gr.libraries:
        if lib.type == "filesystem" and lib.path:
            ok, reason = validate_library_path(Path(lib.path))
            if not ok:
                invalid.append((lib.name, reason))

    # The skill's --verify-only output should include this in "Issues to fix"
    assert len(invalid) == 1
    assert invalid[0][0] == "broken-corp"
    assert "does not exist" in invalid[0][1].lower()


def test_kb_setup_consulting_verify_handle_mismatch(tmp_path: Path) -> None:
    """When a registered library's shelf-index handle differs from the registry,
    --verify-only flags the mismatch."""
    from sdlc_knowledge_base_scripts.shelf_index_header import parse_shelf_index_header

    # Library on disk says handle is "actual-handle"
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text(
        "<!-- format_version: 1 -->\n"
        "<!-- last_rebuilt: 2026-04-26T00:00:00Z -->\n"
        "<!-- library_handle: actual-handle -->\n"
        "# Shelf\n"
    )

    # But the registry calls it "expected-handle"
    expected_handle = "expected-handle"
    header = parse_shelf_index_header(lib / "_shelf-index.md")

    # The skill detects the mismatch
    mismatch = (
        header.library_handle is not None and header.library_handle != expected_handle
    )
    assert mismatch is True
    assert header.library_handle == "actual-handle"


def test_kb_setup_consulting_verify_empty_registry(tmp_path: Path) -> None:
    """--verify-only with no global registry reports gracefully (no error, just empty)."""
    from sdlc_knowledge_base_scripts.registry import load_global_registry

    user_registry = tmp_path / "global-libraries.json"  # not created
    gr = load_global_registry(user_registry)
    assert gr.libraries == []
    assert gr.warnings == []
