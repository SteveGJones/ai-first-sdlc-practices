# RESTART PROMPT — clean slate

**Nothing is in flight as of 2026-08-09.** The last two workstreams are merged:

- **#235 / PR #236** — tool-use & command-execution assessment dimension.
- **#237 / PRs #238, #239** — poker-capstone assessment ladder, local-model
  agentic harness, assessment-first reframing of `sdlc-model-council`, plus a
  research note on why local models failed.

**Start here:** read `CLAUDE.md` "Active Work" for what is open (EPIC #197
Phase C; EPIC #97 sub-features) and the memory index for project state. Do not
resume anything from this file — it now holds only *standing context* that
outlives any single task.

---

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



---

## Standing operational facts (not task state)

**`mlx_lm.server` — always bound the prompt cache.** Unbounded, it accumulates
a KV sequence per session and will OOM or kernel-panic (see above; also
`ml-explore/mlx-lm#883`, where a **96GB** machine panicked the same way).
Bounding is required at every RAM tier, not as a small-machine workaround.

```bash
uv run --with mlx-lm mlx_lm.server --model <hf-id> --port 8081 \
  --decode-concurrency 1 --prompt-concurrency 1 \
  --prompt-cache-size 2 --prompt-cache-bytes 4294967296
```

**`--max-concurrent` does NOT exist** in mlx-lm 0.31.3 — it is
`--decode-concurrency` / `--prompt-concurrency`; the old flag makes the server
exit immediately. The server also load-swaps models by the request's `model`
field, so one instance can serve several cached models sequentially.

**Assessment artefacts are exempt from four validators.**
`research/poker-capstone/{runs,broken-variants}` are skipped by flake8
(`.pre-commit-config.yaml` + `setup.cfg`), CodeQL
(`.github/codeql/codeql-config.yml`), the technical-debt scanner
(`skip_path_prefixes`) and logging compliance (`.ai-sdlc.json`). This is
deliberate — `runs/` is verbatim model output, some defective *on purpose* as a
recorded result, and must stay byte-identical to stay re-verifiable. **Do not
"fix" lint findings in there.** Two of those validators auto-detect
framework-vs-application context *by file ratio*, so adding a large corpus can
silently flip the whole repo onto strict rules — worth remembering before
committing another big body of generated material.

## Standing rules that keep paying off

- **The grader is under test too.** Never accept a judge verdict — or a
  research agent's citation — at face value. Re-verify against source. This has
  found five real bugs in our own grading material, every one in the model's
  favour, plus three overstated citations in web research.
- **Verify a background loop is doing real work within a minute or two**, not
  just that its PID exists. `ps` CPU-time vs wall-clock plus the process log
  told the real story every time something looked "stuck".
- **A cheap targeted probe beats a long exhaustive run** when the question is
  "is this broken?"

## Measurement traps that have cost real time here

- **Stale agent worktrees under `.claude/worktrees/` are full repo copies** and
  inflate any local scan. `git worktree list` and prune before measuring.
- **Compare both sides in clean worktrees outside the repo** — comparing
  main-in-a-worktree against branch-in-the-working-tree is not apples-to-apples.
- **zsh does not word-split unquoted `$VAR`**; **`while read` silently drops a
  final line with no trailing newline.** Both have caused real damage.
- **Never run `pre-commit run --all-files`** casually here — it auto-reformats
  the entire repo, including the byte-identical assessment artefacts. Scope it
  with `--files`.
