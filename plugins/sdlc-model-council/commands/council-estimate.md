---
description: Token-free pre-dispatch cost estimate for a council assessment — per-model cost table and total, no models called.
argument-hint: "models=a,b,... dims=d1,d2 [k=3]"
---

Estimate what a council assessment would cost, without spending a single
token. This is a dry run over `pricing.json` and the shipped stack — no
`extdel.sh` handle is created, no adapter is called.

Arguments: `$ARGUMENTS` — parse `models=` (comma-separated model addresses,
required), `dims=` (comma-separated dimensions, required), optional `k=`
(fan-out multiplier per item, default 1).

Do this:

1. Run:
   ```
   ${CLAUDE_PLUGIN_ROOT}/scripts/council/estimate.py \
     --pricing ${CLAUDE_PLUGIN_ROOT}/scripts/council/pricing.json \
     --stack ${CLAUDE_PLUGIN_ROOT}/assessment/stack/v1/stack.json \
     --priors-dir ${CLAUDE_PLUGIN_ROOT}/scripts/council/priors \
     --models <models> --dims <dims> [--k <k>]
   ```
   The per-model cost table prints to stderr; a JSON summary
   (`{"per_model": …, "total_usd": …}`) prints to stdout. Capture both.

2. **Present the table as-is** — one row per model, then the total. Any
   model resolving to a `free` pricing family (e.g. `opencode-free-tier`)
   shows `$0.00` — call that out explicitly so the user doesn't mistake it
   for a missing price.

3. If a model address doesn't resolve to a known pricing family, `estimate.py`
   falls back to the zero-rated `unknown` family. Flag this plainly: an
   `unknown`-family estimate is "no cost data," not "no cost" — don't let it
   read as free.

4. Close with: this is an estimate only, nothing was spent, and a real
   (paid) assessment run needs `/sdlc-model-council:council-assess` with an
   explicit `budget-usd=`.

Do not call `assess.sh`, `extdel.sh`, or any adapter from this command —
estimation only.
