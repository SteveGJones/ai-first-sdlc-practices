# SDLC Plugin Integration Test

> **This is a smoke test for plugin developers, not a user workflow.** The cache-clear and reinstall steps below are for testing that fresh plugin installs work correctly. Normal users install the plugins once and keep them — see `CLAUDE.md` in the repo root for the standard setup instructions.

Automated end-to-end test of the AI-First SDLC plugin framework. Drop `PROMPT.md` and `ralph.yml` into a blank GitHub repo, run `ralph run`, and walk away. When it finishes you get:

1. **A working demo app** — a Python web app displaying a visual timeline of its own construction, running at http://127.0.0.1:18080
2. **A framework quality report** — honest assessment of what worked, what didn't, and what should change

## Why This Exists

The build journal serves two audiences:
- **External users** browsing the demo app see how an AI built a real application phase by phase — what agents it consulted, what decisions it made, what went wrong
- **Framework maintainers** reading the journal get a prioritised Friction Log, Agent Value Assessment, and Constitution Compliance report that tells them exactly what to fix next

This is both the test and the demo. If the app works and the journal is honest, the framework works. If it doesn't, we have a bug to fix.

## What It Does

Ralph drives Claude through 10 phases with zero human intervention:
bootstrap, planning, architecture, implementation, testing, self-population,
validation, runtime proof, shipping (commit/push/PR/merge), and session handoff.

Every phase produces an 8-section journal entry documenting:
- What agents were invoked and what they **actually** contributed
- What worked and what didn't (honest, specific — not rubber stamps)
- Validation results (actual command output, not just pass/fail)
- Framework recommendations (what should change in the SDLC framework)

## Prerequisites

- GitHub CLI (`gh`) authenticated
- Python 3.12+
- Ralph orchestrator installed (`ralph --version`)
- Claude Code installed
- The `ai-first-sdlc-practices` repo cloned locally (source for plugins)

The SDLC plugins are installed by the loop as part of Phase 0. They install globally (`~/.claude/settings.json`) because Claude Code does not yet support project-scoped installation in non-interactive sessions (see [#81](https://github.com/SteveGJones/ai-first-sdlc-practices/issues/81)). You clear the cache before and clean up after.

### Clearing stale global plugin installs

If you previously installed the SDLC plugins globally (via `/plugin install sdlc-core@ai-first-sdlc` without `--scope project`), the global cached versions will take precedence over the project-scoped install. This means the test runs against old plugin versions, not the latest source.

To ensure the test uses the latest plugins from source:

1. **Remove the global plugin cache:**
   ```bash
   rm -rf ~/.claude/plugins/cache/ai-first-sdlc/
   ```

2. **Remove the SDLC plugins from global settings.** Edit `~/.claude/settings.json` and:
   - Remove all `sdlc-*@ai-first-sdlc` entries from `enabledPlugins`
   - Remove the `ai-first-sdlc` entry from `extraKnownMarketplaces`

   Or use Claude Code:
   ```
   /plugin uninstall sdlc-core@ai-first-sdlc
   /plugin uninstall sdlc-team-common@ai-first-sdlc
   /plugin uninstall sdlc-team-fullstack@ai-first-sdlc
   /plugin uninstall sdlc-team-pm@ai-first-sdlc
   /plugin uninstall sdlc-team-docs@ai-first-sdlc
   /plugin uninstall sdlc-lang-python@ai-first-sdlc
   ```

3. **Verify clean state:**
   ```bash
   # Should show no ai-first-sdlc entries
   grep "ai-first-sdlc" ~/.claude/settings.json
   # Should not exist
   ls ~/.claude/plugins/cache/ai-first-sdlc/ 2>/dev/null
   ```

After this, the test loop's project-scoped install in Phase 0 will install fresh from the source directory every time. No stale cache, no version confusion.

## How to Run

**Important:** You (a human) create and manage the repo. The Ralph loop never creates, deletes, or renames repositories. It only works inside the directory you give it.

1. **You** clear any stale global plugin cache:
   ```bash
   rm -rf ~/.claude/plugins/cache/ai-first-sdlc/
   ```
   This ensures the loop installs fresh from the source directory, not from a stale cache.

2. **You** create a blank GitHub repo and clone it:
   ```bash
   gh repo create my-sdlc-test --public --clone
   cd my-sdlc-test
   ```

3. **You** copy the test files into it:
   ```bash
   cp /path/to/ai-first-sdlc-practices/tests/integration/PROMPT.md .
   cp /path/to/ai-first-sdlc-practices/tests/integration/ralph.yml .
   ```

4. **You** start the loop:
   ```bash
   ralph run
   ```

4. When complete, open http://127.0.0.1:18080 to see the demo app.

5. Read `docs/build-journal.md` for the full framework quality report.

## Interpreting Results

### For Framework Maintainers

The most valuable sections of the build journal:

- **Friction Log** — prioritised list of framework issues found during the run.
  Each entry has phase, description, impact, and suggested fix.
- **Agent Value Assessment** — which agents contributed real value vs which
  were noise. Includes recommendation per agent.
- **Constitution Compliance** — which rules were exercised, which were unclear,
  which were impossible to follow.
- **What Should Change** — top 3 prioritised recommendations.

### For Demo Viewers

Browse the app at http://127.0.0.1:18080:
- `/timeline` — all build phases in chronological order
- `/dashboard` — summary metrics (phases, agents, pass rate)
- `/phases/<id>` — full detail for each phase with multi-paragraph review

## Expected Behaviour

- **Normal run**: 8-12 Ralph iterations, 45-60 minutes
- **If it spirals (>20 iterations)**: check the journal for where it's stuck.
  The journal entries will show which phase is failing and why.
- **Max iterations**: 40. If it hits 40, something is fundamentally broken —
  the journal is the diagnostic.

## After the Test

Clean up the global plugin install so it doesn't affect other projects:

```bash
# Remove the global plugin cache
rm -rf ~/.claude/plugins/cache/ai-first-sdlc/

# Optionally remove from global settings (in Claude Code):
/plugin uninstall sdlc-core@ai-first-sdlc
/plugin uninstall sdlc-team-common@ai-first-sdlc
/plugin uninstall sdlc-team-fullstack@ai-first-sdlc
/plugin uninstall sdlc-team-pm@ai-first-sdlc
/plugin uninstall sdlc-team-docs@ai-first-sdlc
/plugin uninstall sdlc-lang-python@ai-first-sdlc
```

## Re-running

To run the test again, **you** (not the loop) manage the repo:

```bash
# Option A: Delete and recreate (you decide)
cd ..
gh repo delete my-sdlc-test --yes
gh repo create my-sdlc-test --public --clone
cd my-sdlc-test

# Option B: Use a new repo name
gh repo create my-sdlc-test-2 --public --clone
cd my-sdlc-test-2
```

Then clear the cache, copy test files, and run:
```bash
rm -rf ~/.claude/plugins/cache/ai-first-sdlc/
cp /path/to/tests/integration/PROMPT.md .
cp /path/to/tests/integration/ralph.yml .
ralph run
```

**Never put repo deletion or plugin uninstall commands in PROMPT.md.** An unverified AI loop must not have the ability to delete repositories or modify global settings.
