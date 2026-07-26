#!/usr/bin/env bash
# Golden unit tests for the council arithmetic core: roster.py (shrinkage +
# roles), diversity.py (per-defect outcome vectors + pair correlation), cast.py
# (greedy decorrelated selection). Every asserted number is hand-computed from
# the stage-2 contract §4/§5/§6 formulas — this file is the correctness anchor
# for the arithmetic, so the fixtures are tiny and the expected values explicit.
#
# Runnable as `bash tests/test-council-roster.sh` from the plugin dir.
set -u

HERE="$(cd "$(dirname "$0")/.." && pwd)"
COUNCIL="$HERE/scripts/council"
WORK="$(mktemp -d "$HERE/tmp/council-roster-test.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT

PRIORS="$WORK/priors"
mkdir -p "$PRIORS"

# --- fixture priors (9 dims each) ------------------------------------------
python3 - "$PRIORS" <<'PY'
import json, os, sys
priors_dir = sys.argv[1]
DIMS = ["code-gen","bug-fix","code-review","refactor","reasoning",
        "research","long-context","instruction-format","tool-use"]
def write(fam, matches, pricing_ref, overrides=None, flags=None):
    dims = {d: 0.5 for d in DIMS}
    if overrides:
        dims.update(overrides)
    desc = {"schema_version":1, "family":fam, "matches":matches,
            "context_tokens":128000, "pricing_ref":pricing_ref,
            "provenance":"stage-2 golden-test fixture", "dimensions":dims,
            "flags":flags or []}
    with open(os.path.join(priors_dir, fam+".json"), "w") as f:
        json.dump(desc, f)
write("flatfam", ["flat:"], "flatfam")
write("rolefam", ["role:"], "rolefam")
write("lcfam",   ["lc:"],   "lcfam", overrides={"long-context":0.9})
write("freefam", ["free:"], "freefam")
write("unknown", [], "unknown", flags=["no-prior"])
PY

# --- fixture pricing (only freefam is free) --------------------------------
cat > "$WORK/pricing.json" <<'JSON'
{"schema_version":1,"asof":"2026-07-25","provenance":"fixture",
 "families":{"flatfam":{"input_per_mtok":1,"output_per_mtok":1,"free":false},
   "rolefam":{"input_per_mtok":1,"output_per_mtok":1,"free":false},
   "lcfam":{"input_per_mtok":1,"output_per_mtok":1,"free":false},
   "freefam":{"input_per_mtok":0,"output_per_mtok":0,"free":true},
   "unknown":{"input_per_mtok":0,"output_per_mtok":0,"free":false}}}
JSON

# --- fixture results.jsonl (roster + roles) --------------------------------
# Prior 0.5 everywhere except lcfam long-context=0.9. k=3, so
# posterior = (n*raw_mean + 1.5)/(n+3)  (lcfam LC: (n*rm + 2.7)/(n+3)).
python3 - "$WORK/results-roster.jsonl" <<'PY'
import json, sys
out = sys.argv[1]
rows = []
def add(model, dim, score, precision=None, cost=0.01, lat=1.0):
    details = {}
    if precision is not None:
        details = {"precision": precision}
    rows.append({"model":model,"item":f"{dim}-{len(rows)}","dimension":dim,
        "stack_version":"v1","item_sha256":"x","score":score,"status":"scored",
        "details":details,"cost_usd":cost,"cost_basis":"metered",
        "tokens_in":10,"tokens_out":10,"latency_s":lat,"handle":"h","ts":"t"})
# roster-math models (dim bug-fix)
for s in (1.0,1.0,1.0): add("flat:strong","bug-fix",s)
for s in (0.0,0.0,0.0): add("flat:weak","bug-fix",s)
for s in (1.0,0.0):     add("flat:half","bug-fix",s)
# flat:none has ONLY a code-review row so it appears but has bug-fix n=0
add("flat:none","code-review",1.0,precision=1.0)
# roles models
for s in (1.0,1.0): add("role:verifier","bug-fix",s)
for s in (1.0,1.0): add("role:verifier","instruction-format",s)
for s in (1.0,1.0): add("role:reviewer","code-review",s,precision=1.0)
for s in (1.0,1.0): add("role:shotgun","code-review",s,precision=0.3)
for s in (1.0,1.0): add("lc:reader","long-context",s)
for s in (1.0,1.0): add("free:calib","bug-fix",s,cost=0.0)
with open(out,"w") as f:
    for r in rows: f.write(json.dumps(r)+"\n")
PY

"$COUNCIL/roster.py" --results "$WORK/results-roster.jsonl" \
  --priors-dir "$PRIORS" --pricing "$WORK/pricing.json" \
  --now "2026-07-25T00:00:00Z" --out-json "$WORK/roster.json" \
  --out-md "$WORK/roster.md" >/dev/null

# --- fixture results.jsonl (diversity) -------------------------------------
# Two models over 6 objective slots: E1,E2,E3 (exact), F1 (format), and
# planted-defects R1 with universe {d1,d2}. Hand-computed pair:
# a(both correct)=2, b(m1✓m2✗)=2, c=0, d(both wrong)=2 →
# n_common=6, agree=4/6=0.6667, phi=(2*2-2*0)/sqrt(4*2*2*4)=4/8=0.5,
# both_wrong=2/(2+0+2)=0.5, insufficient=false.
python3 - "$WORK/results-div.jsonl" <<'PY'
import json, sys
out = sys.argv[1]
rows = []
def add(model,item,dim,score,details=None):
    rows.append({"model":model,"item":item,"dimension":dim,"stack_version":"v1",
      "item_sha256":"x","score":score,"status":"scored","details":details or {},
      "cost_usd":0.0,"cost_basis":"exact","tokens_in":1,"tokens_out":1,
      "latency_s":1.0,"handle":"h","ts":"t"})
# m1: E1=1,E2=1,E3=0,F1=1, R1 -> d1 found (d2 missed)
add("div:m1","E1","long-context",1.0); add("div:m1","E2","long-context",1.0)
add("div:m1","E3","long-context",0.0); add("div:m1","F1","instruction-format",1.0)
add("div:m1","R1","code-review",0.5,{"defect_ids":["d1","d2"],"matched_defect_ids":["d1"]})
# m2: E1=1,E2=0,E3=0,F1=1, R1 -> none found
add("div:m2","E1","long-context",1.0); add("div:m2","E2","long-context",0.0)
add("div:m2","E3","long-context",0.0); add("div:m2","F1","instruction-format",1.0)
add("div:m2","R1","code-review",0.0,{"defect_ids":["d1","d2"],"matched_defect_ids":[]})
with open(out,"w") as f:
    for r in rows: f.write(json.dumps(r)+"\n")
PY

"$COUNCIL/diversity.py" --results "$WORK/results-div.jsonl" \
  --now "2026-07-25T00:00:00Z" --out "$WORK/diversity.json" >/dev/null

# --- fixture roster + diversity for cast -----------------------------------
cat > "$WORK/roster-cast.json" <<'JSON'
{"schema_version":1,"stack_version":"v1","source":"priors+audition",
 "generated_ts":"t","k":3,"models":[
  {"model":"cast:a","reachable":true,"free":false,"mean_cost_usd_per_item":0.01,
   "dimensions":{"code-review":{"posterior":0.80}}},
  {"model":"cast:b","reachable":true,"free":false,"mean_cost_usd_per_item":0.01,
   "dimensions":{"code-review":{"posterior":0.75}}},
  {"model":"cast:c","reachable":true,"free":false,"mean_cost_usd_per_item":0.01,
   "dimensions":{"code-review":{"posterior":0.70}}},
  {"model":"cast:d","reachable":true,"free":false,"mean_cost_usd_per_item":0.01,
   "dimensions":{"code-review":{"posterior":0.50}}},
  {"model":"cast:e","reachable":true,"free":false,"mean_cost_usd_per_item":0.01,
   "dimensions":{"code-review":{"posterior":0.40}}}]}
JSON
cat > "$WORK/diversity-cast.json" <<'JSON'
{"schema_version":1,"stack_version":"v1","generated_ts":"t","pairs":[
 {"a":"cast:a","b":"cast:b","n_common":9,"agree_rate":0.5,"phi":0.5,"both_wrong_rate":0.8,"insufficient":false},
 {"a":"cast:a","b":"cast:c","n_common":9,"agree_rate":0.5,"phi":0.1,"both_wrong_rate":0.2,"insufficient":false},
 {"a":"cast:a","b":"cast:d","n_common":9,"agree_rate":0.5,"phi":0.1,"both_wrong_rate":0.2,"insufficient":false},
 {"a":"cast:b","b":"cast:c","n_common":9,"agree_rate":0.5,"phi":0.1,"both_wrong_rate":0.2,"insufficient":false},
 {"a":"cast:c","b":"cast:d","n_common":9,"agree_rate":0.5,"phi":0.5,"both_wrong_rate":0.9,"insufficient":false}]}
JSON

"$COUNCIL/cast.py" --roster "$WORK/roster-cast.json" \
  --diversity "$WORK/diversity-cast.json" --dimension code-review --k 3 \
  --out "$WORK/cast.json" >/dev/null

# priors-only (skip-audition) roster from --models/--dims, no results at all
"$COUNCIL/roster.py" --priors-dir "$PRIORS" --pricing "$WORK/pricing.json" \
  --models "flat:strong,free:calib" --dims "bug-fix,code-review" \
  --now "2026-07-25T00:00:00Z" --out-json "$WORK/skip-roster.json" >/dev/null

# --- assertions ------------------------------------------------------------
python3 - "$WORK" <<'PY'
import json, math, sys
work = sys.argv[1]
passed = failed = 0
def check(name, cond):
    global passed, failed
    if cond:
        passed += 1
    else:
        failed += 1
        print(f"FAIL: {name}")
def close(a, b, tol=1e-4):
    if a is None or b is None:
        return a is b
    return abs(a-b) <= tol

roster = json.load(open(f"{work}/roster.json"))
models = {m["model"]: m for m in roster["models"]}

def dim(model, d):
    return models[model]["dimensions"][d]

# roster shrinkage math (dim bug-fix)
s = dim("flat:strong","bug-fix")
check("strong n=3", s["n"]==3)
check("strong posterior 0.75", close(s["posterior"],0.75))
check("strong grade B", s["grade"]=="B")
check("strong not provisional", s["provisional"] is False)
check("strong ci95 0", close(s["ci95"],0.0))

w = dim("flat:weak","bug-fix")
check("weak posterior 0.25", close(w["posterior"],0.25))
check("weak grade D", w["grade"]=="D")

h = dim("flat:half","bug-fix")
check("half n=2", h["n"]==2)
check("half posterior 0.5", close(h["posterior"],0.5))
check("half grade C", h["grade"]=="C")
check("half ci95 0.98", close(h["ci95"],0.98))
check("half provisional", h["provisional"] is True)

nb = dim("flat:none","bug-fix")
check("none bug-fix n=0", nb["n"]==0)
check("none bug-fix posterior=prior 0.5", close(nb["posterior"],0.5))
check("none bug-fix ci95 null", nb["ci95"] is None)
check("none bug-fix provisional", nb["provisional"] is True)

# roles
check("verifier roles", models["role:verifier"]["roles"]==["implementer","verifier"])
check("reviewer roles", models["role:reviewer"]["roles"]==["reviewer"])
check("shotgun benched (precision gate)", models["role:shotgun"]["roles"]==["benched"])
check("lc reader long-context role", "long-context" in models["lc:reader"]["roles"])
check("lc reader LC posterior 0.94", close(dim("lc:reader","long-context")["posterior"],0.94))
check("free:calib free flag", models["free:calib"]["free"] is True)
check("free:calib calibration role", "calibration" in models["free:calib"]["roles"])
check("free:calib bulk role", "bulk" in models["free:calib"]["roles"])
check("free:calib implementer role", "implementer" in models["free:calib"]["roles"])

# diversity
div = json.load(open(f"{work}/diversity.json"))
pair = next(p for p in div["pairs"] if {p["a"],p["b"]}=={"div:m1","div:m2"})
check("div n_common 6", pair["n_common"]==6)
check("div agree_rate 0.6667", close(pair["agree_rate"],0.6667))
check("div phi 0.5", close(pair["phi"],0.5))
check("div both_wrong_rate 0.5", close(pair["both_wrong_rate"],0.5))
check("div not insufficient", pair["insufficient"] is False)

# cast: baseline=a (0.80), then greedy -> c (decorrelated), then b
cast = json.load(open(f"{work}/cast.json"))
check("cast baseline a", cast["baseline_member"]=="cast:a")
check("cast order a,c,b", cast["cast"]==["cast:a","cast:c","cast:b"])
check("cast excludes e (grade<C)", "cast:e" not in cast["cast"])

# priors-only (skip) roster: n=0, posterior=prior, provisional, source=priors
skip = json.load(open(f"{work}/skip-roster.json"))
sm = {m["model"]: m for m in skip["models"]}
check("skip source is priors", skip["source"] == "priors")
check("skip flat:strong bug-fix n=0", sm["flat:strong"]["dimensions"]["bug-fix"]["n"] == 0)
check("skip flat:strong posterior=prior 0.5", close(sm["flat:strong"]["dimensions"]["bug-fix"]["posterior"], 0.5))
check("skip flat:strong provisional", sm["flat:strong"]["dimensions"]["bug-fix"]["provisional"] is True)
check("skip free:calib free flag", sm["free:calib"]["free"] is True)

print(f"=== Results: {passed} passed, {failed} failed ===")
sys.exit(1 if failed else 0)
PY
