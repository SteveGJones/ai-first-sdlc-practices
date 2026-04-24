"""Integration tests for the kb-query orchestrator.

Uses a mock dispatcher to exercise the full flow without real Agent tool calls.
"""
import json
from pathlib import Path
from sdlc_knowledge_base_scripts.orchestrator import (
    run_retrieval_query,
    RetrievalQueryResult,
    DispatchRequest,
)
from sdlc_knowledge_base_scripts.registry import LibrarySource


def _make_fixture_library(root: Path, name: str, shelf_content: str) -> Path:
    lib_dir = root / name / "library"
    lib_dir.mkdir(parents=True)
    (lib_dir / "_shelf-index.md").write_text(shelf_content)
    return lib_dir


def test_orchestrator_dispatches_to_all_sources(tmp_path: Path) -> None:
    local_lib = _make_fixture_library(tmp_path, "proj", "<!-- format_version: 1 -->\n# Shelf\n")
    corp_lib = _make_fixture_library(tmp_path, "corp", "<!-- format_version: 1 -->\n# Shelf\n")

    dispatched: list[DispatchRequest] = []
    def mock_dispatch(req: DispatchRequest) -> str:
        dispatched.append(req)
        return (
            f"### {req.source.name} finding\n"
            f"**Finding**: something from {req.source.name}.\n"
            f"**Source library**: {req.source.name}\n"
        )

    sources = [
        LibrarySource(name="local", type="filesystem", path=str(local_lib)),
        LibrarySource(name="corp", type="filesystem", path=str(corp_lib)),
    ]
    result = run_retrieval_query(
        question="what about X",
        sources=sources,
        priming=None,  # phase A passes None; phase B wires the bundle
        dispatcher=mock_dispatch,
    )
    assert isinstance(result, RetrievalQueryResult)
    assert len(dispatched) == 2
    assert {r.source.name for r in dispatched} == {"local", "corp"}
    assert "local finding" in result.combined_output
    assert "corp finding" in result.combined_output
    assert result.sources_with_findings == ["local", "corp"]
    assert result.sources_failed == []


def test_orchestrator_source_failure_becomes_marker(tmp_path: Path) -> None:
    local_lib = _make_fixture_library(tmp_path, "proj", "<!-- format_version: 1 -->\n# Shelf\n")

    def mock_dispatch(req: DispatchRequest) -> str:
        if req.source.name == "corp":
            raise FileNotFoundError(f"shelf-index missing at {req.source.path}")
        return (
            f"### {req.source.name} finding\n"
            f"**Finding**: ok.\n"
            f"**Source library**: {req.source.name}\n"
        )

    sources = [
        LibrarySource(name="local", type="filesystem", path=str(local_lib)),
        LibrarySource(name="corp", type="filesystem", path=str(tmp_path / "nonexistent")),
    ]
    result = run_retrieval_query(
        question="q",
        sources=sources,
        priming=None,
        dispatcher=mock_dispatch,
    )
    assert result.sources_with_findings == ["local"]
    assert result.sources_failed == ["corp"]
    assert "[corp] dispatch failed" in result.combined_output
    assert "### local finding" in result.combined_output


def test_orchestrator_no_evidence_marker(tmp_path: Path) -> None:
    local_lib = _make_fixture_library(tmp_path, "proj", "<!-- format_version: 1 -->\n# Shelf\n")

    def mock_dispatch(req: DispatchRequest) -> str:
        # Librarian's anti-hallucination response
        return "The library has no evidence on this topic."

    sources = [LibrarySource(name="local", type="filesystem", path=str(local_lib))]
    result = run_retrieval_query(
        question="obscure",
        sources=sources,
        priming=None,
        dispatcher=mock_dispatch,
    )
    assert result.sources_with_findings == []
    assert result.sources_failed == []
    assert "[local] library has no evidence" in result.combined_output


def test_orchestrator_attribution_check_drops_untagged(tmp_path: Path) -> None:
    local_lib = _make_fixture_library(tmp_path, "proj", "<!-- format_version: 1 -->\n# Shelf\n")

    def mock_dispatch(req: DispatchRequest) -> str:
        # Return one tagged and one untagged finding
        return (
            "### Tagged\n"
            "**Finding**: ok.\n"
            "**Source library**: local\n\n"
            "### Untagged\n"
            "**Finding**: bad, no attribution.\n"
        )

    sources = [LibrarySource(name="local", type="filesystem", path=str(local_lib))]
    result = run_retrieval_query(
        question="q",
        sources=sources,
        priming=None,
        dispatcher=mock_dispatch,
    )
    assert "### Tagged" in result.combined_output
    assert "### Untagged" not in result.combined_output
    assert len(result.attribution_warnings) == 1


def test_orchestrator_output_ordering_local_first_externals_alpha(tmp_path: Path) -> None:
    libs = {n: _make_fixture_library(tmp_path, n, "<!-- format_version: 1 -->\n# Shelf\n")
            for n in ("proj", "zebra", "alpha", "mango")}

    def mock_dispatch(req: DispatchRequest) -> str:
        return (f"### {req.source.name}\n**Finding**: x.\n**Source library**: {req.source.name}\n")

    sources = [
        LibrarySource(name="local", type="filesystem", path=str(libs["proj"])),
        LibrarySource(name="zebra", type="filesystem", path=str(libs["zebra"])),
        LibrarySource(name="alpha", type="filesystem", path=str(libs["alpha"])),
        LibrarySource(name="mango", type="filesystem", path=str(libs["mango"])),
    ]
    result = run_retrieval_query(
        question="q", sources=sources, priming=None, dispatcher=mock_dispatch,
    )
    # local must appear before alpha, alpha before mango, mango before zebra
    out = result.combined_output
    assert out.index("### local") < out.index("### alpha") < out.index("### mango") < out.index("### zebra")
