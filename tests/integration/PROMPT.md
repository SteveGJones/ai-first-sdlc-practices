# PROMPT.md — SDLC Plugin Integration Test

Build a Python web app from scratch in this blank repository using the AI-First SDLC plugin framework. The app displays a visual timeline of its own construction. Every phase produces a detailed journal entry documenting what worked, what didn't, and what should change in the framework.

You are done when: the app is **running on port 18080**, **all tests pass**, the **PR is merged to main**, and the **Framework Quality Report is complete**.

## Ground Rules

1. **Virtual environment first.** Before any `pip install` or Python execution: `python3 -m venv .venv && source .venv/bin/activate`. Verify with `which python`. If it doesn't show `.venv/bin/python`, stop and fix.
2. **Tests are continuous.** Set up pytest before writing app code. Write tests per module. Run them after every change. No module is complete without tests.
3. **Smoke test before every commit.** Start the app, hit an endpoint. If it crashes, fix it. Static analysis passing does not mean the code works.
4. **Invoke `verification-enforcer` at every phase boundary.** It checks: documentation matches code, tests exist and pass, the app actually runs. Nothing proceeds until it passes.
5. **Journal every phase** using the prescriptive format below. You cannot skip sections or rubber-stamp with "everything went well."
6. **Port 18080.** Not 5000 — that conflicts with macOS AirPlay. Hardcode `port=18080` in the app's `run()` call.

## Build Journal Format

Maintain `docs/build-journal.md` throughout. Every phase appends an entry using this exact template. **All 8 sections are mandatory.**

```
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

---

## Phase 0: Bootstrap

**Assumption:** You are in a blank, checked-out GitHub repo. A human created this repo and ran `ralph run` in it. Do not create, delete, or rename repositories.

### 0a. Virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Verify `which python` shows `.venv/bin/python`.

### 0b. Gitignore

Create `.gitignore`:
```
.venv/
__pycache__/
*.pyc
*.pyo
.env
*.db
./tmp/
.claude/
.ralph/
```

### 0c. Install SDLC plugins from local marketplace

```
/plugin marketplace add /Users/stevejones/Documents/Development/ai-first-sdlc-practices/plugins
/plugin install sdlc-core@ai-first-sdlc
```

Run team setup:
```
/sdlc-core:setup-team
```

Select **A. Full-stack web application**. Say yes to PM and docs. Then:
```
/plugin install sdlc-lang-python@ai-first-sdlc
```

Verify: `/plugin list` should show sdlc-core, sdlc-team-common, sdlc-team-fullstack, sdlc-team-pm, sdlc-team-docs, sdlc-lang-python.

### 0d. Initial commit

Update `README.md`:
```markdown
# SDLC Integration Test

Python web app built by Claude using the AI-First SDLC plugin framework.
Self-documenting: the app displays its own build timeline.
```

Commit and push to establish the remote baseline.

### 0e. Start build journal

Create `docs/build-journal.md` with the Phase 0 entry using the journal format above.

---

## Phase 1: Planning

Use `/sdlc-core:new-feature` to create feature artifacts and branch.

Feature: **Build Journal Web App** — a Python web app that displays a visual timeline of how it was built, with phase details, agent usage, and validation results.

Consult the `solution-architect` agent to validate the approach.

Record Phase 1 in the journal.

---

## Phase 2: Architecture

Consult the `solution-architect` agent for system design.

### Functional Requirements
1. Python web app (Flask or FastAPI — let `language-python-expert` recommend)
2. SQLite database for build phase data
3. Timeline view showing all build phases in order
4. Detail view per phase showing the **full build journal content** — not summaries, the complete text:
   - What was done (full description)
   - Agent contributions (what each agent recommended and whether it was followed)
   - What worked and what didn't (multi-paragraph honest assessment)
   - Validation results (actual command output)
   - Decisions made and why (with rationale)
   - Framework recommendations
5. Dashboard: total phases, agents invoked, pass/fail rate
6. REST API for CRUD on phases
7. **The app is a browsable version of the build journal.** Phase detail pages must show the full narrative. If a detail page shows only a one-line summary, the data model is too thin.

### Non-Functional Requirements
1. Runs with `python app.py` — no Docker
2. **Must listen on port 18080** (not 5000). Hardcode `port=18080`.
3. Dependencies in `requirements.txt`, installed in venv
4. Fully typed (mypy compatible)
5. Passes SDLC validation

Have `critical-goal-reviewer` review the architecture against requirements.

Record Phase 2 in the journal.

---

## Phase 3: Implementation

Build the app using team agents as appropriate.

**Before writing any application code:**
1. `pip install pytest` into the venv
2. Create `tests/` directory and `tests/conftest.py`
3. Add pytest to `requirements-dev.txt`

**During implementation:**
- Write tests for each module as it is created
- Run `pytest --tb=short -q` after completing each module
- Run `/sdlc-core:validate --syntax` after each significant change
- **Smoke test before finishing**: start the app, confirm it launches, hit one endpoint

Have `code-review-specialist` review the code. Untested code fails review.

**Before leaving Phase 3**, invoke the `verification-enforcer` agent. It must confirm: tests exist for every module, tests pass, the app starts, and at least one endpoint returns HTTP 200.

Record Phase 3 in the journal — include test results, agent contributions, and the verification-enforcer report.

---

## Phase 4: Testing & Verification

**Dedicated testing phase — not a rubber stamp.**

1. Run the full test suite and record output:
   ```bash
   pytest -v --tb=short
   ```

2. Smoke test the running application:
   - Start the app
   - Hit every endpoint
   - Confirm UI renders and API returns valid JSON
   - Record any errors and fixes

3. Verify all modules import cleanly:
   ```bash
   python -c "import app; import models; import database"
   ```
   (adjust module names to match actual project structure)

4. If anything fails, fix and re-run everything. Do not proceed until green.

Invoke `verification-enforcer` — full 3-check verification (docs-code fidelity, tests, runtime).

Record Phase 4 with actual pytest output and endpoint responses.

---

## Phase 5: Self-Population

Seed the database with all build journal phases (0-4 plus this phase). Data must come from actual `docs/build-journal.md` entries — **the full text of each section, not abbreviated summaries.**

Each phase record in the database must include:
- The complete "What was done" text
- The complete "Agent contributions" text
- The complete "What worked" and "What didn't work" text
- The complete "Validation result" text
- The complete "Decisions made and why" text
- The complete "Framework recommendations" text
- The agents and skills lists

When you view a phase detail page in the browser, you should see the full journal entry — multiple paragraphs of honest assessment, specific validation output, detailed rationale. **If the detail page shows only a one-line summary, the seed data is too thin. Fix it.**

Verify the app runs and displays the full seeded data correctly. Run pytest again.

Record Phase 5.

---

## Phase 6: Validation & Hardening

Run full validation:
```
/sdlc-core:validate --pre-push
```

Fix every issue. Note each fix in the journal.

Have `critical-goal-reviewer` do final review against Phase 2 requirements.

Invoke `verification-enforcer` for full verification: documentation-code fidelity (do the architecture docs match what was built?), test execution, and runtime proof. Include its report in the journal.

Record Phase 6.

---

## Phase 7: Prove It Runs

**The app must be proven running before any git operations.**

1. Start the application:
   ```bash
   source .venv/bin/activate
   python app.py &
   APP_PID=$!
   sleep 3
   ```

2. Verify it started:
   ```bash
   curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:18080/timeline
   curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:18080/dashboard
   curl -s http://127.0.0.1:18080/api/phases | python -m json.tool | head -20
   ```
   Every request must succeed. If any fail: stop the app, fix the error, re-run tests, restart, try again.

3. Record Phase 7 in the journal with the actual HTTP responses and status codes.

4. Stop the app:
   ```bash
   kill $APP_PID 2>/dev/null
   ```

**Do NOT proceed to Phase 8 unless the app started and all endpoints returned valid responses.**

---

## Phase 8: Ship — Commit, Push, PR, Merge

Only after the app has been proven running:

1. Seed remaining phases (6, 7, 8) into the database
2. Update the retrospective file
3. Final `pytest -v` — must be green
4. Stage and commit all changes (conventional commit format)
5. Push the feature branch
6. Create the PR using `gh pr create`
7. Merge the PR using `gh pr merge --squash`
8. Record Phase 8 in the journal — include the PR URL and merge confirmation

---

## Phase 9: Session Handoff

A new Claude Code session in this directory must work immediately.

### 9a. Create CLAUDE.md

Create `CLAUDE.md` in the project root describing:
- Quick start commands (activate venv, run app, run tests)
- Project summary (what it is, how it was built)
- Architecture (framework, database, port, key files)
- Validation commands
- SDLC plugin info (which plugins, marketplace path)

Adjust to match what was actually built — do not copy a template blindly.

### 9b. Create Claude memory

Create `.claude/memory/MEMORY.md` with:
- Project type, framework, database, port
- That this was built as an SDLC plugin integration test
- Build journal location and what it contains
- Key architectural decisions and why

### 9c. Start the app and leave it running

```bash
source .venv/bin/activate
nohup python app.py > app.log 2>&1 &
echo "App running at http://127.0.0.1:18080"
```

Record Phase 9 in the journal.

---

## Framework Quality Report

After all phases (0-9), append this report to the build journal. **Every section is mandatory.**

```
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
Every point where you had to work around something, retry,
deviate from instructions, or spend extra iterations:
| Phase | Friction | Impact | Suggested Fix |
|-------|----------|--------|---------------|

### What Should Change
Top 3 recommendations for the framework, prioritised by impact.

### Verdict
<One paragraph: Is the framework ready for external users?
What's the single biggest remaining gap?>
```

---

Output `LOOP_COMPLETE`.

**IMPORTANT: Do NOT output LOOP_COMPLETE until:**
1. All tests pass
2. The application has been started and all endpoints verified
3. Changes are committed and pushed
4. PR is created and merged to main
5. Build journal complete with all 8 sections at every phase
6. Framework Quality Report complete with Friction Log and Agent Value Assessment
7. CLAUDE.md and Claude memory exist and accurately describe the project
8. App is running on port 18080
