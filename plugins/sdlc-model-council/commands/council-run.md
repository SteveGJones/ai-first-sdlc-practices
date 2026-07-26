---
description: Run a cross-model fan-out play (v1: Diff+Synthesis) on a task — cast a decorrelated panel from the roster, fan out to N models, and return one attributed synthesis with a baseline delta.
argument-hint: "task-type=<code-review|...> input=<file-or-text> [play=diff-synthesis] [cast=addr,addr,...] [budget-usd=N] [k=3]"
---

Run a council **play** — a cross-model fan-out — over the given task. v1 ships
one play, **Diff+Synthesis**: the same task goes to a decorrelated panel of
models, and the `council-judge` agent synthesises their responses into one
attributed verdict with a **baseline delta** (did the panel beat the single best
model?). This is the novel work no per-vendor plugin does.

Arguments: `$ARGUMENTS` — parse `task-type=`, `input=` (a file path or inline
text), optional `play=` (default `diff-synthesis`), `cast=` (pin explicit model
addresses, comma-separated), `budget-usd=`, `k=` (default 3).

Scripts live under `${CLAUDE_PLUGIN_ROOT}/scripts/council/`. Do this:

1. **Resolve policy.** Load the `council-policy` skill. If the project is
   commissioned (`.sdlc/model-council/policy.json` exists), read the entry for
   `task-type` to get the play, the cast (pinned addresses or a `cast_rule`),
   and the budget guardrail. If NOT commissioned, say so plainly ("this project
   isn't commissioned; using heuristics") and fall back: play = `diff-synthesis`,
   cast = built live from `.sdlc/model-council/roster.json` if present, else ask
   the user for `cast=`. An explicit `cast=`/`play=`/`budget-usd=` argument
   always overrides policy — note that you did.

2. **Materialise the task.** Write the task to a file (if `input=` is a path,
   use it; if inline text, write it to a scratch file under `./tmp/`).

3. **Set up the play** (deterministic spine, no models yet):
   ```
   scripts/council/play.sh setup --dimension <task-type> --k <k> \
     --roster .sdlc/model-council/roster.json \
     --diversity .sdlc/model-council/diversity.json \
     --task-file <task-file> [--cast <pinned>] [--budget-usd N]
   ```
   It prints `PLAY_DIR=…` and a dispatch table of `label<TAB>model<TAB>result-file`.
   The manifest records the **baseline_member** (the roster's best single model
   for this task) — that's what the synthesis is measured against.

4. **Fan out — one delegation-runner per member, in a single message** (respect
   the cap of 5). For each dispatch-table row, parse the model address
   `adapter:model[@effort]` into `backend` / `model` / `effort` and dispatch the
   `delegation-runner` agent with that backend, the **same** task (from
   `task.md`), and `posture=read-only`. Each runner returns its unified block
   with an **Answer file** path. Do NOT read the answers into your context.

5. **Collect on disk (no context inheritance).** For each member, copy its
   runner's Answer file to `<PLAY_DIR>/<label>.result.md` with `cp` — the answer
   text goes to disk under its blind label, never through your context. A member
   that ERROR/TIMEOUT/NO_OUTPUT'd has no usable answer — leave its result file
   absent (it becomes a non-survivor).

6. **Check quorum:**
   ```
   scripts/council/play.sh combine-check --play-dir <PLAY_DIR>
   ```
   If `verdict` is `PLAY-DEGRADED` (survivors < quorum), report that honestly and
   stop — a panel that couldn't reach quorum must not be dressed up as a
   confident synthesis.

7. **Synthesise (blind).** Dispatch the `council-judge` agent (Sonnet) with the
   `PLAY_DIR` and the manifest's `baseline_label`. It reads
   `combine/blind-bundle.md` + `task.md` (models anonymised as Model A/B/…) and
   writes `combine/synthesis.md` with Convergent / Divergent(attributed) /
   Adjudication / Confidence / **Baseline delta** sections.

8. **Un-blind and report.**
   ```
   scripts/council/play.sh unblind --play-dir <PLAY_DIR> --in <PLAY_DIR>/combine/synthesis.md
   ```
   re-attaches the real model addresses (provenance restored). Present that
   synthesis to the user, then append a spend line — `Council spend: $X across N
   models` — summing each member's cost via
   `scripts/council/usage.py <handle-dir>`. Finally append one line to
   `.sdlc/model-council/outcomes.jsonl`:
   `{"play":"diff-synthesis","dimension":"<task-type>","cast":[…],"baseline_member":"…","ts":"…"}`
   (the measurability ledger; whether the user accepted or reverted the result is
   recorded later, out of scope for v1).

**Measurability reminder:** the Baseline-delta line is the point of the whole
exercise. If, over ~20 real runs, the panel rarely beats the baseline member,
the honest product is roster-driven single-model routing (`/…:delegate` with the
roster's pick), not fan-out. Report the baseline delta faithfully every time; do
not oversell the panel.

If a Claude-family model is ever in the cast, `play.sh` records a
`judge-family-overlap` note — surface it, since the judge (Claude) then shares a
family with a member it's grading.
