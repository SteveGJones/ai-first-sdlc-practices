"""Tests for assured.decomposition — programs.yaml schema + validators."""

from pathlib import Path

import pytest

from sdlc_assured_scripts.assured.decomposition import (
    CodeAnnotation,
    Decomposition,
    DecompositionParseError,
    SpecArtefact,
    code_annotation_maps_to_module,
    default_decomposition,
    parse_programs_yaml,
    req_has_module_assignment,
)


def parse_programs_yaml_inline(content: str) -> Decomposition:
    import tempfile
    from pathlib import Path as _Path

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(content)
        tmp_path = _Path(f.name)
    return parse_programs_yaml(tmp_path)


def test_parse_programs_yaml_extracts_modules(tmp_path: Path):
    pyaml = tmp_path / "programs.yaml"
    pyaml.write_text(
        """schema_version: 1
programs:
  - id: P1
    name: Auth platform
    sub_programs:
      - id: SP1
        name: Identity
        modules:
          - id: M1
            name: OAuth
            paths: [src/auth/oauth/]
            granularity: requirement
            structure: flat
visibility:
  - from: P1.SP1.M1
    to: []
"""
    )
    parsed = parse_programs_yaml(pyaml)
    assert parsed.programs[0].id == "P1"
    assert parsed.programs[0].sub_programs[0].id == "SP1"
    assert parsed.programs[0].sub_programs[0].modules[0].id == "M1"
    assert parsed.programs[0].sub_programs[0].modules[0].paths == ["src/auth/oauth/"]
    assert parsed.programs[0].sub_programs[0].modules[0].granularity == "requirement"


def test_parse_programs_yaml_raises_on_missing_schema_version(tmp_path: Path):
    pyaml = tmp_path / "programs.yaml"
    pyaml.write_text("programs: []\n")
    with pytest.raises(DecompositionParseError):
        parse_programs_yaml(pyaml)


def test_default_decomposition_is_p1_sp1_m1():
    parsed = default_decomposition(project_root_paths=["."])
    assert parsed.programs[0].id == "P1"
    assert parsed.programs[0].sub_programs[0].id == "SP1"
    assert parsed.programs[0].sub_programs[0].modules[0].id == "M1"
    assert parsed.programs[0].sub_programs[0].modules[0].paths == ["."]


def test_req_has_module_assignment_passes_when_frontmatter_declared():
    spec = SpecArtefact(
        path="docs/specs/auth/requirements-spec.md",
        feature_id="auth",
        module="P1.SP1.M1",
        ids=["REQ-auth-001"],
    )
    decomp = default_decomposition()
    result = req_has_module_assignment([spec], decomp)
    assert result.passed is True


def test_req_has_module_assignment_passes_when_positional_id_used():
    spec = SpecArtefact(
        path="docs/specs/auth/requirements-spec.md",
        feature_id=None,
        module=None,
        ids=["P1.SP1.M1.REQ-001"],
    )
    decomp = default_decomposition()
    result = req_has_module_assignment([spec], decomp)
    assert result.passed is True


def test_req_has_module_assignment_fails_when_module_undeclared():
    spec = SpecArtefact(
        path="docs/specs/auth/requirements-spec.md",
        feature_id="auth",
        module="P9.SP9.M9",  # not in decomposition
        ids=["REQ-auth-001"],
    )
    decomp = default_decomposition()
    result = req_has_module_assignment([spec], decomp)
    assert result.passed is False
    assert any("P9.SP9.M9" in e for e in result.errors)


def test_code_annotation_maps_to_module_passes_when_path_under_module():
    annotation = CodeAnnotation(
        file_path="src/auth/oauth/login.py",
        line=42,
        cited_ids=["REQ-auth-001"],
    )
    decomp = parse_programs_yaml_inline(
        """schema_version: 1
programs:
  - id: P1
    name: Auth
    sub_programs:
      - id: SP1
        name: Identity
        modules:
          - id: M1
            name: OAuth
            paths: [src/auth/oauth/]
            granularity: requirement
            structure: flat
"""
    )
    spec_lookup = {"REQ-auth-001": "P1.SP1.M1"}
    result = code_annotation_maps_to_module([annotation], decomp, spec_lookup)
    assert result.passed is True


def test_code_annotation_maps_to_module_fails_when_path_outside_module():
    annotation = CodeAnnotation(
        file_path="src/payments/charge.py",
        line=10,
        cited_ids=["REQ-auth-001"],
    )
    decomp = parse_programs_yaml_inline(
        """schema_version: 1
programs:
  - id: P1
    name: Auth
    sub_programs:
      - id: SP1
        name: Identity
        modules:
          - id: M1
            name: OAuth
            paths: [src/auth/oauth/]
            granularity: requirement
            structure: flat
"""
    )
    spec_lookup = {"REQ-auth-001": "P1.SP1.M1"}
    result = code_annotation_maps_to_module([annotation], decomp, spec_lookup)
    assert result.passed is False
    assert any("src/payments/charge.py" in e for e in result.errors)
