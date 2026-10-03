#!/usr/bin/env python3
"""score/command-check.py — tool-use dimension scorer for the command-exec and
monitoring dimensions (issue #235; design
docs/superpowers/specs/2026-07-26-council-tool-use-assessment-design.md §4).

Invocation: command-check.py <item-dir> <answer-file> <workdir>
Writes <workdir>/score.json {"score":float,"status":"scored|contract-fail|error",
"details":{satisfied,total,failed_checks}}. Always exit 0.

Mechanics: extract_strict_json(raw) -> validate against expected/checks.json, a
rubric of field-level assertions over the emitted JSON object:

    {"field_checks": [
       {"field": "commands", "regex": "\\bgrep\\b", "flags": "i", "desc": "..."},
       {"field": "commands", "not_regex": "rm\\s+-rf", "desc": "..."},
       {"field": "decision", "equals": "stop"},
       {"field": "decision", "enum": ["stop", "continue"]}
    ]}

Each field_check carries exactly one operator key:
  equals    — pass iff obj[field] == value            (missing field fails)
  enum      — pass iff obj[field] in value             (missing field fails)
  regex     — pass iff re.search(pattern, text) hits   (required pattern present)
  not_regex — pass iff re.search(pattern, text) misses (forbidden pattern absent;
              a missing field is vacuously safe -> pass)

For regex/not_regex the field value is coerced to text: a str is used as-is, a
list is joined with "\n" (multi-command answers scored as a block), a missing/
None field -> "". `flags` letters map to re flags (i/m/s). Each check is one
scoring unit; score = satisfied/total. contract-fail (0.0) if the extracted
answer is not a JSON object at all. This scorer is the tool-use analogue of
format-parse but adds regex-over-a-free-string-value and negative constraints,
which format-parse cannot express.
"""

import json
import os
import re
import sys

_FLAG_MAP = {"i": re.IGNORECASE, "m": re.MULTILINE, "s": re.DOTALL}


def _load_extract_answer():
    """Import the sibling extract_answer module (its parent dir is not on
    sys.path when this scorer runs from the score/ subdirectory)."""
    council_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if council_dir not in sys.path:
        sys.path.insert(0, council_dir)
    import extract_answer

    return extract_answer


def write_score(workdir, score, status, details):
    out_path = os.path.join(workdir, "score.json")
    os.makedirs(workdir, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"score": score, "status": status, "details": details}, f)
        f.write("\n")


def _as_text(value):
    """Coerce a field value to searchable text for regex ops. A list is joined
    with newlines so a multi-command answer is checked as one block; a missing
    (None) field becomes the empty string."""
    if value is None:
        return ""
    if isinstance(value, list):
        return "\n".join("" if v is None else str(v) for v in value)
    if isinstance(value, str):
        return value
    return str(value)


def _compile_flags(flags_str):
    flags = 0
    for ch in flags_str or "":
        flags |= _FLAG_MAP.get(ch, 0)
    return flags


def _check_label(check):
    if check.get("desc"):
        return check["desc"]
    field = check.get("field", "?")
    for op in ("equals", "enum", "regex", "not_regex"):
        if op in check:
            return "%s:%s" % (field, op)
    return field


def _check_passes(check, obj):
    """Evaluate one field_check against the answer object. Returns True/False."""
    field = check.get("field")
    present = isinstance(obj, dict) and field in obj
    value = obj.get(field) if present else None

    if "equals" in check:
        return present and value == check["equals"]
    if "enum" in check:
        allowed = check["enum"]
        return present and isinstance(allowed, list) and value in allowed
    if "regex" in check:
        text = _as_text(value)
        return (
            re.search(check["regex"], text, _compile_flags(check.get("flags")))
            is not None
        )
    if "not_regex" in check:
        # Forbidden pattern must be absent. A missing field -> "" -> absent -> pass.
        text = _as_text(value)
        return (
            re.search(check["not_regex"], text, _compile_flags(check.get("flags")))
            is None
        )
    # A check with no recognised operator key is an unsatisfiable spec error
    # rather than a silent pass.
    return False


def evaluate(obj, checks):
    """Returns (satisfied, total, failed_labels)."""
    field_checks = checks.get("field_checks", []) or []
    satisfied = 0
    failed = []
    for check in field_checks:
        if _check_passes(check, obj):
            satisfied += 1
        else:
            failed.append(_check_label(check))
    return satisfied, len(field_checks), failed


def main(argv):
    if len(argv) != 4:
        sys.stderr.write("usage: command-check.py <item-dir> <answer-file> <workdir>\n")
        sys.exit(2)

    item_dir, answer_file, workdir = argv[1], argv[2], argv[3]

    try:
        extract_answer = _load_extract_answer()
        with open(answer_file, "r", encoding="utf-8") as f:
            raw = f.read()

        obj = extract_answer.extract_strict_json(raw)
        if obj is None:
            write_score(
                workdir,
                0.0,
                "contract-fail",
                {"satisfied": 0, "total": 0, "failed_checks": ["not-a-json-object"]},
            )
            sys.exit(0)

        checks_path = os.path.join(item_dir, "expected", "checks.json")
        with open(checks_path, "r", encoding="utf-8") as f:
            checks = json.load(f)

        satisfied, total, failed = evaluate(obj, checks)
        score = round((satisfied / total), 4) if total > 0 else 1.0

        write_score(
            workdir,
            score,
            "scored",
            {"satisfied": satisfied, "total": total, "failed_checks": failed},
        )
    except Exception as exc:  # scorer ABI: always exit 0
        write_score(workdir, 0.0, "error", {"error": str(exc)})

    sys.exit(0)


if __name__ == "__main__":
    main(sys.argv)
