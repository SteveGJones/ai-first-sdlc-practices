# Phase F — Open PR for EPIC #96 (Containerised Workers)

**Status**: Requirements — to be executed in a fresh context with shipped skills/agents
**Date**: 2026-04-19
**Branch**: `feature/96-sdlc-workflows`
**Author**: Claude (after user feedback on 2026-04-19: "Feels like we should do this with a clear context, update memory, CLAUDE.md and create the requirements spec")

---

## Context

EPIC #96 is feature-complete as of commit `f4fc0b4`. Five phases of
infrastructure work plus four Tier-1 tasks (loop.stages, SSE follower,
workflows-status REST+SQLite, loop-stages soak) have landed on the
feature branch with 261 passing unit tests. Ready for PR *except* for
three classes of residual work that must be addressed before opening
it.

A fresh session should execute this phase with the shipped skills and
specialist agents actively in the loop — see
`feedback_use_shipped_skills_and_agents.md`. The prior session
shipped Tier-1 without invoking `brainstorming`,
`test-driven-development`, `code-reviewer`, or
`dispatching-parallel-agents`, and without ever running the
`/sdlc-workflows:*` skills it had just written. Phase F is the
correction.

## Goal

Open a PR from `feature/96-sdlc-workflows` → `main` that an
unambiguous reviewer can merge with confidence, including:

1. An honest "what we got wrong" paragraph in the PR body.
2. All residual uncommitted changes reviewed, grouped, and committed
   or explicitly deferred.
3. Proof that the shipped `/sdlc-workflows:*` skills work as real
   users will invoke them.
4. Specialist-agent review sign-off on the commits that most
   benefit from it (security, architecture, observability).

## Non-goals

- CI/CD automation of image builds — tracked as a separate follow-up
  issue per `feedback_epic_branch_model.md`.
- Prometheus/Grafana exporter — tracked in CLAUDE-CONTEXT-workflows.md
  §"Recommended follow-up issue".
- `workflows-run --server` mode — ditto.
- Any feature scope expansion. Phase F is packaging + verification
  only.

## Residual work inventory (uncommitted on branch)

From `git status --short` at session close:

**Accumulated from Phase B/D pivot (bash-preprocessor replaces ContainerProvider patch):**
- `plugins/sdlc-workflows/patches/apply-patches.sh` (deleted)
- `plugins/sdlc-workflows/patches/container-provider.ts` (deleted)
- `plugins/sdlc-workflows/docker/Dockerfile.base` (remove patch apply, bump Bun to 1.2.17)
- `plugins/sdlc-workflows/workflows/sdlc-*.yaml` (update header comments: no patch required)
- `plugins/sdlc-workflows/README.md` (update delivery surface)
- `plugins/sdlc-workflows/docs/quickstart.md` (update install flow)

**Accumulated from Phase E (fresh-user-flow validator + e2e refinements):**
- `tests/integration/workforce-smoke/run-fresh-user-flow.sh` (new)
- `tests/integration/workforce-smoke/run-e2e.sh` (flag overhaul)
- `tests/integration/workforce-smoke/run-full-formation.sh` (updates)
- `tests/integration/workforce-smoke/miniproject/.archon/commands/*.md` (3 files)

**Workflows-setup polish:**
- `skills/workflows-setup/SKILL.md` and plugin copy
- (large diff — treat as its own commit group)

**Top-level state:**
- `CLAUDE.md` (pending update — this spec refreshes it)

### Action per group

Each group becomes its own focused commit (see
`feedback_pr_granularity.md`). Before committing, dispatch the
appropriate specialist agent:

- Phase B pivot → `sdlc-team-common:solution-architect` to confirm
  the removal of the ContainerProvider patch is documented correctly
  and no dangling references remain.
- Phase E test refinements → `superpowers:code-reviewer` on the diff.
- workflows-setup polish → `superpowers:code-reviewer` and run the
  skill manually to verify the changes are user-facing-correct.

## Work breakdown

### F.1 — Brainstorm the PR narrative (BEFORE writing the body)

Invoke `superpowers:brainstorming` with these seed questions:

- Who is the reviewer? What do they need to see first?
- What is the single riskiest thing in this PR? How do we draw
  attention to it rather than bury it?
- What did we get wrong during the EPIC that a reviewer *should*
  know about (pivots, rework, abandoned paths)?
- What are the explicit deferrals (CI/CD, Prometheus, monitoring
  server mode) and why are they deferred rather than blocking?
- What commands should the reviewer run to verify the PR locally?

Output: a one-page PR narrative outline.

### F.2 — Review and commit residual tree changes

For each residual group above:
1. Dispatch the nominated specialist agent to review the diff.
2. Address any flagged issues.
3. Commit with a focused message that names the group.

Candidate commit sequence:

- `refactor(workflows): retire ContainerProvider patch — preprocessor pivot complete`
- `test(workforce-smoke): fresh-user-flow validator + e2e flag overhaul`
- `docs/skill(workflows-setup): [scope-tbd]` — read the diff first to
  name this accurately.

### F.3 — Dogfood the shipped skills

Before the PR body is written, execute these against the miniproject
fixture and record outputs:

1. `/sdlc-workflows:workflows-status --recent 5` — prove the new
   REST+SQLite query works for a real user.
2. `/sdlc-workflows:workflows-status --run-id <any>` — prove detail
   mode works.
3. `/sdlc-workflows:workflows-run` against an existing workflow —
   prove end-to-end.
4. `python3 plugins/sdlc-workflows/scripts/sse_stream_follow.py` —
   prove it fails cleanly when `archon serve` is not running and
   streams correctly when it is.

If any of these misbehave, fix *before* opening the PR.

### F.4 — Parallel specialist review

Dispatch in parallel (`superpowers:dispatching-parallel-agents`):

- `sdlc-team-security:security-architect` — review cap-drop, signal
  handling, credential resolver, container hardening across the full
  branch diff.
- `sdlc-team-common:solution-architect` — review the three-tier
  Docker model, preprocessor design, loop.stages primitive, and
  REST+SQLite fallback pattern.
- `sdlc-team-common:observability-specialist` — review the SSE
  follower, monitoring gaps section, Prometheus follow-up
  recommendation.
- `sdlc-core:critical-goal-reviewer` — compare the delivered
  feature against the EPIC #96 original goals and flag scope drift
  or gaps.

Findings land in `reviews/2026-04-19-phase-f-*.md` alongside existing
Phase 2 reviews.

### F.5 — Write the PR body

Using the brainstorm output (F.1) + specialist review findings (F.4):

**Required sections:**

1. **Summary** — 3-5 bullets, reviewer-first. What this PR *does*,
   not how.
2. **Honest "what we got wrong"** — the pivots and rework that
   shaped the final design:
   - Archon ContainerProvider patch approach abandoned in favour of
     bash-node preprocessing (Phase B pivot).
   - `--read-only` filesystem dropped mid-Phase 5 — incompatible
     with Claude Code's writable `~/.claude/`.
   - Task #14 scope was wrong — SSE only applies to `archon serve`,
     not `archon workflow run`. Corrected mid-session.
   - Outer-loop-wrapper proposal for cycles replaced by
     `loop.stages:` after user asked "wasn't one of the bugs we
     raised that Archon couldn't detect a loop terminating?"
3. **Explicit deferrals** — with issue links if already filed or a
   note that they will be filed on merge:
   - CI/CD image build automation
   - Prometheus/Grafana exporter
   - `workflows-run --server` mode
   - Real-mode soak test wired into CI
4. **Test matrix** — 261 unit tests + integration smoke families
   (Phase 2/3/container/acceptance/E2E/fresh-user/loop-stages-soak),
   with pass counts.
5. **Test plan for reviewer** — checklist of commands to run
   locally, including the dogfood sequence from F.3.

### F.6 — Open the PR

- Base: `main`
- Head: `feature/96-sdlc-workflows`
- Use the `sdlc-core:pr` skill (the only skill with
  `disable-model-invocation: true` — explicit-only, because it
  creates remote-visible artefacts).

### F.7 — File follow-up issues

Immediately after the PR is open, file (or link existing) issues for:

- CI/CD image build automation
- Prometheus/Grafana exporter (design already in
  CLAUDE-CONTEXT-workflows.md)
- `workflows-run --server` mode
- Real-mode soak test integration

Cross-reference them from the PR body.

## Acceptance criteria

Phase F is done when:

- [ ] All residual tree changes are either committed or explicitly
      removed.
- [ ] `python3 tools/validation/check-plugin-packaging.py` passes.
- [ ] `python3 -m pytest tests/` passes (261+ tests).
- [ ] All four dogfood invocations in F.3 produced correct output.
- [ ] Specialist review outputs exist in `reviews/2026-04-19-*.md`
      and any blocker findings have been addressed.
- [ ] PR body contains the "what we got wrong" paragraph and
      explicit deferrals section.
- [ ] PR is open against `main` and CI is green (or failures are
      clearly understood and narrated in a PR comment).
- [ ] Follow-up issues are filed and linked from the PR.

## Risk register

- **Residual tree changes conflict** when grouped into focused
  commits — pre-check with `git diff` before staging each group.
  *Mitigation:* `git stash` + targeted `git add` per group.
- **Specialist reviews surface a blocker** late in the phase.
  *Mitigation:* F.4 runs in parallel *before* F.5 (PR body), so
  findings inform the narrative rather than contradict it.
- **Dogfood invocations fail** revealing a real bug in a shipped
  skill. *Mitigation:* treat this as a blocker — fix before the PR.
  A broken shipped skill in the PR is a worse outcome than a
  delayed PR.

## Process rules for executing this phase

Lifted from `feedback_use_shipped_skills_and_agents.md`:

1. Invoke `superpowers:brainstorming` at F.1. Do not skip.
2. TDD anything new written during F.2 (unlikely, but possible).
3. `superpowers:code-reviewer` on every commit created in F.2.
4. `superpowers:dispatching-parallel-agents` for F.4 — four
   reviews, one message.
5. Use the `sdlc-core:pr` skill to open the PR in F.6. Do not
   hand-roll `gh pr create`.

If I find myself reaching for a raw `Bash` tool call where a shipped
skill would do the job, stop and use the skill.
