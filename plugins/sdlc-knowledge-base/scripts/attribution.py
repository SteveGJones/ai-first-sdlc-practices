"""Structural attribution post-check for cross-library kb-query output.

The one invariant that must never silently fail: every finding and every
synthesis claim has a source library handle tag. This is a hard invariant
enforced by the skill before returning output to the user.

Implementation uses a line-wise tokenizer (not regex on markdown) to avoid
boundary bugs with --- separators, subheadings, and fenced code blocks.

Phase A of EPIC #164 — see spec §7.1.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RetrievalCheckResult:
    passed: bool
    cleaned_output: str
    dropped_blocks: list[str] = field(default_factory=list)


@dataclass
class SynthesisCheckResult:
    passed: bool
    untagged_claims: list[str] = field(default_factory=list)


# Typo-tolerant Source library attribution detector.
# Accepts case-insensitive, colon-inside-or-outside-asterisks variants
# so that a single-character template typo doesn't silently drop findings.
_SOURCE_LIBRARY_RE = re.compile(
    r"\*\*\s*source\s+library\s*[:*]+\s*",
    re.IGNORECASE,
)

# Bracketed handle token: [alpha-num-and-hyphens]
_HANDLE_TAG_RE = re.compile(r"\[([\w-]+)\]")


def check_retrieval_attribution(output: str) -> RetrievalCheckResult:
    """Verify every '### ' finding block has a Source library attribution.

    Uses a line-wise tokenizer. A block starts at a line whose first three
    non-whitespace characters are '### ' (not inside a fenced code block)
    and ends at the next such line, OR at a '---' horizontal rule line,
    OR at end of input.

    Content outside any '### ' block is dropped. This includes preamble
    before the first block, inter-block bleeds, separator lines, and
    post-last-block trailers. Attribution survives only inside properly-
    structured blocks.

    Blocks whose lines do not contain a case-insensitive "**Source library**:"
    (or trivial typo variants) are also dropped from cleaned_output. Dropped
    block titles are recorded for debugging.

    Empty or tag-free input returns passed=True with the input unchanged.
    """
    if not output.strip():
        return RetrievalCheckResult(passed=True, cleaned_output=output)

    lines = output.splitlines(keepends=True)
    tokens = _tokenize_retrieval(lines)

    kept: list[str] = []
    dropped: list[str] = []

    # Only block tokens with valid attribution are kept.
    # Everything else (preamble, inter-block content, separators, trailers)
    # is dropped — it has no attribution and must not reach the caller (§7.1).
    for token in tokens:
        if token.kind == "block":
            block_text = "".join(token.lines)
            if _SOURCE_LIBRARY_RE.search(block_text):
                kept.append(block_text)
            else:
                # Record the heading line (stripped) for debuggability
                title = token.lines[0].lstrip("# ").rstrip("\n").strip()
                dropped.append(title)

    return RetrievalCheckResult(
        passed=(len(dropped) == 0),
        cleaned_output="".join(kept),
        dropped_blocks=dropped,
    )


@dataclass
class _Token:
    kind: str  # "block" | "between" | "separator"
    lines: list[str]


def _tokenize_retrieval(lines: list[str]) -> list[_Token]:
    """Split a retrieval output into block / between / separator tokens.

    A block is a run of lines starting with a '### ' heading line,
    ending just before the next '### ' heading line, or a '---' line,
    or end of input. Lines inside fenced code blocks (``` fences) are
    always treated as "between" content and never start a block.
    """
    tokens: list[_Token] = []
    current_kind: Optional[str] = None
    current_lines: list[str] = []
    in_fence = False

    def flush() -> None:
        nonlocal current_kind, current_lines
        if current_lines:
            tokens.append(_Token(kind=current_kind or "between", lines=current_lines))
        current_kind = None
        current_lines = []

    for line in lines:
        stripped = line.rstrip("\n").rstrip("\r")
        if stripped.lstrip().startswith("```"):
            in_fence = not in_fence
            # Fence lines belong to whatever section they started in
            if current_kind is None:
                current_kind = "between"
            current_lines.append(line)
            continue

        if in_fence:
            if current_kind is None:
                current_kind = "between"
            current_lines.append(line)
            continue

        # Separator line "---" terminates any current block
        if stripped.strip() == "---":
            flush()
            tokens.append(_Token(kind="separator", lines=[line]))
            continue

        # Heading line "### " (exactly three hashes + space) starts a new block
        # "#### " (four or more) is NOT a new block.
        if stripped.startswith("### ") and not stripped.startswith("#### "):
            flush()
            current_kind = "block"
            current_lines.append(line)
            continue

        # Otherwise append to current token
        if current_kind is None:
            current_kind = "between"
        current_lines.append(line)

    flush()
    return tokens


def check_synthesis_attribution(
    output: str,
    valid_handles: set[str],
) -> SynthesisCheckResult:
    """Verify every supporting-evidence item has an inline [handle] tag in valid_handles.

    valid_handles is required and is typically the set of source names from
    run_synthesis_query's dispatch sources. Bracketed tokens not in the set
    (e.g., [TODO], [0], [citation-needed]) fail the check.

    Any untagged or out-of-whitelist item causes passed=False; the caller is
    expected to abort the synthesis and return retrieval-only output with an
    error block.
    """
    untagged: list[str] = []
    lines = output.splitlines()
    i = 0
    in_evidence = False
    current_item: list[str] = []

    def check_current() -> None:
        if not current_item:
            return
        item_text = " ".join(s.strip() for s in current_item).strip()
        handle_matches = _HANDLE_TAG_RE.findall(item_text)
        if not handle_matches or not any(h in valid_handles for h in handle_matches):
            untagged.append(item_text)

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("**Supporting evidence**"):
            in_evidence = True
            i += 1
            continue

        if in_evidence:
            # Other ** sections (e.g. **Caveats**) end the evidence section
            if stripped.startswith("**") and not stripped.startswith(
                "**Supporting evidence**"
            ):
                check_current()
                current_item = []
                in_evidence = False
                continue

            # An item start line: begins with a number, dash, or asterisk marker
            if _is_item_start(stripped):
                check_current()
                current_item = [_strip_item_marker(stripped)]
            elif stripped and current_item:
                # Continuation of the current item
                current_item.append(stripped)
            # Blank lines inside evidence don't end the item; they're just whitespace

        i += 1

    if in_evidence:
        check_current()

    return SynthesisCheckResult(
        passed=(len(untagged) == 0),
        untagged_claims=untagged,
    )


_ITEM_MARKER_RE = re.compile(r"^(\d+[\.\)]|[\-\*])\s+")


def _is_item_start(stripped_line: str) -> bool:
    return bool(_ITEM_MARKER_RE.match(stripped_line))


def _strip_item_marker(stripped_line: str) -> str:
    return _ITEM_MARKER_RE.sub("", stripped_line, count=1)
