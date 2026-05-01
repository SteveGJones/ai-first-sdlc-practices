"""Tests for assured.decomposition — programs.yaml schema + validators."""

from pathlib import Path

import pytest

from sdlc_assured_scripts.assured.decomposition import (
    CodeAnnotation,
    Decomposition,
    DecompositionParseError,
    ImportEdge,
    Module,
    PathSection,
    Program,
    SpecArtefact,
    SubProgram,
    anaemic_context_detection,
    code_annotation_maps_to_module,
    default_decomposition,
    forward_annotation_completeness,
    granularity_match,
    parse_programs_yaml,
    req_has_module_assignment,
    visibility_rule_enforcement,
)


def parse_programs_yaml_inline(content: str) -> Decomposition:
    import tempfile
    from pathlib import Path as _Path

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(content)
        tmp_path = _Path(f.name)
    return parse_programs_yaml(tmp_path)


def test_parse_programs_yaml_extracts_modules(tmp_path: Path) -> None:
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


def test_parse_programs_yaml_raises_on_missing_schema_version(tmp_path: Path) -> None:
    pyaml = tmp_path / "programs.yaml"
    pyaml.write_text("programs: []\n")
    with pytest.raises(DecompositionParseError):
        parse_programs_yaml(pyaml)


def test_default_decomposition_is_p1_sp1_m1() -> None:
    parsed = default_decomposition(project_root_paths=["."])
    assert parsed.programs[0].id == "P1"
    assert parsed.programs[0].sub_programs[0].id == "SP1"
    assert parsed.programs[0].sub_programs[0].modules[0].id == "M1"
    assert parsed.programs[0].sub_programs[0].modules[0].paths == ["."]


def test_req_has_module_assignment_passes_when_frontmatter_declared() -> None:
    spec = SpecArtefact(
        path="docs/specs/auth/requirements-spec.md",
        feature_id="auth",
        module="P1.SP1.M1",
        ids=["REQ-auth-001"],
    )
    decomp = default_decomposition()
    result = req_has_module_assignment([spec], decomp)
    assert result.passed is True


def test_req_has_module_assignment_passes_when_positional_id_used() -> None:
    spec = SpecArtefact(
        path="docs/specs/auth/requirements-spec.md",
        feature_id=None,
        module=None,
        ids=["P1.SP1.M1.REQ-001"],
    )
    decomp = default_decomposition()
    result = req_has_module_assignment([spec], decomp)
    assert result.passed is True


def test_req_has_module_assignment_fails_when_module_undeclared() -> None:
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


def test_code_annotation_maps_to_module_passes_when_path_under_module() -> None:
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


def test_code_annotation_maps_to_module_fails_when_path_outside_module() -> None:
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


def test_visibility_rule_enforcement_passes_when_edge_declared() -> None:
    edges = [ImportEdge(from_module="P1.SP1.M1", to_module="P1.SP1.M2")]
    decomp = parse_programs_yaml_inline(
        """schema_version: 1
programs:
  - id: P1
    name: P1
    sub_programs:
      - id: SP1
        name: SP1
        modules:
          - {id: M1, name: M1, paths: [src/a/], granularity: requirement, structure: flat}
          - {id: M2, name: M2, paths: [src/b/], granularity: requirement, structure: flat}
visibility:
  - from: P1.SP1.M1
    to: [P1.SP1.M2]
"""
    )
    result = visibility_rule_enforcement(edges, decomp, mode="strict")
    assert result.passed is True


def test_visibility_rule_enforcement_fails_when_edge_undeclared_in_strict_mode() -> (
    None
):
    edges = [ImportEdge(from_module="P1.SP1.M2", to_module="P1.SP1.M1")]
    decomp = parse_programs_yaml_inline(
        """schema_version: 1
programs:
  - id: P1
    name: P1
    sub_programs:
      - id: SP1
        name: SP1
        modules:
          - {id: M1, name: M1, paths: [src/a/], granularity: requirement, structure: flat}
          - {id: M2, name: M2, paths: [src/b/], granularity: requirement, structure: flat}
visibility:
  - from: P1.SP1.M1
    to: [P1.SP1.M2]
"""
    )
    result = visibility_rule_enforcement(edges, decomp, mode="strict")
    assert result.passed is False
    assert any("P1.SP1.M2" in e and "P1.SP1.M1" in e for e in result.errors)


def test_visibility_rule_enforcement_warns_in_advisory_mode() -> None:
    edges = [ImportEdge(from_module="P1.SP1.M2", to_module="P1.SP1.M1")]
    decomp = parse_programs_yaml_inline(
        """schema_version: 1
programs:
  - id: P1
    name: P1
    sub_programs:
      - id: SP1
        name: SP1
        modules:
          - {id: M1, name: M1, paths: [src/a/], granularity: requirement, structure: flat}
          - {id: M2, name: M2, paths: [src/b/], granularity: requirement, structure: flat}
visibility:
  - from: P1.SP1.M1
    to: [P1.SP1.M2]
"""
    )
    result = visibility_rule_enforcement(edges, decomp, mode="advisory")
    assert result.passed is True
    assert any("P1.SP1.M2" in w and "P1.SP1.M1" in w for w in result.warnings)


def test_anaemic_context_passes_when_code_co_located() -> None:
    annotations = [
        CodeAnnotation(
            file_path="src/auth/oauth/login.py", line=10, cited_ids=["REQ-auth-001"]
        ),
        CodeAnnotation(
            file_path="src/auth/oauth/refresh.py", line=20, cited_ids=["REQ-auth-002"]
        ),
    ]
    spec_lookup = {"REQ-auth-001": "P1.SP1.M1", "REQ-auth-002": "P1.SP1.M1"}
    decomp = parse_programs_yaml_inline(
        """schema_version: 1
programs:
  - id: P1
    name: P1
    sub_programs:
      - id: SP1
        name: SP1
        modules:
          - {id: M1, name: OAuth, paths: [src/auth/oauth/], granularity: requirement, structure: flat}
"""
    )
    result = anaemic_context_detection(annotations, decomp, spec_lookup)
    assert result.passed is True


def test_anaemic_context_fails_when_code_scattered() -> None:
    """Two REQs from the same module, but their code lives under different module paths.

    1 inside, 1 outside = 50% scatter — exceeds the 20% default threshold.
    """
    annotations = [
        CodeAnnotation(
            file_path="src/auth/oauth/login.py", line=10, cited_ids=["REQ-auth-001"]
        ),
        CodeAnnotation(
            file_path="src/payments/charge.py", line=20, cited_ids=["REQ-auth-002"]
        ),
    ]
    spec_lookup = {"REQ-auth-001": "P1.SP1.M1", "REQ-auth-002": "P1.SP1.M1"}
    decomp = parse_programs_yaml_inline(
        """schema_version: 1
programs:
  - id: P1
    name: P1
    sub_programs:
      - id: SP1
        name: SP1
        modules:
          - {id: M1, name: OAuth, paths: [src/auth/oauth/], granularity: requirement, structure: flat}
"""
    )
    result = anaemic_context_detection(annotations, decomp, spec_lookup)
    assert result.passed is False
    assert any("50%" in e for e in result.errors)


def test_anaemic_context_passes_with_single_outlier_below_threshold() -> None:
    """One outlier in five annotations (20% scatter) does NOT trigger anaemia.

    A single stray annotation is an outlier, not systemic anaemia.
    Default threshold is >20%, so exactly 20% passes.
    """
    decomp = parse_programs_yaml_inline(
        """schema_version: 1
programs:
  - id: P1
    name: P1
    sub_programs:
      - id: SP1
        name: SP1
        modules:
          - {id: M1, name: OAuth, paths: [src/auth/oauth/], granularity: requirement, structure: flat}
"""
    )
    spec_lookup = {
        "REQ-auth-001": "P1.SP1.M1",
        "REQ-auth-002": "P1.SP1.M1",
        "REQ-auth-003": "P1.SP1.M1",
        "REQ-auth-004": "P1.SP1.M1",
        "REQ-auth-005": "P1.SP1.M1",
    }
    # 4 inside, 1 outside = 20% scatter (not > 20%, so should pass).
    annotations = [
        CodeAnnotation(
            file_path="src/auth/oauth/a.py", line=1, cited_ids=["REQ-auth-001"]
        ),
        CodeAnnotation(
            file_path="src/auth/oauth/b.py", line=1, cited_ids=["REQ-auth-002"]
        ),
        CodeAnnotation(
            file_path="src/auth/oauth/c.py", line=1, cited_ids=["REQ-auth-003"]
        ),
        CodeAnnotation(
            file_path="src/auth/oauth/d.py", line=1, cited_ids=["REQ-auth-004"]
        ),
        CodeAnnotation(
            file_path="src/payments/stray.py", line=1, cited_ids=["REQ-auth-005"]
        ),
    ]
    result = anaemic_context_detection(annotations, decomp, spec_lookup)
    assert result.passed is True


def test_anaemic_context_fails_above_threshold() -> None:
    """More than 20% scatter triggers anaemia (5 inside, 2 outside = ~29%)."""
    decomp = parse_programs_yaml_inline(
        """schema_version: 1
programs:
  - id: P1
    name: P1
    sub_programs:
      - id: SP1
        name: SP1
        modules:
          - {id: M1, name: OAuth, paths: [src/auth/oauth/], granularity: requirement, structure: flat}
"""
    )
    spec_lookup = {f"REQ-auth-{i:03d}": "P1.SP1.M1" for i in range(1, 8)}
    annotations = [
        CodeAnnotation(
            file_path="src/auth/oauth/a.py", line=1, cited_ids=["REQ-auth-001"]
        ),
        CodeAnnotation(
            file_path="src/auth/oauth/b.py", line=1, cited_ids=["REQ-auth-002"]
        ),
        CodeAnnotation(
            file_path="src/auth/oauth/c.py", line=1, cited_ids=["REQ-auth-003"]
        ),
        CodeAnnotation(
            file_path="src/auth/oauth/d.py", line=1, cited_ids=["REQ-auth-004"]
        ),
        CodeAnnotation(
            file_path="src/auth/oauth/e.py", line=1, cited_ids=["REQ-auth-005"]
        ),
        CodeAnnotation(
            file_path="src/payments/x.py", line=1, cited_ids=["REQ-auth-006"]
        ),
        CodeAnnotation(
            file_path="src/payments/y.py", line=1, cited_ids=["REQ-auth-007"]
        ),
    ]
    result = anaemic_context_detection(annotations, decomp, spec_lookup)
    assert result.passed is False
    assert any("module P1.SP1.M1" in e for e in result.errors)


def test_anaemic_context_custom_threshold() -> None:
    """Custom threshold of 0.50 ignores minor scatter."""
    decomp = parse_programs_yaml_inline(
        """schema_version: 1
programs:
  - id: P1
    name: P1
    sub_programs:
      - id: SP1
        name: SP1
        modules:
          - {id: M1, name: OAuth, paths: [src/auth/oauth/], granularity: requirement, structure: flat}
"""
    )
    spec_lookup = {"REQ-auth-001": "P1.SP1.M1", "REQ-auth-002": "P1.SP1.M1"}
    annotations = [
        CodeAnnotation(
            file_path="src/auth/oauth/login.py", line=10, cited_ids=["REQ-auth-001"]
        ),
        CodeAnnotation(
            file_path="src/payments/charge.py", line=20, cited_ids=["REQ-auth-002"]
        ),
    ]
    # 50% scatter but threshold set to >50%, so should pass.
    result = anaemic_context_detection(
        annotations, decomp, spec_lookup, scatter_threshold=0.50
    )
    assert result.passed is True


def test_granularity_match_passes_when_each_req_has_annotation() -> None:
    declared_reqs = ["REQ-auth-001", "REQ-auth-002"]
    annotations = [
        CodeAnnotation(
            file_path="src/auth/oauth/login.py", line=10, cited_ids=["REQ-auth-001"]
        ),
        CodeAnnotation(
            file_path="src/auth/oauth/refresh.py", line=20, cited_ids=["REQ-auth-002"]
        ),
    ]
    spec_lookup = {"REQ-auth-001": "P1.SP1.M1", "REQ-auth-002": "P1.SP1.M1"}
    decomp = parse_programs_yaml_inline(
        """schema_version: 1
programs:
  - id: P1
    name: P1
    sub_programs:
      - id: SP1
        name: SP1
        modules:
          - {id: M1, name: OAuth, paths: [src/auth/oauth/], granularity: requirement, structure: flat}
"""
    )
    result = granularity_match(
        declared_reqs, annotations, decomp, spec_lookup, satisfies_graph={}
    )
    assert result.passed is True


def test_granularity_match_warns_when_req_under_specified() -> None:
    declared_reqs = ["REQ-auth-001", "REQ-auth-002"]
    annotations = [
        CodeAnnotation(
            file_path="src/auth/oauth/login.py", line=10, cited_ids=["REQ-auth-001"]
        ),
    ]
    spec_lookup = {"REQ-auth-001": "P1.SP1.M1", "REQ-auth-002": "P1.SP1.M1"}
    decomp = parse_programs_yaml_inline(
        """schema_version: 1
programs:
  - id: P1
    name: P1
    sub_programs:
      - id: SP1
        name: SP1
        modules:
          - {id: M1, name: OAuth, paths: [src/auth/oauth/], granularity: requirement, structure: flat}
"""
    )
    result = granularity_match(
        declared_reqs, annotations, decomp, spec_lookup, satisfies_graph={}
    )
    assert result.passed is True
    assert any("REQ-auth-002" in w for w in result.warnings)


# ---------------------------------------------------------------------------
# F-002: paths_sections named-anchor scoping
# ---------------------------------------------------------------------------


def test_paths_sections_round_trip(tmp_path: Path) -> None:
    """paths_sections entries survive a parse round-trip with correct values."""
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
            paths_sections:
              - file: docs/specs/auth/design-spec.md
                anchor: "### MODE: SYNTHESISE-ACROSS-SPEC-TYPES"
              - file: docs/specs/auth/requirements-spec.md
                anchor: "## Requirements"
"""
    )
    parsed = parse_programs_yaml(pyaml)
    module = parsed.programs[0].sub_programs[0].modules[0]
    assert len(module.paths_sections) == 2
    assert module.paths_sections[0] == PathSection(
        file="docs/specs/auth/design-spec.md",
        anchor="### MODE: SYNTHESISE-ACROSS-SPEC-TYPES",
    )
    assert module.paths_sections[1] == PathSection(
        file="docs/specs/auth/requirements-spec.md",
        anchor="## Requirements",
    )


def test_paths_sections_defaults_to_empty_list(tmp_path: Path) -> None:
    """A module with no paths_sections key yields an empty list (not None)."""
    pyaml = tmp_path / "programs.yaml"
    pyaml.write_text(
        """schema_version: 1
programs:
  - id: P1
    name: P1
    sub_programs:
      - id: SP1
        name: SP1
        modules:
          - id: M1
            name: M1
            paths: [src/]
            granularity: requirement
            structure: flat
"""
    )
    parsed = parse_programs_yaml(pyaml)
    module = parsed.programs[0].sub_programs[0].modules[0]
    assert module.paths_sections == []


def test_paths_sections_preserved_alongside_existing_fields(tmp_path: Path) -> None:
    """paths_sections does not disturb owner or other optional fields."""
    pyaml = tmp_path / "programs.yaml"
    pyaml.write_text(
        """schema_version: 1
programs:
  - id: P1
    name: P1
    sub_programs:
      - id: SP1
        name: SP1
        modules:
          - id: M1
            name: M1
            paths: [src/]
            granularity: function
            structure: hexagonal
            owner: team-auth
            paths_sections:
              - file: docs/design.md
                anchor: "## Overview"
"""
    )
    parsed = parse_programs_yaml(pyaml)
    module = parsed.programs[0].sub_programs[0].modules[0]
    assert module.owner == "team-auth"
    assert module.granularity == "function"
    assert module.structure == "hexagonal"
    assert len(module.paths_sections) == 1
    assert module.paths_sections[0].anchor == "## Overview"


# ---------------------------------------------------------------------------
# F-008: granularity_match indirect DES-mediated coverage
# ---------------------------------------------------------------------------


def test_granularity_match_indirect_coverage_via_des() -> None:
    """A REQ is covered if any satisfies-linked DES has annotation evidence (F-008)."""
    declared_reqs = ["REQ-foo-001"]
    # No annotation on REQ; one annotation on the satisfying DES
    annotations = [
        CodeAnnotation(file_path="src/foo.py", line=10, cited_ids=["DES-foo-001"]),
    ]
    decomp = parse_programs_yaml_inline(
        """schema_version: 1
programs:
  - id: P1
    name: P1
    sub_programs:
      - id: SP1
        name: SP1
        modules:
          - {id: M1, name: M1, paths: [src/], granularity: requirement, structure: flat}
"""
    )
    spec_lookup = {"REQ-foo-001": "P1.SP1.M1", "DES-foo-001": "P1.SP1.M1"}
    # NEW signature: needs the satisfies-graph
    satisfies_graph = {"DES-foo-001": ["REQ-foo-001"]}
    result = granularity_match(
        declared_reqs, annotations, decomp, spec_lookup, satisfies_graph
    )
    # Indirect coverage: REQ has no direct annotation but DES-foo-001 (which satisfies REQ-foo-001) does
    assert result.passed is True
    assert result.warnings == []  # NO under-specified warning


# ---------------------------------------------------------------------------
# E2: forward_annotation_completeness
# ---------------------------------------------------------------------------


def _decomp_for_path(src_dir: Path) -> Decomposition:
    """Build a minimal Decomposition whose single module covers src_dir."""
    module = Module(
        id="M1",
        name="Test module",
        paths=[str(src_dir)],
        granularity="requirement",
        structure="flat",
        paths_sections=[],
    )
    sub_program = SubProgram(id="SP1", name="Test sub-program", modules=[module])
    program = Program(id="P1", name="Test program", description=None, sub_programs=[sub_program])
    return Decomposition(programs=[program], visibility=[])


def test_forward_annotation_completeness_passes_when_all_public_functions_annotated(
    tmp_path: Path,
) -> None:
    f = tmp_path / "src" / "auth.py"
    f.parent.mkdir(parents=True)
    f.write_text(
        "def login(token):\n"
        "    # implements: DES-auth-001\n"
        "    return token\n"
    )
    decomp = _decomp_for_path(tmp_path / "src")
    result = forward_annotation_completeness(source_paths=[f], decomp=decomp)
    assert result.passed is True


def test_forward_annotation_completeness_fails_when_public_function_missing_annotation(
    tmp_path: Path,
) -> None:
    f = tmp_path / "src" / "auth.py"
    f.parent.mkdir(parents=True)
    f.write_text(
        "def login(token):\n"
        "    return token\n"
    )
    decomp = _decomp_for_path(tmp_path / "src")
    result = forward_annotation_completeness(source_paths=[f], decomp=decomp)
    assert result.passed is False
    assert any("login" in e for e in result.errors)


def test_forward_annotation_completeness_skips_dunder_methods(
    tmp_path: Path,
) -> None:
    f = tmp_path / "src" / "auth.py"
    f.parent.mkdir(parents=True)
    f.write_text(
        "class Auth:\n"
        "    def __init__(self):\n"
        "        self.x = 1\n"
        "    def __repr__(self):\n"
        "        return 'Auth'\n"
    )
    decomp = _decomp_for_path(tmp_path / "src")
    result = forward_annotation_completeness(source_paths=[f], decomp=decomp)
    assert result.passed is True
    assert result.errors == []


def test_forward_annotation_completeness_skips_test_files(
    tmp_path: Path,
) -> None:
    f = tmp_path / "src" / "test_auth.py"
    f.parent.mkdir(parents=True)
    f.write_text(
        "def test_login():\n"
        "    assert True\n"
    )
    decomp = _decomp_for_path(tmp_path / "src")
    result = forward_annotation_completeness(source_paths=[f], decomp=decomp)
    assert result.passed is True
    assert result.errors == []


def test_forward_annotation_completeness_skips_property_decorated_single_line(
    tmp_path: Path,
) -> None:
    f = tmp_path / "src" / "auth.py"
    f.parent.mkdir(parents=True)
    f.write_text(
        "class Auth:\n"
        "    @property\n"
        "    def token(self):\n"
        "        return self._token\n"
    )
    decomp = _decomp_for_path(tmp_path / "src")
    result = forward_annotation_completeness(source_paths=[f], decomp=decomp)
    assert result.passed is True
    assert result.errors == []
