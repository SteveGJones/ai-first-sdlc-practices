#!/usr/bin/env python3
"""Roster builder — turns an assessment ``results.jsonl`` into a roster card.

Implements the small-sample-honest scoring of design §3.1 and the fixed role
rules of §3.3/§4.2, pinned in the stage-2 contract §4. Stdlib only; all emitted
floats rounded to 4 (scores) / 6 (cost) / 3 (latency) decimals for byte-stable
golden tests. Timestamps are injectable via ``--now`` so tests are deterministic.

An *observation* is a result row whose status is one of scored / contract-fail /
timeout (all three are genuine observations of the model's ability; the latter
two contribute score 0.0). error and skipped:budget rows are ignored.

    roster.py --results R.jsonl --priors-dir DIR [--pricing pricing.json]
              [--now ISO] [--out-json roster.json] [--out-md roster.md]
"""
import argparse
import json
import math
import statistics
import sys

# priors.py is a sibling module; the interpreter puts this script's own
# directory on sys.path[0] for direct CLI invocation, so a plain import
# resolves it without any sys.path manipulation.
import priors as priors_mod

K_PSEUDO = 3
OBSERVATION_STATUSES = {"scored", "contract-fail", "timeout"}
CI95_PROVISIONAL_WIDTH = 0.35
CHEAP_COST_THRESHOLD = 0.002
JUDGE_DIMS = {"reasoning", "architecture", "research"}
CORE_DIMS = {"bug-fix", "code-review", "long-context", "instruction-format"}

GRADE_A, GRADE_B, GRADE_C = 0.85, 0.65, 0.45


def _grade(posterior):
    if posterior >= GRADE_A:
        return "A"
    if posterior >= GRADE_B:
        return "B"
    if posterior >= GRADE_C:
        return "C"
    return "D"


def _load_results(path):
    rows = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _row_flags_disagreement(row):
    if "judge-disagreement" in row.get("flags", []):
        return True
    return bool(row.get("details", {}).get("judge_disagreement"))


def _dimension_stat(rows, address, dimension, families):
    """Compute the §4.1 stat block for one (model, dimension)."""
    scores = [float(r["score"]) for r in rows]
    n = len(scores)
    family, prior = priors_mod.prior_for_address(
        address, dimension, families=families)
    if n == 0:
        raw_mean = 0.0
        posterior = prior
        ci95 = None
    else:
        raw_mean = sum(scores) / n
        posterior = (n * raw_mean + K_PSEUDO * prior) / (n + K_PSEUDO)
        if n >= 2:
            sd = statistics.stdev(scores)
            ci95 = round(1.96 * sd / math.sqrt(n), 4)
        else:
            ci95 = None
    judge_scored = dimension in JUDGE_DIMS or any(
        r.get("details", {}).get("judge_scored") for r in rows)
    provisional = (ci95 is None) or (ci95 > CI95_PROVISIONAL_WIDTH) or any(
        _row_flags_disagreement(r) for r in rows)
    return {
        "n": n,
        "raw_mean": round(raw_mean, 4),
        "sd": (round(statistics.stdev(scores), 4) if n >= 2 else None),
        "ci95": ci95,
        "prior": round(prior, 4),
        "posterior": round(posterior, 4),
        "grade": _grade(posterior),
        "provisional": provisional,
        "judge_scored": judge_scored,
    }


def _review_precision(rows):
    """Mean of details.precision across code-review observation rows, or None."""
    precisions = [
        float(r["details"]["precision"]) for r in rows
        if isinstance(r.get("details"), dict) and "precision" in r["details"]
    ]
    if not precisions:
        return None
    return sum(precisions) / len(precisions)


def _roles(dims, review_precision, free, mean_cost, all_dims):
    """Fixed role rules (contract §4.2). Returns a sorted list of role names."""
    def post(dim):
        return dims.get(dim, {}).get("posterior", 0.0) if dim in dims else 0.0

    roles = []

    implementer = post("bug-fix") >= GRADE_B
    if "code-gen" in all_dims:
        implementer = implementer and post("code-gen") >= GRADE_B
    if implementer:
        roles.append("implementer")

    if post("code-review") >= GRADE_B and review_precision is not None \
            and review_precision >= 0.5:
        roles.append("reviewer")

    if post("bug-fix") >= GRADE_B and post("instruction-format") >= GRADE_B:
        roles.append("verifier")

    if post("long-context") >= GRADE_A:
        roles.append("long-context")

    core_ok = any(post(d) >= GRADE_C for d in CORE_DIMS if d in all_dims)
    if core_ok and (free or mean_cost <= CHEAP_COST_THRESHOLD):
        roles.append("bulk")

    if free:
        roles.append("calibration")

    return sorted(set(roles))


def build_roster(rows, families, pricing=None, now="1970-01-01T00:00:00Z",
                 extra_models=None, extra_dims=None):
    # extra_models / extra_dims let a skip-audition commission (design §5.2 step
    # 4) render a priors-only roster: models with no observation rows appear
    # with n=0 → posterior=prior, all provisional, across the requested dims.
    all_dims = sorted({r["dimension"] for r in rows} | set(extra_dims or []))
    by_model = {}
    for row in rows:
        if row.get("status") not in OBSERVATION_STATUSES:
            continue
        by_model.setdefault(row["model"], []).append(row)

    all_models = sorted(set(by_model) | set(extra_models or []))
    models_out = []
    for address in all_models:
        model_rows = by_model.get(address, [])
        family = priors_mod.resolve_family(address, families=families)
        fam_desc = families.get(family, {})
        pricing_ref = fam_desc.get("pricing_ref", family)
        free = False
        if pricing is not None:
            free = bool(
                pricing.get("families", {}).get(pricing_ref, {}).get("free", False))

        dims = {}
        for dimension in all_dims:
            dim_rows = [r for r in model_rows if r["dimension"] == dimension]
            dims[dimension] = _dimension_stat(
                dim_rows, address, dimension, families)

        costs = [float(r.get("cost_usd", 0.0)) for r in model_rows]
        latencies = [float(r.get("latency_s", 0.0)) for r in model_rows
                     if r.get("latency_s") is not None]
        mean_cost = round(sum(costs) / len(costs), 6) if costs else 0.0
        p50_latency = round(statistics.median(latencies), 3) if latencies else 0.0

        review_precision = _review_precision(
            [r for r in model_rows if r["dimension"] == "code-review"])
        roles = _roles(dims, review_precision, free, mean_cost, set(all_dims))

        flags = []
        if family == "unknown":
            flags.append("no-prior")

        models_out.append({
            "model": address,
            "family": family,
            "reachable": True,
            "pricing_ref": pricing_ref,
            "free": free,
            "dimensions": dims,
            "mean_cost_usd_per_item": mean_cost,
            "p50_latency_s": p50_latency,
            "roles": roles if roles else ["benched"],
            "flags": flags,
        })

    source = "priors+audition" if any(
        d["n"] > 0 for m in models_out for d in m["dimensions"].values()
    ) else "priors"
    return {
        "schema_version": 1,
        "stack_version": rows[0]["stack_version"] if rows else "v1",
        "source": source,
        "generated_ts": now,
        "k": K_PSEUDO,
        "models": models_out,
    }


def render_md(roster):
    lines = [
        "# Model council roster",
        "",
        f"- stack: `{roster['stack_version']}` · source: `{roster['source']}`"
        f" · k={roster['k']} · generated: {roster['generated_ts']}",
        "",
    ]
    dims = sorted({d for m in roster["models"] for d in m["dimensions"]})
    header = "| model | family | " + " | ".join(dims) + \
        " | cost/item | p50 lat | roles |"
    sep = "|" + "---|" * (len(dims) + 5)
    lines.append(header)
    lines.append(sep)
    for m in roster["models"]:
        cells = []
        for d in dims:
            stat = m["dimensions"].get(d, {})
            mark = "*" if stat.get("provisional") else ""
            cells.append(
                f"{stat.get('grade', '-')} {stat.get('posterior', 0):.2f}"
                f"(n{stat.get('n', 0)}){mark}")
        lines.append(
            f"| `{m['model']}` | {m['family']} | " + " | ".join(cells) +
            f" | {m['mean_cost_usd_per_item']} | {m['p50_latency_s']} |"
            f" {', '.join(m['roles'])} |")
    lines.append("")
    lines.append("_`*` = provisional (wide CI, n<2, or judge-disagreement)._")
    return "\n".join(lines) + "\n"


def _main(argv):
    parser = argparse.ArgumentParser(description="Build the council roster")
    parser.add_argument("--results",
                        help="results.jsonl; omit for a priors-only (skip "
                             "audition) roster built from --models + --dims")
    parser.add_argument("--priors-dir", required=True)
    parser.add_argument("--pricing")
    parser.add_argument("--now", default="1970-01-01T00:00:00Z")
    parser.add_argument("--models", default="",
                        help="comma-separated addresses to include even with "
                             "no observations (priors-only entries)")
    parser.add_argument("--dims", default="",
                        help="comma-separated dimensions to render for "
                             "priors-only models")
    parser.add_argument("--out-json")
    parser.add_argument("--out-md")
    args = parser.parse_args(argv)

    rows = _load_results(args.results) if args.results else []
    extra_models = [m for m in args.models.split(",") if m]
    extra_dims = [d for d in args.dims.split(",") if d]
    if not rows and not extra_models:
        parser.error("either --results or --models is required")
    families = priors_mod.load_priors(args.priors_dir)
    pricing = None
    if args.pricing:
        with open(args.pricing, encoding="utf-8") as handle:
            pricing = json.load(handle)

    roster = build_roster(rows, families, pricing=pricing, now=args.now,
                          extra_models=extra_models, extra_dims=extra_dims)
    payload = json.dumps(roster, indent=2, sort_keys=True)
    if args.out_json:
        with open(args.out_json, "w", encoding="utf-8") as handle:
            handle.write(payload + "\n")
    if args.out_md:
        with open(args.out_md, "w", encoding="utf-8") as handle:
            handle.write(render_md(roster))
    print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
