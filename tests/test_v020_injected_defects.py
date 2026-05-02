"""Phase G sub-stage 2 — injected-defect tests for v0.2.0 validators.

Each test loads exactly one fixture from tests/fixtures/v020-verification/,
runs the v0.2.0 validator that the fixture is designed to exercise, and asserts
that the validator fires (errors, warnings, or absence of an extracted ID).

These tests prove the validators detect real defects (true-positive verification).
"""
from __future__ import annotations

from pathlib import Path
from typing import List

import pytest

from sdlc_assured_scripts.assured.decomposition import (
    Decomposition,
    Module,
    Program,
    SubProgram,
    VisibilityRule,
    forward_annotation_completeness,
    granularity_match,
    parse_programs_yaml,
    visibility_rule_enforcement,
)
from sdlc_assured_scripts.assured.dependency_extractor import (
    PythonAstExtractor,
    make_swift_extractor,
)
from sdlc_assured_scripts.assured.evidence_status import EvidenceStatus
from sdlc_assured_scripts.assured.ids import build_id_registry
from sdlc_assured_scripts.assured.requirement_metadata import (
    build_requirement_metadata_registry,
)
from sdlc_assured_scripts.assured.traceability_validators import orphan_ids
from sdlc_programme_scripts.programme.gates import requirements_gate


_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "v020-verification"


# ---------------------------------------------------------------------------
# Helper: build a Decomposition from programs.yaml with absolute paths
# ---------------------------------------------------------------------------


def _abs_decomp(fixture_root: Path) -> Decomposition:
    """Parse programs.yaml and rewrite all module paths as absolute paths."""
    raw = parse_programs_yaml(fixture_root / "programs.yaml")
    programs: List[Program] = []
    for p in raw.programs:
        sub_programs: List[SubProgram] = []
        for sp in p.sub_programs:
            modules: List[Module] = []
            for m in sp.modules:
                abs_paths = [
                    str(fixture_root / path.rstrip("/")) + "/"
                    for path in m.paths
                ]
                modules.append(
                    Module(
                        id=m.id,
                        name=m.name,
                        paths=abs_paths,
                        granularity=m.granularity,
                        structure=m.structure,
                        owner=m.owner,
                        paths_sections=list(m.paths_sections),
                    )
                )
            sub_programs.append(SubProgram(id=sp.id, name=sp.name, modules=modules))
        programs.append(
            Program(
                id=p.id,
                name=p.name,
                description=p.description,
                sub_programs=sub_programs,
            )
        )
    return Decomposition(programs=programs, visibility=list(raw.visibility))


# ---------------------------------------------------------------------------
# Test 1 — F-008: REQ-fix8-001 has no direct or indirect annotation coverage
# ---------------------------------------------------------------------------


def test_f008_no_des_evidence_fires_granularity_warning() -> None:
    """granularity_match warns when REQ has no direct or DES-linked annotation."""
    fx = _FIXTURES / "f-008-no-des-evidence"
    decomp = _abs_decomp(fx)

    # Build the ID registry to get REQs and the satisfies graph.
    records = build_id_registry(fx)
    declared_reqs = [r.id for r in records if r.kind == "REQ"]

    # spec_module_lookup: map every ID to its module
    # REQ-fix8-001 is in P1.SP1.M1 (from requirements-spec.md front matter).
    spec_module_lookup = {"REQ-fix8-001": "P1.SP1.M1", "DES-fix8-001": "P1.SP1.M1"}

    # satisfies_graph: DES-fix8-001 satisfies REQ-fix8-001
    satisfies_graph = {
        r.id: list(r.satisfies) for r in records if r.kind == "DES"
    }

    # No annotations: source file has no # implements: annotation at all.
    annotations: list = []

    result = granularity_match(
        declared_reqs=declared_reqs,
        annotations=annotations,
        decomp=decomp,
        spec_module_lookup=spec_module_lookup,
        satisfies_graph=satisfies_graph,
    )
    # Validator returns warnings (not errors) for under-specified REQs.
    assert any("REQ-fix8-001" in w for w in result.warnings), (
        f"Expected warning mentioning REQ-fix8-001; got warnings: {result.warnings}"
    )


# ---------------------------------------------------------------------------
# Test 2 — F-007 Python: mod_a imports mod_b but visibility is not declared
# ---------------------------------------------------------------------------


def test_f007_undeclared_python_import_fires_visibility_warning() -> None:
    """visibility_rule_enforcement warns (advisory) on undeclared Python cross-module import."""
    fx = _FIXTURES / "f-007-undeclared-import"
    decomp = _abs_decomp(fx)

    source_paths = list((fx / "src").rglob("*.py"))
    extractor = PythonAstExtractor()
    edges = extractor.extract(source_paths=source_paths, programs=decomp)

    # Verify the edge was actually extracted before running the validator.
    assert any(
        e.from_module == "P1.SP1.M1" and e.to_module == "P1.SP1.M2" for e in edges
    ), f"Expected M1→M2 edge; got edges: {edges}"

    result = visibility_rule_enforcement(edges=edges, decomp=decomp, mode="advisory")
    assert any(
        "P1.SP1.M1" in w and "P1.SP1.M2" in w for w in result.warnings
    ), f"Expected visibility warning about M1→M2; got warnings: {result.warnings}"


# ---------------------------------------------------------------------------
# Test 3 — F-007 Swift: mod_a imports ModB but visibility is not declared
# ---------------------------------------------------------------------------


def test_f007_undeclared_swift_import_fires_visibility_warning() -> None:
    """visibility_rule_enforcement warns (advisory) on undeclared Swift cross-module import."""
    fx = _FIXTURES / "f-007-swift-undeclared-import"
    decomp = _abs_decomp(fx)

    source_paths = list((fx / "src").rglob("*.swift"))
    extractor = make_swift_extractor()
    edges = extractor.extract(source_paths=source_paths, programs=decomp)

    # Verify the edge was actually extracted before running the validator.
    assert any(
        e.from_module == "P1.SP1.M1" and e.to_module == "P1.SP1.M2" for e in edges
    ), f"Expected M1→M2 Swift edge; got edges: {edges}"

    result = visibility_rule_enforcement(edges=edges, decomp=decomp, mode="advisory")
    assert any(
        "P1.SP1.M1" in w and "P1.SP1.M2" in w for w in result.warnings
    ), f"Expected visibility warning about M1→M2; got warnings: {result.warnings}"


# ---------------------------------------------------------------------------
# Test 4 — F-009: REQ-fix9-001 has evidence_status=NOT_APPLICABLE, no justification
# ---------------------------------------------------------------------------


def test_f009_not_applicable_no_justification_captured_in_metadata() -> None:
    """RequirementMetadata captures NOT_APPLICABLE status with absent justification."""
    fx = _FIXTURES / "f-009-not-applicable-no-justification"
    registry = build_requirement_metadata_registry(fx)

    assert "REQ-fix9-001" in registry, (
        f"Expected REQ-fix9-001 in metadata registry; got keys: {list(registry.keys())}"
    )
    meta = registry["REQ-fix9-001"]
    assert meta.evidence_status == EvidenceStatus.NOT_APPLICABLE, (
        f"Expected NOT_APPLICABLE; got {meta.evidence_status}"
    )
    # The defect: no justification field present
    assert not meta.justification, (
        f"Expected justification to be absent/empty (the defect); got {meta.justification!r}"
    )


# ---------------------------------------------------------------------------
# Test 5 — E1: TEST-fxe1-001 is never cited by any CODE annotation — orphan
# ---------------------------------------------------------------------------


def test_e1_orphan_test_fires_orphan_warning() -> None:
    """orphan_ids warns when TEST record is never cited by any CODE annotation."""
    fx = _FIXTURES / "e1-orphan-test"

    # The fixture source (core.py) only cites DES-fxe1-001, never TEST-fxe1-001.
    # The ID registry from specs gives us REQ, DES, TEST records with satisfies links.
    records = build_id_registry(fx)

    result = orphan_ids(records)
    assert any(
        "TEST-fxe1-001" in w for w in result.warnings
    ), f"Expected orphan warning for TEST-fxe1-001; got warnings: {result.warnings}"


# ---------------------------------------------------------------------------
# Test 6 — E2: calculate_something() is a public function with no annotation
# ---------------------------------------------------------------------------


def test_e2_unannotated_public_fn_fires_annotation_error() -> None:
    """forward_annotation_completeness errors on public function missing # implements:."""
    fx = _FIXTURES / "e2-unannotated-public-fn"
    decomp = _abs_decomp(fx)

    source_paths = list((fx / "src").rglob("*.py"))
    result = forward_annotation_completeness(source_paths=source_paths, decomp=decomp)

    assert not result.passed, "Expected forward_annotation_completeness to fail"
    assert any(
        "calculate_something" in e for e in result.errors
    ), f"Expected error mentioning calculate_something; got errors: {result.errors}"


# ---------------------------------------------------------------------------
# Test 7 — D1: blockquoted REQ-fake-001 must NOT appear in the ID registry
# ---------------------------------------------------------------------------


def test_d1_blockquoted_req_not_extracted() -> None:
    """build_id_registry must NOT extract IDs from markdown blockquotes."""
    fx = _FIXTURES / "d1-blockquoted-req"
    records = build_id_registry(fx)

    extracted_ids = {r.id for r in records}

    # The blockquoted line contains REQ-fake-001 — it must be absent.
    assert "REQ-fake-001" not in extracted_ids, (
        f"REQ-fake-001 should not be extracted from a blockquote; "
        f"got registry IDs: {sorted(extracted_ids)}"
    )
    # The real requirement must be present.
    assert "REQ-fxd1-001" in extracted_ids, (
        f"REQ-fxd1-001 (the real requirement) must be in the registry; "
        f"got registry IDs: {sorted(extracted_ids)}"
    )


# ---------------------------------------------------------------------------
# Test 8 — D2: whitespace-only Motivation section triggers requirements_gate
# ---------------------------------------------------------------------------


def test_d2_whitespace_only_section_fires_requirements_gate_error() -> None:
    """requirements_gate errors when a mandatory section body is whitespace-only."""
    fx = _FIXTURES / "d2-whitespace-only-section"
    feature_dir = fx / "docs" / "specs" / "fxd2"
    feature_id = "fxd2"

    result = requirements_gate(feature_dir=feature_dir, feature_id=feature_id)

    assert not result.passed, "Expected requirements_gate to fail for whitespace Motivation"
    assert any(
        "Motivation" in e and ("whitespace" in e or "empty" in e)
        for e in result.errors
    ), (
        f"Expected error about whitespace-only Motivation section; "
        f"got errors: {result.errors}"
    )
