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


def test_orchestrator_passes_priming_bundle_to_dispatcher(tmp_path: Path) -> None:
    """Priming bundle built from a real project's local state must flow intact
    to each dispatcher invocation, with all fields preserved."""
    # Build a fake project directory with CLAUDE.md and a local library/_shelf-index.md
    proj_dir = tmp_path / "proj"
    proj_dir.mkdir()
    (proj_dir / "CLAUDE.md").write_text(
        "# CLAUDE.md\n\n"
        "## Knowledge Base\n\n"
        "This project uses the knowledge base for semiconductor research.\n"
    )
    local_lib = proj_dir / "library"
    local_lib.mkdir()
    (local_lib / "_shelf-index.md").write_text(
        "# Shelf Index\n\n"
        "## 1. local-topic.md\n"
        "**Terms:** semiconductor, brazilian-fab, alpha\n"
    )

    # Use the real priming builder, not a mock
    from sdlc_knowledge_base_scripts.priming import build_priming_bundle
    priming = build_priming_bundle(question="what about EUV", project_dir=proj_dir)

    # Verify the builder did its job
    assert "semiconductor research" in priming.local_kb_config_excerpt
    assert set(priming.local_shelf_index_terms) >= {"semiconductor", "brazilian-fab", "alpha"}

    # Capture every DispatchRequest the orchestrator passes to the dispatcher
    captured: list[DispatchRequest] = []

    def capturing_dispatcher(req: DispatchRequest) -> str:
        captured.append(req)
        return (
            f"### {req.source.name} finding\n"
            f"**Finding**: ok.\n"
            f"**Source library**: {req.source.name}\n"
        )

    sources = [
        LibrarySource(name="local", type="filesystem", path=str(local_lib)),
        LibrarySource(name="corp", type="filesystem", path=str(tmp_path / "corp" / "library")),
    ]
    # Make corp a real dir so the source preflight passes
    (tmp_path / "corp" / "library").mkdir(parents=True)

    result = run_retrieval_query(
        question="what about EUV",
        sources=sources,
        priming=priming,
        dispatcher=capturing_dispatcher,
    )

    # Both sources should have been dispatched with the SAME priming bundle
    assert len(captured) == 2
    for req in captured:
        assert req.priming is priming, (
            f"Dispatcher received a different priming bundle for source {req.source.name}"
        )
        assert req.priming.local_kb_config_excerpt == priming.local_kb_config_excerpt
        assert req.priming.local_shelf_index_terms == priming.local_shelf_index_terms

    # And the result should still be well-formed
    assert "local finding" in result.combined_output
    assert "corp finding" in result.combined_output


from sdlc_knowledge_base_scripts.orchestrator import is_synthesis_query


def test_is_synthesis_query_build_the_case() -> None:
    assert is_synthesis_query("build me the case for trunk-based development")
    assert is_synthesis_query("Build the case for adopting BDD")
    assert is_synthesis_query("BUILD ME THE CASE FOR TLA+")  # case-insensitive


def test_is_synthesis_query_how_should_we_think() -> None:
    assert is_synthesis_query("how should we think about cycle time?")
    assert is_synthesis_query("How should we think about EUV cleanrooms")


def test_is_synthesis_query_synthesise_phrases() -> None:
    assert is_synthesis_query("synthesise the evidence on TDD effectiveness")
    assert is_synthesis_query("synthesize what we know about DORA metrics")


def test_is_synthesis_query_retrieval_questions_return_false() -> None:
    assert not is_synthesis_query("what does our research say about cycle time")
    assert not is_synthesis_query("what is the deployment frequency threshold")
    assert not is_synthesis_query("list the evidence for TDD")
    assert not is_synthesis_query("show me the citations for trunk-based development")


def test_is_synthesis_query_empty_or_whitespace() -> None:
    assert not is_synthesis_query("")
    assert not is_synthesis_query("   ")
    assert not is_synthesis_query("\n\t")
