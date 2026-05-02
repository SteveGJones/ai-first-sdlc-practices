"""Parse phase artefact markdown to extract declared IDs and cross-phase references.

Each phase artefact (requirements-spec, design-spec, test-spec) declares IDs via
H3 headings of the form ``### TYPE-<feature-id>-NNN`` and (for design-spec and
test-spec) references prior-phase IDs via ``**satisfies:**`` lines.

The parser is line-wise and skips fenced code blocks, blockquotes, HTML comments,
and inline code spans so that IDs in non-prose contexts don't pollute the parse.

Used by the four phase-gate validators in ``gates.py``.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

VALID_PHASES = {"requirements", "design", "test"}

# Phase → ID type prefix
_PHASE_TO_PREFIX = {
    "requirements": "REQ",
    "design": "DES",
    "test": "TEST",
}

_FEATURE_ID_RE = re.compile(
    r"^\*\*Feature-id:\*\*\s+([a-z0-9][a-z0-9-]*)\s*$", re.MULTILINE
)
_HEADING_ID_RE = re.compile(r"^###\s+(?P<id>(?:REQ|DES|TEST)-[a-z0-9][a-z0-9-]*-\d+)\b")
_SATISFIES_RE = re.compile(r"^\*\*satisfies:\*\*\s+(?P<refs>.+)$")
_REF_ID_RE = re.compile(r"\b((?:REQ|DES)-[a-z0-9][a-z0-9-]*-\d+)\b")
_INLINE_CODE_RE = re.compile(r"`[^`]*`")


def _strip_inline_code(text: str) -> str:
    """Remove inline code spans (`` `...` ``) from *text* so their contents
    are not matched as ID references."""
    return _INLINE_CODE_RE.sub("", text)


class SpecParseError(Exception):
    """Raised when a phase artefact cannot be parsed."""


@dataclass
class ParsedSpec:
    """Parsed phase artefact."""

    feature_id: str
    phase: str
    declared_ids: set[str] = field(default_factory=set)
    references: set[str] = field(default_factory=set)


def parse_spec(path: Path, phase: str) -> ParsedSpec:
    """Parse a phase artefact and extract declared IDs + cross-phase references.

    Skips IDs inside fenced code blocks (``` blocks).
    """
    # implements: DES-programme-substrate-001
    if phase not in VALID_PHASES:
        raise SpecParseError(
            f"Unknown phase '{phase}'; must be one of {sorted(VALID_PHASES)}"
        )

    if not path.exists():
        raise SpecParseError(f"Phase artefact not found: {path}")

    text = path.read_text()

    # Extract feature-id (first occurrence wins; required)
    match = _FEATURE_ID_RE.search(text)
    if match is None:
        raise SpecParseError(
            f"Phase artefact missing **Feature-id:** line (no feature-id "
            f"declared): {path}"
        )
    feature_id = match.group(1)

    declared_ids: set[str] = set()
    references: set[str] = set()
    expected_prefix = _PHASE_TO_PREFIX[phase]

    in_code_block = False
    in_html_comment = False
    for line in text.splitlines():
        stripped = line.strip()

        # Track fenced code blocks
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        # Track multi-line HTML comments and skip comment lines
        if in_html_comment:
            if "-->" in line:
                in_html_comment = False
            continue
        if stripped.startswith("<!--"):
            if "-->" not in line:
                in_html_comment = True
            continue

        # Skip blockquote lines
        if stripped.startswith(">"):
            continue

        # H3 headings — declared IDs (only those matching this phase's prefix)
        heading_match = _HEADING_ID_RE.match(line)
        if heading_match:
            heading_id = heading_match.group("id")
            if heading_id.startswith(expected_prefix + "-"):
                declared_ids.add(heading_id)
            continue

        # **satisfies:** lines — cross-phase references
        satisfies_match = _SATISFIES_RE.match(line)
        if satisfies_match:
            refs_text = _strip_inline_code(satisfies_match.group("refs"))
            for ref in _REF_ID_RE.findall(refs_text):
                references.add(ref)

    return ParsedSpec(
        feature_id=feature_id,
        phase=phase,
        declared_ids=declared_ids,
        references=references,
    )
