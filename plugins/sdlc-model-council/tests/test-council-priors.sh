#!/usr/bin/env bash
# Data-validation suite for scripts/council/pricing.json and
# scripts/council/priors/*.json (issue #232, stage-2 contract §8/§9 —
# see docs/superpowers/specs/2026-07-25-sdlc-model-council-design.md
# §5.3, §6). This is a pure data lint: it never spends API quota, never
# invokes an adapter, and does not depend on priors.py (the resolver is
# built separately and consumed by roster.py in a later stage).
#
# Checked:
#   1. pricing.json parses as JSON and every family has
#      input_per_mtok/output_per_mtok/free.
#   2. Each priors/*.json parses, has schema_version==1, all 9 dimension
#      keys with values in [0,1], a `matches` list, and a `pricing_ref`
#      that names a real pricing.json family.
#   3. The union of `matches` across all non-unknown families is
#      non-empty.
#   4. Four representative addresses each substring-match at least one
#      non-unknown family's `matches` list.
#
# Run: bash plugins/sdlc-model-council/tests/test-council-priors.sh

set -u

THIS_DIR="$(cd "$(dirname "$0")" && pwd -P)"
PLUGIN_ROOT="$(cd "$THIS_DIR/.." && pwd -P)"
COUNCIL_DIR="$PLUGIN_ROOT/scripts/council"
PRICING="$COUNCIL_DIR/pricing.json"
PRIORS_DIR="$COUNCIL_DIR/priors"

PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); printf 'PASS: %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf 'FAIL: %s\n' "$1"; }

echo "=== council pricing + priors data validation ==="
echo "COUNCIL_DIR=$COUNCIL_DIR"
echo

# ---------------------------------------------------------------------
# 1. pricing.json exists and parses (literal python3 -c json.load check).
# ---------------------------------------------------------------------
if [ ! -f "$PRICING" ]; then
  fail "pricing.json missing at $PRICING"
  echo
  echo "=== Results: $PASS passed, $FAIL failed ==="
  [ "$FAIL" -eq 0 ]
  exit $?
fi

if python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$PRICING" >/dev/null 2>&1; then
  pass "pricing.json parses as JSON"
else
  fail "pricing.json failed to parse as JSON"
  echo
  echo "=== Results: $PASS passed, $FAIL failed ==="
  [ "$FAIL" -eq 0 ]
  exit $?
fi

# 1b. every family in pricing.json has input_per_mtok/output_per_mtok/free.
pricing_families="$(jq -r '.families | keys[]' "$PRICING" 2>/dev/null)"
if [ -z "$pricing_families" ]; then
  fail "pricing.json has no families"
else
  pass "pricing.json has families: $(printf '%s' "$pricing_families" | tr '\n' ' ')"
  fields_ok=1
  for fam in $pricing_families; do
    for field in input_per_mtok output_per_mtok free; do
      if ! jq -e --arg f "$fam" --arg k "$field" '.families[$f] | has($k)' "$PRICING" >/dev/null 2>&1; then
        fail "pricing.json families.$fam missing key '$field'"
        fields_ok=0
      fi
    done
  done
  [ "$fields_ok" -eq 1 ] && pass "every pricing.json family has input_per_mtok/output_per_mtok/free"
fi

echo

# ---------------------------------------------------------------------
# 2. priors/*.json — parses, schema_version, matches list, pricing_ref,
#    and all 9 dimension keys in [0,1].
# ---------------------------------------------------------------------
if [ ! -d "$PRIORS_DIR" ]; then
  fail "priors directory missing at $PRIORS_DIR"
else
  prior_files=$(ls "$PRIORS_DIR"/*.json 2>/dev/null)
  if [ -z "$prior_files" ]; then
    fail "no priors/*.json files found"
  else
    for pf in $prior_files; do
      name="$(basename "$pf")"
      echo "--- prior: $name ---"

      if ! python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$pf" >/dev/null 2>&1; then
        fail "$name: failed to parse as JSON"
        continue
      fi
      pass "$name: parses as JSON"

      if [ "$(jq -r '.schema_version // empty' "$pf" 2>/dev/null)" = "1" ]; then
        pass "$name: schema_version == 1"
      else
        fail "$name: schema_version is not 1"
      fi

      if jq -e '.matches | type == "array"' "$pf" >/dev/null 2>&1; then
        pass "$name: matches is a list"
      else
        fail "$name: matches is missing or not a list"
      fi

      pricing_ref="$(jq -r '.pricing_ref // empty' "$pf" 2>/dev/null)"
      if [ -z "$pricing_ref" ]; then
        fail "$name: pricing_ref is missing"
      elif jq -e --arg r "$pricing_ref" '.families | has($r)' "$PRICING" >/dev/null 2>&1; then
        pass "$name: pricing_ref ('$pricing_ref') is a real pricing.json family"
      else
        fail "$name: pricing_ref ('$pricing_ref') does not name a pricing.json family"
      fi

      dim_report=$(python3 - "$pf" <<'PYEOF'
import json, sys

REQUIRED_DIMS = [
    "code-gen", "bug-fix", "code-review", "refactor", "reasoning",
    "research", "long-context", "instruction-format", "tool-use",
]

path = sys.argv[1]
try:
    data = json.load(open(path))
except Exception as exc:
    print(f"ERROR:parse failed: {exc}")
    sys.exit(1)

dims = data.get("dimensions")
if not isinstance(dims, dict):
    print("ERROR:dimensions is missing or not an object")
    sys.exit(1)

errors = []
for d in REQUIRED_DIMS:
    if d not in dims:
        errors.append(f"missing dimension '{d}'")
        continue
    v = dims[d]
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        errors.append(f"dimension '{d}' value is not numeric")
        continue
    if v < 0.0 or v > 1.0:
        errors.append(f"dimension '{d}' value {v} out of [0,1]")

if errors:
    print("ERROR:" + " | ".join(errors))
    sys.exit(1)

print("OK")
PYEOF
)
      if [ "$dim_report" = "OK" ]; then
        pass "$name: all 9 dimension keys present with values in [0,1]"
      else
        fail "$name: ${dim_report#ERROR:}"
      fi

      echo
    done
  fi
fi

# ---------------------------------------------------------------------
# 3 & 4. union of matches across non-unknown families is non-empty, and
#    four representative addresses each substring-match at least one
#    non-unknown family via a simple substring test.
# ---------------------------------------------------------------------
match_report=$(python3 - "$PRIORS_DIR" <<'PYEOF'
import glob
import json
import os
import sys

priors_dir = sys.argv[1]

ADDRESSES = [
    "codex:default@medium",
    "agy:gemini-3.1-pro-high",
    "agy:gemini-3.6-flash-medium",
    "opencode:opencode/deepseek-v4-flash-free",
]

families = {}
for path in sorted(glob.glob(os.path.join(priors_dir, "*.json"))):
    name = os.path.splitext(os.path.basename(path))[0]
    try:
        data = json.load(open(path))
    except Exception as exc:
        print(f"ERROR:{name}: failed to parse: {exc}")
        sys.exit(1)
    families[name] = data.get("matches", [])

non_unknown = {fam: subs for fam, subs in families.items() if fam != "unknown"}

union = []
for subs in non_unknown.values():
    union.extend(subs)

if not union:
    print("ERROR:union of matches across non-unknown families is empty")
    sys.exit(1)

lines = [f"OK:union has {len(union)} substring(s) across {len(non_unknown)} non-unknown families"]

for addr in ADDRESSES:
    hit_family = None
    for fam, subs in non_unknown.items():
        if any(sub and sub in addr for sub in subs):
            hit_family = fam
            break
    if hit_family is None:
        print(f"ERROR:address '{addr}' matched no non-unknown family")
        sys.exit(1)
    lines.append(f"OK:'{addr}' matches family '{hit_family}'")

print("\n".join(lines))
PYEOF
)

if printf '%s\n' "$match_report" | grep -q '^ERROR:'; then
  while IFS= read -r line; do
    case "$line" in
      ERROR:*) fail "${line#ERROR:}" ;;
    esac
  done <<EOF
$match_report
EOF
else
  while IFS= read -r line; do
    case "$line" in
      OK:*) pass "${line#OK:}" ;;
    esac
  done <<EOF
$match_report
EOF
fi

echo
echo "=== Results: $PASS passed, $FAIL failed ==="
[ "$FAIL" -eq 0 ]
