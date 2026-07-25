# sdlc-simple-orchestration

Delegate a scoped sub-problem to an external agentic CLI — OpenAI **Codex**
(`codex`) or Antigravity (`agy`) — from inside a Claude Code session, and
fold a compact result back in. The full peer-agent transcript is written to
a durable `./tmp/simple-orchestration/` log; only a small, structured slice
returns to the caller's context. Same pattern family as `command-delegation`
(full output to disk, compact slice back), applied to *peer agentic CLIs*
rather than shell commands.

See `docs/superpowers/specs/2026-07-23-external-agent-delegation-design.md`
in this repo for the full design (§9 is authoritative over §1–§8 wherever
they conflict) and `docs/feature-proposals/232-external-agent-delegation.md`
for the originating proposal (issue #232).

## Status: Stage 1 + 2 + 3 (this build)

This build ships, fully verified against mock CLIs (no real codex/agy
quota spent in tests):

1. **`scripts/extdel.sh`** — the primitives (`start | prompt | status |
   slice | stop | reap`) that own all process plumbing: a portable
   double-fork daemonizer (no dependency on `setsid`/`timeout`, both absent
   on macOS), a perl-alarm timeout wrapper with SIGTERM→SIGKILL escalation
   on the delegated process's own group, a per-handle turn mutex, and
   pinned-posture enforcement.
2. **codex resume mode** — submit-then-poll `codex exec` / `codex exec
   resume`, the `codex-runner` Haiku agent that drives it.
3. **agy resume mode** — submit-then-poll `agy --print` /
   `agy --conversation ID --print`, the `agy-runner` Haiku agent that
   drives it, and cwd-keyed id capture from a per-handle isolated
   `last_conversations.json` (the sole reliable id source for a `--print`
   delegation turn — see the design doc's §9.14 live-probe findings).
4. **Graded agy postures via `--gemini_dir`** — headless `agy --print`
   auto-denies every tool permission unless it's pre-allowed; a per-handle
   config dir carrying a posture-graded `permissions.allow` list is now
   the real enforcement mechanism (`--mode`/`--sandbox` don't gate
   anything headless — see §9.15 of the design doc).
5. **`NO_OUTPUT` status** — an exit-0-but-empty turn (most commonly agy's
   auto-deny) is never reported as a false `SUCCESS`, for both CLIs.

Both CLI-runner agents share the `agent-delegation-policy` skill, which
now also covers when to pick codex vs agy.

**Not yet shipped:** codex *persistent* mode — a held `codex mcp-server`
daemon over a FIFO (Stage 4) — and the `delegate-status`/reap skill
(Stage 5). agy has **no** persistent/held-process mode planned at all (a
deliberate design choice — see the design doc §3.0(c)/§3.2); requesting
`--mode persistent` for either CLI, or any `--cli` other than `codex`/
`agy`, from `extdel.sh` fails fast with `Status: ERROR`, not a hang.

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
sdlc-simple-orchestration/
  .claude-plugin/plugin.json
  agents/
    codex-runner.md        # Haiku; drives extdel.sh for codex resume mode
    agy-runner.md           # Haiku; drives extdel.sh for agy resume mode
  skills/
    agent-delegation-policy/SKILL.md   # when to delegate out vs inline, codex vs agy
  scripts/
    extdel.sh               # start | prompt | status | slice | stop | reap
    turn-supervisor.pl      # perl-alarm timeout wrapper (spawned per turn)
  tests/
    test-extdel-codex-resume.sh   # exercises extdel.sh against a mock codex
    test-extdel-agy-resume.sh     # exercises extdel.sh against a mock agy
    test-turn-supervisor.sh       # direct signal/fork/alarm regression tests
    fixtures/mock-bin/codex       # mock CLI — no real codex/agy calls in tests
    fixtures/mock-bin/agy         # mock CLI — no real codex/agy calls in tests
    fixtures/mock-sleep           # tiny untrapped-TERM CLI stand-in for turn-supervisor.pl tests
    fixtures/mock-sleep-notrap    # like mock-sleep but ignores TERM (escalation-window tests)
```

## Unified contract

Callers pass one request block (`prompt` required; everything else
optional — see `agents/codex-runner.md` for the full field list: `cli`,
`mode`, `handle`, `model`, `effort`, `cwd`/`add_dirs`, `timeout_s`,
`posture`, `expect`). `extdel.sh` returns a compact, structured block:

```
## External Delegation
- CLI: codex            Mode: resume
- Status: RUNNING | SUCCESS | NO_OUTPUT | FAILURE | TIMEOUT | ERROR
- Handle: <HANDLE>
- Session id: <uuid | pending>
- Turn: <n>    Held process: no    Duration: <s>s
- Answer file: ./tmp/simple-orchestration/<HANDLE>/turn-00N.last-message.txt
- Full log:    ./tmp/simple-orchestration/<HANDLE>/turn-00N.events.jsonl
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
as `SUCCESS`. This is most commonly agy's headless permission model (see
below): the conversation completed but the requested tool call was
auto-denied, so nothing useful came back. When `status`/`slice` detects
this, `## Errors` carries the external CLI's own diagnostic verbatim (for
agy, its own "no output produced ... auto-denied" wording) plus concrete
next-step guidance — escalate posture on a fresh handle, or rephrase.
A genuinely empty-but-legitimate answer (no permission problem at all)
also reports `NO_OUTPUT`, just without a permission hint — it is not a
crash, and the caller should decide what to do with it rather than the
wrapper agent silently retrying.

## Safety: posture, and why `read-only` is not `read-nothing`

Every handle pins a permission **posture** at `start` time —
`read-only` (default), `workspace`, or `dangerous`. `extdel.sh prompt`
**refuses** a differing posture on a later turn unless `--steal` is
passed explicitly, so any escalation is visible in the caller's own
transcript rather than silent. The wrapper agents (`codex-runner`,
`agy-runner`) are instructed to never choose `dangerous` on their own
initiative — they only ever pass through a posture the caller gave them.

**codex** posture maps onto its own sandbox flags (`-s read-only` /
`-s workspace-write` / `--dangerously-bypass-approvals-and-sandbox`).

**agy** posture works differently, because live probing found that agy's
headless `--print` mode **auto-denies every tool permission** — reads,
writes, shell commands — unless the tool is pre-listed in a
`permissions.allow` list, or `--dangerously-skip-permissions` is passed;
`--mode`/`--sandbox` are interactive-mode concepts that do **not** gate
anything headless. `extdel.sh` therefore writes a per-handle config dir
(`./tmp/simple-orchestration/<HANDLE>/agy-cfg/antigravity-cli/settings.json`,
passed via `agy --gemini_dir`) carrying a posture-graded allow-list —
`read-only` grants reads + read-only shell commands only, `workspace`
additionally grants `write_file`/`edit_file` + a build/test command set,
`dangerous` passes `--dangerously-skip-permissions` instead. This
per-handle dir also isolates that handle's own conversation-id cache
(`.../agy-cfg/antigravity-cli/cache/last_conversations.json`), which is
where id capture now reads from instead of a machine-global path.

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

All state lives under project-relative `./tmp/simple-orchestration/` (never
`/tmp`), which framework projects already gitignore; logs are local-only
and nothing here uploads them anywhere.

## Install pairing

```
/plugin install sdlc-simple-orchestration@ai-first-sdlc
```

No other plugin is required to install alongside this one. It pairs
naturally with `command-delegation` (same "full log to disk, compact slice
back" pattern family, applied to local shell commands instead of peer
agentic CLIs) if that's also installed, but there's no dependency either
way. Requires `codex` installed and authenticated (`codex login`) on the
host machine for `codex-runner` to do anything, and/or `agy` installed and
signed in at least once interactively (agy has no `login status` verb —
`extdel.sh` checks that `~/.gemini/antigravity-cli/` exists instead) for
`agy-runner` — `extdel.sh` fails fast with an actionable `Status: ERROR`
message for whichever CLI isn't ready.
