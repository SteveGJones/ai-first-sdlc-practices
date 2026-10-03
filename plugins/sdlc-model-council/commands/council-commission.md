---
description: Onboard this project onto the model council — discover the reachable fleet, characterize the repo, audition at the chosen depth, then write the roster + policy + commission record.
argument-hint: "[audition=skip|calibrate|standard|full]"
---

Commission this project for `sdlc-model-council`: discover which models are
actually reachable, characterize what the repo needs, audition them at a
chosen depth, and write `.sdlc/model-council/{roster.json,roster.md,
diversity.json,policy.json,commission.json}`. Load the `council-policy`
skill now — every routing/play/posture decision below leans on it.

Arguments: `$ARGUMENTS` — optional `audition=skip|calibrate|standard|full`.
If omitted, this is a real decision with real cost implications (see step
3) — ask the user rather than guessing.

Do this:

## 0. Pre-flight re-commission check

If `.sdlc/model-council/commission.json` already exists, this project has
been commissioned before. Read it, show the prior `ts` and `audition`
level, and confirm with the user before continuing — re-commissioning
overwrites `roster.json`, `roster.md`, `diversity.json`, and `policy.json`
in place. If they only want a refresh (same fleet, new evidence), point at
`/sdlc-model-council:council-assess` or `/sdlc-model-council:council-roster
rebuild` instead, which don't touch policy.

## 1. Discover — token-free

```
${CLAUDE_PLUGIN_ROOT}/scripts/extdel.sh list-backends --json
```
gives you which backends (`codex`, `agy`, `opencode`, …) are registered,
installed, and authenticated. For every backend reported
`installed: yes` / authenticated, list its actual model ids directly
against the CLI (still token-free — a model listing, not a turn):
`agy models` for agy, `opencode models` for opencode (codex is addressed
as `codex:default@<effort>`, no separate model-listing call). Build the
full set of reachable `adapter:model[@effort]` addresses.

For each address, resolve its pricing family and free flag:
```
${CLAUDE_PLUGIN_ROOT}/scripts/council/priors.py resolve <address> \
  --priors-dir ${CLAUDE_PLUGIN_ROOT}/scripts/council/priors
```
then look up that family in `${CLAUDE_PLUGIN_ROOT}/scripts/council/pricing.json`
(`.families.<family>.free`). Present the discovered fleet as a table:
address, family, free y/n. This is the fleet snapshot that goes into
`commission.json` at the end — capture it now.

## 2. Characterize the repo

Do a lightweight scan, not a deep audit: `git ls-files` grouped by
extension for the language/task mix, rough repo size for blast-radius
sense. Then ask the user two things this scan can't infer: **budget per
day** (a dollar ceiling for council spend) and **latency tolerance**
(is a slow, thorough panel fine, or does this need to stay fast). Record
the answers — they seed `policy.json`'s guardrails in step 5.

## 3. Audition — pick a depth

Four choices, in increasing cost/evidence:

- **`skip`** — priors only, **$0, no dispatch at all**. Every discovered
  model gets a roster entry with `posterior == prior`, `n=0`, and
  `provisional: true` for every dimension — this is the honest "we haven't
  measured anything yet, here's our best guess" roster.
- **`calibrate`** — **free models only**, full stack (all dimensions in
  the shipped `stack.json`), **$0**. Maps to:
  ```
  /sdlc-model-council:council-assess models=<free-addrs> dims=<all-stack-dims>
  ```
  (no `budget-usd=` needed — an all-free fleet runs at $0).
- **`standard`** — calibrate's free evidence plus the reachable **paid**
  models over the stack's dimensions, under a **~$1 cap** (show the
  estimate first; let the user raise the cap if they want). Maps to:
  ```
  /sdlc-model-council:council-assess models=<free-addrs>,<paid-addrs> \
    dims=<all-stack-dims> budget-usd=1.00
  ```
- **`full`** — the whole shipped stack (every dimension `stack.json`
  defines — currently 4 objective dims; this scales forward automatically
  if a future stack version adds judge dims) across the whole discovered
  fleet, free and paid, under a budget the user sets explicitly (no
  default cap — ask). Maps to:
  ```
  /sdlc-model-council:council-assess models=<all-addrs> \
    dims=<all-stack-dims> budget-usd=<user-set>
  ```

For `calibrate`/`standard`/`full`, actually run the corresponding
`/sdlc-model-council:council-assess` invocation now — it handles the
estimate-first gate, the free wave-0 calibration, the budget hard-stop, and
(per its own step 7) already copies `roster.json`/`roster.md`/
`diversity.json` into `.sdlc/model-council/`. Nothing further to do for
step 4 below in these three cases.

## 4. Roster — `skip` only

`skip` never calls `assess.sh`, so there's no `results.jsonl`. `roster.py`
renders a priors-only roster directly from a model list — every discovered
address gets `posterior = prior`, `n = 0`, all-provisional across the
requested dims (its `--models`/`--dims` mode, design §5.2 step 4):

```bash
mkdir -p .sdlc/model-council
"${CLAUDE_PLUGIN_ROOT}/scripts/council/roster.py" \
  --priors-dir "${CLAUDE_PLUGIN_ROOT}/scripts/council/priors" \
  --pricing "${CLAUDE_PLUGIN_ROOT}/scripts/council/pricing.json" \
  --models "<comma-separated discovered addresses>" \
  --dims "code-review,bug-fix,long-context,instruction-format" \
  --now "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --out-json .sdlc/model-council/roster.json \
  --out-md .sdlc/model-council/roster.md >/dev/null

# diversity: no audition evidence at all yet, so an empty pairs list is the
# honest answer (cast.py already treats any missing/insufficient pair as
# maximally correlated — the pessimistic default).
python3 -c "import json; json.dump({'schema_version':1,'stack_version':'v1','generated_ts':'$(date -u +%Y-%m-%dT%H:%M:%SZ)','pairs':[]}, open('.sdlc/model-council/diversity.json','w'), indent=2)"
```

Do **not** create `.sdlc/model-council/results.jsonl` for `skip` — there's
no evidence to put in it. Flag this to the user plainly: since there's no
`results.jsonl`, running `/sdlc-model-council:council-roster rebuild` later
would rebuild from nothing and wipe every model out of the roster — the
next real step for a `skip`-commissioned project is `council-assess`, not
`rebuild`.

## 5. Seed policy

Write `.sdlc/model-council/policy.json`:

```json
{
  "defaults": {"max_usd_per_run": <from step 2's budget/day, sane per-run slice>,
               "max_concurrent": 5, "posture": "read-only", "k": 3},
  "task_types": {
    "<dimension>": {"play": "diff-synthesis", "cast_rule": {"dimension": "<dimension>", "k": 3},
                     "budget_usd": <guardrail>}
    ... one entry per dimension present in the roster ...
  },
  "fallbacks": {"unreachable_member": "recast-from-roster",
                "uncommissioned": "orchestration-heuristics+warn"}
}
```

Default every `task_types` entry to `play: diff-synthesis` (the only play
that ships in v1) with a **`cast_rule`**, not a pinned cast — a rule is
re-evaluated live against the roster at run time, so it survives a roster
refresh or a model going unreachable, where a pinned list would go stale.
Seed `budget_usd` guardrails from the characterization's budget/day
(step 2), divided down to a sane per-run number — don't invent a number
disconnected from what the user told you. If anything about the seeded
policy looks unusual for this repo (e.g. a `k` larger than the roster has
non-benched models for), warn about it in the report but don't block —
this is a starting point the user can hand-edit.

## 6. Record commission.json

Write `.sdlc/model-council/commission.json`:
```json
{"ts": "<now, UTC ISO>", "audition": "<skip|calibrate|standard|full>",
 "discovered_fleet": [{"model": "...", "family": "...", "free": true|false}, ...],
 "characterization": {"languages": [...], "budget_per_day_usd": <n>, "latency_tolerance": "..."},
 "budget_usd": <the cap used, if any>}
```

Report: the discovered fleet table, the audition depth chosen and what it
cost (or `$0` for `skip`/`calibrate`), a roster summary (grades/roles per
model, provisional flags), and where `policy.json` now routes each
dimension. Remind the user: **never spend paid tokens without an explicit
budget and an estimate shown first** — every `standard`/`full` audition
above went through `council-assess`'s own estimate-then-budget gate, not
around it.
