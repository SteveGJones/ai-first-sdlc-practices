#!/usr/bin/env python3
"""REQ-quality linter — flags function-shaped requirements (F-010 v0.2.0).

A capability-shaped REQ opens with WHO does WHAT and WHY. A function-shaped REQ
opens with a Python identifier or uses implementation vocabulary like 'function'
or 'method'. This linter is advisory; it is intended to be wired into CI as a
warning-only check at first, then promoted to a blocker once the corpus is clean.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

_REQ_HEADING_RE = re.compile(r"^###\s+(REQ-[A-Za-z0-9_-]+)\s*$")
_NEXT_BREAK_RE = re.compile(r"^(##|###)\s+")
_FUNCTION_OPENING_RE = re.compile(r"^[a-z_][a-z0-9_]*\s*\(")
_BACKTICK_SPAN_RE = re.compile(r"`[^`]*`")
_FUNCTION_WORD_RE = re.compile(r"\bfunction\b")
_METHOD_WORD_RE = re.compile(r"\bmethod\b")


@dataclass(frozen=True)
class Flag:
    file: Path
    line: int
    req_id: str
    rule: str
    snippet: str


def _strip_backticks(text: str) -> str:
    return _BACKTICK_SPAN_RE.sub("", text)


def _strip_inline_code_around_identifier(line: str) -> str:
    """Turn '`my_func(x)` SHALL...' into 'my_func(x) SHALL...' for opening detection."""
    # only strip leading backticks of the form `<ident>(...)`
    m = re.match(r"^`([a-z_][a-z0-9_]*\s*\([^`]*\))`\s*", line)
    if m:
        return m.group(1) + line[m.end():]
    return line


def lint_file(path: Path) -> List[Flag]:
    flags: List[Flag] = []
    text = path.read_text()
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        m = _REQ_HEADING_RE.match(line.strip())
        if m is None:
            i += 1
            continue
        req_id = m.group(1)
        heading_line = i + 1  # 1-based
        body_lines: List[str] = []
        j = i + 1
        while j < len(lines):
            if _NEXT_BREAK_RE.match(lines[j]):
                break
            body_lines.append(lines[j])
            j += 1
        # find first non-blank body line that isn't a metadata field
        first_content = ""
        for bl in body_lines:
            stripped = bl.strip()
            if not stripped:
                continue
            if stripped.startswith("**"):
                continue
            first_content = stripped
            break
        if first_content:
            opening = _strip_inline_code_around_identifier(first_content)
            if _FUNCTION_OPENING_RE.match(opening):
                flags.append(Flag(
                    file=path, line=heading_line, req_id=req_id,
                    rule="function-shaped opening",
                    snippet=first_content[:80],
                ))
        # check body for 'function' / 'method' outside backticks
        body_joined = "\n".join(body_lines)
        body_no_code = _strip_backticks(body_joined)
        if _FUNCTION_WORD_RE.search(body_no_code):
            flags.append(Flag(
                file=path, line=heading_line, req_id=req_id,
                rule="implementation vocabulary 'function'",
                snippet=first_content[:80] if first_content else "",
            ))
        if _METHOD_WORD_RE.search(body_no_code):
            flags.append(Flag(
                file=path, line=heading_line, req_id=req_id,
                rule="implementation vocabulary 'method'",
                snippet=first_content[:80] if first_content else "",
            ))
        i = j
    return flags


def lint_corpus(root: Path) -> List[Flag]:
    flags: List[Flag] = []
    for spec_file in sorted(root.rglob("requirements-spec.md")):
        if "archive" in spec_file.parts:
            continue
        flags.extend(lint_file(spec_file))
    return flags


def main(argv: List[str]) -> int:
    """Run the REQ-quality linter.

    Default mode: advisory — prints flags and exits 0. This matches the
    "advisory at first, promoted to a blocker once the corpus is clean"
    intent documented at the top of this module. v0.3.0 will wire `--strict`
    into CI as a blocking gate.

    --strict: hard-fail mode — exits 1 when any flag is reported. Use this
    when the corpus is expected to be clean (e.g., per-PR enforcement once
    promoted).
    """
    args = [a for a in argv[1:] if not a.startswith("-")]
    strict = "--strict" in argv[1:]
    root = Path(args[0]) if args else Path("docs/specs")
    if not root.exists():
        print(f"check-req-quality: root not found: {root}", file=sys.stderr)
        return 2
    flags = lint_corpus(root)
    for f in flags:
        print(f"{f.file}:{f.line}: {f.req_id} — {f.rule}: '{f.snippet}'")
    if not flags:
        return 0
    if strict:
        return 1
    print(
        f"\ncheck-req-quality: {len(flags)} advisory flag(s) — exit 0 in default "
        "(advisory) mode. Run with --strict to fail on flags.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
