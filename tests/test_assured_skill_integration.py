"""End-to-end integration tests over the Assured fixture.

These tests traverse the full pipeline: parse programs.yaml, build the ID
registry, parse code annotations, run all validators, render module scope.
The fixture is the smallest plausible Assured-bundle project.
"""

from pathlib import Path

from sdlc_assured_scripts.assured.code_index import parse_code_annotations
from sdlc_assured_scripts.assured.decomposition import (
    CodeAnnotation,
    code_annotation_maps_to_module,
    parse_programs_yaml,
)
from sdlc_assured_scripts.assured.ids import build_id_registry
from sdlc_assured_scripts.assured.render import render_module_scope
from sdlc_assured_scripts.assured.traceability_validators import (
    backward_coverage,
    cited_ids_resolve,
    forward_link_integrity,
    id_uniqueness,
)


FIXTURE = Path(__file__).parent / "fixtures" / "assured" / "feature-sample"


def test_fixture_programs_yaml_parses():
    decomp = parse_programs_yaml(FIXTURE / "programs.yaml")
    assert decomp.programs[0].id == "P1"
    assert decomp.programs[0].sub_programs[0].modules[0].id == "M1"


def test_fixture_id_registry_has_six_ids():
    records = build_id_registry(FIXTURE)
    ids = {r.id for r in records}
    assert ids == {
        "REQ-auth-001",
        "REQ-auth-002",
        "DES-auth-001",
        "DES-auth-002",
        "TEST-auth-001",
        "TEST-auth-002",
    }


def test_fixture_validators_all_pass():
    records = build_id_registry(FIXTURE)
    assert id_uniqueness(records).passed
    assert cited_ids_resolve(records).passed
    assert forward_link_integrity(records).passed
    assert backward_coverage(records).passed


def test_fixture_code_annotations_parse():
    code_files = list((FIXTURE / "src").rglob("*.py"))
    entries = parse_code_annotations(code_files, project_root=FIXTURE)
    cited = sorted({cid for e in entries for cid in e.cited_ids})
    assert cited == ["DES-auth-001", "DES-auth-002", "REQ-auth-001", "REQ-auth-002"]


def test_fixture_render_module_scope_produces_full_doc():
    records = build_id_registry(FIXTURE)
    code_files = list((FIXTURE / "src").rglob("*.py"))
    entries = parse_code_annotations(code_files, project_root=FIXTURE)
    spec_module_lookup = {r.id: "P1.SP1.M1" for r in records}
    output = render_module_scope("P1.SP1.M1", records, entries, spec_module_lookup)
    for required in (
        "REQ-auth-001",
        "DES-auth-001",
        "TEST-auth-001",
        "src/auth/oauth/login.py",
    ):
        assert required in output


def test_fixture_code_annotations_in_module():
    decomp = parse_programs_yaml(FIXTURE / "programs.yaml")
    code_files = list((FIXTURE / "src").rglob("*.py"))
    entries = parse_code_annotations(code_files, project_root=FIXTURE)
    annotations = [
        CodeAnnotation(file_path=e.file_path, line=e.line, cited_ids=e.cited_ids)
        for e in entries
    ]
    spec_module_lookup = {
        "REQ-auth-001": "P1.SP1.M1",
        "REQ-auth-002": "P1.SP1.M1",
        "DES-auth-001": "P1.SP1.M1",
        "DES-auth-002": "P1.SP1.M1",
    }
    result = code_annotation_maps_to_module(annotations, decomp, spec_module_lookup)
    assert result.passed is True
