"""kb-query orchestrator: dispatch, collect, per-source attribution post-check, render.

The orchestrator is pure Python; the `dispatcher` callable abstracts the
Agent tool call so tests can inject mocks. The kb-query skill wires in a
real dispatcher backed by parallel Agent invocations.

Phase A of EPIC #164 — see spec §3.2, §6.1.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

import json as _json

from .attribution import check_retrieval_attribution
from .priming import PrimingBundle
from .registry import LibrarySource


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
        cleaned = check.cleaned_output.rstrip()

        if cleaned.strip() and "### " in cleaned:
            sources_with_findings.append(source.name)
            per_source_sections[source.name] = (
                f"## [{source.name}] Findings\n\n{cleaned}\n"
            )
        else:
            # All findings from this source were dropped by attribution check
            no_evidence.append(source.name)
            per_source_sections[source.name] = (
                f"## [{source.name}] — no valid findings after attribution check\n\n"
                f"[{source.name}] library had findings but none passed attribution check.\n"
            )

    # Render ordered output: local first, then externals alphabetical
    ordered = _ordered_source_list(sources)
    ordered_sections = [per_source_sections[s.name] for s in ordered if s.name in per_source_sections]
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
        f"**Sources with findings:** {', '.join(with_findings) if with_findings else '(none)'}",
    ]
    if no_evidence:
        lines.append(f"**Sources with no evidence on this topic:** {', '.join(no_evidence)}")
    if failed:
        lines.append(f"**Sources that failed:** {', '.join(failed)}")
    return "\n".join(lines)
