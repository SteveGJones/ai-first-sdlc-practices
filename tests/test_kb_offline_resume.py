"""Tests for sdlc_knowledge_base_scripts.resume."""
from __future__ import annotations

from pathlib import Path

from sdlc_knowledge_base_scripts.resume import config_hash, content_hash


def test_content_hash_stable_and_sensitive():
    assert content_hash("abc") == content_hash("abc")
    assert content_hash("abc") != content_hash("abd")


def test_config_hash_order_independent():
    assert config_hash({"a": 1, "b": 2}) == config_hash({"b": 2, "a": 1})
    assert config_hash({"a": 1}) != config_hash({"a": 2})


from sdlc_knowledge_base_scripts.resume import LibraryLock


def test_fencing_token_monotonic(tmp_path: Path):
    lock1 = LibraryLock(tmp_path)
    t1 = lock1.acquire()
    lock1.release()
    lock2 = LibraryLock(tmp_path)
    t2 = lock2.acquire()
    assert t2 > t1
    assert lock2.current_token() == t2
    lock2.release()


def test_second_live_acquire_blocked(tmp_path: Path):
    a = LibraryLock(tmp_path)
    a.acquire()
    b = LibraryLock(tmp_path)
    try:
        acquired = b.try_acquire()
        assert acquired is None
    finally:
        a.release()


def test_stale_lock_reclaimed(tmp_path: Path):
    a = LibraryLock(tmp_path, ttl_seconds=0)
    a.acquire()
    b = LibraryLock(tmp_path, ttl_seconds=0)
    token = b.try_acquire()
    assert token is not None and token > 0
    b.release()


from sdlc_knowledge_base_scripts.resume import RunRegistry


def test_select_resumable_latest_compatible(tmp_path: Path):
    reg = RunRegistry(tmp_path)
    fp = {"operation": "ingest", "config": config_hash({"backend": "anthropic"})}
    r1 = reg.start_run("2026-06-06T00:00:00Z", fp)
    reg.set_state(r1, "failed")
    r2 = reg.start_run("2026-06-06T01:00:00Z", fp)
    reg.set_state(r2, "failed")
    assert reg.select_resumable(fp) == r2


def test_select_resumable_rejects_incompatible_config(tmp_path: Path):
    reg = RunRegistry(tmp_path)
    r1 = reg.start_run("2026-06-06T00:00:00Z",
                       {"operation": "ingest", "config": config_hash({"backend": "anthropic"})})
    reg.set_state(r1, "failed")
    other = {"operation": "ingest", "config": config_hash({"backend": "ollama"})}
    assert reg.select_resumable(other) is None


def test_completed_run_not_resumable(tmp_path: Path):
    reg = RunRegistry(tmp_path)
    fp = {"operation": "ingest", "config": "c"}
    r1 = reg.start_run("2026-06-06T00:00:00Z", fp)
    reg.set_state(r1, "completed")
    assert reg.select_resumable(fp) is None


from sdlc_knowledge_base_scripts.resume import step_id


def test_step_id_canonical_formula():
    assert step_id("run123", "reduce", "topic.md") == "run123:reduce:topic.md"
    assert step_id("run123", "extract", "src-slug") == "run123:extract:src-slug"
    assert step_id("r", "reduce", "t.md") == step_id("r", "reduce", "t.md")
