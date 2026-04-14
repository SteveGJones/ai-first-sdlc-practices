#!/usr/bin/env python3
"""Tests for override_logger — team_extend override logging."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import plugins_sdlc_workflows_scripts as scripts  # noqa: E402

override_logger = scripts.override_logger


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
