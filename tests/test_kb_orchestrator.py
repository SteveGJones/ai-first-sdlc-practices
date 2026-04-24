"""Integration tests for the kb-query orchestrator.

Uses a mock dispatcher to exercise the full flow without real Agent tool calls.
"""
import json
from pathlib import Path
from sdlc_knowledge_base_scripts.orchestrator import (
    run_retrieval_query,
    RetrievalQueryResult,
    DispatchRequest,
    format_dispatch_prompt,
)
from sdlc_knowledge_base_scripts.registry import LibrarySource
from sdlc_knowledge_base_scripts.priming import PrimingBundle


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


def test_format_dispatch_prompt_with_full_priming() -> None:
    source = LibrarySource(name="corp-semi", type="filesystem", path="/lib/corp-semi")
    priming = PrimingBundle(
        question="what about EUV cleanroom",
        local_kb_config_excerpt="This project uses the knowledge base for semiconductor research.",
        local_shelf_index_terms=["semiconductor", "brazilian-fab", "alpha"],
    )
    prompt = format_dispatch_prompt(source=source, question="what about EUV cleanroom", priming=priming)

    assert "SCOPE: /lib/corp-semi" in prompt
    assert "SOURCE_HANDLE: corp-semi" in prompt
    assert "PRIMING_CONTEXT:" in prompt
    assert "semiconductor" in prompt
    assert "brazilian-fab" in prompt
    assert "This project uses the knowledge base" in prompt
    assert "what about EUV cleanroom" in prompt
    assert "---" in prompt and "horizontal rules inside a finding" in prompt


def test_format_dispatch_prompt_without_priming() -> None:
    source = LibrarySource(name="local", type="filesystem", path="/proj/library")
    prompt = format_dispatch_prompt(source=source, question="hello", priming=None)

    assert "SCOPE: /proj/library" in prompt
    assert "SOURCE_HANDLE: local" in prompt
    assert "PRIMING_CONTEXT:" not in prompt
    assert "hello" in prompt


def test_format_dispatch_prompt_with_empty_priming_bundle() -> None:
    source = LibrarySource(name="local", type="filesystem", path="/proj/library")
    priming = PrimingBundle(
        question="hello",
        local_kb_config_excerpt="",
        local_shelf_index_terms=[],
    )
    prompt = format_dispatch_prompt(source=source, question="hello", priming=priming)

    assert "SCOPE: /proj/library" in prompt
    assert "SOURCE_HANDLE: local" in prompt
    assert "PRIMING_CONTEXT:" in prompt
    assert '"local_kb_config_excerpt": ""' in prompt
    assert '"local_shelf_index_terms": []' in prompt


def test_format_dispatch_prompt_json_is_valid() -> None:
    import re
    source = LibrarySource(name="x", type="filesystem", path="/x")
    priming = PrimingBundle(
        question="q",
        local_kb_config_excerpt="line1\nline2",
        local_shelf_index_terms=["term-with-hyphen", "term with space"],
    )
    prompt = format_dispatch_prompt(source=source, question="q", priming=priming)
    match = re.search(r"PRIMING_CONTEXT:\s*\n(\{.*?\n\})", prompt, re.DOTALL)
    assert match is not None, f"PRIMING_CONTEXT JSON block not found in:\n{prompt}"
    parsed = json.loads(match.group(1))
    assert parsed["local_kb_config_excerpt"] == "line1\nline2"
    assert parsed["local_shelf_index_terms"] == ["term-with-hyphen", "term with space"]
