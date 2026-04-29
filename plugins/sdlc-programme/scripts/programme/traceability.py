"""Build and export traceability matrix from a feature's phase artefacts.

The matrix is one row per REQ-ID, with the DES-IDs that satisfy it and the
TEST-IDs that satisfy it (transitively through the design-spec). Two export
formats: CSV (audit tooling) and markdown (review tooling).

Phase E (Assured bundle) extends with standard-specific formats (DO-178C RTM,
IEC 62304 matrix, ISO 26262 ASIL matrix, FDA DHF). Phase D ships csv + markdown.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .spec_parser import ParsedSpec, SpecParseError, parse_spec


class TraceabilityError(Exception):
    """Raised when a traceability matrix cannot be built."""


@dataclass
class TraceabilityRow:
    """One row of the traceability matrix — a REQ and what satisfies it."""

    req_id: str
    des_ids: set[str] = field(default_factory=set)
    test_ids: set[str] = field(default_factory=set)


def _load_phase(feature_dir: Path, phase: str, filename: str) -> ParsedSpec:
    path = feature_dir / filename
    if not path.exists():
        raise TraceabilityError(f"Phase artefact not found: {filename}")
    try:
        return parse_spec(path, phase=phase)
    except SpecParseError as e:
        raise TraceabilityError(f"{filename}: {e}") from e


def _satisfies_for_des(des_spec_text: str) -> dict[str, set[str]]:
    """Map each DES-ID heading to the set of REQ-IDs in its **satisfies:** line.

    Walks the design-spec line-wise: when an ``### DES-...`` heading is found,
    the next ``**satisfies:**`` line within the section is parsed for REQ-IDs.
    """
    result: dict[str, set[str]] = {}
    current_des: str | None = None
    in_code_block = False

    heading_re = re.compile(r"^###\s+(DES-[a-z0-9][a-z0-9-]*-\d+)\b")
    satisfies_re = re.compile(r"^\*\*satisfies:\*\*\s+(.+)$")
    ref_re = re.compile(r"\b(REQ-[a-z0-9][a-z0-9-]*-\d+)\b")

    for line in des_spec_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        m = heading_re.match(line)
        if m:
            current_des = m.group(1)
            result.setdefault(current_des, set())
            continue

        s = satisfies_re.match(line)
        if s and current_des is not None:
            for req in ref_re.findall(s.group(1)):
                result[current_des].add(req)

    return result


def _satisfies_for_test(
    test_spec_text: str,
) -> dict[str, tuple[set[str], set[str]]]:
    """Map each TEST-ID to (REQ-IDs, DES-IDs) it satisfies.

    Walks line-wise like ``_satisfies_for_des`` but extracts both REQ and DES
    references from the ``**satisfies:**`` line of each TEST section.
    """
    result: dict[str, tuple[set[str], set[str]]] = {}
    current_test: str | None = None
    in_code_block = False

    heading_re = re.compile(r"^###\s+(TEST-[a-z0-9][a-z0-9-]*-\d+)\b")
    satisfies_re = re.compile(r"^\*\*satisfies:\*\*\s+(.+)$")
    req_re = re.compile(r"\b(REQ-[a-z0-9][a-z0-9-]*-\d+)\b")
    des_re = re.compile(r"\b(DES-[a-z0-9][a-z0-9-]*-\d+)\b")

    for line in test_spec_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        m = heading_re.match(line)
        if m:
            current_test = m.group(1)
            result.setdefault(current_test, (set(), set()))
            continue

        s = satisfies_re.match(line)
        if s and current_test is not None:
            reqs, dess = result[current_test]
            for req in req_re.findall(s.group(1)):
                reqs.add(req)
            for des in des_re.findall(s.group(1)):
                dess.add(des)

    return result


def build_matrix(feature_dir: Path, feature_id: str) -> list[TraceabilityRow]:
    """Build the traceability matrix as a list of rows ordered by REQ-ID."""
    req = _load_phase(feature_dir, "requirements", "requirements-spec.md")
    _load_phase(feature_dir, "design", "design-spec.md")
    _load_phase(feature_dir, "test", "test-spec.md")

    des_text = (feature_dir / "design-spec.md").read_text()
    test_text = (feature_dir / "test-spec.md").read_text()

    des_satisfies = _satisfies_for_des(des_text)
    test_satisfies = _satisfies_for_test(test_text)

    # Reverse-index: for each REQ, which DES-IDs satisfy it?
    req_to_des: dict[str, set[str]] = {r: set() for r in req.declared_ids}
    for des_id, reqs in des_satisfies.items():
        for r in reqs:
            req_to_des.setdefault(r, set()).add(des_id)

    # For each REQ, which TEST-IDs satisfy it directly OR via a satisfying DES?
    req_to_test: dict[str, set[str]] = {r: set() for r in req.declared_ids}
    for test_id, (reqs, dess) in test_satisfies.items():
        for r in reqs:
            req_to_test.setdefault(r, set()).add(test_id)
        # Transitive: if test satisfies DES, and DES satisfies REQ, then test → REQ
        for d in dess:
            for r, satisfying_des in req_to_des.items():
                if d in satisfying_des:
                    req_to_test.setdefault(r, set()).add(test_id)

    rows: list[TraceabilityRow] = []
    for r in sorted(req.declared_ids):
        rows.append(
            TraceabilityRow(
                req_id=r,
                des_ids=req_to_des.get(r, set()),
                test_ids=req_to_test.get(r, set()),
            )
        )
    return rows


def export_csv(feature_dir: Path, feature_id: str) -> str:
    """Export the matrix as CSV: one row per (REQ, DES, TEST) triple.

    Cartesian-product expansion: a REQ with 2 DES and 3 TEST yields up to 6 rows.
    Empty DES or TEST cells render as empty strings.
    """
    rows = build_matrix(feature_dir, feature_id)
    out_lines = ["REQ,DES,TEST"]
    for row in rows:
        des_list = sorted(row.des_ids) or [""]
        test_list = sorted(row.test_ids) or [""]
        for d in des_list:
            for t in test_list:
                out_lines.append(f"{row.req_id},{d},{t}")
    return "\n".join(out_lines) + "\n"


def export_markdown(feature_dir: Path, feature_id: str) -> str:
    """Export the matrix as a markdown table."""
    rows = build_matrix(feature_dir, feature_id)
    lines = ["| REQ | DES | TEST |", "| --- | --- | --- |"]
    for row in rows:
        des_list = sorted(row.des_ids) or [""]
        test_list = sorted(row.test_ids) or [""]
        for d in des_list:
            for t in test_list:
                lines.append(f"| {row.req_id} | {d} | {t} |")
    return "\n".join(lines) + "\n"
