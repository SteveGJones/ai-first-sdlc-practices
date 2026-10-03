---
title: "Task Delegation & Merging — Decomposition, Context Passing & Git Strategies for Parallel AI Workers"
domain: task-decomposition, context-engineering, merging, git-strategies, failure-handling, parallel-execution
status: active
tags: [decomposition, file-partitioning, context-passing, merge-strategy, worktrees, failure-handling, circuit-breaker, checkpoint, spec-driven, epic-96]
source: agent_prompts/campaign-96-containerized-workers/research/R4-output.md
cross_references:
  - library/claude-code-native-parallelism.md
  - library/containerised-worker-economics.md
  - library/containerised-worker-recommendations.md
  - library/multi-agent-framework-landscape.md
  - agent_prompts/campaign-96-containerized-workers/00-campaign-plan.md
---

## Key Question

How should a supervisor decompose coding tasks for parallel AI workers, pass context, aggregate results via git, and handle failures?

## Core Findings

1. **Accuracy degrades steeply with task size.** Single function (~100 lines): ~87% accuracy. Single file (~500 lines): ~60-75%. Multiple files (2-5 files, ~2000 lines): ~19%. Module (~10 files, ~10k lines): ~5-10%. Target 500-1500 lines per agent, ~2 hour max duration. Anything larger triggers sub-task decomposition. -- R4 sec 1.3
2. **Five decomposition strategies exist with different success rates.** Feature-based (75-80%, each agent owns one feature end-to-end). Component/module-based (70-75%, codebase partitioned into non-overlapping modules). Step/task-based hierarchical (65-70%, sequential steps with independent parallel steps). Layer-based unidirectional (70% with strict interface contracts, 30% without). File-level partitioning (90%+, non-overlapping file sets, zero merge conflicts if properly partitioned). -- R4 sec 1.1
3. **Spec-driven decomposition by the supervisor prevents ~90% of agent collisions.** Manual decomposition outperforms AI self-decomposition in production systems. AI self-decomposition works as a fallback (re-decompose on failure via ADaPT pattern), not upfront. Hybrid approach: human writes spec, AI suggests task list, human approves. Decomposition should happen in the supervisor prompt, not delegated to workers. -- R4 sec 1.4
4. **Minimal viable context outperforms full-repo context injection.** Spec-only with tool access achieves ~81% accuracy at 200-500 tokens/agent. Manifest + minimal context achieves ~78% at 500-2k tokens. Full repo clone achieves only ~65% accuracy at 10k-50k tokens. "Context engineering is about finding minimal context, not adding more." Agents should fetch on-demand via Glob/Grep/Read. -- R4 sec 2.1-2.2
5. **Sub-agent context isolation reduces token costs by 60%.** Single agent over 10 steps: ~80k tokens (quadratic blowup). Architect + 2 specialists + merge agent: ~32k tokens. Break-even at step 5-6. Pattern: architect agent reads full spec (no code), implementation agents read assigned files only, verification agent reads changes only. -- R4 sec 2.3
6. **Sequential git merge achieves 85% success; file-level partitioning achieves 95%.** Sequential merge: merge Worker A to main, rebase Worker B on new main, merge Worker B, repeat. Prevents "merge skew" where B is based on stale main. File-level partitioning: each agent owns non-overlapping files, supervisor combines via git add + commit, zero merge conflicts if boundaries correct. AI-assisted merge: 60-75% success, unproven at scale. -- R4 sec 3.1
7. **Shared files (package.json, routes, config) cannot be safely parallelised.** Solutions ranked: (1) file locking (agent acquires exclusive write lock, blocks others), (2) separate files + merge (each agent writes own deps file, supervisor combines), (3) central manager (agents request changes via HTTP, supervisor updates single file). Best practice: avoid shared files; if unavoidable, use file locking. -- R4 sec 6.5
8. **Failure handling requires circuit breakers, not just retries.** Retry decision tree: transient error (exponential backoff 3x), context overflow (re-decompose + reduce context), bad code generation (retry with error feedback + stronger model), stuck/infinite loop (kill + checkpoint + escalate), hallucination (retry with few-shot examples), unknown (escalate, do NOT retry blindly). Circuit breaker opens after 3 consecutive failures with 5-minute cool-off. -- R4 sec 4.1-4.3
9. **Checkpoint recovery enables partial success.** Agent checkpoints state after each subtask (saves to disk: "completed [task1, task2, ...]"). On retry, worker resumes from last checkpoint. Each checkpoint must pass automated tests; otherwise invalid and worker restarts from beginning. LangGraph provides native checkpointing via `stream()` with configurable `thread_id`. -- R4 sec 4.4
10. **Supervisor-only communication is the dominant 2026 pattern.** All communication flows through supervisor; workers never talk directly. Simple orchestration, full visibility, easy logging/rollback/verification. Scales to ~1000 agents before supervisor becomes bottleneck. Peer-to-peer (A2A protocol) is experimental, not yet in production AI coding. -- R4 sec 5.1-5.2

## Frameworks Reviewed

| Framework | Evidence Base | Limitations |
|---|---|---|
| Git Worktree Isolation | Claude Code docs, community guides | File-level only; no env/DB isolation; shared .git/objects |
| Sequential Git Merge | Production systems (GitHub Agent HQ), R4 analysis | 85% success; fails on shared config files and interdependent refactors |
| File-Level Partitioning | R4 field analysis, multiple production case studies | Requires upfront human effort; some files (package.json) cannot be partitioned |
| AI-Assisted Merge (CHATMERGE, CodeGPT) | R4 sec 3.1, emerging tools | 60-75% success; unproven at scale; not automated end-to-end |
| LangGraph Checkpointing | Official docs, production patterns | Requires LangGraph adoption; adds framework dependency |
| ADaPT (As-Needed Decomposition) | Research papers, R4 sec 1.4 | Works on-failure; upfront self-decomposition unproven at scale |

## Actionable Thresholds

| Metric | Threshold | Source | Signal |
|---|---|---|---|
| Lines per agent | 500-1500 | R4 sec 1.3 | Below 500: over-decomposed (coordination overhead). Above 1500: accuracy collapses |
| Max duration per agent | ~2 hours | R4 sec 1.3 | Beyond this, context bloat and diminishing returns |
| Multi-file task accuracy | ~19% | R4 sec 1.3 | Tasks spanning 2-5 files need decomposition into single-file scope |
| File-level partition success | 95%+ | R4 sec 3.1 | Best available merge outcome; requires correct upfront partitioning |
| Sequential merge success | 85% | R4 sec 3.1 | Default when file-level partitioning is not feasible |
| Spec-driven collision prevention | ~90% | R4 sec 1.4 | Supervisor-authored specs with explicit file boundaries |
| Circuit breaker trigger | 3 consecutive failures | R4 sec 4.3 | Opens circuit; 5-minute cool-off before half-open test |

## Design Principles

1. **Decompose by file boundaries, not by concept.** File-level partitioning (95% success) beats feature-based (75-80%) and module-based (70-75%) because it eliminates merge conflicts structurally rather than hoping agents will stay in lanes.
2. **Minimal viable context, maximum tool access.** Give agents a 300-500 word task spec, a file manifest, key interfaces, and verification criteria. Let them fetch code on demand via Glob/Grep/Read. Do not inject the full repo.
3. **Supervisors decompose, workers execute.** The supervisor writes the spec with explicit file boundaries, dependency declarations, and success criteria. Workers are pure executors. AI self-decomposition is a fallback on failure, not the primary strategy.
4. **Merge sequentially, not simultaneously.** Sequential git merge (A to main, rebase B, B to main) avoids merge skew. Parallel three-way merges require sophisticated conflict resolution with only 60-75% success.
5. **Fail fast, checkpoint often, escalate early.** Circuit breakers (3 failures, 5-min cool-off), per-subtask checkpoints, and explicit escalation to human when blast radius is too high. Retries alone are insufficient for AI agents because they can fail silently (hallucinated answers that look correct).

## Key References

1. OpenHands: Automating Massive Refactors (Nov 2025) -- 10-15 agents on non-overlapping components, 80-90% automation
2. Vercel v0: Coding Agent at Scale -- 59% reduction in time-to-ticket-closing; sequential per-feature, human review before merge
3. GitHub Agent HQ (2026) -- Sequential merge with one-click AI resolution for conflicts
4. ADaPT: As-Needed Decomposition and Planning (research, 2025) -- On-failure decomposition outperforms upfront self-decomposition
5. Anthropic C Compiler Project -- 16 parallel agents, file-partitioned, 99% test pass rate
6. Claude Code Worktree Guide -- https://claudefa.st/blog/guide/development/worktree-guide (CRAAP 23)
7. Database Isolation via WorktreeCreate hooks -- https://www.damiangalarza.com/posts/2026-03-10-extending-claude-code-worktrees-for-true-database-isolation/ (CRAAP 22)

## Programme Relevance

**EPIC #96 (Containerised Claude Code Workers):**
- The 19% accuracy on multi-file tasks (finding 1) is the single strongest argument for containerised workers: each worker must receive a narrowly scoped, single-file or tight-feature task to be effective.
- File-level partitioning (finding 6, 95% success) should be the default merge strategy. Sequential git merge (85%) is the fallback. AI-assisted merge is experimental and should not be relied upon.
- Spec-driven decomposition (finding 3) means the supervisor prompt is the most important piece of the containerised worker system. Investing in supervisor prompt engineering pays more than investing in container infrastructure.
- The minimal viable context principle (finding 4) directly reduces token costs -- each containerised worker receives a spec and uses tools to fetch code, rather than receiving a full repo clone. This compounds with the prompt caching optimisation from the economics analysis.
- Circuit breakers and checkpointing (findings 8-9) are required infrastructure for any containerised worker system. Without them, stuck agents consume API quota silently.
