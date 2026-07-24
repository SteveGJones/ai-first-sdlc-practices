# Retrospective: External Agent Delegation (codex + agy)

**Branch:** `feature/external-agent-delegation`
**Date:** 2026-07-23 (started)
**Duration:** In progress
**Tracking Issue:** #232

---

## Summary

_In progress._ Building a new SDLC-family plugin (`sdlc-agent-delegation`) with two Haiku wrapper agents — `codex-delegate` and `agy-delegate` — that let a Claude Code session delegate prompts to external agentic CLIs (OpenAI Codex, Antigravity), keep sessions open across multiple prompts, and fan out across concurrent subagents. Two continuity modes are required: id-based resume (default) and a persistent live process (opt-in).

## What Went Well

- **Tiered delegation matched cost to difficulty.** Fable for the architecture spike + two adversarial reviews (design and code), Sonnet for execution, Haiku as the shipped wrapper. Each Fable review caught real defects a cheaper pass would have missed (the `setsid`/timeout-cap BLOCKERs at design time; the `stop`-orphans-codex BLOCKER at code time).
- **End-to-end dogfood (2026-07-23) worked and paid off immediately.** Drove the real `extdel.sh` against the REAL codex + agy CLIs to review our own `turn-supervisor.pl`. The full machinery worked: submit-then-poll (`RUNNING`→`SUCCESS`), real session-id capture for BOTH CLIs, `slice` extraction, durable `./tmp` logs, `stop`, `reap`. codex returned a high-quality 10-finding review; and the run surfaced two real bugs in our own code (below).

## Dogfood Findings (2026-07-23) — follow-up work

- **DF1 (agy read-only posture is too restrictive for real work).** `agy --mode plan --sandbox` (our `read-only` mapping) **auto-denies the "command"/tool permission in headless mode**, so any task that must read a file or run a command produces **no output**. The trivial "PONG" live probe missed this because it needed no tools; a real review task exposed it. agy's own stderr suggests a `permissions.allow` settings.json allow-rule (e.g. `command(<target>)`) or `--dangerously-skip-permissions`. **Action:** rethink the agy `read-only` mapping — likely need a middle posture that permits read-only file/command access, or document that agy read-only cannot touch files.
- **DF2 (false SUCCESS on empty output).** agy exited 0 with an empty answer (tool auto-denied), and our contract reported `Status: SUCCESS`. **Action:** treat exit-0-with-empty-answer — especially when stderr matches `no output produced|auto-denied|required the .* permission` — as a distinct non-SUCCESS status (e.g. `NO_OUTPUT`/`DENIED`), so callers aren't misled.
- **DF3 (codex-found bugs in `turn-supervisor.pl`).** The delegated codex review flagged several real races the Fable review and tests missed: (a) TERM/INT keep default disposition in the window between `fork` and handler install (line ~70→179) — a signal there kills the supervisor uncleanly; (b) the parent can signal `-$child` before the child's `setpgrp` establishes the group → signals miss and `waitpid` can hang; (c) the timeout alarm stays armed inside the TERM/INT handler and can misclassify a stop as timeout 124; (d) a second signal during cleanup `exit 0`s mid-escalation; (e) `owner.pid` handoff truncates in place and ignores I/O failure. **Action:** harden the supervisor (block TERM/INT/ALRM during setup + a fork/setpgrp handshake + cancel alarm on entering the handler + atomic owner.pid write).

## What Could Improve

- **A trivial live probe under-tested agy.** The "PONG" probe answered "does plan mode hang?" (no) but not "does plan mode allow the tools a real task needs?" (no) — DF1. Lesson: probe with a task shaped like the real workload (one that must read a file), not a no-op.

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
