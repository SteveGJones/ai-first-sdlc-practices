#!/usr/bin/env python3
"""Diversity / correlation map over objective assessment items (design §3.2).

Builds a per-model binary outcome vector over the OBJECTIVE items, then for each
model pair computes agreement, the phi coefficient, and — the load-bearing
measure for decorrelated casting — ``both_wrong_rate`` = P(both wrong | ≥1
wrong): the shared-blind-spot rate. Fewer than 6 common slots is flagged
``insufficient`` and treated as maximally correlated by cast.py (pessimism).

Planted-defects items EXPAND per defect: each planted defect is one binary slot
(found / missed), so a review where two models miss the *same* defect registers
a shared blind spot. The defect universe per item comes from the stack's
``expected/defects.json`` (via ``--stack``), or from a row's
``details.defect_ids`` if present, or — last resort — the union of everyone's
``matched_defect_ids`` for that item.

    diversity.py --results R.jsonl [--stack stack.json] [--now ISO] [--out D.json]
"""
import argparse
import itertools
import json
import math
import os
import sys

OBSERVATION_STATUSES = {"scored", "contract-fail", "timeout"}
OBJECTIVE_DIMS = {"long-context", "instruction-format", "bug-fix",
                  "code-review", "code-gen", "refactor"}
PER_DEFECT_DIMS = {"code-review"}
INSUFFICIENT_MIN = 6


def _load_results(path):
    rows = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _binarize(dimension, score):
    if dimension == "long-context":
        return 1 if float(score) >= 1.0 else 0
    return 1 if float(score) >= 0.5 else 0


def _defect_universe(rows, stack_path):
    """Map item-id -> ordered list of defect ids for per-defect dims."""
    universe = {}
    # Preferred: explicit defect_ids carried on any row's details.
    for row in rows:
        ids = row.get("details", {}).get("defect_ids")
        if ids:
            universe.setdefault(row["item"], list(ids))
    # Authoritative: the stack's expected/defects.json.
    if stack_path and os.path.exists(stack_path):
        stack_dir = os.path.dirname(os.path.abspath(stack_path))
        with open(stack_path, encoding="utf-8") as handle:
            stack = json.load(handle)
        for item in stack.get("items", []):
            if item.get("dimension") not in PER_DEFECT_DIMS:
                continue
            defects_path = os.path.join(
                stack_dir, item["path"], "expected", "defects.json")
            if os.path.exists(defects_path):
                with open(defects_path, encoding="utf-8") as handle:
                    defects = json.load(handle)
                universe[item["id"]] = [d["id"] for d in defects]
    # Fallback: union of matched ids (loses all-missed defects; documented).
    for row in rows:
        if row["dimension"] in PER_DEFECT_DIMS and row["item"] not in universe:
            matched = set()
            for r in rows:
                if r["item"] == row["item"]:
                    matched.update(r.get("details", {}).get("matched_defect_ids", []))
            universe[row["item"]] = sorted(matched)
    return universe


def build_vectors(rows, stack_path=None):
    """model -> {slot_key: 0/1} over objective items (planted-defects expanded)."""
    universe = _defect_universe(rows, stack_path)
    vectors = {}
    for row in rows:
        if row.get("status") not in OBSERVATION_STATUSES:
            continue
        dim = row["dimension"]
        if dim not in OBJECTIVE_DIMS:
            continue
        model = row["model"]
        vec = vectors.setdefault(model, {})
        if dim in PER_DEFECT_DIMS:
            matched = set(row.get("details", {}).get("matched_defect_ids", []))
            for defect_id in universe.get(row["item"], []):
                vec[f"{row['item']}#{defect_id}"] = 1 if defect_id in matched else 0
        else:
            vec[row["item"]] = _binarize(dim, row["score"])
    return vectors


def _pair_stats(vec_a, vec_b):
    common = sorted(set(vec_a) & set(vec_b))
    n = len(common)
    a = b = c = d = 0  # both-correct, a-correct/b-wrong, a-wrong/b-correct, both-wrong
    agree = 0
    for slot in common:
        oa, ob = vec_a[slot], vec_b[slot]
        if oa == ob:
            agree += 1
        if oa == 1 and ob == 1:
            a += 1
        elif oa == 1 and ob == 0:
            b += 1
        elif oa == 0 and ob == 1:
            c += 1
        else:
            d += 1
    agree_rate = round(agree / n, 4) if n else 0.0
    denom = math.sqrt((a + b) * (c + d) * (a + c) * (b + d))
    phi = round((a * d - b * c) / denom, 4) if denom else 0.0
    at_least_one_wrong = b + c + d
    both_wrong_rate = round(d / at_least_one_wrong, 4) if at_least_one_wrong else 0.0
    return {
        "n_common": n,
        "agree_rate": agree_rate,
        "phi": phi,
        "both_wrong_rate": both_wrong_rate,
        "insufficient": n < INSUFFICIENT_MIN,
    }


def build_diversity(rows, stack_path=None, now="1970-01-01T00:00:00Z"):
    vectors = build_vectors(rows, stack_path)
    pairs = []
    for addr_a, addr_b in itertools.combinations(sorted(vectors), 2):
        stats = _pair_stats(vectors[addr_a], vectors[addr_b])
        stats.update({"a": addr_a, "b": addr_b})
        pairs.append(stats)
    return {
        "schema_version": 1,
        "stack_version": rows[0]["stack_version"] if rows else "v1",
        "generated_ts": now,
        "pairs": pairs,
    }


def _main(argv):
    parser = argparse.ArgumentParser(description="Build the diversity map")
    parser.add_argument("--results", required=True)
    parser.add_argument("--stack")
    parser.add_argument("--now", default="1970-01-01T00:00:00Z")
    parser.add_argument("--out")
    args = parser.parse_args(argv)

    rows = _load_results(args.results)
    diversity = build_diversity(rows, stack_path=args.stack, now=args.now)
    payload = json.dumps(diversity, indent=2, sort_keys=True)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(payload + "\n")
    print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
