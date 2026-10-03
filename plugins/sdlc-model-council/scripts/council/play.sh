#!/usr/bin/env bash
# play.sh — deterministic, testable spine for the Diff+Synthesis fan-out play
# (design §4.1). The choreography above it lives in commands/council-run.md (the
# main thread dispatches one delegation-runner per cast member) and the
# synthesis itself is the council-judge agent; play.sh owns only the mechanical,
# reproducible parts so they can be unit-tested over canned result files:
#
#   setup         cast a decorrelated panel, assign BLIND labels (address
#                 stripped so the judge can't tell who's who), write manifest.json
#                 + task.md, and print the per-member dispatch table.
#   combine-check quorum + survivor check over the <label>.result.md files the
#                 runners wrote; build combine/blind-bundle.md for the judge.
#   unblind       map the judge's blind labels back to model addresses in the
#                 finished synthesis (provenance is restored, not laundered).
#
# The baseline_member (cast[0], the roster's best single model for the task) is
# recorded in the manifest so the synthesis can state a Baseline delta — the
# measurability spine (design §10). Bash 3.2 safe; Python 3 stdlib for JSON.
set -u

THIS_DIR="$(cd "$(dirname "$0")" && pwd -P)"
COUNCIL="$THIS_DIR"
die() { echo "play.sh: $1" >&2; exit 1; }

SUB="${1:-}"; shift 2>/dev/null || true

# ---------------------------------------------------------------------------
cmd_setup() {
  local dimension="" roster="" diversity="" k=3 task_file="" cast="" budget=""
  local now="1970-01-01T00:00:00Z" out=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --dimension) dimension="$2"; shift 2 ;;
      --roster) roster="$2"; shift 2 ;;
      --diversity) diversity="$2"; shift 2 ;;
      --k) k="$2"; shift 2 ;;
      --task-file) task_file="$2"; shift 2 ;;
      --cast) cast="$2"; shift 2 ;;
      --budget-usd) budget="$2"; shift 2 ;;
      --now) now="$2"; shift 2 ;;
      --out) out="$2"; shift 2 ;;
      *) die "setup: unknown option $1" ;;
    esac
  done
  [ -n "$dimension" ] || die "setup: --dimension required"
  [ -n "$task_file" ] || die "setup: --task-file required"
  [ -f "$task_file" ] || die "setup: task file not found: $task_file"

  local base="${PWD}/tmp/model-council"
  mkdir -p "$base"
  if [ -z "$out" ]; then
    out="$(mktemp -d "$base/play-diff-XXXXXX")"
  else
    mkdir -p "$out"
  fi
  mkdir -p "$out/combine"
  cp "$task_file" "$out/task.md"

  # Resolve the cast: pinned --cast wins, else cast.py against the roster.
  local cast_csv="$cast"
  local baseline=""
  if [ -z "$cast_csv" ]; then
    [ -n "$roster" ] && [ -f "$roster" ] || die "setup: --roster required unless --cast is pinned"
    [ -n "$diversity" ] && [ -f "$diversity" ] || die "setup: --diversity required unless --cast is pinned"
    local castout
    castout="$("$COUNCIL/cast.py" --roster "$roster" --diversity "$diversity" \
      --dimension "$dimension" --k "$k" ${budget:+--budget-usd "$budget"})" \
      || die "setup: cast.py failed"
    cast_csv="$(printf '%s' "$castout" | python3 -c 'import json,sys;d=json.load(sys.stdin);print(",".join(d["cast"]))')"
    baseline="$(printf '%s' "$castout" | python3 -c 'import json,sys;print(json.load(sys.stdin).get("baseline_member") or "")')"
  fi
  [ -n "$cast_csv" ] || die "setup: empty cast"
  [ -n "$baseline" ] || baseline="$(printf '%s' "$cast_csv" | cut -d, -f1)"

  # Blind labels: order the cast by sha256(model + seed) so the label carries
  # NO signal about posterior/rank, then A, B, C, ... — reproducible for tests.
  python3 - "$out/manifest.json" "$dimension" "$k" "$now" "$baseline" "$budget" "$cast_csv" <<'PY'
import hashlib, json, sys
manifest_path, dimension, k, now, baseline, budget, cast_csv = sys.argv[1:8]
cast = [m for m in cast_csv.split(",") if m]
order = sorted(cast, key=lambda m: hashlib.sha256((m + "|" + now).encode()).hexdigest())
labels = [chr(ord("A") + i) for i in range(len(order))]
members = [{"model": m, "label": labels[i]} for i, m in enumerate(order)]
label_of = {m["model"]: m["label"] for m in members}
manifest = {
    "play": "diff-synthesis", "dimension": dimension, "k": int(k), "ts": now,
    "baseline_member": baseline, "baseline_label": label_of.get(baseline),
    "budget_usd": budget or None,
    "members": members,
}
with open(manifest_path, "w", encoding="utf-8") as fh:
    json.dump(manifest, fh, indent=2, sort_keys=True)
    fh.write("\n")
# Dispatch table on stdout: label \t model \t result-file
for m in members:
    print("%s\t%s\t%s.result.md" % (m["label"], m["model"], m["label"]))
PY
  echo "PLAY_DIR=$out"
}

# ---------------------------------------------------------------------------
cmd_combine_check() {
  local play_dir="" quorum=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --play-dir) play_dir="$2"; shift 2 ;;
      --quorum) quorum="$2"; shift 2 ;;
      *) die "combine-check: unknown option $1" ;;
    esac
  done
  [ -n "$play_dir" ] || die "combine-check: --play-dir required"
  [ -f "$play_dir/manifest.json" ] || die "combine-check: no manifest in $play_dir"

  python3 - "$play_dir" "${quorum:-}" <<'PY'
import json, os, sys
play_dir, quorum_arg = sys.argv[1], sys.argv[2]
manifest = json.load(open(os.path.join(play_dir, "manifest.json"), encoding="utf-8"))
members = manifest["members"]
k = len(members)
quorum = int(quorum_arg) if quorum_arg else max(2, k // 2 + 1)

def nonblank(path):
    if not os.path.exists(path):
        return False
    with open(path, encoding="utf-8") as fh:
        return fh.read().strip() != ""

present, bundle = [], []
for m in members:
    rf = os.path.join(play_dir, m["label"] + ".result.md")
    ok = nonblank(rf)
    present.append({"label": m["label"], "present": ok})
    if ok:
        with open(rf, encoding="utf-8") as fh:
            body = fh.read().strip()
        # BLIND: the bundle references the source only as "Model <label>";
        # the model address never appears here (bias containment, §2.3).
        bundle.append("## Model %s\n\n%s\n" % (m["label"], body))

survivors = sum(1 for p in present if p["present"])
degraded = survivors < quorum
os.makedirs(os.path.join(play_dir, "combine"), exist_ok=True)
with open(os.path.join(play_dir, "combine", "blind-bundle.md"), "w", encoding="utf-8") as fh:
    fh.write("# Blind response bundle\n\n")
    fh.write("Task is in `task.md`. Each response below is from a distinct "
             "model shown only as an anonymous label.\n\n")
    fh.write("\n".join(bundle) if bundle else "_No responses survived._\n")

status = {
    "play": "diff-synthesis", "k": k, "survivors": survivors, "quorum": quorum,
    "degraded": degraded, "baseline_label": manifest.get("baseline_label"),
    "members": present,
    "verdict": "PLAY-DEGRADED" if degraded else "OK",
}
print(json.dumps(status, indent=2, sort_keys=True))
PY
}

# ---------------------------------------------------------------------------
cmd_unblind() {
  local play_dir="" infile=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --play-dir) play_dir="$2"; shift 2 ;;
      --in) infile="$2"; shift 2 ;;
      *) die "unblind: unknown option $1" ;;
    esac
  done
  [ -n "$play_dir" ] || die "unblind: --play-dir required"
  [ -n "$infile" ] && [ -f "$infile" ] || die "unblind: --in file required"
  python3 - "$play_dir" "$infile" <<'PY'
import json, os, re, sys
play_dir, infile = sys.argv[1], sys.argv[2]
manifest = json.load(open(os.path.join(play_dir, "manifest.json"), encoding="utf-8"))
text = open(infile, encoding="utf-8").read()
# Longest labels first is irrelevant (single chars), but replace the explicit
# "Model <label>" convention the judge is instructed to use, restoring the
# real model address as attribution (provenance, never laundering).
for m in manifest["members"]:
    text = re.sub(r"\bModel %s\b" % re.escape(m["label"]),
                  "`%s`" % m["model"], text)
sys.stdout.write(text)
PY
}

case "$SUB" in
  setup) cmd_setup "$@" ;;
  combine-check) cmd_combine_check "$@" ;;
  unblind) cmd_unblind "$@" ;;
  *) die "usage: play.sh {setup|combine-check|unblind} ..." ;;
esac
