# RESTART PROMPT — `sdlc-model-council` v1 build (#232)

Paste this into a fresh session to resume. It is self-contained; read the three specs it points to before writing code.

---

## Mission (one line)

Build **`sdlc-model-council`** — a Claude Code plugin that onboards the AI models reachable on this machine (via `codex`, `agy`, `opencode` CLIs, which are *gateways* to 19+ models) by **assessing them against a standardized problem stack**, casting them into roles from the results (a **roster**), and running **cross-model fan-out plays** (diff+synthesis, consensus, best-of-N, generator↔verifier) chosen **per project** from that roster.

This is a **pivot**, made after an honest self-assessment: as a "delegate one task to one CLI" tool we were near-needless (the official `codex-plugin-cc` and community `antigravity` plugins already wrap their vendors better). The defensible product is **cross-model orchestration** — the one thing no per-vendor plugin does. The whole design is instrumented to **prove or disprove its own value** (see "measurability" below).

## Where we are

- **Repo:** `/Users/stevejones/Documents/Development/ai-first-sdlc-practices` · **Branch:** `feature/external-agent-delegation` · **Issue:** #232 · never merge to `main`; feature branches only.
- **Committed & pushed:** the full design trail + a working substrate. Latest commit is the model-council architecture design.
- **The substrate exists and is green:** `plugins/sdlc-simple-orchestration/` — the adapter engine (`extdel.sh` + `turn-supervisor.pl`), unified return contract, `list-backends`, graded postures, and **3 working adapters** (codex, agy, opencode). **313 tests pass**, zero technical debt.
  - Run them: `cd <repo>; P=plugins/sdlc-simple-orchestration; for t in test-extdel-codex-resume test-extdel-agy-resume test-extdel-opencode-resume test-turn-supervisor test-adapter-descriptors test-list-backends; do bash $P/tests/$t.sh 2>&1 | tail -1; done` (codex 67, agy 104, opencode 69, supervisor 14, adapter-descriptors 28, list-backends 31). The agy suite is slow (~2 min) — run it in the background.
- **Nothing of the council layer is built yet.** We are at migration **stage 0**, about to start **stage 1** (the rename).

## Read these first (in order)

1. `docs/superpowers/specs/2026-07-25-sdlc-model-council-charter.md` — vision + **locked decisions**.
2. `docs/superpowers/specs/2026-07-25-sdlc-model-council-design.md` — **THE ARCHITECTURE; authoritative for the build.** Assessment harness, scorer ABI, roster+diversity math, the 4 plays, policy+commission, cost model, reuse/rename/new map, **migration order**, v1 slice, testability, risks.
3. `docs/superpowers/specs/2026-07-24-sdlc-simple-orchestration-design.md` — the **substrate** you build ON (engine, §4.2 contract, adapters, `list-backends`). Kept unchanged.
4. `retrospectives/232-external-agent-delegation.md` — full history, decision log, and the two dogfood findings (DF1 validated; DF4 = OpenCode hardening follow-ups).

## Locked decisions (do not relitigate)

- **Name:** `sdlc-model-council` (rename from `sdlc-simple-orchestration`).
- **v1 patterns:** all four plays designed; **v1 slice builds only Diff+Synthesis** end-to-end first.
- **Rating source:** static priors + optional live audition (priors = k=3 pseudo-observations shrunk toward by audition evidence; "skip audition" = priors only, n=0). Adaptive learning is a fast-follow.
- **Policy/roster live in `.sdlc/model-council/`** (project config, not KB).
- **Council arithmetic = Python 3 stdlib only** (no pip/venv); choreography = bash 3.2.
- **codex Mode B (app-server per-action approval) is CUT** — superseded by this pivot (banner in its spec). Do not build it.

## Migration order (design §7 — tests green at each ⭐ step)

- ⭐**1. Rename:** `git mv plugins/sdlc-simple-orchestration plugins/sdlc-model-council`; sed state dir `tmp/simple-orchestration → tmp/model-council` and `sdlc-simple-orchestration → sdlc-model-council`; update `plugin.json` name/desc. Delete the stale `known_engine_limitation` note in `scripts/adapters/opencode/adapter.json` (validate_handle is already generalized). **All 313 tests green from the new path.** (This mirrors the v0.1.0 rename; do it carefully — BSD `sed -i ''`, and `grep -rl ... | while read f; do sed -i '' ... "$f"; done`, NOT `xargs -0`.)
- ⭐**2. Council scripts + problem stack + unit tests** (no commands yet — everything runnable as `bash`/`python3` directly): `scripts/council/*.py` (schedule, extract_answer, usage, estimate, roster, diversity, cast, complexity), `scripts/council/score/*.py` (the scorer ABI), `priors/*.json`, `pricing.json`, `assessment/stack/v1/` (9 objective items for the slice), and the scorer/roster/diversity **golden unit tests** with the mock answer-bank personas.
- ⭐**3. Mock-fleet assessment end-to-end** (`assess.sh` over mock adapters): waves, cap-5 concurrency, budget hard-stop, resume, timeout rows.
- **4. Commands + skill + agents:** `commands/{council-commission,council-assess,council-roster,council-run,council-estimate}.md`, reframe `orchestration-policy → council-policy` skill, add `agents/council-judge.md` (Sonnet, blind-label synthesis).
- **5. Registration:** update `.claude-plugin/marketplace.json`, `CLAUDE.md` plugin table, `AGENT-INDEX.md` (retarget `delegation-runner`, add `council-judge`).
- **6. ONE gated live slice:** `COUNCIL_LIVE=1` (free opencode models = $0 by default; paid requires explicit budget). Run the assessment → roster → **Diff+Synthesis** on a real decision (reviewing this feature's own PR). Record results in the retrospective.
- **7. Validation + release:** `python tools/validation/local-validation.py --pre-push`, `check-broken-references.py`, retrospective, PR.

## v1 vertical slice (what "done" means for the first milestone)

9 **objective, judge-free** items (code-review/planted-defects ×3, bug-fix/hidden-tests ×2, long-context/exact-match ×2, instruction-format/format-parse ×2) → a real **roster** over a 5-model cast (`codex:default@medium`, `agy:gemini-3.6-flash-medium`, `agy:gemini-3.1-pro-high`, two free opencode models — **no Claude-family**, so judge-bias machinery isn't yet load-bearing) → the **Diff+Synthesis** play run once, live, on a real decision, producing a Convergent/Divergent/Adjudication/**Baseline-delta** synthesis + a spend line. Everything deterministic-testable via mocks; the ONE live run is gated.

## The measurability spine (the point of the whole thing)

Every play keeps the roster's best single model as `baseline_member` in the cast; the synthesis must state whether the panel materially changed the outcome vs. that baseline; `outcomes.jsonl` accumulates. **Pre-committed rule:** if after ~20 real runs the panel helps in <20% of them, the honest product is roster-driven **single-model routing** (`/delegate` auto-pick, already a shipped path) — the fallback is a feature removal, not a rewrite. Build with this in mind; do not oversell fan-out.

## Ground-truth facts (hard-won by probing — don't re-derive)

- **Fleet:** codex 0.145.0 (GPT-5.x). `agy models` = 11 ids incl. `gemini-3.{1,5,6}-*`, `claude-sonnet-4-6`, `claude-opus-4-6-thinking`, `gpt-oss-120b-medium` — **agy bakes effort into the model id** (no `@effort`). `opencode models` = 7 incl. **6 free (`cost:0`)**. Model address = `adapter:model[@effort]`; `adapter:default` = gateway default.
- **macOS gotchas:** `setsid`, `timeout`, `gtimeout` are **ABSENT** (engine uses a perl `POSIX::setsid` daemonizer + perl-alarm; don't reintroduce them). `opencode` is at `~/.opencode/bin/opencode`, **off the non-interactive Bash PATH**. `/bin/sh` = bash 3.2 — no assoc arrays, no `${var,,}`.
- **Cost telemetry:** opencode `--format json` `step_finish` has exact tokens+cost; codex `--json` has tokens; **agy emits none → estimated (chars/4 × pricing, flagged)**. Engine doesn't aggregate — `usage.py` parses per-handle `events.jsonl` (zero engine edits).
- **Adapters:** codex = `codex exec [resume]`, `-s read-only|workspace-write`, `codex login status` works. agy = per-handle `--gemini_dir` config for **graded permissions** (DF1 fix — read-only that reads, workspace that writes, no blanket yolo); `--print` takes the prompt as its flag VALUE and must be **last**. opencode = `opencode run --dir --format json --session <id> -m <model>`; `sessionID` in every event; postures via `OPENCODE_CONFIG` per-handle permission file.
- **Sibling plugins installed** (for detection/routing): `codex@openai-codex` and `antigravity@antigravity-for-claude-code` (manifest v2 at `~/.claude/plugins/installed_plugins.json`). `list-backends` already detects them.
- **Harness:** Bash tool times out at **120 s default / 600 s cap** → the engine uses **submit-then-poll** (`start` returns `RUNNING` immediately; `status --wait-s N` polls). Respect this in council choreography. State lives under `./tmp/...` (gitignored). `validate_handle` is already generalized to any `[a-z][a-z0-9]*` adapter id.

## Working practices (this project's rhythm)

- **Delegation tiers:** you (main) are **Opus 4.8**. Delegate **complex architecture + reviews to Fable** (`model: fable`), **execution to Sonnet**, and the shipped wrapper agents run on **Haiku**. Dispatch via the Agent tool, `run_in_background: true`; verify their output yourself — never trust blind.
- **Gate every stage on the 313 substrate tests** staying green (they are the behaviour-preserving regression harness).
- **Adversarial review before commit** on anything security/correctness-sensitive (a Fable code-review caught a BLOCKER + false-SUCCESS bug in `turn-supervisor.pl`; two independent Fable passes each found a distinct defect — review the *fix*, not just the original).
- **Dogfood:** use the delegation we ship to review our own code — it found real bugs (codex flagged 2 CRITICALs in the OpenCode adapter; agy validated DF1 by producing a real review). This spends real OpenAI/agy quota — the user has authorised it for reviews; free opencode models cost $0.
- **Zero technical debt:** no TODO/FIXME/commented-out code; `./tmp` not `/tmp`; run `python tools/validation/check-technical-debt.py --threshold 0 <plugin>`.
- **Commit style:** feature branch only; end commit messages with `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`. Update the retrospective as you go.

## Open follow-ups (parked, not blocking the council build)

- **DF4 — OpenCode adapter hardening** (from the codex+agy dogfood): CRITICAL — `OPENCODE_CONFIG` is *lower* precedence than a target repo's own `opencode.json` (a project config can override our read-only denies → use higher-precedence `OPENCODE_CONFIG_CONTENT`); CRITICAL — project `.opencode/plugins` auto-load = code exec under read-only; plus HIGH (unspecified tools default-allow → `"*":"deny"`+allowlist; `bash:allow` bypasses webfetch via curl) and agy MEDIUMs (`jq -rs` fails on any non-JSON line; missing `local` in a *sourced* adapter pollutes the engine). Verify each against our actual `./tmp` state-dir layout (some HIGHs may be false positives). Address when the OpenCode model matters to a live council run.

## Immediate next step

Start migration **stage 1** (the rename), gated by the 313 tests. Then stage 2 (council scripts + the 9-item stack + scorer/roster golden unit tests). Build in gated stages, delegate execution to Sonnet with the 313-test gate enforced, verify each stage yourself, and check in between stages.
