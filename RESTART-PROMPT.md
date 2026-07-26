# RESTART PROMPT — `sdlc-model-council`: evaluate local **MLX** models (#232 follow-on)

Paste into a fresh session to resume. Self-contained; read the pointers before writing code.

---

## Mission (one line)

Bring **local MLX (Apple-Silicon) LLMs into the council assessment** so they sit in the
same **roster** and **fan-out plays** as the hosted fleet — a **local-vs-hosted
comparison** on a **32 GB MacBook Pro**: does a $0, no-egress, fully-private local model
grade well enough on the standardized problem stack to earn roster roles (e.g. a
privacy-preserving reviewer) against the paid hosted models? Prove or disprove it with
real numbers.

## Approach — reuse the OpenCode adapter first; a dedicated adapter is later

**Path A — MLX *through* OpenCode (DO THIS FIRST; fastest, zero new adapter code).**
`mlx_lm.server` exposes an **OpenAI-compatible** endpoint; OpenCode registers it as a
custom provider, so an MLX model becomes addressable as `opencode:mlx/<model>` and is
assessed by the **existing opencode adapter** — no engine or adapter changes.
- Confirmed real: [awni's "OpenCode with MLX" gist](https://gist.github.com/awni/93a973a0cf5fb539b2ce1f37ec4a9989),
  [OpenCode providers docs](https://opencode.ai/docs/providers/). Config shape:
  ```json
  {"$schema":"https://opencode.ai/config.json","provider":{"mlx":{
    "npm":"@ai-sdk/openai-compatible","name":"MLX (local)",
    "options":{"baseURL":"http://127.0.0.1:8080/v1"},
    "models":{"mlx-community/<model>":{"name":"<display>"}}}}}
  ```
- **The one wrinkle to solve first (DF4 precedence):** our opencode adapter writes a
  *per-handle* `OPENCODE_CONFIG` carrying the read-only permission block. The `mlx`
  provider block must be visible to that same run — so the adapter's per-handle config
  must *include/merge* the provider block, or the provider must live where opencode
  still reads it under `OPENCODE_CONFIG`. **First task = a one-model smoke test** to
  confirm the provider is picked up under our read-only posture (recall from #232:
  `OPENCODE_CONFIG` is lower precedence than a repo's own `opencode.json`; prefer
  `OPENCODE_CONFIG_CONTENT` or a merged per-handle config).

**Path B — dedicated `mlx` adapter (later productization).** `mlx:<model>` via one-shot
`mlx_lm.generate`, no OpenCode dependency (one directory: `adapter.json` + `adapter.sh`,
zero engine edits; opencode adapter is the template; see `plugins/sdlc-model-council/
docs/ADAPTER-AUTHORING.md`). Build this only if MLX earns a permanent seat and we want
it independent of OpenCode. Not needed for the evaluation.

## Where we are

- **model-council v1 is MERGED to `main`** (PR #233, merge commit `b524066`). 681 tests
  green (368 council + 313 substrate). This branch (`feature/model-council-mlx`) is cut
  off that merge. Never commit to `main`; feature branch only.
- The council layer lives at `plugins/sdlc-model-council/scripts/council/` — `assess.sh`
  (estimate gate → free wave-0 → paid waves w/ budget hard-stop + resume + timeout),
  `roster.py`/`diversity.py`/`cast.py`, 4 scorers, `play.sh` (Diff+Synthesis) +
  `council-judge` agent, 5 commands, the `council-policy` skill, priors + pricing.
- Assessment stack: `plugins/sdlc-model-council/assessment/stack/v1/` — 9 objective
  items across code-review/bug-fix/long-context/instruction-format.

## The 32 GB constraint shapes everything

Unified memory shared by macOS + apps + model + KV cache. Budget ~8–10 GB for the system
→ **~22 GB for weights + context**. 4-bit quant ≈ 0.5–0.6 GB per 1B params:

| Model (4-bit, `mlx-community/*`) | ~Weights | 32 GB | Role |
|---|---|---|---|
| Qwen2.5-Coder-**7B** / Llama-3.1-8B | ~4–5 GB | ✅ fast | fast-local baseline |
| Qwen2.5-Coder-**14B** | ~8 GB | ✅ comfortable | quality/latency sweet spot |
| Qwen2.5-Coder-**32B** | ~18 GB | ⚠️ tight | stretch test (long-context items inflate KV cache → watch swap) |
| any 70B | ~40 GB | ❌ | excluded on 32 GB |

**Two hard constraints for the local wave:**
1. **Concurrency = 1.** `mlx_lm.server` serves ONE model and 32 GB can't hold two large
   models → MLX runs **sequentially** (server up → assess model → server down → next).
   Use `assess.sh --max-concurrent 1` for the MLX wave; the hosted fleet still fans out.
2. **Generous timeouts.** Local 32B on the 7k-token long-context items is slow
   (tens of seconds–minutes/turn). Bump item `timeout_s` for the MLX wave (consider
   adding a `--timeout-override` to assess.sh), or run 32B on a **reduced dim set**
   (skip/shorten long-context) to avoid OOM/swap.

## Methodology — reuse the council assessment unchanged

1. **Assess** each MLX model on the 4 objective dims — the identical 9-item stack the
   hosted fleet ran.
2. **Include a hosted anchor** in the SAME run (e.g. `agy:gemini-3.6-flash-medium`, the
   cheap solid-B baseline) → one roster with **local and hosted side by side**: grade
   per dim, **$0 cost** for all MLX, and **p50 latency** (where local pays).
3. **Diff+Synthesis test:** best local model + a hosted member reviewing our own code —
   the "is a private, $0, no-egress local reviewer good enough for the panel?" question;
   record the baseline-delta.

**What we learn (success criteria):** does a local model grade ≥ B on code-review/bug-fix
(→ a privacy-preserving zero-cost reviewer)? the quality-vs-latency curve across
7B/14B/32B? does 32B-4bit survive the long-context items on 32 GB or swap/OOM? does a
local member still add material value to a hosted panel?

## Ground-truth facts (probed 2026-07-25/26 — don't re-derive)

- **Machine:** arm64 (Apple Silicon), 32 GB unified memory. MLX runs natively.
- **`mlx-lm` is NOT pre-installed** (system python has neither `mlx_lm` nor `mlx.core`)
  but IS installable. **User Python policy (global `~/.claude/CLAUDE.md`): never global
  pip — use a project `.venv` via `uv`.** So `uv venv --seed` then `uv pip install
  mlx-lm`; run via `uv run mlx_lm.server --model <hf-id> --port 8080` (OpenAI-compatible
  `/v1`) or `uv run mlx_lm.generate`. Models from `mlx-community/*` on HuggingFace
  (first run downloads weights — several GB, slow).
- **opencode** binary is at `~/.opencode/bin/opencode`, OFF the non-interactive Bash
  PATH; opencode 1.18.5; anonymous OpenCode Zen free tier = ~100 req/day (irrelevant for
  local — a local provider bypasses Zen entirely).
- **`jack-tar-mlx` plugin exists but is IMAGES (mflux), not LLM** — reference only.
- Adapter grammar `^[a-z][a-z0-9]*`; addresses `opencode:mlx/<model>` (Path A) or
  `mlx:<model>` (Path B).

## Lessons from the v1 build (apply them)

- **Family resolution MUST go through `priors.py`** (address→family via `matches`), NOT
  substring-match on pricing keys — `estimate.py` and `usage.py` were both bitten (paid
  models priced $0 → budget hard-stop silently ineffective; both now take `--priors-dir`).
  Add an `mlx-local` family (free) to `pricing.json` + a `scripts/council/priors/
  mlx-local.json` (matches e.g. `["opencode:mlx/","mlx:"]`, humble ~0.40–0.55 priors —
  quality is genuinely unknown until this audit).
- **Cost model is metered-API-equivalent.** MLX is a genuine $0 (local, no egress) — the
  comparison's headline. See memory `model-council-cost-framing`.
- **`assess.sh` bash gotchas already fixed** (don't reintroduce): `IFS=$'\t' read`
  collapses empty middle TSV fields → use `awk -F'\t'`; `python3 -c` one-liners need
  `import sys`; empty-`status` poll guard; resume back-fills `SPENT`.
- **MLX is slow** → background `assess.sh` and poll; generous timeouts; the live compare
  will take real wall-clock (weight load + inference).
- **Gate every step on the 313 substrate + council suites staying green.** Adapter/mock
  tests use the mock-CLI pattern (no weights, no tokens). Zero debt (`./tmp` not `/tmp`;
  no TODO/FIXME). Commit trailer: `Co-Authored-By: Claude Opus 4.8 (1M context)
  <noreply@anthropic.com>`.

## Deliverables

1. **Path-A smoke test** — `mlx_lm.server` one 7B model + opencode `mlx` provider config
   resolving under our read-only posture (the DF4 wrinkle); one assess turn against
   `opencode:mlx/<model>` returns a scored row.
2. `mlx-local` family in `pricing.json` (free) + `priors/mlx-local.json`.
3. **The gated live comparison** (user-authorised): assess 7B + 14B (+ 32B stretch on a
   reduced dim set) + a hosted anchor at `--max-concurrent 1` → a **local-vs-hosted
   roster** (grade / $0 / latency); then a Diff+Synthesis with a local + hosted member on
   our own code. Record in `retrospectives/232-external-agent-delegation.md`.
4. Decide on Path B (dedicated `mlx` adapter + mock + `test-extdel-mlx-resume.sh`) based
   on whether MLX earned its seat.

## Immediate next step

`uv venv --seed && uv pip install mlx-lm`; download a Qwen2.5-Coder-7B-Instruct-4bit;
`uv run mlx_lm.server ... --port 8080`; add the opencode `mlx` provider and confirm it's
picked up under our per-handle `OPENCODE_CONFIG` (the DF4 precedence check) with one
`opencode:mlx/<model>` assess turn. THEN wire `mlx-local` priors/pricing and run the
gated live comparison at concurrency 1. Verify each step yourself; delegate mechanical
execution to Sonnet with the 313-test gate enforced.
