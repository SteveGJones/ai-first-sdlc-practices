---
description: Delegate a scoped sub-problem to an external agentic CLI backend (codex, agy, …) and get a compact result back.
argument-hint: "<backend> <prompt> [posture=read-only|workspace|dangerous] [model=...] [handle=...]"
---

Delegate the following request to a peer agentic CLI backend through this
plugin's `delegation-runner` agent.

Arguments: `$ARGUMENTS`

Parse `$ARGUMENTS` as: the first whitespace-delimited token is the
**backend** (`codex`, `agy`, or any other id `extdel.sh list-backends`
shows as registered); the rest, up to any trailing `key=value` tokens, is
the **prompt**; trailing `posture=`, `model=`, `effort=`, `handle=`,
`cwd=`, `timeout_s=` tokens are optional fields to pass through. If no
backend is given, do not guess — ask, or run
`${CLAUDE_PLUGIN_ROOT}/scripts/extdel.sh list-backends` and offer the
installed options.

Do this:

1. **Consult the routing table first.** Load the `council-policy`
   skill (in particular its §3.3 routing table) before dispatching
   anything. Some request shapes — reviewing this session's own diff, an
   adversarial review gate, rescuing a stuck codex task, continuing a
   persistent codex thread — should be **handed off** to the matching
   `/codex:*` sibling-plugin command in this main thread instead of
   dispatched through this plugin, if that sibling plugin is installed
   (check your own available-skills listing for `/codex:*` commands
   first; only fall back to a `list-backends` probe if you can't tell).
   If the routing table says hand off, do that instead of continuing
   below, and say so plainly.
2. **Otherwise, dispatch `delegation-runner`** (the Agent tool, this
   plugin's agent) with the parsed fields: `backend`, `prompt`, and any
   optional fields given (`posture` defaults to `read-only` if omitted —
   never choose `dangerous` on the caller's behalf). If `handle=` was
   given, this is a continuation of an existing delegation — pass it
   through so the runner resumes rather than starting fresh.
3. **Report the runner's return verbatim** — the `## External Delegation`
   block, `## Answer`, and `## Errors` if present. Do not summarize away
   the status line, handle, or session id; the caller may need them to
   continue the conversation later.

Remember the fan-out cap of 5 concurrent external sessions (see
`council-policy`) if this command is being invoked multiple times in
quick succession for a manual compare — `/…:delegate` itself only ever
dispatches one backend per call.
