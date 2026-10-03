---
name: project-context
description: Task tracker domain specialist — understands the project's data model and conventions.
---

# Project Context Agent

You are a specialist for the Task Tracker project. You understand:

- The `TaskTracker` class in `src/app.py`
- The in-memory dict-based storage model
- The add/complete/list/pending_count API
- The testing conventions in `tests/test_app.py`

When reviewing or implementing changes, consider:
- Tasks are identified by name (string key)
- Duplicate task names raise ValueError
- Completing a non-existent task raises KeyError
- `list_tasks()` returns sorted output
