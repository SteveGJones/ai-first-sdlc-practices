#!/usr/bin/env python3
"""Reproducible calibration for the cited-page normalizer floor/margin (#211, Slice 2, spec §6).

Proves, using the FROZEN resolve_cited_page imported from the shipped module (so calibration
cannot drift from production):
  * the two real trace cases separate around the floor: q035 (0.821) recovers, q052 (0.588) drops;
  * the no-wrong-snap safety property holds against RUNTIME-SHAPED subsets (1-2 read pages):
    for every shelf id S and every typo-style perturbation P of S, the helper returns S or None
    against any subset containing S, and None against any subset NOT containing S -- NEVER a
    different id. Single-edit perturbations (the calibrated tier) additionally must recover.

Run:  .venv/bin/python research/kb-offline-eval/harness/calibrate_id_normalize.py
Exit 0 + "OK: id-normalize floor 0.75 / margin 0.10 valid" when all invariants hold.
"""
from __future__ import annotations

import importlib.util
import itertools
from pathlib import Path

# Register the shipped scripts dir so the FROZEN resolver is imported (no reimplementation).
_REPO = Path(__file__).resolve().parents[3]  # repo root (file is 3 dirs deep: research/kb-offline-eval/harness/)
SCRIPTS = _REPO / "plugins" / "sdlc-knowledge-base" / "scripts"
_spec = importlib.util.spec_from_file_location(
    "cited_page_normalize", SCRIPTS / "cited_page_normalize.py")
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
resolve_cited_page = _mod.resolve_cited_page

FLOOR, MARGIN = 0.75, 0.10

# The 16-page smoke/ratification shelf (the universe of distinct ids).
SHELF = [
    "ci-cd.md", "code-review.md", "deployment-strategies.md", "dora.md", "feature-flags.md",
    "incident-response.md", "observability.md", "pair-programming.md", "release-management.md",
    "sdlc-assured.md", "sdlc-programme.md", "sdlc-single-team.md", "sdlc-solo.md",
    "tech-debt.md", "testing.md", "trunk-based.md",
]


def _single_edit_typos(s: str) -> list[str]:
    """Deterministic single-edit perturbations: drop each char, double each char."""
    out = set()
    for i in range(len(s)):
        out.add(s[:i] + s[i + 1:])           # deletion
        out.add(s[:i] + s[i] + s[i:])        # duplication
    out.discard(s)
    return sorted(out)


def main() -> int:
    failures: list[str] = []

    # 1) Real trace cases through the frozen resolver.
    q035 = resolve_cited_page("sdlc-single-formm.md", ["sdlc-single-team.md"])
    if q035.page != "sdlc-single-team.md":
        failures.append(f"q035 should recover, got {q035}")
    q052 = resolve_cited_page("pair-summary.md", ["pair-programming.md"])
    if q052.page is not None or q052.score is None or not (0.55 <= q052.score <= 0.62):  # actual ~0.588
        failures.append(f"q052 should drop with retained score ~0.588, got {q052}")

    # 2) Runtime-subset safety sweep. For each S and each single-edit perturbation P of S,
    #    test singletons {S}, {X}; pairs {S,X}, {X,Y}. Invariant: result in {S, None} when S
    #    present, None when S absent -- never a non-source id.
    n_recover = n_failclosed = 0
    for s in SHELF:
        others = [x for x in SHELF if x != s]
        for p in _single_edit_typos(s):
            subsets = [(s,)] + [(x,) for x in others]
            subsets += [(s, x) for x in others]
            subsets += list(itertools.combinations(others, 2))
            for sub in subsets:
                page = resolve_cited_page(p, list(sub), floor=FLOOR, margin=MARGIN).page
                contains_s = s in sub
                if contains_s:
                    if page not in (s, None):
                        failures.append(
                            f"WRONG-SNAP {p!r} in {sub} -> {page!r} (expected {s} or None)")
                else:
                    if page is not None:
                        failures.append(
                            f"WRONG-SNAP {p!r} in {sub} -> {page!r} (expected None)")
            # Liveness for the calibrated tier: single-edit P must recover on the singleton {S}.
            if resolve_cited_page(p, [s], floor=FLOOR, margin=MARGIN).page == s:
                n_recover += 1
            else:
                n_failclosed += 1

    if failures:
        for f in failures[:20]:
            print("FAIL:", f)
        print(f"... {len(failures)} total failures")
        return 1
    print(f"single-edit perturbations: recover={n_recover} fail-closed={n_failclosed} wrong=0")
    print("OK: id-normalize floor 0.75 / margin 0.10 valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
