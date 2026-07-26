# RESTART PROMPT — `sdlc-model-council`: add a local **MLX** backend (#232 follow-on)

Paste into a fresh session to resume. Self-contained; read the pointers before writing code.

---

## Mission (one line)

Add a **local MLX backend adapter** to `sdlc-model-council` so Apple-Silicon-hosted
LLMs (addresses `mlx:<model>`) join the same **roster** and **fan-out plays** as the
hosted fleet (codex, agy, opencode) — turning the council into a **local-vs-hosted
comparison**: does a $0, no-egress, fully-private local model grade well enough on the
assessment to earn roster roles (e.g. a privacy-preserving reviewer) against the paid
hosted models? That's the payoff — prove or disprove it with real numbers.

## Where we are (as of 2026-07-25)

- **model-council v1 is BUILT and shipped in PR #233** (`feature/external-agent-delegation` → `main`), **CI green, mergeState CLEAN, mergeable**. 9 commits; 681 tests (368 council + 313 substrate). Check whether #233 has MERGED:
  - If merged → branch the MLX work off `main` (`git checkout main && git pull && git checkout -b feature/model-council-mlx`).
  - If not merged → either wait, or branch off `feature/external-agent-delegation` (the MLX adapter is additive — one new directory — so it rebases cleanly).
- **What v1 ships (build ON this, don't rebuild):** the adapter engine (`extdel.sh` + `turn-supervisor.pl`) with 3 adapters (codex, agy, opencode); the council layer under `plugins/sdlc-model-council/scripts/council/` — `assess.sh` (assessment: estimate gate → free wave-0 → paid waves w/ budget hard-stop + resume + timeout), `roster.py`/`diversity.py`/`cast.py` (arithmetic), 4 scorers, `play.sh` (Diff+Synthesis spine) + `council-judge` agent; 5 commands; the `council-policy` skill; priors + pricing.
- **The whole point of the adapter architecture is THIS task:** "adding a backend = one directory, zero engine edits." MLX is the third-party proof of it (opencode was the first live proof). If you touch `extdel.sh` or `turn-supervisor.pl`, you're doing it wrong.

## Read these first (in order)

1. `plugins/sdlc-model-council/docs/ADAPTER-AUTHORING.md` — **the authoritative how-to** for a new adapter (the ABI, the one-directory rule, the mock-CLI test pattern).
2. `plugins/sdlc-model-council/scripts/adapters/opencode/{adapter.json,adapter.sh}` — the **best template**: config-driven, non-native answer file (extracts the answer itself before the engine reads it), id-capture from a stream, binary off the default PATH. MLX will resemble it.
3. `docs/superpowers/specs/2026-07-24-sdlc-simple-orchestration-design.md` §2 (adapter interface/ABI), §4 (registry + `list-backends`).
4. `retrospectives/232-external-agent-delegation.md` — the full v1 history + the "Open follow-ups (from the live slice)" section that names this MLX task, plus the hard-won lessons below.

## Ground-truth facts (probed 2026-07-25 — don't re-derive)

- **Machine:** arm64 (Apple Silicon) — MLX runs natively.
- **MLX LLM tooling is `mlx-lm`, and it is NOT pre-installed** (system `python3` has neither `mlx_lm` nor `mlx.core`). It IS installable. **Per the user's Python policy (global `~/.claude/CLAUDE.md`): never global pip — use a project `.venv` via `uv`.** So: `uv venv --seed` (or reuse a repo `.venv`) then `uv pip install mlx-lm`, and invoke via `uv run mlx_lm.generate ...` or the venv's console scripts. Models come from `mlx-community/*` on HuggingFace (first run downloads weights — slow, several GB).
- **Two invocation modes:** (a) one-shot `mlx_lm.generate --model <hf-id> --prompt <text> [--max-tokens N]` → prints generated text to stdout (no session); (b) `mlx_lm.server` → an **OpenAI-compatible HTTP** server on localhost (has sessions/streaming). The council's assessment items and Diff+Synthesis are **single-turn**, so **start with one-shot** — simpler, no server lifecycle. (A server mode is a possible `kind:http-server` fast-follow, out of scope.)
- **`jack-tar-mlx` plugin exists but is IMAGES (mflux), not LLM** — reference only for MLX/venv patterns, not reusable for text.
- **Adapter grammar:** `^[a-z][a-z0-9]*` — `mlx` is valid. Address form `mlx:<model>` (e.g. `mlx:mlx-community/Qwen2.5-Coder-7B-Instruct-4bit`); slashes are fine in the model part per the address grammar `[A-Za-z0-9./_-]+`.
- **Engine timeouts + submit-then-poll:** local inference (esp. first load + long prompts) is SLOW — use generous item `timeout_s` and rely on the engine's perl-alarm timeout + `status --wait-s` polling (the Bash tool caps at 600s → `assess.sh` already backgrounds/polls).

## The adapter to build (the crux)

`scripts/adapters/mlx/{adapter.json, adapter.sh}` implementing the ABI (see ADAPTER-AUTHORING + opencode as template). Decisions to make up front:

- **`kind: direct-cli`**, `binary` = however you invoke mlx-lm from the venv (probe: a wrapper, or `uv run` — resolve a stable, PATH-independent invocation like opencode's `~/.opencode/bin` handling; MLX has no fixed binary, so `adapter_detect` likely checks `python -c "import mlx_lm"` in the venv / a resolvable `mlx_lm.generate`).
- **`session_resume: false`** (one-shot). The assessment + plays are single-turn, so turn-1-only is fine. Make turn-N (resume) a clean `ERROR` (like the "held mode" adapters do), NOT a hang. Confirm the engine tolerates a `session_resume:false` adapter for the single-turn assessment/play paths (it should — assessment never resumes; `play.sh` fan-out is one turn per member).
- **`postures`:** local generation gives the model **no disk/network access at all** — it just emits text. So `read-only` is trivially `hard` (there's nothing to gate). No `--gemini_dir`/`OPENCODE_CONFIG`-style graded config needed; document that plainly in the descriptor `notes`.
- **answer extraction:** mlx_lm.generate prints the completion to stdout (possibly with a stats/prompt echo header/footer). The adapter must isolate the actual generated text into `turn-001.last-message.txt` (like opencode's non-native `answer_file` handling — `answer_file_native:false`). Probe the exact stdout shape and strip the framing.
- **cost/usage:** `$0`, local. Add pricing family **`mlx-local`** (`free:true`) and `scripts/council/priors/mlx-local.json` (matches `["mlx:"]`, humble priors ~0.40–0.55 across dims + a `no-track`/`local` flag — quality is genuinely unknown until audited; that's the investigation). `usage.py` already meters non-cost adapters as estimated/$0 — confirm `mlx` falls through to $0 cleanly (it has no events.jsonl cost; tokens can be estimated from chars, basis "estimated").

## Deliverables

1. `scripts/adapters/mlx/adapter.json` + `adapter.sh` (the adapter; zero engine edits — that's the acceptance test).
2. `tests/fixtures/mock-bin/mlx` (a mock `mlx_lm.generate`-shaped CLI, no real weights) + `tests/test-extdel-mlx-resume.sh` (mirror `test-extdel-opencode-resume.sh`: start/status/slice/stop over the mock, id/one-shot behavior, `session_resume:false` → ERROR-not-hang). This proves "one directory, zero core edits."
3. `scripts/council/priors/mlx-local.json` + a `mlx-local` family in `scripts/council/pricing.json` (free).
4. Registration touch-ups: `list-backends` should detect `mlx` (it enumerates `adapters/*/adapter.json` — free); update `docs/ADAPTER-AUTHORING.md`'s worked-examples list; `AGENT-INDEX`/marketplace unaffected (no new agent).
5. **The comparison run (gated live, user-authorised):** install 2–3 small MLX coder models (e.g. a Qwen2.5-Coder-7B-4bit, a Llama-3.x-8B-4bit — pick from `mlx-community`), run `assess.sh` over {those MLX models} ∪ {a hosted anchor or two} on the 4 objective dims, and produce a **roster comparing local vs hosted** (grades + $0 cost + latency — local will be slower but free/private). Then a Diff+Synthesis mixing a local + a hosted member. Record in the retrospective: do local models earn roster roles? at what latency? is a local reviewer viable?

## Hard-won lessons from the v1 build (apply them)

- **Family resolution MUST go through `priors.py`** (address→family via `matches` substrings), NOT substring-match against pricing keys. `estimate.py` AND `usage.py` were both bitten by this (paid models priced at $0 → budget hard-stop silently ineffective). Both now take `--priors-dir`. Your `mlx-local` priors need a `matches:["mlx:"]` entry so `mlx:...` resolves. (For MLX it's $0 anyway, but keep it consistent.)
- **The cost model is metered-API-equivalent.** MLX is genuinely $0 marginal (local) — a real, not just proxy, zero. That's the comparison's headline (privacy + $0 vs paid hosted).
- **`assess.sh` bash gotchas already fixed** (don't reintroduce): `IFS=$'\t' read` collapses empty middle TSV fields (use `awk -F'\t'`); `python3 -c` one-liners need `import sys`; the empty-`status` poll guard; resume back-fills `SPENT`. If you extend assess.sh, respect these.
- **MLX is slow** → the live comparison will take real wall-clock (weight load + inference). Background `assess.sh` and poll; set item `timeout_s` generously for the MLX run (a per-model timeout override on assess.sh may be worth adding — currently timeouts come from item.json).
- **Gate every step on the 313 substrate + the council suites staying green.** Adapter tests use the mock-CLI pattern (no real weights, no tokens). Zero technical debt (`./tmp` not `/tmp`; no TODO/FIXME). Feature branch only; never commit to `main`. Commit-message trailer: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.
- **Dogfood:** once the MLX adapter works, run a Diff+Synthesis with a local MLX reviewer in the panel on our own code — the ultimate "is a private local model good enough" test.

## Immediate next step

Confirm #233's merge state and branch accordingly. Then: probe `mlx-lm` one-shot output shape in a `.venv` (`uv pip install mlx-lm`; run `mlx_lm.generate` on a tiny model), author the `mlx` adapter + mock + test against that shape (gated by the 313 substrate tests), wire the `mlx-local` priors/pricing, and only then do the gated live local-vs-hosted comparison. Verify each stage yourself; delegate mechanical execution to Sonnet with the test gate enforced.
