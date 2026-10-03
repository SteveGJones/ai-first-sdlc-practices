#!/usr/bin/env python3
"""extract_answer.py — answer-contract extraction library + CLI.

Stage 2 contract §2 (docs/superpowers/specs/2026-07-25-sdlc-model-council-design.md
§2.1/§2.3; stage2-contract.md §2). Python 3 stdlib only.

Parses a model's raw last-message text according to one of five answer
contracts: text | file-blocks | findings-json | strict-json | verdict-line.
This module is the SINGLE SOURCE OF TRUTH for that parsing — the scorers
under scripts/council/score/ import these functions rather than re-parsing.

CLI:
    extract_answer.py <contract> <raw-file>

Prints the extracted value (plain text for text/verdict-line, json.dumps(...)
for file-blocks/findings-json/strict-json) to stdout. Exit 0 on success, exit
3 on contract-fail (unparseable / absent for the given contract), exit 2 on
CLI usage error (bad contract name / wrong arg count).
"""

import json
import re
import sys

_FILE_BLOCK_RE = re.compile(
    r"```file:(?P<name>\S+)[^\n]*\n(?P<body>.*?)\n```[ \t]*(?=\n|$)",
    re.DOTALL,
)

_VERDICT_RE = re.compile(r"^VERDICT:\s*(.*)$", re.MULTILINE)


def extract_text(raw):
    """Stripped text. Never fails — always returns a string (possibly empty)."""
    if raw is None:
        return ""
    return raw.strip()


def extract_file_blocks(raw):
    """Parse ```file:NAME``` fenced blocks -> {name: body}.

    Tolerant of leading/trailing prose around the fences and of an optional
    language hint trailing the name on the opening fence line (e.g.
    ```file:foo.py python```). Returns {} if no fenced file blocks are found.
    """
    if raw is None:
        return {}
    blocks = {}
    for match in _FILE_BLOCK_RE.finditer(raw):
        name = match.group("name")
        body = match.group("body")
        blocks[name] = body
    return blocks


def _find_first_json(raw, marker, wanted_type):
    """Scan raw left-to-right for the first JSON value of wanted_type that
    starts at an occurrence of `marker` ('[' or '{'). Works whether the JSON
    is bare in the text or embedded inside a ```json fence — the decoder
    only cares about the character span, not what surrounds it. Returns None
    if no such value is found.
    """
    if raw is None:
        return None
    decoder = json.JSONDecoder()
    idx = 0
    while True:
        idx = raw.find(marker, idx)
        if idx == -1:
            return None
        try:
            obj, _end = decoder.raw_decode(raw, idx)
        except json.JSONDecodeError:
            idx += 1
            continue
        if isinstance(obj, wanted_type):
            return obj
        idx += 1


def extract_findings_json(raw):
    """Pull the first top-level JSON array from raw (bare or ```json fenced).
    Returns None on parse failure (no JSON array found anywhere in raw).
    """
    return _find_first_json(raw, "[", list)


def extract_strict_json(raw):
    """Pull the first top-level JSON object from raw (bare or ```json fenced).
    Returns None on parse failure (no JSON object found anywhere in raw).
    """
    return _find_first_json(raw, "{", dict)


def extract_verdict_line(raw):
    """Value after the first line matching ^VERDICT:\\s* (case-sensitive,
    anchored at line start). Returns the remainder of that line (e.g.
    "APPROVE — reason"), or None if no such line is present.
    """
    if raw is None:
        return None
    match = _VERDICT_RE.search(raw)
    if match is None:
        return None
    return match.group(1).rstrip()


def _cli_usage_error(msg):
    sys.stderr.write("extract_answer.py: %s\n" % msg)
    sys.stderr.write(__doc__ or "")
    sys.exit(2)


def main(argv):
    if len(argv) != 3:
        _cli_usage_error(
            "usage: extract_answer.py <contract> <raw-file> "
            "(got %d args)" % (len(argv) - 1)
        )

    contract = argv[1]
    raw_file = argv[2]

    valid_contracts = (
        "text",
        "file-blocks",
        "findings-json",
        "strict-json",
        "verdict-line",
    )
    if contract not in valid_contracts:
        _cli_usage_error(
            "unknown contract '%s' — must be one of %s"
            % (contract, ", ".join(valid_contracts))
        )

    try:
        with open(raw_file, "r", encoding="utf-8") as f:
            raw = f.read()
    except OSError as exc:
        _cli_usage_error("cannot read raw-file '%s': %s" % (raw_file, exc))
        return  # unreachable; _cli_usage_error exits

    if contract == "text":
        text = extract_text(raw)
        if text == "":
            sys.exit(3)
        sys.stdout.write(text + "\n")
        sys.exit(0)

    if contract == "verdict-line":
        verdict = extract_verdict_line(raw)
        if verdict is None:
            sys.exit(3)
        sys.stdout.write(verdict + "\n")
        sys.exit(0)

    if contract == "file-blocks":
        blocks = extract_file_blocks(raw)
        if not blocks:
            sys.exit(3)
        sys.stdout.write(json.dumps(blocks) + "\n")
        sys.exit(0)

    if contract == "findings-json":
        findings = extract_findings_json(raw)
        if findings is None:
            sys.exit(3)
        sys.stdout.write(json.dumps(findings) + "\n")
        sys.exit(0)

    if contract == "strict-json":
        obj = extract_strict_json(raw)
        if obj is None:
            sys.exit(3)
        sys.stdout.write(json.dumps(obj) + "\n")
        sys.exit(0)

    # Unreachable: contract already validated against valid_contracts above.
    _cli_usage_error("unhandled contract '%s'" % contract)


if __name__ == "__main__":
    main(sys.argv)
