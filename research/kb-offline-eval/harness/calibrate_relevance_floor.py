#!/usr/bin/env python3
"""Reproducible calibration for the claim<->span RELEVANCE_FLOOR (#211, Slice 1, spec §8).

The verifier hardening (entailment.ground_claim) rejects a verbatim-but-irrelevant span when its
content-token coverage of the CLAIM falls below RELEVANCE_FLOOR. This script proves the chosen
floor (0.20) sits STRICTLY between two empirically separated populations, using the FROZEN
tokenizer + coverage function imported from the shipped module (so the calibration cannot drift
from production):

  * absence claims        -> coverage 0.0  (the §6.2 vulnerability: absence-shaped claims cite an
                            irrelevant verbatim span; they must be rejectable)
  * legitimate supported  -> coverage >= 0.286 (real answers genuinely share content tokens with
                            their evidence span)

Data: the committed gemma4:12b ratification trace (every published/graded claim of the 97-question
suite) plus a handful of synthetic edge fixtures (legit-negative, short-claim, irrelevant-span).
A legit-negative ("the solo method does not require formal sign-off") must NOT be rejected — it is
a real negation grounded by a relevant span, distinct from an epistemic-absence claim.

Run:  .venv/bin/python research/kb-offline-eval/harness/calibrate_relevance_floor.py
Exit 0 + "OK: floor 0.20 valid" when the separation holds; non-zero otherwise.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

# Register the shipped scripts dir as a package so the FROZEN tokenizer + floor are imported
# from production (calibration == production); the module uses relative imports.
_REPO = Path(__file__).resolve().parents[3]
_SCRIPTS = _REPO / "plugins" / "sdlc-knowledge-base" / "scripts"


def _register(pkg: str, scripts_dir: Path) -> None:
    spec = importlib.util.spec_from_file_location(
        pkg, scripts_dir / "__init__.py", submodule_search_locations=[str(scripts_dir)])
    mod = importlib.util.module_from_spec(spec)
    sys.modules[pkg] = mod
    spec.loader.exec_module(mod)


_register("sdlc_knowledge_base_scripts", _SCRIPTS)

from sdlc_knowledge_base_scripts.entailment import (  # noqa: E402
    RELEVANCE_FLOOR,
    _claim_span_coverage,
    is_epistemic_absence,
)

_TRACE = _REPO / "research" / "kb-offline-eval" / "trace-gemma4_12b-20260619T044923Z-run1.jsonl"

# Synthetic edge fixtures: (claim_text, span_text, must_pass). `must_pass` True means coverage
# must be >= floor (a relevant span that should ground); False means it must be < floor (an
# irrelevant span that must not ground).
_FIXTURES = [
    # legit-negative: real negation, span on-topic -> must PASS (not an epistemic absence).
    ("The solo method does not require formal sign-off.",
     "the solo method requires no formal sign-off", True),
    # synthetic irrelevant span: absence claim citing an off-topic verbatim header -> must FAIL.
    ("The company payroll schedule is not mentioned.", "DORA Metrics", False),
    # short content-bearing claim with a matching span -> must PASS.
    ("Trunk-based development avoids long-lived branches.",
     "trunk-based development avoids long-lived branches", True),
]


def _claim_coverage(claim: dict) -> float:
    """Best (max) content-token coverage of the claim across its declared evidence spans."""
    spans = claim.get("evidence_spans") or []
    return max((_claim_span_coverage(claim["text"], s.get("text", "")) for s in spans), default=0.0)


def _load_trace_populations(trace_path: Path):
    """Split every graded claim in the trace into (absence_coverages, legit_supported_coverages)."""
    absence, legit = [], []
    for line in trace_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("type") != "question":
            continue
        for claim in rec.get("claims") or []:
            cov = _claim_coverage(claim)
            if is_epistemic_absence(claim["text"]):
                absence.append(cov)
            elif claim.get("final_status") == "supported":
                legit.append(cov)
    return sorted(absence), sorted(legit)


def main() -> int:
    if not _TRACE.is_file():
        print(f"ERROR: trace not found: {_TRACE}", file=sys.stderr)
        return 2

    absence, legit = _load_trace_populations(_TRACE)
    if not absence or not legit:
        print(f"ERROR: empty population (absence={len(absence)}, legit={len(legit)})", file=sys.stderr)
        return 2

    absence_max = max(absence)
    legit_min = min(legit)
    legit_median = legit[len(legit) // 2]

    print(f"trace: {_TRACE.name}")
    print(f"RELEVANCE_FLOOR = {RELEVANCE_FLOOR}")
    print(f"absence claims:        n={len(absence):3d}  max coverage = {absence_max:.4f}")
    print(f"legit supported claims: n={len(legit):3d}  min = {legit_min:.4f}  median = {legit_median:.4f}")
    print(f"separation: {absence_max:.4f} < {RELEVANCE_FLOOR} < {legit_min:.4f}")

    ok = absence_max < RELEVANCE_FLOOR < legit_min

    print("\nsynthetic edge fixtures:")
    for claim_text, span_text, must_pass in _FIXTURES:
        cov = _claim_span_coverage(claim_text, span_text)
        passes = cov >= RELEVANCE_FLOOR
        verdict = "PASS" if passes == must_pass else "MISMATCH"
        ok = ok and (passes == must_pass)
        print(f"  [{verdict}] coverage={cov:.4f} expect_pass={must_pass}  {claim_text[:54]!r}")

    if ok:
        print(f"\nOK: floor {RELEVANCE_FLOOR} valid "
              f"(absence_max {absence_max:.4f} < {RELEVANCE_FLOOR} < legit_min {legit_min:.4f})")
        return 0
    print("\nFAIL: floor does not strictly separate the populations / a fixture mismatched",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
