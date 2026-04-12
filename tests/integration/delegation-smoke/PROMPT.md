# Delegation Smoke Test

You are running inside a Docker container with Archon and Claude Code installed. Your job is to execute an autonomous fix-review loop via Archon and verify it actually fixes the code.

## Phase 1: Verify Prerequisites

Check the following. Report PASS or FAIL for each:

1. Archon CLI is installed: `archon version`
2. Archon sees the smoke workflow: `archon workflow list` shows `smoke-fix-loop`
3. SDLC plugins are installed: Check for sdlc-core in installed plugins

If any prerequisite fails, report and stop.

## Phase 2: Record Initial State

Before running the workflow, record the initial state of the fixture project:

```bash
cat src/app.py
cat tests/test_app.py
```

Note the known issues:
- SQL injection in GET /users (f-string in SQL)
- No input validation on POST /users
- No test for DELETE endpoint
- debug=True in production code

## Phase 3: Run the Fix-Review Loop

Execute the fix-review workflow:

```bash
archon workflow run smoke-fix-loop --no-worktree 2>&1
```

This workflow:
1. Reads the code, fixes issues, adds tests, reviews its own work
2. If issues remain, loops back with fresh context (max 3 iterations)
3. Produces a final report with structured JSON

Monitor the output. The workflow uses Sonnet for each Claude instance.

## Phase 4: Verify Results

After the workflow completes, check:

4. Workflow completed (not timed out or errored)
5. At least one commit was made (code was actually changed):
   ```bash
   git log --oneline | head -5
   ```
6. SQL injection is fixed in src/app.py (no f-string in SQL queries):
   ```bash
   grep -n "f\"SELECT\|f'SELECT" src/app.py && echo "STILL_VULNERABLE" || echo "FIXED"
   ```
7. Input validation exists in src/app.py:
   ```bash
   grep -n "if.*not.*data\|KeyError\|get(" src/app.py | head -5
   ```
8. debug=True is removed or guarded:
   ```bash
   grep -n "debug=True" src/app.py && echo "STILL_DEBUG" || echo "FIXED"
   ```
9. DELETE endpoint has a test:
   ```bash
   grep -n "def test.*delete\|DELETE" tests/test_app.py | head -5
   ```
10. Final report JSON is valid with required fields (iterations_completed, issues_fixed, tests_added, clean)
11. Total workflow duration was under 10 minutes

Print a summary:

```
=== Delegation Smoke Test Results ===
Check 1 (Archon installed):          PASS/FAIL
Check 2 (workflow discovered):       PASS/FAIL
Check 3 (plugins installed):         PASS/FAIL
Check 4 (workflow completed):        PASS/FAIL
Check 5 (commits made):             PASS/FAIL
Check 6 (SQL injection fixed):      PASS/FAIL
Check 7 (input validation added):   PASS/FAIL
Check 8 (debug mode fixed):         PASS/FAIL
Check 9 (DELETE test added):        PASS/FAIL
Check 10 (final report valid):      PASS/FAIL
Check 11 (duration < 10min):        PASS/FAIL

Result: X/11 PASS
```

Output `LOOP_COMPLETE`.
