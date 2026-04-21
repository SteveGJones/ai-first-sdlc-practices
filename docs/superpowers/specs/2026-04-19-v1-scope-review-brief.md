# sdlc-workflows v1 Scope Review — Team Brief

**Date:** 2026-04-19
**Branch:** `feature/96-plugin-scope-review` (off `feature/96-sdlc-workflows`)
**Triggered by:** user direction — *"the point of v1 is to be helpful, and
kicking this stuff down the road isn't helpful. I want a full team review
on what we should be doing, to properly leverage Archon and not
overcomplicate… focused on genuinely bringing help to people who use our
SDLC."*

## The question

**For every capability the `sdlc-workflows` plugin currently ships —
does it genuinely help an SDLC practitioner, and is it the minimum
viable shape given what Archon already provides natively?**

This is not a "can we ship?" review. We already know we *can*. This is a
"should we ship it this shape?" review, with permission to delete or
rework anything that doesn't meet the bar.

Reviewers are empowered to recommend **cuts, reworks, and deferrals**.
"Ship as-is and file a follow-up" is the weakest acceptable
recommendation and should be justified.

## Decision context

We are mid-Phase-F of EPIC #96. 108 commits on `feature/96-sdlc-workflows`.
PR body drafted at `.pr-body-phase-f.md` (not yet opened). The user has
paused PR opening because today's dogfooding surfaced evidence that we
may have overbuilt in places where Archon's native capabilities would
suffice, and underbuilt the honest disclosure of where Archon's
capabilities fall short for the integration shape we chose.

## What Archon actually provides (verified 2026-04-19)

Verified live against Archon v0.3.6 compiled release (`~/.archon-bin/archon`).

**CLI:**
- `archon workflow run <name>` — runs a workflow, DAG ordering, persists
  outcomes to `~/.archon/archon.db`. Discovers workflows from
  `.archon/workflows/*.yaml` relative to cwd via
  `discoverWorkflowsWithConfig(cwd, config)`.
- `archon workflow run --resume` — resumes the most recent failed run.
- `archon workflow status` — lists active runs.
- `archon isolation list` / `isolation cleanup` — manages per-run
  worktrees.
- `archon continue <branch>` — continues work on an existing worktree
  with prior context.
- `archon complete <branch>` — full branch lifecycle teardown.
- `archon workflow list`, `archon validate workflows` — discovery +
  validation.

**Serve (`archon serve`, port 3090 by default):**
- Bundled web UI (downloaded first run, cached at `~/.archon/web-dist/`).
- REST API: `/api/workflows/runs`, `/api/workflows/runs/<id>`,
  `/api/dashboard/runs`, `/api/conversations`, `/api/codebases`,
  `/api/workflows`, `/api/health`, `/api/commands`, `/api/update-check`.
- SSE stream: `/api/stream/__dashboard__` (heartbeats + events for
  **server-initiated** runs only).
- Writable endpoints: `POST /api/conversations` works; **`POST /api/workflows`
  returns 404** (no runtime workflow registration).

**Isolation model:**
- Per-run git worktrees, fully managed (`--branch`, `--no-worktree`,
  `--from`).
- Tracked via `archon isolation list`, cleaned via `archon isolation cleanup`.
- **No container isolation** — nodes execute in-process on the host.

**Storage:**
- `~/.archon/archon.db` SQLite state, canonical source of truth.
- Schema: `remote_agent_conversations`, `remote_agent_workflow_runs`,
  `remote_agent_workflow_events`.

**Credentials:**
- `archon setup` wizard writes `~/.archon/config.yaml`.

**Confirmed gaps / asymmetries** (discovered today):
- `archon serve`'s `/api/workflows` exposes only workflows bundled into
  the binary. Project-local workflows (the CLI path) aren't registered
  with the running serve instance. Result: the UI's DAG graph view,
  conversation thread view, and SSE stream all render-spinner-forever
  for CLI-launched runs.
- No HTTP endpoint accepts a workflow definition POST.
- `app_defaults_not_available` fires on every install because the
  binary's default-workflow path is hardcoded to the GitHub Actions
  runner path (build-time absolute path leak).

## What we currently ship

**Plugin surface** (`plugins/sdlc-workflows/`):

| Component | Purpose | Archon equivalent? |
|---|---|---|
| `workflows-setup` skill | Install archon, build base+full images, scaffold `.archon/` | `archon setup` (partial) |
| `deploy-team` skill | Build a team image from a manifest | none |
| `author-workflow` skill | Interactive workflow YAML generator | none |
| `workflows-run` skill | Resolve creds → preprocess → `archon workflow run` | thin wrapper |
| `workflows-status` skill | Query runs via REST or SQLite fallback | `archon workflow status` (partial) |
| `manage-teams` skill | Team lifecycle coaching | none |
| `teams-status` skill | Fleet visibility, coaching signals | none |
| `preprocess_workflow.py` | Rewrites `image:` nodes to `bash: docker run` | none (deliberate) |
| `resolve_credentials.py` | 3-tier fallback (Keychain → volume → config) | `archon setup` is 1-tier |
| `workflows_status_query.py` | REST+SQLite dual-source status | REST only via `archon serve` |
| `sse_stream_follow.py` | Follow `/api/stream/__dashboard__` | same endpoint, CLI follower |
| Three-tier Docker image model | base → dev-team/review-team → full | none |
| Team manifest schema (v1.0) | Per-team plugin/agent/skill/context lists | none |
| `loop.stages:` primitive | Declarative designer→dev→review cycles | none |
| Bundled workflow YAMLs | feature-pipeline, parallel-review, etc. | Archon has 13 bundled of its own |
| Specialist agent | Coaching / brainstorming | none |

**Tests:** 276 pytest / 20 container integration / 5 loop-stages /
18 fresh-user-flow / 8 sequential e2e / parallel e2e all green. We have
good coverage of whatever we keep; re-verification cost for cuts is
low.

## Review deliverables expected

Each reviewer should produce a file under `reviews/2026-04-19-v1-scope-*.md`
matching your speciality, with these sections:

### 1. Scope inventory
List every component in your area of review. Categorise each as:
- **KEEP AS-IS** (genuinely helpful, minimum viable shape)
- **REWORK** (helpful but over/under-shaped — specify the new shape)
- **CUT** (not needed, users lose nothing meaningful — justify)
- **DEFER** (ship without it, file follow-up issue — justify that
  the gap doesn't make v1 actively harmful)

### 2. Per-component rationale
For every KEEP / REWORK / CUT / DEFER, answer:
1. What real SDLC-practitioner problem does this solve?
2. Does Archon already solve it? Evidence.
3. If kept, what is the simplest shape that still solves the problem?
4. If cut/reworked, what is the user-visible change?

### 3. Honest disclosure check
Look at the PR body at `.pr-body-phase-f.md`. Flag any claims that are:
- Over-claimed (says we did X; we did less).
- Under-disclosed (we did Y but didn't mention it; users need to know).
- Misleading about Archon's coverage.

### 4. Cut/rework priority
Rank your recommended cuts and reworks by user-visible impact per
line-of-code removed (or simplified). Highest-priority cut at the top.

## Ground rules for the review

1. **User-first framing.** An SDLC practitioner who installs this
   plugin on day 1 — what do they get? What would frustrate them?
   What's over their head but shouldn't be? Don't optimize for what's
   technically interesting; optimize for what helps.
2. **No "ship and follow up" without explicit justification.** The
   user specifically rejected this default. If you recommend deferral,
   you must explain why *not* fixing it now would still be helpful to
   v1 users.
3. **Prefer cuts over reworks over keeping.** If a capability is
   marginal, cut it. v1 that does fewer things well is more helpful
   than v1 that does many things shakily.
4. **Treat "we'd fix it upstream" as a valid answer.** If the right fix
   is an Archon PR not an sdlc-workflows feature, recommend filing
   that and cutting our local workaround.
5. **Evidence, not speculation.** Cite line numbers, file paths,
   probe results. The Archon capability inventory above is evidence;
   extend it as you find more.

## Timeline

This review is synchronous. All reviewers should produce their file
in one pass. Once reviews are in, we will synthesise a single cut/rework
plan, execute it, re-verify all suites, and then open the PR.

## Files to read for context

- `CLAUDE.md` — project conventions
- `.pr-body-phase-f.md` — current PR narrative (candidate for pruning)
- `docs/superpowers/specs/2026-04-17-phase5-production-hardening-design.md` — security hardening rationale
- `docs/superpowers/specs/2026-04-19-phase-f-pr-open-requirements.md` — current ship requirements
- `CLAUDE-CONTEXT-workflows.md` — user-facing reference doc
- `plugins/sdlc-workflows/` — plugin source
- `tests/integration/workforce-smoke/run-e2e.sh` — canonical integration harness
- `reviews/2026-04-19-phase-f-*.md` — prior phase-F specialist reviews (not to be confused with these)
