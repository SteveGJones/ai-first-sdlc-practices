"""Tests for assured.requirement_metadata."""

from pathlib import Path

from sdlc_assured_scripts.assured.evidence_status import EvidenceStatus
from sdlc_assured_scripts.assured.requirement_metadata import (
    RequirementMetadata,
    build_requirement_metadata_registry,
)


def test_metadata_captured_from_per_req_inline_fields(tmp_path: Path) -> None:
    spec = tmp_path / "docs" / "specs" / "auth" / "requirements-spec.md"
    spec.parent.mkdir(parents=True)
    spec.write_text(
        "---\n"
        "feature_id: auth\n"
        "module: P1.SP1.M1\n"
        "---\n"
        "## Requirements\n"
        "\n"
        "### REQ-auth-001\n"
        "Real one.\n"
        "**Module:** P1.SP1.M1\n"
        "**Evidence-status:** linked\n"
        "\n"
        "### REQ-auth-002\n"
        "Configuration-only.\n"
        "**Module:** P1.SP1.M1\n"
        "**Evidence-status:** configuration_artifact\n"
        "**Justification:** Implemented entirely by `programs.yaml` declarations.\n"
        "**Related:** REQ-auth-001\n"
    )
    registry = build_requirement_metadata_registry(tmp_path)
    md1 = registry["REQ-auth-001"]
    assert md1.evidence_status == EvidenceStatus.LINKED
    assert md1.justification is None
    assert md1.related == []
    md2 = registry["REQ-auth-002"]
    assert md2.evidence_status == EvidenceStatus.CONFIGURATION_ARTIFACT
    assert "programs.yaml" in (md2.justification or "")
    assert md2.related == ["REQ-auth-001"]


def test_missing_evidence_status_field_defaults_to_none() -> None:
    md = RequirementMetadata(req_id="REQ-x-001")
    assert md.evidence_status is None
    assert md.justification is None
    assert md.related == []


def test_multiple_reqs_across_two_spec_files(tmp_path: Path) -> None:
    for feature in ("feat-a", "feat-b"):
        spec = tmp_path / "docs" / "specs" / feature / "requirements-spec.md"
        spec.parent.mkdir(parents=True)
        spec.write_text(
            f"### REQ-{feature}-001\n"
            "**Evidence-status:** linked\n"
            f"\n"
            f"### REQ-{feature}-002\n"
            "**Evidence-status:** missing\n"
        )
    registry = build_requirement_metadata_registry(tmp_path)
    assert len(registry) == 4
    assert registry["REQ-feat-a-001"].evidence_status == EvidenceStatus.LINKED
    assert registry["REQ-feat-b-002"].evidence_status == EvidenceStatus.MISSING
