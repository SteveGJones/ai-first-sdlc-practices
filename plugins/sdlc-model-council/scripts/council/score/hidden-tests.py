#!/usr/bin/env python3
"""score/hidden-tests.py — bug-fix dimension scorer (stage2-contract.md §3).

Invocation: hidden-tests.py <item-dir> <answer-file> <workdir>
Writes <workdir>/score.json {"score":float,"status":"scored|contract-fail|error",
"details":{passed,total,stdout_tail}}. Always exit 0.

Mechanics: extract_file_blocks(raw) -> materialize each {name: body} into
workdir -> copy expected/tests/ alongside -> run stdlib unittest discovery
in a subprocess (python3, stdlib-only) -> score = passed/total. contract-fail
(score 0.0) if no file-blocks were extracted at all. If discovery finds zero
tests, that's an infra/fixture problem, not a model answer to grade ->
status "error" (distinct from contract-fail, which is about the ANSWER).
"""

import json
import os
import shutil
import subprocess
import sys

def _load_extract_answer():
    """Import the sibling extract_answer module (its parent dir is not on
    sys.path when this scorer runs from the score/ subdirectory)."""
    council_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if council_dir not in sys.path:
        sys.path.insert(0, council_dir)
    import extract_answer
    return extract_answer

_STDOUT_TAIL_CHARS = 4000
_TEST_TIMEOUT_S = 60

# Inline runner materialized into workdir: uses unittest's own TestLoader /
# TextTestRunner (stdlib only) so we get exact passed/total counts from the
# TestResult object rather than fragile text-scraping of `-m unittest`
# console output. Named with a leading underscore so unittest's own
# `test_*.py` discovery pattern never picks it up as a test module itself.
_RUNNER_SOURCE = """
import json
import sys
import unittest

loader = unittest.TestLoader()
suite = loader.discover(start_dir=".", pattern="test_*.py")
runner = unittest.TextTestRunner(stream=sys.stdout, verbosity=2)
result = runner.run(suite)
total = result.testsRun
passed = total - len(result.failures) - len(result.errors)
print("RESULT_JSON:" + json.dumps({"passed": passed, "total": total}))
"""


def write_score(workdir, score, status, details):
    out_path = os.path.join(workdir, "score.json")
    os.makedirs(workdir, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"score": score, "status": status, "details": details}, f)
        f.write("\n")


def _safe_join(base, name):
    """Join `name` under `base`, refusing any path that escapes base
    (defence against a maliciously/accidentally path-traversing file-block
    name such as "../../etc/passwd")."""
    base_abs = os.path.abspath(base)
    dest_abs = os.path.abspath(os.path.join(base_abs, name))
    if dest_abs != base_abs and not dest_abs.startswith(base_abs + os.sep):
        raise ValueError("file-block name escapes workdir: %r" % name)
    return dest_abs


def materialize_blocks(blocks, workdir):
    for name, body in blocks.items():
        dest = _safe_join(workdir, name)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            f.write(body)


def main(argv):
    if len(argv) != 4:
        sys.stderr.write(
            "usage: hidden-tests.py <item-dir> <answer-file> <workdir>\n"
        )
        sys.exit(2)

    item_dir, answer_file, workdir = argv[1], argv[2], argv[3]

    try:
        extract_answer = _load_extract_answer()
        with open(answer_file, "r", encoding="utf-8") as f:
            raw = f.read()

        blocks = extract_answer.extract_file_blocks(raw)
        if not blocks:
            write_score(
                workdir,
                0.0,
                "contract-fail",
                {"passed": 0, "total": 0, "stdout_tail": ""},
            )
            sys.exit(0)

        os.makedirs(workdir, exist_ok=True)
        materialize_blocks(blocks, workdir)

        expected_tests_dir = os.path.join(item_dir, "expected", "tests")
        shutil.copytree(expected_tests_dir, workdir, dirs_exist_ok=True)

        runner_path = os.path.join(workdir, "_run_hidden_tests.py")
        with open(runner_path, "w", encoding="utf-8") as f:
            f.write(_RUNNER_SOURCE)

        proc = subprocess.run(
            [sys.executable, "_run_hidden_tests.py"],
            cwd=workdir,
            capture_output=True,
            text=True,
            timeout=_TEST_TIMEOUT_S,
        )
        combined_output = (proc.stdout or "") + (proc.stderr or "")
        stdout_tail = combined_output[-_STDOUT_TAIL_CHARS:]

        result_line = None
        for line in (proc.stdout or "").splitlines():
            if line.startswith("RESULT_JSON:"):
                result_line = line[len("RESULT_JSON:"):]

        if result_line is None:
            write_score(
                workdir,
                0.0,
                "error",
                {"passed": 0, "total": 0, "stdout_tail": stdout_tail},
            )
            sys.exit(0)

        result = json.loads(result_line)
        passed = result["passed"]
        total = result["total"]

        if total == 0:
            write_score(
                workdir,
                0.0,
                "error",
                {"passed": passed, "total": total, "stdout_tail": stdout_tail},
            )
            sys.exit(0)

        score = round(passed / total, 4)
        write_score(
            workdir,
            score,
            "scored",
            {"passed": passed, "total": total, "stdout_tail": stdout_tail},
        )
    except subprocess.TimeoutExpired as exc:
        write_score(
            workdir,
            0.0,
            "error",
            {"error": "test run timed out: %s" % exc},
        )
    except Exception as exc:  # scorer ABI: always exit 0
        write_score(workdir, 0.0, "error", {"error": str(exc)})

    sys.exit(0)


if __name__ == "__main__":
    main(sys.argv)
