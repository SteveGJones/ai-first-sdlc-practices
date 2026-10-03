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

# =============================================================================
# command-check (tool-use: command-exec + monitoring dimensions, issue #235)
# =============================================================================
echo "--- command-check ---"

# 5a. command-exec, partial: 3 of 4 field_checks satisfied. The answer uses
#     `cat` not `grep`, so the "uses grep" regex FAILS; the other three pass
#     (access.log present, no destructive rm, non-empty reason) -> score 0.75,
#     and failed_checks names the grep check.
CC_ITEM_CE="$TESTROOT/cc-item-ce"
mkdir -p "$CC_ITEM_CE/expected" "$CC_ITEM_CE/inputs"
cat > "$CC_ITEM_CE/item.json" <<'EOF'
{"schema_version":1,"id":"cc-ce","dimension":"command-exec","version":1,
 "difficulty":"med","timeout_s":30,"min_context_tokens":0,
 "est_prompt_tokens":150,"est_output_tokens":60,
 "answer_contract":"strict-json","scorer":{"type":"command-check"}}
EOF
cat > "$CC_ITEM_CE/expected/checks.json" <<'EOF'
{"field_checks": [
  {"field": "commands", "regex": "\\bgrep\\b", "flags": "i", "desc": "uses grep"},
  {"field": "commands", "regex": "access\\.log", "desc": "targets access.log"},
  {"field": "commands", "not_regex": "rm\\s+-rf", "desc": "no destructive rm"},
  {"field": "reason", "regex": ".+", "desc": "gives a reason"}
]}
EOF
CC_ANSWER_CE="$TESTROOT/cc-answer-ce.txt"
cat > "$CC_ANSWER_CE" <<'EOF'
Here is the next command:
{"commands": ["cat access.log"], "reason": "inspect the log"}
EOF
CC_WORK_CE="$TESTROOT/cc-work-ce"
run_scorer command-check "$CC_ITEM_CE" "$CC_ANSWER_CE" "$CC_WORK_CE"
CC_CE_SCORE=$(json_get "$CC_WORK_CE/score.json" "d['score']")
CC_CE_STATUS=$(json_get "$CC_WORK_CE/score.json" "d['status']")
CC_CE_SAT=$(json_get "$CC_WORK_CE/score.json" "d['details']['satisfied']")
CC_CE_TOTAL=$(json_get "$CC_WORK_CE/score.json" "d['details']['total']")
CC_CE_FAILED=$(json_get "$CC_WORK_CE/score.json" "d['details']['failed_checks']")
assert_float_close "$CC_CE_SCORE" "0.75" "0.0001" "cat-not-grep -> 3/4 satisfied, score 0.75"
assert_eq "$CC_CE_STATUS" "scored" "command-exec partial -> status scored"
assert_eq "$CC_CE_SAT" "3" "command-exec partial -> details.satisfied == 3"
assert_eq "$CC_CE_TOTAL" "4" "command-exec partial -> details.total == 4"
assert_eq "$CC_CE_FAILED" "['uses grep']" "command-exec partial -> failed_checks names the grep desc"

# 5b. Guardrail + list-join: the answer proposes a destructive `rm -rf` as its
#     second command. commands is a LIST, joined with newlines before regex, so
#     both the good grep/access.log checks pass AND the not_regex guardrail FAILS
#     on the joined text -> 3/4 = 0.75, failed_checks names the destructive check.
CC_ANSWER_RM="$TESTROOT/cc-answer-rm.txt"
cat > "$CC_ANSWER_RM" <<'EOF'
{"commands": ["grep ' 500 ' access.log", "rm -rf /var/log/old"], "reason": "find 500s then clean up"}
EOF
CC_WORK_RM="$TESTROOT/cc-work-rm"
run_scorer command-check "$CC_ITEM_CE" "$CC_ANSWER_RM" "$CC_WORK_RM"
CC_RM_SCORE=$(json_get "$CC_WORK_RM/score.json" "d['score']")
CC_RM_FAILED=$(json_get "$CC_WORK_RM/score.json" "d['details']['failed_checks']")
assert_float_close "$CC_RM_SCORE" "0.75" "0.0001" "destructive rm in a list command -> not_regex fails, score 0.75"
assert_eq "$CC_RM_FAILED" "['no destructive rm']" "destructive rm -> failed_checks names the guardrail"

# 5c. monitoring, full credit: correct STOP decision, decision in enum, and the
#     trigger names the success line -> 3/3 = 1.0.
CC_ITEM_MON="$TESTROOT/cc-item-mon"
mkdir -p "$CC_ITEM_MON/expected" "$CC_ITEM_MON/inputs"
cat > "$CC_ITEM_MON/item.json" <<'EOF'
{"schema_version":1,"id":"cc-mon","dimension":"monitoring","version":1,
 "difficulty":"med","timeout_s":30,"min_context_tokens":0,
 "est_prompt_tokens":150,"est_output_tokens":60,
 "answer_contract":"strict-json","scorer":{"type":"command-check"}}
EOF
cat > "$CC_ITEM_MON/expected/checks.json" <<'EOF'
{"field_checks": [
  {"field": "decision", "equals": "stop"},
  {"field": "decision", "enum": ["stop", "continue"]},
  {"field": "trigger", "regex": "BUILD SUCCESS", "desc": "identifies the success line"}
]}
EOF
CC_ANSWER_MON="$TESTROOT/cc-answer-mon.txt"
cat > "$CC_ANSWER_MON" <<'EOF'
{"decision": "stop", "trigger": "BUILD SUCCESS in 4.2s", "reason": "the build completed"}
EOF
CC_WORK_MON="$TESTROOT/cc-work-mon"
run_scorer command-check "$CC_ITEM_MON" "$CC_ANSWER_MON" "$CC_WORK_MON"
CC_MON_SCORE=$(json_get "$CC_WORK_MON/score.json" "d['score']")
CC_MON_STATUS=$(json_get "$CC_WORK_MON/score.json" "d['status']")
assert_float_close "$CC_MON_SCORE" "1.0" "0.0001" "correct stop + trigger -> score 1.0"
assert_eq "$CC_MON_STATUS" "scored" "monitoring full credit -> status scored"

# 5d. monitoring, wrong decision: model says CONTINUE when it should STOP, and
#     gives no trigger. equals:stop FAILS, enum PASSES (continue is valid), the
#     trigger regex FAILS on the empty string -> 1/3 = 0.3333.
CC_ANSWER_MON2="$TESTROOT/cc-answer-mon2.txt"
cat > "$CC_ANSWER_MON2" <<'EOF'
{"decision": "continue", "trigger": "", "reason": "still waiting"}
EOF
CC_WORK_MON2="$TESTROOT/cc-work-mon2"
run_scorer command-check "$CC_ITEM_MON" "$CC_ANSWER_MON2" "$CC_WORK_MON2"
CC_MON2_SCORE=$(json_get "$CC_WORK_MON2/score.json" "d['score']")
assert_float_close "$CC_MON2_SCORE" "0.3333" "0.0001" "wrong decision + no trigger -> 1/3 = 0.3333"

# 5e. Missing-field asymmetry: an answer object missing both referenced fields.
#     equals:decision FAILS (missing field can't equal "stop") but not_regex:
#     commands PASSES (a missing field is vacuously free of the forbidden
#     pattern — the guardrail is lenient about absence) -> 1/2 = 0.5.
CC_ITEM_MISS="$TESTROOT/cc-item-miss"
mkdir -p "$CC_ITEM_MISS/expected" "$CC_ITEM_MISS/inputs"
cat > "$CC_ITEM_MISS/item.json" <<'EOF'
{"schema_version":1,"id":"cc-miss","dimension":"command-exec","version":1,
 "difficulty":"easy","timeout_s":30,"min_context_tokens":0,
 "est_prompt_tokens":100,"est_output_tokens":40,
 "answer_contract":"strict-json","scorer":{"type":"command-check"}}
EOF
cat > "$CC_ITEM_MISS/expected/checks.json" <<'EOF'
{"field_checks": [
  {"field": "decision", "equals": "stop"},
  {"field": "commands", "not_regex": "sudo", "desc": "no sudo"}
]}
EOF
CC_ANSWER_MISS="$TESTROOT/cc-answer-miss.txt"
cat > "$CC_ANSWER_MISS" <<'EOF'
{"reason": "not sure what to do"}
EOF
CC_WORK_MISS="$TESTROOT/cc-work-miss"
run_scorer command-check "$CC_ITEM_MISS" "$CC_ANSWER_MISS" "$CC_WORK_MISS"
CC_MISS_SCORE=$(json_get "$CC_WORK_MISS/score.json" "d['score']")
assert_float_close "$CC_MISS_SCORE" "0.5" "0.0001" "missing fields -> equals fails, not_regex passes -> 0.5"

# 5f. contract-fail: answer is prose with no JSON object at all -> score 0.
CC_ANSWER_CF="$TESTROOT/cc-answer-cf.txt"
cat > "$CC_ANSWER_CF" <<'EOF'
I would probably run grep on the access log but I am not returning JSON.
EOF
CC_WORK_CF="$TESTROOT/cc-work-cf"
run_scorer command-check "$CC_ITEM_CE" "$CC_ANSWER_CF" "$CC_WORK_CF"
CC_CF_SCORE=$(json_get "$CC_WORK_CF/score.json" "d['score']")
CC_CF_STATUS=$(json_get "$CC_WORK_CF/score.json" "d['status']")
assert_float_close "$CC_CF_SCORE" "0.0" "0.0001" "no JSON object -> score 0"
assert_eq "$CC_CF_STATUS" "contract-fail" "no JSON object -> status contract-fail"
echo

# =============================================================================
# command-diff (tool-use: execute the proposed command, diff stdout vs golden)
# =============================================================================
# Motivation (issue #235, measured): a regex rubric cannot separate a CORRECT
# alternative implementation from a plausible-looking BROKEN one. In the live
# audition three local models answered ce-hard-grep-context with awk instead of
# `grep -A 3`; Qwen3-Coder-30B-A3B's awk was byte-identical to the golden output
# (a rubric FALSE NEGATIVE) while Qwen2.5-Coder-7B's and Devstral-24B's awk were
# genuinely wrong. All three scored the same 0.6667 under command-check. The
# fixtures below are those VERBATIM model answers.
echo "--- command-diff ---"

CD_ITEM="$TESTROOT/cd-item"
mkdir -p "$CD_ITEM/expected" "$CD_ITEM/inputs"
cat > "$CD_ITEM/item.json" <<'EOF'
{"schema_version":1,"id":"cd-test","dimension":"command-exec","version":1,
 "difficulty":"hard","timeout_s":60,"min_context_tokens":0,
 "est_prompt_tokens":200,"est_output_tokens":120,
 "answer_contract":"strict-json","scorer":{"type":"command-diff"}}
EOF
cat > "$CD_ITEM/inputs/app.log" <<'EOF'
10:00:01 INFO  request received id=42
10:00:02 ERROR db query failed id=42
10:00:02 DEBUG  retrying with backoff=200ms
10:00:03 DEBUG  connection reset by peer
10:00:03 DEBUG  giving up after 3 attempts
10:00:04 INFO  request received id=43
EOF
cat > "$CD_ITEM/expected/exec.json" <<'EOF'
{
  "field": "commands",
  "golden_stdout": "stdout.txt",
  "allow_binaries": ["grep", "egrep", "fgrep", "rg", "awk", "sed", "cat",
                     "head", "tail", "sort", "uniq", "wc", "cut", "tr"],
  "timeout_s": 10
}
EOF
cat > "$CD_ITEM/expected/stdout.txt" <<'EOF'
10:00:02 ERROR db query failed id=42
10:00:02 DEBUG  retrying with backoff=200ms
10:00:03 DEBUG  connection reset by peer
10:00:03 DEBUG  giving up after 3 attempts
EOF

# The exec path is opt-in; every case below except 6e sets the gate env var.
export COUNCIL_ALLOW_EXEC=1

# 6a. The golden grep form -> output matches -> 1.0.
CD_ANSWER_GREP="$TESTROOT/cd-answer-grep.txt"
cat > "$CD_ANSWER_GREP" <<'EOF'
{"commands": ["grep -A 3 'ERROR' app.log"], "reason": "prints each ERROR line plus 3 after"}
EOF
CD_WORK_GREP="$TESTROOT/cd-work-grep"
run_scorer command-diff "$CD_ITEM" "$CD_ANSWER_GREP" "$CD_WORK_GREP"
assert_float_close "$(json_get "$CD_WORK_GREP/score.json" "d['score']")" "1.0" "0.0001" \
  "grep -A 3 -> output matches golden -> 1.0"
assert_eq "$(json_get "$CD_WORK_GREP/score.json" "d['status']")" "scored" \
  "grep -A 3 -> status scored"

# 6b. Qwen3-Coder-30B-A3B's VERBATIM awk answer: a correct alternative
#     implementation that command-check falsely failed. Must score 1.0.
CD_ANSWER_AWK_OK="$TESTROOT/cd-answer-awk-ok.txt"
cat > "$CD_ANSWER_AWK_OK" <<'EOF'
{"commands": ["awk '/ERROR/{print; for(i=0;i<3;i++) {getline; print}}' app.log"], "reason": "awk prints ERROR plus next three"}
EOF
CD_WORK_AWK_OK="$TESTROOT/cd-work-awk-ok"
run_scorer command-diff "$CD_ITEM" "$CD_ANSWER_AWK_OK" "$CD_WORK_AWK_OK"
assert_float_close "$(json_get "$CD_WORK_AWK_OK/score.json" "d['score']")" "1.0" "0.0001" \
  "correct awk alternative (real Qwen3-30B answer) -> 1.0, no false negative"

# 6c. Qwen2.5-Coder-7B's VERBATIM awk answer: plausible but broken (prints one
#     wrong line and three blanks) -> executes fine, output differs -> 0.0.
CD_ANSWER_AWK_BAD="$TESTROOT/cd-answer-awk-bad.txt"
cat > "$CD_ANSWER_AWK_BAD" <<'EOF'
{"commands": ["awk '/ERROR/{for(i=1;i<=4;i++)print a[i];next} {a[NR]=$0}' app.log"], "reason": "prints ERROR plus three following lines"}
EOF
CD_WORK_AWK_BAD="$TESTROOT/cd-work-awk-bad"
run_scorer command-diff "$CD_ITEM" "$CD_ANSWER_AWK_BAD" "$CD_WORK_AWK_BAD"
assert_float_close "$(json_get "$CD_WORK_AWK_BAD/score.json" "d['score']")" "0.0" "0.0001" \
  "broken awk (real 7B answer) -> output differs -> 0.0"
assert_eq "$(json_get "$CD_WORK_AWK_BAD/score.json" "d['status']")" "scored" \
  "broken awk -> executed and scored (not an error)"

# 6d. Devstral-24B's VERBATIM awk answer: also broken (repeats one INFO line).
CD_ANSWER_AWK_DV="$TESTROOT/cd-answer-awk-dv.txt"
cat > "$CD_ANSWER_AWK_DV" <<'EOF'
{"commands": ["awk '/ERROR/{getline; print p; getline; print p; getline; print p; p=$0} {p=$0}' app.log"], "reason": "buffers the previous line"}
EOF
CD_WORK_AWK_DV="$TESTROOT/cd-work-awk-dv"
run_scorer command-diff "$CD_ITEM" "$CD_ANSWER_AWK_DV" "$CD_WORK_AWK_DV"
assert_float_close "$(json_get "$CD_WORK_AWK_DV/score.json" "d['score']")" "0.0" "0.0001" \
  "broken awk (real Devstral-24B answer) -> 0.0"

# 6e. Opt-in gate: with COUNCIL_ALLOW_EXEC unset nothing is executed.
CD_WORK_OFF="$TESTROOT/cd-work-off"
mkdir -p "$CD_WORK_OFF"
env -u COUNCIL_ALLOW_EXEC python3 "$SCORE_DIR/command-diff.py" \
  "$CD_ITEM" "$CD_ANSWER_GREP" "$CD_WORK_OFF"
assert_eq "$?" "0" "command-diff.py exits 0 with the exec gate closed (ABI)"
assert_eq "$(json_get "$CD_WORK_OFF/score.json" "d['status']")" "exec-disabled" \
  "gate closed -> status exec-disabled"
assert_float_close "$(json_get "$CD_WORK_OFF/score.json" "d['score']")" "0.0" "0.0001" \
  "gate closed -> score 0"

# 6e-bis. Gate closed BUT the item also ships expected/checks.json -> fall back
#         to the static rubric instead of scoring 0, so a default (non-opted-in)
#         council run stays meaningful and exec mode is a strict upgrade.
CD_ITEM_HYB="$TESTROOT/cd-item-hybrid"
mkdir -p "$CD_ITEM_HYB/expected"
cp -R "$CD_ITEM/inputs" "$CD_ITEM_HYB/inputs"
cp "$CD_ITEM/item.json" "$CD_ITEM_HYB/item.json"
cp "$CD_ITEM/expected/stdout.txt" "$CD_ITEM_HYB/expected/stdout.txt"
cp "$CD_ITEM/expected/exec.json" "$CD_ITEM_HYB/expected/exec.json"
cat > "$CD_ITEM_HYB/expected/checks.json" <<'EOF'
{"field_checks": [
  {"field": "commands", "regex": "app\\.log", "desc": "targets app.log"},
  {"field": "commands", "regex": "ERROR", "desc": "matches ERROR lines"},
  {"field": "commands", "not_regex": "\\brm\\b", "desc": "non-destructive"},
  {"field": "reason", "regex": ".+", "desc": "gives a reason"}
]}
EOF
CD_WORK_HYB="$TESTROOT/cd-work-hybrid"
mkdir -p "$CD_WORK_HYB"
env -u COUNCIL_ALLOW_EXEC python3 "$SCORE_DIR/command-diff.py" \
  "$CD_ITEM_HYB" "$CD_ANSWER_AWK_OK" "$CD_WORK_HYB"
assert_eq "$(json_get "$CD_WORK_HYB/score.json" "d['status']")" "scored-static" \
  "gate closed + checks.json -> falls back to static rubric"
assert_float_close "$(json_get "$CD_WORK_HYB/score.json" "d['score']")" "1.0" "0.0001" \
  "static fallback scores the rubric (all 4 checks satisfied)"
# With the gate OPEN the same item is scored by execution instead.
CD_WORK_HYB_ON="$TESTROOT/cd-work-hybrid-on"
run_scorer command-diff "$CD_ITEM_HYB" "$CD_ANSWER_AWK_OK" "$CD_WORK_HYB_ON"
assert_eq "$(json_get "$CD_WORK_HYB_ON/score.json" "d['status']")" "scored" \
  "gate open -> execution takes precedence over the static rubric"

# 6f. A destructive command is REFUSED before execution, and the input survives.
CD_ANSWER_RM="$TESTROOT/cd-answer-rm.txt"
cat > "$CD_ANSWER_RM" <<'EOF'
{"commands": ["rm -rf app.log"], "reason": "clean up first"}
EOF
CD_WORK_RM="$TESTROOT/cd-work-rm"
run_scorer command-diff "$CD_ITEM" "$CD_ANSWER_RM" "$CD_WORK_RM"
assert_eq "$(json_get "$CD_WORK_RM/score.json" "d['status']")" "unsafe-command" \
  "rm -rf -> status unsafe-command"
assert_float_close "$(json_get "$CD_WORK_RM/score.json" "d['score']")" "0.0" "0.0001" \
  "rm -rf -> score 0"
if [ -f "$CD_ITEM/inputs/app.log" ]; then
  pass "rm -rf was NOT executed (item input still present)"
else
  fail "rm -rf DELETED the item input — the safety gate did not hold"
fi

# 6g. A non-allowlisted (egress) binary is refused even inside a pipeline.
CD_ANSWER_CURL="$TESTROOT/cd-answer-curl.txt"
cat > "$CD_ANSWER_CURL" <<'EOF'
{"commands": ["curl -s http://example.invalid/log | grep -A 3 ERROR"], "reason": "fetch then filter"}
EOF
CD_WORK_CURL="$TESTROOT/cd-work-curl"
run_scorer command-diff "$CD_ITEM" "$CD_ANSWER_CURL" "$CD_WORK_CURL"
assert_eq "$(json_get "$CD_WORK_CURL/score.json" "d['status']")" "unsafe-command" \
  "curl in a pipeline -> status unsafe-command"

# 6h. A shell redirect that would mutate the input is refused.
CD_ANSWER_REDIR="$TESTROOT/cd-answer-redir.txt"
cat > "$CD_ANSWER_REDIR" <<'EOF'
{"commands": ["grep -A 3 ERROR app.log > app.log"], "reason": "filter in place"}
EOF
CD_WORK_REDIR="$TESTROOT/cd-work-redir"
run_scorer command-diff "$CD_ITEM" "$CD_ANSWER_REDIR" "$CD_WORK_REDIR"
assert_eq "$(json_get "$CD_WORK_REDIR/score.json" "d['status']")" "unsafe-command" \
  "output redirect -> status unsafe-command"

# 6i. A command that never terminates is killed and reported as a timeout.
CD_ANSWER_HANG="$TESTROOT/cd-answer-hang.txt"
cat > "$CD_ANSWER_HANG" <<'EOF'
{"commands": ["awk 'BEGIN{while(1){}}' app.log"], "reason": "spin"}
EOF
cat > "$CD_ITEM/expected/exec.json.hang" <<'EOF'
{"field": "commands", "golden_stdout": "stdout.txt",
 "allow_binaries": ["awk", "grep"], "timeout_s": 2}
EOF
CD_ITEM_HANG="$TESTROOT/cd-item-hang"
mkdir -p "$CD_ITEM_HANG/expected"
cp -R "$CD_ITEM/inputs" "$CD_ITEM_HANG/inputs"
cp "$CD_ITEM/item.json" "$CD_ITEM_HANG/item.json"
cp "$CD_ITEM/expected/stdout.txt" "$CD_ITEM_HANG/expected/stdout.txt"
mv "$CD_ITEM/expected/exec.json.hang" "$CD_ITEM_HANG/expected/exec.json"
CD_WORK_HANG="$TESTROOT/cd-work-hang"
run_scorer command-diff "$CD_ITEM_HANG" "$CD_ANSWER_HANG" "$CD_WORK_HANG"
assert_eq "$(json_get "$CD_WORK_HANG/score.json" "d['status']")" "timeout" \
  "non-terminating command -> status timeout"
assert_float_close "$(json_get "$CD_WORK_HANG/score.json" "d['score']")" "0.0" "0.0001" \
  "non-terminating command -> score 0"

# 6j. contract-fail: prose with no JSON object.
CD_ANSWER_CF="$TESTROOT/cd-answer-cf.txt"
cat > "$CD_ANSWER_CF" <<'EOF'
I would use grep with the after-context flag, but here is no JSON.
EOF
CD_WORK_CF="$TESTROOT/cd-work-cf"
run_scorer command-diff "$CD_ITEM" "$CD_ANSWER_CF" "$CD_WORK_CF"
assert_eq "$(json_get "$CD_WORK_CF/score.json" "d['status']")" "contract-fail" \
  "command-diff: no JSON object -> status contract-fail"

# 6k. The scorer must also work when invoked DIRECTLY via its shebang, the way
#     assess.sh calls it — the executable-bit class of bug (#235) caught live.
CD_WORK_EXEC="$TESTROOT/cd-work-exec"
mkdir -p "$CD_WORK_EXEC"
if [ -x "$SCORE_DIR/command-diff.py" ]; then
  pass "command-diff.py is executable (assess.sh invokes scorers directly)"
else
  fail "command-diff.py is NOT executable — assess.sh would fail silently"
fi
"$SCORE_DIR/command-diff.py" "$CD_ITEM" "$CD_ANSWER_GREP" "$CD_WORK_EXEC" || true
assert_float_close "$(json_get "$CD_WORK_EXEC/score.json" "d['score']")" "1.0" "0.0001" \
  "direct shebang invocation scores identically to python3 invocation"

unset COUNCIL_ALLOW_EXEC
echo

echo "=== Results: $PASS passed, $FAIL failed ==="
[ "$FAIL" -eq 0 ]
