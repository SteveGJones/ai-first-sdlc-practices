You are planning a change to a Python task tracker at /workspace.

Read src/app.py — it has a TaskTracker class.

Produce a plan document at /workspace/plan.md with:

## Scope
Short description of the change: adding a "priority" field.

## Acceptance Criteria
- add() accepts optional priority (default "medium", valid "low"/"medium"/"high")
- list_tasks() includes priority in returned dicts
- high_priority_count() method returns count of incomplete high-priority tasks

## Risks
Anything the dev-team should watch for.

Then commit: cd /workspace && git add -A && git commit -m "plan: priority field"
