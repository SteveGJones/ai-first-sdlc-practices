# Retrospective: Council tool-use & command-line-execution assessment

**Branch:** `feature/council-tool-use-assessment`
**Date:** 2026-07-26
**Duration:** One day (two assessment rounds)
**Tracking Issue:** #235 (follow-on to #232 / PR #234)

---

## Summary

Add a **tool-use / command-line-execution** capability to the `sdlc-model-council`
assessment and run a comparison across local MLX (Qwen2.5-Coder 7B/14B/32B,
Qwen3-Coder-30B-A3B 4bit + DWQ, Devstral-Small-2-24B), **Haiku 4.5**, and the
hosted fleet (codex / agy / opencode) — turning the un-audited `tool-use` prior
(0.42 placeholder) and the extrapolated "Haiku should win command execution on
latency × tool-call reliability" intuition into real, measured numbers.

**Outcome:** two dimensions (`command-exec`, `monitoring`), 10 items, two scorers
(`command-check` rubric + `command-diff` execute-and-diff), 10 models audited at
$0 total. Measured answer: **a local `Qwen3-Coder-30B-A3B` ties Haiku 4.5 and the
whole hosted fleet at 2s p50 and genuine $0** — the extrapolation did not hold.

## Why this feature exists

The v1 stack measures only static, single-turn dimensions; nothing exercises the
agentic loop (emit command → observe → decide → iterate → stop). The local-MLX
comparison (PR #234) therefore could not answer "how do local models compare with
Haiku for command-line execution and monitoring?" — the answer was extrapolation
only. This feature closes that gap with a deterministic, safety-first assessment.

## Goals / success criteria (from the proposal)

- A `tool-use` / command-line-execution dimension integrated into the stack,
  priors, roster, and diversity machinery, with deterministic scoring.
- A recorded comparison with **Haiku 4.5 as an anchor** producing grade /
  task-success / turns-to-success / latency / $ numbers.
- Replace the `mlx-local` `tool-use` placeholder with an audition-derived prior.
- Full council suite green; zero technical debt.

## Decisions & rationale

Design spec: `docs/superpowers/specs/2026-07-26-council-tool-use-assessment-design.md`.

- **Propose-and-score, no live shell.** Each item gives a goal + a *simulated*
  terminal transcript; the model emits the correct next command(s) or
  continue/stop decision; scored deterministically. Safe, reproducible, and
  isolates model capability from harness plumbing.
- **Split into two dims** (operator decision): `command-exec` (produce the right
  command for a goal) and `monitoring` (stop-condition judgment over a stream).
- **Reuse `strict-json`** as the answer contract — zero change to
  `extract_answer.py` (the single source of truth). command-exec answers are
  `{"commands":[...],"reason":...}`; monitoring answers are
  `{"decision":"stop|continue","trigger":...,"reason":...}`.
- **New scorer `command-check`** — `format-parse` can't express regex-over-a-free-
  string-value or *negative* constraints, and command-checking needs both (must
  contain `grep` + the target path; must **not** contain `rm -rf`). `checks.json`
  is a rubric of field-level assertions (`equals`/`enum`/`regex`/`not_regex`);
  score = satisfied/total. The `not_regex` guardrail penalises a proposed
  destructive command even though nothing is ever executed.
- **Haiku reached via subagent, at $0** (operator decision): we are *in* Claude
  Code, so Haiku is dispatched as a `model: haiku` subagent and its answer piped
  through the identical scorer — no `ANTHROPIC_API_KEY`, no metered API. The whole
  comparison ran at the free level: MLX $0 local, Haiku $0 subscription-marginal,
  agy pro-sub (~$0.0007 total, API-equivalent proxy).

## Results — the comparison

The comparison ran in two rounds. **Round 1** (6 items, 3/dim) had every model at
raw 1.0 — the tier did not discriminate. **Round 2** added a hard tier (10 items,
5/dim), three more local models, and the `command-diff` execute-and-diff scorer.
The numbers below are round 2 and supersede round 1.

**Final roster — 10 models × 10 items, exec-scored, $0 total.**
Artifacts: `./tmp/final/{merged.jsonl,roster.md,roster.json,diversity.json}`.

| model | family | command-exec | monitoring | raw | p50 lat | $/item |
|---|---|---|---|---|---|---|
| `codex default@medium` | openai-gpt5 | A 0.90 | A 0.90 | 1.00 | 5.0s | $0.0862* |
| `agy gemini-3.6-flash@medium` | google-gemini-3-flash | A 0.90 | A 0.90 | 1.00 | 6.5s | $0.00012* |
| `opencode deepseek-v4-flash-free` | opencode-free-tier | A 0.90 | A 0.90 | 1.00 | 5.0s | $0 |
| `anthropic claude-haiku-4-5` | anthropic-claude-4 | A 0.90 | A 0.90 | 1.00 | 4.67s† | $0 (sub) |
| **`mlx Qwen3-Coder-30B-A3B` 4bit** | mlx-local | A 0.87 | A 0.90 | **1.00** | **2.0s** | **$0** |
| **`mlx Qwen3-Coder-30B-A3B` DWQ** | mlx-local | A 0.87 | A 0.90 | **1.00** | **2.0s** | **$0** |
| `mlx Qwen2.5-Coder-14B` | mlx-local | A 0.87 | A 0.90 | 1.00 | 3.0s | $0 |
| `mlx Qwen2.5-Coder-32B` | mlx-local | A 0.87 | A 0.90 | 1.00 | 7.0s | $0 |
| `mlx Qwen2.5-Coder-7B` | mlx-local | B 0.74‡ | A 0.90 | 0.90 | 2.0s | $0 |
| `mlx Devstral-Small-2-24B` | mlx-local | B 0.74‡ | A 0.90 | 0.90 | 7.0s | $0 |

`*` API-equivalent proxy metered by `usage.py`; on pro subscriptions the marginal
cost is $0 (memory `model-council-cost-framing`).
`†` includes Claude Code harness overhead — not comparable to the bare-prompt
adapter paths. `‡` provisional (wide CI at n=5).

**The answer to the question that motivated the feature.** For command-line
execution and monitoring at this tier, **`Qwen3-Coder-30B-A3B` running locally
ties Haiku 4.5 and the entire hosted fleet on correctness, at 2s p50 and genuine
$0** — and the DWQ quant is indistinguishable from the plain 4bit. The
extrapolated "Haiku should win command execution on latency × tool-call
reliability" **does not hold**. The MoE architecture is what makes this work: the
30B-A3B is as fast as the 7B (2s p50) while being as correct as the 32B.

**What actually discriminates.** `monitoring` is **saturated** — all 10 models
perfect on all 5 items, including both hard traps (an early stage's success is not
the deploy finishing; a retried `ERROR` followed by progress is not terminal).
`command-exec` separates exactly two models, both on `ce-hard-grep-context`:
Qwen2.5-Coder-7B and Devstral-24B, each of which proposed an `awk` program that
**does not do what it claims** (verified by execution). So the honest summary is
one discriminating item out of ten, and the tier still mostly certifies "clears the
bar" rather than ranking the top end.

**Priors re-derived for every audited family** (rule in spec §8a:
`max(0.40, raw_mean − 0.28)`):

| family | command-exec | monitoring | n |
|---|---|---|---|
| anthropic-claude-4 | 0.78 → 0.72 | 0.72 → 0.72 | 5 |
| openai-gpt5 | 0.74 → 0.72 | 0.70 → 0.72 | 5 |
| google-gemini-3-flash | 0.56 → **0.72** | 0.54 → **0.72** | 5 |
| opencode-free-tier | 0.42 → **0.72** | 0.40 → **0.72** | 5 |
| mlx-local | 0.72 → **0.65** | 0.72 → 0.72 | 30 |

This removed a real artifact: with only `mlx-local` updated (round 1), the roster
graded local MLX **above** agy and opencode on *identical* raw 1.0 scores.
`mlx-local` command-exec *drops* to 0.65 — it is the only family with genuine
failures (raw 0.933 over 30 observations). Unaudited families (gemini-3-pro,
oss-gpt-oss, unknown) untouched. **Caveat recorded rather than hidden:** four
families converge on 0.72 because the tier is easy — that is the tier failing to
discriminate, not evidence the families are equivalent.

**Path A vs Path B, settled with data.** Same model
(`Qwen3-Coder-30B-A3B`), same 10 items, concurrency 1: **Path B (bare-prompt `mlx`
adapter) 10/10 in 1–5s per item; Path A (opencode → MLX, agentic system prompt)
5/10 with five 90s+ timeouts.** The items Path A completed scored 1.0, so this is a
throughput verdict rather than the output-corruption seen in #234 — but it
independently re-confirms keeping Path B for local models.

## What went well

- **TDD on the scorer paid off** — 6 golden cases (partial credit, list-join,
  the `not_regex` guardrail catching a planted `rm -rf`, missing-field asymmetry,
  contract-fail) written RED first, scorer GREEN, 45/45. The rubric proved
  self-consistent: all 6 real items score 1.0 on an ideal answer and are
  discriminating on wrong ones (a destructive `rm -rf` answer scored 0.4).
- **$0 whole-fleet comparison** — the operator's reframing (Haiku is a subagent,
  not an API call) plus pro-sub/local pricing meant the full local-vs-Haiku-vs-
  hosted run cost effectively nothing. Round 2 added 4 more models and 4 more
  items at the same $0 (codex's $0.86 metered figure is proxy-only).
- **Full 15-file council suite stayed green** throughout (946 assertions at the
  end); zero technical debt.
- **Re-scoring saved re-running.** Every model's raw answer is persisted in its
  handle dir (`turn-001.last-message.txt`), so when `command-diff` landed, all
  nine adapter runs could be re-scored against the new scorer **for free** — no
  tokens, no MLX time. Worth designing for deliberately: the scorer is a pure
  function of a saved answer, so scorer changes are cheap to re-evaluate.
- **The measurement bugs were caught before the write-up, not after.** Three of
  them (latency contamination, the server crash, the rubric false negative) would
  each have produced a confidently wrong claim.

## What was hard / surprising

- **A real rubric-fairness bug, surfaced by codex (not by review).** codex answered
  `ce-grep-errors` with `awk -F'"' '$3 ~ /500/'` — a *correct, arguably more
  precise* filter — and my rubric's `uses grep` check unfairly failed it (0.8).
  The intent checks (filters for 500, targets access.log, non-destructive) already
  captured correctness; the tool-name check was over-specification. Broadened to
  `grep|egrep|fgrep|rg|ag|awk|sed`; re-scored codex's *saved* answer (free, no
  re-run) → 1.0. Lesson (echoing #234): a live run catches over-fitted golden
  rubrics that a read-through waves through. A command-check rubric should assert
  *what the command must achieve*, not *which binary* achieves it.
- **Adapter invocation — I mis-drove codex and mis-detected opencode at first.**
  (1) codex uses a `default` **sentinel**: `assess.sh` *omits* `--model` when the
  id is `default`, letting codex use its ChatGPT-account model. My manual probe
  passed `--model default` literally, which codex rejects ("not supported with a
  ChatGPT account") — so I wrongly concluded codex was broken. Driving it through
  `assess.sh` (`codex:default@medium`) works. (2) opencode *is* installed
  (`~/.opencode/bin/opencode`) but on the login-shell PATH, not the non-login Bash
  tool PATH — `command -v` missed it. Fix: `export PATH="$HOME/.opencode/bin:$PATH"`
  before the opencode pass. Both were operator/harness-usage errors, not tooling
  faults — the user caught them.
- **The executable-bit gotcha.** `assess.sh` invokes scorers *directly*
  (`"$COUNCIL/score/command-check.py" …`), relying on the shebang + `chmod +x`.
  A `Write`-created scorer is **not** executable, so it failed silently under the
  `|| true` and every item scored `no-output` / `error` — while the *unit test*
  (which calls `python3 <file>`) stayed green. Lesson: the scorer unit test should
  also exercise the exec path; and new scorers need `chmod +x`. Fixed with the
  chmod; verified end-to-end.
- **The cold-start race.** Launching the MLX assess pass before `mlx_lm.server`
  finished loading weights made the first turns return empty. Fix: *warm each
  model with a direct request before assessing it* (also the right way to trigger
  the server's load-switch between 7B/14B/32B).
- **The tier doesn't discriminate.** A genuinely useful negative: at this
  difficulty everyone is perfect, so the assessment certifies "clears the bar"
  rather than ranking the top end. Honest to report, and the motivation for a
  harder follow-up tier.

### Round 2 — the hard tier, and what it exposed

- **The regex rubric was measuring the wrong thing, and the hard tier proved it.**
  On `ce-hard-grep-context` three local models answered with `awk` instead of
  `grep -A 3` and all three scored an identical 0.6667. Executing their commands
  showed the scores were meaningless: Qwen3-30B's awk was **byte-identical to
  `grep -A 3`** (a false negative), while the 7B's printed one wrong line plus three
  blanks and Devstral's repeated a single `INFO` line three times (genuinely
  wrong). The trap is that **both** ways of fixing the regex are wrong — leaving it
  strict keeps failing correct awk, widening it to admit awk turns two false
  negatives into false **positives**. A regex over a proposed command cannot
  separate *correct* from *plausible-looking*. This is the deepest finding of the
  feature and it is what justified `command-diff`: run the command, diff the
  output. Note the new scorer is *harsher* as well as fairer — wrong answers lose
  their partial credit (0.6667 → 0.0) while the correct one goes 0.6667 → 1.0.
- **My own safety deny-list reproduced the exact bug it was fixing.** The first
  `command-diff` refused every awk answer as `unsafe-command`, because `;` inside a
  quoted awk *program* looked like shell command-chaining. Two of my own tests went
  red and caught it. Fix: match the deny-list against a **quote-masked** copy of the
  command, so metacharacter checks only fire on real shell syntax. Lesson: when the
  whole point is "don't over-constrain the command's form", the safety layer needs
  the same discipline as the scoring layer.
- **`--max-concurrent 3` silently corrupted my latency numbers.** One MLX server
  serialises generation, so concurrency adds queueing to the measured `latency_s` —
  and latency was a headline claim ("the 7B is fastest"). The same setting made
  Path A fail outright: three concurrent agentic-system-prompt calls to one 30B
  server blew the 90s item timeout (exit 124, empty output), which I first
  mis-read as "the proxy died". Local passes must run at concurrency 1.
- **Load-switching crashes `mlx_lm.server`.** Reusing one server across models —
  the #234 approach — eventually failed with
  `ValueError: [broadcast_shapes] Shapes (7,1,1,6228) and (7,32,1,8275) cannot be
  broadcast`, a KV/prompt-cache collision. Worse, the server **kept listening**
  while answering nothing, so it looked like a hang rather than a crash. Fix: one
  fresh server per model, poll `/v1/models` until it answers. This supersedes the
  #234 load-switch guidance.
- **A zero that meant "unmeasured".** The Haiku rows initially reported
  `p50_latency_s: 0.0` because the harness rows were synthesised without
  latencies — which renders as "instant" in the roster. Backfilled from the
  observed subagent durations and flagged as including harness overhead. A missing
  measurement should never be encoded as a fast one.
- **Two of the four hard items were still too easy.** `mon-hard-multistage` and
  `mon-hard-transient-error` were written as traps and every single model walked
  through both. Designing an item that *feels* hard is not the same as designing
  one that discriminates.

## Fairness caveats (recorded)

- Haiku is elicited through the Claude Code **subagent** path (carries the harness
  system prompt), whereas MLX/agy go through the bare-prompt adapter path. Bounded
  for single-turn propose-and-score, but a known asymmetry.
- Haiku's `$/item = 0` is the **subscription/subagent marginal cost**; the
  pricing.json `anthropic-claude-4` rate is the API-equivalent proxy. Subagent
  token counts (~20k/item) are dominated by the system prompt and are **not**
  comparable to the bare-prompt paths, so they are not reported as cost.
- MLX latency prints at 1-second integer resolution (7B sub-second → 0s).

## Fairness caveats (round 2 additions)

- **The two scorers are not equally strict**, and 8 of 10 items still use the
  rubric. `command-diff` is binary (achieves the goal or not); `command-check`
  gives partial credit. So a model can still bank partial credit on the 8
  rubric-scored items for a command that would not actually work. Extending
  execution coverage means redesigning those items to be self-contained.
- **`monitoring` scores carry no execution check at all** — they are decisions,
  scored by rubric, and the dimension is saturated. Treat its A grades as
  "cleared a low bar", not as a measured ranking.

## Follow-ups

- **A genuinely harder tool-use tier.** Round 2's hard items were not hard enough:
  9 of 10 models cleared 9 of 10 items, and both monitoring traps caught nobody.
  Candidates with better odds: multi-step sequences where step 2 depends on step
  1's output, commands needing non-obvious flags (`-print0`/`-z` pairing, `--` for
  dash-prefixed paths), stop conditions that require counting stages rather than
  pattern-matching a line, and streams where the terminal line *looks* transient.
- **Make `ce-disk-usage` / `ce-port-inspect` / `ce-hard-find-large-recent`
  executable** by giving them self-contained fixture trees instead of `/var/log`
  and a live port, so `command-diff` can cover them and the partial-credit gap
  above closes.
- **Role integration:** consider a tool-use-driven "executor" role in `roster.py`
  (`command-exec`/`monitoring` are gradable columns today but drive no role).
- **Fold the two measurement rules into the tooling**, not just the docs: have
  `assess.sh` warn when an `mlx:` address is run with `--max-concurrent > 1`, and
  ship the fresh-server-per-model loop as a helper script rather than a
  hand-rolled `./tmp` chain.
- **Elicit Haiku through a real adapter** rather than a subagent harness, to
  remove the system-prompt asymmetry (and to get comparable token/latency
  accounting) — see ADAPTER-AUTHORING.md.
- **Widen `command-diff` beyond exact stdout match** where a task has several
  correct output orderings. Today it normalises trailing whitespace and trailing
  blank lines and then compares exactly; an order-insensitive mode would need a new
  `exec.json` key and its own golden cases.
