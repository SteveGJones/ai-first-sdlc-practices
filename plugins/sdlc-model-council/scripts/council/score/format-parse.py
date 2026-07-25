#!/usr/bin/env python3
"""score/format-parse.py — instruction-format dimension scorer
(stage2-contract.md §3).

Invocation: format-parse.py <item-dir> <answer-file> <workdir>
Writes <workdir>/score.json {"score":float,"status":"scored|contract-fail|error",
"details":{satisfied,total,failed_constraints}}. Always exit 0.

Mechanics: extract_strict_json(raw) -> validate against expected/schema.json
mini-schema: {"required_keys":[...], "types":{key:"string|number|integer|
boolean|array|object"}, "enums":{key:[allowed...]}, "array_min_len":{key:int}}.
Each listed constraint is one scoring unit; score = satisfied/total. A
missing required key fails its own presence constraint AND any type/enum/
array_min_len constraint keyed on it. contract-fail (score 0.0) if the
extracted answer is not a JSON object at all.
"""

import json
import os
import sys

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


def _type_ok(value, type_name):
    if type_name == "string":
        return isinstance(value, str)
    if type_name == "boolean":
        return isinstance(value, bool)
    if type_name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if type_name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if type_name == "array":
        return isinstance(value, list)
    if type_name == "object":
        return isinstance(value, dict)
    # Unknown type name in the schema: treat as an unsatisfiable constraint
    # rather than silently passing it.
    return False


def check_schema(obj, schema):
    """Returns (satisfied, total, failed_constraints)."""
    failed = []
    total = 0
    satisfied = 0

    required_keys = schema.get("required_keys", []) or []
    types = schema.get("types", {}) or {}
    enums = schema.get("enums", {}) or {}
    array_min_len = schema.get("array_min_len", {}) or {}

    for key in required_keys:
        total += 1
        if key in obj:
            satisfied += 1
        else:
            failed.append("required:%s" % key)

    for key, type_name in types.items():
        total += 1
        if key in obj and _type_ok(obj[key], type_name):
            satisfied += 1
        else:
            failed.append("type:%s" % key)

    for key, allowed in enums.items():
        total += 1
        if key in obj and obj[key] in allowed:
            satisfied += 1
        else:
            failed.append("enum:%s" % key)

    for key, min_len in array_min_len.items():
        total += 1
        if key in obj and isinstance(obj[key], list) and len(obj[key]) >= min_len:
            satisfied += 1
        else:
            failed.append("array_min_len:%s" % key)

    return satisfied, total, failed


def main(argv):
    if len(argv) != 4:
        sys.stderr.write(
            "usage: format-parse.py <item-dir> <answer-file> <workdir>\n"
        )
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
                {"satisfied": 0, "total": 0, "failed_constraints": ["not-a-json-object"]},
            )
            sys.exit(0)

        schema_path = os.path.join(item_dir, "expected", "schema.json")
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)

        satisfied, total, failed = check_schema(obj, schema)
        score = round((satisfied / total), 4) if total > 0 else 1.0

        write_score(
            workdir,
            score,
            "scored",
            {"satisfied": satisfied, "total": total, "failed_constraints": failed},
        )
    except Exception as exc:  # scorer ABI: always exit 0
        write_score(workdir, 0.0, "error", {"error": str(exc)})

    sys.exit(0)


if __name__ == "__main__":
    main(sys.argv)
