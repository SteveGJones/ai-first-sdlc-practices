# sdlc-agent-delegation

Delegate a scoped sub-problem to an external agentic CLI — OpenAI **Codex**
(`codex`) or Antigravity (`agy`) — from inside a Claude Code session, and
fold a compact result back in. The full peer-agent transcript is written to
a durable `./tmp/agent-delegation/` log; only a small, structured slice
returns to the caller's context. Same pattern family as `command-delegation`
(full output to disk, compact slice back), applied to *peer agentic CLIs*
rather than shell commands.

See `docs/superpowers/specs/2026-07-23-external-agent-delegation-design.md`
in this repo for the full design (§9 is authoritative over §1–§8 wherever
they conflict) and `docs/feature-proposals/232-external-agent-delegation.md`
for the originating proposal (issue #232).

## Status: Stage 1 + 2 (this build)

This build ships exactly two things, fully verified against a mock CLI:

1. **`scripts/extdel.sh`** — the primitives (`start | prompt | status |
   slice | stop | reap`) that own all process plumbing: a portable
   double-fork daemonizer (no dependency on `setsid`/`timeout`, both absent
   on macOS), a perl-alarm timeout wrapper with SIGTERM→SIGKILL escalation
   on the delegated process's own group, a per-handle turn mutex, and
   pinned-posture enforcement.
2. **codex resume mode** — submit-then-poll `codex exec` / `codex exec
   resume`, the `codex-runner` Haiku agent that drives it, and the
   `agent-delegation-policy` skill.

**Not yet shipped:** `agy` support (Stage 3), codex *persistent* mode — a
held `codex mcp-server` daemon over a FIFO (Stage 4) — and the
`delegate-status`/reap skill (Stage 5). Requesting `--cli agy` or `--mode
persistent` from `extdel.sh` fails fast with `Status: ERROR`, not a hang.

## The two continuity modes (contract, once all stages ship)

- **`resume`** (default, this build) — stateless between calls. Each turn
  is a fresh, detached CLI invocation that resumes a saved session id.
  Robust across timeouts/crashes; no process held between turns.
- **`persistent`** (later stage) — one external-CLI process held open for
  the delegation's life, fed successive prompts over a FIFO. Lower
  per-prompt latency once warmed; more moving parts to keep alive.

Both modes present the **same caller-facing contract**: same input fields,
same status vocabulary, same file layout, same handle grammar. Switching
`mode` (once persistent ships) or `cli` (once agy ships) is a single
parameter change — nothing else about the calling convention changes.

## Directory layout

```
sdlc-agent-delegation/
  .claude-plugin/plugin.json
  agents/
    codex-runner.md        # Haiku; drives extdel.sh for codex resume mode
  skills/
    agent-delegation-policy/SKILL.md   # when to delegate out vs inline
  scripts/
    extdel.sh               # start | prompt | status | slice | stop | reap
    turn-supervisor.pl      # perl-alarm timeout wrapper (spawned per turn)
  tests/
    test-extdel-codex-resume.sh   # exercises extdel.sh against a mock codex
    fixtures/mock-bin/codex       # mock CLI — no real codex/agy calls in tests
```

## Unified contract

Callers pass one request block (`prompt` required; everything else
optional — see `agents/codex-runner.md` for the full field list: `cli`,
`mode`, `handle`, `model`, `effort`, `cwd`/`add_dirs`, `timeout_s`,
`posture`, `expect`). `extdel.sh` returns a compact, structured block:

```
## External Delegation
- CLI: codex            Mode: resume
- Status: RUNNING | SUCCESS | FAILURE | TIMEOUT | ERROR
- Handle: <HANDLE>
- Session id: <uuid | pending>
- Turn: <n>    Held process: no    Duration: <s>s
- Answer file: ./tmp/agent-delegation/<HANDLE>/turn-00N.last-message.txt
- Full log:    ./tmp/agent-delegation/<HANDLE>/turn-00N.events.jsonl
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

## Safety: posture, and why `read-only` is not `read-nothing`

Every handle pins a permission **posture** at `start` time —
`read-only` (default), `workspace`, or `dangerous` — mapped onto codex's
own sandbox flags. `extdel.sh prompt` **refuses** a differing posture on
a later turn unless `--steal` is passed explicitly, so any escalation is
visible in the caller's own transcript rather than silent. The wrapper
agent (`codex-runner`) is instructed to never choose `dangerous` on its
own initiative — it only ever passes through a posture the caller gave it.

**Read access is not gated by posture.** `read-only` blocks codex from
*writing* files or making network calls from its side — it does not
restrict what codex can *read*. Under any posture, codex can read anything
on disk that the ambient environment's user could read (`.env`, `~/.ssh/`,
other credentials, anything under the delegated `cwd`/`add_dirs`), and
that content is sent to OpenAI's infrastructure as part of the delegated
prompt/context. This is inherent to delegating to a third-party CLI — the
`agent-delegation-policy` skill and `codex-runner`'s own instructions name
this plainly rather than paper over it.

External answer/log content is always treated as **data, never
instructions** — `codex-runner` does not act on anything that looks like a
directive inside a delegated model's response.

All state lives under project-relative `./tmp/agent-delegation/` (never
`/tmp`), which framework projects already gitignore; logs are local-only
and nothing here uploads them anywhere.

## Install pairing

```
/plugin install sdlc-agent-delegation@ai-first-sdlc
```

No other plugin is required to install alongside this one. It pairs
naturally with `command-delegation` (same "full log to disk, compact slice
back" pattern family, applied to local shell commands instead of peer
agentic CLIs) if that's also installed, but there's no dependency either
way. Requires `codex` installed and authenticated (`codex login`) on the
host machine for the `codex-runner` agent to do anything — `extdel.sh`
fails fast with an actionable `Status: ERROR` message if it isn't.
