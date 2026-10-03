"""EvidenceStatus enum for typed RTM cells (F-009)."""

from __future__ import annotations

from enum import Enum


class EvidenceStatus(Enum):
    LINKED = "linked"
    MISSING = "missing"
    NOT_APPLICABLE = "not_applicable"
    MANUAL_EVIDENCE_REQUIRED = "manual_evidence_required"
    CONFIGURATION_ARTIFACT = "configuration_artifact"

    def display(self) -> str:
        return {
            EvidenceStatus.LINKED: "linked",
            EvidenceStatus.MISSING: "MISSING",
            EvidenceStatus.NOT_APPLICABLE: "n/a",
            EvidenceStatus.MANUAL_EVIDENCE_REQUIRED: "manual",
            EvidenceStatus.CONFIGURATION_ARTIFACT: "config",
        }[self]
