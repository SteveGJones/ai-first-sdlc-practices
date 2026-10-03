#!/usr/bin/env python3
"""schedule.py -- build a deterministic (model x item) dispatch plan for the
model-council assessment harness.

Authoritative shape: docs/superpowers/specs/2026-07-25-sdlc-model-council-design.md
S2.4/S6; pinned in the stage-2 implementation contract S7.

Usage:
    schedule.py --stack <stack.json> --models m1,m2 --dims d1,d2 \
        [--min-context-map addr1=tokens1,addr2=tokens2,...]

Reads the shipped stack.json (contract S10 shape:
{"schema_version","stack_version","items":[{"id","dimension","path","sha256"},
...]}) plus, for every item that survives the requested-dimension filter,
that item's own item.json (found at <dir-of-stack.json>/<item.path>/item.json)
to read "timeout_s" and "min_context_tokens" -- stack.json itself never
carries those two fields, only item.json does.

Queue order is fully deterministic: models outer loop (in the exact order
given on --models), items inner loop (in stack.json listing order, already
filtered to the requested dimensions). No sorting, no de-duplicating set()
that would scramble order -- the caller's input order IS the contract.

If --min-context-map is given, a pair is dropped when the item's
min_context_tokens exceeds the named model's context budget. A model named
in --models but absent from the map is treated the same as "no map at all"
for that model -- no context information available means no filtering
decision can be made, so the pair is kept. This is a deliberate
default-to-inclusion choice for missing data, distinct from an explicit
low-context entry (which does filter).

Prints one JSON object to stdout:
    {"pairs":[{"model","item","dimension","item_sha256","timeout_s"}, ...],
     "stack_version": "...", "n_pairs": N}

Zero third-party dependencies (Python 3 stdlib only).
"""
import argparse
import json
import os
import sys


def _split_csv(value):
    """Split a comma-separated CLI value into a list of non-empty, stripped
    tokens. Preserves input order and duplicates -- callers decide whether
    repeats matter (they don't here: a model repeated on --models simply
    gets scheduled against the item set twice, which is the caller's choice,
    not this tool's to silently collapse)."""
    return [v.strip() for v in value.split(",") if v.strip()]


def parse_min_context_map(value):
    """Parse "addr1=tokens1,addr2=tokens2" into {addr: int(tokens)}.

    Raises ValueError with a clear message on malformed entries (missing
    '=', non-integer token count) so the CLI can report a clean usage error
    rather than a stack trace.
    """
    result = {}
    if not value:
        return result
    for pair in _split_csv(value):
        if "=" not in pair:
            raise ValueError(
                "--min-context-map entries must be key=value, got: %r" % pair
            )
        key, _, raw_val = pair.partition("=")
        key = key.strip()
        raw_val = raw_val.strip()
        try:
            result[key] = int(raw_val)
        except ValueError:
            raise ValueError(
                "--min-context-map value for %r is not an integer: %r"
                % (key, raw_val)
            )
    return result


def load_stack(stack_path):
    """Load and return the parsed stack.json document."""
    with open(stack_path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_item_meta(stack_path, item_path):
    """Read <dir-of-stack.json>/<item_path>/item.json and return
    (timeout_s, min_context_tokens).

    Defensive by design: a missing or unparseable item.json never crashes
    scheduling. It falls back to (60, 0) -- a conservative default timeout
    and "no minimum context requirement" (so it is never context-filtered
    out, erring on the side of still scheduling it; a broken item.json is a
    stack-authoring bug that test-council-stack-lint.sh is responsible for
    catching, not this tool).
    """
    stack_dir = os.path.dirname(os.path.abspath(stack_path))
    item_json_path = os.path.join(stack_dir, item_path, "item.json")
    try:
        with open(item_json_path, "r", encoding="utf-8") as fh:
            meta = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return 60, 0
    timeout_s = meta.get("timeout_s", 60)
    min_context_tokens = meta.get("min_context_tokens", 0)
    return timeout_s, min_context_tokens


def build_plan(stack, stack_path, models, dims, context_map):
    """Return (pairs, stack_version) per the module docstring's ordering and
    filtering rules."""
    dims_set = set(dims)
    items = [it for it in stack.get("items", []) if it.get("dimension") in dims_set]

    # Item metadata (timeout_s, min_context_tokens) does not depend on the
    # model being scheduled -- read each item.json exactly once, not once
    # per model, even though the same item is scheduled against every model.
    item_metas = [
        (item, load_item_meta(stack_path, item["path"])) for item in items
    ]

    pairs = []
    for model in models:
        model_context = context_map.get(model)
        for item, (timeout_s, min_context_tokens) in item_metas:
            if model_context is not None and min_context_tokens > model_context:
                continue
            pairs.append(
                {
                    "model": model,
                    "item": item["id"],
                    "dimension": item["dimension"],
                    "item_sha256": item.get("sha256", ""),
                    "timeout_s": timeout_s,
                }
            )

    return pairs, stack.get("stack_version", "")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Build a deterministic model x item dispatch plan."
    )
    parser.add_argument("--stack", required=True, help="path to stack.json")
    parser.add_argument(
        "--models", required=True, help="comma-separated model addresses"
    )
    parser.add_argument(
        "--dims", required=True, help="comma-separated dimensions to include"
    )
    parser.add_argument(
        "--min-context-map",
        default="",
        help="comma-separated addr=tokens pairs; omit to skip context filtering",
    )
    args = parser.parse_args(argv)

    try:
        context_map = parse_min_context_map(args.min_context_map)
    except ValueError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2

    try:
        stack = load_stack(args.stack)
    except (OSError, json.JSONDecodeError) as exc:
        print("error: could not read stack %r: %s" % (args.stack, exc), file=sys.stderr)
        return 2

    models = _split_csv(args.models)
    dims = _split_csv(args.dims)

    pairs, stack_version = build_plan(stack, args.stack, models, dims, context_map)

    plan = {
        "pairs": pairs,
        "stack_version": stack_version,
        "n_pairs": len(pairs),
    }
    print(json.dumps(plan))
    return 0


if __name__ == "__main__":
    sys.exit(main())
