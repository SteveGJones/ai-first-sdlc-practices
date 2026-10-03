"""Tests for EvidenceStatus."""

from sdlc_assured_scripts.assured.evidence_status import EvidenceStatus


def test_evidence_status_has_five_values() -> None:
    assert {s.name for s in EvidenceStatus} == {
        "LINKED",
        "MISSING",
        "NOT_APPLICABLE",
        "MANUAL_EVIDENCE_REQUIRED",
        "CONFIGURATION_ARTIFACT",
    }


def test_evidence_status_display_strings() -> None:
    assert EvidenceStatus.LINKED.display() == "linked"
    assert EvidenceStatus.MISSING.display() == "MISSING"
    assert EvidenceStatus.NOT_APPLICABLE.display() == "n/a"
    assert EvidenceStatus.MANUAL_EVIDENCE_REQUIRED.display() == "manual"
    assert EvidenceStatus.CONFIGURATION_ARTIFACT.display() == "config"
