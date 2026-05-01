"""End-to-end tests of the commission flow against the sample bundle.

Each test simulates the bash flow inside skills/commission/SKILL.md
by invoking the same Python helpers (parse_manifest -> install_bundle ->
write_record) that the skill's bash snippets call. This catches gaps
between the helpers and the skill flow.
"""
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from sdlc_core_scripts.commission.installer import install_bundle
from sdlc_core_scripts.commission.manifest import parse_manifest
from sdlc_core_scripts.commission.recorder import (
    CommissioningRecord,
    is_commissioned,
    read_record,
    write_record,
)


REPO_ROOT = Path(__file__).parent.parent
SAMPLE_BUNDLE = REPO_ROOT / "skills/commission/templates/sample-bundle"
EMPTY_FIXTURE = REPO_ROOT / "tests/fixtures/commissioning/empty-project"
EXISTING_FIXTURE = REPO_ROOT / "tests/fixtures/commissioning/existing-project"


def test_fresh_project_full_commission_flow(tmp_path: Path) -> None:
    """A fresh project commissions cleanly: install bundle + write record."""
    project = tmp_path / "fresh"
    shutil.copytree(EMPTY_FIXTURE, project)

    manifest = parse_manifest(SAMPLE_BUNDLE / "manifest.yaml")

    assert is_commissioned(project / ".sdlc" / "team-config.json") is False

    install_bundle(SAMPLE_BUNDLE, project, manifest)
    record = CommissioningRecord(
        sdlc_option="single-team",
        sdlc_level="production",
        commissioned_at=datetime.now(timezone.utc).isoformat(),
        commissioned_by="claude-agent",
        option_bundle_version=manifest.version,
    )
    write_record(project / ".sdlc" / "team-config.json", record)

    # Verify final state
    assert (project / "CONSTITUTION.md").exists()
    assert (project / ".claude" / "agents" / "sample-agent.md").exists()
    assert is_commissioned(project / ".sdlc" / "team-config.json") is True

    loaded = read_record(project / ".sdlc" / "team-config.json")
    assert loaded.sdlc_option == "single-team"
    assert loaded.option_bundle_version == "0.0.1-mock"


def test_existing_project_keeps_unrelated_team_config_keys(tmp_path: Path) -> None:
    """A project with an existing team-config.json keeps its non-commissioning keys."""
    project = tmp_path / "existing"
    shutil.copytree(EXISTING_FIXTURE, project)

    # Pre-existing keys
    pre_config = json.loads((project / ".sdlc" / "team-config.json").read_text())
    assert pre_config["team_name"] == "alpha"

    manifest = parse_manifest(SAMPLE_BUNDLE / "manifest.yaml")
    install_bundle(SAMPLE_BUNDLE, project, manifest, overwrite=True)
    write_record(
        project / ".sdlc" / "team-config.json",
        CommissioningRecord(
            sdlc_option="single-team",
            sdlc_level="production",
            commissioned_at="2026-04-27T12:00:00Z",
            commissioned_by="claude-agent",
            option_bundle_version=manifest.version,
        ),
    )

    post_config = json.loads((project / ".sdlc" / "team-config.json").read_text())
    assert post_config["team_name"] == "alpha"  # unrelated key preserved
    assert post_config["sdlc_option"] == "single-team"
    assert post_config["created"] == "2025-12-01T00:00:00Z"


def test_re_commissioning_appends_to_history(tmp_path: Path) -> None:
    """Re-commissioning to a different option appends to commissioning_history."""
    project = tmp_path / "rec"
    shutil.copytree(EMPTY_FIXTURE, project)
    manifest = parse_manifest(SAMPLE_BUNDLE / "manifest.yaml")

    # First commission
    install_bundle(SAMPLE_BUNDLE, project, manifest)
    write_record(
        project / ".sdlc" / "team-config.json",
        CommissioningRecord(
            sdlc_option="solo",
            sdlc_level="prototype",
            commissioned_at="2026-04-27T10:00:00Z",
            commissioned_by="alice",
            option_bundle_version=manifest.version,
        ),
    )

    # Re-commission
    write_record(
        project / ".sdlc" / "team-config.json",
        CommissioningRecord(
            sdlc_option="single-team",
            sdlc_level="production",
            commissioned_at="2026-04-28T10:00:00Z",
            commissioned_by="alice",
            option_bundle_version=manifest.version,
        ),
    )

    record = read_record(project / ".sdlc" / "team-config.json")
    assert record.sdlc_option == "single-team"  # latest wins
    assert len(record.commissioning_history) == 2
    assert record.commissioning_history[0]["sdlc_option"] == "solo"
    assert record.commissioning_history[1]["sdlc_option"] == "single-team"
