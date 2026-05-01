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
