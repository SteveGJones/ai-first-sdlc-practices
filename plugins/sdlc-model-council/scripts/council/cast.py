#!/usr/bin/env python3
"""Cast a decorrelated panel from the roster + diversity map (design §3.2, §6).

Greedy: seed with the best posterior on the task dimension (the *baseline
member*, kept for the measurability spine — design §10), then repeatedly add the
model maximising ``posterior − 0.5·max_both_wrong_rate_vs_current_cast`` so each
addition is strong AND decorrelated from those already chosen. A missing or
``insufficient`` pair contributes both_wrong_rate 1.0 (pessimism). Under a tight
budget a free/cheap member is guaranteed. Stdlib only.

    cast.py --roster R.json --diversity D.json --dimension code-review --k 3
            [--budget-usd X]
"""
import argparse
import json
import sys

GRADE_C = 0.45
CHEAP_COST_THRESHOLD = 0.002


def _load(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _posterior(model_entry, dimension):
    return float(model_entry.get("dimensions", {}).get(dimension, {})
                 .get("posterior", 0.0))


def _is_free_or_cheap(model_entry):
    return bool(model_entry.get("free")) or \
        float(model_entry.get("mean_cost_usd_per_item", 0.0)) <= CHEAP_COST_THRESHOLD


def _bw_lookup(diversity):
    """(addr,addr) -> both_wrong_rate; insufficient -> 1.0. Symmetric."""
    table = {}
    for pair in diversity.get("pairs", []):
        rate = 1.0 if pair.get("insufficient") else float(pair["both_wrong_rate"])
        table[(pair["a"], pair["b"])] = rate
        table[(pair["b"], pair["a"])] = rate
    return table


def _bw(table, m, cast):
    """max both_wrong_rate of m against the current cast; 1.0 if any pair unknown."""
    if not cast:
        return 0.0
    return max(table.get((m, c), 1.0) for c in cast)


def cast_panel(roster, diversity, dimension, k, budget_usd=None):
    entries = {m["model"]: m for m in roster["models"]}
    bw_table = _bw_lookup(diversity)

    pool = []
    for addr, entry in entries.items():
        if not entry.get("reachable", True):
            continue
        if _posterior(entry, dimension) < GRADE_C:
            continue
        if budget_usd is not None and k > 0:
            per_member = budget_usd / k
            if float(entry.get("mean_cost_usd_per_item", 0.0)) > per_member:
                continue
        pool.append(addr)

    rationale = []
    if not pool:
        return {"dimension": dimension, "k": k, "baseline_member": None,
                "cast": [], "rationale": [], "note": "no cost-feasible model at grade>=C"}

    # 1. baseline = best posterior (ties -> lexicographic address).
    baseline = max(sorted(pool),
                   key=lambda a: _posterior(entries[a], dimension))
    cast = [baseline]
    rationale.append({"model": baseline, "posterior": _posterior(entries[baseline], dimension),
                      "max_both_wrong_vs_prior_cast": 0.0, "reason": "baseline"})

    # 2. greedily add decorrelated-yet-strong members.
    while len(cast) < k:
        remaining = [a for a in pool if a not in cast]
        if not remaining:
            break

        def marginal(addr):
            return _posterior(entries[addr], dimension) - 0.5 * _bw(bw_table, addr, cast)

        pick = max(sorted(remaining), key=marginal)
        rationale.append({
            "model": pick,
            "posterior": _posterior(entries[pick], dimension),
            "max_both_wrong_vs_prior_cast": round(_bw(bw_table, pick, cast), 4),
        })
        cast.append(pick)

    # 3. tight-budget free/cheap guarantee.
    if k >= 3 and budget_usd is not None and \
            not any(_is_free_or_cheap(entries[a]) for a in cast):
        free_candidates = [a for a in pool if a not in cast and _is_free_or_cheap(entries[a])]
        if free_candidates:
            best_free = max(sorted(free_candidates),
                            key=lambda a: _posterior(entries[a], dimension))
            # swap out the lowest-marginal NON-baseline member.
            non_baseline = [a for a in cast if a != baseline]
            if non_baseline:
                drop = min(sorted(non_baseline),
                           key=lambda a: _posterior(entries[a], dimension))
                cast = [best_free if a == drop else a for a in cast]
                rationale.append({"model": best_free, "posterior": _posterior(entries[best_free], dimension),
                                  "reason": f"free/cheap swap for {drop} (tight budget)"})

    return {
        "dimension": dimension,
        "k": k,
        "baseline_member": baseline,
        "cast": cast,
        "rationale": rationale,
    }


def _main(argv):
    parser = argparse.ArgumentParser(description="Cast a decorrelated panel")
    parser.add_argument("--roster", required=True)
    parser.add_argument("--diversity", required=True)
    parser.add_argument("--dimension", required=True)
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument("--budget-usd", type=float)
    parser.add_argument("--out")
    args = parser.parse_args(argv)

    roster = _load(args.roster)
    diversity = _load(args.diversity)
    result = cast_panel(roster, diversity, args.dimension, args.k,
                        budget_usd=args.budget_usd)
    payload = json.dumps(result, indent=2, sort_keys=True)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(payload + "\n")
    print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
