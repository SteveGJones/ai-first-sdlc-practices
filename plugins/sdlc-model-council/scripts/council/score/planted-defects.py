#!/usr/bin/env python3
"""score/planted-defects.py — code-review dimension scorer
(stage2-contract.md §3).

Invocation: planted-defects.py <item-dir> <answer-file> <workdir>
Writes <workdir>/score.json {"score":float,"status":"scored|contract-fail|error",
"details":{recall,precision,tp,fp,fn,matched_defect_ids}}. Always exit 0.

Mechanics: extract_findings_json(raw) -> list of {"file","line","message"} ->
match each finding (in returned order, capped at max_findings_counted — an
anti-shotgun measure) to expected/defects.json entries by file + line-window
(|finding.line - defect.line| <= line_window) OR any of the defect's
match_any regexes (re.search, IGNORECASE) against finding.message. Each
defect may be matched by at most one finding (first match wins, in returned
order). score = F1(recall, precision) where recall = matched/total-defects
and precision = tp / min(#findings, max_findings_counted). contract-fail
(score 0.0) if findings-json is unparseable.
"""

import json
import os
import re
import sys

def _load_extract_answer():
    """Import the sibling extract_answer module (its parent dir is not on
    sys.path when this scorer runs from the score/ subdirectory)."""
    council_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if council_dir not in sys.path:
        sys.path.insert(0, council_dir)
    import extract_answer
    return extract_answer

_DEFAULT_LINE_WINDOW = 3
_DEFAULT_MAX_FINDINGS_COUNTED = 8


def write_score(workdir, score, status, details):
    out_path = os.path.join(workdir, "score.json")
    os.makedirs(workdir, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"score": score, "status": status, "details": details}, f)
        f.write("\n")


def _finding_matches_defect(finding, defect, default_line_window):
    f_file = finding.get("file")
    f_line = finding.get("line")
    f_message = finding.get("message", "") or ""

    window = defect.get("line_window", default_line_window)
    if (
        f_file is not None
        and defect.get("file") == f_file
        and f_line is not None
        and isinstance(f_line, (int, float))
        and abs(f_line - defect.get("line", 0)) <= window
    ):
        return True

    for pattern in defect.get("match_any", []) or []:
        if re.search(pattern, f_message, re.IGNORECASE):
            return True

    return False


def match_findings(findings, defects, line_window, max_findings_counted):
    """Returns (tp, fp, matched_defect_ids, precision_denom)."""
    counted = findings[:max_findings_counted]
    matched_ids = set()
    matched_order = []
    tp = 0

    for finding in counted:
        if not isinstance(finding, dict):
            continue
        for defect in defects:
            did = defect.get("id")
            if did in matched_ids:
                continue
            if _finding_matches_defect(finding, defect, line_window):
                matched_ids.add(did)
                matched_order.append(did)
                tp += 1
                break

    fp = len(counted) - tp
    precision_denom = min(len(findings), max_findings_counted)
    return tp, fp, matched_order, precision_denom


def main(argv):
    if len(argv) != 4:
        sys.stderr.write(
            "usage: planted-defects.py <item-dir> <answer-file> <workdir>\n"
        )
        sys.exit(2)

    item_dir, answer_file, workdir = argv[1], argv[2], argv[3]

    try:
        extract_answer = _load_extract_answer()
        with open(answer_file, "r", encoding="utf-8") as f:
            raw = f.read()

        item_path = os.path.join(item_dir, "item.json")
        with open(item_path, "r", encoding="utf-8") as f:
            item = json.load(f)
        scorer_cfg = item.get("scorer", {}) or {}
        line_window = scorer_cfg.get("line_window", _DEFAULT_LINE_WINDOW)
        max_findings_counted = scorer_cfg.get(
            "max_findings_counted", _DEFAULT_MAX_FINDINGS_COUNTED
        )

        defects_path = os.path.join(item_dir, "expected", "defects.json")
        with open(defects_path, "r", encoding="utf-8") as f:
            defects = json.load(f)
        total_defects = len(defects)

        findings = extract_answer.extract_findings_json(raw)

        if findings is None:
            write_score(
                workdir,
                0.0,
                "contract-fail",
                {
                    "recall": 0.0,
                    "precision": 0.0,
                    "tp": 0,
                    "fp": 0,
                    "fn": total_defects,
                    "matched_defect_ids": [],
                },
            )
            sys.exit(0)

        tp, fp, matched_ids, precision_denom = match_findings(
            findings, defects, line_window, max_findings_counted
        )
        fn = total_defects - len(matched_ids)
        recall = (len(matched_ids) / total_defects) if total_defects > 0 else 0.0
        precision = (tp / precision_denom) if precision_denom > 0 else 0.0
        if (precision + recall) > 0:
            f1 = 2 * precision * recall / (precision + recall)
        else:
            f1 = 0.0

        write_score(
            workdir,
            round(f1, 4),
            "scored",
            {
                "recall": round(recall, 4),
                "precision": round(precision, 4),
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "matched_defect_ids": matched_ids,
            },
        )
    except Exception as exc:  # scorer ABI: always exit 0
        write_score(workdir, 0.0, "error", {"error": str(exc)})

    sys.exit(0)


if __name__ == "__main__":
    main(sys.argv)
