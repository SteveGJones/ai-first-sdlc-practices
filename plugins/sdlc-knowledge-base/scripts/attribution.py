"""Structural attribution post-check for cross-library kb-query output.

The one invariant that must never silently fail: every finding and every
synthesis claim has a source library handle tag. This is a hard invariant
enforced by the skill before returning output to the user.

Phase A of EPIC #164 — see spec §7.1.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class RetrievalCheckResult:
    passed: bool
    cleaned_output: str
    dropped_blocks: list[str] = field(default_factory=list)


@dataclass
class SynthesisCheckResult:
    passed: bool
    untagged_claims: list[str] = field(default_factory=list)


# A retrieval finding block starts with "### " and is terminated by the next
# "### " or "---" or EOF. Each block must contain "**Source library**:".
_FINDING_BLOCK_RE = re.compile(
    r"(###\s+[^\n]+\n(?:(?!###\s+|^---\s*$).|\n)*)",
    re.MULTILINE,
)

# In synthesis output, a supporting evidence item is a numbered or bulleted
# line under a "**Supporting evidence**:" heading. Each must contain "[<handle>]".
_SUPPORTING_EVIDENCE_SECTION_RE = re.compile(
    r"\*\*Supporting evidence\*\*:\s*\n((?:\s*[\d\-\*][\.\)]?\s+.+\n?)+)",
    re.MULTILINE,
)
_EVIDENCE_ITEM_RE = re.compile(r"^\s*[\d\-\*][\.\)]?\s+(.+)$", re.MULTILINE)
_HANDLE_TAG_RE = re.compile(r"\[[\w-]+\]")


def check_retrieval_attribution(output: str) -> RetrievalCheckResult:
    """Verify every '### ' finding block has a '**Source library**:' tag.

    Blocks without the tag are dropped from cleaned_output and returned in
    dropped_blocks for logging. Empty or tag-free input returns passed=True.
    """
    if not output.strip():
        return RetrievalCheckResult(passed=True, cleaned_output=output)

    kept_parts: list[str] = []
    dropped: list[str] = []
    last_end = 0
    for match in _FINDING_BLOCK_RE.finditer(output):
        block_text = match.group(1)
        start, end = match.span(1)
        # Keep everything between blocks (headers, separators)
        kept_parts.append(output[last_end:start])
        if "**Source library**:" in block_text:
            kept_parts.append(block_text)
        else:
            # Summarise the first line (the '### ' title) for the dropped log
            first_line = block_text.splitlines()[0].lstrip("# ").strip()
            dropped.append(first_line)
        last_end = end
    kept_parts.append(output[last_end:])
    cleaned = "".join(kept_parts)

    return RetrievalCheckResult(
        passed=(len(dropped) == 0),
        cleaned_output=cleaned,
        dropped_blocks=dropped,
    )


def check_synthesis_attribution(output: str) -> SynthesisCheckResult:
    """Verify every supporting-evidence item has an inline [handle] tag.

    Any untagged item causes passed=False; the caller is expected to abort
    the synthesis and return the retrieval-only output with an error block.
    """
    untagged: list[str] = []
    for section_match in _SUPPORTING_EVIDENCE_SECTION_RE.finditer(output):
        section_body = section_match.group(1)
        for item_match in _EVIDENCE_ITEM_RE.finditer(section_body):
            item_text = item_match.group(1).strip()
            if not _HANDLE_TAG_RE.search(item_text):
                untagged.append(item_text)

    return SynthesisCheckResult(
        passed=(len(untagged) == 0),
        untagged_claims=untagged,
    )
