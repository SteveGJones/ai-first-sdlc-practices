---
description: Inspect the project's council roster — grades, roles, provisional flags, cost, and the diversity map's most/least decorrelated model pairs.
argument-hint: "[rebuild]"
---

Show the project's current model-council roster. This is a read of
`.sdlc/model-council/`, not a new assessment — no adapter is called, no
tokens are spent, unless `rebuild` is given (still token-free, see step 3).

Arguments: `$ARGUMENTS` — optional literal `rebuild`.

Do this:

1. **No roster yet?** If `.sdlc/model-council/roster.json` doesn't exist,
   say so plainly and stop: point at
   `/sdlc-model-council:council-commission` (full onboarding: discover,
   characterize, audition, roster, policy) or
   `/sdlc-model-council:council-assess` (just the assessment) as the two
   ways to produce one. Don't fabricate a roster from priors here — that's
   what commission's `skip` audition choice is for.

2. **Roster exists — present it.** Show `.sdlc/model-council/roster.md`
   as-is (it already has the per-model table: grades, per-dimension
   posterior/n/ci95, roles, cost/item, p50 latency). Then read
   `.sdlc/model-council/diversity.json` and summarise its `pairs` array:
     - **Most decorrelated pair** — lowest `both_wrong_rate` among pairs
       where `insufficient` is false — this is the best casting complement.
     - **Most correlated pair** — highest `both_wrong_rate` (or any pair
       marked `insufficient`, which `cast.py` treats as maximally
       correlated by design — call these out separately, they're a data gap
       not a diversity finding).
   Reference the `council-policy` skill if the user asks what any of this
   means for routing — role assignment and casting rules live there, not in
   this command.

3. **`rebuild`** — re-derive the roster and diversity map from the existing
   `.sdlc/model-council/results.jsonl` without dispatching any model. This is
   for after a manual edit to `results.jsonl`, a pricing refresh, or a
   priors update — cheap and token-free because it only re-scores rows
   already on disk. Run:
   ```
   ${CLAUDE_PLUGIN_ROOT}/scripts/council/roster.py \
     --results .sdlc/model-council/results.jsonl \
     --priors-dir ${CLAUDE_PLUGIN_ROOT}/scripts/council/priors \
     --pricing ${CLAUDE_PLUGIN_ROOT}/scripts/council/pricing.json \
     --out-json .sdlc/model-council/roster.json \
     --out-md .sdlc/model-council/roster.md

   ${CLAUDE_PLUGIN_ROOT}/scripts/council/diversity.py \
     --results .sdlc/model-council/results.jsonl \
     --stack ${CLAUDE_PLUGIN_ROOT}/assessment/stack/v1/stack.json \
     --out .sdlc/model-council/diversity.json
   ```
   Then present the rebuilt roster per step 2. If
   `.sdlc/model-council/results.jsonl` doesn't exist either, there's nothing
   to rebuild from — say so and point at `council-assess`/`council-commission`
   instead.

4. **Staleness check.** Compare the roster's `generated_ts`
   (`.sdlc/model-council/roster.json`) against the timestamps in
   `.sdlc/model-council/assessment-log.jsonl` — if any log entry's `ts` is
   newer than `roster.json`'s `generated_ts`, the on-disk roster predates
   the latest assessment run. Flag this plainly and suggest `rebuild` (if
   `results.jsonl` already reflects the newer run) or a fresh
   `/sdlc-model-council:council-assess` (if it doesn't).
