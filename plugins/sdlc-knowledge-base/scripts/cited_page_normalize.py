"""Narrow fuzzy recovery of corrupted cited-page ids (#211, Slice 2).

Synthesize-side ONLY: repair a model citation/span page-id back to a page actually read,
when there is a unique high-confidence match above a calibrated floor and runner-up margin.
Page ids are opaque, case-sensitive strings; the function is fail-closed (returns no page
when uncertain). No handle/library awareness — same-handle bucketing lives in the caller.

Spec: docs/superpowers/specs/2026-06-22-kb-offline-cited-page-normalize-design.md
"""
from __future__ import annotations

import difflib
from collections.abc import Collection
from typing import NamedTuple


class Resolution(NamedTuple):
    page: str | None        # resolved candidate, or None when no confident match
    score: float | None     # best ratio among candidates; None ONLY for an empty set.
    runner_up: float | None  # second-best score, or None when <2 distinct candidates


def resolve_cited_page(
    cited_page: str,
    candidates: Collection[str],
    *,
    floor: float = 0.75,
    margin: float = 0.10,
) -> Resolution:
    """Resolve a (possibly corrupted) page id against candidates. Frozen decision function."""
    uniq = sorted(set(candidates))  # dedupe + deterministic order before scoring
    if not uniq:
        return Resolution(None, None, None)
    if cited_page in uniq:  # exact match bypasses fuzzy floor/margin entirely
        return Resolution(cited_page, 1.0, None)
    scored = sorted(
        ((difflib.SequenceMatcher(None, cited_page, c).ratio(), c) for c in uniq),
        key=lambda t: (-t[0], t[1]),
    )
    best_score, best = scored[0]
    runner_up = scored[1][0] if len(scored) > 1 else None
    if best_score < floor:  # >= floor accepted (boundary)
        return Resolution(None, best_score, runner_up)
    # single distinct candidate: margin check bypassed (no runner-up => cannot be ambiguous)
    if runner_up is not None and (best_score - runner_up) < margin:  # >= margin accepted
        return Resolution(None, best_score, runner_up)
    return Resolution(best, best_score, runner_up)


def normalize_cited_page(
    cited_page: str,
    candidates: Collection[str],
    *,
    floor: float = 0.75,
    margin: float = 0.10,
) -> str | None:
    """Narrow str|None wrapper over resolve_cited_page (contract callers + unit tests)."""
    return resolve_cited_page(cited_page, candidates, floor=floor, margin=margin).page
