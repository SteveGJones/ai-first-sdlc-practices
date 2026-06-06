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
