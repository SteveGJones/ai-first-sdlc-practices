# RESTART PROMPT — `sdlc-model-council`: assess **tool-use & command-line execution** (#235)

Paste into a fresh session to resume. Self-contained; read the pointers before writing code.

---

## Mission (one line)

Add a **tool-use / command-line-execution** capability to the council assessment
and run a **local-MLX vs Haiku-4.5 vs hosted-fleet** comparison — turning the
un-audited `tool-use` prior (0.42 placeholder) and the *extrapolated* "Haiku
should win command execution on latency × tool-call reliability" answer into
**real, measured numbers** (grade / task-success / turns-to-success / latency / $).

## Where we are

- **Issue #235** raised (follow-on to #232 / PR #234). Branch
  **`feature/council-tool-use-assessment`** (pushed). **Scaffolding only — no
  implementation yet.**
- Committed on the branch: the **feature definition**
  `docs/feature-proposals/235-council-tool-use-assessment.md` and the
  **retrospective** `retrospectives/235-council-tool-use-assessment.md`. Read the
  proposal first — it holds the scope, the recommended design stance, and the
  open questions.
- **model-council v1 (PR #233) + local-MLX backend (PR #234) are MERGED to
  `main`.** This feature builds directly on them. Never commit to `main`; feature
  branch only.

## Read these first (pointers)

- `docs/feature-proposals/235-council-tool-use-assessment.md` — this feature's scope.
- `retrospectives/232-external-agent-delegation.md` — the full council + MLX story,
  incl. the live comparison, the Path-A/Path-B fairness lesson, and the SDLC/CI
  gotchas (all directly relevant).
- `plugins/sdlc-model-council/scripts/council/` — the assessment layer.
- `plugins/sdlc-model-council/assessment/stack/v1/` — the problem stack you'll extend.
- `plugins/sdlc-model-council/scripts/adapters/mlx/` — the Path-B MLX adapter (text-only).
- `plugins/sdlc-model-council/docs/ADAPTER-AUTHORING.md` — if a new adapter is needed
  (e.g. a `claude`/Haiku adapter).

## What the capability needs (why it's different from v1)

The v1 stack grades **static, single-turn** dims (code-review, bug-fix,
long-context, instruction-format). Tool use / command execution is **agentic**:
emit a command/tool call → observe output → decide → iterate → **know when to
stop** (monitoring). It stresses tool-call **format validity**, **reasoning over
observations**, and **stop-condition judgment** — none of which v1 measures.

## Recommended approach — **propose-and-score** (the proposal's design stance)

Default to a **deterministic propose-and-score contract with NO live shell**:
give the model a goal + a *simulated* terminal transcript; it emits the correct
next command(s) / decision; score deterministically against a golden command set
/ decision. This (a) is safe + reproducible, (b) isolates **model capability**
from harness plumbing, and (c) keeps elicitation **uniform** — a single prompt,
**no agentic system prompt** (the #234 fairness lesson: OpenCode's system prompt
corrupted small-local-model output; send only the item prompt). Real sandboxed
execution is an **opt-in stretch**, gated behind explicit authorisation.

**Decide up front (open questions in the proposal):**
1. One `tool-use` dimension, or split `command-exec` (produce the right command
   for a goal) vs `monitoring` (given a stream, decide continue/stop + when the
   condition fires)? Leaning: start with items under a single `tool-use` dim; split
   only if the data shows they grade differently.
2. **How to reach Haiku for an apples-to-apples harness.** There is **no Claude
   adapter** in the council today (adapters are codex/agy/opencode/mlx). For
   propose-and-score, elicitation is one prompt → answer → deterministic score, so
   Haiku can be reached either by a **new minimal `claude` adapter** (see
   ADAPTER-AUTHORING.md) or by a direct Claude API call in a comparison harness.
   Pick one and keep every model on the identical prompt + scorer.

## How the council works (ground-truth — don't re-derive)

**Assessment stack** — `assessment/stack/v1/stack.json` lists items; each item dir
has `item.json` + `prompt.md` (+ `inputs/`, `expected/`). `item.json` fields:
`id, dimension, version, difficulty, timeout_s, min_context_tokens,
est_prompt_tokens, est_output_tokens, answer_contract, scorer.type`.
- `answer_contract` ∈ `text | file-blocks | findings-json | strict-json |
  verdict-line` — parsed by `scripts/council/extract_answer.py` (the SINGLE source
  of truth; scorers import it, never re-parse). A command-exec item likely uses
  `verdict-line` / `strict-json` for the emitted command(s)/decision, or a **new
  contract** if needed.
- `scorer.type` ∈ existing `hidden-tests | exact-match | format-parse |
  planted-defects` (`scripts/council/score/<type>.py`). A command-comparison
  scorer is probably a **new type** (normalise + compare commands / decisions).

**Scorer ABI** — `score/<type>.py <item_dir> <answer_file> <workdir>` writes
`<workdir>/score.json` = `{score: float, status: str, details: {...}}`, and MUST
**always exit 0** (use `os.makedirs(workdir, exist_ok=True)` in `write_score` —
this bit the v1 scorers). Stdlib only. Add golden cases to
`tests/test-council-scorers.sh`; items are linted by
`tests/test-council-stack-lint.sh` (add the new item shas to `stack.json`).

**Priors + grades** — `scripts/council/priors.py` resolves an address
`adapter:model[@effort]` to a family by **longest matching `matches` substring**;
`priors/<family>.json` has a `dimensions` map (add a real `tool-use` value per
family; `mlx-local`'s is a 0.42 placeholder to REPLACE with audition data).
`scripts/council/roster.py`: `posterior = (n·raw_mean + 3·prior)/(n+3)`; grades
**A≥0.85, B≥0.65, C≥0.45**, else D. Consider adding `tool-use` to `CORE_DIMS` /
role logic if it should drive roles.

**Run an assessment / comparison** (from repo root — `./tmp` matters):
```bash
C=plugins/sdlc-model-council/scripts/council
MLX_BASE_URL="http://127.0.0.1:8081/v1" bash "$C/assess.sh" \
  --stack plugins/sdlc-model-council/assessment/stack/v1/stack.json \
  --priors-dir "$C/priors" --pricing "$C/pricing.json" \
  --models "mlx:mlx-community/Qwen2.5-Coder-14B-Instruct-4bit" \
  --dims tool-use --max-concurrent 1 --run-dir ./tmp/model-council/tu-14b
```
Paid models (Haiku, hosted fleet) need `--budget-usd`. Merge per-model
`results.jsonl` → `roster.py --results <merged>` + `diversity.py` for the
side-by-side roster (grade / $ / p50-latency) — exactly how #234's comparison was
built (see the 232 retrospective for the worked example).

## The 32 GB MLX environment (already set up in #234)

- arm64, 32 GB. Repo `.venv` (gitignored) has `mlx-lm`. Qwen2.5-Coder-**7B/14B/32B**
  `-Instruct-4bit` are cached in `~/.cache/huggingface`. Start a server per model:
  `uv run mlx_lm.server --model <hf-id> --port 8081` (OpenAI `/v1`).
- **Concurrency = 1** (one server, 32 GB can't hold two large models) → MLX runs
  **sequentially**; swap the server's loaded model between passes (it load-switches
  on the request `model` field). **Generous timeouts** — local is slow (14B hit
  293s on a long-context item; 32B ~161s on a bug-fix item).
- The Path-B `mlx` adapter (`scripts/adapters/mlx/`) is **text-only, no tools** —
  it injects `stop` itself (no proxy needed) and sends only the item prompt. The
  `tmp/mlx-stop-proxy.py` shim is Path-A (opencode) only. For a **real-execution**
  tool-use mode you would need a tool-wired harness — out of scope for the
  propose-and-score default.

## Immediate next step

Invoke `superpowers:writing-plans-and-specs` (or the `Plan` subagent) to lock the
**scoring contract + item schema + metrics** for the propose-and-score dimension,
and resolve the two open questions (single-vs-split dim; how to reach Haiku).
THEN, TDD (`superpowers:test-driven-development`): author the scorer + 3–5
deterministic command-line-execution / monitoring items with golden answers, wire
the `tool-use` dim into `stack.json` / priors / roster, keep the **15-file council
suite green**, and run the gated comparison (MLX 7B/14B/32B + **Haiku 4.5** +
hosted fleet). Re-derive the `tool-use` prior from the audition; record in the
retrospective.

## Deliverables

1. Design spec (scoring contract, item schema, metrics) — the two open questions
   resolved.
2. New scorer + 3–5 items + stack/priors/roster wiring; council suite green; zero debt.
3. The **gated comparison** with **Haiku 4.5 as an anchor** → a tool-use roster
   (grade / task-success / turns-to-success / latency / $) answering "how do local
   models compare with Haiku for command-line execution and monitoring?".
4. Audition-derived `tool-use` priors replacing the placeholders; findings in
   `retrospectives/235-council-tool-use-assessment.md`.

## Lessons from #234 to apply

- **Fairness:** single item prompt, **no agentic system prompt** — that's the whole
  reason Path B exists. Keep every model on the identical elicitation + scorer.
- **SDLC/CI:** the branch already has a branch-named proposal + retrospective, so
  the PR-gated `Feature Proposal Check` / `Retrospective Check` will pass (they
  derive expected artifacts from the branch name; #234 initially failed because it
  reused the #232 names). `validation.yml` is informational-only (main is red on
  it); the real fatal steps are those two PR-gated checks. **Never** use `--admin`
  / `--force` / branch-protection bypass — report a block and ask.
- **Gate every step on the council suite staying green** (`plugins/sdlc-model-council/
  tests/*.sh`, incl. the slow `test-extdel-*-resume.sh`). Adapter/mock tests use the
  mock-CLI pattern (no weights, no tokens). Zero debt (`./tmp` not `/tmp`; no
  TODO/FIXME). Run `pre-commit` (installed via `uv tool`) — it auto-normalises JSON
  (`pretty-format-json`) + Python (`black`); re-stage its fixes.
- **Cost framing:** MLX is genuine $0; hosted/Haiku $ are metered-API-equivalent
  (subscription users read $/item as a usage proxy). See memory `model-council-cost-framing`.
- **Verify yourself; delegate mechanical execution** to Sonnet with the test gate
  enforced. Commit trailer:
  `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.
