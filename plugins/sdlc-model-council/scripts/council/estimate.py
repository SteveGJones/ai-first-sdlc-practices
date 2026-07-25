#!/usr/bin/env python3
"""estimate.py -- token-free pre-dispatch cost estimator for the
model-council assessment harness ("never-surprise-spend" gate).

Authoritative shape: docs/superpowers/specs/2026-07-25-sdlc-model-council-design.md
S2.4/S6; pinned in the stage-2 implementation contract S7/S8.

Usage:
    estimate.py --pricing p.json --stack s.json --models m1,m2 --dims d1,d2 \
        [--k N] [--family-map addr1=fam1,addr2=fam2,...]

For each requested model x in-scope item (items whose top-level "dimension"
field in stack.json is one of --dims), the estimated cost is:

    est_cost = (item.est_prompt_tokens * input_rate
                + item.est_output_tokens * output_rate) / 1e6 * k

using the RESOLVED family's rates from --pricing (contract S8 shape:
{"families":{<family>:{"input_per_mtok":F,"output_per_mtok":F,
"free":bool}}}). `k` (default 1) scales for fan-out -- e.g. a play or
audition wave that runs the same item k times against the same model.

Family resolution, per model address:
  1. --family-map override, if the address is a key in it (must also name a
     family present in --pricing; otherwise treated as unresolved).
  2. Else a case-insensitive substring match, in EITHER direction, between
     the model address and each pricing family key (first match in the
     pricing file's own key order wins -- deterministic).
  3. No match -> family "unknown" (or whatever "unknown" maps to in
     --pricing, typically 0-rated); est_usd for that model is 0.0 and it is
     flagged so the caller can see the estimate is not to be trusted, per
     contract S7 ("unknown -> 0 flagged").

This tool is entirely token-free: it never calls extdel.sh, never dispatches
a model, and consumes zero real usage. It reads only stack.json/item.json/
pricing.json.

Prints a readable per-model table to STDERR (for human/operator review
before a live run) and a JSON summary to STDOUT:
    {"per_model": {"<addr>": {"items": N, "est_usd": F, "family": "<fam>"|null,
                               "flagged": bool}, ...},
     "total_usd": F, "k": N}

Zero third-party dependencies (Python 3 stdlib only).
"""
import argparse
import json
import os
import sys


def _split_csv(value):
    return [v.strip() for v in value.split(",") if v.strip()]


def parse_family_map(value):
    """Parse "addr1=fam1,addr2=fam2" into {addr: fam}. Raises ValueError
    with a clear message on malformed entries (missing '=')."""
    result = {}
    if not value:
        return result
    for pair in _split_csv(value):
        if "=" not in pair:
            raise ValueError(
                "--family-map entries must be addr=family, got: %r" % pair
            )
        key, _, fam = pair.partition("=")
        result[key.strip()] = fam.strip()
    return result


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_item_tokens(stack_path, item_path):
    """Read <dir-of-stack.json>/<item_path>/item.json and return
    (est_prompt_tokens, est_output_tokens). Defensive: a missing or
    unparseable item.json yields (0, 0) rather than crashing the estimate
    (a broken item is a stack-authoring bug caught by
    test-council-stack-lint.sh, not something this tool should die on)."""
    stack_dir = os.path.dirname(os.path.abspath(stack_path))
    item_json_path = os.path.join(stack_dir, item_path, "item.json")
    try:
        meta = load_json(item_json_path)
    except (OSError, json.JSONDecodeError):
        return 0, 0
    return meta.get("est_prompt_tokens", 0), meta.get("est_output_tokens", 0)


def resolve_family(address, families, family_map):
    """Resolve a pricing family for `address`. Returns (family_name_or_None,
    used_override_bool). See the module docstring's "Family resolution"
    section for the precedence rules."""
    if address in family_map:
        mapped = family_map[address]
        return (mapped if mapped in families else None), True

    addr_lower = address.lower()
    for family in families:
        fam_lower = family.lower()
        if fam_lower in addr_lower or addr_lower in fam_lower:
            return family, False
    return None, False


def rates_for(family, families):
    if not family or family not in families:
        return 0.0, 0.0
    rates = families[family]
    return rates.get("input_per_mtok", 0.0), rates.get("output_per_mtok", 0.0)


def build_estimate(pricing, stack, stack_path, models, dims, k, family_map):
    families = pricing.get("families", {})
    dims_set = set(dims)
    items = [it for it in stack.get("items", []) if it.get("dimension") in dims_set]
    item_tokens = [
        (it, load_item_tokens(stack_path, it["path"])) for it in items
    ]

    per_model = {}
    total_usd = 0.0
    table_rows = []

    for model in models:
        family, _ = resolve_family(model, families, family_map)
        input_rate, output_rate = rates_for(family, families)
        flagged = family is None

        est_usd = 0.0
        for _item, (prompt_tok, output_tok) in item_tokens:
            single = (prompt_tok * input_rate + output_tok * output_rate) / 1e6
            est_usd += single * k

        per_model[model] = {
            "items": len(item_tokens),
            "est_usd": round(est_usd, 6),
            "family": family,
            "flagged": flagged,
        }
        total_usd += est_usd
        table_rows.append((model, family or "unknown", len(item_tokens), est_usd, flagged))

    return per_model, round(total_usd, 6), table_rows


def print_table(table_rows, k, total_usd):
    print("estimate.py -- token-free cost estimate (k=%d)" % k, file=sys.stderr)
    print(
        "%-40s %-22s %8s %12s %s" % ("model", "family", "items", "est_usd", "flag"),
        file=sys.stderr,
    )
    for model, family, n_items, est_usd, flagged in table_rows:
        flag_str = "UNKNOWN-FAMILY" if flagged else ""
        print(
            "%-40s %-22s %8d %12.6f %s" % (model, family, n_items, est_usd, flag_str),
            file=sys.stderr,
        )
    print("total_usd: %.6f" % total_usd, file=sys.stderr)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Token-free pre-dispatch cost estimator."
    )
    parser.add_argument("--pricing", required=True, help="path to pricing.json")
    parser.add_argument("--stack", required=True, help="path to stack.json")
    parser.add_argument(
        "--models", required=True, help="comma-separated model addresses"
    )
    parser.add_argument(
        "--dims", required=True, help="comma-separated dimensions to include"
    )
    parser.add_argument(
        "--k", type=int, default=1, help="fan-out multiplier (default 1)"
    )
    parser.add_argument(
        "--family-map",
        default="",
        help="comma-separated addr=family overrides",
    )
    args = parser.parse_args(argv)

    try:
        family_map = parse_family_map(args.family_map)
    except ValueError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2

    try:
        pricing = load_json(args.pricing)
    except (OSError, json.JSONDecodeError) as exc:
        print("error: could not read pricing %r: %s" % (args.pricing, exc), file=sys.stderr)
        return 2

    try:
        stack = load_json(args.stack)
    except (OSError, json.JSONDecodeError) as exc:
        print("error: could not read stack %r: %s" % (args.stack, exc), file=sys.stderr)
        return 2

    models = _split_csv(args.models)
    dims = _split_csv(args.dims)

    per_model, total_usd, table_rows = build_estimate(
        pricing, stack, args.stack, models, dims, args.k, family_map
    )

    print_table(table_rows, args.k, total_usd)

    summary = {"per_model": per_model, "total_usd": total_usd, "k": args.k}
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
