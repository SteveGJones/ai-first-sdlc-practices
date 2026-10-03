---
name: council-policy
description: >
  Policy for the cross-model council: when to hand off to an installed
  sibling plugin's own slash command (`/codex:*`) versus dispatching our
  `delegation-runner` (backend: codex|agy|…), which backend to pick, what
  permission posture to use, and the fan-out/cost discipline that applies
  regardless of backend — plus the council layer built on that substrate:
  which play to run, how a cast gets picked from the project roster, budget
  guardrails, and where project policy/commission config lives. Consult
  before delegating out to a peer agentic CLI, before choosing between a
  sibling plugin's command and our runner, before choosing a permission
  posture, before fanning out more than one external delegation
  concurrently, or before running a council play (`/…:council-run`).
---

# Council Policy

`sdlc-model-council` is a **cross-model council**: it assesses the peer
agentic CLIs installed on this machine, keeps a project roster of how each
model performs by task type, and runs fan-out **plays** — the same task to
a decorrelated panel, synthesised into one attributed verdict — on top of
an in-session, uncontainerised, single-machine delegation substrate to
locally-installed peer agentic CLIs. No Archon, no Docker, no DAG. (That's
the one-line distinction from `sdlc-workflows`, which *is* Archon-
orchestrated, containerised, DAG-based delegation — reach for that plugin
instead when a task genuinely needs an isolated container or a multi-step
workflow graph; reach for this one for a single in-session hand-off to a
peer CLI, or a cross-model fan-out play, without any of that machinery.)

## §3.3 Routing: sibling-plugin hand-off vs our `delegation-runner`

Before dispatching anything, work out whether the request is better served
by an installed sibling plugin's own slash command than by our adapter.
Per-vendor plugins do the per-vendor job well; our value is cross-vendor
uniformity, graded postures, and fan-out — not re-implementing what a
sibling plugin already does better.

**Detecting whether a sibling plugin is installed — the harness-truth
signal first:** the most reliable, token-free signal is whether the
sibling's own slash commands (`/codex:review`, `/codex:adversarial-review`,
`/codex:rescue`, `/codex:transfer`, `/codex:status`, `/codex:result`,
`/codex:cancel`; `/antigravity:delegate`, `/antigravity:review`,
`/antigravity:research`, `/antigravity:cloud-run-debug`,
`/antigravity:status`, `/antigravity:result`, `/antigravity:cancel`)
appear in *your own* available-skills listing in this session — if they're
there, the plugin is installed and invocable directly, no probing needed.
Only fall back to the `~/.claude/plugins/installed_plugins.json` probe
(`extdel.sh list-backends` runs this for you, advisory-only, never
gating) when you can't otherwise tell — e.g. deciding what to recommend
for a *different* session, or writing guidance that must hold before this
session's own skill listing is available.

| Task shape | codex-plugin-cc (`/codex:*`) installed | Route |
|---|---|---|
| Review my diff / adversarial review gate / rescue a stuck codex task / continue a persistent codex thread | yes | **Hand off** to the matching `/codex:*` command in the main thread; do NOT also dispatch `delegation-runner` for the same task |
| Same task shapes | no | Dispatch `delegation-runner backend=codex`; note in your response that the official `codex@openai-codex` plugin exists and would be a better fit (`/plugin install codex@openai-codex` hint) |
| Cross-model compare/fan-out, unified §4.2-contract collection, an isolated second opinion under a graded posture, posture-graded write delegation | either | **Always our adapter** — this is exactly the work no per-vendor plugin does |
| Anything involving Gemini/agy | either | **Always our agy adapter.** The installed `antigravity@antigravity-for-claude-code` plugin is itself capable (cost-disciplined delegate/review/research/cloud-debug with verification) — this is a **coexist** relationship, not a supersession. Our differentiators are narrow but real: graded `--gemini_dir` read-only/workspace postures (finer than a blanket write-approval) and the unified cross-vendor contract + cross-model fan-out that a single-vendor plugin can't offer by definition. Do not claim our agy adapter is strictly better — it solves a different problem (uniformity across vendors) than the sibling plugin does (depth on one vendor). |

**Why hand-off, not call-through:** our `delegation-runner` subagent (Haiku;
Bash/Read/Grep/Glob, no Skill/Agent tool) cannot invoke another plugin's
slash command, and granting it that ability would break context isolation
and be unreliable. Even from the main thread, calling `/codex:review` and
then wrapping its output would mean scraping another plugin's own
conversational output into a different shape — fragile, and it double-
spends context. So "prefer codex-plugin-cc when installed" is a **routing
decision made once, in the main thread, before dispatch** — never
inter-plugin RPC. Say this plainly if a caller asks how the hand-off
works; there is no hidden call-through mechanism.

## Picking a backend

Run `${CLAUDE_PLUGIN_ROOT}/scripts/extdel.sh list-backends` (add
`--probe-auth` for a live auth check, `--json` for machine-readable output)
to see which backends are registered as adapters, which are actually
installed on this machine, and — advisory only — whether a sibling plugin
for that vendor is present. Use this before dispatching `delegation-runner`
if you're not sure a backend is ready; it's a pure read-only report, no
handle created, no tokens spent.

If the caller names a provider ("GPT", "codex", "Gemini", "agy"), that
picks the backend directly. If they just say "get a second opinion"
without naming one, ask rather than guessing, or default to whichever
`list-backends` shows as installed+authenticated on this project.

## Which platform: codex vs agy

Both backends present the identical caller-facing contract (design doc
§4.2) — the choice is purely about which model/provider's take you want:

| | `codex` | `agy` |
|---|---|---|
| Provider / model | OpenAI, GPT | Google Antigravity, Gemini (and other models `agy models` lists) |
| Continuity mode shipped | resume | resume |
| Held-process (`mode: persistent`) | not yet shipped (planned: `codex mcp-server` daemon) | **not planned as a held process at all** — agy's own continuity is server-side/id-addressable, so a pty-held interactive session would trade real state for fragile heuristic completion detection; `mode: persistent` is a clean `Status: ERROR`, not attempted |
| Headless permission model | a real sandbox (`-s read-only`/`workspace-write`) gates tool use non-interactively | **auto-denies every tool call** (`read_file`/`command`/`write_file`/`edit_file`) in `--print` mode unless pre-allowed — `--mode`/`--sandbox` do NOT gate anything headless (live-probed; see the design doc's §9.15) |
| `read-only` posture mapping | `-s read-only` | a per-handle `--gemini_dir` config carrying a `permissions.allow` list scoped to reads + read-only shell commands — the real enforcement lever, not `--mode`/`--sandbox` |
| Answer source | `-o`/`--output-last-message` file | plain stdout (no separate answer file from the CLI itself — `extdel.sh` captures it into the same `turn-NNN.last-message.txt` convention) |
| Installed sibling plugin | `codex@openai-codex` (official) — `prefer-for` review/rescue/persistent-thread shapes, see the routing table above | `antigravity@antigravity-for-claude-code` — `coexist`, see the routing table above |

## Delegate out to `delegation-runner`

Delegate to an external agentic CLI backend when the value is specifically
in a **different model/provider's** take on the problem, not just in
offloading verbose output (that's what `command-delegation`'s
`command-runner` family is for):

- **Cross-model second opinion.** You want GPT's (codex) or Gemini's (agy)
  independent read on a design, a bug, or a piece of code — to compare
  against or merge with your own analysis.
- **Independent fan-out sub-problems.** N genuinely independent sub-tasks
  where you want N concurrent external sessions rather than doing them
  serially yourself or via N internal subagents.
- **Continuing an existing external conversation.** The caller already has
  a `handle` from a prior `delegation-runner` turn and wants to continue
  that specific external session (pass `handle:` through — never start a
  new one when continuity with the prior turn matters).

## Keep it inline or use an internal subagent instead

- The sub-problem doesn't benefit from a different model's perspective —
  use a Claude subagent (or handle it directly).
- You need to react to output turn-by-turn, mid-stream — external
  delegation is submit-then-poll; you get a compact answer only once each
  turn finishes, not a live stream.
- The task is destructive/mutating and needs a human in the loop for
  approval — external CLIs run non-interactively (`codex exec` /
  `agy --print`), so anything requiring an approval prompt will just fail
  under `read-only`/`workspace` posture rather than pausing for a human.
  That's intended behavior, not a bug to route around. (codex's
  `app-server` protocol exposes a real per-action approval loop —
  `ExecCommandApprovalRequest`/`ApplyPatchApprovalRequest`/etc, answered
  with a `ReviewDecision` — that a future `rpc-server`-kind adapter could
  drive for fine-grained, in-conversation approval; agy has no equivalent
  verb in its machine channel. Out of scope for this build — see the
  design doc's §6.3/§9.15 for the roadmap.)
- It's a local shell command, build, test suite, or log to watch — that's
  `command-delegation`'s territory (`command-runner`/`build-runner`/
  `test-runner`/`process-monitor`), not this plugin.

## Posture: default read-only, escalate only when the caller says so

| posture | codex mapping | agy mapping | when |
|---|---|---|---|
| `read-only` (**default**) | `-s read-only` — read and reason; no writes, no network from its side | `--gemini_dir` allow-list scoped to `read_file(*)` + read-only shell command prefixes (`cat`/`head`/`tail`/`sed`/`grep`/`rg`/`ls`/`find`/`wc`/`git`) — no `write_file`/`edit_file` rule at all | the default for every delegation unless told otherwise |
| `workspace` | `-s workspace-write` — can write files within its working directory | the read-only allow-list PLUS `write_file(*)`/`edit_file(*)` and a build/test command set (`python`/`node`/`npm`/`pytest`/`go`/`cargo`/`make`/`bash`/`sh`) | only when the caller explicitly wants the external model to make edits |
| `dangerous` | `--dangerously-bypass-approvals-and-sandbox` | `--dangerously-skip-permissions` (supersedes any allow-list; a config dir is still passed for uniformity) | only when the caller explicitly opts in — never chosen by the wrapper itself |

**Why agy's mapping changed from `--mode`/`--sandbox`:** an earlier design
mapped agy's posture onto `--mode plan|accept-edits` + `--sandbox`.
Live probing (design doc §9.15) found neither flag gates anything in
headless `--print` mode — agy auto-denies every tool call there regardless
of `--mode`, and only a `permissions.allow` entry (delivered via
`--gemini_dir`) or `--dangerously-skip-permissions` actually lets a tool
call through. `extdel.sh` writes a fresh per-handle
`agy-cfg/antigravity-cli/settings.json` before every turn (start AND every
resume), so a `--steal` posture escalation is picked up automatically.

**Escalation is a caller decision, never the wrapper's.** `delegation-runner`
is instructed to never select `dangerous` on its own initiative, and a
handle's posture is *pinned* at `start` time — `extdel.sh prompt` refuses a
differing posture unless `--steal` is passed explicitly, so any escalation
mid-conversation is visible in the transcript rather than silent. This pin
is enforced identically for every backend — `extdel.sh` refuses the
mismatch before it ever builds a command line, regardless of adapter.

**`read-only` is not `read-nothing`.** The sandbox/allow-list posture
restricts what the external model can *do* (write, run network-touching
commands) — it does not restrict what it can *read*. Under any posture,
codex or agy can read any file on disk that the calling environment's user
could read: `.env` files, `~/.ssh/`, credentials, anything in the delegated
`cwd`/`add_dirs`. That content becomes part of what's sent to the external
provider's infrastructure (OpenAI for codex, Google for agy) as prompt
context. This is inherent to delegating to an external CLI, not a bug in
this plugin — name it plainly to the caller if a delegation is pointed at
a directory that plausibly contains secrets, rather than silently
proceeding.

## Fan-out and process count

Each delegation is submit-then-poll, not a held daemon, in the resume mode
this build ships for every backend — so a single delegated turn is one
detached process while it runs, not three, regardless of backend. (Codex
*persistent* mode, when it ships, will use a daemon + holder + watchdog per
handle — 3 processes per handle — worth knowing in advance: **N concurrent
persistent handles ≈ 3N processes**, against the family's fan-out cap of
**5 concurrent external sessions**. agy has **no** persistent/held-process
mode planned at all — see the platform comparison table above — so this
concern is codex-only.) Apply the cap of 5 regardless of backend or mode
when deciding how many `delegation-runner` dispatches to fan out at once —
it exists to bound both process count and concurrent spend against the
external provider's quota. This cap applies to `compare`/fan-out
(below) exactly as it does to individual `delegate` dispatches.

**agy's old cross-handle id-capture race is now closed by construction:**
earlier builds read a single machine-global
`~/.gemini/antigravity-cli/cache/last_conversations.json` keyed by cwd, so
two agy `start` calls landing in the *same* cwd at nearly the same time
could race on which conversation that shared cache ended up recording.
Each handle now gets its own isolated `--gemini_dir`
(`./tmp/model-council/<HANDLE>/agy-cfg/`), so id capture reads a
per-handle cache with nothing else to race against — concurrent
`delegation-runner` dispatches in the same cwd no longer contend over id
capture at all. `status` can still surface a `WARNING` if a handle's own
isolated cache entry changes identity out-of-band between turns (now a
much narrower, more anomalous signal than the old cross-process race) —
report it, don't silently trust the newer id.

## `NO_OUTPUT`: an exit-0 turn is not automatically a successful one

`delegation-runner` can report `Status: NO_OUTPUT` on any backend — a turn
that exited success-shaped (exit code 0) but whose captured answer was
empty after trimming whitespace. This is never silently upgraded to
`SUCCESS`. It's most common with agy: the headless auto-deny above means a
turn can complete cleanly while the actual requested tool call was denied,
leaving nothing useful in the answer. When that's the cause, `## Errors`
carries agy's own diagnostic verbatim (its "no output produced ...
auto-denied" wording) plus the fix — broaden the posture on a fresh
handle, or rephrase the task to fit the current one. A codex turn can also
exit 0 with an empty `-o` file (e.g. an unretried sandbox denial); the
same check applies there too, backend-generally. A `NO_OUTPUT` with no
permission hint at all is a legitimately empty answer, not a crash — the
wrapper agent reports it as-is rather than fabricating content or
silently retrying.

## Cost is real and invisible to Claude's own telemetry

Delegated turns spend the external provider's quota/credits (OpenAI's for
codex, Google's for agy), not Anthropic's — and that spend does not show
up in Claude Code's own token/cost reporting. Codex's `--json` event
stream includes token-count events; agy's `--log-file` output is retained
per turn. The full transcript for either backend is kept under
`./tmp/model-council/<HANDLE>/`, so it's auditable after the fact,
but nothing surfaces it proactively today. Don't fan out delegations
casually; each one is real spend on someone else's bill — this is what
makes the fan-out cap above a cost control, not just a process-count
control.

## Plays (cross-model fan-out)

A **play** is a choreographed fan-out over the delegation substrate above —
the same task goes to a decorrelated panel of models, the results are
collected on disk (never inheriting the main thread's context), and a
combine step produces one attributed answer. Four plays are designed;
one ships in v1.

- **Diff+Synthesis — SHIPPING in v1.** Cast a decorrelated panel (default
  k=3) from the project roster, fan the same task out to each member (cap
  5, per the fan-out section above), and dispatch the `council-judge`
  agent (Sonnet, reads result files from disk under blind labels) to
  synthesise them into `combine/synthesis.md`: **Convergent** (points of
  agreement) / **Divergent (attributed)** (disagreements, each pinned to
  its model) / **Adjudication** (the judge's call on each divergence) /
  **Confidence** / **Baseline delta** (did the panel materially beat the
  roster's single best model for this task, the `baseline_member`?). Run
  it via `/…:council-run task-type=… input=…`.
- **Consensus/Vote — designed, deferred.** An odd-N cast each ends its
  response with a mechanically-tallied `VERDICT: APPROVE|BLOCK|UNSURE`
  line; a split or majority-UNSURE escalates to a judge.
- **Best-of-N — designed, deferred.** N generators produce independent
  candidates; an outcome scorer (test-pass rate for code, judge-vs-rubric
  for design) ranks them and returns an attributed winner.
- **Generator↔Verifier — designed, deferred.** A generator and a
  cross-family verifier run one bounded repair round; an unverified result
  is flagged rather than silently accepted.

**The measurability spine:** every play keeps the roster's best single
model in the cast as the `baseline_member`, and the synthesis states
plainly whether the panel beat it, confirmed it, or was net-negative. This
is not decoration — it's how the whole approach proves or disproves its
own worth. If, over real use, the panel rarely beats the baseline member,
the honest fallback is **roster-driven single-model routing**
(`/…:delegate` with the roster's pick, no fan-out at all) — a feature
removal, not a rewrite, and one this policy exists to make honest to reach
for.

## Policy & commission consult

A project's council configuration lives under `.sdlc/model-council/`:
`roster.json` (per-model performance by task type, from assessment),
`policy.json` (task-type → {play, cast or cast_rule, budget}), and
`commission.json` (the record of how the project was commissioned).

`/…:council-run` reads `policy.json` for the task type it's given, to pick
the play, the cast, and the budget guardrail without the caller having to
specify them. If the project isn't commissioned (no `policy.json`), it
falls back to heuristics — play = `diff-synthesis`, cast built live from
`roster.json` if present, else ask the caller — and says plainly that the
project isn't commissioned rather than silently guessing.

Casts in policy are usually a **`cast_rule`** (re-evaluated live against
the current roster at run time), not a pinned list of addresses — that way
a policy set up today keeps selecting good models after a roster refresh
or a model's retirement, rather than pointing at addresses that no longer
resolve well or at all. Pinned casts are supported for when a caller
deliberately wants a fixed panel.

Set this up with `/…:council-commission` (discover → characterize →
assess → write roster + policy), refresh it with `/…:council-assess`,
inspect the roster with `/…:council-roster`, and preview spend with
`/…:council-estimate` before a run that would cost real money.
