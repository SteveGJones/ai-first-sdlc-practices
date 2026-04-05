# Integration Test Harness: Ralph-Driven Plugin Ecosystem Test

**Date**: 2026-04-04
**Status**: Approved
**Epic**: #75 — Plugin Ecosystem Integration Test Findings
**Issue**: #80

## Problem

The SDLC plugin ecosystem has no repeatable, automated integration test. The only way to verify the framework works end-to-end is to manually run a PROMPT.md that evolved across multiple sessions with live fixes. We need a stable, self-contained test harness that:

1. Proves the plugin ecosystem works from a blank repo to a merged PR with zero human intervention
2. Produces a working demo app that external users can browse
3. Generates a detailed framework quality report that tells us what works and what doesn't

## Solution

A pair of files (`PROMPT.md` + `ralph.yml`) that live in `tests/integration/` in this repo. Copied into a blank checked-out GitHub repo and executed with `ralph run`, they produce a Build Journal Web App — a self-documenting Python web app that displays a visual timeline of its own construction with full review perspectives at every phase.

The build journal serves two audiences reading the same content:
- **External users** see how an AI built an app phase by phase, what it decided and why
- **Framework maintainers** see which agents contributed, where skills fell short, what friction the AI hit, and what it recommends changing

## Deliverables

### File Structure

```
tests/integration/
  PROMPT.md       — the test prompt (standalone, self-contained)
  ralph.yml       — ralph loop configuration
  README.md       — how to run the test and interpret results
```

### ralph.yml

```yaml
cli:
  backend: "claude"

event_loop:
  prompt_file: "PROMPT.md"
  completion_promise: "LOOP_COMPLETE"
  max_iterations: 40
```

40 iterations: normal runs should complete in 8-12. If it spirals to 40, that's a finding — the journal will show where and why.

### PROMPT.md Structure

#### Part 1: Preamble

What this test is, ground rules, local marketplace path. Ground rules:

1. Virtual environment first — `python3 -m venv .venv && source .venv/bin/activate`, verify with `which python`
2. Tests are continuous — pytest before app code, tests per module, run after every change
3. Smoke test before every commit — start app, hit endpoint, fix if broken
4. Invoke `verification-enforcer` at every phase boundary
5. Journal everything using the prescriptive format (Part 3)
6. Port 18080 (not 5000 — macOS AirPlay conflict)
7. Local marketplace: `/Users/stevejones/Documents/Development/ai-first-sdlc-practices/plugins`

#### Part 2: Phases

| Phase | Title | Entry Criteria | Exit Gate |
|-------|-------|---------------|-----------|
| 0 | Bootstrap | Blank repo checked out | venv verified, plugins installed, initial commit pushed |
| 1 | Planning | Phase 0 complete | Feature artifacts created via `/sdlc-core:new-feature`, solution-architect consulted |
| 2 | Architecture | Phase 1 complete | Design complete, critical-goal-reviewer approved |
| 3 | Implementation | Phase 2 complete | Code + tests written, pytest passing, app starts |
| 4 | Testing & Verification | Phase 3 complete | verification-enforcer passes all 3 checks (docs match code, tests pass, app runs) |
| 5 | Self-Population | Phase 4 complete | Database seeded with full journal content, app displays it correctly, detail pages show multi-paragraph content not summaries |
| 6 | Validation & Hardening | Phase 5 complete | `/sdlc-core:validate --pre-push` passes, critical-goal-reviewer final review |
| 7 | Prove It Runs | Phase 6 complete | App started, every endpoint curled, HTTP responses recorded in journal |
| 8 | Ship | Phase 7 complete | Committed, pushed, PR created, PR merged to main |
| 9 | Session Handoff | Phase 8 complete | CLAUDE.md created, memory configured, **app left running** |

Phase 9 leaves the app running so a user can open a browser immediately after ralph finishes.

#### Part 3: Build Journal Format

Every phase appends an entry to `docs/build-journal.md` using this prescriptive template. The AI cannot skip sections or rubber-stamp with "everything went well."

```markdown
## Phase N: <Title>
**Started**: <timestamp>
**Completed**: <timestamp>
**Agents invoked**: <list with what each actually contributed>
**Skills used**: <list with what each actually did>

### What was done
<Files created/modified, commands run, concrete actions>

### Agent contributions
<For each agent invoked: what was asked, what it recommended,
whether the recommendation was followed, and if not, why not.
If no agents were invoked, explain why — was the phase mechanical
or was there a reason specialists weren't consulted?>

### What worked
<Specific things that went smoothly — which tools, patterns,
or framework features made this phase easier>

### What didn't work
<Friction, errors, workarounds, gaps. Be specific: "ruff check
returned 12 E501 errors" not "linting had some issues".
If nothing went wrong, say so — but explain why you're confident>

### Validation result
<Actual command output, not just pass/fail.
Paste the pytest summary line. Paste the ruff output.
Show the HTTP status codes from smoke tests.>

### Decisions made and why
<Every choice with rationale. Framework, patterns, architecture,
even "I chose not to invoke X agent because Y">

### Framework recommendations
<What would you change about the SDLC framework based on this phase?
Missing agent? Unclear constitution rule? Skill that should exist?
If nothing, say "No recommendations — this phase worked as designed">
```

Key differences from the previous format:
- **Agent contributions** is its own section — forces detail on what agents actually did
- **What didn't work** is separate from what worked — forces honesty
- **Framework recommendations** is new — forces critical thinking about the framework at every phase

#### Part 4: Framework Quality Report

After all phases, the journal gets a structured report:

```markdown
## Framework Quality Report

### Plugin Ecosystem
- Marketplace registration: <pass/fail + details>
- Plugin installation: <pass/fail + details>
- Each skill invoked: <name, worked/failed, notes>
- Each agent invoked: <name, what it contributed, quality assessment>

### Verification Enforcer Assessment
- Invoked at which phases: <list>
- Documentation-code mismatches found: <count + details>
- Missing tests flagged: <yes/no + details>
- Runtime errors caught that static analysis missed: <yes/no + details>
- Verdict: <did the enforcer add value or rubber-stamp?>

### Testing Pipeline
- Were tests written alongside implementation? <evidence>
- Did tests catch real bugs during development? <which ones>
- Did the smoke test catch anything? <what>
- Final: <N> tests, <N> passed, <N> failed
- App started on first attempt? <yes/no, if no what failed>

### Constitution Compliance
- Which articles were exercised? <list with notes>
- Which articles were irrelevant to this project? <list>
- Any articles that were unclear or contradictory? <details>
- Any rules that were impossible to follow? <details>

### Agent Value Assessment
For each agent invoked across all phases:
| Agent | Times Used | Added Value? | Best Contribution | Recommendation |
|-------|-----------|-------------|-------------------|----------------|

### Friction Log
Every point where the AI had to work around something, retry,
deviate from instructions, or spend extra iterations:
| Phase | Friction | Impact | Suggested Fix |
|-------|----------|--------|---------------|

### What Should Change
Top 3 recommendations for the framework, prioritised by impact.

### Verdict
<One paragraph: Is the framework ready for external users?
What's the single biggest remaining gap?>
```

The **Friction Log** is the most valuable output for framework maintainers — a prioritised list of what to fix next. The **Agent Value Assessment** shows which agents earn their invocation cost.

### App Requirements

The Build Journal Web App (same as current test):

**Functional:**
1. Python web app (Flask or FastAPI — let language-python-expert recommend)
2. SQLite database for build phase data
3. Timeline view showing all phases in order
4. Detail view per phase showing **full journal content** — complete multi-paragraph review perspectives, agent contributions, friction, recommendations. Not summaries.
5. Dashboard: total phases, agents invoked, pass/fail rate
6. REST API for CRUD on phases
7. Port 18080

**Non-Functional:**
1. Runs with `python app.py` — no Docker
2. All dependencies in `requirements.txt`, installed in venv
3. Fully typed (mypy compatible)
4. Passes SDLC validation

### LOOP_COMPLETE Prerequisites

Do NOT output LOOP_COMPLETE until:
1. All tests pass
2. App started and all endpoints verified with actual HTTP responses
3. Committed, pushed, PR created, PR merged to main
4. Build journal complete with honest review at every phase
5. Framework Quality Report appended with Friction Log and Agent Value Assessment
6. CLAUDE.md exists and accurately describes the project
7. Claude memory configured for session continuity
8. App left running on port 18080

### README.md

The README in `tests/integration/` explains:

```markdown
# SDLC Plugin Integration Test

Automated end-to-end test of the AI-First SDLC plugin framework.
Produces a working demo app with a full framework quality report.

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

- **Friction Log**: Prioritised list of framework issues found during the run
- **Agent Value Assessment**: Which agents contributed vs which were noise
- **Verdict**: Overall framework readiness assessment

## Expected Duration

8-12 Ralph iterations, ~45-60 minutes. If it exceeds 20 iterations,
check the journal for where it's spiralling.
```

## Success Criteria

1. `ralph run` completes in under 20 iterations on a blank repo
2. The app is running and browsable at http://127.0.0.1:18080 when ralph finishes
3. Every phase in the journal has all 8 sections filled with specific, honest content
4. The Framework Quality Report has a populated Friction Log and Agent Value Assessment
5. The demo app's phase detail pages show full multi-paragraph journal content
6. PR is merged to main
7. A framework maintainer reading only the journal can identify what to fix next

## What This Does NOT Cover

- Non-Python projects (JS, Go, etc.) — future enhancement
- Multi-developer workflows — this tests solo AI development
- Enterprise-level SDLC features — this tests Prototype/Production level
- Performance benchmarking — this tests correctness, not speed
