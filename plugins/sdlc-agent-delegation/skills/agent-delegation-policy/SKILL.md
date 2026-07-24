---
name: agent-delegation-policy
description: >
  Policy for when to delegate a sub-problem to an external agentic CLI
  (codex, agy) via codex-runner/agy-runner versus handling it inline or
  with an internal Claude subagent. Consult before delegating out to a
  peer agentic CLI, before choosing a permission posture, or before
  fanning out more than one external delegation concurrently.
---

# Agent Delegation Policy

## Delegate out to codex-runner (or, once shipped, agy-runner)

Delegate to an external agentic CLI when the value is specifically in a
**different model/provider's** take on the problem, not just in offloading
verbose output (that's what `command-delegation`'s `command-runner` family
is for):

- **Cross-model second opinion.** You want GPT's (codex) or Gemini's (agy)
  independent read on a design, a bug, or a piece of code — to compare
  against or merge with your own analysis.
- **Independent fan-out sub-problems.** N genuinely independent sub-tasks
  where you want N concurrent external sessions rather than doing them
  serially yourself or via N internal subagents.
- **Continuing an existing external conversation.** The caller already has
  a `handle` from a prior codex-runner turn and wants to continue that
  specific external session (pass `handle:` through — never start a new
  one when continuity with the prior turn matters).

## Keep it inline or use an internal subagent instead

- The sub-problem doesn't benefit from a different model's perspective —
  use a Claude subagent (or handle it directly).
- You need to react to output turn-by-turn, mid-stream — external
  delegation is submit-then-poll; you get a compact answer only once each
  turn finishes, not a live stream.
- The task is destructive/mutating and needs a human in the loop for
  approval — external CLIs run non-interactively (`codex exec`), so
  anything requiring an approval prompt will just fail under `read-only`/
  `workspace` posture rather than pausing for a human. That's intended
  behavior, not a bug to route around.
- It's a local shell command, build, test suite, or log to watch — that's
  `command-delegation`'s territory (`command-runner`/`build-runner`/
  `test-runner`/`process-monitor`), not this plugin.

## Posture: default read-only, escalate only when the caller says so

| posture | what it allows | when |
|---|---|---|
| `read-only` (**default**) | codex can read and reason; no writes, no network from its side | the default for every delegation unless told otherwise |
| `workspace` | codex can write files within its working directory | only when the caller explicitly wants codex to make edits |
| `dangerous` | bypasses codex's own approvals/sandbox entirely | only when the caller explicitly opts in — never chosen by the wrapper itself |

**Escalation is a caller decision, never the wrapper's.** codex-runner is
instructed to never select `dangerous` on its own initiative, and a
handle's posture is *pinned* at `start` time — `extdel.sh prompt` refuses a
differing posture unless `--steal` is passed explicitly, so any escalation
mid-conversation is visible in the transcript rather than silent.

**`read-only` is not `read-nothing`.** The sandbox posture restricts what
codex can *do* (write, run network-touching commands) — it does not
restrict what codex can *read*. Under any posture, codex can read any file
on disk that the calling environment's user could read: `.env` files,
`~/.ssh/`, credentials, anything in the delegated `cwd`/`add_dirs`. That
content becomes part of what's sent to OpenAI's infrastructure as prompt
context. This is inherent to delegating to an external CLI, not a bug in
this plugin — name it plainly to the caller if a delegation is pointed at
a directory that plausibly contains secrets, rather than silently
proceeding.

## Fan-out and process count

Each delegation is submit-then-poll, not a held daemon, in the codex-resume
mode this build ships — so a single delegated turn is one detached process
while it runs, not three. (Codex *persistent* mode, when it ships, will use
a daemon + holder + watchdog per handle — 3 processes per handle — worth
knowing in advance: **N concurrent persistent handles ≈ 3N processes**,
against the family's fan-out cap of **5 concurrent external sessions**.)
Apply the cap of 5 regardless of mode when deciding how many codex-runner
dispatches to fan out at once — it exists to bound both process count and
concurrent spend against the external provider's quota.

## Cost is real and invisible to Claude's own telemetry

Delegated turns spend the external provider's (OpenAI's) quota/credits,
not Anthropic's — and that spend does not show up in Claude Code's own
token/cost reporting. Codex's `--json` event stream includes token-count
events, and the full transcript is retained under
`./tmp/agent-delegation/<HANDLE>/`, so it's auditable after the fact, but
nothing surfaces it proactively today. Don't fan out delegations casually;
each one is real spend on someone else's bill.
