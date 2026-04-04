# SDLC Plugin Integration Test

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
- Claude Code with SDLC plugins accessible at the marketplace path

## How to Run

1. Create a blank GitHub repo:
   ```bash
   gh repo create sdlc-integration-test --public --clone
   cd sdlc-integration-test
   ```

2. Copy the test files:
   ```bash
   cp /path/to/ai-first-sdlc-practices/tests/integration/PROMPT.md .
   cp /path/to/ai-first-sdlc-practices/tests/integration/ralph.yml .
   ```

3. Run:
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

## Cleaning Up

To re-run the test, delete and recreate the repo:
```bash
cd ..
gh repo delete sdlc-integration-test --yes
gh repo create sdlc-integration-test --public --clone
cd sdlc-integration-test
cp /path/to/tests/integration/PROMPT.md .
cp /path/to/tests/integration/ralph.yml .
ralph run
```
