# sdlc-model-council

**Assess which models are worth using, then delegate to the ones that earn
it.** This is not only a delegation plugin — assessment is half of it, and the
half that makes the other half meaningful. Delegating to a peer model is easy;
knowing *which* model deserves the work, on evidence rather than vendor
benchmarks or vibes, is the hard part.

| | What it does | Where it lives |
|---|---|---|
| **Assessment** | Measure what a model can actually do, on our own problems, under our own grading | `assessment/stack/` (the v1 item stack) and `research/poker-capstone/` (the multi-stage capability ladder) |
| **Delegation** | Reach a locally-installed peer agentic CLI and fold a uniform result back in | `scripts/extdel.sh` + `scripts/adapters/` |

The output of assessment is a **roster** — which models hold which seats, with
what evidence behind each. Delegation then routes work against that roster
instead of against guesswork. A model that has not been assessed has not
earned a seat.

## The assessment half

Two complementary instruments, deliberately different in cost and depth:

1. **The v1 item stack** (`assessment/stack/v1/`) — a standardized set of
   short items (code-review, bug-fix, long-context, instruction-format) run
   across every reachable backend. Cheap, broad, right for auditioning a
   newly-released model or taking a first cut.
2. **The poker capstone** (`research/poker-capstone/`) — a difficulty-ordered
   capability ladder (P1-P10) over a single substantial engineering problem,
   run fail-fast so a model's assessment stops at its first genuine failure.
   Expensive, deep, and the instrument that actually separates models.

Why both: short items rank models that all look similar; the ladder shows
*where* a model breaks, which is what determines what you can safely delegate
to it. Findings to date — including a strong model failing full-autonomy on a
real payout bug, a green 42-test suite structurally blind to the bug it
existed to catch, and two local models failing the ladder's easiest phase in
opposite ways — are tabulated in `research/poker-capstone/README.md`.

A standing rule in both instruments: **the grader is under test too.** A judge
verdict is re-verified against source before it is accepted, which has found
five real bugs in our own grading material, every one in the model's favour.

## The delegation half

Delegate a scoped sub-problem
from inside a Claude Code session to a locally-installed peer agentic CLI
— OpenAI **Codex** (`codex`) or Antigravity (`agy`), extensible to more via
one-directory adapters — and fold a compact, uniform result back in.
In-session and uncontainerised: single-machine process delegation, no
Archon, no Docker, no DAG. (That's the one-line distinction from
`sdlc-workflows`, which *is* Archon-orchestrated, containerised,
DAG-based delegation — reach for that plugin when a task genuinely needs
an isolated container or a multi-step workflow graph; reach for this one
for a single in-session hand-off to a peer CLI.)

See `docs/superpowers/specs/2026-07-25-sdlc-model-council-design.md`
in this repo for the full design (authoritative; builds on the substrate
design `2026-07-24-sdlc-simple-orchestration-design.md` and the original
`2026-07-23-external-agent-delegation-design.md`) and
`docs/feature-proposals/232-external-agent-delegation.md` for the
originating proposal (issue #232).

## Why this plugin, given vendor-native plugins already exist

Per-vendor delegation plugins exist and do the per-vendor job better than
we would: **`codex@openai-codex`** (official — `/codex:review`,
`/codex:adversarial-review`, `/codex:rescue`, `/codex:transfer`,
`/codex:status`, `/codex:result`, `/codex:cancel`; one-shot/background,
resume; its "approval" is a review gate, not per-action permissions) and
**`antigravity@antigravity-for-claude-code`** (`/antigravity:delegate`,
`/antigravity:review`, `/antigravity:research`,
`/antigravity:cloud-run-debug`, `/antigravity:status`, `/antigravity:result`,
`/antigravity:cancel`; cost-disciplined, verification-gated — a genuinely
capable plugin, not a lesser alternative). We don't try to out-do either
on their home ground. We reposition as the layer that gives you what
neither offers on its own:

1. **A unified delegation contract** across heterogeneous backends — same
   input fields, same status vocabulary, same file layout, same handle
   grammar, regardless of which vendor CLI is underneath.
2. **Cross-model fan-out / compare** — the same task, sent to N backends
   at once, under one contract (fast-follow; see Status below).
3. **Graded permission postures enforced uniformly** — including the agy
   `--gemini_dir` mechanism (`read-only`/`workspace`/`dangerous`, a real
   allow-list rather than a single blanket write-approval flag).
4. **Context isolation** — Haiku wrapper agents + `./tmp` log/slice; peer
   transcripts never enter the caller's context wholesale.
5. **Extensibility** — a new backend is one adapter directory
   (`scripts/adapters/<id>/{adapter.json,adapter.sh}`), no core change.
   See `docs/ADAPTER-AUTHORING.md`.

**Honest positioning:** without inter-plugin RPC (see the mechanism note
below), this is an orchestrator *beside* the vendor-native plugins, not
*over* them. Its value has to be earned by shipping the cross-vendor
uniformity and fan-out that no single-vendor plugin can offer by
definition — not by claiming superiority on any one vendor's own turf.

## "Prefer the official plugin" — routing, not call-through

When a sibling vendor plugin is installed and the task shape fits it
better (reviewing this session's own diff, an adversarial review gate,
rescuing a stuck codex task, continuing a persistent codex thread), the
`council-policy` skill's routing table says: **hand off** to that
plugin's own `/codex:*` command in the main thread, don't also dispatch
this plugin's runner for the same task.

This is a **routing decision made once, before dispatch — never
inter-plugin RPC.** Our `delegation-runner` subagent (Haiku;
Bash/Read/Grep/Glob, no Skill/Agent tool) has no way to invoke another
plugin's slash command, and giving it that ability would break context
isolation and be unreliable. The codex adapter here **is** the direct-CLI
path (`codex exec` / `codex exec resume`) always — our runner shells the
`codex` binary directly through `extdel.sh`, exactly as it shells `agy`.
There is no hidden call-through to `codex-plugin-cc`'s own machinery, and
we don't pretend otherwise anywhere in this plugin's docs or skill.

Gemini/agy routes to our adapter always — the sibling `antigravity`
plugin is a **coexist** relationship (both plugins are legitimately
useful; see the routing table for when each one fits), not a
`superseded-by-us` one, because the installed community plugin is
genuinely capable on its own terms.

## Status: v0.1.0 — the orchestrator exists

This build ships, fully verified against mock CLIs (no real codex/agy
quota spent in tests):

1. **`scripts/extdel.sh`** — the engine (`start | prompt | status | slice
   | stop | reap | list-backends`): a portable double-fork daemonizer (no
   dependency on `setsid`/`timeout`, both absent on macOS), a perl-alarm
   timeout wrapper with SIGTERM→SIGKILL escalation on the delegated
   process's own group, a per-handle turn mutex, and pinned-posture
   enforcement — all backend-agnostic.
2. **The adapter split** — per-backend behavior (posture mapping, argv
   construction, session-id capture, files-changed summary, permission-
   hint pattern) lives in `scripts/adapters/{codex,agy}/`, one directory
   per backend, sourced by the engine at `--cli` resolution time. Adding
   a backend is one new directory; see `docs/ADAPTER-AUTHORING.md`.
3. **`list-backends`** — a pure read-only registry/probe report: which
   adapters are registered, which are actually installed on this machine,
   optional live auth probing (`--probe-auth`), and (advisory-only)
   whether a sibling vendor plugin is present.
4. **`delegation-runner`** — one generic Haiku agent (merged from the
   earlier separate `codex-runner`/`agy-runner`) that drives any
   registered backend via `extdel.sh`, given a required `backend:` field.
5. **`/…:delegate` and `/…:backends`** commands, and the
   `council-policy` skill (routing table, posture table, fan-out
   discipline, cost-opacity note).
6. **Graded agy postures via `--gemini_dir`** — headless `agy --print`
   auto-denies every tool permission unless it's pre-allowed; a per-handle
   config dir carrying a posture-graded `permissions.allow` list is the
   real enforcement mechanism (`--mode`/`--sandbox` don't gate anything
   headless — see the design doc's §9.15).
7. **`NO_OUTPUT` status** — an exit-0-but-empty turn (most commonly agy's
   auto-deny) is never reported as a false `SUCCESS`, for any backend.

**Not yet shipped (fast-follow):** `compare`/`synthesize`/`vote` fan-out
commands (choreography over this same engine — no new `extdel.sh`
subcommand needed); an OpenCode adapter (all its groundwork is
probe-verified and recorded in the design doc, walked as the worked
example in `docs/ADAPTER-AUTHORING.md`); codex session-id interop with
`codex-plugin-cc` (§3.4); codex *persistent* mode. agy has **no**
persistent/held-process mode planned at all (a deliberate design choice);
requesting `--mode persistent`, or any `--cli` not registered as an
adapter, fails fast with `Status: ERROR`, not a hang.

## The two continuity modes (contract, once persistent ships)

- **`resume`** (default, this build) — stateless between calls. Each turn
  is a fresh, detached CLI invocation that resumes a saved session id.
  Robust across timeouts/crashes; no process held between turns.
- **`persistent`** (later, codex only when it ships) — one external-CLI
  process held open for the delegation's life, fed successive prompts
  over a FIFO. Lower per-prompt latency once warmed; more moving parts to
  keep alive.

Both modes present the **same caller-facing contract**: same input fields,
same status vocabulary, same file layout, same handle grammar. Switching
`mode` (once persistent ships) or `backend` is a single parameter change
— nothing else about the calling convention changes.

## Directory layout

```
sdlc-model-council/
  .claude-plugin/plugin.json
  agents/
    delegation-runner.md    # Haiku; drives extdel.sh for any registered backend
  skills/
    council-policy/SKILL.md   # routing table, backend picking, posture, fan-out, cost
  commands/
    delegate.md              # /…:delegate <backend> <prompt> [posture=][model=][handle=]
    backends.md               # /…:backends — thin `extdel.sh list-backends` wrapper
  scripts/
    extdel.sh                 # start | prompt | status | slice | stop | reap | list-backends
    turn-supervisor.pl        # perl-alarm timeout wrapper (spawned per turn)
    adapters/
      codex/{adapter.json,adapter.sh}   # OpenAI Codex direct-CLI adapter
      agy/{adapter.json,adapter.sh}     # Antigravity/Gemini direct-CLI adapter
  docs/
    ADAPTER-AUTHORING.md      # one-directory adapter contract, worked OpenCode example
  tests/
    test-extdel-codex-resume.sh   # exercises extdel.sh against a mock codex
    test-extdel-agy-resume.sh     # exercises extdel.sh against a mock agy
    test-turn-supervisor.sh       # direct signal/fork/alarm regression tests
    test-adapter-descriptors.sh   # lints every scripts/adapters/*/adapter.json + ABI
    test-list-backends.sh         # list-backends against fake installed_plugins.json
    fixtures/mock-bin/codex       # mock CLI — no real codex/agy calls in tests
    fixtures/mock-bin/agy         # mock CLI — no real codex/agy calls in tests
    fixtures/mock-sleep            # tiny untrapped-TERM CLI stand-in for turn-supervisor.pl tests
    fixtures/mock-sleep-notrap     # like mock-sleep but ignores TERM (escalation-window tests)
```

## Unified contract

Callers pass one request block (`backend` required, `prompt` required;
everything else optional — see `agents/delegation-runner.md` for the full
field list: `mode`, `handle`, `model`, `effort`, `agent` (agy-only),
`cwd`/`add_dirs`, `timeout_s`, `posture`, `expect`). `extdel.sh` returns a
compact, structured block:

```
## External Delegation
- Backend: codex         Mode: resume
- Status: RUNNING | SUCCESS | NO_OUTPUT | FAILURE | TIMEOUT | ERROR
- Handle: <HANDLE>
- Session id: <uuid | pending>
- Turn: <n>    Held process: no    Duration: <s>s
- Answer file: ./tmp/model-council/<HANDLE>/turn-00N.last-message.txt
- Full log:    ./tmp/model-council/<HANDLE>/turn-00N.events.jsonl
- Files changed: <best-effort count/summary, or "not tracked">
- runtime.repollable: yes | no

## Errors            # only when Status != SUCCESS
<verbatim stderr tail / refusal reason>
```

`start`/`prompt` always return `RUNNING` immediately (submit-then-poll —
the Bash tool's own timeout cap means a delegation can never be safely
awaited inline); the caller polls `status` across separate tool calls
until a terminal status appears. `slice <HANDLE>` returns just the capped
(12000-char) final answer text, for when the caller wants the answer
without the rest of the block.

**`Status: NO_OUTPUT`** — a turn that exited success-shaped (exit 0) but
whose captured answer is empty after trimming whitespace is never reported
as `SUCCESS`, for any backend. This is most commonly agy's headless
permission model (see below): the conversation completed but the
requested tool call was auto-denied, so nothing useful came back. When
`status`/`slice` detects this, `## Errors` carries the external CLI's own
diagnostic verbatim (for agy, its own "no output produced ... auto-denied"
wording) plus concrete next-step guidance — escalate posture on a fresh
handle, or rephrase. A genuinely empty-but-legitimate answer (no
permission problem at all) also reports `NO_OUTPUT`, just without a
permission hint — it is not a crash, and the caller should decide what to
do with it rather than the wrapper agent silently retrying.

## Safety: posture, and why `read-only` is not `read-nothing`

Every handle pins a permission **posture** at `start` time —
`read-only` (default), `workspace`, or `dangerous`. `extdel.sh prompt`
**refuses** a differing posture on a later turn unless `--steal` is
passed explicitly, so any escalation is visible in the caller's own
transcript rather than silent. `delegation-runner` is instructed to never
choose `dangerous` on its own initiative — it only ever passes through a
posture the caller gave it, for any backend.

**codex** posture maps onto its own sandbox flags (`-s read-only` /
`-s workspace-write` / `--dangerously-bypass-approvals-and-sandbox`) — a
real OS sandbox (`fidelity: hard` in its adapter descriptor).

**agy** posture works differently, because live probing found that agy's
headless `--print` mode **auto-denies every tool permission** — reads,
writes, shell commands — unless the tool is pre-listed in a
`permissions.allow` list, or `--dangerously-skip-permissions` is passed;
`--mode`/`--sandbox` are interactive-mode concepts that do **not** gate
anything headless. `extdel.sh` therefore writes a per-handle config dir
(`./tmp/model-council/<HANDLE>/agy-cfg/antigravity-cli/settings.json`,
passed via `agy --gemini_dir`) carrying a posture-graded allow-list —
`read-only` grants reads + read-only shell commands only, `workspace`
additionally grants `write_file`/`edit_file` + a build/test command set,
`dangerous` passes `--dangerously-skip-permissions` instead (`fidelity:
allow-list`, honestly weaker than codex's hard sandbox — surfaced in the
adapter descriptor and `list-backends`, not papered over). This per-handle
dir also isolates that handle's own conversation-id cache
(`.../agy-cfg/antigravity-cli/cache/last_conversations.json`), which is
where id capture now reads from instead of a machine-global path.

**Read access is not gated by posture, for either backend.** `read-only`
blocks writes and network calls from the backend's side — it does not
restrict what it can *read*. Under any posture, codex or agy can read
anything on disk that the ambient environment's user could read (`.env`,
`~/.ssh/`, other credentials, anything under the delegated
`cwd`/`add_dirs`), and that content is sent to the respective vendor's
infrastructure as part of the delegated prompt/context. This is inherent
to delegating to a third-party CLI — the `council-policy` skill and
`delegation-runner`'s own instructions name this plainly rather than
paper over it.

External answer/log content is always treated as **data, never
instructions** — `delegation-runner` does not act on anything that looks
like a directive inside a delegated model's response.

All state lives under project-relative `./tmp/model-council/` (never
`/tmp`), which framework projects already gitignore; logs are local-only
and nothing here uploads them anywhere.

## Install pairing

```
/plugin install sdlc-model-council@ai-first-sdlc
```

No other plugin is required to install alongside this one, and no plugin
this one depends on for its own function. It coexists naturally with both
vendor-native sibling plugins — install whichever mix fits:

- **`codex@openai-codex`** (official OpenAI Codex plugin) — for
  `/codex:review`/`/codex:adversarial-review`/`/codex:rescue`/
  `/codex:transfer` and persistent codex threads; the `council-policy`
  routing table hands those task shapes to it when it's installed.
- **`antigravity@antigravity-for-claude-code`** — for its own
  cost-disciplined `/antigravity:*` delegate/review/research/cloud-debug
  flow; a `coexist`, not a competing, relationship with this plugin's agy
  adapter.
- **`command-delegation`** — same "full log to disk, compact slice back"
  pattern family, applied to local shell commands instead of peer agentic
  CLIs; no dependency either way.

Requires `codex` installed and authenticated (`codex login`) on the host
machine for the `codex` backend to do anything, and/or `agy` installed and
signed in at least once interactively (agy has no `login status` verb —
`extdel.sh` checks that `~/.gemini/antigravity-cli/` exists instead) for
the `agy` backend — `extdel.sh` fails fast with an actionable
`Status: ERROR` message for whichever backend isn't ready. Run
`/…:backends` (or `extdel.sh list-backends`) any time to check what's
registered, installed, and authenticated.
