# RESTART PROMPT — `sdlc-model-council` assessment: what is done, what is next

Paste into a fresh session to resume. Self-contained; read the pointers before
writing code.

**Two workstreams completed and merged/open as PRs — do not restart either:**

- **#235 / PR #236 (merged)** — tool-use & command-line-execution assessment
  dimension, execute-and-diff scorer, 10-model audition.
- **#237 / PR #238** — poker-capstone assessment ladder, the local-model
  agentic harness, and the assessment-first reframing of the plugin docs.

Keep the MLX safety section below: it is standing operational context for any
local-MLX work, not a record of a closed task.

## ⚠️ Local MLX kernel-panic history — resolved as of 2026-07-28, read before trusting large dense models unattended

**Status: OS updated (26.5.1/25F80 → 26.6/25G72), panic-diagnosis tooling
verified working, full re-test of every currently-cached model clean, zero
panics.** Not proof the underlying bug is gone — see "What's still unknown"
below — but there is no live risk signal against anything in the current
local cache.

### What happened (2026-07-26/27, pre-update)

Four kernel panics in ~30 hours, all during local MLX (Apple Silicon Metal/GPU)
inference, all in the same kernel subsystem:

| Timestamp (local) | Panic reason | Subsystem |
|---|---|---|
| 2026-07-26 13:20:10 | `"pending memory object unexpectedly found in non pending hash"` | `IOGPUGroupMemory.cpp:528` |
| 2026-07-26 14:51:34 | same as above | `IOGPUGroupMemory.cpp:528` |
| 2026-07-27 15:15:56 | `"completeMemory() prepare count underflow"` | `IOGPUMemory.cpp:550` |
| 2026-07-27 17:43:37 | `"pending memory object unexpectedly found in non pending hash"` | `IOGPUGroupMemory.cpp:528` |

All four are macOS/Metal **kernel** driver faults (IOGPU memory-object
accounting), not app-level crashes — they happen below anything `assess.sh`
or the MLX adapter can catch or prevent.

- The 2026-07-27 17:43:37 panic is breadcrumb-confirmed: an in-flight
  `mlx-chat` request to `mlx-community/Devstral-Small-2-24B-Instruct-2512-4bit`
  (`REQUEST_WAITING` at `T-4min`), with `Qwen3-Coder-30B-A3B-Instruct-4bit`
  also active in the same run directory.
- The 2026-07-27 15:15:56 panic's attribution to `Qwen2.5-Coder-32B-Instruct-4bit`
  is **unconfirmed** — a 2026-07-28 review found the breadcrumb tooling didn't
  exist yet at that timestamp (earliest breadcrumb on disk: `22:04:52Z` that
  day), and the panic report itself carries no model strings. The operator
  did delete 32B from the cache after this panic believing it was the cause;
  a second, differently-signatured panic happened anyway with 32B already
  gone, so the risk generalizes beyond one model. Full account in the
  retrospective's "What was hard / surprising" section — read that, not this
  summary, for the actual evidence chain.

**Working theory (unchanged):** a macOS/Metal driver bug under unified-memory
pressure on this 32GB Apple Silicon machine, most acute with large dense
models on long-context prompts or multiple large models in flight. Panics
rather than OOM-killing gracefully. `hardware_risk` field in
`plugins/sdlc-model-council/scripts/adapters/mlx/adapter.json`.

### 2026-07-28 re-test — clean

Every model still in the local cache (7B, 14B, both 30B-A3B variants,
Devstral-24B — `Qwen2.5-Coder-32B` excluded, no longer cached) run through the
long-context dimension via **both** Path A (OpenCode) and Path B (direct), one
MLX server loaded at a time, `mlx-server-run.sh` heartbeat logging watching
memory pressure throughout. Uptime stayed continuous the whole session
(zero reboots), including a run where `Pages free` dropped to ~7k pages. The
breadcrumb tooling's `SUSPECTED_PANIC_VICTIM` detection was verified
end-to-end first (deliberately `SIGKILL`-ing `assess.sh` mid-dispatch,
confirming the victim model/item was correctly identified) — and that check
surfaced a real bug (`last_alive` always `"unknown"`, fixed) before the fleet
re-test was trusted.

### What's still unknown

- **`Qwen2.5-Coder-32B` itself is untested** since it was deleted — the only
  model with even circumstantial (not confirmed) evidence against it has not
  been re-run on the updated OS.
- **Two MLX servers loaded concurrently** (the documented
  `fanout_safe:false` case, and the actual condition during the second
  panic) was deliberately *not* reproduced in the 2026-07-28 re-test —
  operator chose sequential-only for that pass.
- A clean re-test is evidence of reduced/absent risk, not proof — GPU kernel
  panics under memory pressure are not perfectly deterministic.

### Panic post-mortem tooling (built 2026-07-27, committed, verified)

- `plugins/sdlc-model-council/scripts/council/mlx-panic-report.sh` — read-only;
  correlates in-flight-request breadcrumbs (Path A + Path B + `assess.sh`
  orchestrator) against the newest macOS panic reports in
  `/Library/Logs/DiagnosticReports`. Run it after any unexplained reboot,
  before starting new work, so old breadcrumb files don't get overwritten by
  a fresh run's traffic.
- `plugins/sdlc-model-council/scripts/council/mlx-server-run.sh` — wraps
  `mlx_lm.server` with unbuffered, timestamped logging + a `vm_stat`/RSS
  heartbeat every 5s, fsync'd, so a post-mortem has a memory-pressure trend
  leading up to the panic, not just a last-known-good log tail.
- `plugins/sdlc-model-council/scripts/adapters/mlx/mlx-stop-proxy.py` — Path A
  (OpenCode) breadcrumb instrumentation, same idea as `mlx-chat`'s existing
  breadcrumbs but for the proxy path, which can't see item IDs directly so
  fingerprints requests by content instead.
- `assess.sh` now writes `panic-breadcrumb.jsonl` per run dir (DISPATCH /
  HEARTBEAT / DONE events) and archives any stale `active/*.pair` files found
  at startup as `SUSPECTED_PANIC_VICTIM` before wiping them — previously that
  evidence was destroyed by the normal startup cleanup on every run.

---


## Where the assessment capability stands

`sdlc-model-council` is **assessment + delegation**, in that order — assess a
model, put it on a roster with evidence, then route work against that roster.
Two instruments:

1. **v1 item stack** (`plugins/sdlc-model-council/assessment/stack/v1/`) —
   short items, cheap, broad. Right for auditioning a newly-released model.
2. **Poker capstone** (`research/poker-capstone/`) — a difficulty-ordered
   ladder (P1-P10) over one substantial problem, run fail-fast. Shows *where*
   a model breaks.

**Terminology, easy to get wrong:** P1-P10 are the phases. **P11 is the
cross-model roster exercise, NOT a phase** — "running P11" for a model means
running it from P1 upwards. There is no phase 11 to jump to, and no phase
should be skipped to reach the more interesting build phases faster.

### Assessment results to date

| Model | Outcome |
|---|---|
| Sonnet | P1-P10 baseline; strong until **P9 FAIL** (real payout bug) |
| Haiku | Stopped at P6; **P5/P6 FAIL**; P2 suite green but blind to the planted bug |
| Qwen2.5-Coder-14B | **P1 FAIL** (2/15 facts) — coherent but shallow, zero confabulation |
| Qwen3-Coder-30B-A3B | **P1 FAIL** (5 right / 4 **wrong**) — deeper but confabulates, and collapses into a repetition loop at any temperature |

**Local-model seat is closed for now.** Both auditioned 4-bit local models
fail P1, the ladder's easiest phase. Scope that claim honestly: two models,
4-bit, one 32GB Mac, one phase — not a general verdict on local models.

### Settled — do not re-investigate

- **`mlx_lm.server` prompt-cache OOM.** Unbounded cache accumulated a KV
  sequence per session (9 sequences / 9.72 GB) until the GPU OOM'd. Fix:
  `--prompt-cache-size 2`. Turns a 2h48m hang into a 71s clean run.
  **`--max-concurrent` does NOT exist in mlx-lm 0.31.3** — it is
  `--decode-concurrency` / `--prompt-concurrency`; the old flag makes the
  server exit immediately. Working launch:
  ```bash
  uv run --with mlx-lm mlx_lm.server --model <hf-id> --port 8081 \
    --decode-concurrency 1 --prompt-concurrency 1 \
    --prompt-cache-size 2 --prompt-cache-bytes 4294967296
  ```
- **OpenCode (Path A) for code-reproduction work.** Quote-escaping corruption
  reproduces on 14B, not just 7B. Scope it honestly: 1 corrupted item vs 3
  clean ones on the same model (the clean ones emit JSON, not source), so it
  is task-shaped, not blanket. Enough to rule it out for file-writing phases.
  **0 of the 11 poker phases have ever been run through OpenCode.**

### The local-model agentic harness (built, verified, unused)

`research/poker-capstone/harness/{file_blocks,mlx_client,local_agent,run_local}.py`
supplies the write → verify → feed-back → retry loop a text-only local model
needs to attempt build phases. 36 unit tests plus three live checks against the
real 14B. **It was never the constraint** — neither local model reached the
build phases it unlocks. It stays ready for a stronger local model.

## Candidate next steps (pick with the operator, don't assume)

1. **Run a stronger model up the ladder from P1** — Opus as the "above Sonnet"
   reference point was previously declined; a larger local model would finally
   exercise the agentic harness.
2. **Fold poker-capstone results into the roster card format**
   (`plugins/sdlc-model-council/scripts/council/roster.py`) so ladder findings
   sit alongside the v1 stack's dimensions in one comparable report. This is
   still outstanding and is the main integration gap.
3. **Repo-wide technical-debt backlog** — `SDLC Compliance Check` fails on
   `main` itself (5586 violations, pre-existing, not from #237). Worth a
   dedicated cleanup PR rather than blocking feature work.

## Standing rules that keep paying off

- **The grader is under test too.** Never accept a judge verdict at face
  value — re-verify against source. This has found five real bugs in our own
  grading material, every one in the model's favour.
- **Verify a background loop is doing real work within a minute or two**, not
  just that its PID exists. A shell bug once silently killed a run for an
  hour; an OOM once looked like "a slow model" for 2h48m. `ps` CPU-time vs
  wall-clock plus the server log told the real story both times.
- **A cheap targeted probe beats a long exhaustive run** when the question is
  "is this broken?" — one 71s item replaced an 18-pair multi-hour re-run and
  answered more than the big run could have.
- **`mlx_lm.server` load-swaps models by the request's `model` field**, so one
  instance can serve several cached models sequentially without a restart.
