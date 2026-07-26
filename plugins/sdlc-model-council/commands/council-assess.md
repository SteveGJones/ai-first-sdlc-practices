---
description: Run the standardized problem stack across models under a budget cap — free calibration wave first, then paid waves, then a roster + diversity map.
argument-hint: "models=a,b,... dims=d1,d2 [budget-usd=N] [--estimate] [--resume run-dir=DIR]"
---

Run (or resume) a council assessment: the shipped problem stack goes to each
named model, scored, and turned into a roster card + diversity map. This
wraps `assess.sh` — the choreography, not a new engine.

Arguments: `$ARGUMENTS` — parse `models=` (comma-separated model addresses,
required), `dims=` (comma-separated dimensions, required), optional
`budget-usd=` (a dollar cap — see step 2), `--estimate` (stop after the
estimate, spend nothing), `--resume run-dir=DIR` (continue an earlier run,
re-running only missing/`skipped:budget` pairs).

Do this:

1. **It always estimates first, token-free.** Run:
   ```
   ${CLAUDE_PLUGIN_ROOT}/scripts/council/assess.sh \
     --stack ${CLAUDE_PLUGIN_ROOT}/assessment/stack/v1/stack.json \
     --priors-dir ${CLAUDE_PLUGIN_ROOT}/scripts/council/priors \
     --pricing ${CLAUDE_PLUGIN_ROOT}/scripts/council/pricing.json \
     --models <models> --dims <dims> \
     [--budget-usd <budget-usd>] [--estimate] \
     [--resume --run-dir <run-dir>]
   ```
   `assess.sh` prints the per-model estimate table before touching any
   adapter. **Echo that table to the user before anything paid happens** —
   this is the never-surprise-spend contract, not optional politeness.

2. **`--estimate` stops there.** If the caller passed `--estimate`, the
   script exits after the estimate table with no tokens spent — report the
   table and total, and stop; do not proceed to the steps below.

3. **A live run over any paid model requires `budget-usd=`.** If the fleet
   named in `models=` includes anything outside the free family
   (`opencode-free-tier`) and no `budget-usd=` was given, `assess.sh` itself
   refuses (`fleet contains paid models; a live run requires --budget-usd`)
   — don't try to work around that by inventing a number; tell the user the
   command needs `budget-usd=` and stop. Free-only fleets run at $0 with no
   budget flag needed.

4. **Free calibration runs first, automatically.** Wave-0 dispatches only
   free models over the full item set (cost $0) to validate items/scorers
   and refine the paid-wave estimate before any paid token is spent — this
   is inside `assess.sh`, nothing to do here except let it run.

5. **Paid waves run at ≤5 concurrent handles**, hard-stopping the instant
   spend reaches `budget-usd`; anything still pending at that point is
   marked `skipped:budget` and is safe to pick up later with `--resume`.

6. **On completion**, `assess.sh` prints
   `[assess] Council spend: $X (est $Y) across N models` as its last log
   line, followed by the run directory path. The run dir now contains
   `results.jsonl`, `roster.json`, `roster.md`, `diversity.json`, and
   `assessment-log.jsonl`.

7. **Promote the run's roster to the project roster.** Copy the three
   artifacts from the run dir into `.sdlc/model-council/` (create the
   directory if it doesn't exist):
   ```
   mkdir -p .sdlc/model-council
   cp <run-dir>/roster.json .sdlc/model-council/roster.json
   cp <run-dir>/roster.md .sdlc/model-council/roster.md
   cp <run-dir>/diversity.json .sdlc/model-council/diversity.json
   ```
   Also append the run dir's `assessment-log.jsonl` line(s) onto
   `.sdlc/model-council/assessment-log.jsonl` (create if absent) — this is
   the greppable spend history, not just the latest snapshot.

8. **Report**: the final spend line verbatim, then a short roster summary —
   grades and roles per model from `roster.md`, flagging anything
   `provisional` (n=0 or wide CI). If this project has never been
   commissioned (no `.sdlc/model-council/commission.json`), mention that
   `/sdlc-model-council:council-commission` wraps this same flow with
   repo-characterization and policy seeding, in case that's what the user
   actually wanted.

**Resuming:** `--resume run-dir=DIR` maps to `assess.sh --resume --run-dir
DIR` — it keeps every terminal row already scored (scored/contract-fail/
timeout) and re-runs only what's missing or was cut short by the budget
hard-stop. Same promotion step (7) applies once it completes.
