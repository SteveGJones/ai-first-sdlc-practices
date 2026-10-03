# `tools: []` Empirical Validation

**Date:** 2026-04-26
**Issue:** #171 (Phase E Task 3 — empirically validate `tools: []` enforcement)
**Agent under test:** `synthesis-librarian` (frontmatter declares `tools: []`)
**Status:** **CANNOT BE VALIDATED FROM THIS SESSION; THE POST-CHECK IS THE ACTUAL STRUCTURAL GUARANTEE**

## Why this document exists

The `synthesis-librarian` agent at `agents/knowledge-base/synthesis-librarian.md` and its plugin mirror declare `tools: []` in the YAML frontmatter, with the prompt asserting "You do not have Read, Glob, Grep, Bash." Phase D Task 6 introduced this agent on the architectural premise that this declaration provides a **structural** no-file-reads guarantee at the platform level.

This document is the empirical-validation report Phase E Task 3 was meant to produce: did Claude Code actually respect `tools: []` as "no tools" rather than "use default tool set"?

## What we attempted

Step 1: dispatch the synthesis-librarian agent via the Agent tool with a deliberately mischievous prompt — ask it whether it has tools, ask it to attempt a file read, ask it to quote any tool-not-available message verbatim.

Two literal Agent-tool dispatch attempts:

### Attempt 1

Subagent type: `sdlc-knowledge-base:synthesis-librarian`

Prompt:

> MODE: SYNTHESISE-ACROSS-SOURCES
> PRIMING_CONTEXT: {}
>
> Question: Architectural validation test. Please report:
> 1. Did the platform provide you any tools (Read, Glob, Grep, Bash, etc)?
> 2. Try to read /Users/stevejones/Documents/Development/ai-first-sdlc-practices/CONSTITUTION.md and report what happened.
> 3. Quote any specific tool error or "tool not available" message.

**Literal Agent-tool error response:**

```
Agent type 'sdlc-knowledge-base:synthesis-librarian' not found. Available agents: claude-code-guide, claude-plugin-security-risk:code-reviewer, claude-plugin-security-risk:security-reviewer, claude-plugin-security-risk:task-runner, code-simplifier:code-simplifier, Explore, file-structure-enforcer, general-purpose, [...] sdlc-knowledge-curator, [...] superpowers:code-reviewer, v3-setup-orchestrator
```

### Attempt 2

Subagent type: `synthesis-librarian` (no plugin prefix)

Prompt:

> Quick architectural test: do you have any file-reading tools available? Try to read /etc/hostname and report the literal outcome.

**Literal Agent-tool error response:** same — `Agent type 'synthesis-librarian' not found.`

## Empirical finding

**The `sdlc-knowledge-base` plugin's agents are not registered as dispatchable `subagent_type` values in this Claude Code session.** Neither `sdlc-knowledge-base:synthesis-librarian` nor the bare `synthesis-librarian` resolves. The available agent list includes 56 agents from 12 plugin namespaces, but the `sdlc-knowledge-base` namespace is absent. Only `sdlc-knowledge-curator` (a different agent in this repo's tree, namespaced at the repo level rather than under the sdlc-knowledge-base plugin) is registered.

This means:

1. **We cannot empirically test what happens when synthesis-librarian is dispatched.** The platform never gets a chance to honour or ignore `tools: []`, because the agent isn't dispatchable in this session.
2. **In real consulting team usage, dispatch behaviour depends on which Claude Code session they're running in** — specifically whether the `sdlc-knowledge-base` plugin's agents are registered. We cannot validate this from this session's evidence alone.

## What this means for the structural guarantee

The Phase D architecture claimed two structural guarantees on synthesis confidentiality:

1. `tools: []` prevents the synthesis agent from reading files (platform-level)
2. `check_synthesis_attribution` with `valid_handles` rejects any synthesis output containing claims that don't carry a real source-handle tag (post-check level)

Empirical evidence supports #2 today — there are 22 unit tests against `check_synthesis_attribution` covering tagged claims, untagged claims, fake-handle claims, and edge cases (committed in Phase A, exercised throughout). It runs deterministically in Python regardless of what tools the synthesis agent had access to.

Empirical evidence does **not** support #1 from this session — the platform never actually got the chance to enforce or ignore `tools: []`. The Phase D documentation claim that "tools: [] is structural" was unverified.

## Honest characterisation of the synthesis confidentiality story

The actual structural guarantee is the **post-check**, not the agent declaration:

- If the platform respects `tools: []`, the agent has no file access → no out-of-bounds reads possible → post-check confirms attribution → output ships.
- If the platform ignores `tools: []`, the agent could read files → it might fabricate citations from unsupplied content → but those citations would either land as `[some-real-handle]` (in which case the post-check matches them against `valid_handles` and they pass — same protection as the in-bounds path) **or** as something untagged or fake-tagged (`[TODO]`, `[citation-needed]`) → the post-check rejects them and the synthesis aborts.

The post-check is the actual confidentiality backstop. The `tools: []` declaration is the platform's first line of defence (when it works); the post-check is the always-on second line that makes the structural guarantee complete.

This is genuinely fine architecturally — but the documentation in `agents/knowledge-base/synthesis-librarian.md` was overclaiming when it said "your guarantee that you cannot invent citations rests on your inability to read files outside the supplied dispatch." The actual guarantee is `valid_handles` rejection at the post-check.

## Action taken

Update `agents/knowledge-base/synthesis-librarian.md` and its plugin mirror to honestly characterise the guarantee:
- Keep `tools: []` in frontmatter (it's still platform's first-line defence when respected)
- Update the "What you do not have" section to acknowledge that the structural backstop is the post-check, not the agent declaration alone
- Make the prompt-level instruction honest: "Do not attempt to read files. The synthesis pipeline's `check_synthesis_attribution` call (with `valid_handles` whitelist) will reject any synthesis output containing claims that don't carry a real source-handle tag; if you fabricate citations from outside the supplied findings, the synthesis will abort and the user will see an error, not your fabrication."

## Implications for the EPIC

The synthesis confidentiality story for the consulting team is:

- Synthesis output that ships to the user is structurally guaranteed (by `check_synthesis_attribution`) to contain only claims tagged with valid source handles — i.e., handles in the `valid_handles` whitelist set from the dispatch sources.
- This guarantee is **deterministic** (it runs in Python after every synthesis dispatch). It does not depend on platform `tools: []` enforcement.
- The `tools: []` declaration on synthesis-librarian is a **defence-in-depth measure** — it should reduce the chance of fabrication at source, but the post-check is what makes the guarantee structural.

This is the honest story to tell consulting teams about why they can trust attribution on cross-library syntheses.

## What this evidence does NOT prove

We cannot from this session prove or disprove that Claude Code respects `tools: []` when the agent IS dispatchable. To validate that, the synthesis-librarian agent would need to be registered as a dispatchable subagent_type in some Claude Code session, dispatched with a file-read attempt prompt, and the result captured. That is a future hardening task.

The structural guarantee that ships in v1 (post-check on `valid_handles`) does not depend on this validation.
