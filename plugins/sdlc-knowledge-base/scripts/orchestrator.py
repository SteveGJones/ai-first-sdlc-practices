"""kb-query orchestrator: dispatch, collect, attribution post-check, render.

The orchestrator is pure Python; the `dispatcher` callable abstracts the
Agent tool call so tests can inject mocks. The kb-query skill wires in a
real dispatcher backed by parallel Agent invocations against the
research-librarian (retrieval) and synthesis-librarian (synthesis) agents.

Phases A+B+C+D of EPIC #164 — see spec §3.2, §6.1, §6.2, §7.1, and the
Phase D operational maturity additions (audit logging, staleness caveats,
priming transparency).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

import json as _json

from .attribution import check_retrieval_attribution, check_synthesis_attribution
from .audit import AuditEvent, log_event
from .priming import PrimingBundle
from .registry import LibrarySource


def _render_priming_block(priming: Optional[PrimingBundle]) -> list[str]:
    """Return prompt lines for the PRIMING_CONTEXT block, empty if priming is None."""
    if priming is None:
        return []
    priming_json = _json.dumps(
        {
            "local_kb_config_excerpt": priming.local_kb_config_excerpt,
            "local_shelf_index_terms": priming.local_shelf_index_terms,
        },
        indent=2,
    )
    return ["PRIMING_CONTEXT:", priming_json]


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


def format_dispatch_prompt(
    source: LibrarySource,
    question: str,
    priming: Optional[PrimingBundle],
) -> str:
    """Render the dispatch message a research-librarian invocation should receive.

    Output structure per librarian agent prompt spec:
        SCOPE: <source.path>
        SOURCE_HANDLE: <source.name>
        PRIMING_CONTEXT: <json>     (only when priming is provided)

        Question: <question>

        <closing instruction lines>

    The librarian's prompt extension (see agents/knowledge-base/research-librarian.md)
    documents the expected structure and the active-biasing semantics that consume
    PRIMING_CONTEXT.
    """
    lines: list[str] = []
    lines.append(f"SCOPE: {source.path}")
    lines.append(f"SOURCE_HANDLE: {source.name}")
    lines.extend(_render_priming_block(priming))
    lines.append("")
    lines.append(f"Question: {question}")
    lines.append("")
    lines.append(
        f"Read the shelf-index at {source.path}/_shelf-index.md, identify the 2-4 "
        "most relevant library files for the question, deep-read only those, and "
        "return findings in the retrieval format. Every finding block must include "
        f"a **Source library**: {source.name} line (see your agent prompt)."
    )
    lines.append("")
    lines.append(
        f"Do not read any files outside {source.path}. Do not emit --- horizontal "
        "rules inside a finding block (they are treated as structural separators "
        "by the post-check tokenizer)."
    )
    return "\n".join(lines)


@dataclass
class DispatchRequest:
    """One librarian invocation request — what the dispatcher receives."""

    source: LibrarySource
    question: str
    priming: Optional[PrimingBundle] = None


Dispatcher = Callable[[DispatchRequest], str]


@dataclass
class RetrievalQueryResult:
    combined_output: str
    sources_with_findings: list[str] = field(default_factory=list)
    sources_failed: list[str] = field(default_factory=list)
    sources_no_evidence: list[str] = field(default_factory=list)
    attribution_warnings: list[str] = field(default_factory=list)


_NO_EVIDENCE_MARKER_PHRASES = (
    "the library has no evidence",
    "library has no evidence",
    "no evidence on this",
)


def run_retrieval_query(
    question: str,
    sources: list[LibrarySource],
    priming: Optional[PrimingBundle],
    dispatcher: Dispatcher,
    audit_log_path: Optional[Path] = None,
) -> RetrievalQueryResult:
    """Execute a retrieval query across all dispatch sources."""
    # Per-source: dispatch, classify (findings / no-evidence / failure),
    # and run attribution post-check on any findings output.
    per_source_sections: dict[str, str] = {}
    failed: list[str] = []
    no_evidence: list[str] = []
    sources_with_findings: list[str] = []
    attribution_warnings: list[str] = []

    for source in sources:
        request = DispatchRequest(source=source, question=question, priming=priming)
        try:
            raw = dispatcher(request)
        except Exception as exc:
            failed.append(source.name)
            per_source_sections[source.name] = (
                f"## [{source.name}] — failed\n\n"
                f"[{source.name}] dispatch failed: {exc}\n"
            )
            if audit_log_path is not None:
                log_event(audit_log_path, AuditEvent(
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    event_type="source_dispatch_failed",
                    query=question,
                    source_handle=source.name,
                    reason=str(exc),
                    detail={"exception_type": type(exc).__name__},
                ))
            continue

        lower = raw.strip().lower()
        if any(phrase in lower for phrase in _NO_EVIDENCE_MARKER_PHRASES):
            no_evidence.append(source.name)
            per_source_sections[source.name] = (
                f"## [{source.name}] — no evidence\n\n"
                f"[{source.name}] library has no evidence on this topic.\n"
            )
            continue

        # Apply attribution post-check to this source's findings only
        check = check_retrieval_attribution(raw)
        attribution_warnings.extend(
            f"[{source.name}] {title}" for title in check.dropped_blocks
        )
        if check.dropped_blocks and audit_log_path is not None:
            log_event(audit_log_path, AuditEvent(
                timestamp=datetime.now(timezone.utc).isoformat(),
                event_type="attribution_drop_retrieval",
                query=question,
                source_handle=source.name,
                reason=f"{len(check.dropped_blocks)} finding(s) lacked Source library tag",
                detail={"dropped_block_titles": check.dropped_blocks},
            ))
        cleaned = check.cleaned_output.rstrip()

        if cleaned.strip() and "### " in cleaned:
            sources_with_findings.append(source.name)
            per_source_sections[
                source.name
            ] = f"## [{source.name}] Findings\n\n{cleaned}\n"
        else:
            # All findings from this source were dropped by attribution check
            no_evidence.append(source.name)
            per_source_sections[source.name] = (
                f"## [{source.name}] — no valid findings after attribution check\n\n"
                f"[{source.name}] library had findings but none passed "
                "attribution check.\n"
            )

    # Render ordered output: local first, then externals alphabetical
    ordered = _ordered_source_list(sources)
    ordered_sections = [
        per_source_sections[s.name] for s in ordered if s.name in per_source_sections
    ]
    body = "\n\n---\n\n".join(ordered_sections)

    # Header summarising what ran
    header = _render_header(sources, sources_with_findings, failed, no_evidence)
    full = header + "\n\n---\n\n" + body

    return RetrievalQueryResult(
        combined_output=full,
        sources_with_findings=sources_with_findings,
        sources_failed=failed,
        sources_no_evidence=no_evidence,
        attribution_warnings=attribution_warnings,
    )


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
    lines.extend(_render_priming_block(priming))
    lines.append("")
    lines.append(f"Question: {question}")
    lines.append("")
    lines.append(
        "Per-source findings (your only source of facts — do not read any files):"
    )
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


# SynthesisDispatcher: callable that takes a synthesis prompt and returns the
# librarian's output. In the kb-query skill, this is wired to dispatch the
# `synthesis-librarian` agent (NOT research-librarian) so the structural
# "no file reads" guarantee is enforced at the agent level (tools: [])
# rather than purely by prompt instruction.
SynthesisDispatcher = Callable[[str], str]


def run_synthesis_query(
    question: str,
    retrieval: RetrievalQueryResult,
    priming: Optional[PrimingBundle],
    sources: list[LibrarySource],
    synthesis_dispatcher: SynthesisDispatcher,
    per_source_findings: dict[str, str],
    audit_log_path: Optional[Path] = None,
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
        if audit_log_path is not None:
            log_event(audit_log_path, AuditEvent(
                timestamp=datetime.now(timezone.utc).isoformat(),
                event_type="synthesis_aborted_dispatcher_error",
                query=question,
                source_handle=None,
                reason=str(exc),
                detail={"exception_type": type(exc).__name__},
            ))
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
        if audit_log_path is not None:
            log_event(audit_log_path, AuditEvent(
                timestamp=datetime.now(timezone.utc).isoformat(),
                event_type="synthesis_aborted_attribution",
                query=question,
                source_handle=None,
                reason=f"{len(check.untagged_claims)} untagged supporting-evidence claim(s)",
                detail={"untagged_claims": check.untagged_claims},
            ))
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


def _ordered_source_list(sources: list[LibrarySource]) -> list[LibrarySource]:
    """Return sources in render order: local first, then alphabetical by name."""
    local = [s for s in sources if s.name == "local"]
    others = sorted((s for s in sources if s.name != "local"), key=lambda s: s.name)
    return local + others


def _render_header(
    sources: list[LibrarySource],
    with_findings: list[str],
    failed: list[str],
    no_evidence: list[str],
) -> str:
    all_names = [s.name for s in _ordered_source_list(sources)]
    lines = [
        "# Knowledge Base Query Results",
        "",
        f"**Sources queried:** {', '.join(all_names)}",
        f"**Sources with findings:** "
        f"{', '.join(with_findings) if with_findings else '(none)'}",
    ]
    if no_evidence:
        lines.append(
            f"**Sources with no evidence on this topic:** {', '.join(no_evidence)}"
        )
    if failed:
        lines.append(f"**Sources that failed:** {', '.join(failed)}")
    return "\n".join(lines)
