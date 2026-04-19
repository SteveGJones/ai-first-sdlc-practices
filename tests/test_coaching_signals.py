#!/usr/bin/env python3
"""Tests for coaching_signals — tiered coaching signal analysis."""

from pathlib import Path

from sdlc_workflows_scripts import coaching_signals


class TestSignalTiers:
    def test_stale_image_is_advisory(self) -> None:
        team = {
            "name": "dev-team",
            "status": "active",
            "staleness": "stale",
            "updated": "2026-04-12",
            "image_built": "2026-04-10",
            "workflow_count": 1,
        }
        signals = coaching_signals.analyse_team(team)
        stale = [s for s in signals if s["type"] == "stale_image"]
        assert len(stale) == 1
        assert stale[0]["tier"] == "advisory"

    def test_not_built_is_critical(self) -> None:
        team = {
            "name": "new-team",
            "status": "active",
            "staleness": "not_built",
            "workflow_count": 1,
        }
        signals = coaching_signals.analyse_team(team)
        not_built = [s for s in signals if s["type"] == "not_built"]
        assert len(not_built) == 1
        assert not_built[0]["tier"] == "critical"

    def test_unused_team_is_advisory(self) -> None:
        team = {
            "name": "orphan",
            "status": "active",
            "staleness": "current",
            "workflow_count": 0,
        }
        signals = coaching_signals.analyse_team(team)
        unused = [s for s in signals if s["type"] == "unused_team"]
        assert len(unused) == 1
        assert unused[0]["tier"] == "advisory"

    def test_healthy_team_has_no_signals(self) -> None:
        team = {
            "name": "healthy",
            "status": "active",
            "staleness": "current",
            "workflow_count": 2,
        }
        signals = coaching_signals.analyse_team(team)
        assert signals == []


class TestFleetSignals:
    def test_aggregates_across_teams(self) -> None:
        teams = [
            {
                "name": "stale-team",
                "status": "active",
                "staleness": "stale",
                "updated": "2026-04-12",
                "image_built": "2026-04-10",
                "workflow_count": 1,
            },
            {
                "name": "healthy",
                "status": "active",
                "staleness": "current",
                "workflow_count": 1,
            },
        ]
        result = coaching_signals.analyse_fleet(teams)
        assert result["critical"] == []
        assert len(result["advisory"]) == 1
        assert result["advisory"][0]["team"] == "stale-team"

    def test_empty_fleet(self) -> None:
        result = coaching_signals.analyse_fleet([])
        assert result == {"critical": [], "advisory": [], "informational": []}


class TestOverrideSignals:
    def test_frequent_override_detected(self, tmp_path: Path) -> None:
        """An agent extended 3+ times triggers a promotion signal."""
        log_path = tmp_path / "overrides.jsonl"
        lines = [
            '{"team": "dev", "agent": "sec:architect", "workflow": "feat"}',
            '{"team": "dev", "agent": "sec:architect", "workflow": "feat"}',
            '{"team": "dev", "agent": "sec:architect", "workflow": "fix"}',
        ]
        log_path.write_text("\n".join(lines) + "\n")

        signals = coaching_signals.analyse_overrides(log_path, threshold=3)
        assert len(signals) == 1
        assert signals[0]["type"] == "frequent_override"
        assert signals[0]["agent"] == "sec:architect"
        assert signals[0]["tier"] == "informational"

    def test_below_threshold_no_signal(self, tmp_path: Path) -> None:
        log_path = tmp_path / "overrides.jsonl"
        log_path.write_text('{"team": "dev", "agent": "sec:architect"}\n')
        signals = coaching_signals.analyse_overrides(log_path, threshold=3)
        assert signals == []

    def test_missing_log_file(self, tmp_path: Path) -> None:
        signals = coaching_signals.analyse_overrides(
            tmp_path / "nonexistent.jsonl"
        )
        assert signals == []
