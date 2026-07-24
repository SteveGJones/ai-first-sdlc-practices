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

## Delegate out to codex-runner or agy-runner

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
  a `handle` from a prior codex-runner/agy-runner turn and wants to
  continue that specific external session (pass `handle:` through — never
  start a new one when continuity with the prior turn matters).

## Which platform: codex vs agy

Both CLIs present the identical caller-facing contract (§4 of the design
doc) — the choice is purely about which model/provider's take you want:

| | `codex` (codex-runner) | `agy` (agy-runner) |
|---|---|---|
| Provider / model | OpenAI, GPT | Google Antigravity, Gemini (and other models `agy models` lists) |
| Continuity mode shipped | resume | resume |
| Held-process (`mode: persistent`) | not yet shipped (planned: `codex mcp-server` daemon) | **not planned as a held process at all** — agy's own continuity is server-side/id-addressable, so a pty-held interactive session would trade real state for fragile heuristic completion detection; `mode: persistent` is a clean `Status: ERROR`, not attempted |
| Headless permission model | a real sandbox (`-s read-only`/`workspace-write`) gates tool use non-interactively | **auto-denies every tool call** (`read_file`/`command`/`write_file`/`edit_file`) in `--print` mode unless pre-allowed — `--mode`/`--sandbox` do NOT gate anything headless (live-probed; see the design doc's §9.15) |
| `read-only` posture mapping | `-s read-only` | a per-handle `--gemini_dir` config carrying a `permissions.allow` list scoped to reads + read-only shell commands — the real enforcement lever, not `--mode`/`--sandbox` |
| Answer source | `-o`/`--output-last-message` file | plain stdout (no separate answer file from the CLI itself — `extdel.sh` captures it into the same `turn-NNN.last-message.txt` convention) |

Pick `codex` when the caller wants GPT specifically; pick `agy` when they
want Gemini (or another model `agy` exposes) specifically. If the caller
just says "get a second opinion" without naming a provider, ask rather
than guessing, or default to whichever the caller's project already has
authenticated/working.

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
  with a `ReviewDecision` — that a future Mode B could drive for
  fine-grained, in-conversation approval; agy has no equivalent verb in
  its machine channel. Out of scope for this build — see the design doc's
  §9.15 "Design consequences" for the roadmap.)
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

**Escalation is a caller decision, never the wrapper's.** codex-runner and
agy-runner are both instructed to never select `dangerous` on their own
initiative, and a handle's posture is *pinned* at `start` time —
`extdel.sh prompt` refuses a differing posture unless `--steal` is passed
explicitly, so any escalation mid-conversation is visible in the
transcript rather than silent. This pin is enforced identically for both
CLIs — `extdel.sh` refuses the mismatch before it ever builds a command
line, regardless of which platform the handle is for.

**`read-only` is not `read-nothing`.** The sandbox posture restricts what
the external model can *do* (write, run network-touching commands) — it
does not restrict what it can *read*. Under any posture, codex or agy can
read any file on disk that the calling environment's user could read:
`.env` files, `~/.ssh/`, credentials, anything in the delegated
`cwd`/`add_dirs`. That content becomes part of what's sent to the external
provider's infrastructure (OpenAI for codex, Google for agy) as prompt
context. This is inherent to delegating to an external CLI, not a bug in
this plugin — name it plainly to the caller if a delegation is pointed at
a directory that plausibly contains secrets, rather than silently
proceeding.

## Fan-out and process count

Each delegation is submit-then-poll, not a held daemon, in the resume mode
this build ships for both CLIs — so a single delegated turn is one
detached process while it runs, not three, whether it's codex or agy.
(Codex *persistent* mode, when it ships, will use a daemon + holder +
watchdog per handle — 3 processes per handle — worth knowing in advance:
**N concurrent persistent handles ≈ 3N processes**, against the family's
fan-out cap of **5 concurrent external sessions**. agy has **no**
persistent/held-process mode planned at all — see the platform comparison
table above — so this concern is codex-only.) Apply the cap of 5
regardless of CLI or mode when deciding how many codex-runner/agy-runner
dispatches to fan out at once — it exists to bound both process count and
concurrent spend against the external provider's quota.

**agy's old cross-handle id-capture race is now closed by construction:**
earlier builds read a single machine-global
`~/.gemini/antigravity-cli/cache/last_conversations.json` keyed by cwd, so
two agy `start` calls landing in the *same* cwd at nearly the same time
could race on which conversation that shared cache ended up recording.
Each handle now gets its own isolated `--gemini_dir`
(`./tmp/agent-delegation/<HANDLE>/agy-cfg/`), so id capture reads a
per-handle cache with nothing else to race against — concurrent
`agy-runner` dispatches in the same cwd no longer contend over id capture
at all. `status` can still surface a `WARNING` if a handle's own isolated
cache entry changes identity out-of-band between turns (now a much
narrower, more anomalous signal than the old cross-process race) — report
it, don't silently trust the newer id.

## `NO_OUTPUT`: an exit-0 turn is not automatically a successful one

Both `codex-runner` and `agy-runner` can report `Status: NO_OUTPUT` — a
turn that exited success-shaped (exit code 0) but whose captured answer
was empty after trimming whitespace. This is never silently upgraded to
`SUCCESS`. It's most common with agy: the headless auto-deny above means a
turn can complete cleanly while the actual requested tool call was denied,
leaving nothing useful in the answer. When that's the cause, `## Errors`
carries agy's own diagnostic verbatim (its "no output produced ...
auto-denied" wording) plus the fix — broaden the posture on a fresh
handle, or rephrase the task to fit the current one. A codex turn can also
exit 0 with an empty `-o` file (e.g. an unretried sandbox denial); the
same check applies there too, CLI-generally. A `NO_OUTPUT` with no
permission hint at all is a legitimately empty answer, not a crash — the
wrapper agents report it as-is rather than fabricating content or
silently retrying.

## Cost is real and invisible to Claude's own telemetry

Delegated turns spend the external provider's quota/credits (OpenAI's for
codex, Google's for agy), not Anthropic's — and that spend does not show
up in Claude Code's own token/cost reporting. Codex's `--json` event
stream includes token-count events; agy's `--log-file` output is retained
per turn. The full transcript for either CLI is kept under
`./tmp/agent-delegation/<HANDLE>/`, so it's auditable after the fact, but
nothing surfaces it proactively today. Don't fan out delegations casually;
each one is real spend on someone else's bill.
