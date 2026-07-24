# Retrospective: External Agent Delegation (codex + agy)

**Branch:** `feature/external-agent-delegation`
**Date:** 2026-07-23 (started)
**Duration:** In progress
**Tracking Issue:** #232

---

## Summary

_In progress._ Building a new SDLC-family plugin (`sdlc-agent-delegation`) with two Haiku wrapper agents — `codex-delegate` and `agy-delegate` — that let a Claude Code session delegate prompts to external agentic CLIs (OpenAI Codex, Antigravity), keep sessions open across multiple prompts, and fan out across concurrent subagents. Two continuity modes are required: id-based resume (default) and a persistent live process (opt-in).

## What Went Well

- _TBD_

## What Could Improve

- _TBD_

## Lessons Learned

- **Design before code, tiered delegation.** Fable for the hard architecture (Mode B lifecycle / IPC framing) and review, Sonnet for execution, Haiku for the shipped wrapper agents — matching model cost to task difficulty.

## Decisions Log

- **2026-07-23** — Branch `feature/external-agent-delegation` created; issue #232 updated to require BOTH continuity modes as first-class, single-contract modes.
- **2026-07-23** — Confirmed both CLIs support the needed session model locally (codex 0.145.0 `exec resume`; agy 1.1.5 `--conversation`/`-i`).
- **2026-07-23** — Fable architecture spike + adversarial review (verdict: proceed-with-changes); §9 of the design spec is authoritative. BLOCKER fixed at design time: `setsid`/`timeout`/`gtimeout` absent on macOS → portable perl `POSIX::setsid` daemonizer; submit-then-poll to respect the Bash-tool 120s/600s cap.
- **2026-07-23** — Stage 1+2 (extdel.sh + codex resume, Sonnet-built) landed in working tree: 33/33 mock tests green, injection-safe (prompt via stdin), posture pinned, read-only default. Pending Fable code review before commit.
- **2026-07-23** — **User authorized** running the one-off agy live probe at the Stage 3 boundary (`agy --print --mode plan` → execute vs hang; spends a small amount of agy/Google quota). No need to re-ask when Stage 3 starts.
- **2026-07-23** — Fable code review of Stage 1+2 found 1 BLOCKER (B1: `stop` orphaned codex via process-group mismatch → double-drive) + 9 MAJOR + minors. Sonnet applied all fixes; regression tests added for the gaps. **Stage 1+2 committed**: 64/64 mock tests green, syntax-clean, zero debt. B1 fix verified independently (supervisor TERM/INT handlers forward to `-$child`, signal-aware exit codes, ownership-checked lock release claimed synchronously post-fork).
- **2026-07-23** — **User authorized** delegating real code reviews of our own implementation to BOTH external platforms (codex + agy) as the end-to-end dogfood test (spends OpenAI + agy quota).
- **2026-07-23** — agy live probes (authorized): plan+sandbox executes non-interactively (no hang); `--print` takes the prompt as its flag value (ordering load-bearing); `last_conversations.json[cwd]` is the sole reliable id source (metadata absent for `--print` convos). Findings → spec §9.14.
- **2026-07-23** — **Stage 3 (agy resume) committed**: agy wired into extdel.sh (two-layer %q-quoted argv, `--print` last, cwd-keyed id capture w/ retry, plan/sandbox posture map), agy-runner Haiku agent, policy skill extended, mock-agy tests (HOME-redirected). Suites: codex 64/64, agy 86/86 (150 total), zero debt, injection-safe (verified independently).

## Changes Made

### Files Added
- `docs/feature-proposals/232-external-agent-delegation.md` — feature proposal
- `retrospectives/232-external-agent-delegation.md` — this file

_(More to follow as implementation proceeds.)_
