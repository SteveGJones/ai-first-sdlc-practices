"""Mandatory + optional traceability validators for the Assured bundle."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import List

from .ids import IdRecord


@dataclass
class ValidatorResult:
    """Outcome of a single validator run."""

    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def id_uniqueness(records: List[IdRecord]) -> ValidatorResult:
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
