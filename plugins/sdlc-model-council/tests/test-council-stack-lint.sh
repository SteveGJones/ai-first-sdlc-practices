#!/usr/bin/env bash
# Lint the v1 assessment problem stack: schema shape, referenced files exist,
# scorer types are known, envelopes present, sha256 hashes match stack.json,
# and no item-id collisions. Prints "=== Results: N passed, M failed ===" and
# exits nonzero on any failure. Stdlib Python 3 only; bash 3.2 compatible.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
STACK_DIR="${PLUGIN_DIR}/assessment/stack/v1"

if [ ! -d "${STACK_DIR}" ]; then
    echo "FATAL: stack directory not found: ${STACK_DIR}"
    echo "=== Results: 0 passed, 1 failed ==="
    exit 1
fi

PY_EXIT_FILE="$(mktemp 2>/dev/null || echo "${STACK_DIR}/.lint-exit.tmp")"

python3 - "${PLUGIN_DIR}" "${STACK_DIR}" "${PY_EXIT_FILE}" << 'PYEOF'
import json
import os
import re
import sys

plugin_dir, stack_dir, exit_file = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, os.path.join(plugin_dir, "scripts", "council"))
import stack_hash  # noqa: E402

passed = 0
failed = 0
failures = []


def check(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
    else:
        failed += 1
        msg = f"FAIL: {name}"
        if detail:
            msg += f" — {detail}"
        failures.append(msg)


KNOWN_SCORER_TYPES = {"hidden-tests", "planted-defects", "exact-match", "format-parse"}
KNOWN_ANSWER_CONTRACTS = {"text", "file-blocks", "findings-json", "strict-json", "verdict-line"}
ENVELOPE_SNIPPETS = {
    "file-blocks": "```file:NAME``` fenced",
    "findings-json": "JSON array of findings",
    "text": "answer text on a single line",
    "strict-json": "single JSON object",
    "verdict-line": "VERDICT:",
}
REQUIRED_ITEM_KEYS = {
    "schema_version", "id", "dimension", "version", "difficulty", "timeout_s",
    "min_context_tokens", "est_prompt_tokens", "est_output_tokens",
    "answer_contract", "scorer",
}

stack_json_path = os.path.join(stack_dir, "stack.json")
stack_data = None
try:
    with open(stack_json_path) as f:
        raw_text = f.read()
    stack_data = json.loads(raw_text)
    check("stack.json parses as JSON", True)
except (OSError, json.JSONDecodeError) as exc:
    check("stack.json parses as JSON", False, str(exc))

if stack_data is not None:
    check("stack.json has schema_version", stack_data.get("schema_version") == 1)
    check("stack.json has stack_version", stack_data.get("stack_version") == "v1")
    items = stack_data.get("items")
    check("stack.json has a non-empty items list", isinstance(items, list) and len(items) > 0)
    items = items or []

    check("stack has exactly 9 items", len(items) == 9, f"found {len(items)}")

    seen_ids = set()
    for entry in items:
        item_id = entry.get("id", "<missing-id>")
        check(
            f"{item_id}: no id collision",
            item_id not in seen_ids,
            f"duplicate id {item_id}",
        )
        seen_ids.add(item_id)

        rel_path = entry.get("path")
        item_dir = os.path.join(stack_dir, rel_path) if rel_path else None
        item_dir_exists = bool(item_dir) and os.path.isdir(item_dir)
        check(f"{item_id}: stack.json path exists on disk", item_dir_exists, str(rel_path))
        if not item_dir_exists:
            continue

        # --- item.json ---
        item_json_path = os.path.join(item_dir, "item.json")
        item_json = None
        try:
            with open(item_json_path) as f:
                item_json = json.load(f)
            check(f"{item_id}: item.json parses as JSON", True)
        except (OSError, json.JSONDecodeError) as exc:
            check(f"{item_id}: item.json parses as JSON", False, str(exc))

        scorer_type = None
        answer_contract = None
        if item_json is not None:
            missing_keys = REQUIRED_ITEM_KEYS - set(item_json.keys())
            check(
                f"{item_id}: item.json has all required keys",
                not missing_keys,
                f"missing {sorted(missing_keys)}" if missing_keys else "",
            )
            check(
                f"{item_id}: item.json id matches stack.json id",
                item_json.get("id") == item_id,
            )
            check(
                f"{item_id}: item.json dimension matches stack.json dimension",
                item_json.get("dimension") == entry.get("dimension"),
            )
            answer_contract = item_json.get("answer_contract")
            check(
                f"{item_id}: answer_contract is known",
                answer_contract in KNOWN_ANSWER_CONTRACTS,
                str(answer_contract),
            )
            scorer = item_json.get("scorer")
            scorer_type = scorer.get("type") if isinstance(scorer, dict) else None
            check(
                f"{item_id}: scorer.type is known",
                scorer_type in KNOWN_SCORER_TYPES,
                str(scorer_type),
            )
            if scorer_type == "planted-defects" and isinstance(scorer, dict):
                check(
                    f"{item_id}: planted-defects scorer has line_window",
                    isinstance(scorer.get("line_window"), int),
                )
                check(
                    f"{item_id}: planted-defects scorer has max_findings_counted",
                    isinstance(scorer.get("max_findings_counted"), int),
                )

        # --- prompt.md envelope ---
        prompt_path = os.path.join(item_dir, "prompt.md")
        prompt_exists = os.path.isfile(prompt_path)
        check(f"{item_id}: prompt.md exists", prompt_exists)
        if prompt_exists:
            with open(prompt_path, encoding="utf-8") as f:
                prompt_text = f.read()
            non_empty_lines = [ln for ln in prompt_text.splitlines() if ln.strip()]
            last_line = non_empty_lines[-1] if non_empty_lines else ""
            check(f"{item_id}: prompt.md ends with a non-empty line", bool(last_line))
            if answer_contract in ENVELOPE_SNIPPETS:
                snippet = ENVELOPE_SNIPPETS[answer_contract]
                check(
                    f"{item_id}: prompt.md envelope matches its answer_contract ({answer_contract})",
                    snippet in last_line,
                    f"expected snippet {snippet!r} in last line {last_line!r}",
                )

        # --- inputs/ exists (shown-to-model material) ---
        inputs_dir = os.path.join(item_dir, "inputs")
        check(f"{item_id}: inputs/ directory exists", os.path.isdir(inputs_dir))

        # --- expected/ per scorer type ---
        expected_dir = os.path.join(item_dir, "expected")
        check(f"{item_id}: expected/ directory exists", os.path.isdir(expected_dir))

        if scorer_type == "planted-defects":
            defects_path = os.path.join(expected_dir, "defects.json")
            defects_exists = os.path.isfile(defects_path)
            check(f"{item_id}: expected/defects.json exists", defects_exists)
            if defects_exists:
                try:
                    with open(defects_path) as f:
                        defects = json.load(f)
                    check(f"{item_id}: expected/defects.json parses as JSON", True)
                    valid_shape = isinstance(defects, list) and len(defects) >= 1 and all(
                        isinstance(d, dict) and {"id", "file", "line", "line_window", "match_any"} <= set(d.keys())
                        for d in defects
                    )
                    check(
                        f"{item_id}: expected/defects.json entries have required keys",
                        valid_shape,
                    )
                except (OSError, json.JSONDecodeError) as exc:
                    check(f"{item_id}: expected/defects.json parses as JSON", False, str(exc))

        elif scorer_type == "hidden-tests":
            tests_dir = os.path.join(expected_dir, "tests")
            tests_dir_exists = os.path.isdir(tests_dir)
            check(f"{item_id}: expected/tests/ directory exists", tests_dir_exists)
            if tests_dir_exists:
                test_files = [
                    fn for fn in os.listdir(tests_dir)
                    if fn.startswith("test_") and fn.endswith(".py")
                ]
                check(
                    f"{item_id}: expected/tests/ has at least one test_*.py",
                    len(test_files) >= 1,
                )

        elif scorer_type == "exact-match":
            answer_path = os.path.join(expected_dir, "answer.txt")
            answer_exists = os.path.isfile(answer_path)
            check(f"{item_id}: expected/answer.txt exists", answer_exists)
            if answer_exists:
                with open(answer_path, encoding="utf-8") as f:
                    answer_text = f.read().strip()
                check(f"{item_id}: expected/answer.txt is non-empty", bool(answer_text))

        elif scorer_type == "format-parse":
            schema_path = os.path.join(expected_dir, "schema.json")
            schema_exists = os.path.isfile(schema_path)
            check(f"{item_id}: expected/schema.json exists", schema_exists)
            if schema_exists:
                try:
                    with open(schema_path) as f:
                        schema = json.load(f)
                    check(f"{item_id}: expected/schema.json parses as JSON", True)
                    check(
                        f"{item_id}: expected/schema.json has required_keys",
                        isinstance(schema.get("required_keys"), list) and len(schema["required_keys"]) > 0,
                    )
                    check(
                        f"{item_id}: expected/schema.json has types",
                        isinstance(schema.get("types"), dict),
                    )
                except (OSError, json.JSONDecodeError) as exc:
                    check(f"{item_id}: expected/schema.json parses as JSON", False, str(exc))

        # --- sha256 recompute matches stack.json ---
        declared_sha = entry.get("sha256", "")
        try:
            recomputed = stack_hash.compute_hash(item_dir)
            check(
                f"{item_id}: recomputed sha256 matches stack.json",
                recomputed == declared_sha,
                f"declared={declared_sha} recomputed={recomputed}",
            )
        except FileNotFoundError as exc:
            check(f"{item_id}: recomputed sha256 matches stack.json", False, str(exc))

    # --- dimension distribution matches the v1 slice (design §8) ---
    from collections import Counter
    dim_counts = Counter(e.get("dimension") for e in items)
    expected_counts = {
        "code-review": 3,
        "bug-fix": 2,
        "long-context": 2,
        "instruction-format": 2,
    }
    for dim, expected_n in expected_counts.items():
        check(
            f"dimension count: {dim} == {expected_n}",
            dim_counts.get(dim) == expected_n,
            f"found {dim_counts.get(dim)}",
        )

for msg in failures:
    print(msg)

print(f"=== Results: {passed} passed, {failed} failed ===")

with open(exit_file, "w") as f:
    f.write("1" if failed > 0 else "0")
PYEOF

PY_STATUS="$(cat "${PY_EXIT_FILE}" 2>/dev/null || echo 1)"
rm -f "${PY_EXIT_FILE}"

if [ "${PY_STATUS}" = "0" ]; then
    exit 0
else
    exit 1
fi
