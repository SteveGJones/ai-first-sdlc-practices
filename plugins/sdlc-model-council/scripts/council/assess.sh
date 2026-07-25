#!/usr/bin/env bash
# assess.sh — run/resume the standardized problem stack across N models under a
# budget cap, entirely as choreography ABOVE the unchanged adapter engine
# (design §2.4). Every external-model call is `extdel.sh start|status|stop`
# --posture read-only; this script never touches spawn/session mechanics. It
# schedules model×item pairs, runs a FREE wave-0 calibration first, then paid
# waves at ≤5 concurrent handles with a mid-run budget hard-stop (resumable),
# scores each answer with the stdlib scorer ABI, and emits results.jsonl plus a
# roster + diversity map.
#
# Bash 3.2 safe (matches extdel.sh): indexed arrays only where needed; the
# active-handle pool is tracked as a space-separated string + per-handle sidecar
# files so empty-array expansion under `set -u` is never an issue.
#
# Run from the repo root (where ./tmp lives) — extdel.sh keys its state dir off
# $(pwd), and this script resolves handle dirs the same way.
set -u

THIS_DIR="$(cd "$(dirname "$0")" && pwd -P)"          # scripts/council
COUNCIL="$THIS_DIR"
EXTDEL_DEFAULT="$(cd "$THIS_DIR/.." && pwd -P)/extdel.sh"

# ---- defaults ----
STACK=""; PRIORS=""; PRICING=""; MODELS=""; DIMS=""
BUDGET=""; ESTIMATE=0; RESUME=0; RUN_DIR=""; POSTURE="read-only"
MAX_CONC=5; NOW=""; EXTDEL="$EXTDEL_DEFAULT"; K=1
NO_REACH=0; POLL_WAIT=1

die() { echo "assess.sh: $1" >&2; exit 1; }

while [ $# -gt 0 ]; do
  case "$1" in
    --stack) STACK="$2"; shift 2 ;;
    --priors-dir) PRIORS="$2"; shift 2 ;;
    --pricing) PRICING="$2"; shift 2 ;;
    --models) MODELS="$2"; shift 2 ;;
    --dims) DIMS="$2"; shift 2 ;;
    --budget-usd) BUDGET="$2"; shift 2 ;;
    --estimate) ESTIMATE=1; shift ;;
    --resume) RESUME=1; shift ;;
    --run-dir) RUN_DIR="$2"; shift 2 ;;
    --posture) POSTURE="$2"; shift 2 ;;
    --max-concurrent) MAX_CONC="$2"; shift 2 ;;
    --k) K="$2"; shift 2 ;;
    --now) NOW="$2"; shift 2 ;;
    --extdel) EXTDEL="$2"; shift 2 ;;
    --no-reachability-check) NO_REACH=1; shift ;;
    --poll-wait-s) POLL_WAIT="$2"; shift 2 ;;
    *) die "unknown option: $1" ;;
  esac
done

[ -n "$STACK" ] || die "--stack is required"
[ -n "$PRIORS" ] || die "--priors-dir is required"
[ -n "$PRICING" ] || die "--pricing is required"
[ -n "$MODELS" ] || die "--models is required"
[ -n "$DIMS" ] || die "--dims is required"
[ -x "$EXTDEL" ] || die "extdel.sh not executable at $EXTDEL"

RUN_CWD="$(pwd -P)"
BASE_DIR="$RUN_CWD/tmp/model-council"
NOW_TS="${NOW:-$(date -u +%Y-%m-%dT%H:%M:%SZ)}"

# ---------------------------------------------------------------------------
# Run dir
# ---------------------------------------------------------------------------
if [ "$RESUME" -eq 1 ]; then
  [ -n "$RUN_DIR" ] || die "--resume requires --run-dir"
  [ -d "$RUN_DIR" ] || die "resume run-dir does not exist: $RUN_DIR"
else
  if [ -z "$RUN_DIR" ]; then
    mkdir -p "$BASE_DIR"
    RUN_DIR="$(mktemp -d "$BASE_DIR/assess-XXXXXX")"
  else
    mkdir -p "$RUN_DIR"
  fi
fi
RESULTS="$RUN_DIR/results.jsonl"
PLAN="$RUN_DIR/plan.json"
mkdir -p "$RUN_DIR/prompts" "$RUN_DIR/score" "$RUN_DIR/active"
: > "$RUN_DIR/active.reap" 2>/dev/null || true
rm -f "$RUN_DIR/active/"*.pair "$RUN_DIR/active/"*.t0 2>/dev/null || true

log() { echo "[assess] $*"; }

# ---------------------------------------------------------------------------
# Item manifest: item -> path,dimension,scorer_type,answer_contract,timeout,sha
# ---------------------------------------------------------------------------
MANIFEST="$RUN_DIR/item-manifest.tsv"
python3 - "$STACK" > "$MANIFEST" <<'PY'
import json, os, sys
stack_path = sys.argv[1]
stack_dir = os.path.dirname(os.path.abspath(stack_path))
with open(stack_path, encoding="utf-8") as fh:
    stack = json.load(fh)
for it in stack.get("items", []):
    item_dir = os.path.join(stack_dir, it["path"])
    with open(os.path.join(item_dir, "item.json"), encoding="utf-8") as fh:
        meta = json.load(fh)
    print("\t".join([
        it["id"], item_dir, it.get("dimension", meta.get("dimension", "")),
        meta.get("scorer", {}).get("type", ""),
        meta.get("answer_contract", "text"),
        str(meta.get("timeout_s", 120)),
        it.get("sha256", ""),
    ]))
PY
STACK_VERSION="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1])).get("stack_version","v1"))' "$STACK")"

manifest_field() { # manifest_field <item> <col 2..7>
  awk -F'\t' -v id="$1" -v c="$2" '$1==id{print $c; exit}' "$MANIFEST"
}

# ---------------------------------------------------------------------------
# Fleet resolution: model -> adapter, model-id, effort, free(0/1)
# ---------------------------------------------------------------------------
FLEET="$RUN_DIR/fleet.tsv"
python3 - "$PRIORS" "$PRICING" "$MODELS" "$COUNCIL" > "$FLEET" <<'PY'
import json, os, re, sys
priors_dir, pricing_path, models_csv, council = sys.argv[1:5]
sys.path.insert(0, council)
import priors as P
fams = P.load_priors(priors_dir)
with open(pricing_path, encoding="utf-8") as fh:
    pricing = json.load(fh)
GRAMMAR = re.compile(r"^([a-z][a-z0-9]*):([A-Za-z0-9./_-]+)(?:@(low|medium|high))?$")
for addr in [m for m in models_csv.split(",") if m]:
    m = GRAMMAR.match(addr)
    if not m:
        sys.stderr.write(f"assess.sh: bad model address: {addr}\n")
        sys.exit(2)
    adapter, model_id, effort = m.group(1), m.group(2), m.group(3) or ""
    fam = P.resolve_family(addr, families=fams)
    ref = fams.get(fam, {}).get("pricing_ref", fam)
    free = bool(pricing.get("families", {}).get(ref, {}).get("free", False))
    print("\t".join([addr, adapter, model_id, effort, "1" if free else "0"]))
PY
[ -s "$FLEET" ] || die "fleet resolution failed"

fleet_field() { awk -F'\t' -v a="$1" -v c="$2" '$1==a{print $c; exit}' "$FLEET"; }

# ---------------------------------------------------------------------------
# Reachability (best-effort; design §2.4 step 1)
# ---------------------------------------------------------------------------
UNREACHABLE=" "
if [ "$NO_REACH" -eq 0 ]; then
  LB="$("$EXTDEL" list-backends --json 2>/dev/null || true)"
  if [ -n "$LB" ]; then
    for ad in $(awk -F'\t' '{print $2}' "$FLEET" | sort -u); do
      ok="$(printf '%s' "$LB" | python3 -c 'import json,sys
try: data=json.load(sys.stdin)
except Exception: print("1"); sys.exit()
ad=sys.argv[1]
for row in data:
    d=row.get("descriptor",row)
    if d.get("id")==ad:
        det=row.get("detect",row.get("installed",row.get("detected",True)))
        print("1" if (det or det is None) else "0"); break
else: print("0")' "$ad" 2>/dev/null || echo 1)"
      [ "$ok" = "0" ] && UNREACHABLE="$UNREACHABLE$ad "
    done
  fi
fi
is_unreachable() { case "$UNREACHABLE" in *" $1 "*) return 0 ;; *) return 1 ;; esac; }

# ---------------------------------------------------------------------------
# Schedule (design §2.4 step 2) — plan.json of model×item pairs
# ---------------------------------------------------------------------------
"$COUNCIL/schedule.py" --stack "$STACK" --models "$MODELS" --dims "$DIMS" > "$PLAN" \
  || die "schedule.py failed"

# Expand plan into a pending TSV: model \t item \t dimension \t timeout \t sha
ALLPAIRS="$RUN_DIR/pairs.tsv"
python3 - "$PLAN" > "$ALLPAIRS" <<'PY'
import json, sys
plan = json.load(open(sys.argv[1], encoding="utf-8"))
for p in plan.get("pairs", []):
    print("\t".join([p["model"], p["item"], p["dimension"],
                     str(p.get("timeout_s", 120)), p.get("item_sha256", "")]))
PY

# ---------------------------------------------------------------------------
# Estimate gate (design §2.4 step 3)
# ---------------------------------------------------------------------------
log "estimate:"
"$COUNCIL/estimate.py" --pricing "$PRICING" --stack "$STACK" --models "$MODELS" \
  --dims "$DIMS" --k "$K" --priors-dir "$PRIORS" \
  > "$RUN_DIR/estimate.json" 2> "$RUN_DIR/estimate.table" || true
cat "$RUN_DIR/estimate.table" >&2 || true
EST_TOTAL="$(python3 -c 'import json,sys
try: print(json.load(open(sys.argv[1])).get("total_usd",0.0))
except Exception: print(0.0)' "$RUN_DIR/estimate.json")"
if [ "$ESTIMATE" -eq 1 ]; then
  log "estimate-only: est total \$$EST_TOTAL (no tokens spent)"
  exit 0
fi

# A paid dispatch requires an explicit budget (design §6 rule 1: no surprise spend).
# awk -F'\t' (not `read`, whose whitespace IFS collapses the empty effort field
# and shifts the free column) reads column 5 = free flag; "0" => a paid model.
HAVE_PAID="$(awk -F'\t' 'BEGIN{p=0} $5=="0"{p=1} END{print p}' "$FLEET")"
if [ "$HAVE_PAID" = "1" ] && [ -z "$BUDGET" ]; then
  die "fleet contains paid models; a live run requires --budget-usd (no default spend)"
fi

# ---------------------------------------------------------------------------
# Resume: keep terminal rows (scored/contract-fail/timeout/error), drop
# skipped:budget so those pairs re-run (design §2.4 --resume + step 5).
# ---------------------------------------------------------------------------
DONE_KEYS="$RUN_DIR/done-keys.txt"
: > "$DONE_KEYS"
if [ "$RESUME" -eq 1 ] && [ -f "$RESULTS" ]; then
  python3 - "$RESULTS" "$DONE_KEYS" <<'PY'
import json, sys
res, keys = sys.argv[1], sys.argv[2]
kept = []
done = set()
for line in open(res, encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    row = json.loads(line)
    if row.get("status") == "skipped:budget":
        continue          # re-run on resume
    kept.append(line)
    done.add(row["model"] + "\t" + row["item"])
open(res, "w", encoding="utf-8").write("\n".join(kept) + ("\n" if kept else ""))
open(keys, "w", encoding="utf-8").write("\n".join(sorted(done)) + ("\n" if done else ""))
PY
else
  : > "$RESULTS"
fi
is_done() { grep -qxF "$1	$2" "$DONE_KEYS" 2>/dev/null; }

# ---------------------------------------------------------------------------
# Prompt composition (item prompt.md + shown inputs)
# ---------------------------------------------------------------------------
compose_prompt() { # compose_prompt <item> <item_dir> -> path
  local item="$1" item_dir="$2"
  local out="$RUN_DIR/prompts/$item.txt"
  {
    cat "$item_dir/prompt.md" 2>/dev/null
    if [ -d "$item_dir/inputs" ]; then
      printf '\n\n--- INPUTS ---\n'
      for f in "$item_dir/inputs"/*; do
        [ -f "$f" ] || continue
        printf '\n### %s\n' "$(basename "$f")"
        cat "$f"
      done
    fi
  } > "$out"
  printf '%s' "$out"
}

# ---------------------------------------------------------------------------
# Row emission + scoring
# ---------------------------------------------------------------------------
SPENT="0"
emit_row() {
  # emit_row model item dim sha status score details_json cost basis tin tout lat handle
  python3 - "$@" >> "$RESULTS" <<'PY'
import json, sys
(model, item, dim, sha, status, score, details, cost, basis, tin, tout, lat,
 handle, stack_version, ts) = sys.argv[1:16]
print(json.dumps({
    "model": model, "item": item, "dimension": dim, "stack_version": stack_version,
    "item_sha256": sha, "score": float(score), "status": status,
    "details": json.loads(details) if details else {},
    "cost_usd": float(cost), "cost_basis": basis,
    "tokens_in": int(tin), "tokens_out": int(tout), "latency_s": float(lat),
    "handle": handle, "ts": ts,
}, separators=(",", ":")))
PY
}

process_terminal() { # process_terminal <handle> <pairline> <engine_status> <t0>
  local handle="$1" pairline="$2" est="$3" t0="$4"
  local model item dim timeout sha
  model="$(printf '%s' "$pairline" | cut -f1)"
  item="$(printf '%s' "$pairline" | cut -f2)"
  dim="$(printf '%s' "$pairline" | cut -f3)"
  sha="$(printf '%s' "$pairline" | cut -f5)"
  local item_dir scorer_type
  item_dir="$(manifest_field "$item" 2)"
  scorer_type="$(manifest_field "$item" 4)"
  local handle_dir="$BASE_DIR/$handle"
  local answer="$handle_dir/turn-001.last-message.txt"
  local now_epoch lat
  now_epoch="$(date +%s)"; lat=$((now_epoch - t0))

  local score status details cost basis tin tout
  cost=0; basis="estimated"; tin=0; tout=0

  # Usage (cost) — best effort from the handle's events.
  if [ -d "$handle_dir" ]; then
    local u
    u="$("$COUNCIL/usage.py" "$handle_dir" --pricing "$PRICING" 2>/dev/null || echo '{}')"
    cost="$(printf '%s' "$u" | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d.get("cost_usd",0))' 2>/dev/null || echo 0)"
    basis="$(printf '%s' "$u" | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d.get("cost_basis","estimated"))' 2>/dev/null || echo estimated)"
    tin="$(printf '%s' "$u" | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d.get("tokens_in",0))' 2>/dev/null || echo 0)"
    tout="$(printf '%s' "$u" | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d.get("tokens_out",0))' 2>/dev/null || echo 0)"
  fi

  case "$est" in
    TIMEOUT) status="timeout"; score=0; details='{}' ;;
    ERROR)   status="error";   score=0; details='{"engine":"ERROR"}' ;;
    *)
      # SUCCESS / NO_OUTPUT → run the scorer over the answer file.
      local wd="$RUN_DIR/score/$handle"
      mkdir -p "$wd"
      if [ -n "$scorer_type" ] && [ -f "$COUNCIL/score/$scorer_type.py" ]; then
        "$COUNCIL/score/$scorer_type.py" "$item_dir" "$answer" "$wd" >/dev/null 2>&1 || true
        if [ -f "$wd/score.json" ]; then
          score="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["score"])' "$wd/score.json" 2>/dev/null || echo 0)"
          status="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["status"])' "$wd/score.json" 2>/dev/null || echo error)"
          details="$(python3 -c 'import json,sys;print(json.dumps(json.load(open(sys.argv[1])).get("details",{})))' "$wd/score.json" 2>/dev/null || echo '{}')"
        else
          score=0; status="error"; details='{"scorer":"no-output"}'
        fi
      else
        score=0; status="error"; details='{"scorer":"unknown-type"}'
      fi
      ;;
  esac

  emit_row "$model" "$item" "$dim" "$sha" "$status" "$score" "$details" \
           "$cost" "$basis" "$tin" "$tout" "$lat" "$handle" "$STACK_VERSION" "$NOW_TS"
  SPENT="$(python3 -c 'import sys;print(round(float(sys.argv[1])+float(sys.argv[2]),8))' "$SPENT" "$cost" 2>/dev/null || echo "$SPENT")"
}

emit_skipped() { # emit_skipped <pairline>
  local model item dim sha
  model="$(printf '%s' "$1" | cut -f1)"; item="$(printf '%s' "$1" | cut -f2)"
  dim="$(printf '%s' "$1" | cut -f3)"; sha="$(printf '%s' "$1" | cut -f5)"
  emit_row "$model" "$item" "$dim" "$sha" "skipped:budget" 0 '{}' 0 "estimated" 0 0 0 "" "$STACK_VERSION" "$NOW_TS"
}

start_pair() { # start_pair <pairline> -> echoes handle (or empty on failure)
  local pairline="$1"
  local model item timeout adapter model_id effort
  model="$(printf '%s' "$pairline" | cut -f1)"
  item="$(printf '%s' "$pairline" | cut -f2)"
  timeout="$(printf '%s' "$pairline" | cut -f4)"
  adapter="$(fleet_field "$model" 2)"; model_id="$(fleet_field "$model" 3)"
  effort="$(fleet_field "$model" 4)"
  local item_dir pfile
  item_dir="$(manifest_field "$item" 2)"
  pfile="$(compose_prompt "$item" "$item_dir")"
  local margs=""
  [ "$model_id" != "default" ] && margs="--model $model_id"
  [ -n "$effort" ] && margs="$margs --effort $effort"
  local out
  out="$("$EXTDEL" start --cli "$adapter" $margs --posture "$POSTURE" \
        --prompt-file "$pfile" --timeout-s "$timeout" 2>/dev/null || true)"
  printf '%s\n' "$out" | grep -m1 '^- Handle:' | sed -E 's/^- Handle:[[:space:]]*//'
}

# ---------------------------------------------------------------------------
# Concurrency pool driver over a pending TSV
# ---------------------------------------------------------------------------
ACTIVE=""   # space-separated handles
count_active() { set -- $ACTIVE; echo $#; }

run_wave() { # run_wave <pending-tsv> <budget-enforced 0|1>
  local pending="$1" enforce="$2"
  local budget_hit=0
  # dispatch/poll loop
  while :; do
    # top up the pool
    while [ "$(count_active)" -lt "$MAX_CONC" ] && [ -s "$pending" ] && [ "$budget_hit" -eq 0 ]; do
      local pairline
      pairline="$(head -n1 "$pending")"
      sed -i.bak '1d' "$pending" 2>/dev/null && rm -f "$pending.bak"
      [ -n "$pairline" ] || continue
      local pm pi
      pm="$(printf '%s' "$pairline" | cut -f1)"; pi="$(printf '%s' "$pairline" | cut -f2)"
      if is_done "$pm" "$pi"; then continue; fi
      local h
      h="$(start_pair "$pairline")"
      if [ -z "$h" ]; then
        # dispatch failed → record an error row, don't wedge the pool
        process_terminal "nohandle-$pi" "$pairline" "ERROR" "$(date +%s)"
        continue
      fi
      printf '%s' "$pairline" > "$RUN_DIR/active/$h.pair"
      date +%s > "$RUN_DIR/active/$h.t0"
      ACTIVE="$ACTIVE $h"
    done

    [ "$(count_active)" -eq 0 ] && break

    # poll active handles one pass
    local newactive="" progressed=0
    for h in $ACTIVE; do
      local sout st
      sout="$("$EXTDEL" status "$h" --wait-s "$POLL_WAIT" 2>/dev/null || true)"
      st="$(printf '%s' "$sout" | grep -m1 '^- Status:' | sed -E 's/^- Status:[[:space:]]*//' | awk '{print $1}')"
      case "$st" in
        RUNNING|"")
          newactive="$newactive $h" ;;
        *)
          local pairline t0
          pairline="$(cat "$RUN_DIR/active/$h.pair" 2>/dev/null)"
          t0="$(cat "$RUN_DIR/active/$h.t0" 2>/dev/null || date +%s)"
          process_terminal "$h" "$pairline" "$st" "$t0"
          "$EXTDEL" stop "$h" >/dev/null 2>&1 || true
          rm -f "$RUN_DIR/active/$h.pair" "$RUN_DIR/active/$h.t0"
          progressed=1
          # budget hard-stop (design §2.4 step 5)
          if [ "$enforce" -eq 1 ] && [ -n "$BUDGET" ]; then
            local over
            over="$(python3 -c 'import sys;print("1" if float(sys.argv[1])>=float(sys.argv[2]) else "0")' "$SPENT" "$BUDGET" 2>/dev/null || echo 0)"
            [ "$over" = "1" ] && budget_hit=1
          fi
          ;;
      esac
    done
    ACTIVE="$newactive"

    if [ "$budget_hit" -eq 1 ]; then
      log "budget hard-stop: spent \$$SPENT >= \$$BUDGET — cancelling pending paid pairs"
      while [ -s "$pending" ]; do
        local pl; pl="$(head -n1 "$pending")"; sed -i.bak '1d' "$pending" 2>/dev/null && rm -f "$pending.bak"
        [ -n "$pl" ] || continue
        local sm si; sm="$(printf '%s' "$pl" | cut -f1)"; si="$(printf '%s' "$pl" | cut -f2)"
        is_done "$sm" "$si" && continue
        emit_skipped "$pl"
      done
    fi
  done
}

# ---------------------------------------------------------------------------
# Build wave pending files: wave-0 = FREE models, then paid.
# ---------------------------------------------------------------------------
FREE_PENDING="$RUN_DIR/pending-free.tsv"; : > "$FREE_PENDING"
PAID_PENDING="$RUN_DIR/pending-paid.tsv"; : > "$PAID_PENDING"
while IFS='	' read -r model item dim timeout sha; do
  [ -n "$model" ] || continue
  if is_unreachable "$(fleet_field "$model" 2)"; then
    emit_row "$model" "$item" "$dim" "$sha" "error" 0 '{"engine":"unreachable"}' 0 estimated 0 0 0 "" "$STACK_VERSION" "$NOW_TS"
    continue
  fi
  is_done "$model" "$item" && continue
  if [ "$(fleet_field "$model" 5)" = "1" ]; then
    printf '%s\t%s\t%s\t%s\t%s\n' "$model" "$item" "$dim" "$timeout" "$sha" >> "$FREE_PENDING"
  else
    printf '%s\t%s\t%s\t%s\t%s\n' "$model" "$item" "$dim" "$timeout" "$sha" >> "$PAID_PENDING"
  fi
done < "$ALLPAIRS"

log "wave-0 (free calibration): $(wc -l < "$FREE_PENDING" | tr -d ' ') pairs"
run_wave "$FREE_PENDING" 0
log "paid waves: $(wc -l < "$PAID_PENDING" | tr -d ' ') pairs (budget \$${BUDGET:-none})"
run_wave "$PAID_PENDING" 1

# ---------------------------------------------------------------------------
# Roster + diversity (design §2.4 step 6)
# ---------------------------------------------------------------------------
if [ -s "$RESULTS" ]; then
  "$COUNCIL/roster.py" --results "$RESULTS" --priors-dir "$PRIORS" \
    --pricing "$PRICING" --now "$NOW_TS" \
    --out-json "$RUN_DIR/roster.json" --out-md "$RUN_DIR/roster.md" >/dev/null \
    || log "roster.py failed"
  "$COUNCIL/diversity.py" --results "$RESULTS" --stack "$STACK" \
    --now "$NOW_TS" --out "$RUN_DIR/diversity.json" >/dev/null \
    || log "diversity.py failed"
fi

ROWS="$(wc -l < "$RESULTS" | tr -d ' ')"
printf '{"ts":"%s","run_dir":"%s","stack_version":"%s","rows":%s,"spent_usd":%s,"est_usd":%s,"budget_usd":"%s"}\n' \
  "$NOW_TS" "$RUN_DIR" "$STACK_VERSION" "$ROWS" "$SPENT" "$EST_TOTAL" "${BUDGET:-}" \
  >> "$RUN_DIR/assessment-log.jsonl"

log "done: $ROWS rows -> $RESULTS"
log "Council spend: \$$SPENT (est \$$EST_TOTAL) across $(echo "$MODELS" | tr ',' '\n' | grep -c .) models"
echo "$RUN_DIR"
