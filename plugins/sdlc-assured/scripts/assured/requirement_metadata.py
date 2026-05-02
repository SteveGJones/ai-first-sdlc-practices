"""Per-requirement metadata captured from inline `**Field:**` lines.

This complements `IdRecord` (which carries only id/kind/source/satisfies)
with the metadata that v0.2.0 typed-evidence-status (F-009) and per-REQ
relation tracking (F-006) require.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .evidence_status import EvidenceStatus


@dataclass(frozen=True)
class RequirementMetadata:
    req_id: str
    evidence_status: Optional[EvidenceStatus] = None
    justification: Optional[str] = None
    related: list[str] = field(default_factory=list)


_REQ_HEADING_RE = re.compile(
    r"^###\s+(?P<id>(?:P\d+\.SP\d+\.M\d+\.)?REQ-(?:[a-z0-9][a-z0-9-]*-)?\d+)\b"
)
_FIELD_RE = re.compile(r"^\*\*(?P<key>[A-Za-z][A-Za-z0-9-]*)?:\*\*\s+(?P<value>.+)$")
_ID_TOKEN_RE = re.compile(
    r"\b((?:P\d+\.SP\d+\.M\d+\.)?(?:REQ|DES|TEST|CODE)-(?:[a-z0-9][a-z0-9-]*-)?\d+)\b"
)


def build_requirement_metadata_registry(
    project_root: Path,
) -> dict[str, RequirementMetadata]:
    """Walk docs/specs/**/requirements-spec.md; build {req_id: RequirementMetadata}."""
    registry: dict[str, RequirementMetadata] = {}
    specs_dir = project_root / "docs" / "specs"
    if not specs_dir.is_dir():
        return registry
    for spec_file in sorted(specs_dir.glob("**/requirements-spec.md")):
        text = spec_file.read_text(encoding="utf-8")
        current_id: Optional[str] = None
        evidence_status: Optional[EvidenceStatus] = None
        justification: Optional[str] = None
        related: list[str] = []
        in_code_block = False

        def _flush() -> None:
            nonlocal current_id, evidence_status, justification, related
            if current_id is not None:
                registry[current_id] = RequirementMetadata(
                    req_id=current_id,
                    evidence_status=evidence_status,
                    justification=justification,
                    related=list(related),
                )
            current_id = None
            evidence_status = None
            justification = None
            related = []

        for line in text.splitlines():
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue
            heading = _REQ_HEADING_RE.match(line)
            if heading:
                _flush()
                current_id = heading["id"]
                continue
            if current_id is None:
                continue
            field_match = _FIELD_RE.match(line)
            if not field_match:
                continue
            key = (field_match["key"] or "").lower()
            value = field_match["value"].strip()
            if key == "evidence-status":
                try:
                    evidence_status = EvidenceStatus(value.lower())
                except ValueError:
                    pass
            elif key == "justification":
                justification = value
            elif key == "related":
                related = _ID_TOKEN_RE.findall(value)
        _flush()
    return registry
