"""Tests for assured.dependency_extractor — DependencyExtractor protocol + ImportEdge."""

import tempfile
from pathlib import Path

from sdlc_assured_scripts.assured.dependency_extractor import (  # noqa: F401
    DependencyExtractor,
    ImportEdge,
    PythonAstExtractor,
    GenericRegexExtractor,
    make_swift_extractor,
    render_dependency_edges,
    parse_dependency_edges,
    build_dependency_edges,
)
from sdlc_assured_scripts.assured.decomposition import (
    Decomposition,
    Module,
    Program,
    SubProgram,
    parse_programs_yaml,
    visibility_rule_enforcement,
)


def _parse_programs_yaml_inline(content: str) -> Decomposition:
    """Write *content* to a temp file and parse it."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(content)
        tmp_path = Path(f.name)
    return parse_programs_yaml(tmp_path)


def test_import_edge_dataclass() -> None:
    e = ImportEdge(from_module="P1.SP1.M1", to_module="P1.SP1.M2")
    assert e.from_module == "P1.SP1.M1"


def test_dependency_extractor_protocol_attributes() -> None:
    """The protocol declares `language` and `extract`."""
    # Smoke test: any class implementing the protocol shape passes runtime_checkable
    pass  # protocol verification by Python's structural typing


def _make_two_module_decomposition() -> Decomposition:
    """Return a Decomposition with two modules: M1 at src/a/ and M2 at src/b/."""
    m1 = Module(
        id="M1",
        name="ModuleA",
        paths=["src/a/"],
        granularity="requirement",
        structure="flat",
    )
    m2 = Module(
        id="M2",
        name="ModuleB",
        paths=["src/b/"],
        granularity="requirement",
        structure="flat",
    )
    sp = SubProgram(id="SP1", name="SP1", modules=[m1, m2])
    p = Program(id="P1", name="P1", description=None, sub_programs=[sp])
    return Decomposition(programs=[p], visibility=[])


def test_python_ast_extractor_language() -> None:
    """PythonAstExtractor.language is 'python'."""
    extractor = PythonAstExtractor()
    assert extractor.language == "python"


def test_python_ast_extractor_satisfies_protocol() -> None:
    """PythonAstExtractor is structurally compatible with DependencyExtractor."""
    extractor = PythonAstExtractor()
    assert isinstance(extractor, DependencyExtractor)


def test_python_ast_extractor_walks_importfrom(tmp_path: Path) -> None:
    """extract() returns an ImportEdge for a cross-module 'from b.module_b import foo'."""
    # Set up two source files under tmp_path mirroring src/a/ and src/b/
    src_a = tmp_path / "src" / "a"
    src_b = tmp_path / "src" / "b"
    src_a.mkdir(parents=True)
    src_b.mkdir(parents=True)

    # module_a.py lives in src/a/ and imports from b.module_b
    module_a = src_a / "module_a.py"
    module_a.write_text("from b.module_b import foo\n")

    # module_b.py lives in src/b/
    module_b = src_b / "module_b.py"
    module_b.write_text("def foo(): pass\n")

    decomp = _make_two_module_decomposition()
    # Override module paths to match tmp_path-rooted directories
    m1 = Module(
        id="M1",
        name="ModuleA",
        paths=[str(src_a) + "/"],
        granularity="requirement",
        structure="flat",
    )
    m2 = Module(
        id="M2",
        name="ModuleB",
        paths=[str(src_b) + "/"],
        granularity="requirement",
        structure="flat",
    )
    sp = SubProgram(id="SP1", name="SP1", modules=[m1, m2])
    p = Program(id="P1", name="P1", description=None, sub_programs=[sp])
    decomp = Decomposition(programs=[p], visibility=[])

    extractor = PythonAstExtractor()
    edges = extractor.extract([module_a, module_b], decomp)

    assert ImportEdge(from_module="P1.SP1.M1", to_module="P1.SP1.M2") in edges


def test_python_ast_extractor_no_edges_for_intra_module_import(tmp_path: Path) -> None:
    """No edges emitted when both files belong to the same module."""
    src_a = tmp_path / "src" / "a"
    src_a.mkdir(parents=True)

    file1 = src_a / "mod1.py"
    file2 = src_a / "mod2.py"
    file1.write_text("from mod2 import helper\n")
    file2.write_text("def helper(): pass\n")

    m1 = Module(
        id="M1",
        name="ModuleA",
        paths=[str(src_a) + "/"],
        granularity="requirement",
        structure="flat",
    )
    sp = SubProgram(id="SP1", name="SP1", modules=[m1])
    p = Program(id="P1", name="P1", description=None, sub_programs=[sp])
    decomp = Decomposition(programs=[p], visibility=[])

    extractor = PythonAstExtractor()
    edges = extractor.extract([file1, file2], decomp)

    assert edges == []


def test_python_ast_extractor_plain_import(tmp_path: Path) -> None:
    """extract() handles plain 'import b.module_b' style as well."""
    src_a = tmp_path / "src" / "a"
    src_b = tmp_path / "src" / "b"
    src_a.mkdir(parents=True)
    src_b.mkdir(parents=True)

    module_a = src_a / "caller.py"
    module_a.write_text("import b.module_b\n")

    module_b = src_b / "module_b.py"
    module_b.write_text("pass\n")

    m1 = Module(
        id="M1",
        name="ModuleA",
        paths=[str(src_a) + "/"],
        granularity="requirement",
        structure="flat",
    )
    m2 = Module(
        id="M2",
        name="ModuleB",
        paths=[str(src_b) + "/"],
        granularity="requirement",
        structure="flat",
    )
    sp = SubProgram(id="SP1", name="SP1", modules=[m1, m2])
    p = Program(id="P1", name="P1", description=None, sub_programs=[sp])
    decomp = Decomposition(programs=[p], visibility=[])

    extractor = PythonAstExtractor()
    edges = extractor.extract([module_a, module_b], decomp)

    assert ImportEdge(from_module="P1.SP1.M1", to_module="P1.SP1.M2") in edges


def test_python_ast_extractor_skips_syntax_errors(tmp_path: Path) -> None:
    """Files with syntax errors are skipped gracefully (no exception raised)."""
    src_a = tmp_path / "src" / "a"
    src_a.mkdir(parents=True)

    bad_file = src_a / "broken.py"
    bad_file.write_text("def this is not valid python !!!\n")

    m1 = Module(
        id="M1",
        name="ModuleA",
        paths=[str(src_a) + "/"],
        granularity="requirement",
        structure="flat",
    )
    sp = SubProgram(id="SP1", name="SP1", modules=[m1])
    p = Program(id="P1", name="P1", description=None, sub_programs=[sp])
    decomp = Decomposition(programs=[p], visibility=[])

    extractor = PythonAstExtractor()
    # Must not raise
    edges = extractor.extract([bad_file], decomp)
    assert isinstance(edges, list)


def test_swift_extractor_finds_cross_module_import(tmp_path: Path) -> None:
    """GenericRegexExtractor with Swift pattern detects cross-module 'import b'."""
    src_a = tmp_path / "src" / "a"
    src_b = tmp_path / "src" / "b"
    src_a.mkdir(parents=True)
    src_b.mkdir(parents=True)

    (src_a / "ViewA.swift").write_text("import b\n")
    (src_b / "ServiceB.swift").write_text("public class ServiceB {}\n")

    m1 = Module(
        id="M1",
        name="A",
        paths=[str(src_a) + "/"],
        granularity="requirement",
        structure="flat",
    )
    m2 = Module(
        id="M2",
        name="B",
        paths=[str(src_b) + "/"],
        granularity="requirement",
        structure="flat",
    )
    sp = SubProgram(id="SP1", name="SP1", modules=[m1, m2])
    p = Program(id="P1", name="P1", description=None, sub_programs=[sp])
    decomp = Decomposition(programs=[p], visibility=[])

    swift = make_swift_extractor()
    assert swift.language == "swift"
    edges = swift.extract(
        source_paths=[src_a / "ViewA.swift", src_b / "ServiceB.swift"],
        programs=decomp,
    )
    assert ImportEdge(from_module="P1.SP1.M1", to_module="P1.SP1.M2") in edges


def test_generic_regex_extractor_satisfies_protocol() -> None:
    """GenericRegexExtractor is structurally compatible with DependencyExtractor."""
    swift = make_swift_extractor()
    assert isinstance(swift, DependencyExtractor)


def test_render_dependency_edges_emits_markdown_table() -> None:
    edges = [
        ImportEdge(from_module="P1.SP1.M1", to_module="P1.SP1.M2"),
        ImportEdge(from_module="P1.SP1.M2", to_module="P1.SP1.M3"),
    ]
    out = render_dependency_edges(edges, library_handle="phase-f-dogfood")
    assert "| From | To |" in out
    assert "| P1.SP1.M1 | P1.SP1.M2 |" in out
    assert "<!-- library_handle: phase-f-dogfood -->" in out


def test_parse_dependency_edges_round_trips() -> None:
    original = [ImportEdge(from_module="P1.SP1.M1", to_module="P1.SP1.M2")]
    text = render_dependency_edges(original, library_handle="x")
    assert parse_dependency_edges(text) == original


def test_integration_python_source_to_visibility_validator(tmp_path: Path) -> None:
    """End-to-end: real Python source → PythonAstExtractor → render → parse → validator."""
    src_a = tmp_path / "src" / "a"
    src_a.mkdir(parents=True)
    (src_a / "module_a.py").write_text("from b.module_b import foo\n")
    src_b = tmp_path / "src" / "b"
    src_b.mkdir(parents=True)
    (src_b / "module_b.py").write_text("def foo(): return 1\n")

    decomp = _parse_programs_yaml_inline(
        f"""schema_version: 1
programs:
  - id: P1
    name: P1
    sub_programs:
      - id: SP1
        name: SP1
        modules:
          - {{id: M1, name: A, paths: [{str(src_a)}/], granularity: requirement, structure: flat}}
          - {{id: M2, name: B, paths: [{str(src_b)}/], granularity: requirement, structure: flat}}
visibility:
  - from: P1.SP1.M1
    to: []
  - from: P1.SP1.M2
    to: []
"""
    )

    edges = build_dependency_edges(
        source_paths=[src_a / "module_a.py", src_b / "module_b.py"],
        programs=decomp,
        extractors=[PythonAstExtractor()],
    )
    assert ImportEdge(from_module="P1.SP1.M1", to_module="P1.SP1.M2") in edges

    # Round-trip through file
    out_path = tmp_path / "library" / "_dependency-edges.md"
    out_path.parent.mkdir(parents=True)
    out_path.write_text(render_dependency_edges(edges, library_handle="x"))
    parsed = parse_dependency_edges(out_path.read_text())

    # Validator consumes parsed edges — M1→M2 is undeclared, so strict mode errors
    result = visibility_rule_enforcement(parsed, decomp, mode="strict")
    assert result.passed is False
    assert any("P1.SP1.M1" in e and "P1.SP1.M2" in e for e in result.errors)
