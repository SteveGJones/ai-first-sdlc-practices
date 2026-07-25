# Architecture Design: `sdlc-model-council` — cross-model fan-out with a team-onboarding assessment

**Issue:** #232 · **Branch:** `feature/external-agent-delegation` · **Status:** Architecture design v1 (Fable-tier), for implementation · **Date:** 2026-07-25
**Designs to:** `2026-07-25-sdlc-model-council-charter.md` (authoritative vision + locked decisions).
**Builds on (unchanged substrate):** `2026-07-24-sdlc-simple-orchestration-design.md` — the adapter engine (`extdel.sh` + `turn-supervisor.pl`), unified §4.2 return contract, `list-backends`, graded postures, one-directory adapters, 313 mock-only assertions across 6 suites.

**Ground truth (2026-07-25, read-only probes):** codex 0.145.0 (GPT-5.x). `agy models` → 11 ids incl. `gemini-3.{1,5,6}-*`, `claude-sonnet-4-6`, `claude-opus-4-6-thinking`, `gpt-oss-120b-medium` (**agy bakes effort into the model id**). `opencode models` → 7 ids incl. **6 free** (`cost:0`). Fleet = 19+ `(adapter,model)` pairs. Cost telemetry: opencode `step_finish` carries exact tokens+cost; codex `--json` carries tokens; **agy emits none → estimated**. Engine does not aggregate usage — that's a council-layer parser over per-handle `events.jsonl`, zero engine edits. `validate_handle` is already generalized to any adapter id (stale `known_engine_limitation` note in opencode's adapter.json must be deleted during rename — docs-only).

---

## 1. Overview — choreography + arithmetic ABOVE the engine

Nothing here edits `extdel.sh`, `turn-supervisor.pl`, or adapter behavior. Every external-model call (assessment items and play members alike) is `extdel.sh start|status|slice|stop --cli <adapter> --model <id> --posture read-only`, returning the same unified block + per-handle `./tmp/model-council/<handle>/` state the 313 tests pin.

```
caller (main Claude)
  ├── skills/council-policy         routing + plays + budget rules (reframed orchestration-policy)
  ├── commands/council-commission   discover fleet → characterize → (opt) audition → roster + policy
  ├── commands/council-assess       run/resume the problem stack across N models under a budget cap
  ├── commands/council-roster       render/inspect roster, diversity, staleness
  ├── commands/council-run          execute a play per policy (v1: diff-synthesis only)
  ├── commands/council-estimate     dry-run cost estimator (no tokens)
  ├── commands/{delegate,backends}  KEPT (single-model)
  ├── agents/delegation-runner (Haiku)  KEPT — one per fan-out member
  ├── agents/council-judge (Sonnet)     NEW — file-reading synthesis/judge, blind labels
  └── scripts/ extdel.sh + turn-supervisor.pl + adapters/{codex,agy,opencode}/   ← SUBSTRATE, UNCHANGED
             council/*.py + assess.sh                                            ← NEW (stdlib Python + bash)
  assessment/stack/v1/          shipped problem stack (versioned)
  .sdlc/model-council/          project-local: roster.json, policy.json, commission.json, outcomes.jsonl
  ./tmp/model-council/          runtime state
```

**Layering invariant:** engine knows nothing of model quality/budgets/plays; council layer knows nothing of spawn/session mechanics. Sole interface = the extdel.sh CLI + per-handle dir contents (`last-message.txt`, `events.jsonl`, `meta.json`, exit codes). **All council arithmetic is Python 3 stdlib-only** (no pip/venv); choreography is bash-3.2.

**Canonical model address:** `adapter:model[@effort]` — `codex:default@medium`, `agy:gemini-3.6-flash-low` (effort in id, no `@`), `opencode:opencode/deepseek-v4-flash-free`. Grammar `^[a-z][a-z0-9]*:[A-Za-z0-9./_-]+(@(low|medium|high))?$`; `adapter:default` = gateway default (omit `--model`). This string is the key in every results/roster/policy file.

---

## 2. Onboarding assessment harness

### 2.1 Problem-item format
```
assessment/stack/v1/
  stack.json                       # {stack_version, items:[{id,dimension,path,sha256}]}
  items/<dim>/<item-id>/
    item.json                      # metadata + scorer spec
    prompt.md                      # {{INPUT:name}} splices; ends with the harness ENVELOPE for its contract
    inputs/                        # shown to the model
    expected/                      # NEVER shown: hidden tests, defect list, needle answer, rubric
```
`item.json`: `{schema_version, id, dimension, version, difficulty, timeout_s, min_context_tokens, est_prompt_tokens, est_output_tokens, answer_contract, scorer:{type,...}}`. `answer_contract` ∈ `text|file-blocks|findings-json|strict-json|verdict-line`; prompt.md ends with the standard envelope for its contract (e.g. file-blocks → "Respond with ONLY ```file:NAME``` fenced blocks"). `scripts/council/extract_answer.py` parses `last-message.txt` per contract; parse failure → score 0, `status:"contract-fail"` (distinct from "wrong"). **Assessment always runs `--posture read-only`** — models never touch disk; the harness materializes returned `file:` blocks into scratch and runs scorers locally (makes tool-use/agentic a deferred dim needing a workspace sandbox). Hidden tests are **stdlib `unittest`** (zero installs).

### 2.2 Versioning & extensibility
Every result row records `stack_version` + item `sha256`; **scores from different hashes of the same item id are never averaged** (editing an item visibly invalidates comparability). Project add-ons: `.sdlc/model-council/stack-addons/` (same format; id collision → hard error) let a project audition on its own code shapes. `docs/COUNCIL-STACK-AUTHORING.md` + `tests/test-stack-lint.sh` (schema, referenced files exist, scorer type known, envelope present). Items are **original, private, small** (never public-benchmark copies — leakage).

### 2.3 Scorer plug-in ABI (parallel to the adapter ABI)
```
scripts/council/score/<type>.py  <item-dir> <answer-file> <workdir>
  → writes <workdir>/score.json {"score":0.0–1.0,"status":"scored|contract-fail|error","details":{…}}; exit 0
```
Deterministic, hermetic, token-free EXCEPT `judge-rubric`:

| type | dims | mechanics | score |
|---|---|---|---|
| `hidden-tests` | code-gen, bug-fix | materialize file-blocks → run stdlib unittest | passed/total |
| `planted-defects` | code-review | match `findings-json` to `expected/defects.json` by file+line-window OR `match_any` regex; ignore beyond `max_findings_counted` (anti-shotgun) | F1(recall,precision) |
| `exact-match` | long-context | normalize → compare `expected/answer.txt` | 1/0 |
| `format-parse` | instruction/format | `json.loads` + mini schema-check vs `expected/schema.json` | fraction of constraints |
| `behavior-complexity` | refactor | hidden tests pass (gate) AND ast branch-count drop vs baseline | 0.7·tests+0.3·drop |
| `cited-fact` | research | required facts present + citation matches domain pattern | valid/total |
| `judge-rubric` | reasoning/architecture | judge subagent, weighted criteria | weighted mean |

**Judge-bias containment (enforced by harness, not convention):** (1) objective-first is structural — 7/9 dims have non-judge scorers; (2) **blind grading** — judge receives answers with model address stripped→random label, re-joined after; (3) **family-conflict rule** — primary judge is orchestrator (Claude-family); if candidate is Claude-family, a **cross-family second judge** (from the fleet, cheapest reachable) is mandatory, final = mean, |Δ|>threshold → `flagged:"judge-disagreement"`, dimension provisional; (4) provenance — roster renders "(judge-scored)" next to any judge-influenced grade.

### 2.4 Run model
`council-assess models=… dims=… budget-usd=1.00 [--estimate] [--resume <run-id>]` → `assess.sh`:
1. list-backends --json → drop unreachable (recorded).
2. `schedule.py`: queue = models × items (filtered by dims + min_context vs prior context) → run dir with plan.json/results.jsonl.
3. **estimate gate**: `estimate.py` per-model table; `--estimate` stops here; live run REQUIRES `budget-usd` (no default-spend).
4. **wave-0 calibration = FREE models only** (cost 0): full item set → validates items+scorers against real behavior, floors scores, and **measures tokens/item to re-estimate paid waves before any paid token**.
5. paid waves, ≤5 concurrent handles: per (model,item) `extdel.sh start … --posture read-only --timeout-s item.timeout_s` → poll → `usage.py` (cost from events.jsonl) → `score/<type>.py` → append row → `stop`. Accumulated actuals ≥ budget → cancel pending paid, mark `skipped:budget` (resumable). TIMEOUT → score 0.
6. `roster.py` + `diversity.py` → artifacts; append `assessment-log.jsonl`.

Result row: `{model,item,dimension,stack_version,item_sha256,score,status,details,cost_usd,cost_basis:exact|metered|estimated,tokens_in,tokens_out,latency_s,handle,ts}`. `--resume` runs only missing pairs.

---

## 3. Roster & diversity

### 3.1 Scores, confidence, small-sample honesty
Per (model,dimension): `n, raw_mean, ci95 (=1.96·sd/√n), prior, posterior=(n·raw_mean + k·prior)/(n+k)` with **k=3 pseudo-obs** (audition evidence displaces prior smoothly; skip audition ⇒ posterior=prior, n=0). `grade` A/B/C/D on posterior (≥.85/.65/.45/else), **"provisional"** when ci95 width>0.35 or any judge-disagreement. No grade shown without its n. **Cost/latency kept separate, never blended into score** (`mean_cost_usd_per_item`, `p50_latency_s`).

### 3.2 Diversity map (objective items only)
Per model: outcome vector over common items (hidden-tests pass/fail; planted-defects found/missed **per defect**; exact/format 1/0). Per pair: `n_common, agree_rate, phi, both_wrong_rate = P(both wrong | ≥1 wrong)` (the shared-blind-spot measure). `n_common<6` → `insufficient`, treated as maximally correlated (pessimistic).
**Casting** (`cast.py`): pool = grade≥C, reachable, cost-feasible; start with argmax posterior; greedily add `argmax(posterior − 0.5·max_{c∈cast} both_wrong_rate(m,c))`; if k≥3 & tight budget ensure ≥1 free/cheap member; cast[0] = **baseline member** (§10 measurability).

### 3.3 Roster card + roles
`.sdlc/model-council/roster.json` (authoritative) + generated `roster.md`. Per model: reachable, gateway_version, context_tokens, pricing_ref, per-dimension {n,raw_mean,ci95,prior,posterior,grade,judge_scored}, cost, latency, **roles**, flags. `source: priors|priors+audition`. Role table (fixed rules in `roster.py`, not model-judged): `implementer` (code-gen&bug-fix ≥.65), `reviewer` (code-review ≥.65 AND precision ≥.5 — no shotguns), `verifier` (bug-fix ≥.65 AND instruction-format ≥.65), `researcher` (research ≥.65 — deferred), `long-context` (≥.85), `bulk` (any core ≥.45 AND cheap/free), `calibration` (free). A model may hold several roles or be "benched" (visible, cast by no rule).

---

## 4. The four plays (choreography over the engine)

Shared: `./tmp/model-council/play-<play>-<ts>-<rand6>/{manifest.json, task.md, <label>.result.md, combine/}`. **Fan:** main thread dispatches N `delegation-runner` Haiku subagents in one message (cap 5). **Combine:** `council-judge` (Sonnet) reads result files from disk (no main-context inheritance; blind labels). **Failure:** a member ERROR/TIMEOUT/NO_OUTPUT writes a stub; play proceeds if survivors ≥ quorum else `PLAY-DEGRADED`; never aborts siblings. **Provenance invariant:** combined output retains per-model attribution (laundering = defect). **Budget:** estimate pre-dispatch; actuals in manifest; final line `Council spend: $X (est $Y) across N models`.

- **4.1 Diff+Synthesis (v1 lead):** cast k=3 (decorrelated) → identical task → council-judge → `combine/synthesis.md` with mandatory sections **Convergent / Divergent (attributed) / Adjudication / Confidence / Baseline delta** (vs baseline_member alone — measurability). Claude-family member present → header `judge-family-overlap:<addr>`.
- **4.2 Consensus/Vote:** odd N; contract suffix `End with: VERDICT: <APPROVE|BLOCK|UNSURE> — <reason>`; **mechanical tally** (`grep -m1 '^VERDICT:'`), missing→UNSURE flagged; strict majority of returned (min 3); split/majority-UNSURE → escalate to judge (marked ESCALATED). Fails **closed** (can't reach quorum → BLOCKED-BY-DEGRADATION).
- **4.3 Best-of-N:** N generators (spread across families) → **outcome scorer**: code = per-candidate scratch + `tests=<cmd>` (reuses `hidden-tests` machinery), rank tests-passed then cost; design = judge vs generated rubric (shown before dispatch for veto). `combine/winner.md` = winner (attributed) + scoreboard. Expensive; policy guards (only where diversity real; default N=3).
- **4.4 Generator↔Verifier:** generator (top implementer) + verifier (top verifier, **different family**, min both_wrong_rate). Generator turn → verifier turn (ALWAYS read-only, findings-json contract, same as review dim) → ≥1 blocking finding → ONE repair round (`extdel.sh prompt <gen-handle>` session resume) → verifier re-checks → `combine/verification.md`. Bounded (1 round); verifier failure → generator result flagged `UNVERIFIED`.

---

## 5. Project policy & commission

### 5.1 Formats & location
**Project config, not KB** (must work without sdlc-knowledge-base; consumed mechanically). `.sdlc/model-council/`: commission.json, roster.json/roster.md/diversity.json, policy.json, stack-addons/, assessment-log.jsonl, **outcomes.jsonl** (adaptive hook — plays append {play,cast,accepted|reverted,ts}; consumed by NOTHING in v1). `policy.json`: `{defaults:{max_usd_per_run,max_concurrent,posture,k}, task_types:{<type>:{play, cast|cast_rule, budget_usd, quorum?, requires?}}, fallbacks:{unreachable_member:"recast-from-roster", uncommissioned:"orchestration-heuristics+warn"}}`. Casts may be **pinned** (explicit addresses) or **cast_rule** (re-evaluated live — survives drift); commission writes rules by default.

### 5.2 `/sdlc-model-council:council-commission` (reuses sdlc-core commission structure)
0. Pre-flight re-commission check. 1. **Discover** (list-backends --json + `agy models`/`opencode models`, token-free; pricing + free flags). 2. **Characterize** (repo scan for stack; task-mix, blast radius, budget/day, latency). 3. **Audition?** four options: `skip` (priors only), `calibrate` (FREE only, full stack, $0), `standard` (calibrate + paid objective dims under a cap ~$1, estimate first), `full` (whole stack incl judge dims). 4. **Roster** (skip still writes a roster: posterior=prior, n=0, all provisional). 5. **Policy** (seeded from characterization × role table; overridable; unusual overrides warn not block). 6. **Record** commission.json.

### 5.3 Priors vs audition
Shipped `scripts/council/priors/<family>.json` (coarse, versioned: matches[], context_tokens, per-dim scores, pricing, provenance). Files: openai-gpt5, google-gemini-3-pro, google-gemini-3-flash, anthropic-claude-4, oss-gpt-oss, opencode-free-tier (humble ~0.4–0.5, pricing 0), unknown (0.5 wide + `no-prior` flag). **Blend IS the §3.1 shrinkage** — priors are the k=3 pseudo-obs; "skip audition" is just n=0.

### 5.4 Runtime consult
`/council-run task-type=… input=… [budget-usd=][play=][cast=]`: missing policy → v0.1.0 heuristics + "not commissioned" warn; type not in policy → nearest default + warn; found → play + (pinned cast | cast_rule via cast.py against live roster); member unreachable → recast + note; explicit play=/cast= → override, recorded. `/delegate` gains: with a roster, `backend=` may be omitted → roster's best single model for the task (**the honest fallback product if fan-out uplift disappoints**). v0.1.0 sibling-routing survives in council-policy (hand off to codex-plugin-cc when installed; plays are the cross-model work no sibling does).

---

## 6. Cost & budget (never-surprise-spend)
Truth: `scripts/council/pricing.json` (per-family rates, free=0). Actuals: `usage.py` over `events.jsonl` — opencode exact, codex metered (tokens×pricing), agy estimated (chars/4×pricing, flagged). Zero engine edits. `estimate.py`: Σ members×(est tokens)×rates; items carry est_*_tokens refined by **wave-0 free calibration before paid dispatch**. Enforced-in-code rules: (1) no paid dispatch without explicit `budget-usd=` or resolved policy default **echoed before dispatch**; (2) `--estimate` prints table + exits token-free; (3) mid-run hard stop at cap (cancel pending, mark skipped:budget, resumable); (4) free-only labeled `$0.00 (free tier)`; (5) every report ends with actual-vs-estimate spend line + greppable history.

---

## 7. Reuse / rename / new + migration order
KEEP zero-behavior-edit: extdel.sh (sed state dir → tmp/model-council + name), turn-supervisor.pl, 3 adapters (delete stale opencode `known_engine_limitation` note), 313 tests (path/name sed — the **substrate regression gate**, green before/after), delegation-runner, delegate/backends commands, ADAPTER-AUTHORING. REFRAME: orchestration-policy → council-policy (add plays, budget, policy-consult). REWRITE: README, plugin.json (name `sdlc-model-council`). `git mv` plugin dir. NEW: `scripts/council/` (assess.sh, schedule/extract_answer/usage/estimate/roster/diversity/cast/complexity.py, score/*.py, priors/*.json, pricing.json), `assessment/stack/v1/`, `agents/council-judge.md` (Sonnet), commands (council-commission/assess/roster/run/estimate), COUNCIL-STACK-AUTHORING.md, tests (stack-lint, scorer units, roster/diversity golden, play-choreography over canned files, estimate, gated live).
**Migration order (tests green at each *step):** *(1) git mv + sed, 313 green from new path → *(2) council scripts + stack + unit tests (runnable as bash/python3, no commands) → *(3) mock-fleet assessment end-to-end → (4) commands + skill + agents → (5) registration (marketplace/CLAUDE/AGENT-INDEX: retarget delegation-runner, add council-judge) → (6) gated live slice → (7) pre-push + broken-refs + release.

---

## 8. v1 vertical slice (charter-locked: assessment → roster → Diff+Synthesis on a real decision)
**In:** 4 objective dims, 9 items, **judge-free** (deterministic): code-review/planted-defects ×3, bug-fix/hidden-tests ×2, long-context/exact-match ×2, instruction-format/format-parse ×2. **5-model cast:** codex:default@medium, agy:gemini-3.6-flash-medium, agy:gemini-3.1-pro-high, opencode deepseek-v4-flash-free, opencode nemotron-3-ultra-free (3 families, 2 free, **zero Claude-family** → judge-overlap never fires; deliberate). Est. paid < $0.50 under $1 cap. Artifacts: results.jsonl → roster with posteriors/provisional/diversity. **One play:** diff-synthesis via `council-run task-type=code-review` on a **real repo decision** (reviewing this feature's own first implementation PR), producing Convergent/Divergent/Adjudication/**Baseline-delta** synthesis + spend line. Commands: council-assess/roster/estimate/run(diff-synthesis)/commission(priors+calibrate+standard). **Measurability live day one:** manifest `baseline_member` + synthesis Baseline-delta + outcomes.jsonl.
**Deferred (designed, not built):** consensus/best-of-N/gen↔verify plays; judge-rubric + reasoning/research dims; tool-use/agentic dim; refactor/code-gen items; adaptive learning (outcomes.jsonl consumer); spend-report; cast pinning UI; KB mirror; codex session-id interop.

---

## 9. Testability (no tokens)
Mock fleet via answer banks `tests/fixtures/council/answers/<persona>/<item-id>.txt`, personas `strong|weak|contrarian|shotgun|mute|noncompliant` chosen for **hand-computable golden** roster/diversity values. (2) Scorer unit tests (deterministic golden score.json incl. edge cases). (3) Roster/diversity golden (byte-stable with injected fixed timestamps; asserts shrinkage, provisional thresholds, insufficient-pair pessimism, roles). (4) Play choreography over pre-populated `<label>.result.md` (incl. failure stubs): quorum, mechanical tally, degraded reports, **provenance grep** (every divergent claim attributed), budget line; judge tested at contract level (blind labels, no address in its inputs). (5) Harness end-to-end on mock fleet (waves, cap-5, budget hard-stop, resume, timeout rows). (6) Estimate tests (token-free by construction). (7) ONE live gate `COUNCIL_LIVE=1` (free-only default $0; paid requires `COUNCIL_LIVE_PAID=1`+budget; never CI). (8) 313 substrate assertions unmodified before/during/after.

---

## 10. Ranked risks
1. **Multi-model may not beat the best single model often enough.** Existential — made MEASURABLE: `baseline_member` always in cast; synthesis states baseline delta; outcomes.jsonl accumulates. Decision rule: <20% material change over ~20 runs → honest product is roster-driven **single-model routing** (`/delegate` auto-pick, already shipped) — fallback is a feature removal, not a rewrite.
2. **Assessment cost & trust.** free wave-0 before paid; measured re-estimation; hard budget stop+resume; priors-only always available; cost_basis honesty (agy=estimated, says so).
3. **Small-sample noise.** shrinkage k=3; ci95+n shown; "provisional"; insufficient pairs = correlated; roles by threshold not ranking.
4. **Judge bias.** objective-first structural; blind labels; mandatory cross-family second for Claude-family; visible flags; v1 slice judge-free. Residual: synthesis adjudication is one Claude judgment (flagged).
5. **Item leakage.** original private hash-pinned items; project add-ons; edits break comparability visibly. Residual: static stacks decay → adaptive data (fast-follow).
6. **Model/gateway drift.** cast_rules re-eval live; unreachable→recast; commission fleet snapshot + roster staleness check; pricing asof. Residual: silent quality drift behind a stable id → re-audition/adaptive catches.
7. **Answer-contract fragility.** contract-fail is a distinct recorded status; instruction-format is itself scored (measured before relied on); lenient-whitespace/strict-structure extractors.
8. **Layer complexity vs thin substrate.** v1 slice minimal (9 items, 1 play, judge-free); every migration stage independently runnable; substrate gate means a stalled council never breaks working delegation.
9. **Naming confusion** (council-commission vs sdlc-core:commission; council vs sdlc-workflows). `council-` prefix; mandated one-line sdlc-workflows distinction everywhere. Minor.
