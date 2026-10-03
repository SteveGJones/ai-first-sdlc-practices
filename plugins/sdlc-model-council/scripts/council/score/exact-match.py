#!/usr/bin/env python3
"""score/exact-match.py — long-context dimension scorer (stage2-contract.md §3).

Invocation: exact-match.py <item-dir> <answer-file> <workdir>
Writes <workdir>/score.json {"score":float,"status":"scored|error",
"details":{normalized_answer,normalized_expected,match}}. Always exit 0.

Mechanics: extract_text(raw) -> normalize both the extracted answer and
expected/answer.txt (strip, collapse internal whitespace to a single space,
casefold) -> score 1.0 if equal else 0.0. extract_text never fails, so this
scorer has no contract-fail status — only scored, or error on infra failure
(e.g. missing expected/answer.txt).
"""

import json
import os
import re
import sys

_WS_RE = re.compile(r"\s+")


def _load_extract_answer():
    """Import the sibling extract_answer module (its parent dir is not on
    sys.path when this scorer runs from the score/ subdirectory)."""
    council_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if council_dir not in sys.path:
        sys.path.insert(0, council_dir)
    import extract_answer
    return extract_answer


def normalize(s):
    return _WS_RE.sub(" ", s.strip()).casefold()


def write_score(workdir, score, status, details):
    out_path = os.path.join(workdir, "score.json")
    os.makedirs(workdir, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"score": score, "status": status, "details": details}, f)
        f.write("\n")


def main(argv):
    if len(argv) != 4:
        sys.stderr.write(
            "usage: exact-match.py <item-dir> <answer-file> <workdir>\n"
        )
        sys.exit(2)

    item_dir, answer_file, workdir = argv[1], argv[2], argv[3]

    try:
        extract_answer = _load_extract_answer()
        with open(answer_file, "r", encoding="utf-8") as f:
            raw = f.read()

        expected_path = os.path.join(item_dir, "expected", "answer.txt")
        with open(expected_path, "r", encoding="utf-8") as f:
            expected_raw = f.read()

        answer_text = extract_answer.extract_text(raw)
        norm_answer = normalize(answer_text)
        norm_expected = normalize(expected_raw)
        match = norm_answer == norm_expected
        score = 1.0 if match else 0.0

        write_score(
            workdir,
            score,
            "scored",
            {
                "normalized_answer": norm_answer,
                "normalized_expected": norm_expected,
                "match": match,
            },
        )
    except Exception as exc:  # scorer ABI: always exit 0
        write_score(workdir, 0.0, "error", {"error": str(exc)})

    sys.exit(0)


if __name__ == "__main__":
    main(sys.argv)
