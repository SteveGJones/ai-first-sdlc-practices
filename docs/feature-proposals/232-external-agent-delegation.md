# Feature Proposal: External Agent Delegation (codex + agy)

**Proposal Number:** 232
**Status:** Draft
**Author:** Claude (Opus 4.8) — pairing with SteveGJones
**Created:** 2026-07-23
**Target Branch:** `feature/external-agent-delegation`
**Tracking Issue:** #232

---

## Problem Statement

A Claude Code session cannot currently hand a scoped sub-problem to a *peer agentic CLI* — OpenAI's `codex` or Antigravity's `agy` — and fold the result back in. The only way to use those tools today is to leave the session and drive them by hand. That means:

- **No cross-model second opinions.** We cannot cheaply ask Codex (GPT models) or Antigravity (Gemini models) to attempt a sub-problem and compare/merge the answer.
- **No fan-out to peer agents.** Independent sub-problems cannot each get their own external-CLI session running concurrently.
- **Context blow-up if done naively.** Shelling out to `codex exec` from the main thread dumps the peer agent's entire verbose transcript into the caller's context — the exact problem the `command-delegation` pattern family already solves for shell commands.

Both CLIs are installed and authenticated on the target machine (`codex` 0.145.0, `agy` 1.1.5) and both already expose resumable sessions, so the capability is within reach — it just needs a wrapper.

## User Stories

- As an orchestrating agent, I want to delegate a prompt to `codex` or `agy` and get back a **compact result** (not its full transcript) so my context stays clean.
- As an orchestrating agent, I want to keep a delegated session **open across multiple prompts** so I can have a multi-turn exchange with the peer agent.
- As an orchestrating agent, I want each **new subagent to start a new external session** so I can **fan out** N independent sub-problems concurrently.
- As an orchestrating agent, I want to choose between **stateless id-resume** and a **persistent live process** per delegation, depending on whether I care more about robustness or latency/streaming.
- As a developer, I want unauthenticated / missing-CLI cases to **fail fast with an actionable message** rather than hang.

## Proposed Solution

### High-Level Approach

Ship a new plugin in the SDLC family — working name **`sdlc-agent-delegation`** — that provides two **Haiku** wrapper agents and matching skills:

1. **`codex-delegate`** — wraps `codex exec` / `codex exec resume` (Mode A) and a codex daemon (`mcp-server`/`app-server`/`exec-server`, Mode B).
2. **`agy-delegate`** — wraps `agy --print` / `agy --conversation` (Mode A) and `agy -i` (Mode B).

The wrapper is deliberately **Haiku**: orchestration is cheap; the expensive reasoning happens inside the external CLI. Full external output goes to a durable `./tmp/` log; only a compact slice returns to the caller — identical to the `command-delegation` family's contract.

### Technical Approach

**Two continuity modes, both first-class, one shared contract** (per issue #232):

- **Mode A — id-based resume (default).** First prompt starts a session and captures the session/conversation id; each later prompt is a fresh CLI invocation resuming that id (`codex exec resume <id>`, `agy --conversation <ID> --print`). No process held between the subagent's own tool calls — robust across the agent tool re-entering, tolerant of timeouts/crashes.
- **Mode B — persistent live process (opt-in).** One external-CLI process stays running for the subagent's life and is fed successive prompts (`codex mcp-server`/daemon, or `agy -i`). Warm state, lower per-prompt latency, streaming — at the cost of a small process-manager (spawn/detach, feed, frame-response, liveness, teardown).

**Session lifetime = subagent lifetime.** One subagent holds one external session (an id in Mode A, a daemon handle in Mode B). Fan-out = dispatch N subagents (per `superpowers:dispatching-parallel-agents`) → N independent concurrent sessions, in either mode.

**Unified caller-facing contract.** Same input options (`prompt`, `mode`, `cli`, `model`, `effort`, `cwd`/`add-dir`, `timeout`, permission posture, session handle in/out) and same compact return shape (`status`, session/handle id, answer/diff summary, `log_path`, `error`) across both CLIs and both modes. Switching CLI or mode is a single parameter change with nothing else altered.

> The concrete Mode B process-holding mechanism (how a Haiku subagent whose only durable state is the filesystem keeps one process alive across turns — detached daemon + FIFO/socket handle under `./tmp/` vs. codex's purpose-built server subcommands vs. `agy -i` via pty) is being pinned down in the accompanying architecture design (Fable-tier) and will be folded into `docs/architecture/` before implementation.

**Delegation tiers for building this** (per the maintainer's direction):
- **Fable** — the hard architecture (Mode B lifecycle, I/O framing) and the pre-implementation design review.
- **Sonnet** — execution (writing agents, skills, plugin scaffolding, tests).
- **Haiku** — the shipped wrapper agents themselves (`codex-delegate`, `agy-delegate`).

### Alternatives Considered

1. **Single mode only (id-resume).** Simpler, but the maintainer explicitly requires both modes; persistent mode gives warm state / streaming that id-resume cannot.
2. **Drive the CLIs inline from the main thread.** Rejected — dumps the full peer transcript into the caller's context and blocks the main thread; defeats the point of delegation.
3. **A single generic "external-agent" agent parameterised by CLI.** Rejected for v1 — codex and agy differ enough in flags, session addressing, and Mode B transport that two focused Haiku agents are clearer and easier to test. A shared skill/policy doc keeps them consistent.
4. **MCP-only integration (register codex `mcp-server` as an MCP server for Claude Code).** Interesting and possibly a future path, but it doesn't cover `agy`, doesn't give the fan-out-via-subagents story, and couples us to MCP wiring. Keep `mcp-server` as one *Mode B transport option*, not the whole design.

---

## Implementation Plan

### Phase 1: Design & Specify (this phase)
- [x] Feature proposal (this doc)
- [ ] [P] Fable-tier architecture design — Mode B lifecycle, I/O framing, unified contract
- [ ] [P] Plugin structure decision — name, agent/skill layout, marketplace + release-mapping entries
- [ ] Architecture docs in `docs/architecture/` (as required by CONSTITUTION for new components)
- [ ] Fable-tier design review before any code

### Phase 2: Mode A (id-resume) — the robust default
- [ ] Plugin scaffold: `plugin.json`, README, marketplace entry, release-mapping
- [ ] `codex-delegate` Haiku agent + skill — `codex exec` + `resume`, compact-return + `./tmp/` log
- [ ] `agy-delegate` Haiku agent + skill — `agy --print` + `--conversation`, compact-return + `./tmp/` log
- [ ] Auth/CLI preflight (fast-fail), timeouts, safe permission defaults
- [ ] Tests: single prompt, multi-prompt resume, missing-CLI, unauth

### Phase 3: Mode B (persistent process)
- [ ] Process manager: spawn/detach, handle file under `./tmp/`, feed prompt, frame response, liveness, teardown-on-exit
- [ ] `codex` Mode B transport (daemon)
- [ ] `agy -i` Mode B transport
- [ ] Reap orphaned daemons; tests for liveness + teardown

### Phase 4: Fan-out, docs, release
- [ ] Demonstrate N subagents → N independent sessions, both modes
- [ ] Docs: README, AGENT-INDEX / CLAUDE.md plugin table, skill docs
- [ ] Release-plugin packaging; retrospective; PR

**Dependencies:** `codex` and `agy` installed & authenticated; existing `command-delegation` conventions as the pattern reference.

---

## Acceptance Criteria

```
Given a caller with codex installed and authenticated
When it delegates a prompt to codex-delegate in Mode A
Then it receives a compact result plus a session id, and the full transcript is written to ./tmp/
```

```
Given a codex-delegate subagent that has run one prompt in Mode A
When the caller sends a second prompt to the same subagent
Then codex resumes the same session id and answers with prior context
```

```
Given a caller using agy-delegate in Mode B (persistent)
When it sends three successive prompts to the same subagent
Then all three are served by a single long-lived agy process, which is torn down when the subagent exits
```

```
Given both delegate agents present the same contract
When the caller switches mode: resume -> persistent (or cli: codex -> agy)
Then no other caller-side parameter changes are required
```

```
Given N sub-problems dispatched as N subagents
When they run concurrently
Then each holds an independent external session and results do not cross-contaminate
```

```
Given a CLI that is not installed or not authenticated
When a delegation is attempted
Then the agent fails fast with an actionable message (no hang), and Mode B leaves no orphaned process
```

---

## Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Mode B: Haiku subagent cannot hold a live process across its own tool calls (filesystem-only durable state) | High | High | Fable architecture spike resolves this first; fall back to detached daemon + socket/FIFO handle, or codex's own server subcommands; if truly infeasible for a CLI, ship Mode A for it and document |
| Response-complete framing unreliable (can't tell when peer agent finished) | Medium | High | Per-transport completion detection (exit code for one-shot; JSON-RPC framing for mcp-server; sentinel/idle-timeout for pty); always cap with a timeout |
| Orphaned Mode B daemons leak processes | Medium | Medium | Handle files under `./tmp/`; teardown on subagent exit; reaper that kills daemons past a max-age |
| External CLI auth expiry mid-session | Low | Medium | Preflight check + clear error mapping; surface re-login instruction |
| Destructive actions by the peer agent (it can edit files / run commands) | Medium | High | Safe defaults: no `--dangerously-skip-permissions`, sandbox where available; destructive posture is explicit opt-in only |
| Cost surprise (peer agents burn their own tokens/quota) | Medium | Medium | Document that delegation spends the external provider's quota; keep wrappers Haiku; surface log path for auditing |

## Open Questions

- [ ] Default mode: propose **Mode A** as default (robustness), Mode B opt-in — confirm with maintainer.
- [ ] Plugin name: `sdlc-agent-delegation` vs. contributing these profiles into the existing `command-delegation` bundle (which is external/superpowers, not in this repo) — recommend a new in-repo plugin.
- [ ] Mode B transport for codex: `mcp-server` (MCP/JSON-RPC framing) vs `app-server`/`exec-server` — architecture spike to pick.
- [ ] Do we expose model/effort pass-through in v1, or lock to CLI defaults first? (Lean: pass-through, since it's cheap and high-value.)

## Security & Privacy

- **Delegation publishes context to a third-party service.** Prompts sent to `codex`/`agy` leave for OpenAI/Google infrastructure. The wrapper must not send secrets or PII; document this clearly and keep the caller in control of what is delegated.
- **Peer agents can act on the filesystem.** Safe defaults: no permission-bypass flags, sandbox where the CLI supports it, and destructive/auto-approve posture only as an explicit, logged opt-in.
- **Auth** is handled by each external CLI's own login; the wrapper never handles credentials, only detects the unauthenticated state and fails fast.
- **Auditability:** every delegation writes its full transcript to a `./tmp/` log referenced in the compact return.

---

**Retrospective**: `retrospectives/232-external-agent-delegation.md` (link after implementation)
