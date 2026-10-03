# Design spec — Council tool-use & command-line-execution assessment (#235)

**Status:** Approved (open questions resolved with operator, 2026-07-26)
**Feature proposal:** `docs/feature-proposals/235-council-tool-use-assessment.md`
**Builds on:** model-council v1 (PR #233) + local-MLX backend (PR #234), both on `main`.
**Design authority for existing machinery:** `docs/superpowers/specs/2026-07-25-sdlc-model-council-design.md`.

---

## 1. Purpose & scope

Add an **agentic tool-use** capability to the council assessment so a model can be
graded on *command-line execution* and *monitoring*, and run a **local-MLX vs
Haiku-4.5 vs hosted-fleet** comparison. This turns the un-audited `tool-use` prior
(0.42 placeholder) and the extrapolated "Haiku should win command execution"
answer into measured numbers.

The v1 stack grades static, single-turn dimensions (code-review, bug-fix,
long-context, instruction-format). Tool use is different in kind: emit a command
→ observe output → decide → iterate → **know when to stop**. It stresses tool-call
**format validity**, **reasoning over observations**, and **stop-condition
judgment** — none of which v1 measures.

## 2. Resolved open questions

| Question | Decision | Rationale |
|---|---|---|
| One `tool-use` dim, or split? | **Split into two dims: `command-exec` and `monitoring`.** | Operator decision. Command production and stop-condition judgment are distinct skills; grading them separately makes the local-vs-Haiku story legible per-skill. |
| How to reach Haiku for an apples-to-apples harness? | **Dispatch `model: haiku` subagents inside the Claude Code environment; pipe each answer through the identical deterministic scorer.** | Operator decision. We are *in* Claude Code, so Haiku is $0 marginal — no `ANTHROPIC_API_KEY`, no metered API. Cost-control generalises: MLX is $0 local, codex/agy are pro-sub ($0 marginal), opencode is free-tier → **the whole comparison runs at the free level.** |
| Live shell? | **No.** Propose-and-score only in the default path. | Safety + reproducibility + isolates model capability from harness plumbing. |

**Fairness caveat (recorded).** MLX and the hosted fleet are elicited through the
bare-prompt adapter path (single item prompt, no agentic system prompt — the #234
lesson). Haiku is elicited through the Claude Code subagent path, which carries
the harness system prompt. For **single-turn propose-and-score** items this is
bounded, but it is a known asymmetry and is flagged on the Haiku numbers in the
retrospective. Every model sees the **same rendered item prompt** and is scored by
the **same** `command-check` scorer.

## 3. Elicitation contract (propose-and-score)

Each item gives the model a **goal + a simulated terminal transcript** (never a
live shell). The model emits the correct next command(s) or the correct
continue/stop decision. Scoring is deterministic against a golden rubric.

**Answer contract: reuse `strict-json`.** No change to `extract_answer.py` (the
single source of truth) — smaller blast radius, and fair. The model returns one
JSON object:

- **command-exec** items:
  ```json
  {"commands": ["<shell command>", "..."], "reason": "<why>"}
  ```
  `commands` is an ordered list of the shell command(s) to run next (a single
  command is a one-element list).

- **monitoring** items:
  ```json
  {"decision": "stop" | "continue", "trigger": "<the line/condition that fired, or empty>", "reason": "<why>"}
  ```

Every tool-use `prompt.md` ends with a line containing the substring **`single
JSON object`** (the stack-lint envelope check for `strict-json`).

## 4. Scorer: new type `command-check`

`format-parse` cannot express what command-checking needs — **regex over a free
string value** and **negative constraints** ("must contain `grep` + the target
path; must **not** contain `rm -rf`"). So a new scorer type is justified (as the
restart pointer anticipated).

**ABI (unchanged contract):** `command-check.py <item-dir> <answer-file> <workdir>`
→ writes `<workdir>/score.json = {score, status, details}`, **always exits 0**
(`os.makedirs(workdir, exist_ok=True)` in `write_score`). Stdlib only. Imports
`extract_answer.extract_strict_json` — never re-parses.

**Rubric — `expected/checks.json`:**
```json
{
  "field_checks": [
    {"field": "commands", "regex": "\\bgrep\\b",  "flags": "i", "desc": "uses grep"},
    {"field": "commands", "regex": "access\\.log",              "desc": "targets the right file"},
    {"field": "commands", "not_regex": "rm\\s+-rf",             "desc": "no destructive rm"},
    {"field": "decision", "equals": "stop"},
    {"field": "decision", "enum": ["stop", "continue"]}
  ]
}
```

**Semantics (one operator key per check):**

- **Field resolution:** `obj.get(field)`. For `regex`/`not_regex` the value is
  coerced to text: a string is used as-is; a **list is joined with `\n`**
  (so multi-command answers are checked as a block); a missing/`None` field → `""`.
  For `equals`/`enum` the raw typed value is compared.
- **`equals`** — pass iff `value == expected` (missing field fails).
- **`enum`** — pass iff `value in allowed` (missing field fails).
- **`regex`** — pass iff `re.search(pattern, text, flags)` matches (required
  pattern present).
- **`not_regex`** — pass iff `re.search(pattern, text, flags)` does **not** match
  (forbidden pattern absent). A missing field is vacuously safe → pass. This is a
  guardrail check (destructive commands), deliberately lenient about absence.
- **`flags`** — optional string; letters map to `re` flags (`i`→IGNORECASE,
  `m`→MULTILINE, `s`→DOTALL). Unknown letters ignored.

**Scoring:** `score = satisfied / total`, `total = len(field_checks)`, rounded to
4 dp. `status = "scored"`. If `extract_strict_json` returns `None` (not a JSON
object) → `status = "contract-fail"`, `score = 0.0`. Any infra exception →
`status = "error"`, `score = 0.0` (ABI: still exit 0).

**`details`:** `{"satisfied": int, "total": int, "failed_checks": [labels]}` where
a label is the check's `desc` if present, else `"<field>:<op>"`.

## 4a. Scorer: `command-diff` — execute-and-diff (added 2026-07-26, post-audition)

**Why the rubric was not enough.** §4's regex rubric asserts *what a command looks
like*. The audition proved that insufficient at the hard tier: on
`ce-hard-grep-context` three local models answered with `awk` instead of
`grep -A 3`, and the rubric gave all three the same 0.6667 — yet on execution
Qwen3-Coder-30B-A3B's awk was **byte-identical to the golden output** (a false
negative) while Qwen2.5-Coder-7B's and Devstral-24B's were genuinely wrong.
Widening the regex to admit `awk` would have converted two false negatives into
false **positives**. A regex over a proposed command cannot separate *correct*
from *plausible-looking*; only running it can. This is the "real sandboxed
execution" opt-in that §1/§9 deferred, now justified by measurement.

**Scope.** Applies only to items whose inputs are **self-contained files**, so a
sandbox can reproduce the world the command acts on: `ce-grep-errors` and
`ce-hard-grep-context`. Items whose correct answer inspects **live machine state**
(`ce-disk-usage`, `ce-port-inspect`, `ce-hard-find-large-recent` → `/var/log`, a
listening port) and all `monitoring` items (decisions, not commands) stay on
`command-check`. Stack-lint enforces the structural half of this.

**ABI (unchanged):** `command-diff.py <item-dir> <answer-file> <workdir>` →
`<workdir>/score.json`, always exit 0, stdlib only. Imports
`extract_answer.extract_strict_json`; same `strict-json` answer contract, so no
change to the elicitation and no new contract.

**Rubric — `expected/exec.json`** plus the golden file it names:
```json
{"field": "commands", "golden_stdout": "stdout.txt",
 "allow_binaries": ["grep", "egrep", "rg", "awk", "sed", "cat", "head", "tail",
                    "sort", "uniq", "wc", "cut", "tr"],
 "timeout_s": 10}
```

**Scoring.** Run the command(s) with cwd = a sandbox of input **copies**; compare
stdout to the golden after normalising trailing whitespace and trailing blank
lines. Match → `1.0`, mismatch → `0.0`, both `status = "scored"`. Binary, not
partial: a command either achieves the goal or does not. Note this is **harsher**
than the rubric as well as fairer — a wrong command loses the partial credit it
used to collect (7B and Devstral went 0.6667 → 0.0 while Qwen3-30B went
0.6667 → 1.0).

**Safety — three gates, off by default.** Executing model-proposed shell text is
the new risk, so:
1. **Opt-in.** Refuses unless `COUNCIL_ALLOW_EXEC=1`. No env var, no execution.
2. **Allowlist.** Every pipeline segment's leading binary must be in
   `allow_binaries` (leading `VAR=value` and `env` skipped). Read-only text tools
   only — no `curl`/`wget`/`nc`/`ssh`, so there is no egress path. Stack-lint
   additionally rejects any item whose `allow_binaries` names a destructive or
   egress binary, so an item cannot widen the gate by accident.
3. **Deny-list** on shell metacharacters: output redirects, process/command
   substitution, chaining, backgrounding, `find -exec|-delete`. A plain `|`
   pipeline is allowed.

Gates 2–3 match against a **quote-masked** copy of the command (quoted regions
replaced by same-length filler). This is essential, not cosmetic: an awk program
legitimately contains `;`, `&&` and `>` inside its quoted script, and matching
those as shell operators reproduces exactly the over-strictness this scorer
exists to remove. Execution then uses a per-invocation sandbox of input copies, a
stripped environment (`PATH`, `LC_ALL`, `HOME`/`TMPDIR` → sandbox), and a hard
timeout. The item's own `inputs/` is never the cwd, so a redirect inside a quoted
awk/sed program can only touch throwaway files.

**Exec-disabled fallback.** An item may ship `expected/checks.json` alongside
`exec.json`. With the gate closed the scorer falls back to that static rubric and
reports `status = "scored-static"` rather than scoring 0.0. This keeps a default
(non-opted-in) council run meaningful and makes exec mode a strict **upgrade**
rather than a prerequisite. Stack-lint requires `command-diff` items to ship the
fallback.

**Statuses:** `scored | scored-static | exec-disabled | unsafe-command | timeout |
exec-error | contract-fail | error`.

## 5. Items

Six new deterministic items (both dims gradable at n=3):

| dim | id | goal shape |
|---|---|---|
| command-exec | `ce-grep-errors` | find the failing request in an access log → correct `grep` |
| command-exec | `ce-disk-usage` | locate the biggest dir under a path → `du`/`sort` pipeline, no destructive op |
| command-exec | `ce-port-inspect` | find which process holds a port → `lsof`/`ss`, read-only |
| monitoring | `mon-build-finished` | build log stream → STOP on success line, identify it |
| monitoring | `mon-migration-error` | migration stream → STOP on the error line, identify it |
| monitoring | `mon-still-running` | health-check stream, not yet converged → CONTINUE |

Each item ships `item.json` (`answer_contract: strict-json`, `scorer.type:
command-check`), `prompt.md`, `inputs/` (the simulated transcript), and
`expected/checks.json`. Item ids are prefixed `ce-*` / `mon-*` so the two skills
stay eyeball-separable within the roster.

## 6. Wiring

- **stack.json** — append the 6 items with recomputed `sha256` (via `stack_hash.py`).
- **priors** — add `command-exec` and `monitoring` to the `dimensions` map of all
  8 shipped priors. `mlx-local` gets placeholders first, **replaced with
  audition-derived values** after the run. Legacy `tool-use` key is retained (the
  priors/roster tests require the original 9 dims to be present; extras allowed) as
  a now-superseded rollup.
- **stack-lint** (`tests/test-council-stack-lint.sh`) — add `command-check` to
  `KNOWN_SCORER_TYPES`; item count `9 → 15`; dimension distribution gains
  `command-exec: 3, monitoring: 3`; add a `command-check` expected-files branch
  (`expected/checks.json` parses and has a non-empty `field_checks` list).
- **diversity** (`diversity.py`) — add `command-exec` and `monitoring` to
  `OBJECTIVE_DIMS` so the tool-use comparison feeds the correlation map (both are
  deterministically scored, binarised at ≥0.5).
- **roster** — no change. New dims flow through generically; role logic is guarded
  by `if d in all_dims`. Role integration (a tool-use-driven "executor" role) is a
  documented follow-up, out of scope here.

## 7. Metrics surfaced

Per model, per dim: grade / posterior / raw_mean / n (roster); plus **task
success** (score ≥ 0.5 fraction), **format validity** (non-contract-fail
fraction), **latency** (p50, compounds badly for local), **cost** ($0 across the
board this run). Turns-to-success is degenerate at 1 in propose-and-score (single
turn) and is reported as such.

## 5a. Hard tier (added 2026-07-26, post-audition)

The first six items did not discriminate — every model scored raw 1.0, so the
assessment certified "clears the bar" rather than ranking. Four **hard** items
were added (10 tool-use items total, 19 in the stack; 5 per dim):

| dim | id | what it stresses |
|---|---|---|
| command-exec | `ce-hard-grep-context` | after-context retrieval — the only item that discriminates |
| command-exec | `ce-hard-find-large-recent` | conjunction of two `find` predicates (size **and** mtime) |
| monitoring | `mon-hard-multistage` | an early stage's success is **not** the whole deploy finishing |
| monitoring | `mon-hard-transient-error` | a retried `ERROR` followed by progress is **not** terminal |

Outcome: `monitoring` is **saturated** — all 10 models perfect on all 5 items,
including both traps. `command-exec` separates exactly two models. A genuinely
harder tier is still open work (see the retrospective's follow-ups).

## 8. Comparison protocol

1. Build green (scorer + items + wiring; full 15-file council suite passes).
2. Run `assess.sh` on `--dims command-exec,monitoring` **per MLX model** into
   separate run-dirs, with `COUNCIL_ALLOW_EXEC=1` so the two executable items are
   scored by execution.
3. Run `assess.sh` on the same dims for the hosted fleet (codex/agy/opencode).
4. Elicit **Haiku** via a small harness: render each item prompt exactly as
   `compose_prompt` does, dispatch a `model: haiku` subagent, capture the raw
   answer, score it with the identical scorer, emit a `results.jsonl` row in the
   standard schema (`cost_usd: 0`, `cost_basis: subscription-marginal`).
5. Merge all `results.jsonl` → `roster.py` + `diversity.py` for the side-by-side.
6. Re-derive `command-exec`/`monitoring` priors for **every family with
   observations** (see §8a). Record findings in the retrospective.

**Two measurement rules, learned the hard way (2026-07-26):**

- **One fresh `mlx_lm.server` per model — never load-switch.** Switching the
  loaded model mid-session crashed the server with
  `ValueError: [broadcast_shapes] Shapes (7,1,1,6228) and (7,32,1,8275) cannot be
  broadcast` (a KV/prompt-cache collision), after which it kept listening but
  answered nothing. The #234 "one server, it load-switches on the request `model`
  field" shortcut is **not** reliable. Restart per model and poll `/v1/models`.
- **`--max-concurrent 1` for any local (MLX) pass.** A single server serialises
  generation, so concurrency only adds queueing to the measured `latency_s` — and
  latency is a headline metric of this comparison. It also made every Path-A pass
  fail: three concurrent agentic-system-prompt calls to one 30B server exceeded
  the 90s item timeout (exit 124, empty output). Hosted adapters are unaffected.

## 8a. Prior re-derivation rule

`prior = max(0.40, round(raw_mean − 0.28, 2))` per dim, applied to **every family
with audition observations** (the phase-1 `mlx-local` precedent of raw 1.0 → 0.72,
generalised). The legacy `tool-use` rollup becomes the mean of the two real dims.

Two properties worth stating plainly:

- **It must be applied to all audited families, not just one.** Updating only
  `mlx-local` (phase 1) made the roster grade local MLX **above** agy and opencode
  on *identical* raw 1.0 scores — a pure artifact of stale priors, not a measured
  difference.
- **The prior is held below the observation on purpose.** The roster already
  shrinks toward the prior (`posterior = (n·raw + 3·prior)/(n+3)`), so a prior set
  *at* the observation would double-count the same evidence. Held below, it stays
  a conservative expectation over the whole dimension rather than a restatement of
  one easy audition tier.
- **Caveat to record, not to hide:** because this tier is easy, four families
  converge on 0.72. That is the tier failing to discriminate, **not** evidence
  that the families are equivalent.

## 9. Safety & privacy

The default path executes **no commands** — it scores *proposed* commands as text,
so there is no destructive-command or egress risk from the assessment itself, and
`not_regex` guardrail checks penalise a model that proposes a destructive command
even though it is never run.

Execution is available only through `command-diff` (§4a) and only when the
operator sets `COUNCIL_ALLOW_EXEC=1`. Its three gates (opt-in, read-only binary
allowlist with no egress tools, shell-metacharacter deny-list), the sandbox of
input copies, the stripped environment and the hard timeout are the safety
argument; the test suite asserts each gate, including that a proposed
`rm -rf app.log` is refused *and* that the item's input still exists afterwards.
The residual accepted risk is a write from inside a quoted `awk`/`sed` program,
which the copies-only sandbox contains.
