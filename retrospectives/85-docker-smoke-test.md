# Retrospective: Feature #85 — Docker Setup Smoke Test

**Branch**: `feature/docker-smoke-test` (merged via PR #87)
**Date**: 2026-04-06

## Context

Before this feature, we had no fast, reproducible way to verify that the public plugin install path actually worked end-to-end. The full integration test (`tests/integration/PROMPT.md`) takes 45-60 minutes and builds an entire web app — too slow to run on every plugin/agent/skill change. We needed a 5-minute smoke test that exercises plugin install, setup-team, tech detection, 1st-party discovery, and tool installation against a realistic fixture, using the developer's Claude Code Max subscription instead of paid API tokens.

## What Went Well

- **All 9 success criteria from the spec met on the first complete run.** Once the auth and permissions issues were untangled, a single Ralph iteration completed in 348 seconds with 10/10 output checks passing and 14 plugins discovered and installed against the EventFlow fixture (MongoDB, Redis, Kafka, React, FastAPI, AWS, Terraform, Grafana, Python, Celery, TypeScript, Prometheus, Tailwind, GitHub Actions).
- **The two-layer Docker architecture (base image + disposable runtime container) worked exactly as designed.** Building `sdlc-smoke-base:latest` once and re-running `run.sh` against it gives a fast iteration loop without rebuilding tooling on every test.
- **EventFlow fixture exercised the discovery pipeline broadly.** The fictional e-commerce analytics platform is intentionally polyglot — it surfaced gaps and successes across MCP servers, GitHub Actions, and Python packages all in one run.
- **Documenting blockers as we hit them paid off.** The "Lessons Learned (the hard way)" section in `tests/integration/setup-smoke/README.md` captures seven specific gotchas with code-level fixes. Anyone setting up a similar Docker + Claude Code + Ralph environment in the future can skip the painful parts.
- **Credentials stayed out of git.** `.claude/`, `.claude.json`, and `.credentials.json` are all gitignored; the smoke test runs inside a Docker named volume that never touches the working directory.

## What Could Improve

- **The path from spec to working test was much longer than the spec implied.** The design doc described mounting `~/.claude` and `~/.claude.json` from the host as a one-line fix. In practice this hit four cascading issues (root vs non-root user, named volume ownership inheritance, UID 1000 collision in `node:22-slim`, `.claude.json` living outside `.claude/`) that each took an iteration to diagnose. The spec should have flagged "Docker auth + OAuth + non-root user" as a known-hard area, not a routine setup step.
- **Ralph silently runs zero-second iterations on auth failures.** When Claude Code refused to start because of `--dangerously-skip-permissions` running as root, Ralph reported "Too many consecutive failures" in 3 seconds with no actionable error. The diagnostic logs at `.ralph/diagnostics/logs/` had the real cause but weren't surfaced. This wasted significant debugging time before we figured out to run the underlying `claude` command directly.
- **I jumped to abandoning the Ralph approach prematurely.** When the root-user issue surfaced, my first instinct was to replace Ralph with a bash loop. The user correctly pushed back ("are you sure you aren't jumping too quickly?") and pointed out the standard Docker pattern: build/install as root, switch to a non-root `USER` before running. The fix was straightforward once I followed that pattern. Lesson: when a tool seems "broken," exhaust the standard fixes before reaching for a replacement.
- **No CI integration yet.** The smoke test runs locally against the developer's Max subscription. Running it in CI requires solving the auth model (CI runners can't do interactive OAuth). The spec explicitly deferred this and the README documents the trade-offs, but it's still an open gap before this can become a true gate.
- **No retrospective at merge time.** PR #87 was merged without this file being created, which is a process violation under the AI-First SDLC framework's "feature proposal + retrospective" rule. This retrospective is being added after the fact.

## Lessons Learned

1. **OAuth credentials in Docker are a known-hard problem, not a routine bind mount.** Anyone integrating Claude Code (or any browser-based OAuth tool) into a Docker workflow should plan on a named volume + interactive login script + entrypoint restoration pattern from the start, not a host bind mount. The README captures the exact pattern.
2. **Pre-create directories owned by your runtime user before declaring a named volume mount point.** Docker named volumes inherit ownership from the directory they're mounted onto. If the directory doesn't exist in the image, the volume defaults to root ownership and silently breaks the non-root user. Creating `/home/sdlc/.claude` (owned by `sdlc`) in the Dockerfile before the `USER sdlc` switch was the fix.
3. **Always verify the "obvious" assumption about UIDs in base images.** `node:22-slim` already has a `node` user at UID 1000. We shifted to UID 1001 to avoid the collision. Always check `id` in the base image before adding a new user.
4. **When a long-running tool fails fast and quietly, run its underlying command manually.** Ralph wraps `claude --dangerously-skip-permissions ...` and swallows stderr. Running that exact command by hand surfaced the root permission error that Ralph was hiding. Document the underlying invocation in your test README so future debuggers don't have to dig it out.
5. **Users want tools fixed, not replaced.** Twice in this feature I floated abandoning a working tool (Ralph, then host bind mounts) when the right answer was to debug the standard pattern. Default to "fix it correctly" before "swap it out."
6. **The "shipped only" rule for skills/agents emerged from this work.** While testing the smoke harness, I discovered our local `.claude/agents/` was full of stale February versions of agents we were actively editing in `agents/`. That spawned PR #88 (the dev environment setup script) and PR #89 (CONTRIBUTING.md docs) — a useful side effect of dogfooding our own setup flow.

## Changes Made

| File | Change |
|------|--------|
| `tests/integration/setup-smoke/Dockerfile` | Base image: node:22-slim + Python + git + xz-utils + claude-code + ralph-cli + non-root sdlc user (UID 1001) with pre-created `/home/sdlc/.claude` |
| `tests/integration/setup-smoke/build.sh` | Builds `sdlc-smoke-base:latest` |
| `tests/integration/setup-smoke/login.sh` | Interactive Claude Code OAuth login into named volume `sdlc-smoke-claude-creds` |
| `tests/integration/setup-smoke/run.sh` | Runs the smoke test against the EventFlow fixture, mounts the credential volume |
| `tests/integration/setup-smoke/entrypoint.sh` | Container entrypoint — restores `.claude.json` from backup, unsets `ANTHROPIC_API_KEY`, runs Ralph |
| `tests/integration/setup-smoke/PROMPT.md` | 4-phase smoke test prompt (install plugins → setup-team → install recommended tools → verify outputs) |
| `tests/integration/setup-smoke/ralph.yml` | Ralph config — 10 iteration cap, `LOOP_COMPLETE` sigil |
| `tests/integration/setup-smoke/fixtures/eventflow/README.md` | EventFlow fictional project — broad polyglot tech stack |
| `tests/integration/setup-smoke/README.md` | Full how-to-run docs + 7 lessons-learned blockers + troubleshooting |
| `docs/feature-proposals/85-docker-smoke-test.md` | Feature proposal |
| `docs/superpowers/specs/2026-04-06-docker-smoke-test-design.md` | Design spec |
| `docs/superpowers/plans/2026-04-06-docker-smoke-test.md` | Implementation plan |
| `.gitignore` | Added `.claude.json` (was missing — `claude.json` pattern doesn't match dotfile), `.credentials.json`, `**/.credentials.json` |

## Metrics

- **Last successful run**: 1 Ralph iteration, 348 seconds, 10/10 PASS
- **Plugins discovered + installed in run**: 14 (MongoDB, Redis, Kafka, React, FastAPI, AWS, Terraform, Grafana, Python, Celery, TypeScript, Prometheus, Tailwind, GitHub Actions)
- **Spec success criteria met**: 9 of 9
- **Blockers documented in README "Lessons Learned"**: 7
- **Side-effect PRs spawned by dogfooding the setup**: 2 (#88 dev env script, #89 CONTRIBUTING.md docs)

## Open Follow-Up

Not part of #85, but worth tracking if we want to extend this:

- **CI integration** — needs an auth model that works without interactive OAuth (API key, refresh token + secret, or recorded session)
- **Additional fixtures** — currently only EventFlow; could add AI/ML, cloud-native, security-focused, etc.
- **Discovery result caching** — most of the 5-6 minute runtime is web searches; cached results would make repeated runs near-instant
- **Local plugin testing flag** — `./run.sh --local /path/to/repo` to test unpublished plugin changes (was explicitly out of scope for #85, see spec "Future" section)
