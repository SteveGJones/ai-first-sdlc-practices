# Poker capstone — a model **assessment** benchmark

**This is assessment infrastructure, not a shipped plugin and not a poker
game.** The poker implementation is a means, not the point: it is a
deliberately-chosen problem hard enough to separate models that all look
equally capable on toy tasks. What this directory actually provides is a
**repeatable way to measure what a coding model can and cannot do**, and a
record of what each assessed model actually scored.

Companion to the `sdlc-model-council` plugin: that plugin is the *delivery*
mechanism (how you reach a model and delegate to it), this is the
*assessment* mechanism (how you decide whether that model is worth a seat on
the roster). See `docs/feature-proposals/237-council-poker-capstone.md` for
the design rationale.

## Why an assessment capability at all

Model choice is normally made on vendor benchmarks, vibes, or a one-off try.
None of those survive contact with a real multi-stage engineering task. This
benchmark exists so a roster decision can be made on **evidence produced on
our own problem, under our own grading, reproducibly**.

Three design commitments make the results trustworthy:

1. **Difficulty-ordered phases, run fail-fast.** A model's assessment stops at
   its first genuine failure rather than always paying for the full pipeline.
2. **Grading is independent of the exemplar.** The stage-4 harness
   cross-validates payouts against its own oracle, so a submission is not
   graded by comparison to our implementation's particular choices.
3. **The grader is itself under test.** Every verdict is re-verified against
   source before being accepted. This has repeatedly found bugs in *our own*
   grading material — see "The grading apparatus is not trusted" below.

## The capability ladder

**P1-P10 are the phases. P11 is the cross-model roster exercise, not a
phase** — "running P11" for a model means running that model from P1 upwards.

| Phase | What it measures |
|---|---|
| P1 | Document the exemplar — comprehension of existing code |
| P2 | Author a QA suite blind — does it catch a planted bug |
| P3 | Judged architecture quality |
| P4 | Judged detailed-design quality |
| P5 | Spec-fidelity server build |
| P6 | Spec-fidelity client build |
| P7/P8 | Cross-pairing a submitted client/server with the exemplar's |
| P9 | Full-autonomy full-stack build |
| P10 | Post-hoc documentation drift |

## Results so far

| Phase | Sonnet | Haiku | Qwen2.5-Coder-14B | Qwen3-Coder-30B-A3B |
|---|---|---|---|---|
| P1 | 14/15 facts | 15/15 facts | **FAIL** 2/15 | **FAIL** 5 right, 4 **wrong** |
| P2 | 72/72, 3/3 catch bug | 42/42 but **0/42** catch bug | — | — |
| P3 | 2/2/1/2 | 2/2/2/2 | — | — |
| P4 | server 2/2/2/2, client 1/2/2/2 | server 2/2/2/1, client 2/2/1/1 | — | — |
| P5 | 3/3 pass | **FAIL** | — | — |
| P6 | 3/3 pass | **FAIL** | — | — |
| P7/P8 | clean pass | not run (stopped) | — | — |
| P9 | **FAIL** — real payout bug | not run (stopped) | — | — |
| P10 | 5/5 | not run (stopped) | — | — |

Each run stopped where fail-fast dictated. Full per-phase detail and the
reasoning behind every stop is in
`retrospectives/237-council-poker-capstone.md`; per-run detail is in
each run's own `RESULTS.md`.

**What the assessment surfaced that a single score would not have:**

- Sonnet is strong on comprehension and spec-fidelity but **failed
  full-autonomy (P9)** on a real hand-completion/payout bug. A model's
  ceiling on one phase does not predict another.
- Haiku's P2 suite passed 42/42 against the exemplar yet caught **none** of
  the planted bug — every payout test asserted only chip conservation, never
  which seat won. A suite can be large, green, and structurally blind.
- Both local 4-bit models failed P1, the *easiest* phase, in opposite ways:
  the 14B was coherent but shallow with **zero** confabulation; the MoE
  engaged more deeply but **confabulated four facts** and collapsed into a
  repetition loop. By this benchmark's own stated ordering — a confidently
  wrong claim is worse than an omission — the larger model is the worse one.

## Layout

```
research/poker-capstone/
  exemplar/              Reference implementation, built by Claude
    docs/                  architecture, design-server, design-client
    server/                FastAPI + WebSocket, in-memory game state
    client/                Static HTML/JS, no build step
    docker-compose.yml
  harness/               The assessment machinery
    runner                 docker-compose lifecycle (build/up/health/down)
    scenarios              REST-driven turn enforcement, multi-hand, side pots
    oracle                 Independent hand-eval + pot reconstruction
    browser_scenarios      Playwright client verification
    client_verify          Client contract checks
    checklist              Deterministic topic coverage
    doc_fidelity           P1 scoring — checklist + judge-prompt builder
    design_judge           P3/P4 judge-prompt builder
    qa_fidelity            P2 scoring
    file_blocks            Parse/write fenced file blocks, traversal-safe
    mlx_client             Multi-turn client for a local mlx_lm.server
    local_agent            write -> verify -> feed-back -> retry loop
    run_local              CLI wiring the Docker verifier into that loop
  broken-variants/       Deliberately-broken copies, proving the harness
                         fails on the SPECIFIC injected bug
  runs/                  Every assessment run, with its results write-up
  docs/                  Harness contract, client test contract,
                         P1 ground-truth facts, brief template
```

## Assessing a model that cannot use tools

Hosted models are assessed via subagent delegation. A **local** model reached
through the `mlx:` adapter is text-only and one-shot — no filesystem, no
Docker — so unaided it could only attempt the judged-document phases, which
are precisely the phases that do *not* discriminate between models.

`local_agent` closes that gap by supplying the missing feedback cycle: parse
the model's file blocks, write them to disk, run the real verifier, feed the
failures back, retry. `model_fn` and `verify_fn` are injected, so the loop is
testable without a live server or Docker and can drive any backend.

```bash
# 1. Start the server with a BOUNDED prompt cache. Unbounded, it accumulates a
#    KV sequence per session and OOMs the GPU. Note --max-concurrent does not
#    exist in mlx-lm 0.31.3; it is --decode-concurrency/--prompt-concurrency.
uv run --with mlx-lm mlx_lm.server \
  --model mlx-community/Qwen2.5-Coder-14B-Instruct-4bit --port 8081 \
  --decode-concurrency 1 --prompt-concurrency 1 \
  --prompt-cache-size 2 --prompt-cache-bytes 4294967296

# 2. Run a build phase agentically.
python -m harness.run_local \
  --brief runs/local-p5/brief.md --impl-dir runs/local-p5/impl \
  --transcript-dir runs/local-p5/transcript \
  --model mlx-community/Qwen2.5-Coder-14B-Instruct-4bit \
  --context docs/HARNESS-CONTRACT.md
```

Two fairness rules are built in rather than left to the operator:

- **`iteration_count` is recorded on every result** and written to the
  transcript. A pass on attempt 5 is not a pass on attempt 1, and any
  comparison against the baselines must say which it was.
- **A reply with no file blocks gets a format nudge, not a zero.** A model was
  previously contract-failed for using a plain language-tagged fence when its
  actual fix was correct; that is a formatting slip, not a capability gap.

## The grading apparatus is not trusted

A standing rule, learned the hard way: **never accept a judge verdict at face
value.** Grading real model output has now found bugs in this project's own
grading material **five times**, and every time the model was right and our
reference was wrong:

- The P1 ground-truth facts F1 (turn-check ordering) and F15 (showdown
  reveal) were both wrong; correcting F15 retroactively lowered Sonnet's own
  P1 tally.
- The exemplar's server design doc had drifted from its own implementation.
- A P3 judge verdict claimed a contradiction the candidate had explicitly
  scoped out.
- The `doc_fidelity` checklist had two substring false positives — `turn`
  matched inside **"Returns"** and `layer` matched inside **"player"**, the
  latter satisfying the side-pot topic for *any* poker document. Found only
  by grading a thin document; two clean baseline runs never exposed it.

Corrections are recorded as dated `CORRECTED` verdict files rather than
silently edited, so the audit trail survives.

## Running the harness

```bash
cd research/poker-capstone
uv venv --seed && source .venv/bin/activate
uv pip install -r harness/requirements.txt
python -m playwright install chromium        # for browser scenarios

python -m harness --impl-dir exemplar --project-name my-run
# exit 0 + {"passed": true, ...}; builds, runs, tears down automatically

python -m pytest harness/tests/ -q           # 60 tests
```

## Running the exemplar locally

```bash
cd research/poker-capstone/exemplar
docker compose up -d
# server: http://localhost:8000   client: http://localhost:8081
docker compose down
```
