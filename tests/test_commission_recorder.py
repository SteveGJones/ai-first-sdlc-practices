"""Tests for plugins.sdlc-core.scripts.commission.recorder."""
import json
from pathlib import Path

from sdlc_core_scripts.commission.recorder import (
    CommissioningRecord,
    read_record,
    write_record,
    is_commissioned,
    default_option_for_uncommissioned,
)


def test_write_and_read_round_trip(tmp_path: Path) -> None:
    """Writing a record and reading it back returns equivalent data."""
    config_path = tmp_path / ".sdlc" / "team-config.json"
    record = CommissioningRecord(
        sdlc_option="single-team",
        sdlc_level="production",
        commissioned_at="2026-04-27T10:00:00Z",
        commissioned_by="claude-agent",
        option_bundle_version="0.1.0",
    )

    write_record(config_path, record)

    loaded = read_record(config_path)
    assert loaded.sdlc_option == "single-team"
    assert loaded.sdlc_level == "production"
    assert loaded.option_bundle_version == "0.1.0"
    assert len(loaded.commissioning_history) == 1


def test_write_preserves_existing_team_config_keys(tmp_path: Path) -> None:
    """Writing a record into an existing team-config.json keeps unrelated keys."""
    config_path = tmp_path / ".sdlc" / "team-config.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        json.dumps({"existing_key": "existing_value", "team_name": "alpha"})
    )

    record = CommissioningRecord(
        sdlc_option="solo",
        sdlc_level="prototype",
        commissioned_at="2026-04-27T10:00:00Z",
        commissioned_by="alice",
        option_bundle_version="0.1.0",
    )
    write_record(config_path, record)

    loaded_raw = json.loads(config_path.read_text())
    assert loaded_raw["existing_key"] == "existing_value"
    assert loaded_raw["team_name"] == "alpha"
    assert loaded_raw["sdlc_option"] == "solo"


def test_write_appends_to_commissioning_history(tmp_path: Path) -> None:
    """Re-commissioning appends to history rather than replacing it."""
    config_path = tmp_path / ".sdlc" / "team-config.json"

    first = CommissioningRecord(
        sdlc_option="solo",
        sdlc_level="prototype",
        commissioned_at="2026-04-27T10:00:00Z",
        commissioned_by="alice",
        option_bundle_version="0.1.0",
    )
    write_record(config_path, first)

    second = CommissioningRecord(
        sdlc_option="single-team",
        sdlc_level="production",
        commissioned_at="2026-04-28T10:00:00Z",
        commissioned_by="alice",
        option_bundle_version="0.2.0",
    )
    write_record(config_path, second)

    loaded = read_record(config_path)
    assert loaded.sdlc_option == "single-team"  # latest wins
    assert len(loaded.commissioning_history) == 2
    assert loaded.commissioning_history[0]["sdlc_option"] == "solo"
    assert loaded.commissioning_history[1]["sdlc_option"] == "single-team"


def test_is_commissioned_true_when_record_exists(tmp_path: Path) -> None:
    """is_commissioned returns True when a record exists in the file."""
    config_path = tmp_path / ".sdlc" / "team-config.json"
    write_record(
        config_path,
        CommissioningRecord(
            sdlc_option="single-team",
            sdlc_level="production",
            commissioned_at="2026-04-27T10:00:00Z",
            commissioned_by="claude-agent",
            option_bundle_version="0.1.0",
        ),
    )

    assert is_commissioned(config_path) is True


def test_is_commissioned_false_when_file_absent(tmp_path: Path) -> None:
    """is_commissioned returns False when team-config.json does not exist."""
    config_path = tmp_path / ".sdlc" / "team-config.json"
    assert is_commissioned(config_path) is False


def test_is_commissioned_false_when_file_lacks_sdlc_option(tmp_path: Path) -> None:
    """is_commissioned returns False when team-config.json has no sdlc_option key."""
    config_path = tmp_path / ".sdlc" / "team-config.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(json.dumps({"team_name": "alpha"}))

    assert is_commissioned(config_path) is False


def test_default_option_for_uncommissioned_returns_single_team() -> None:
    """Backward compatibility: uncommissioned projects default to single-team."""
    assert default_option_for_uncommissioned() == "single-team"
