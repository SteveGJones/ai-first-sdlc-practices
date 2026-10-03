#!/usr/bin/env python3
"""Tests for override_logger — team_extend override logging."""

import json
from pathlib import Path

import pytest

from sdlc_workflows_scripts import override_logger


class TestLogOverride:
    def test_appends_entry(self, tmp_path: Path) -> None:
        log_path = tmp_path / "overrides.jsonl"
        override_logger.log_override(
            log_path=log_path,
            team="dev-team",
            agent="sec:architect",
            workflow="feature-dev",
            node="implement",
        )
        lines = log_path.read_text().strip().splitlines()
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["team"] == "dev-team"
        assert entry["agent"] == "sec:architect"
        assert entry["workflow"] == "feature-dev"
        assert entry["node"] == "implement"
        assert "timestamp" in entry

    def test_appends_multiple(self, tmp_path: Path) -> None:
        log_path = tmp_path / "overrides.jsonl"
        override_logger.log_override(log_path, "t1", "a1", "w1", "n1")
        override_logger.log_override(log_path, "t2", "a2", "w2", "n2")
        lines = log_path.read_text().strip().splitlines()
        assert len(lines) == 2

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        log_path = tmp_path / "logs" / "deep" / "overrides.jsonl"
        override_logger.log_override(log_path, "t", "a", "w", "n")
        assert log_path.exists()


class TestReadOverrides:
    def test_reads_all_entries(self, tmp_path: Path) -> None:
        log_path = tmp_path / "overrides.jsonl"
        override_logger.log_override(log_path, "t1", "a1", "w1", "n1")
        override_logger.log_override(log_path, "t2", "a2", "w2", "n2")
        entries = override_logger.read_overrides(log_path)
        assert len(entries) == 2

    def test_empty_file(self, tmp_path: Path) -> None:
        log_path = tmp_path / "overrides.jsonl"
        log_path.write_text("")
        entries = override_logger.read_overrides(log_path)
        assert entries == []

    def test_missing_file(self, tmp_path: Path) -> None:
        entries = override_logger.read_overrides(tmp_path / "nope.jsonl")
        assert entries == []


class TestConcurrentAppend:
    """CR-M-4: concurrent appends to the JSONL log must not lose or corrupt entries.

    POSIX ``open(path, "a")`` guarantees atomic appends for writes up to
    PIPE_BUF (4096 bytes on Linux/macOS).  Each override entry is ~200 bytes
    of JSON + newline, so concurrent ``log_override`` calls from multiple
    threads in the same process are safe.  This test locks that contract
    in place: if someone later switches to ``open("r+")`` + ``seek`` +
    ``write`` the assertion breaks immediately.
    """

    @pytest.mark.slow
    def test_concurrent_threads_do_not_lose_entries(self, tmp_path: Path) -> None:
        import threading

        log_path = tmp_path / "overrides.jsonl"
        threads_count = 8
        per_thread = 25
        total = threads_count * per_thread

        def worker(thread_idx: int) -> None:
            for i in range(per_thread):
                override_logger.log_override(
                    log_path,
                    team=f"t{thread_idx}",
                    agent=f"a{thread_idx}",
                    workflow="wf",
                    node=f"n{i}",
                )

        threads = [
            threading.Thread(target=worker, args=(idx,)) for idx in range(threads_count)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Every write must be present and parseable.
        entries = override_logger.read_overrides(log_path)
        assert len(entries) == total, (
            f"expected {total} entries, got {len(entries)} — "
            "concurrent appends are dropping writes"
        )

        # Each thread's writes must all be present (no interleaved corruption).
        per_team_counts: dict[str, int] = {}
        for e in entries:
            per_team_counts[e["team"]] = per_team_counts.get(e["team"], 0) + 1
        for idx in range(threads_count):
            assert per_team_counts.get(f"t{idx}") == per_thread, (
                f"team t{idx} wrote {per_team_counts.get(f't{idx}')} entries, "
                f"expected {per_thread}"
            )
