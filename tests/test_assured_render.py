"""Tests for assured.render — module-scoped traceability render."""

from sdlc_assured_scripts.assured.code_index import CodeIndexEntry
from sdlc_assured_scripts.assured.decomposition import (
    Decomposition,
    ImportEdge,
    Module,
    Program,
    SubProgram,
    VisibilityRule,
)
from sdlc_assured_scripts.assured.ids import IdRecord
from sdlc_assured_scripts.assured.render import (
    render_module_dependency_graph,
    render_module_scope,
)


def test_render_module_scope_includes_reqs_des_tests_code():
    records = [
        IdRecord(
            id="REQ-auth-001",
            kind="REQ",
            source="docs/specs/auth/requirements-spec.md",
            satisfies=[],
        ),
        IdRecord(
            id="DES-auth-001",
            kind="DES",
            source="docs/specs/auth/design-spec.md",
            satisfies=["REQ-auth-001"],
        ),
        IdRecord(
            id="TEST-auth-001",
            kind="TEST",
            source="docs/specs/auth/test-spec.md",
            satisfies=["REQ-auth-001", "DES-auth-001"],
        ),
    ]
    code_entries = [
        CodeIndexEntry(
            file_path="src/auth/login.py", line=10, cited_ids=["REQ-auth-001"]
        ),
    ]
    spec_module_lookup = {
        "REQ-auth-001": "P1.SP1.M1",
        "DES-auth-001": "P1.SP1.M1",
        "TEST-auth-001": "P1.SP1.M1",
    }
    output = render_module_scope(
        module_id="P1.SP1.M1",
        records=records,
        code_entries=code_entries,
        spec_module_lookup=spec_module_lookup,
    )
    assert "# Module: P1.SP1.M1" in output
    assert "## Requirements" in output
    assert "REQ-auth-001" in output
    assert "## Designs" in output
    assert "DES-auth-001" in output
    assert "## Tests" in output
    assert "TEST-auth-001" in output
    assert "## Code" in output
    assert "src/auth/login.py:10" in output


def test_render_module_scope_flags_orphan_code():
    records = []
    code_entries = [
        CodeIndexEntry(
            file_path="src/auth/orphan.py", line=5, cited_ids=["REQ-auth-999"]
        ),
    ]
    spec_module_lookup = {}
    output = render_module_scope(
        module_id="P1.SP1.M1",
        records=records,
        code_entries=code_entries,
        spec_module_lookup=spec_module_lookup,
    )
    assert "## Orphan code" in output
    assert "src/auth/orphan.py:5" in output


def _two_module_decomp() -> Decomposition:
    m1 = Module(
        id="M1",
        name="M1",
        paths=["src/a/"],
        granularity="requirement",
        structure="flat",
    )
    m2 = Module(
        id="M2",
        name="M2",
        paths=["src/b/"],
        granularity="requirement",
        structure="flat",
    )
    sp = SubProgram(id="SP1", name="SP1", modules=[m1, m2])
    p = Program(id="P1", name="P1", description=None, sub_programs=[sp])
    visibility = [VisibilityRule(from_module="P1.SP1.M1", to_modules=["P1.SP1.M2"])]
    return Decomposition(programs=[p], visibility=visibility)


def test_render_module_dependency_graph_lists_each_actual_edge():
    decomp = _two_module_decomp()
    actual_edges = [
        ImportEdge(from_module="P1.SP1.M1", to_module="P1.SP1.M2"),
        ImportEdge(from_module="P1.SP1.M2", to_module="P1.SP1.M1"),  # disallowed
    ]
    output = render_module_dependency_graph(decomp, actual_edges)
    assert "| From | → | To | Allowed? |" in output
    assert "| P1.SP1.M1 | → | P1.SP1.M2 | yes |" in output
    assert "| P1.SP1.M2 | → | P1.SP1.M1 | NO |" in output


def test_render_module_dependency_graph_handles_zero_edges():
    decomp = _two_module_decomp()
    output = render_module_dependency_graph(decomp, [])
    assert "_(no module-to-module dependencies detected)_" in output
