#!/usr/bin/env bash
# Choreography tests for the Diff+Synthesis play spine (play.sh) over canned
# <label>.result.md files (design §9 point 4): blind labelling (no address
# leaks to the judge), quorum + degraded reporting, baseline_member recorded for
# the measurability spine, and label→address un-blinding on the way out.
# Bash 3.2 safe; no external models — pure choreography.
#
# Run: bash plugins/sdlc-model-council/tests/test-council-play.sh
set -u

THIS_DIR="$(cd "$(dirname "$0")" && pwd -P)"
PLUGIN_ROOT="$(cd "$THIS_DIR/.." && pwd -P)"
REPO_ROOT="$(cd "$PLUGIN_ROOT/../.." && pwd -P)"
COUNCIL="$PLUGIN_ROOT/scripts/council"
PLAY="$COUNCIL/play.sh"

mkdir -p "$REPO_ROOT/tmp"
TESTROOT="$(mktemp -d "$REPO_ROOT/tmp/play-test.XXXXXX")"
trap 'rm -rf "$TESTROOT"' EXIT
cd "$TESTROOT" || exit 1

PASS=0; FAIL=0
pass() { PASS=$((PASS + 1)); printf 'PASS: %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf 'FAIL: %s\n' "$1"; }
assert_eq() { if [ "$1" = "$2" ]; then pass "$3"; else fail "$3 (want [$2] got [$1])"; fi; }
assert_contains() { case "$1" in *"$2"*) pass "$3" ;; *) fail "$3 (missing [$2])" ;; esac; }
assert_not_contains() { case "$1" in *"$2"*) fail "$3 (unexpectedly found [$2])" ;; *) pass "$3" ;; esac; }

NOW="2026-07-25T00:00:00Z"
printf 'Review this diff for correctness bugs.\n' > "$TESTROOT/task.md"

jget() { python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))'"$2"')' "$1"; }

# ---------------------------------------------------------------------------
# 1. setup with a pinned cast — manifest, blind labels, dispatch table
# ---------------------------------------------------------------------------
CAST="codex:alpha,agy:beta,opencode:gamma"
OUT1="$("$PLAY" setup --dimension code-review --k 3 --cast "$CAST" \
  --task-file "$TESTROOT/task.md" --now "$NOW" --out "$TESTROOT/play1")"
assert_contains "$OUT1" "PLAY_DIR=$TESTROOT/play1" "1a setup echoes the play dir"
assert_eq "$(jget "$TESTROOT/play1/manifest.json" '["play"]')" "diff-synthesis" "1b manifest play type"
assert_eq "$(jget "$TESTROOT/play1/manifest.json" '["baseline_member"]')" "codex:alpha" "1c baseline_member = cast[0]"
NMEM="$(jget "$TESTROOT/play1/manifest.json" '["members"].__len__()')"
assert_eq "$NMEM" "3" "1d three members labelled"
LABELS="$(python3 -c 'import json;print(",".join(sorted(m["label"] for m in json.load(open("'"$TESTROOT"'/play1/manifest.json"))["members"])))')"
assert_eq "$LABELS" "A,B,C" "1e blind labels are A,B,C"
# baseline_label must be the label actually assigned to the baseline model
BL="$(jget "$TESTROOT/play1/manifest.json" '["baseline_label"]')"
BLMODEL="$(python3 -c 'import json;m={x["label"]:x["model"] for x in json.load(open("'"$TESTROOT"'/play1/manifest.json"))["members"]};print(m["'"$BL"'"])')"
assert_eq "$BLMODEL" "codex:alpha" "1f baseline_label maps back to the baseline model"
assert_file() { if [ -f "$1" ]; then pass "$2"; else fail "$2"; fi; }
assert_file "$TESTROOT/play1/task.md" "1g task.md copied into the play dir"
DISPATCH_LINES="$(printf '%s\n' "$OUT1" | grep -c '\.result\.md$')"
assert_eq "$DISPATCH_LINES" "3" "1h dispatch table lists 3 members"

# ---------------------------------------------------------------------------
# 2. combine-check at full quorum — blind bundle, no address leak
# ---------------------------------------------------------------------------
for L in A B C; do
  printf 'Finding from an anonymous model: the loop bound is off by one.\n' \
    > "$TESTROOT/play1/$L.result.md"
done
CC="$("$PLAY" combine-check --play-dir "$TESTROOT/play1")"
assert_eq "$(printf '%s' "$CC" | python3 -c 'import json,sys;print(json.load(sys.stdin)["survivors"])')" "3" "2a all 3 responses survived"
assert_eq "$(printf '%s' "$CC" | python3 -c 'import json,sys;print(json.load(sys.stdin)["degraded"])')" "False" "2b not degraded at full quorum"
assert_eq "$(printf '%s' "$CC" | python3 -c 'import json,sys;print(json.load(sys.stdin)["verdict"])')" "OK" "2c verdict OK"
BUNDLE="$(cat "$TESTROOT/play1/combine/blind-bundle.md")"
assert_contains "$BUNDLE" "Model A" "2d bundle labels responses by blind label"
assert_not_contains "$BUNDLE" "codex:alpha" "2e bundle does NOT leak the model address (bias containment)"
assert_not_contains "$BUNDLE" "agy:beta" "2f bundle does NOT leak the second address"

# ---------------------------------------------------------------------------
# 3. combine-check degraded — too few survivors
# ---------------------------------------------------------------------------
"$PLAY" setup --dimension code-review --k 3 --cast "$CAST" \
  --task-file "$TESTROOT/task.md" --now "$NOW" --out "$TESTROOT/play2" >/dev/null
# only one member responds; the other two are missing → below quorum (2)
FIRST_LABEL="$(python3 -c 'import json;print(sorted(m["label"] for m in json.load(open("'"$TESTROOT"'/play2/manifest.json"))["members"])[0])')"
printf 'the one response that came back\n' > "$TESTROOT/play2/$FIRST_LABEL.result.md"
CC2="$("$PLAY" combine-check --play-dir "$TESTROOT/play2")"
assert_eq "$(printf '%s' "$CC2" | python3 -c 'import json,sys;print(json.load(sys.stdin)["survivors"])')" "1" "3a one survivor"
assert_eq "$(printf '%s' "$CC2" | python3 -c 'import json,sys;print(json.load(sys.stdin)["verdict"])')" "PLAY-DEGRADED" "3b degraded verdict below quorum"

# ---------------------------------------------------------------------------
# 4. unblind — the judge's blind labels become model addresses
# ---------------------------------------------------------------------------
printf 'Convergent: Model A and Model C agree. Adjudication: trust Model A.\n' \
  > "$TESTROOT/synthesis.md"
UNB="$("$PLAY" unblind --play-dir "$TESTROOT/play1" --in "$TESTROOT/synthesis.md")"
assert_not_contains "$UNB" "Model A" "4a unblinded synthesis no longer says 'Model A'"
A_MODEL="$(python3 -c 'import json;m={x["label"]:x["model"] for x in json.load(open("'"$TESTROOT"'/play1/manifest.json"))["members"]};print(m["A"])')"
assert_contains "$UNB" "$A_MODEL" "4b unblinded synthesis attributes to the real model address"

# ---------------------------------------------------------------------------
# 5. setup via roster — cast.py picks the baseline (best posterior)
# ---------------------------------------------------------------------------
cat > "$TESTROOT/roster.json" <<'JSON'
{"schema_version":1,"stack_version":"v1","source":"priors+audition","generated_ts":"t","k":3,
 "models":[
  {"model":"m:top","reachable":true,"free":false,"mean_cost_usd_per_item":0.01,"dimensions":{"code-review":{"posterior":0.82}}},
  {"model":"m:mid","reachable":true,"free":false,"mean_cost_usd_per_item":0.01,"dimensions":{"code-review":{"posterior":0.70}}},
  {"model":"m:low","reachable":true,"free":false,"mean_cost_usd_per_item":0.01,"dimensions":{"code-review":{"posterior":0.55}}}]}
JSON
cat > "$TESTROOT/diversity.json" <<'JSON'
{"schema_version":1,"stack_version":"v1","generated_ts":"t","pairs":[
 {"a":"m:top","b":"m:mid","n_common":9,"agree_rate":0.5,"phi":0.1,"both_wrong_rate":0.2,"insufficient":false},
 {"a":"m:top","b":"m:low","n_common":9,"agree_rate":0.5,"phi":0.1,"both_wrong_rate":0.2,"insufficient":false},
 {"a":"m:mid","b":"m:low","n_common":9,"agree_rate":0.5,"phi":0.1,"both_wrong_rate":0.2,"insufficient":false}]}
JSON
"$PLAY" setup --dimension code-review --k 3 --roster "$TESTROOT/roster.json" \
  --diversity "$TESTROOT/diversity.json" --task-file "$TESTROOT/task.md" \
  --now "$NOW" --out "$TESTROOT/play3" >/dev/null
assert_eq "$(jget "$TESTROOT/play3/manifest.json" '["baseline_member"]')" "m:top" "5a cast.py picks the top-posterior model as baseline"

echo "=== Results: $PASS passed, $FAIL failed ==="
[ "$FAIL" -eq 0 ]
