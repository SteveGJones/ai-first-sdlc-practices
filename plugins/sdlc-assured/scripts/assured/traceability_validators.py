"""Mandatory + optional traceability validators for the Assured bundle."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List

from .ids import IdParseError, IdRecord, parse_id


@dataclass
class ValidatorResult:
    """Outcome of a single validator run."""

    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def id_uniqueness(records: List[IdRecord]) -> ValidatorResult:  # implements: DES-assured-traceability-validators-001
    counts = Counter(r.id for r in records)
    duplicates = [id_ for id_, n in counts.items() if n > 1]
    if not duplicates:
        return ValidatorResult(passed=True)
    errors = [
        f"duplicate ID {id_!r} declared in: "
        + ", ".join(r.source for r in records if r.id == id_)
        for id_ in sorted(duplicates)
    ]
    return ValidatorResult(passed=False, errors=errors)


def cited_ids_resolve(records: List[IdRecord]) -> ValidatorResult:  # implements: DES-assured-traceability-validators-001
    declared = {r.id for r in records}
    errors: List[str] = []
    for r in records:
        for cited in r.satisfies:
            if cited not in declared:
                errors.append(
                    f"{r.id} (in {r.source}) cites {cited!r} which is not declared anywhere"
                )
    return ValidatorResult(passed=not errors, errors=errors)


def orphan_ids(records: List[IdRecord]) -> ValidatorResult:  # implements: DES-assured-traceability-validators-001, DES-assured-traceability-validators-005
    """Warn when any declared ID is never cited by another record.

    Covers REQ, DES, TEST, and CODE kinds (E1: widened in v0.2.0).
    Complementary to backward_coverage, which checks the REQ→DES→TEST chain.
    """
    cited: set[str] = set()
    for r in records:
        cited.update(r.satisfies)
    warnings: List[str] = []
    for r in records:
        if r.kind in {"REQ", "DES", "TEST", "CODE"} and r.id not in cited:
            warnings.append(
                f"orphan {r.kind} {r.id!r} (declared in {r.source}) is never cited"
            )
    return ValidatorResult(passed=True, warnings=warnings)


def forward_link_integrity(records: List[IdRecord]) -> ValidatorResult:  # implements: DES-assured-traceability-validators-002
    """Verify every DES cites at least one REQ; every TEST cites at least one DES; targets resolve."""
    declared = {r.id: r for r in records}
    errors: List[str] = []
    for r in records:
        if r.kind == "DES" and not r.satisfies:
            errors.append(
                f"{r.id} (in {r.source}) has no satisfies links — DES must cite at least one REQ"
            )
        if r.kind == "TEST" and not r.satisfies:
            errors.append(
                f"{r.id} (in {r.source}) has no satisfies links — TEST must cite at least one DES"
            )
        for cited in r.satisfies:
            if cited not in declared:
                errors.append(f"{r.id} (in {r.source}) cites missing target {cited!r}")
    return ValidatorResult(passed=not errors, errors=errors)


def backward_coverage(records: List[IdRecord]) -> ValidatorResult:  # implements: DES-assured-traceability-validators-002
    """Verify every REQ is covered by a DES; every DES is covered by a TEST."""
    cited_by: dict[str, List[str]] = {r.id: [] for r in records}
    for r in records:
        for target in r.satisfies:
            if target in cited_by:
                cited_by[target].append(r.id)
    errors: List[str] = []
    for r in records:
        if r.kind == "REQ":
            des_children = [
                c
                for c in cited_by[r.id]
                if c.startswith("DES") or "DES-" in c.split(".")[-1]
            ]
            if not des_children:
                errors.append(f"{r.id} (in {r.source}) has no DES covering it")
        if r.kind == "DES":
            test_children = [
                c
                for c in cited_by[r.id]
                if c.startswith("TEST") or "TEST-" in c.split(".")[-1]
            ]
            if not test_children:
                errors.append(f"{r.id} (in {r.source}) has no TEST covering it")
    return ValidatorResult(passed=not errors, errors=errors)


def index_regenerability(  # implements: DES-assured-traceability-validators-003
    index_path: Path, regenerate: Callable[[], str]
) -> ValidatorResult:
    """Idempotency check: re-running the generator must produce byte-identical output."""
    if not index_path.is_file():
        return ValidatorResult(
            passed=False,
            errors=[f"index file does not exist: {index_path}"],
        )
    on_disk = index_path.read_text(encoding="utf-8")
    fresh = regenerate()
    if on_disk == fresh:
        return ValidatorResult(passed=True)
    return ValidatorResult(
        passed=False,
        errors=[
            f"index {index_path} is not idempotent — committed content differs from "
            "regenerated output. Run kb-rebuild-indexes and commit."
        ],
    )


def change_impact_gate(  # implements: DES-assured-substrate-003
    changed_code_files: List[Path],
    change_impact_records_dir: Path,
    enabled: bool,
) -> ValidatorResult:
    """When enabled, every changed code file must be cited in at least one change-impact record."""
    if not enabled:
        return ValidatorResult(passed=True)
    if not change_impact_records_dir.is_dir():
        return ValidatorResult(
            passed=False,
            errors=[
                f"change-impact directory {change_impact_records_dir} does not exist"
            ],
        )
    cited_paths: set[str] = set()
    for record in change_impact_records_dir.glob("*.md"):
        cited_paths |= {
            line.split(":")[0].strip().lstrip("- ")
            for line in record.read_text(encoding="utf-8").splitlines()
            if "src/" in line and ":" in line
        }
    errors: List[str] = []
    for f in changed_code_files:
        rel = str(f).replace(str(f.anchor), "")
        if not any(rel.endswith(c) or c in str(f) for c in cited_paths):
            errors.append(f"{f}: no change-impact record cites this file")
    return ValidatorResult(passed=not errors, errors=errors)


_IMPLEMENTS_RE = re.compile(r"^\s*#\s*implements:\s*(?P<ids>.+)$", re.MULTILINE)
_ID_TOKEN_RE = re.compile(r"[A-Za-z0-9.\-]+")


def annotation_format_integrity(  # implements: DES-assured-traceability-validators-004
    code_files: List[Path], declared_ids: set[str]
) -> ValidatorResult:
    """Check that every `# implements:` annotation cites a declared, well-formed ID."""
    errors: List[str] = []
    for f in code_files:
        if not f.is_file():
            continue
        text = f.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), start=1):
            m = _IMPLEMENTS_RE.match(line)
            if not m:
                continue
            ids_part = m["ids"]
            tokens = [t.strip(",") for t in _ID_TOKEN_RE.findall(ids_part)]
            for tok in tokens:
                try:
                    parse_id(tok)
                except IdParseError:
                    errors.append(f"{f}:{line_no}: malformed annotation token {tok!r}")
                    continue
                if tok not in declared_ids:
                    errors.append(
                        f"{f}:{line_no}: annotation cites {tok!r} which is not declared"
                    )
    return ValidatorResult(passed=not errors, errors=errors)
