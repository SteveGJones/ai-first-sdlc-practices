#!/usr/bin/env bash
# Unit tests for the token-free / accounting utility scripts under
# scripts/council/: schedule.py, usage.py, estimate.py, complexity.py
# (stage-2 implementation contract S7). All fixtures (stack.json, item
# dirs, handle dirs, pricing.json) are crafted throwaway files built by
# this test itself under ./tmp -- nothing here reads or depends on the
# shipped assessment/stack/v1 stack or scripts/council/pricing.json.
#
# Run: bash plugins/sdlc-model-council/tests/test-council-harness-utils.sh
#
# Prints "=== Results: N passed, M failed ===" and exits nonzero on any
# failure. Stdlib Python 3 only; bash 3.2 compatible (no associative
# arrays, no [[ ]]-only constructs relied upon for portability -- matches
# this repo's other test scripts).

set -u

THIS_DIR="$(cd "$(dirname "$0")" && pwd -P)"
PLUGIN_ROOT="$(cd "$THIS_DIR/.." && pwd -P)"
COUNCIL="$PLUGIN_ROOT/scripts/council"

# Repo rule: ./tmp, never /tmp -- scoped under the plugin dir since this
# suite is documented to run "from plugin dir".
mkdir -p "$PLUGIN_ROOT/tmp"
TESTROOT="$(mktemp -d "$PLUGIN_ROOT/tmp/council-harness-test.XXXXXX")"
trap 'rm -rf "$TESTROOT"' EXIT

PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); printf 'PASS: %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf 'FAIL: %s\n' "$1"; }

assert_eq() {
  # assert_eq <actual> <expected> <label>
  if [ "$1" = "$2" ]; then
    pass "$3"
  else
    fail "$3 (expected [$2], got [$1])"
  fi
}

# Numeric comparison with an absolute tolerance, done in python3 (stdlib)
# rather than bash/bc, so this suite never depends on bc being installed.
assert_close() {
  # assert_close <actual> <expected> <tol> <label>
  actual="$1"; expected="$2"; tol="$3"; label="$4"
  ok=$(python3 -c "
actual = float('$actual')
expected = float('$expected')
tol = float('$tol')
print('1' if abs(actual - expected) <= tol else '0')
" 2>/dev/null)
  if [ "$ok" = "1" ]; then
    pass "$label"
  else
    fail "$label (expected ~[$expected] +/- $tol, got [$actual])"
  fi
}

echo "=== council harness-utils test suite ==="
echo "TESTROOT=$TESTROOT"
echo

# =============================================================================
# 1. schedule.py -- 3-item stack, 2 models, dim filter, min-context filter
# =============================================================================
echo "--- 1. schedule.py ---"

STACK_DIR="$TESTROOT/stack1"
mkdir -p "$STACK_DIR/items/code-review/item-a" \
         "$STACK_DIR/items/bug-fix/item-b" \
         "$STACK_DIR/items/code-review/item-c"

cat > "$STACK_DIR/stack.json" <<'EOF'
{
  "schema_version": 1,
  "stack_version": "v1",
  "items": [
    {"id": "item-a", "dimension": "code-review", "path": "items/code-review/item-a", "sha256": "aaa111"},
    {"id": "item-b", "dimension": "bug-fix", "path": "items/bug-fix/item-b", "sha256": "bbb222"},
    {"id": "item-c", "dimension": "code-review", "path": "items/code-review/item-c", "sha256": "ccc333"}
  ]
}
EOF
printf '{"timeout_s": 30, "min_context_tokens": 1000}' > "$STACK_DIR/items/code-review/item-a/item.json"
printf '{"timeout_s": 60, "min_context_tokens": 5000}' > "$STACK_DIR/items/bug-fix/item-b/item.json"
printf '{"timeout_s": 90, "min_context_tokens": 200000}' > "$STACK_DIR/items/code-review/item-c/item.json"

PLAN=$(python3 "$COUNCIL/schedule.py" \
  --stack "$STACK_DIR/stack.json" \
  --models modelA,modelB \
  --dims code-review,bug-fix \
  --min-context-map modelA=300000,modelB=2000)

N_PAIRS=$(printf '%s' "$PLAN" | python3 -c "import json,sys; print(json.load(sys.stdin)['n_pairs'])")
assert_eq "$N_PAIRS" "4" "schedule.py: n_pairs is 4 (3 for modelA, 1 for modelB after context filter)"

STACK_VERSION=$(printf '%s' "$PLAN" | python3 -c "import json,sys; print(json.load(sys.stdin)['stack_version'])")
assert_eq "$STACK_VERSION" "v1" "schedule.py: stack_version passed through"

MODELA_COUNT=$(printf '%s' "$PLAN" | python3 -c "
import json, sys
plan = json.load(sys.stdin)
print(sum(1 for p in plan['pairs'] if p['model'] == 'modelA'))
")
assert_eq "$MODELA_COUNT" "3" "schedule.py: modelA (huge context) gets all 3 items"

MODELB_ITEMS=$(printf '%s' "$PLAN" | python3 -c "
import json, sys
plan = json.load(sys.stdin)
items = sorted(p['item'] for p in plan['pairs'] if p['model'] == 'modelB')
print(','.join(items))
")
assert_eq "$MODELB_ITEMS" "item-a" "schedule.py: modelB (2000 context) keeps only item-a, drops item-b (5000) and item-c (200000)"

ITEM_A_TIMEOUT=$(printf '%s' "$PLAN" | python3 -c "
import json, sys
plan = json.load(sys.stdin)
row = next(p for p in plan['pairs'] if p['model'] == 'modelB' and p['item'] == 'item-a')
print(row['timeout_s'])
")
assert_eq "$ITEM_A_TIMEOUT" "30" "schedule.py: surviving pair carries the item's timeout_s from item.json"
echo

# =============================================================================
# 2. usage.py -- opencode handle dir (exact tokens+cost) and agy handle dir
#    (estimated tokens from char counts)
# =============================================================================
echo "--- 2. usage.py ---"

# --- 2a. opencode: two turns, step_finish tokens+cost summed exactly ---
OC_HANDLE="$TESTROOT/handle-opencode"
mkdir -p "$OC_HANDLE"
printf '{"cli": "opencode", "model": "opencode/deepseek-v4-flash-free"}' > "$OC_HANDLE/meta.json"
cat > "$OC_HANDLE/turn-001.events.jsonl" <<'EOF'
{"type":"step_start","sessionID":"ses_1"}
{"type":"text","sessionID":"ses_1","part":{"type":"text","text":"hello"}}
{"type":"step_finish","sessionID":"ses_1","part":{"tokens":11,"cost":0.001}}
EOF
cat > "$OC_HANDLE/turn-002.events.jsonl" <<'EOF'
{"type":"step_start","sessionID":"ses_1"}
{"type":"step_finish","sessionID":"ses_1","part":{"tokens":9,"cost":0.0005}}
EOF

OC_USAGE=$(python3 "$COUNCIL/usage.py" "$OC_HANDLE")
OC_TOKENS_OUT=$(printf '%s' "$OC_USAGE" | python3 -c "import json,sys; print(json.load(sys.stdin)['tokens_out'])")
OC_TOKENS_IN=$(printf '%s' "$OC_USAGE" | python3 -c "import json,sys; print(json.load(sys.stdin)['tokens_in'])")
OC_BASIS=$(printf '%s' "$OC_USAGE" | python3 -c "import json,sys; print(json.load(sys.stdin)['cost_basis'])")
OC_COST=$(printf '%s' "$OC_USAGE" | python3 -c "import json,sys; print(json.load(sys.stdin)['cost_usd'])")

assert_eq "$OC_TOKENS_OUT" "20" "usage.py opencode: tokens_out summed across turns (11+9)"
assert_eq "$OC_TOKENS_IN" "0" "usage.py opencode: tokens_in is 0 (split unknown, all goes to tokens_out)"
assert_eq "$OC_BASIS" "exact" "usage.py opencode: cost_basis is exact"
assert_close "$OC_COST" "0.0015" "0.0000001" "usage.py opencode: cost_usd summed exactly (0.001+0.0005)"

# --- 2b. agy: no usage events -> estimate tokens from char counts ---
AGY_HANDLE="$TESTROOT/handle-agy"
mkdir -p "$AGY_HANDLE"
printf '{"cli": "agy", "model": "gemini-3.6-flash-medium"}' > "$AGY_HANDLE/meta.json"
# 40 chars -> 10 est tokens
python3 -c "open('$AGY_HANDLE/turn-001.last-message.txt','w').write('A'*40)"
# 20 chars -> 5 est tokens
python3 -c "open('$AGY_HANDLE/turn-002.last-message.txt','w').write('B'*20)"
# 8 chars of prompt -> 2 est input tokens
python3 -c "open('$AGY_HANDLE/turn-001.prompt.txt','w').write('P'*8)"

AGY_USAGE=$(python3 "$COUNCIL/usage.py" "$AGY_HANDLE")
AGY_TOKENS_OUT=$(printf '%s' "$AGY_USAGE" | python3 -c "import json,sys; print(json.load(sys.stdin)['tokens_out'])")
AGY_TOKENS_IN=$(printf '%s' "$AGY_USAGE" | python3 -c "import json,sys; print(json.load(sys.stdin)['tokens_in'])")
AGY_BASIS=$(printf '%s' "$AGY_USAGE" | python3 -c "import json,sys; print(json.load(sys.stdin)['cost_basis'])")
AGY_COST=$(printf '%s' "$AGY_USAGE" | python3 -c "import json,sys; print(json.load(sys.stdin)['cost_usd'])")

assert_eq "$AGY_TOKENS_OUT" "15" "usage.py agy: tokens_out estimated as chars//4 summed across turns (40//4 + 20//4)"
assert_eq "$AGY_TOKENS_IN" "2" "usage.py agy: tokens_in estimated from prompt files (8//4)"
assert_eq "$AGY_BASIS" "estimated" "usage.py agy: cost_basis is estimated"
assert_eq "$AGY_COST" "0.0" "usage.py agy: cost_usd is 0.0 with no --pricing passed"

# --- 2c. agy with --pricing + --family override: cost computed from rates ---
UPRICING="$TESTROOT/usage-pricing.json"
cat > "$UPRICING" <<'EOF'
{"families": {"fam-a": {"input_per_mtok": 10.0, "output_per_mtok": 20.0, "free": false}}}
EOF
AGY_PRICED=$(python3 "$COUNCIL/usage.py" "$AGY_HANDLE" --pricing "$UPRICING" --family fam-a)
AGY_PRICED_COST=$(printf '%s' "$AGY_PRICED" | python3 -c "import json,sys; print(json.load(sys.stdin)['cost_usd'])")
# (tokens_in=2 * 10 + tokens_out=15 * 20) / 1e6 = (20 + 300) / 1e6 = 0.00032
assert_close "$AGY_PRICED_COST" "0.00032" "0.0000001" "usage.py agy: --pricing + --family override computes (tokens_in*input_rate + tokens_out*output_rate)/1e6"
echo

# =============================================================================
# 3. estimate.py -- 2-family pricing.json + 2-item stack, hand-computed total
# =============================================================================
echo "--- 3. estimate.py ---"

EPRICING="$TESTROOT/estimate-pricing.json"
cat > "$EPRICING" <<'EOF'
{
  "families": {
    "fam-a": {"input_per_mtok": 10.0, "output_per_mtok": 20.0, "free": false},
    "fam-b": {"input_per_mtok": 0.0, "output_per_mtok": 0.0, "free": true}
  }
}
EOF

ESTACK_DIR="$TESTROOT/stack2"
mkdir -p "$ESTACK_DIR/items/long-context/item-x" "$ESTACK_DIR/items/instruction-format/item-y"
cat > "$ESTACK_DIR/stack.json" <<'EOF'
{
  "schema_version": 1,
  "stack_version": "v1",
  "items": [
    {"id": "item-x", "dimension": "long-context", "path": "items/long-context/item-x", "sha256": "xxx"},
    {"id": "item-y", "dimension": "instruction-format", "path": "items/instruction-format/item-y", "sha256": "yyy"}
  ]
}
EOF
printf '{"est_prompt_tokens": 1000, "est_output_tokens": 200}' > "$ESTACK_DIR/items/long-context/item-x/item.json"
printf '{"est_prompt_tokens": 500, "est_output_tokens": 100}' > "$ESTACK_DIR/items/instruction-format/item-y/item.json"

ESTIMATE=$(python3 "$COUNCIL/estimate.py" \
  --pricing "$EPRICING" \
  --stack "$ESTACK_DIR/stack.json" \
  --models vendorA:model-fam-a,vendorB:model-fam-b \
  --dims long-context,instruction-format \
  --k 2 2>/dev/null)

# Hand-computed:
#   item-x: (1000*10 + 200*20)/1e6 = 0.014   item-y: (500*10 + 100*20)/1e6 = 0.007
#   vendorA (fam-a) per-item sum = 0.021, * k=2 = 0.042
#   vendorB (fam-b, 0-rated) = 0.0
#   total = 0.042
TOTAL_USD=$(printf '%s' "$ESTIMATE" | python3 -c "import json,sys; print(json.load(sys.stdin)['total_usd'])")
assert_close "$TOTAL_USD" "0.042" "0.000001" "estimate.py: total_usd matches hand-computed sum across both models"

VENDORA_USD=$(printf '%s' "$ESTIMATE" | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(d['per_model']['vendorA:model-fam-a']['est_usd'])
")
assert_close "$VENDORA_USD" "0.042" "0.000001" "estimate.py: per_model est_usd for the priced family (k=2 fan-out applied)"

VENDORB_USD=$(printf '%s' "$ESTIMATE" | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(d['per_model']['vendorB:model-fam-b']['est_usd'])
")
assert_eq "$VENDORB_USD" "0.0" "estimate.py: per_model est_usd for the free/zero-rated family is 0.0"

ITEMS_COUNT=$(printf '%s' "$ESTIMATE" | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(d['per_model']['vendorA:model-fam-a']['items'])
")
assert_eq "$ITEMS_COUNT" "2" "estimate.py: per_model items count reflects both in-scope dims"
echo

# =============================================================================
# 4. complexity.py -- known branch count over a small crafted file
# =============================================================================
echo "--- 4. complexity.py ---"

COMPLEX_PY="$TESTROOT/complexity_fixture.py"
cat > "$COMPLEX_PY" <<'EOF'
def f(items):
    if items:
        pass
    for i in items:
        pass
    while items:
        break
    try:
        pass
    except Exception:
        pass
    flag = items and True
    listed = [i for i in items]
    setted = {i for i in items}
    mapped = {i: i for i in items}
    gen = (i for i in items)
    return flag, listed, setted, mapped, gen
EOF

COMPLEXITY=$(python3 "$COUNCIL/complexity.py" "$COMPLEX_PY")
BRANCHES=$(printf '%s' "$COMPLEXITY" | python3 -c "import json,sys; print(json.load(sys.stdin)['branches'])")
# If(1) + For(1) + While(1) + Try(1) + BoolOp(1) + ListComp(1) + SetComp(1)
# + DictComp(1) + GeneratorExp(1) = 9
assert_eq "$BRANCHES" "9" "complexity.py: counts exactly 9 branch nodes (If/For/While/Try/BoolOp/4 comprehension forms)"
echo

echo "=== Results: $PASS passed, $FAIL failed ==="
[ "$FAIL" -eq 0 ]
