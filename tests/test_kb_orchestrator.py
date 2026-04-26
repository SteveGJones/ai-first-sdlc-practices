"""Integration tests for the kb-query orchestrator.

Uses a mock dispatcher to exercise the full flow without real Agent tool calls.
"""
import json
import re
from pathlib import Path

from sdlc_knowledge_base_scripts.orchestrator import (
    DispatchRequest,
    RetrievalQueryResult,
    SynthesisQueryResult,
    format_dispatch_prompt,
    format_synthesis_prompt,
    is_synthesis_query,
    run_retrieval_query,
    run_synthesis_query,
)
from sdlc_knowledge_base_scripts.priming import PrimingBundle, build_priming_bundle
from sdlc_knowledge_base_scripts.registry import LibrarySource


def _make_fixture_library(root: Path, name: str, shelf_content: str) -> Path:
    lib_dir = root / name / "library"
    lib_dir.mkdir(parents=True)
    (lib_dir / "_shelf-index.md").write_text(shelf_content)
    return lib_dir


def test_orchestrator_dispatches_to_all_sources(tmp_path: Path) -> None:
    local_lib = _make_fixture_library(
        tmp_path, "proj", "<!-- format_version: 1 -->\n# Shelf\n"
    )
    corp_lib = _make_fixture_library(
        tmp_path, "corp", "<!-- format_version: 1 -->\n# Shelf\n"
    )

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
    local_lib = _make_fixture_library(
        tmp_path, "proj", "<!-- format_version: 1 -->\n# Shelf\n"
    )

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
        LibrarySource(
            name="corp", type="filesystem", path=str(tmp_path / "nonexistent")
        ),
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
    local_lib = _make_fixture_library(
        tmp_path, "proj", "<!-- format_version: 1 -->\n# Shelf\n"
    )

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
    local_lib = _make_fixture_library(
        tmp_path, "proj", "<!-- format_version: 1 -->\n# Shelf\n"
    )

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


def test_orchestrator_output_ordering_local_first_externals_alpha(
    tmp_path: Path,
) -> None:
    libs = {
        n: _make_fixture_library(tmp_path, n, "<!-- format_version: 1 -->\n# Shelf\n")
        for n in ("proj", "zebra", "alpha", "mango")
    }

    def mock_dispatch(req: DispatchRequest) -> str:
        return (
            f"### {req.source.name}\n**Finding**: x.\n"
            f"**Source library**: {req.source.name}\n"
        )

    sources = [
        LibrarySource(name="local", type="filesystem", path=str(libs["proj"])),
        LibrarySource(name="zebra", type="filesystem", path=str(libs["zebra"])),
        LibrarySource(name="alpha", type="filesystem", path=str(libs["alpha"])),
        LibrarySource(name="mango", type="filesystem", path=str(libs["mango"])),
    ]
    result = run_retrieval_query(
        question="q",
        sources=sources,
        priming=None,
        dispatcher=mock_dispatch,
    )
    # local must appear before alpha, alpha before mango, mango before zebra
    out = result.combined_output
    assert (
        out.index("### local")
        < out.index("### alpha")
        < out.index("### mango")
        < out.index("### zebra")
    )


def test_format_dispatch_prompt_with_full_priming() -> None:
    source = LibrarySource(name="corp-semi", type="filesystem", path="/lib/corp-semi")
    priming = PrimingBundle(
        question="what about EUV cleanroom",
        local_kb_config_excerpt=(
            "This project uses the knowledge base for semiconductor research."
        ),
        local_shelf_index_terms=["semiconductor", "brazilian-fab", "alpha"],
    )
    prompt = format_dispatch_prompt(
        source=source, question="what about EUV cleanroom", priming=priming
    )

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
    priming = build_priming_bundle(question="what about EUV", project_dir=proj_dir)

    # Verify the builder did its job
    assert "semiconductor research" in priming.local_kb_config_excerpt
    assert set(priming.local_shelf_index_terms) >= {
        "semiconductor",
        "brazilian-fab",
        "alpha",
    }

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
        LibrarySource(
            name="corp", type="filesystem", path=str(tmp_path / "corp" / "library")
        ),
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
            f"Dispatcher received a different priming bundle "
            f"for source {req.source.name}"
        )
        assert req.priming.local_kb_config_excerpt == priming.local_kb_config_excerpt
        assert req.priming.local_shelf_index_terms == priming.local_shelf_index_terms

    # And the result should still be well-formed
    assert "local finding" in result.combined_output
    assert "corp finding" in result.combined_output


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


def test_format_synthesis_prompt_with_priming_and_findings() -> None:
    priming = PrimingBundle(
        question="how should we think about EUV cleanrooms",
        local_kb_config_excerpt="Brazilian semiconductor packaging operations.",
        local_shelf_index_terms=["semiconductor", "brazilian-fab"],
    )
    per_source = {
        "local": (
            "### Site baseline\n**Finding**: RH 75-85%.\n**Source library**: local"
        ),
        "corp-semi": (
            "### EUV spec\n**Finding**: RH must be ≤45%.\n**Source library**: corp-semi"
        ),
    }
    prompt = format_synthesis_prompt(
        question="how should we think about EUV cleanrooms",
        priming=priming,
        per_source_findings=per_source,
    )

    # Mode marker so the librarian knows it's a synthesis pass
    assert "SYNTHESISE-ACROSS-SOURCES" in prompt
    # Question echoed
    assert "how should we think about EUV cleanrooms" in prompt
    # Priming context still threaded through
    assert "PRIMING_CONTEXT:" in prompt
    assert "Brazilian semiconductor" in prompt
    # All per-source findings present, marked by source handle
    assert "[local]" in prompt
    assert "Site baseline" in prompt
    assert "[corp-semi]" in prompt
    assert "EUV spec" in prompt
    # Hard rule: librarian cannot re-read files
    assert "do not read any files" in prompt.lower()
    # Hard rule: every supporting-evidence claim must carry inline [handle]
    assert "[<handle>]" in prompt or "[handle]" in prompt
    assert "Source library" in prompt or "source handle" in prompt.lower()


def test_format_synthesis_prompt_without_priming() -> None:
    per_source = {"local": "### x\n**Finding**: y.\n**Source library**: local"}
    prompt = format_synthesis_prompt(
        question="build the case for X",
        priming=None,
        per_source_findings=per_source,
    )
    assert "SYNTHESISE-ACROSS-SOURCES" in prompt
    assert "PRIMING_CONTEXT:" not in prompt
    assert "build the case for X" in prompt
    assert "[local]" in prompt


def test_format_synthesis_prompt_includes_all_source_findings_in_order() -> None:
    """Per-source findings appear in dict-iteration order (caller controls)."""
    per_source = {
        "alpha": "### a\n**Finding**: a1.\n**Source library**: alpha",
        "beta": "### b\n**Finding**: b1.\n**Source library**: beta",
        "gamma": "### c\n**Finding**: c1.\n**Source library**: gamma",
    }
    prompt = format_synthesis_prompt(
        question="how should we think about it",
        priming=None,
        per_source_findings=per_source,
    )
    # All three sources represented
    for handle in ("alpha", "beta", "gamma"):
        assert f"[{handle}]" in prompt
        assert handle in prompt


def test_format_synthesis_prompt_empty_findings_dict() -> None:
    """Caller should not invoke synthesis with no findings, but defensive shape OK."""
    prompt = format_synthesis_prompt(
        question="q",
        priming=None,
        per_source_findings={},
    )
    # Still emits the mode marker and question; the input-findings section may be empty
    assert "SYNTHESISE-ACROSS-SOURCES" in prompt
    assert "q" in prompt


def _good_synthesis_output() -> str:
    return (
        "### EUV cleanroom under regional constraints\n\n"
        "**Claim**: Tropical sites need multi-stage dehumidification.\n\n"
        "**Supporting evidence**:\n"
        "1. EUV reticle requires ≤45% RH — [corp-semi] EUV-operations.md\n"
        "2. Brazilian ambient RH 75-85% — [local] site-baseline.md\n\n"
        "**Caveats**: This synthesis draws on local and corp-semi libraries.\n"
    )


def test_run_synthesis_query_skipped_when_question_is_retrieval(tmp_path: Path) -> None:
    """A non-synthesis question should not trigger a synthesis call."""
    retrieval = RetrievalQueryResult(
        combined_output="header\n## [local] Findings\n### x\n**Source library**: local",
        sources_with_findings=["local", "corp-semi"],
    )
    sources = [
        LibrarySource(name="local", type="filesystem", path="/x"),
        LibrarySource(name="corp-semi", type="filesystem", path="/y"),
    ]

    dispatcher_calls: list[str] = []

    def synthesis_dispatcher(prompt: str) -> str:
        dispatcher_calls.append(prompt)
        return _good_synthesis_output()

    result = run_synthesis_query(
        question="what does the research say about cycle time",
        retrieval=retrieval,
        priming=None,
        sources=sources,
        synthesis_dispatcher=synthesis_dispatcher,
        per_source_findings={"local": "x", "corp-semi": "y"},
    )
    assert isinstance(result, SynthesisQueryResult)
    assert result.synthesis_attempted is False
    assert result.synthesis_succeeded is False
    assert dispatcher_calls == []  # no synthesis dispatch happened
    # Combined output is the retrieval output unchanged
    assert result.combined_output == retrieval.combined_output


def test_run_synthesis_query_skipped_with_only_one_source_with_findings(
    tmp_path: Path,
) -> None:
    """Synthesis is only useful when findings span multiple sources."""
    retrieval = RetrievalQueryResult(
        combined_output="solo content",
        sources_with_findings=["local"],
    )
    sources = [LibrarySource(name="local", type="filesystem", path="/x")]

    def synthesis_dispatcher(prompt: str) -> str:
        return _good_synthesis_output()

    result = run_synthesis_query(
        question="how should we think about cycle time",  # synthesis question
        retrieval=retrieval,
        priming=None,
        sources=sources,
        synthesis_dispatcher=synthesis_dispatcher,
        per_source_findings={"local": "x"},
    )
    assert result.synthesis_attempted is False
    assert result.synthesis_succeeded is False
    assert "single source" in (result.fallback_reason or "").lower()


def test_run_synthesis_query_succeeds_with_well_formed_output() -> None:
    retrieval = RetrievalQueryResult(
        combined_output="retrieval output",
        sources_with_findings=["local", "corp-semi"],
    )
    sources = [
        LibrarySource(name="local", type="filesystem", path="/x"),
        LibrarySource(name="corp-semi", type="filesystem", path="/y"),
    ]
    captured: list[str] = []

    def synthesis_dispatcher(prompt: str) -> str:
        captured.append(prompt)
        return _good_synthesis_output()

    result = run_synthesis_query(
        question="how should we think about EUV cleanrooms",
        retrieval=retrieval,
        priming=None,
        sources=sources,
        synthesis_dispatcher=synthesis_dispatcher,
        per_source_findings={
            "local": "site finding",
            "corp-semi": "EUV finding",
        },
    )
    assert result.synthesis_attempted is True
    assert result.synthesis_succeeded is True
    assert result.attribution_warnings == []
    # The good synthesis text should appear in the combined output
    assert "EUV cleanroom under regional constraints" in result.combined_output
    # Should mention both source handles
    assert "[corp-semi]" in result.combined_output
    assert "[local]" in result.combined_output
    # Dispatcher was called once with the synthesis prompt
    assert len(captured) == 1
    assert "SYNTHESISE-ACROSS-SOURCES" in captured[0]


def test_run_synthesis_query_falls_back_when_attribution_check_fails() -> None:
    retrieval = RetrievalQueryResult(
        combined_output="retrieval output",
        sources_with_findings=["local", "corp"],
    )
    sources = [
        LibrarySource(name="local", type="filesystem", path="/x"),
        LibrarySource(name="corp", type="filesystem", path="/y"),
    ]

    bad_synthesis = (
        "### Argument\n\n"
        "**Claim**: Something.\n\n"
        "**Supporting evidence**:\n"
        "1. Untagged claim with no inline handle\n"
        "2. Another untagged claim\n\n"
        "**Caveats**: None.\n"
    )

    def synthesis_dispatcher(prompt: str) -> str:
        return bad_synthesis

    result = run_synthesis_query(
        question="how should we think about it",
        retrieval=retrieval,
        priming=None,
        sources=sources,
        synthesis_dispatcher=synthesis_dispatcher,
        per_source_findings={"local": "x", "corp": "y"},
    )
    assert result.synthesis_attempted is True
    assert result.synthesis_succeeded is False
    assert len(result.attribution_warnings) >= 1
    # Combined output: retrieval output PLUS an error block, NOT the bad synthesis
    assert "retrieval output" in result.combined_output
    assert "Untagged claim" not in result.combined_output
    assert (
        "Synthesis aborted" in result.combined_output
        or "synthesis failed" in result.combined_output.lower()
    )


def test_run_synthesis_query_falls_back_when_dispatcher_raises() -> None:
    retrieval = RetrievalQueryResult(
        combined_output="retrieval output",
        sources_with_findings=["local", "corp"],
    )
    sources = [
        LibrarySource(name="local", type="filesystem", path="/x"),
        LibrarySource(name="corp", type="filesystem", path="/y"),
    ]

    def synthesis_dispatcher(prompt: str) -> str:
        raise RuntimeError("agent timeout")

    result = run_synthesis_query(
        question="how should we think about it",
        retrieval=retrieval,
        priming=None,
        sources=sources,
        synthesis_dispatcher=synthesis_dispatcher,
        per_source_findings={"local": "x", "corp": "y"},
    )
    assert result.synthesis_attempted is True
    assert result.synthesis_succeeded is False
    assert "agent timeout" in (result.fallback_reason or "")
    # Retrieval output preserved
    assert "retrieval output" in result.combined_output


def test_run_synthesis_query_uses_valid_handles_from_sources() -> None:
    """Synthesis check should reject [TODO]-style bogus handles even
    when phrased as inline tags."""
    retrieval = RetrievalQueryResult(
        combined_output="retrieval output",
        sources_with_findings=["local", "corp"],
    )
    sources = [
        LibrarySource(name="local", type="filesystem", path="/x"),
        LibrarySource(name="corp", type="filesystem", path="/y"),
    ]
    bogus_synthesis = (
        "### Argument\n\n"
        "**Claim**: X.\n\n"
        "**Supporting evidence**:\n"
        "1. Looks valid — [TODO] not a real handle\n"
        "2. Also bogus — [citation-needed] also not real\n\n"
        "**Caveats**: None.\n"
    )

    def synthesis_dispatcher(prompt: str) -> str:
        return bogus_synthesis

    result = run_synthesis_query(
        question="how should we think about it",
        retrieval=retrieval,
        priming=None,
        sources=sources,
        synthesis_dispatcher=synthesis_dispatcher,
        per_source_findings={"local": "x", "corp": "y"},
    )
    # Bogus handles fail the whitelist; synthesis aborts
    assert result.synthesis_succeeded is False
    assert len(result.attribution_warnings) == 2


from sdlc_knowledge_base_scripts.audit import read_log


def test_orchestrator_writes_audit_event_on_attribution_drop(tmp_path: Path) -> None:
    """When a finding is dropped for missing Source library tag, an audit event is written."""
    audit_log = tmp_path / "audit.log"
    local_lib = _make_fixture_library(tmp_path, "proj", "<!-- format_version: 1 -->\n# Shelf\n")

    def mock_dispatch(req: DispatchRequest) -> str:
        return (
            "### Tagged finding\n"
            "**Finding**: ok.\n"
            "**Source library**: local\n\n"
            "### Untagged finding\n"
            "**Finding**: bad, no attribution.\n"
        )

    sources = [LibrarySource(name="local", type="filesystem", path=str(local_lib))]
    result = run_retrieval_query(
        question="q",
        sources=sources,
        priming=None,
        dispatcher=mock_dispatch,
        audit_log_path=audit_log,
    )
    events = read_log(audit_log, event_type="attribution_drop_retrieval")
    assert len(events) == 1
    assert events[0].source_handle == "local"
    assert "Untagged finding" in events[0].detail.get("dropped_block_titles", [])[0]


def test_orchestrator_writes_audit_event_on_dispatcher_failure(tmp_path: Path) -> None:
    audit_log = tmp_path / "audit.log"
    local_lib = _make_fixture_library(tmp_path, "proj", "<!-- format_version: 1 -->\n# Shelf\n")

    def mock_dispatch(req: DispatchRequest) -> str:
        raise RuntimeError("agent timeout")

    sources = [LibrarySource(name="corp", type="filesystem", path=str(local_lib))]
    result = run_retrieval_query(
        question="q",
        sources=sources,
        priming=None,
        dispatcher=mock_dispatch,
        audit_log_path=audit_log,
    )
    events = read_log(audit_log, event_type="source_dispatch_failed")
    assert len(events) == 1
    assert events[0].source_handle == "corp"
    assert "agent timeout" in events[0].reason


def test_orchestrator_writes_audit_event_on_synthesis_attribution_abort(tmp_path: Path) -> None:
    audit_log = tmp_path / "audit.log"
    retrieval = RetrievalQueryResult(
        combined_output="output",
        sources_with_findings=["local", "corp"],
    )
    sources = [
        LibrarySource(name="local", type="filesystem", path="/x"),
        LibrarySource(name="corp", type="filesystem", path="/y"),
    ]
    bad_synth = "### Argument\n**Claim**: X.\n**Supporting evidence**:\n1. Untagged.\n**Caveats**: None.\n"
    def synth_dispatch(p: str) -> str:
        return bad_synth
    result = run_synthesis_query(
        question="how should we think",
        retrieval=retrieval,
        priming=None,
        sources=sources,
        synthesis_dispatcher=synth_dispatch,
        per_source_findings={"local": "x", "corp": "y"},
        audit_log_path=audit_log,
    )
    events = read_log(audit_log, event_type="synthesis_aborted_attribution")
    assert len(events) == 1


def test_orchestrator_writes_audit_event_on_synthesis_dispatcher_error(tmp_path: Path) -> None:
    audit_log = tmp_path / "audit.log"
    retrieval = RetrievalQueryResult(
        combined_output="output",
        sources_with_findings=["local", "corp"],
    )
    sources = [
        LibrarySource(name="local", type="filesystem", path="/x"),
        LibrarySource(name="corp", type="filesystem", path="/y"),
    ]
    def synth_dispatch(p: str) -> str:
        raise RuntimeError("synth timeout")
    result = run_synthesis_query(
        question="how should we think",
        retrieval=retrieval,
        priming=None,
        sources=sources,
        synthesis_dispatcher=synth_dispatch,
        per_source_findings={"local": "x", "corp": "y"},
        audit_log_path=audit_log,
    )
    events = read_log(audit_log, event_type="synthesis_aborted_dispatcher_error")
    assert len(events) == 1
    assert "synth timeout" in events[0].reason


def test_orchestrator_no_audit_when_path_is_none(tmp_path: Path) -> None:
    """audit_log_path=None (default) means no logging — preserves backwards compat."""
    local_lib = _make_fixture_library(tmp_path, "proj", "<!-- format_version: 1 -->\n# Shelf\n")
    def mock_dispatch(req: DispatchRequest) -> str:
        return "### Untagged\n**Finding**: bad.\n"
    sources = [LibrarySource(name="local", type="filesystem", path=str(local_lib))]
    # Use default audit_log_path=None
    result = run_retrieval_query(
        question="q",
        sources=sources,
        priming=None,
        dispatcher=mock_dispatch,
    )
    # No audit log file should have been created
    assert not (tmp_path / "audit.log").exists()
