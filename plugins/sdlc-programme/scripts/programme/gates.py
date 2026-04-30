"""Phase-gate validators for the Programme bundle (Method 1).

Four gates correspond to the four phases:
- requirements_gate — checks requirements-spec.md exists with feature-id
  and at least one REQ
- design_gate — checks design-spec.md exists with feature-id, references
  requirements-spec, and all satisfies references resolve to declared REQ-IDs
- test_gate — checks test-spec.md exists, references both prior phases,
  and all references resolve to declared REQ + DES IDs
- code_gate — checks code text has at least one # implements: TEST-<feature>-NNN
  annotation and the cited TEST-ID exists in test-spec.md

Each gate returns a GateResult with passed: bool and errors: list[str]. Block
on errors at pre-push validation; weak (vague but non-broken) references are
out of scope here — phase-review (skill) catches those.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .spec_parser import ParsedSpec, SpecParseError, parse_spec


_TEST_ID_REF_RE = re.compile(r"#\s*implements:\s*([^\n]+)")
_TEST_ID_RE = re.compile(r"\b(TEST-[a-z0-9][a-z0-9-]*-\d+)\b")


class GateError(Exception):
    """Raised when a gate cannot be executed (not the same as gate failing)."""


@dataclass
class GateResult:
    """Outcome of running a phase gate."""

    gate_name: str
    feature_id: str
    passed: bool = True
    errors: list[str] = field(default_factory=list)


def _try_parse(path: Path, phase: str) -> tuple[ParsedSpec | None, str | None]:
    """Parse a spec; return (parsed, None) or (None, error_message)."""
    try:
        return parse_spec(path, phase=phase), None
    except SpecParseError as e:
        return None, str(e)


def _has_review_record(feature_dir: Path, phase: str) -> bool:
    """Return True if a review record exists for the given phase.

    Review records live at <feature_dir>/reviews/<phase>-review-*.md
    (pattern includes any reviewer name).
    """
    reviews_dir = feature_dir / "reviews"
    if not reviews_dir.is_dir():
        return False
    matches = list(reviews_dir.glob(f"{phase}-review-*.md"))
    return len(matches) > 0


def requirements_gate(feature_dir: Path, feature_id: str) -> GateResult:
    """Check requirements-spec.md exists, has feature-id, declares ≥ 1 REQ-ID."""
    # implements: DES-programme-validators-001
    result = GateResult(gate_name="requirements", feature_id=feature_id)
    spec = feature_dir / "requirements-spec.md"

    parsed, err = _try_parse(spec, "requirements")
    if parsed is None:
        result.passed = False
        result.errors.append(f"requirements-spec.md: {err}")
        return result

    if parsed.feature_id != feature_id:
        result.passed = False
        result.errors.append(
            f"requirements-spec.md feature-id mismatch: "
            f"expected {feature_id}, got {parsed.feature_id}"
        )
    if not parsed.declared_ids:
        result.passed = False
        result.errors.append(
            "requirements-spec.md declares no REQ-IDs "
            "(need at least one ### REQ-<feature>-NNN heading)"
        )

    return result


def design_gate(feature_dir: Path, feature_id: str) -> GateResult:
    """Check design-spec.md exists with valid satisfies refs to requirements-spec."""
    # implements: DES-programme-validators-002
    result = GateResult(gate_name="design", feature_id=feature_id)

    req_spec = feature_dir / "requirements-spec.md"
    des_spec = feature_dir / "design-spec.md"

    req_parsed, req_err = _try_parse(req_spec, "requirements")
    if req_parsed is None:
        result.passed = False
        result.errors.append(f"requirements-spec.md (prerequisite): {req_err}")
        return result

    des_parsed, des_err = _try_parse(des_spec, "design")
    if des_parsed is None:
        result.passed = False
        result.errors.append(f"design-spec.md: {des_err}")
        return result

    if des_parsed.feature_id != feature_id:
        result.passed = False
        result.errors.append(
            f"design-spec.md feature-id mismatch: "
            f"expected {feature_id}, got {des_parsed.feature_id}"
        )

    if not des_parsed.declared_ids:
        result.passed = False
        result.errors.append(
            "design-spec.md declares no DES-IDs "
            "(need at least one ### DES-<feature>-NNN heading)"
        )

    # Every satisfies reference must resolve to a declared REQ-ID
    for ref in sorted(des_parsed.references):
        if ref.startswith("REQ-") and ref not in req_parsed.declared_ids:
            result.passed = False
            result.errors.append(
                f"design-spec.md references {ref} which is not declared "
                f"in requirements-spec.md"
            )

    # Article 14: design-spec requires a review record
    if not _has_review_record(feature_dir, "design"):
        result.passed = False
        result.errors.append(
            "design-spec.md has no review record at "
            f"{feature_dir}/reviews/design-review-*.md (run phase-review design <feature-id>)"
        )

    return result


def test_gate(feature_dir: Path, feature_id: str) -> GateResult:
    """Check test-spec.md exists with valid satisfies refs to both prior phases."""
    # implements: DES-programme-validators-003
    result = GateResult(gate_name="test", feature_id=feature_id)

    req_spec = feature_dir / "requirements-spec.md"
    des_spec = feature_dir / "design-spec.md"
    test_spec = feature_dir / "test-spec.md"

    req_parsed, req_err = _try_parse(req_spec, "requirements")
    if req_parsed is None:
        result.passed = False
        result.errors.append(f"requirements-spec.md (prerequisite): {req_err}")
        return result

    des_parsed, des_err = _try_parse(des_spec, "design")
    if des_parsed is None:
        result.passed = False
        result.errors.append(f"design-spec.md (prerequisite): {des_err}")
        return result

    test_parsed, test_err = _try_parse(test_spec, "test")
    if test_parsed is None:
        result.passed = False
        result.errors.append(f"test-spec.md: {test_err}")
        return result

    if test_parsed.feature_id != feature_id:
        result.passed = False
        result.errors.append(
            f"test-spec.md feature-id mismatch: "
            f"expected {feature_id}, got {test_parsed.feature_id}"
        )

    if not test_parsed.declared_ids:
        result.passed = False
        result.errors.append(
            "test-spec.md declares no TEST-IDs "
            "(need at least one ### TEST-<feature>-NNN heading)"
        )

    for ref in sorted(test_parsed.references):
        if ref.startswith("REQ-") and ref not in req_parsed.declared_ids:
            result.passed = False
            result.errors.append(
                f"test-spec.md references {ref} which is not declared "
                f"in requirements-spec.md"
            )
        elif ref.startswith("DES-") and ref not in des_parsed.declared_ids:
            result.passed = False
            result.errors.append(
                f"test-spec.md references {ref} which is not declared "
                f"in design-spec.md"
            )

    # Article 14: test-spec requires a review record
    if not _has_review_record(feature_dir, "test"):
        result.passed = False
        result.errors.append(
            "test-spec.md has no review record at "
            f"{feature_dir}/reviews/test-review-*.md (run phase-review test <feature-id>)"
        )

    return result


def code_gate(feature_dir: Path, feature_id: str, code_text: str) -> GateResult:
    """Check code_text has a TEST-ID annotation that resolves to test-spec.md."""
    # implements: DES-programme-validators-004
    result = GateResult(gate_name="code", feature_id=feature_id)

    test_spec = feature_dir / "test-spec.md"
    test_parsed, test_err = _try_parse(test_spec, "test")
    if test_parsed is None:
        result.passed = False
        result.errors.append(f"test-spec.md (prerequisite): {test_err}")
        return result

    # Find # implements: lines and the TEST-IDs in them
    cited_test_ids: set[str] = set()
    for match in _TEST_ID_REF_RE.finditer(code_text):
        for tid in _TEST_ID_RE.findall(match.group(1)):
            cited_test_ids.add(tid)

    if not cited_test_ids:
        result.passed = False
        result.errors.append("code has no # implements: TEST-<feature>-NNN annotation")
        return result

    for tid in sorted(cited_test_ids):
        if tid not in test_parsed.declared_ids:
            result.passed = False
            result.errors.append(
                f"code references {tid} which is not declared in test-spec.md"
            )

    return result
