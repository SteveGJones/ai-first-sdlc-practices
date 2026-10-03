# Cross-Library KB Query — Phase C Synthesis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Activate cross-library synthesis. When the user asks a synthesis question ("build me the case for X", "how should we think about Y") and findings span multiple libraries, kb-query produces a connected argument with mandatory inline `[handle]` attribution on every supporting-evidence claim, validated by the existing structural post-check from Phase A. Per spec §3.3, §6.2, §7.1.

**Architecture:** Phase A built `check_synthesis_attribution` (the structural validator) and the librarian agent already accepts `SOURCE_HANDLE`. Phase B added `format_dispatch_prompt` for retrieval. Phase C adds three new pieces in the orchestrator: (a) `is_synthesis_query` to detect synthesis intent from a question string, (b) `format_synthesis_prompt` to render the synthesis dispatch message (single call, takes pre-retrieved findings as input — librarian cannot re-read files), and (c) `run_synthesis_query` to orchestrate the whole flow including attribution post-check with valid_handles whitelist. The librarian agent prompt gains a "synthesise-across-sources" mode section. The kb-query skill's placeholder Step 6 is replaced with the real synthesis branch.

**Tech Stack:** Python 3.10+, pytest. No new external dependencies.

**Spec:** `docs/superpowers/specs/2026-04-24-cross-library-kb-query-design.md`
**Issue:** #169 (phase C of EPIC #164)
**Branch:** `feature/164-cross-library-kb-query` (continues from Phases A + B)

---

## Critical lesson from Phase A regression (apply to every plugin-file edit)

**For files in `release-mapping.yaml` with a separate root source (e.g., `source: skills/foo/SKILL.md` packaged to `plugins/<plugin>/skills/foo/SKILL.md`):**

1. Edit the **root source** (`skills/foo/SKILL.md`)
2. Mirror to plugin-dir: `cp skills/foo/SKILL.md plugins/<plugin>/skills/foo/SKILL.md`
3. Verify with `python3 tools/validation/check-plugin-packaging.py` — must report 12 plugins verified

This applies to Tasks 4 (research-librarian.md) and 5 (kb-query/SKILL.md) below. See `memory/feedback_phase_a_plugin_dir_regression.md`.

For files that live ONLY in the plugin-dir (the orchestrator/scripts under `plugins/sdlc-knowledge-base/scripts/`), edit them in place — release-mapping has them as `source: plugins/sdlc-knowledge-base/scripts/...` (no separate root source).

---

## File structure

**Files to modify:**

| File | Change | Root source? |
|---|---|---|
| `plugins/sdlc-knowledge-base/scripts/orchestrator.py` | Add `is_synthesis_query`, `format_synthesis_prompt`, `SynthesisQueryResult`, `run_synthesis_query` | No (in-plugin only) |
| `tests/test_kb_orchestrator.py` | Add tests for the four new exports | N/A (test file) |
| `agents/knowledge-base/research-librarian.md` + plugin mirror | Add "synthesise-across-sources" mode section to the existing dispatch parameters block | YES — root first |
| `skills/kb-query/SKILL.md` + plugin mirror | Replace Step 6 (synthesis placeholder) with real synthesis branch using the new orchestrator helpers | YES — root first |

**No new files** — Phase C is activation, not new abstractions.

---

## Task 1: `is_synthesis_query` heuristic

**Files:**
- Modify: `plugins/sdlc-knowledge-base/scripts/orchestrator.py`
- Modify: `tests/test_kb_orchestrator.py`

Pure function that classifies a question as synthesis vs retrieval based on phrase matching. Conservative — false negatives (treating a synthesis query as retrieval) are recoverable; false positives (forcing synthesis on a simple retrieval) are noisier.

- [ ] **Step 1: Write failing tests**

Append to `tests/test_kb_orchestrator.py`:

```python
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
```

- [ ] **Step 2: Run tests — verify they fail**

Run from repo root: `python3 -m pytest tests/test_kb_orchestrator.py::test_is_synthesis_query_build_the_case -v`
Expected: FAIL with `ImportError: cannot import name 'is_synthesis_query'`

- [ ] **Step 3: Implement `is_synthesis_query`**

Append to `plugins/sdlc-knowledge-base/scripts/orchestrator.py` (place near the top, after the existing `format_dispatch_prompt` helper from Phase B):

```python
_SYNTHESIS_PHRASES = (
    "build me the case",
    "build the case",
    "how should we think",
    "synthesise",
    "synthesize",
)


def is_synthesis_query(question: str) -> bool:
    """Heuristic: does this question call for synthesis rather than retrieval?

    Synthesis queries ask for a connected argument across multiple findings.
    Retrieval queries ask for specific facts. The distinction matters because
    synthesis requires a separate librarian call with all retrieval findings
    as input, plus mandatory inline source attribution on every claim.

    Conservative — false negatives (synthesis treated as retrieval) yield
    per-source findings the user can connect manually. False positives
    (retrieval treated as synthesis) waste a librarian call and produce a
    less specific answer.
    """
    if not question or not question.strip():
        return False
    lower = question.lower()
    return any(phrase in lower for phrase in _SYNTHESIS_PHRASES)
```

- [ ] **Step 4: Run tests — all pass**

Run: `python3 -m pytest tests/test_kb_orchestrator.py -v`
Expected: 15 tests pass (10 from Phases A+B + 5 new).

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/orchestrator.py tests/test_kb_orchestrator.py
git commit -m "feat(kb): add is_synthesis_query heuristic (phase C, #169)

Pure function that classifies a question as synthesis vs retrieval
based on phrase matching ('build the case for', 'how should we think
about', 'synthesise/synthesize'). Conservative — only obvious synthesis
phrases trigger; everything else is treated as retrieval. False
negatives are recoverable (user gets per-source findings to connect
manually); false positives waste a librarian call.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: `format_synthesis_prompt` helper

**Files:**
- Modify: `plugins/sdlc-knowledge-base/scripts/orchestrator.py`
- Modify: `tests/test_kb_orchestrator.py`

Renders the dispatch message for the synthesis librarian call. Unlike `format_dispatch_prompt` (one source, scoped to a library), this is a single dispatch with all per-source retrieval findings as input. The librarian works ONLY from the input findings — it cannot re-read files. This is what makes synthesis attribution structurally guaranteed.

- [ ] **Step 1: Write failing tests**

Append to `tests/test_kb_orchestrator.py`:

```python
from sdlc_knowledge_base_scripts.orchestrator import format_synthesis_prompt


def test_format_synthesis_prompt_with_priming_and_findings() -> None:
    priming = PrimingBundle(
        question="how should we think about EUV cleanrooms",
        local_kb_config_excerpt="Brazilian semiconductor packaging operations.",
        local_shelf_index_terms=["semiconductor", "brazilian-fab"],
    )
    per_source = {
        "local": "### Site baseline\n**Finding**: RH 75-85%.\n**Source library**: local",
        "corp-semi": "### EUV spec\n**Finding**: RH must be ≤45%.\n**Source library**: corp-semi",
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
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `python3 -m pytest tests/test_kb_orchestrator.py::test_format_synthesis_prompt_with_priming_and_findings -v`
Expected: FAIL with `ImportError: cannot import name 'format_synthesis_prompt'`

- [ ] **Step 3: Implement `format_synthesis_prompt`**

Append to `plugins/sdlc-knowledge-base/scripts/orchestrator.py` (after `format_dispatch_prompt`):

```python
def format_synthesis_prompt(
    question: str,
    priming: Optional[PrimingBundle],
    per_source_findings: dict[str, str],
) -> str:
    """Render the dispatch message for the synthesis-across-sources pass.

    Unlike format_dispatch_prompt (per-source retrieval), this is a single
    dispatch that receives all per-source retrieval findings as input. The
    librarian must produce a connected argument with inline [handle] tags
    on every supporting-evidence claim — and cannot re-read files (the
    findings are its only ground truth, which is what makes attribution
    structurally guaranteed).

    Output structure:
        MODE: SYNTHESISE-ACROSS-SOURCES
        PRIMING_CONTEXT: <json>     (only when priming is provided)

        Question: <question>

        Per-source findings (your only source of facts):
        --- [<handle>] ---
        <findings text>
        --- [<other handle>] ---
        <findings text>
        ...

        <synthesis instructions>
    """
    lines: list[str] = []
    lines.append("MODE: SYNTHESISE-ACROSS-SOURCES")
    if priming is not None:
        priming_json = _json.dumps(
            {
                "local_kb_config_excerpt": priming.local_kb_config_excerpt,
                "local_shelf_index_terms": priming.local_shelf_index_terms,
            },
            indent=2,
        )
        lines.append("PRIMING_CONTEXT:")
        lines.append(priming_json)
    lines.append("")
    lines.append(f"Question: {question}")
    lines.append("")
    lines.append("Per-source findings (your only source of facts — do not read any files):")
    lines.append("")
    for handle, findings in per_source_findings.items():
        lines.append(f"--- [{handle}] ---")
        lines.append(findings.rstrip())
        lines.append("")
    lines.append(
        "Produce a single connected argument that addresses the question, drawing on "
        "the findings above. Use the synthesis output format (Claim / Supporting "
        "evidence / Caveats / Programme application)."
    )
    lines.append("")
    lines.append(
        "MANDATORY: every claim in the Supporting evidence list must carry an inline "
        "[<handle>] tag identifying which source library it came from (e.g., "
        "'1. EUV reticle requires ≤45% RH — [corp-semi] EUV-operations.md'). The "
        "structural attribution post-check will abort the synthesis if any "
        "supporting-evidence item lacks an inline handle. Untagged claims are dropped."
    )
    lines.append("")
    lines.append(
        "When findings span multiple libraries, the Caveats section MUST explicitly "
        "name the cross-library span — for example: 'This synthesis draws on local "
        "and corp-semi libraries; the corp-semi findings are from a different "
        "regional context.'"
    )
    lines.append("")
    lines.append(
        "You do not have file-reading tools in this mode. The findings above are "
        "your only source of ground truth. Do not invent citations, statistics, or "
        "claims that aren't traceable to one of the per-source findings."
    )
    return "\n".join(lines)
```

- [ ] **Step 4: Run tests — all pass**

Run: `python3 -m pytest tests/test_kb_orchestrator.py -v`
Expected: 19 tests pass (15 + 4 new).

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/orchestrator.py tests/test_kb_orchestrator.py
git commit -m "feat(kb): add format_synthesis_prompt helper (phase C, #169)

Renders the synthesise-across-sources dispatch message. Unlike
format_dispatch_prompt (per-source retrieval), this is a single
call that receives all per-source retrieval findings as input.
The librarian works only from those findings — no file reading —
which makes the inline [handle] attribution structurally guaranteed.

Prompt explicitly forbids file reading, mandates inline source-handle
tagging on every supporting-evidence claim, and requires the Caveats
section to flag cross-library spans.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: `SynthesisQueryResult` + `run_synthesis_query`

**Files:**
- Modify: `plugins/sdlc-knowledge-base/scripts/orchestrator.py`
- Modify: `tests/test_kb_orchestrator.py`

The orchestrator function that ties it all together: detect synthesis intent, dispatch the synthesis librarian call, validate attribution with the registry's known handles, and either return the synthesis or fall back to retrieval with an explanatory note.

- [ ] **Step 1: Write failing tests**

Append to `tests/test_kb_orchestrator.py`:

```python
from sdlc_knowledge_base_scripts.orchestrator import (
    run_synthesis_query,
    SynthesisQueryResult,
)


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


def test_run_synthesis_query_skipped_with_only_one_source_with_findings(tmp_path: Path) -> None:
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
    # Combined output should be retrieval output PLUS an error block, NOT the bad synthesis
    assert "retrieval output" in result.combined_output
    assert "Untagged claim" not in result.combined_output
    assert "Synthesis aborted" in result.combined_output or "synthesis failed" in result.combined_output.lower()


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
    """Synthesis check should reject [TODO]-style bogus handles even when phrased as inline tags."""
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
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `python3 -m pytest tests/test_kb_orchestrator.py::test_run_synthesis_query_succeeds_with_well_formed_output -v`
Expected: FAIL with `ImportError: cannot import name 'run_synthesis_query'`

- [ ] **Step 3: Implement `SynthesisQueryResult` + `run_synthesis_query`**

Append to `plugins/sdlc-knowledge-base/scripts/orchestrator.py` (after `format_synthesis_prompt`):

```python
from .attribution import check_synthesis_attribution


@dataclass
class SynthesisQueryResult:
    """Outcome of an attempted synthesis pass on retrieval results.

    When `synthesis_attempted` is False, the question was not classified as
    synthesis or there were too few sources to synthesise across; the
    retrieval output is returned unchanged in `combined_output`.

    When `synthesis_attempted` is True and `synthesis_succeeded` is True,
    `combined_output` contains the synthesis answer (which already has
    inline source-handle attribution validated by the post-check).

    When `synthesis_attempted` is True and `synthesis_succeeded` is False,
    something failed (attribution missing, dispatcher error). The retrieval
    output is preserved in `combined_output` with an appended error block;
    `fallback_reason` names what went wrong.
    """
    combined_output: str
    synthesis_attempted: bool
    synthesis_succeeded: bool
    attribution_warnings: list[str] = field(default_factory=list)
    fallback_reason: Optional[str] = None


SynthesisDispatcher = Callable[[str], str]


def run_synthesis_query(
    question: str,
    retrieval: RetrievalQueryResult,
    priming: Optional[PrimingBundle],
    sources: list[LibrarySource],
    synthesis_dispatcher: SynthesisDispatcher,
    per_source_findings: dict[str, str],
) -> SynthesisQueryResult:
    """Optionally extend retrieval with cross-library synthesis.

    Synthesis runs only when:
      1. The question is classified as synthesis (is_synthesis_query)
      2. At least 2 sources returned findings (otherwise there's nothing
         to synthesise across)

    On success the synthesis output replaces the retrieval body. On any
    failure (attribution check, dispatcher exception) the retrieval body
    is preserved and an explanatory error block is appended.
    """
    if not is_synthesis_query(question):
        return SynthesisQueryResult(
            combined_output=retrieval.combined_output,
            synthesis_attempted=False,
            synthesis_succeeded=False,
            fallback_reason="question is not a synthesis query",
        )

    if len(retrieval.sources_with_findings) < 2:
        return SynthesisQueryResult(
            combined_output=retrieval.combined_output,
            synthesis_attempted=False,
            synthesis_succeeded=False,
            fallback_reason="single source has findings — nothing to synthesise across",
        )

    prompt = format_synthesis_prompt(
        question=question,
        priming=priming,
        per_source_findings=per_source_findings,
    )

    try:
        synthesis_output = synthesis_dispatcher(prompt)
    except Exception as exc:
        error_block = (
            f"\n\n---\n\n"
            f"**Synthesis aborted:** dispatcher failed: {exc}.\n"
            f"Per-source findings above are complete; synthesis was not produced.\n"
        )
        return SynthesisQueryResult(
            combined_output=retrieval.combined_output + error_block,
            synthesis_attempted=True,
            synthesis_succeeded=False,
            fallback_reason=str(exc),
        )

    valid_handles = {s.name for s in sources}
    check = check_synthesis_attribution(synthesis_output, valid_handles=valid_handles)
    if not check.passed:
        error_block = (
            f"\n\n---\n\n"
            f"**Synthesis aborted:** attribution post-check failed. "
            f"{len(check.untagged_claims)} supporting-evidence "
            f"claim(s) lacked an inline source-handle tag and were not safe to "
            f"publish. Per-source findings above remain valid; you can draw "
            f"connections manually.\n"
        )
        return SynthesisQueryResult(
            combined_output=retrieval.combined_output + error_block,
            synthesis_attempted=True,
            synthesis_succeeded=False,
            attribution_warnings=check.untagged_claims,
            fallback_reason="attribution post-check failed",
        )

    # Success: combine retrieval header with synthesis body
    combined = (
        retrieval.combined_output
        + "\n\n---\n\n"
        + "## Cross-library synthesis\n\n"
        + synthesis_output.rstrip()
        + "\n"
    )
    return SynthesisQueryResult(
        combined_output=combined,
        synthesis_attempted=True,
        synthesis_succeeded=True,
    )
```

- [ ] **Step 4: Run tests — all pass**

Run: `python3 -m pytest tests/test_kb_orchestrator.py -v`
Expected: 25 tests pass (19 + 6 new).

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-knowledge-base/scripts/orchestrator.py tests/test_kb_orchestrator.py
git commit -m "feat(kb): add run_synthesis_query orchestrator (phase C, #169)

Top-level entry for cross-library synthesis. Detects synthesis intent
via is_synthesis_query, dispatches a single synthesis librarian call
through format_synthesis_prompt, and validates the result via the
existing check_synthesis_attribution structural post-check (with
valid_handles whitelist drawn from the dispatch sources).

Synthesis is skipped (not a failure) when the question is retrieval-
shaped or fewer than 2 sources have findings. On dispatcher failure or
attribution-check failure, the retrieval output is preserved and an
explanatory error block is appended — never silently shipping a
synthesis missing attribution.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: Librarian prompt — synthesise-across-sources mode

**Files:**
- Modify root: `agents/knowledge-base/research-librarian.md`
- Mirror to plugin: `plugins/sdlc-knowledge-base/agents/research-librarian.md`

Add a new section explaining the SYNTHESISE-ACROSS-SOURCES mode. The librarian already handles synthesis (its existing "synthesis queries" output format is preserved). What's new is the cross-source variant: input is pre-retrieved findings from multiple libraries, output requires inline `[handle]` tags on every supporting-evidence line, and file-reading is forbidden.

- [ ] **Step 1: Locate the insertion point in the root source**

Run: `grep -n "Dispatch message parameters\|How you work" agents/knowledge-base/research-librarian.md`

The new section goes inside the "## Dispatch message parameters (cross-library queries)" section, AFTER the SOURCE_HANDLE bullet and BEFORE the closing paragraph "When these parameters are absent, behave exactly as a single-library query (the default, non-cross-library case)."

- [ ] **Step 2: Insert the new mode subsection**

In `agents/knowledge-base/research-librarian.md`, find the line that introduces the "When these parameters are absent..." closing paragraph at the end of the dispatch parameters section. Just BEFORE that paragraph, insert this new subsection (note the leading H3 heading inside the H2 section):

```markdown
### Synthesise-across-sources mode

When the dispatch message starts with `MODE: SYNTHESISE-ACROSS-SOURCES`, you are
producing a cross-library synthesis from pre-retrieved findings rather than
running a fresh retrieval. Behaviour changes substantially:

- **You have no file-reading tools in this mode.** The dispatch message contains
  per-source findings already retrieved from each scoped library. Those findings
  are your ONLY ground truth. Do not invent citations, statistics, or claims
  that are not traceable to one of the per-source findings supplied. If the
  available findings cannot answer the question, say so plainly — see the
  "no evidence" rule below.

- **Output uses the synthesis format** (Claim / Supporting evidence / Caveats /
  Programme application) rather than the retrieval format. One synthesis block
  per question.

- **Every supporting-evidence item MUST carry an inline source-handle tag.**
  The format is:

  ```
  1. <claim text> — [<handle>] <library file>
  2. <next claim> — [<other-handle>] <library file>
  ```

  The handle is the source library name (e.g., `[local]`, `[corp-semi]`). The
  attribution post-check whitelists handles against the dispatch sources — any
  bracketed token that is not a real source handle (e.g., `[TODO]`, `[citation
  needed]`, `[0]`) will fail the post-check and the synthesis will be aborted.
  Untagged claims will also fail the post-check. There are no warnings — the
  synthesis either ships with full attribution or it doesn't ship at all.

- **The Caveats section MUST flag cross-library spans explicitly.** If your
  supporting evidence draws on more than one source library, name the libraries
  in the Caveats section. For example:

  > **Caveats**: This synthesis draws on local and corp-semi libraries; the
  > corp-semi findings come from a different regional context and may need
  > adaptation before applying to the local project.

  This is a transparency requirement. The reader needs to know which boundaries
  the synthesis crosses, so they can judge whether the cross-library inference
  is sound for their decision.

- **No-evidence rule still applies.** If the supplied per-source findings genuinely
  do not answer the question, say "the supplied findings do not support a synthesis
  for this question" and identify which aspects are missing. Do NOT pad with
  speculation. The trust users place in the librarian depends on this exactly as
  much in synthesis mode as in retrieval mode.

- **Programme application** (the optional final section in the synthesis format) is
  drawn from the priming context if `PRIMING_CONTEXT` is supplied. If the local
  KB config excerpt names a specific project lens, frame the programme application
  through that lens. If no priming is supplied, omit the Programme application
  section.
```

- [ ] **Step 3: Mirror to plugin-dir**

```bash
cp agents/knowledge-base/research-librarian.md plugins/sdlc-knowledge-base/agents/research-librarian.md
```

- [ ] **Step 4: Verify packaging check still passes**

Run: `python3 tools/validation/check-plugin-packaging.py`
Expected: 12 plugins verified.

- [ ] **Step 5: Commit**

```bash
git add agents/knowledge-base/research-librarian.md plugins/sdlc-knowledge-base/agents/research-librarian.md
git commit -m "feat(kb): librarian SYNTHESISE-ACROSS-SOURCES mode (phase C, #169)

Adds a new subsection to the dispatch parameters block explaining the
synthesis-across-sources mode:

- No file-reading tools — pre-retrieved findings are the only ground truth
- Mandatory inline [handle] tag on every supporting-evidence claim
- Caveats section MUST explicitly name cross-library spans
- No-evidence rule applies in synthesis mode too — no speculation

Aligns the librarian agent with what format_synthesis_prompt produces
and what check_synthesis_attribution validates.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: kb-query skill — replace Step 6 with real synthesis

**Files:**
- Modify root: `skills/kb-query/SKILL.md`
- Mirror to plugin: `plugins/sdlc-knowledge-base/skills/kb-query/SKILL.md`

Replace the Phase A/B placeholder Step 6 (which printed "synthesis coming in phase C") with the real synthesis branch.

- [ ] **Step 1: Read current Step 6**

Run: `grep -n -A 20 "### 6. Synthesis" skills/kb-query/SKILL.md`

The existing Step 6 says synthesis is deferred to phase C. We're replacing that with actual orchestration code.

- [ ] **Step 2: Replace Step 6 entirely**

In `skills/kb-query/SKILL.md`, replace the entire `### 6. Synthesis (phase C, #169 — not in phase A)` section (heading + body, until end of file or next H2) with:

```markdown
### 6. Cross-library synthesis (when the question calls for it)

After Step 5, decide whether to run synthesis. The orchestrator's
`run_synthesis_query` handles the decision and the dispatch:

```bash
python3 -c "
from sdlc_knowledge_base_scripts.orchestrator import (
    run_synthesis_query,
    format_synthesis_prompt,
    is_synthesis_query,
    RetrievalQueryResult,
)
from sdlc_knowledge_base_scripts.priming import PrimingBundle
from sdlc_knowledge_base_scripts.registry import LibrarySource
import json

# Reconstruct the retrieval result, sources, and per-source findings collected in Steps 3-5
retrieval = RetrievalQueryResult(
    combined_output='<combined retrieval output from Step 5>',
    sources_with_findings=['<list of source names that returned findings>'],
)
sources = [
    LibrarySource(name='<source.name>', type='filesystem', path='<source.path>'),
    # ... one entry per dispatched source
]
per_source = {
    '<source.name>': '<raw librarian output for that source>',
    # ... one entry per source that returned findings
}
priming_data = json.loads('<priming_bundle_json_from_step_2>')
priming = PrimingBundle(
    question=priming_data['question'],
    local_kb_config_excerpt=priming_data['local_kb_config_excerpt'],
    local_shelf_index_terms=priming_data['local_shelf_index_terms'],
)

# is_synthesis_query handles the heuristic check; run_synthesis_query decides
# whether to actually dispatch (it will skip if <2 sources have findings)
def synthesis_dispatcher(prompt):
    # In the real skill, this wraps the Agent tool: dispatch one
    # research-librarian invocation with the synthesis prompt as input.
    raise NotImplementedError('replace with Agent tool dispatch in the skill body')

result = run_synthesis_query(
    question='<the user question>',
    retrieval=retrieval,
    priming=priming,
    sources=sources,
    synthesis_dispatcher=synthesis_dispatcher,
    per_source_findings=per_source,
)
print(result.combined_output)
"
```

In the actual skill flow, replace the `synthesis_dispatcher` placeholder with the
**Agent tool** invocation: when `is_synthesis_query(question)` returns True AND at
least 2 sources have findings, dispatch ONE more `research-librarian` call with the
synthesis prompt as its input. Otherwise, skip — the orchestrator detects this and
returns the retrieval output unchanged.

The dispatched synthesis prompt looks like:

```
MODE: SYNTHESISE-ACROSS-SOURCES
PRIMING_CONTEXT:
{
  "local_kb_config_excerpt": "...",
  "local_shelf_index_terms": [...]
}

Question: <the user question>

Per-source findings (your only source of facts — do not read any files):

--- [local] ---
<local librarian's findings>

--- [corp-semi] ---
<corp-semi librarian's findings>

Produce a single connected argument that addresses the question, drawing on
the findings above. Use the synthesis output format (Claim / Supporting
evidence / Caveats / Programme application).

MANDATORY: every claim in the Supporting evidence list must carry an inline
[<handle>] tag identifying which source library it came from ...
```

The librarian agent's prompt has a section "Synthesise-across-sources mode" describing how to consume this; the orchestrator's `format_synthesis_prompt` produces it; the skill, agent prompt, and orchestrator stay in lockstep on the format.

After the synthesis call returns, the orchestrator runs `check_synthesis_attribution` (with `valid_handles` drawn from the dispatch sources) on the librarian's output. If any supporting-evidence claim lacks an inline `[handle]` tag, or the bracketed token is not in the source whitelist (e.g., `[TODO]`, `[0]`), the synthesis is aborted: the retrieval output is preserved and an explanatory error block is appended. The user always sees something they can act on.
```

- [ ] **Step 3: Mirror to plugin-dir**

```bash
cp skills/kb-query/SKILL.md plugins/sdlc-knowledge-base/skills/kb-query/SKILL.md
```

- [ ] **Step 4: Verify**

Run: `python3 tools/validation/check-plugin-packaging.py`
Expected: 12 plugins verified.

Run: `diff skills/kb-query/SKILL.md plugins/sdlc-knowledge-base/skills/kb-query/SKILL.md`
Expected: no output (files identical).

- [ ] **Step 5: Commit**

```bash
git add skills/kb-query/SKILL.md plugins/sdlc-knowledge-base/skills/kb-query/SKILL.md
git commit -m "feat(kb): kb-query Step 6 runs real cross-library synthesis (phase C, #169)

Replaces the phase-A/B placeholder ('synthesis coming in phase C') with
the real synthesis branch using run_synthesis_query. The orchestrator
detects synthesis intent (is_synthesis_query) and skips the dispatch
when <2 sources have findings. Synthesis output is structurally validated
via check_synthesis_attribution with the dispatch sources as the
valid_handles whitelist.

On any failure (attribution check, dispatcher error), retrieval output is
preserved and an explanatory error block is appended — synthesis missing
attribution never reaches the user.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: Feature proposal + retrospective scaffold for #169

**Files:**
- Create: `docs/feature-proposals/169-kb-cross-library-phase-c.md`
- Create: `retrospectives/169-kb-cross-library-phase-c.md`

Mirrors the Phases A and B pattern. Per CONSTITUTION Article 2.

- [ ] **Step 1: Create the feature proposal**

Create `docs/feature-proposals/169-kb-cross-library-phase-c.md`:

```markdown
# Feature Proposal: Cross-Library KB Query — Phase C Synthesis

**Proposal Number:** 169
**Status:** In Progress
**Author:** Claude (AI Agent) and Steve Jones
**Created:** 2026-04-24
**Target Branch:** `feature/164-cross-library-kb-query` (continues from Phases A + B)
**EPIC:** #164 (Cross-Library KB Query Support)
**Sub-feature:** #169 (sub-3 of 3 in v1)

## Summary

Activate cross-library synthesis. When the user asks a synthesis question and findings span multiple libraries, kb-query produces a connected argument with mandatory inline `[handle]` attribution on every supporting-evidence claim, validated by the structural post-check from Phase A.

## Motivation

See EPIC #164 body and design spec §3.3 (synthesis as architectural property), §6.2 (data flow), §7.1 (attribution integrity hard invariant). Phases A and B delivered the foundation and priming respectively; Phase C is the third leg of the v1 deliverable. Without it, the EPIC ships per-source retrieval only — the user has to draw cross-library connections manually.

## Design

Full design in `docs/superpowers/specs/2026-04-24-cross-library-kb-query-design.md`.

Phase C implementation per spec §6.2 (synthesis flow) and §7.1 (attribution invariant). Adds three orchestrator helpers (`is_synthesis_query`, `format_synthesis_prompt`, `run_synthesis_query`) and one new dataclass (`SynthesisQueryResult`). Reuses the Phase A `check_synthesis_attribution` validator with the registry's known handles passed as the `valid_handles` whitelist. The librarian agent prompt gains a "synthesise-across-sources" mode section.

## Success Criteria

Per issue #169 acceptance criteria:

- [ ] `is_synthesis_query(question)` heuristic detects synthesis intent via phrase matching
- [ ] `format_synthesis_prompt` renders the synthesis dispatch message including PRIMING_CONTEXT, per-source findings, and explicit instructions forbidding file reads
- [ ] `run_synthesis_query` skips synthesis when the question is retrieval-shaped or fewer than 2 sources have findings
- [ ] `run_synthesis_query` aborts and falls back to retrieval-with-error-block when attribution post-check fails or dispatcher raises
- [ ] Librarian agent prompt has a SYNTHESISE-ACROSS-SOURCES mode section covering the input format, attribution requirements, and the no-evidence rule
- [ ] kb-query skill Step 6 dispatches a real synthesis call (not a placeholder) when conditions are met
- [ ] All Phase A and B tests still pass; `check-plugin-packaging.py` reports 12 plugins verified
- [ ] `python tools/validation/local-validation.py --pre-push` passes (modulo pre-commit env issue)

## Out of scope (phase C)

- RemoteAgentSource (deferred EPIC)
- E2E tests with real librarian dispatch (deferred — would require live agent runs)
- Tuning the synthesis heuristic (`is_synthesis_query`) based on real usage data
- Synthesis ingest, lint, staleness-check (kb-* skills remain local-only in v1)

## Dependencies

- Blocked by: #167 (Phase A) — **complete**
- Benefits from: #168 (Phase B) — **complete**

## Implementation plan

`docs/superpowers/plans/2026-04-24-cross-library-kb-query-phase-c.md`

## Closing the EPIC

When Phase C ships, EPIC #164 v1 is complete: foundation + priming + synthesis. Phase D (RemoteAgentSource) becomes a separate future EPIC.
```

- [ ] **Step 2: Create the retrospective scaffold**

Create `retrospectives/169-kb-cross-library-phase-c.md`:

```markdown
# Retrospective: Cross-Library KB Query — Phase C Synthesis

**Issue:** #169 (sub-3 of EPIC #164)
**Branch:** `feature/164-cross-library-kb-query`
**Status:** In progress

## What went well

_(Fill in at end of implementation.)_

## What was harder than expected

_(Fill in at end of implementation.)_

## What surprised us

_(Fill in at end of implementation.)_

## What we'd do differently next time

_(Fill in at end of implementation.)_

## Metrics

- Implementation time: TBD
- Tests added: TBD
- Commits on branch for this sub-feature: TBD
- Validation pipeline pass status: TBD

## Decisions worth capturing in memory

_(Review at end; copy relevant patterns/feedback into MEMORY.md if not already captured.)_
```

- [ ] **Step 3: Commit**

```bash
git add docs/feature-proposals/169-kb-cross-library-phase-c.md retrospectives/169-kb-cross-library-phase-c.md
git commit -m "docs: feature proposal + retrospective scaffold for phase C (#169)

Required by CONSTITUTION Article 2.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 7: Final validation + retrospective + EPIC closure prep

**Files:**
- Modify: `retrospectives/169-kb-cross-library-phase-c.md` (fill in)
- Modify: MEMORY.md

This is the FINAL task in v1 of EPIC #164. Phase C completing means EPIC #164 v1 is feature-complete and ready for PR.

- [ ] **Step 1: Run full kb test suite**

Run from repo root: `python3 -m pytest tests/test_kb_registry.py tests/test_kb_priming.py tests/test_kb_attribution.py tests/test_kb_format_version.py tests/test_kb_orchestrator.py -v`

Expected: 25 orchestrator tests + 14 attribution + 5 format_version + 7 priming + 21 registry = 72 total. (Phase A: 52; Phase B added 5; Phase C adds 15: 5 in Task 1, 4 in Task 2, 6 in Task 3.)

Report final test count.

- [ ] **Step 2: Plugin packaging check**

Run: `python3 tools/validation/check-plugin-packaging.py`
Expected: 12 plugins verified.

- [ ] **Step 3: Pre-push validation**

Run: `python3 tools/validation/local-validation.py --pre-push`
Expected: PASS, or 9/10 with the pre-commit env issue (same pattern as Phases A and B).

- [ ] **Step 4: Fill in the retrospective**

Edit `retrospectives/169-kb-cross-library-phase-c.md`. Use this content as a starting point, refining based on actual outcomes:

- **What went well**:
  - All Phase A scaffolding (`check_synthesis_attribution`, `valid_handles` parameter, librarian SOURCE_HANDLE) was usable as-is — Phase C is purely activation work, no scaffolding rework
  - Three new orchestrator helpers (`is_synthesis_query`, `format_synthesis_prompt`, `run_synthesis_query`) compose cleanly: each is independently testable, the run_synthesis_query just orchestrates them
  - Attribution post-check from Phase A caught bogus `[TODO]` / `[0]` handles in the test cases — reuse of the validator with `valid_handles` whitelist gave us synthesis-grade rigour for free
  - Plugin-dir vs root-source pattern: applied the lesson from Phases A/B, no regression in C
- **What was harder than expected**:
  - `format_synthesis_prompt` required careful prompt engineering — the librarian needs explicit "no file reading", "tag every claim", "name the cross-library spans" instructions that the existing prompt's synthesis section didn't cover
  - Deciding what `run_synthesis_query` does when there's only one source with findings: settled on "skip silently with fallback_reason" rather than treating it as an error
- **What surprised us**:
  - Phase C completed in 7 tasks — same as Phase B, smaller than Phase A. The Phase A foundation paid off
  - The synthesis dispatcher signature `Callable[[str], str]` is simpler than retrieval's `Callable[[DispatchRequest], str]` because synthesis is a single call with no per-source iteration
- **What we'd do differently**:
  - Maybe build adversarial tests for synthesis attribution earlier (Phase A) — they would have caught the regex fail-open then, before Phase B/C built on it
- **Metrics**: implementation time, test count, commit count, validation result
- **Decisions worth capturing**:
  - Synthesis dispatcher takes a formatted prompt string, not a DispatchRequest — different shape from retrieval because there's no per-source iteration
  - Synthesis attribution check uses `valid_handles` derived from the dispatch sources — this is what makes `[TODO]` / `[0]` handles fail
  - When synthesis fails (attribution or dispatcher error), the retrieval output is always preserved with an error block — never silently downgrades to "no answer"

- [ ] **Step 5: Update MEMORY.md**

Memory location: `/Users/stevejones/.claude/projects/-Users-stevejones-Documents-Development-ai-first-sdlc-practices/memory/MEMORY.md`

Update the EPIC #164 entry under "Active EPICs": "Phases A+B+C complete on branch `feature/164-cross-library-kb-query`. v1 feature-complete; ready for PR. Phase D (RemoteAgentSource) tracked as a separate future EPIC."

Move the EPIC #164 entry from "Active EPICs" to a new section or mark it as "v1 complete, awaiting PR" — your choice but make the state visible.

Add a new "Recent Work (session 2026-04-24)" entry for Phase C completion.

- [ ] **Step 6: Commit retrospective**

```bash
git add retrospectives/169-kb-cross-library-phase-c.md
git commit -m "docs: complete phase C retrospective (#169)

Phase C of EPIC #164 implementation-complete. Cross-library synthesis
is active: kb-query produces an attributed connected argument when
a synthesis question hits findings across multiple libraries.

EPIC #164 v1 (foundation + priming + synthesis) is feature-complete
on branch feature/164-cross-library-kb-query. Phase D (RemoteAgentSource)
becomes a separate future EPIC.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 7: Report branch state**

Run: `git log main..HEAD --oneline | wc -l`
Run: `git status` — should be clean.

Phase C complete. EPIC #164 v1 is feature-complete on branch `feature/164-cross-library-kb-query`. The branch is ready for PR after the user reviews.

---

## Self-review

**Spec coverage:**

| Spec section | Covered by task |
|---|---|
| §3.3 synthesis as architectural property | Tasks 1-3 (orchestrator helpers), Task 4 (librarian prompt) |
| §6.2 synthesis data flow | Task 3 (run_synthesis_query) and Task 5 (skill Step 6) |
| §7.1 attribution integrity invariant | Task 3 — re-uses Phase A's check_synthesis_attribution with valid_handles whitelist |
| §8.3 e2e synthesis test scenario | **Deferred** — out-of-scope per proposal §"Out of scope" |
| §9.1 cross-library synthesis in v1 | Tasks 3 + 5 deliver this |

**Placeholder scan:** no TBDs in implementation tasks. The retrospective scaffold has explicit "Fill in at end" markers — intentional.

**Type consistency:** `RetrievalQueryResult` (Phase A), `SynthesisQueryResult` (Phase C — new), `LibrarySource`, `PrimingBundle`, `DispatchRequest`, `Dispatcher` (retrieval), `SynthesisDispatcher` (Phase C — new) all consistent across tasks. Function names `is_synthesis_query`, `format_synthesis_prompt`, `run_synthesis_query` consistent across Tasks 1, 2, 3, 5.

**Plugin-dir lesson coverage:** Tasks 4 and 5 explicitly call out the root-first pattern. Tasks 1, 2, 3 don't touch root-sourced files (orchestrator.py is in-plugin only).

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-24-cross-library-kb-query-phase-c.md`. Two execution options:

**1. Subagent-Driven (recommended)** — fresh subagent per task with two-stage review.

**2. Inline Execution** — `superpowers:executing-plans` with checkpoints.

Phase C is comparable in size to Phase B (7 tasks). Same recommendation — Subagent-Driven for consistency with Phases A and B's quality ratchet.
