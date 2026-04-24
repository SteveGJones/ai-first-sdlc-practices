"""Priming bundle construction for cross-library kb-query.

Phase B of EPIC #164 (sub-2, #168). The bundle is consumed by external
librarian invocations via orchestrator.format_dispatch_prompt — see the
research-librarian agent's PRIMING_CONTEXT documentation for how the
librarian uses these fields to bias term-matching and frame findings.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class PrimingBundle:
    """Context passed to external librarians to frame their query.

    Consumed by `orchestrator.format_dispatch_prompt` and rendered into
    the librarian's PRIMING_CONTEXT JSON block. The librarian uses:

    - `local_kb_config_excerpt` — to interpret findings under the project's
      lens (e.g., "Brazilian semiconductor packaging operations")
    - `local_shelf_index_terms` — to bias term-matching against its scoped
      shelf-index, preferring files whose Terms overlap with the local
      project's vocabulary
    """
    question: str
    local_kb_config_excerpt: str = ""
    local_shelf_index_terms: list[str] = field(default_factory=list)


def build_priming_bundle(question: str, project_dir: Path) -> PrimingBundle:
    """Build the priming bundle from the project's local state.

    Missing CLAUDE.md → empty excerpt. Missing [Knowledge Base] section →
    empty excerpt. Missing library/ or shelf-index → empty terms list.
    """
    claude_md_path = project_dir / "CLAUDE.md"
    excerpt = _extract_kb_section(claude_md_path) if claude_md_path.exists() else ""

    shelf_index_path = project_dir / "library" / "_shelf-index.md"
    terms = _extract_shelf_index_terms(shelf_index_path) if shelf_index_path.exists() else []

    return PrimingBundle(
        question=question,
        local_kb_config_excerpt=excerpt,
        local_shelf_index_terms=terms,
    )


def _extract_kb_section(claude_md_path: Path) -> str:
    """Extract the [Knowledge Base] section from CLAUDE.md.

    Matches '## Knowledge Base' (heading) through the next H2 heading or EOF.
    Returns the section body (text after the heading), or empty string.
    """
    content = claude_md_path.read_text()
    match = re.search(
        r"^##\s+Knowledge Base\s*\n(.*?)(?=\n##\s+|\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    )
    if not match:
        return ""
    body = match.group(1).strip()
    # Defence against regex walking past an empty section into the next heading
    if body.startswith("##"):
        return ""
    return body


def _extract_shelf_index_terms(shelf_index_path: Path) -> list[str]:
    """Extract the union of Terms: across all shelf-index entries.

    Each entry has a '**Terms:** ...' line. Return deduplicated, order-preserving.
    """
    content = shelf_index_path.read_text()
    seen: set[str] = set()
    result: list[str] = []
    for match in re.finditer(r"^\*\*Terms:\*\*[ \t]*(.*?)(?=\n|$)", content, re.MULTILINE):
        raw_terms = match.group(1)
        if not raw_terms.strip():
            continue  # empty Terms line, skip
        for term in (t.strip() for t in raw_terms.split(",")):
            if term and term not in seen:
                seen.add(term)
                result.append(term)
    return result
