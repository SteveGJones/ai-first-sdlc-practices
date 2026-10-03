You are implementing a change to a Python task tracker at /workspace.

Read src/app.py — it has a TaskTracker class with add, complete, list_tasks, pending_count.

Add a "priority" field:
1. add() accepts optional priority (default: "medium", valid: "low"/"medium"/"high")
2. list_tasks() includes priority in returned dicts
3. Add high_priority_count() returning count of incomplete high-priority tasks

Edit src/app.py and tests/test_app.py. Then commit:
  cd /workspace && git add -A && git commit -m "feat: add priority field"
