#!/usr/bin/env bash
# End-to-end tests for assess.sh over the MOCK fleet (design §9 point 5): the
# estimate gate, free wave-0 calibration, cap-N concurrency drain, mid-run
# budget hard-stop + resume, and timeout rows. Every external call goes through
# the real extdel.sh against mock CLIs on PATH — no real tokens. State is
# isolated by cd-ing into a throwaway TESTROOT (extdel keys its state dir off
# $(pwd)), exactly like the substrate suites. Bash 3.2 safe.
#
# Run: bash plugins/sdlc-model-council/tests/test-council-assess.sh
set -u

THIS_DIR="$(cd "$(dirname "$0")" && pwd -P)"
PLUGIN_ROOT="$(cd "$THIS_DIR/.." && pwd -P)"
REPO_ROOT="$(cd "$PLUGIN_ROOT/../.." && pwd -P)"
COUNCIL="$PLUGIN_ROOT/scripts/council"
ASSESS="$COUNCIL/assess.sh"
STACK_V1="$PLUGIN_ROOT/assessment/stack/v1/stack.json"
PRIORS="$COUNCIL/priors"
PRICING="$COUNCIL/pricing.json"
MOCK_BIN="$THIS_DIR/fixtures/mock-bin"

mkdir -p "$REPO_ROOT/tmp"
TESTROOT="$(mktemp -d "$REPO_ROOT/tmp/assess-test.XXXXXX")"
trap 'rm -rf "$TESTROOT"' EXIT
export HOME="$TESTROOT/fake-home"; mkdir -p "$HOME"
export PATH="$MOCK_BIN:$PATH"
cd "$TESTROOT" || exit 1

PASS=0; FAIL=0
pass() { PASS=$((PASS + 1)); printf 'PASS: %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf 'FAIL: %s\n' "$1"; }
assert_eq() { if [ "$1" = "$2" ]; then pass "$3"; else fail "$3 (want [$2] got [$1])"; fi; }
assert_contains() { case "$1" in *"$2"*) pass "$3" ;; *) fail "$3 (missing [$2])" ;; esac; }
assert_file() { if [ -f "$1" ]; then pass "$2"; else fail "$2 (missing file $1)"; fi; }

NOW="2026-07-25T00:00:00Z"
FREE2="opencode:opencode/deepseek-v4-flash-free,opencode:opencode/nemotron-3-ultra-free"
PAID2="opencode:paidA,opencode:paidB"

tally() { # tally <results.jsonl> <status>  -> count of rows with that status
  python3 -c 'import json,sys
n=sum(1 for l in open(sys.argv[1]) if l.strip() and json.loads(l).get("status")==sys.argv[2])
print(n)' "$1" "$2"
}
rows() { python3 -c 'import sys;print(sum(1 for l in open(sys.argv[1]) if l.strip()))' "$1"; }

# ---------------------------------------------------------------------------
# 1. Estimate gate — token-free, no handles, paid family resolves
# ---------------------------------------------------------------------------
R1="$TESTROOT/run-estimate"
OUT1="$("$ASSESS" --stack "$STACK_V1" --priors-dir "$PRIORS" --pricing "$PRICING" \
  --models "$FREE2" --dims long-context --estimate --no-reachability-check \
  --run-dir "$R1" --now "$NOW" 2>&1)"
assert_contains "$OUT1" "estimate-only" "1a estimate mode announces estimate-only"
HANDLES_AFTER_EST="$(find "$TESTROOT/tmp/model-council" -maxdepth 1 -type d -name 'opencode-*' 2>/dev/null | wc -l | tr -d ' ')"
assert_eq "$HANDLES_AFTER_EST" "0" "1b estimate mode spends no tokens (no handle dirs)"
# paid family resolves to a non-zero estimate (regression on the priors wiring)
ESTPAID="$("$COUNCIL/estimate.py" --pricing "$PRICING" --stack "$STACK_V1" \
  --models "codex:default@medium" --dims code-review --priors-dir "$PRIORS" 2>/dev/null)"
PAID_USD="$(printf '%s' "$ESTPAID" | python3 -c 'import json,sys;print(json.load(sys.stdin)["total_usd"])')"
NONZERO="$(python3 -c 'import sys;print("1" if float(sys.argv[1])>0 else "0")' "$PAID_USD")"
assert_eq "$NONZERO" "1" "1c paid model resolves to a non-zero estimate"

# ---------------------------------------------------------------------------
# 2. Free wave-0 end-to-end — 2 free models x 2 long-context items = 4 rows
# ---------------------------------------------------------------------------
R2="$TESTROOT/run-free"
"$ASSESS" --stack "$STACK_V1" --priors-dir "$PRIORS" --pricing "$PRICING" \
  --models "$FREE2" --dims long-context --no-reachability-check \
  --run-dir "$R2" --poll-wait-s 1 --now "$NOW" >/dev/null 2>&1
assert_eq "$(rows "$R2/results.jsonl")" "4" "2a free wave produced 4 rows"
assert_eq "$(tally "$R2/results.jsonl" scored)" "4" "2b all 4 rows scored (free calibration ran)"
assert_file "$R2/roster.json" "2c roster.json produced"
assert_file "$R2/diversity.json" "2d diversity.json produced"
assert_file "$R2/roster.md" "2e roster.md produced"
python3 -c 'import json,sys;json.load(open(sys.argv[1]))' "$R2/roster.json" \
  && pass "2f roster.json is valid JSON" || fail "2f roster.json is valid JSON"

# ---------------------------------------------------------------------------
# 3. Budget hard-stop — cap 1, cost 0.5, budget 1.0, 4 paid pairs
# ---------------------------------------------------------------------------
R3="$TESTROOT/run-budget"
OUT3="$(MOCK_OPENCODE_COST=0.5 "$ASSESS" --stack "$STACK_V1" --priors-dir "$PRIORS" \
  --pricing "$PRICING" --models "$PAID2" --dims instruction-format \
  --budget-usd 1.0 --max-concurrent 1 --no-reachability-check --run-dir "$R3" \
  --poll-wait-s 1 --now "$NOW" 2>&1)"
assert_contains "$OUT3" "budget hard-stop" "3a budget hard-stop fired"
assert_eq "$(tally "$R3/results.jsonl" skipped:budget)" "2" "3b 2 pairs marked skipped:budget"
NONSKIP3="$(python3 -c 'import json,sys
n=sum(1 for l in open(sys.argv[1]) if l.strip() and json.loads(l)["status"]!="skipped:budget")
print(n)' "$R3/results.jsonl")"
assert_eq "$NONSKIP3" "2" "3c exactly 2 pairs ran before the cap"
assert_contains "$OUT3" "Council spend: \$1.0" "3d spend line reports \$1.0"

# ---------------------------------------------------------------------------
# 4. Resume — reuse run 3's dir with a higher budget; skipped pairs complete
# ---------------------------------------------------------------------------
MOCK_OPENCODE_COST=0.5 "$ASSESS" --stack "$STACK_V1" --priors-dir "$PRIORS" \
  --pricing "$PRICING" --models "$PAID2" --dims instruction-format \
  --budget-usd 10.0 --max-concurrent 1 --no-reachability-check --resume \
  --run-dir "$R3" --poll-wait-s 1 --now "$NOW" >/dev/null 2>&1
assert_eq "$(tally "$R3/results.jsonl" skipped:budget)" "0" "4a resume cleared skipped:budget rows"
assert_eq "$(rows "$R3/results.jsonl")" "4" "4b resume completed all 4 pairs"

# ---------------------------------------------------------------------------
# 5. Timeout rows — item timeout_s=1, mock sleeps 3
# ---------------------------------------------------------------------------
FX="$TESTROOT/stack-timeout"
mkdir -p "$FX/items/long-context/lc-t/expected"
printf 'needle?\nRespond with ONLY the answer text on a single line.\n' > "$FX/items/long-context/lc-t/prompt.md"
printf 'NEEDLE-XYZ\n' > "$FX/items/long-context/lc-t/expected/answer.txt"
printf '%s' '{"schema_version":1,"id":"lc-t","dimension":"long-context","version":1,"difficulty":"easy","timeout_s":1,"min_context_tokens":0,"est_prompt_tokens":10,"est_output_tokens":5,"answer_contract":"text","scorer":{"type":"exact-match"}}' > "$FX/items/long-context/lc-t/item.json"
SHA_T="$(python3 "$COUNCIL/stack_hash.py" "$FX/items/long-context/lc-t")"
printf '{"schema_version":1,"stack_version":"vT","items":[{"id":"lc-t","dimension":"long-context","path":"items/long-context/lc-t","sha256":"%s"}]}' "$SHA_T" > "$FX/stack.json"
R5="$TESTROOT/run-timeout"
MOCK_OPENCODE_SLEEP=3 "$ASSESS" --stack "$FX/stack.json" --priors-dir "$PRIORS" \
  --pricing "$PRICING" --models "opencode:opencode/deepseek-v4-flash-free" \
  --dims long-context --no-reachability-check --run-dir "$R5" \
  --poll-wait-s 1 --now "$NOW" >/dev/null 2>&1
assert_eq "$(tally "$R5/results.jsonl" timeout)" "1" "5a slow turn recorded as a timeout row"
TSCORE="$(python3 -c 'import json;print(json.loads(open("'"$R5"'/results.jsonl").readline())["score"])')"
assert_eq "$TSCORE" "0.0" "5b timeout row scores 0.0"

# ---------------------------------------------------------------------------
# 6. Concurrency drain — cap 2 over 5 slow pairs, pool fully drains
# ---------------------------------------------------------------------------
FX6="$TESTROOT/stack-conc"
for i in 1 2 3 4 5; do
  d="$FX6/items/long-context/lc-$i"
  mkdir -p "$d/expected"
  printf 'q\nRespond with ONLY the answer text on a single line.\n' > "$d/prompt.md"
  printf 'A%s\n' "$i" > "$d/expected/answer.txt"
  printf '%s' '{"schema_version":1,"id":"lc-'"$i"'","dimension":"long-context","version":1,"difficulty":"easy","timeout_s":30,"min_context_tokens":0,"est_prompt_tokens":5,"est_output_tokens":2,"answer_contract":"text","scorer":{"type":"exact-match"}}' > "$d/item.json"
done
python3 - "$FX6" > "$FX6/stack.json" <<'PY'
import json, os, sys
base = sys.argv[1]
sys.path.insert(0, os.path.join(os.path.dirname(base), "..", "scripts", "council"))
items = []
for i in range(1, 6):
    p = f"items/long-context/lc-{i}"
    items.append({"id": f"lc-{i}", "dimension": "long-context", "path": p, "sha256": "x"})
print(json.dumps({"schema_version": 1, "stack_version": "vC", "items": items}))
PY
R6="$TESTROOT/run-conc"
MOCK_OPENCODE_SLEEP=1 "$ASSESS" --stack "$FX6/stack.json" --priors-dir "$PRIORS" \
  --pricing "$PRICING" --models "opencode:opencode/deepseek-v4-flash-free" \
  --dims long-context --max-concurrent 2 --no-reachability-check --run-dir "$R6" \
  --poll-wait-s 1 --now "$NOW" >/dev/null 2>&1
assert_eq "$(rows "$R6/results.jsonl")" "5" "6a cap-2 pool drained all 5 pairs"

# ---------------------------------------------------------------------------
# 6b. Resume back-fills prior spend into the budget cap (no cumulative overspend)
# ---------------------------------------------------------------------------
R6B="$TESTROOT/run-backfill"
MOCK_OPENCODE_COST=0.5 "$ASSESS" --stack "$STACK_V1" --priors-dir "$PRIORS" \
  --pricing "$PRICING" --models "$PAID2" --dims instruction-format \
  --budget-usd 1.0 --max-concurrent 1 --no-reachability-check --run-dir "$R6B" \
  --poll-wait-s 1 --now "$NOW" >/dev/null 2>&1   # prior spend $1.0, 2 skipped
# resume with budget 1.2: backfilled $1.0 + one more $0.5 = $1.5 >= 1.2 → stops
# again, leaving 1 skipped. Without back-fill, SPENT would start at 0 and both
# remaining pairs would run (0 skipped) — so this asserts the back-fill.
MOCK_OPENCODE_COST=0.5 "$ASSESS" --stack "$STACK_V1" --priors-dir "$PRIORS" \
  --pricing "$PRICING" --models "$PAID2" --dims instruction-format \
  --budget-usd 1.2 --max-concurrent 1 --no-reachability-check --resume \
  --run-dir "$R6B" --poll-wait-s 1 --now "$NOW" >/dev/null 2>&1
assert_eq "$(tally "$R6B/results.jsonl" skipped:budget)" "1" "6b resume back-fills prior spend (cumulative budget still enforced)"

# ---------------------------------------------------------------------------
# 7. Paid dispatch requires an explicit budget (no surprise spend)
# ---------------------------------------------------------------------------
set +e
OUT7="$("$ASSESS" --stack "$STACK_V1" --priors-dir "$PRIORS" --pricing "$PRICING" \
  --models "$PAID2" --dims instruction-format --no-reachability-check \
  --run-dir "$TESTROOT/run-nobudget" --now "$NOW" 2>&1)"
RC7=$?
set -e 2>/dev/null || true
if [ "$RC7" -ne 0 ]; then pass "7a paid run without --budget-usd is refused (nonzero exit)"; else fail "7a paid run without --budget-usd is refused"; fi
assert_contains "$OUT7" "requires --budget-usd" "7b refusal message names --budget-usd"

echo "=== Results: $PASS passed, $FAIL failed ==="
[ "$FAIL" -eq 0 ]
