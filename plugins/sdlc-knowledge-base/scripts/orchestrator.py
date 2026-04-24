"""kb-query orchestrator: dispatch, collect, per-source attribution post-check, render.

The orchestrator is pure Python; the `dispatcher` callable abstracts the
Agent tool call so tests can inject mocks. The kb-query skill wires in a
real dispatcher backed by parallel Agent invocations.

Phase A of EPIC #164 — see spec §3.2, §6.1.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

from .attribution import check_retrieval_attribution
from .priming import PrimingBundle
from .registry import LibrarySource


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
