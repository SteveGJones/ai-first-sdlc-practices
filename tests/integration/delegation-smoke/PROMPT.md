# Delegation Smoke Test

You are running inside a Docker container with Archon and Claude Code installed. Your job is to execute a parallel workflow via Archon and verify it works.

## Phase 1: Verify Prerequisites

Check the following. Report PASS or FAIL for each:

1. Archon CLI is installed: `archon --version`
2. Archon sees the smoke workflow: `archon workflow list` shows `smoke-parallel-review`
3. SDLC plugins are installed: Check for sdlc-core in installed plugins

If any prerequisite fails, report and stop.

## Phase 2: Run the Parallel Workflow

Execute the smoke parallel review workflow:

```bash
archon run smoke-parallel-review
```

Monitor the output. This workflow runs two review agents in parallel (review-structure and review-tests), then synthesises their findings.

## Phase 3: Verify Results

After the workflow completes, check:

4. Node `review-structure` completed (output was captured)
5. Node `review-tests` completed (output was captured)
6. Both nodes ran concurrently (check Archon logs — start times should be within 5 seconds of each other)
7. `synthesise` node produced valid JSON with all required fields (issues_found, review_a_completed, review_b_completed, summary)
8. The synthesised output found at least 1 issue (the fixture has deliberate problems)
9. Total workflow duration was under 10 minutes

Print a summary:

```
=== Delegation Smoke Test Results ===
Check 1 (Archon installed):          PASS/FAIL
Check 2 (workflow discovered):       PASS/FAIL
Check 3 (plugins installed):         PASS/FAIL
Check 4 (review-structure complete): PASS/FAIL
Check 5 (review-tests complete):     PASS/FAIL
Check 6 (parallel execution):        PASS/FAIL
Check 7 (synthesis JSON valid):      PASS/FAIL
Check 8 (issues found):             PASS/FAIL
Check 9 (duration < 10min):         PASS/FAIL

Result: X/9 PASS
```

Output `LOOP_COMPLETE`.
