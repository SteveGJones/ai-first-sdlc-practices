#!/usr/bin/env python3
"""usage.py -- summarize actual token/cost usage for one extdel.sh handle
directory, by parsing its per-turn artifacts. Zero engine edits: this is a
read-only parser over files the substrate (extdel.sh + turn-supervisor.pl +
adapters) already writes, never a participant in dispatch.

Authoritative shape: docs/superpowers/specs/2026-07-25-sdlc-model-council-design.md
S2.4/S6; pinned in the stage-2 implementation contract S7.

Usage:
    usage.py <handle-dir> [--pricing pricing.json] [--family <family-name>]

Adapter is detected from <handle-dir>/meta.json's "cli" field. Per-adapter
summation, driven by the real event shapes observed in
tests/fixtures/mock-bin/{opencode,codex,agy} and documented in
docs/superpowers/specs/2026-07-23-external-agent-delegation-design.md:

  opencode -- every turn-*.events.jsonl line of type "step_finish" carries
    an exact {"part":{"tokens":N,"cost":X}}. Summed directly: cost is exact
    dollars already; the split between input/output tokens is not
    represented in this event shape, so the total goes to tokens_out
    (tokens_in stays 0) per the pinned contract. basis = "exact".

  codex -- `codex exec --json` emits a JSONL event stream that is documented
    to carry token counts, but neither this repo's mock codex CLI (see
    tests/fixtures/mock-bin/codex: session_meta/turn_started/
    agent_message_delta/turn_complete/error only) nor any fixture available
    to this build actually emits one. This parser recognizes the token-field
    shapes documented in the delegation design doc (a "usage" sub-object
    with input_tokens/output_tokens or prompt_tokens/completion_tokens, or
    flat input_tokens/output_tokens on the event) wherever they appear, so a
    real event stream is picked up automatically; an event stream carrying
    none of these fields (the current mock's reality) sums to zero rather
    than raising. basis is always "metered" for codex regardless of whether
    any token field was actually found -- that is the TRUTH-SOURCE this
    adapter is entitled to claim, distinct from opencode's "exact" (cost is
    already in dollars) and agy's "estimated" (no usage events at all).

  agy -- emits no usage events whatsoever. tokens_out is estimated from the
    character count of the concatenated turn-*.last-message.txt files
    (chars // 4, a standard rough token/char ratio); tokens_in likewise from
    turn-*.prompt.txt files if present, else 0. basis = "estimated".

  unknown/missing meta.json -- defensive fallback: zero tokens, zero cost,
  basis "estimated" (the most conservative label available when the
  adapter itself cannot be identified).

Cost, when the adapter itself does not already report it verbatim
(opencode), is computed from --pricing (a pricing.json shaped per contract
S8: {"families":{<family>:{"input_per_mtok":F,"output_per_mtok":F,
"free":bool}}}) as (tokens_in*input_rate + tokens_out*output_rate) / 1e6.
Family is resolved via --family if given (must name a family present in the
pricing file), else by a case-insensitive substring match, in EITHER
direction, between meta.json's "model" field and each pricing family key
(first match in the pricing file's own key order wins). No pricing file, or
no resolvable family, yields cost_usd 0.0 -- never a crash, never a
fabricated number.

Prints one JSON object to stdout:
    {"tokens_in": N, "tokens_out": N, "cost_usd": F, "cost_basis": "..."}

Zero third-party dependencies (Python 3 stdlib only).
"""
import argparse
import glob
import json
import os
import sys


def load_meta(handle_dir):
    """Read <handle_dir>/meta.json. Returns {} (never raises) if the file
    is missing or unparseable -- a handle dir with no readable meta.json
    carries no adapter identity, which the caller treats as the "unknown"
    case."""
    meta_path = os.path.join(handle_dir, "meta.json")
    try:
        with open(meta_path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}


def load_pricing(pricing_path):
    """Read a pricing.json file. Returns {} (with a stderr warning) if the
    path is missing/unparseable rather than aborting the whole summary --
    usage.py must still print zero-cost-but-real-tokens output when pricing
    data is simply unavailable."""
    if not pricing_path:
        return {}
    try:
        with open(pricing_path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(
            "warning: could not read pricing file %r: %s" % (pricing_path, exc),
            file=sys.stderr,
        )
        return {}


def resolve_family(hint, families):
    """Resolve a pricing family name from `families` (a dict keyed by
    family name) via a case-insensitive substring match against `hint`, in
    EITHER direction: a family key found inside the hint, or the hint found
    inside a family key. Families are tried in the dict's own (insertion)
    order, making the pricing file's own key ordering the deterministic
    tie-break. Returns None if `hint` is falsy or nothing matches."""
    if not hint:
        return None
    hint_lower = hint.lower()
    for family in families:
        fam_lower = family.lower()
        if fam_lower in hint_lower or hint_lower in fam_lower:
            return family
    return None


def priced_cost(tokens_in, tokens_out, family, families):
    """(tokens_in*input_rate + tokens_out*output_rate) / 1e6, or 0.0 if the
    family is unresolved or absent from `families` -- an unpriceable model
    never fabricates a cost."""
    if not family or family not in families:
        return 0.0
    rates = families[family]
    input_rate = rates.get("input_per_mtok", 0.0)
    output_rate = rates.get("output_per_mtok", 0.0)
    return (tokens_in * input_rate + tokens_out * output_rate) / 1e6


def _iter_events(handle_dir):
    """Yield parsed JSON objects from every turn-*.events.jsonl file in
    handle_dir, in turn order. Unparseable lines are silently skipped
    (a corrupt or partial line from a killed/timed-out turn must never
    crash usage accounting)."""
    for events_path in sorted(
        glob.glob(os.path.join(handle_dir, "turn-*.events.jsonl"))
    ):
        with open(events_path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue


def sum_opencode(handle_dir):
    """opencode: sum step_finish.part.{tokens,cost}. tokens go entirely to
    tokens_out (the split is not represented in this event shape); cost is
    exact dollars, summed directly. Returns (tokens_in, tokens_out,
    cost_usd)."""
    tokens_out = 0
    cost = 0.0
    for obj in _iter_events(handle_dir):
        if obj.get("type") != "step_finish":
            continue
        part = obj.get("part") or {}
        tokens_out += int(part.get("tokens", 0) or 0)
        cost += float(part.get("cost", 0.0) or 0.0)
    return 0, tokens_out, cost


def _extract_codex_tokens(obj):
    """Best-effort, defensive extraction of (input_tokens, output_tokens)
    from one parsed codex --json event. See the module docstring's "codex"
    section for why this must be tolerant rather than pinned to one exact
    shape."""
    usage = obj.get("usage")
    if isinstance(usage, dict):
        in_tok = usage.get("input_tokens", usage.get("prompt_tokens"))
        out_tok = usage.get("output_tokens", usage.get("completion_tokens"))
        if in_tok is not None or out_tok is not None:
            return int(in_tok or 0), int(out_tok or 0)
    in_tok = obj.get("input_tokens")
    out_tok = obj.get("output_tokens")
    if in_tok is not None or out_tok is not None:
        return int(in_tok or 0), int(out_tok or 0)
    return 0, 0


def sum_codex(handle_dir):
    """codex: sum whatever token fields (see _extract_codex_tokens) appear
    across every turn-*.events.jsonl event. Returns (tokens_in,
    tokens_out); zero for both when no token-field shape is present in the
    event stream (today's mock reality)."""
    tokens_in = 0
    tokens_out = 0
    for obj in _iter_events(handle_dir):
        in_tok, out_tok = _extract_codex_tokens(obj)
        tokens_in += in_tok
        tokens_out += out_tok
    return tokens_in, tokens_out


def sum_agy(handle_dir):
    """agy: no usage events exist at all. Estimate tokens_out from the
    character count of every turn-*.last-message.txt (chars // 4); estimate
    tokens_in the same way from turn-*.prompt.txt files if any exist, else
    0. Returns (tokens_in, tokens_out)."""
    tokens_out = 0
    for msg_path in sorted(
        glob.glob(os.path.join(handle_dir, "turn-*.last-message.txt"))
    ):
        with open(msg_path, "r", encoding="utf-8") as fh:
            tokens_out += len(fh.read()) // 4

    tokens_in = 0
    for prompt_path in sorted(
        glob.glob(os.path.join(handle_dir, "turn-*.prompt.txt"))
    ):
        with open(prompt_path, "r", encoding="utf-8") as fh:
            tokens_in += len(fh.read()) // 4

    return tokens_in, tokens_out


def summarize(handle_dir, pricing, family_override, priors_families=None):
    meta = load_meta(handle_dir)
    cli = meta.get("cli")
    families = pricing.get("families", {})

    if family_override:
        family = family_override if family_override in families else None
    elif priors_families:
        # Resolve family from the full model ADDRESS (adapter:model) via the
        # priors matches map — the roster/assess layer's resolution. A bare
        # meta.model like "default" never substring-matches "openai-gpt5", so
        # the old path priced live codex/agy at $0 (defeating the budget cap).
        import priors as priors_mod
        model = meta.get("model") or ""
        address = ("%s:%s" % (cli, model)) if cli else model
        fam = priors_mod.resolve_family(address, families=priors_families)
        pricing_ref = priors_families.get(fam, {}).get("pricing_ref", fam)
        family = (pricing_ref if pricing_ref in families
                  else resolve_family(meta.get("model"), families))
    else:
        family = resolve_family(meta.get("model"), families)

    if cli == "opencode":
        tokens_in, tokens_out, cost = sum_opencode(handle_dir)
        basis = "exact"
    elif cli == "codex":
        tokens_in, tokens_out = sum_codex(handle_dir)
        cost = priced_cost(tokens_in, tokens_out, family, families)
        basis = "metered"
    elif cli == "agy":
        tokens_in, tokens_out = sum_agy(handle_dir)
        cost = priced_cost(tokens_in, tokens_out, family, families)
        basis = "estimated"
    else:
        # Unknown/missing meta.json -- no adapter identity, so no evidence
        # of any kind. Zero tokens and cost, "estimated" as the most
        # conservative available label.
        tokens_in, tokens_out, cost = 0, 0, 0.0
        basis = "estimated"

    return {
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_usd": round(cost, 6),
        "cost_basis": basis,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Summarize actual token/cost usage for one extdel.sh handle dir."
    )
    parser.add_argument("handle_dir", help="path to the ./tmp/model-council/<handle> dir")
    parser.add_argument(
        "--pricing", default=None, help="path to pricing.json (optional)"
    )
    parser.add_argument(
        "--family",
        default=None,
        help="override family resolution (must name a family in --pricing)",
    )
    parser.add_argument(
        "--priors-dir",
        default=None,
        help="priors dir; resolve family from the adapter:model address via the "
             "priors matches map (same as the roster/assess layer)",
    )
    args = parser.parse_args(argv)

    pricing = load_pricing(args.pricing)
    priors_families = None
    if args.priors_dir:
        import priors as priors_mod
        priors_families = priors_mod.load_priors(args.priors_dir)
    result = summarize(args.handle_dir, pricing, args.family, priors_families)
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
