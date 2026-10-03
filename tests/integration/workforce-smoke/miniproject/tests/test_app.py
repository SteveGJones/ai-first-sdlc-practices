"""Tests for the task tracker."""

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

TaskTracker = importlib.import_module("app").TaskTracker


def test_add_and_list() -> None:
    t = TaskTracker()
    t.add("task-a")
    tasks = t.list_tasks()
    assert len(tasks) == 1
    assert tasks[0]["name"] == "task-a"
    assert tasks[0]["done"] is False


def test_complete() -> None:
    t = TaskTracker()
    t.add("task-b")
    t.complete("task-b")
    tasks = t.list_tasks()
    assert tasks[0]["done"] is True


def test_pending_count() -> None:
    t = TaskTracker()
    t.add("x")
    t.add("y")
    t.complete("x")
    assert t.pending_count() == 1
