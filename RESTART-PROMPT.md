# RESTART PROMPT — run the local MLX model through the poker-capstone ladder from P1 (#237)

Paste into a fresh session to resume. Self-contained; read the pointers before
writing code. Two earlier blockers (the `mlx_lm.server` OOM, and whether
OpenCode was viable) are now **closed** — do not re-open them.

---

## Mission (one line)

Run `mlx-community/Qwen2.5-Coder-14B-Instruct-4bit` through the
`research/poker-capstone/` ladder **starting at P1 and going up in order**,
fail-fast, using the agentic wrapper built on 2026-07-31.

## Terminology — read this before planning anything

**P1-P10 are the ladder phases. P11 is NOT a phase — it is the cross-model
roster exercise**, i.e. the activity of running a further model through P1
onwards. "Running P11 for model X" means "run X through P1, P2, P3, ...",
exactly as Haiku's P11 run meant P1-P6 before it was stopped. There is no
phase 11 to jump to, and no phase may be skipped to get somewhere more
interesting — the ladder is difficulty-ordered precisely so a run can stop at
its first genuine failure.

## Where we are (don't re-derive)

- **`research/poker-capstone/`** (branch `feature/council-poker-capstone`,
  issue #237): a reusable multi-stage agentic-coding benchmark (Texas Hold'em
  client/server, difficulty-ordered ladder P1-P11). Sonnet's P1-P10 baseline is
  done and clean. Haiku's run is done, deliberately stopped at P6 (P5/P6 were
  genuine, independently-verified FAILs). Full detail:
  `retrospectives/237-council-poker-capstone.md`, memory
  `poker-capstone-p11-status`.
- **Model choice is settled**: `Qwen2.5-Coder-14B-Instruct-4bit`, confirmed by
  a real head-to-head audition against `Qwen3-Coder-30B-A3B-Instruct-4bit`.
  Do not re-audition.

## CLOSED — do not re-investigate

1. **`mlx_lm.server` prompt-cache OOM (was blocking).** Root cause was an
   unbounded prompt cache accumulating a KV sequence per session ("9 sequences,
   9.72 GB") until the GPU OOM'd. **Fixed**: launch with
   `--prompt-cache-size 2`. Verified — the exact item that hung for 2h48m now
   completes in 71s with the cache steady at "1 sequences, 0.10 GB".
   **`--max-concurrent` does NOT exist in mlx-lm 0.31.3**; it is
   `--decode-concurrency` / `--prompt-concurrency`, and passing the old flag
   makes the server exit immediately.
2. **OpenCode / Path A — definitively rejected.** With the OOM fixed the run
   completes, and the completed output is corrupted by the quote-escaping bug
   (`\"\"\"` instead of `"""`, does not compile) — now **reproduced on 14B**,
   not just the 7B where it was first seen. It is an encoding fault, not a
   capability one: repair only the escaping and the same answer passes 9/9.
   The planned 18-pair re-run was abandoned as uninterpretable. Do not use
   OpenCode for local MLX models, including for file-writing phases.

## What exists now — the agentic wrapper

The `mlx:` adapter is one-shot and text-only, so it could only attempt
P1/P3/P4/P10 — exactly the phases that did NOT discriminate between Sonnet and
Haiku (whose FAILs were P5/P6). These modules close that gap, all under
`research/poker-capstone/harness/`:

- `file_blocks.py` — parse/write ```file:PATH fences, path-traversal safe
- `mlx_client.py` — multi-turn client for `mlx_lm.server`
- `local_agent.py` — the write → verify → feed-back → retry loop
- `run_local.py` — CLI wiring the real Docker verifier into the loop

Verified with 36 new unit tests (60 total, no regressions) plus three live
checks against the real 14B, including confirmation the model actually receives
its prior answer and feedback, and 1 → 6 → 1 failure convergence over three
iterations.

## How to run it

```bash
# 1. Start the server WITH a bounded cache (see "CLOSED" #1 above).
uv run --with mlx-lm mlx_lm.server \
  --model mlx-community/Qwen2.5-Coder-14B-Instruct-4bit --port 8081 \
  --decode-concurrency 1 --prompt-concurrency 1 \
  --prompt-cache-size 2 --prompt-cache-bytes 4294967296

# 2. Run a build phase.
cd research/poker-capstone
python -m harness.run_local \
  --brief runs/local-p5/brief.md \
  --impl-dir runs/local-p5/impl \
  --transcript-dir runs/local-p5/transcript \
  --model mlx-community/Qwen2.5-Coder-14B-Instruct-4bit \
  --context docs/HARNESS-CONTRACT.md
```

## What to actually do

1. **Start at P1** (fail-fast, same as the Sonnet and Haiku runs). See the
   "P3-P10 built and run" and "P11 begins: Haiku run" sections of
   `retrospectives/237-council-poker-capstone.md` for the exact per-phase
   mechanics (judge prompts, harness verification, blind-mode dispatch) to
   replicate.
2. **Then P2, P3, ... in order**, stopping at the first genuine FAIL per the
   ladder's fail-fast design intent. Do not skip ahead to the build phases
   because the wrapper makes them newly reachable — the earlier phases are
   what make a later failure interpretable, and Haiku's P2 result (42/42 pass
   but 0/42 catching the planted bug) is exactly the kind of finding that only
   shows up if you actually run the phase.
3. **Record `iteration_count` for every phase.** This is the headline fairness
   caveat: a pass on attempt 5 is not comparable to a Sonnet baseline pass on
   attempt 1, and the write-up must say which it was.
4. **Re-verify any judge "INCORRECT" verdict** against the actual exemplar
   source before trusting it. Grading previous models found five real errors in
   this project's OWN reference materials — every time, the model was right and
   our reference was wrong.

## Lessons already learned — apply, don't repeat

- **Verify a background loop is doing real work within a minute or two**, not
  just that its PID exists. A shell bug once silently killed a run for an hour;
  an OOM once looked like "a slow model" for 2h48m. `ps` CPU-time vs wall-clock
  elapsed, plus the server log, told the real story both times.
- **A cheap targeted probe beats a long exhaustive run** when the question is
  "is this broken?" — one 71s item replaced an 18-pair multi-hour re-run and
  answered more than the big run could have.
- **`mlx_lm.server` load-swaps models by the request's `model` field**, so one
  instance can serve multiple cached local models sequentially without a
  restart between them.
