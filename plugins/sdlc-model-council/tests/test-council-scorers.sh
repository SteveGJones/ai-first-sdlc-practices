#!/usr/bin/env bash
# Test harness for the four v1 scorer plug-ins (issue #232, stage 2 —
# scripts/council/score/{hidden-tests,planted-defects,exact-match,format-parse}.py
# — see docs/superpowers/specs/2026-07-25-sdlc-model-council-design.md §2.3
# and the stage2-contract.md §3/§11 pin). For each scorer this crafts a tiny
# throwaway item-dir + answer fixture under a mktemp dir inside the plugin's
# own ./tmp/, invokes the scorer exactly per its ABI
# (`<type>.py <item-dir> <answer-file> <workdir>`), and asserts the emitted
# score.json against a HAND-COMPUTED golden value (numeric fields compared
# with an absolute tolerance of 1e-4 via python3; string/int fields compared
# exactly). Every scorer is stdlib-only Python 3 invoked directly as
# `python3 <file> ...` — no pip/venv, no network, no model calls.
#
# Run: bash plugins/sdlc-model-council/tests/test-council-scorers.sh

set -u

THIS_DIR="$(cd "$(dirname "$0")" && pwd -P)"
PLUGIN_ROOT="$(cd "$THIS_DIR/.." && pwd -P)"
SCORE_DIR="$PLUGIN_ROOT/scripts/council/score"

mkdir -p "$PLUGIN_ROOT/tmp"
TESTROOT="$(mktemp -d "$PLUGIN_ROOT/tmp/council-scorers-test.XXXXXX")"
trap 'rm -rf "$TESTROOT"' EXIT

PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); printf 'PASS: %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf 'FAIL: %s\n' "$1"; }

# json_get <score.json path> <python expr over `d`> -- prints the value
json_get() {
  python3 - "$1" "$2" <<'PYEOF'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as f:
    d = json.load(f)
expr = sys.argv[2]
print(eval(expr, {}, {"d": d}))
PYEOF
}

# assert_float_close <actual> <expected> <tol> <label>
assert_float_close() {
  actual="$1"; expected="$2"; tol="$3"; label="$4"
  if python3 - "$actual" "$expected" "$tol" <<'PYEOF'
import sys
a = float(sys.argv[1])
e = float(sys.argv[2])
tol = float(sys.argv[3])
sys.exit(0 if abs(a - e) <= tol else 1)
PYEOF
  then
    pass "$label (actual=$actual expected=$expected tol=$tol)"
  else
    fail "$label (actual=$actual expected=$expected tol=$tol)"
  fi
}

# assert_eq <actual> <expected> <label>
assert_eq() {
  if [ "$1" = "$2" ]; then
    pass "$3"
  else
    fail "$3 (actual=[$1] expected=[$2])"
  fi
}

run_scorer() {
  # run_scorer <type> <item-dir> <answer-file> <workdir>
  type_name="$1"; item_dir="$2"; answer_file="$3"; workdir="$4"
  mkdir -p "$workdir"
  python3 "$SCORE_DIR/$type_name.py" "$item_dir" "$answer_file" "$workdir"
  rc=$?
  if [ "$rc" -ne 0 ]; then
    fail "$type_name.py exited $rc (ABI requires always-exit-0)"
  fi
  if [ ! -f "$workdir/score.json" ]; then
    fail "$type_name.py did not write $workdir/score.json"
  fi
}

echo "=== council scorer test suite ==="
echo "TESTROOT=$TESTROOT"
echo

# =============================================================================
# hidden-tests
# =============================================================================
echo "--- hidden-tests ---"

HT_ITEM="$TESTROOT/ht-item"
mkdir -p "$HT_ITEM/expected/tests" "$HT_ITEM/inputs"
cat > "$HT_ITEM/item.json" <<'EOF'
{"schema_version":1,"id":"ht-test","dimension":"bug-fix","version":1,
 "difficulty":"easy","timeout_s":30,"min_context_tokens":0,
 "est_prompt_tokens":100,"est_output_tokens":100,
 "answer_contract":"file-blocks","scorer":{"type":"hidden-tests"}}
EOF
cat > "$HT_ITEM/expected/tests/test_calc.py" <<'EOF'
import unittest
from calc import add, sub


class TestCalc(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(2, 3), 5)

    def test_sub(self):
        self.assertEqual(sub(5, 2), 3)

    def test_sub_zero(self):
        self.assertEqual(sub(5, 5), 0)
EOF

# 1a. Answer passes 2/3 tests (add() has a planted off-by-one bug; sub() is
#     correct) -> golden score = 2/3 = 0.6667.
HT_ANSWER_A="$TESTROOT/ht-answer-a.txt"
cat > "$HT_ANSWER_A" <<'EOF'
Here is my patch:

```file:calc.py
def add(a, b):
    return a + b + 1


def sub(a, b):
    return a - b
```
EOF
HT_WORK_A="$TESTROOT/ht-work-a"
run_scorer hidden-tests "$HT_ITEM" "$HT_ANSWER_A" "$HT_WORK_A"
HT_A_SCORE=$(json_get "$HT_WORK_A/score.json" "d['score']")
HT_A_STATUS=$(json_get "$HT_WORK_A/score.json" "d['status']")
HT_A_PASSED=$(json_get "$HT_WORK_A/score.json" "d['details']['passed']")
HT_A_TOTAL=$(json_get "$HT_WORK_A/score.json" "d['details']['total']")
assert_float_close "$HT_A_SCORE" "0.6667" "0.0001" "2/3 passing tests -> score ~0.6667"
assert_eq "$HT_A_STATUS" "scored" "2/3 passing tests -> status scored"
assert_eq "$HT_A_PASSED" "2" "2/3 passing tests -> details.passed == 2"
assert_eq "$HT_A_TOTAL" "3" "2/3 passing tests -> details.total == 3"

# 1b. Answer with no file-blocks at all -> contract-fail, score 0.
HT_ANSWER_B="$TESTROOT/ht-answer-b.txt"
cat > "$HT_ANSWER_B" <<'EOF'
I believe the fix is straightforward but I will not show any code.
EOF
HT_WORK_B="$TESTROOT/ht-work-b"
run_scorer hidden-tests "$HT_ITEM" "$HT_ANSWER_B" "$HT_WORK_B"
HT_B_SCORE=$(json_get "$HT_WORK_B/score.json" "d['score']")
HT_B_STATUS=$(json_get "$HT_WORK_B/score.json" "d['status']")
assert_float_close "$HT_B_SCORE" "0.0" "0.0001" "no file-blocks -> score 0"
assert_eq "$HT_B_STATUS" "contract-fail" "no file-blocks -> status contract-fail"
echo

# =============================================================================
# planted-defects
# =============================================================================
echo "--- planted-defects ---"

PD_ITEM_A="$TESTROOT/pd-item-a"
mkdir -p "$PD_ITEM_A/expected" "$PD_ITEM_A/inputs"
cat > "$PD_ITEM_A/item.json" <<'EOF'
{"schema_version":1,"id":"pd-test-a","dimension":"code-review","version":1,
 "difficulty":"med","timeout_s":30,"min_context_tokens":0,
 "est_prompt_tokens":200,"est_output_tokens":200,
 "answer_contract":"findings-json","scorer":{"type":"planted-defects"}}
EOF
cat > "$PD_ITEM_A/expected/defects.json" <<'EOF'
[
  {"id": "d1", "file": "foo.py", "line": 10, "match_any": ["sql injection", "injection"]},
  {"id": "d2", "file": "bar.py", "line": 50},
  {"id": "d3", "file": "baz.py", "line": 100, "match_any": ["hardcoded secret"]}
]
EOF

# 2a. 2 of 3 defects found (d1 via line-window+regex, d3 via line-window
#     only) with 1 false positive (unrelated bar.py finding, far from d2's
#     line and matching no regex) -> recall 2/3, precision 2/3, F1 ~0.6667.
PD_ANSWER_A="$TESTROOT/pd-answer-a.txt"
cat > "$PD_ANSWER_A" <<'EOF'
My review findings:

```json
[
  {"file": "foo.py", "line": 11, "message": "possible SQL injection vulnerability"},
  {"file": "bar.py", "line": 200, "message": "unrelated stylistic nit"},
  {"file": "baz.py", "line": 99, "message": "looks fragile here"}
]
```
EOF
PD_WORK_A="$TESTROOT/pd-work-a"
run_scorer planted-defects "$PD_ITEM_A" "$PD_ANSWER_A" "$PD_WORK_A"
PD_A_SCORE=$(json_get "$PD_WORK_A/score.json" "d['score']")
PD_A_STATUS=$(json_get "$PD_WORK_A/score.json" "d['status']")
PD_A_RECALL=$(json_get "$PD_WORK_A/score.json" "d['details']['recall']")
PD_A_PRECISION=$(json_get "$PD_WORK_A/score.json" "d['details']['precision']")
PD_A_TP=$(json_get "$PD_WORK_A/score.json" "d['details']['tp']")
PD_A_FP=$(json_get "$PD_WORK_A/score.json" "d['details']['fp']")
PD_A_FN=$(json_get "$PD_WORK_A/score.json" "d['details']['fn']")
assert_float_close "$PD_A_RECALL" "0.6667" "0.0001" "2/3 defects found -> recall ~0.6667"
assert_float_close "$PD_A_PRECISION" "0.6667" "0.0001" "2 tp of 3 findings -> precision ~0.6667"
assert_float_close "$PD_A_SCORE" "0.6667" "0.0001" "F1 of equal P/R -> score ~0.6667"
assert_eq "$PD_A_STATUS" "scored" "2/3 found + 1 fp -> status scored"
assert_eq "$PD_A_TP" "2" "2/3 found + 1 fp -> tp == 2"
assert_eq "$PD_A_FP" "1" "2/3 found + 1 fp -> fp == 1"
assert_eq "$PD_A_FN" "1" "2/3 found + 1 fp -> fn == 1"

# 2b. Shotgun: 20 findings, only the first 8 (max_findings_counted default)
#     are counted at all. Exactly 1 true match falls within that first-8
#     window; the single defect is otherwise fully recalled (1/1) so the
#     interesting number here is precision: 1/8 = 0.125, NOT 1/20 = 0.05 —
#     that distinction is the whole point of the anti-shotgun cap.
PD_ITEM_B="$TESTROOT/pd-item-b"
mkdir -p "$PD_ITEM_B/expected" "$PD_ITEM_B/inputs"
cat > "$PD_ITEM_B/item.json" <<'EOF'
{"schema_version":1,"id":"pd-test-b","dimension":"code-review","version":1,
 "difficulty":"med","timeout_s":30,"min_context_tokens":0,
 "est_prompt_tokens":200,"est_output_tokens":200,
 "answer_contract":"findings-json","scorer":{"type":"planted-defects","max_findings_counted":8}}
EOF
cat > "$PD_ITEM_B/expected/defects.json" <<'EOF'
[{"id": "d1", "file": "only.py", "line": 42}]
EOF
PD_ANSWER_B="$TESTROOT/pd-answer-b.txt"
python3 - "$PD_ANSWER_B" <<'PYEOF'
import json
import sys

findings = []
for i in range(20):
    if i == 1:
        # within the first 8 (index 1) -> the one true positive
        findings.append({"file": "only.py", "line": 42, "message": "real defect here"})
    else:
        findings.append({"file": "noise%d.py" % i, "line": 1, "message": "irrelevant finding"})

with open(sys.argv[1], "w", encoding="utf-8") as f:
    f.write("Shotgun review:\n\n```json\n" + json.dumps(findings) + "\n```\n")
PYEOF
PD_WORK_B="$TESTROOT/pd-work-b"
run_scorer planted-defects "$PD_ITEM_B" "$PD_ANSWER_B" "$PD_WORK_B"
PD_B_PRECISION=$(json_get "$PD_WORK_B/score.json" "d['details']['precision']")
PD_B_RECALL=$(json_get "$PD_WORK_B/score.json" "d['details']['recall']")
PD_B_SCORE=$(json_get "$PD_WORK_B/score.json" "d['score']")
PD_B_TP=$(json_get "$PD_WORK_B/score.json" "d['details']['tp']")
PD_B_FP=$(json_get "$PD_WORK_B/score.json" "d['details']['fp']")
assert_float_close "$PD_B_PRECISION" "0.125" "0.0001" "20 findings capped at 8 -> precision denom is 8 (1/8=0.125), not 20"
assert_float_close "$PD_B_RECALL" "1.0" "0.0001" "the one real defect was recalled -> recall 1.0"
assert_float_close "$PD_B_SCORE" "0.2222" "0.0001" "F1(precision=0.125,recall=1.0) ~0.2222"
assert_eq "$PD_B_TP" "1" "shotgun -> tp == 1"
assert_eq "$PD_B_FP" "7" "shotgun -> fp == 7 (8 counted - 1 tp)"

# 2c. Unparseable findings (no JSON array anywhere in the answer) ->
#     contract-fail, score 0.
PD_ANSWER_C="$TESTROOT/pd-answer-c.txt"
cat > "$PD_ANSWER_C" <<'EOF'
I looked at the code but I am not going to give you structured findings,
just prose commentary with no brackets of any kind.
EOF
PD_WORK_C="$TESTROOT/pd-work-c"
run_scorer planted-defects "$PD_ITEM_A" "$PD_ANSWER_C" "$PD_WORK_C"
PD_C_SCORE=$(json_get "$PD_WORK_C/score.json" "d['score']")
PD_C_STATUS=$(json_get "$PD_WORK_C/score.json" "d['status']")
PD_C_FN=$(json_get "$PD_WORK_C/score.json" "d['details']['fn']")
assert_float_close "$PD_C_SCORE" "0.0" "0.0001" "unparseable findings -> score 0"
assert_eq "$PD_C_STATUS" "contract-fail" "unparseable findings -> status contract-fail"
assert_eq "$PD_C_FN" "3" "unparseable findings -> all 3 defects counted as missed (fn==3)"
echo

# =============================================================================
# exact-match
# =============================================================================
echo "--- exact-match ---"

EM_ITEM="$TESTROOT/em-item"
mkdir -p "$EM_ITEM/expected" "$EM_ITEM/inputs"
cat > "$EM_ITEM/item.json" <<'EOF'
{"schema_version":1,"id":"em-test","dimension":"long-context","version":1,
 "difficulty":"easy","timeout_s":30,"min_context_tokens":0,
 "est_prompt_tokens":500,"est_output_tokens":20,
 "answer_contract":"text","scorer":{"type":"exact-match"}}
EOF
printf 'The Quick Brown Fox Jumps Over The Lazy Dog.' > "$EM_ITEM/expected/answer.txt"

# 3a. Whitespace/case-different but semantically equal -> 1.0.
EM_ANSWER_A="$TESTROOT/em-answer-a.txt"
printf '   THE   QUICK brown FOX   \n Jumps over the LAZY DOG.   ' > "$EM_ANSWER_A"
EM_WORK_A="$TESTROOT/em-work-a"
run_scorer exact-match "$EM_ITEM" "$EM_ANSWER_A" "$EM_WORK_A"
EM_A_SCORE=$(json_get "$EM_WORK_A/score.json" "d['score']")
EM_A_MATCH=$(json_get "$EM_WORK_A/score.json" "d['details']['match']")
assert_float_close "$EM_A_SCORE" "1.0" "0.0001" "whitespace/case-different but equal -> score 1.0"
assert_eq "$EM_A_MATCH" "True" "whitespace/case-different but equal -> details.match True"

# 3b. Genuinely different answer -> 0.0.
EM_ANSWER_B="$TESTROOT/em-answer-b.txt"
printf 'A completely different sentence about something else entirely.' > "$EM_ANSWER_B"
EM_WORK_B="$TESTROOT/em-work-b"
run_scorer exact-match "$EM_ITEM" "$EM_ANSWER_B" "$EM_WORK_B"
EM_B_SCORE=$(json_get "$EM_WORK_B/score.json" "d['score']")
EM_B_MATCH=$(json_get "$EM_WORK_B/score.json" "d['details']['match']")
assert_float_close "$EM_B_SCORE" "0.0" "0.0001" "different answer -> score 0.0"
assert_eq "$EM_B_MATCH" "False" "different answer -> details.match False"
echo

# =============================================================================
# format-parse
# =============================================================================
echo "--- format-parse ---"

FP_ITEM="$TESTROOT/fp-item"
mkdir -p "$FP_ITEM/expected" "$FP_ITEM/inputs"
cat > "$FP_ITEM/item.json" <<'EOF'
{"schema_version":1,"id":"fp-test","dimension":"instruction-format","version":1,
 "difficulty":"easy","timeout_s":30,"min_context_tokens":0,
 "est_prompt_tokens":150,"est_output_tokens":50,
 "answer_contract":"strict-json","scorer":{"type":"format-parse"}}
EOF
cat > "$FP_ITEM/expected/schema.json" <<'EOF'
{"required_keys": ["name", "status"],
 "types": {"name": "string"},
 "enums": {"status": ["pass", "fail"]}}
EOF

# 4a. Object satisfies 3 of 4 constraints (required:name ok, required:status
#     ok, type:name ok, enum:status FAILS because "unknown" isn't in
#     ["pass","fail"]) -> score 0.75.
FP_ANSWER_A="$TESTROOT/fp-answer-a.txt"
cat > "$FP_ANSWER_A" <<'EOF'
Here is the structured result:
{"name": "widget", "status": "unknown"}
EOF
FP_WORK_A="$TESTROOT/fp-work-a"
run_scorer format-parse "$FP_ITEM" "$FP_ANSWER_A" "$FP_WORK_A"
FP_A_SCORE=$(json_get "$FP_WORK_A/score.json" "d['score']")
FP_A_STATUS=$(json_get "$FP_WORK_A/score.json" "d['status']")
FP_A_SATISFIED=$(json_get "$FP_WORK_A/score.json" "d['details']['satisfied']")
FP_A_TOTAL=$(json_get "$FP_WORK_A/score.json" "d['details']['total']")
FP_A_FAILED=$(json_get "$FP_WORK_A/score.json" "d['details']['failed_constraints']")
assert_float_close "$FP_A_SCORE" "0.75" "0.0001" "3/4 constraints satisfied -> score 0.75"
assert_eq "$FP_A_STATUS" "scored" "3/4 constraints satisfied -> status scored"
assert_eq "$FP_A_SATISFIED" "3" "3/4 constraints satisfied -> details.satisfied == 3"
assert_eq "$FP_A_TOTAL" "4" "3/4 constraints satisfied -> details.total == 4"
assert_eq "$FP_A_FAILED" "['enum:status']" "3/4 constraints satisfied -> failed_constraints names the enum violation"

# 4b. Not JSON at all -> contract-fail, score 0.
FP_ANSWER_B="$TESTROOT/fp-answer-b.txt"
cat > "$FP_ANSWER_B" <<'EOF'
I refuse to produce structured output, here is just prose with no braces.
EOF
FP_WORK_B="$TESTROOT/fp-work-b"
run_scorer format-parse "$FP_ITEM" "$FP_ANSWER_B" "$FP_WORK_B"
FP_B_SCORE=$(json_get "$FP_WORK_B/score.json" "d['score']")
FP_B_STATUS=$(json_get "$FP_WORK_B/score.json" "d['status']")
assert_float_close "$FP_B_SCORE" "0.0" "0.0001" "non-JSON answer -> score 0"
assert_eq "$FP_B_STATUS" "contract-fail" "non-JSON answer -> status contract-fail"
echo

echo "=== Results: $PASS passed, $FAIL failed ==="
[ "$FAIL" -eq 0 ]
