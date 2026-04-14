"""Minimal task tracker — smoke test project."""

from __future__ import annotations


class TaskTracker:
    """In-memory task tracker with add, complete, and list operations."""

    def __init__(self) -> None:
        self._tasks: dict[str, bool] = {}

    def add(self, name: str) -> None:
        """Add a new task. Raises ValueError if it already exists."""
        if name in self._tasks:
            raise ValueError(f"Task already exists: {name}")
        self._tasks[name] = False

    def complete(self, name: str) -> None:
        """Mark a task as complete. Raises KeyError if not found."""
        if name not in self._tasks:
            raise KeyError(f"Task not found: {name}")
        self._tasks[name] = True

    def list_tasks(self) -> list[dict[str, object]]:
        """Return all tasks as a list of dicts."""
        return [
            {"name": name, "done": done}
            for name, done in sorted(self._tasks.items())
        ]

    def pending_count(self) -> int:
        """Count of incomplete tasks."""
        return sum(1 for done in self._tasks.values() if not done)


if __name__ == "__main__":
    import sys

    if "--self-test" in sys.argv:
        t = TaskTracker()
        t.add("write tests")
        t.add("implement feature")
        t.complete("write tests")
        assert t.pending_count() == 1
        assert len(t.list_tasks()) == 2
        print("Self-test passed.")
    else:
        print("Usage: python src/app.py --self-test")
