#!/usr/bin/env python3
"""Tests for teams_status_report — fleet status data generation."""

from datetime import datetime, timezone
from pathlib import Path

from sdlc_workflows_scripts import teams_status_report


def write_manifest(teams_dir: Path, name: str, **overrides: str) -> Path:
    """Write a minimal team manifest YAML."""
    fields = {
        "schema_version": '"1.0"',
        "name": name,
        "status": "active",
        "plugins": "[sdlc-core]",
        "agents": "[]",
        "skills": "[]",
        **overrides,
    }
    content = "\n".join(f"{k}: {v}" for k, v in fields.items())
    path = teams_dir / f"{name}.yaml"
    path.write_text(content)
    return path


class TestLoadManifests:
    def test_loads_all_yaml_files(self, tmp_path: Path) -> None:
        teams_dir = tmp_path / "teams"
        teams_dir.mkdir()
        write_manifest(teams_dir, "alpha")
        write_manifest(teams_dir, "beta")

        result = teams_status_report.load_manifests(teams_dir)
        assert len(result) == 2
        names = {m["name"] for m in result}
        assert names == {"alpha", "beta"}

    def test_skips_generated_subdir(self, tmp_path: Path) -> None:
        teams_dir = tmp_path / "teams"
        teams_dir.mkdir()
        write_manifest(teams_dir, "alpha")
        gen_dir = teams_dir / ".generated"
        gen_dir.mkdir()
        (gen_dir / "should-skip.yaml").write_text("name: skip")

        result = teams_status_report.load_manifests(teams_dir)
        assert len(result) == 1

    def test_empty_dir(self, tmp_path: Path) -> None:
        teams_dir = tmp_path / "teams"
        teams_dir.mkdir()
        result = teams_status_report.load_manifests(teams_dir)
        assert result == []


class TestStalenessCheck:
    def test_current_when_image_newer(self) -> None:
        manifest = {
            "name": "team-a",
            "updated": "2026-04-10T12:00:00",
            "image_built": "2026-04-12T12:00:00",
        }
        assert teams_status_report.staleness(manifest) == "current"

    def test_stale_when_manifest_newer(self) -> None:
        manifest = {
            "name": "team-a",
            "updated": "2026-04-12T12:00:00",
            "image_built": "2026-04-10T12:00:00",
        }
        assert teams_status_report.staleness(manifest) == "stale"

    def test_not_built_when_no_image_timestamp(self) -> None:
        manifest = {"name": "team-a", "updated": "2026-04-12T12:00:00"}
        assert teams_status_report.staleness(manifest) == "not_built"

    def test_current_when_equal(self) -> None:
        manifest = {
            "name": "team-a",
            "updated": "2026-04-12T12:00:00",
            "image_built": "2026-04-12T12:00:00",
        }
        assert teams_status_report.staleness(manifest) == "current"

    def test_stale_when_generated_claude_md_newer_than_image(
        self, tmp_path: Path
    ) -> None:
        """SA-M-5: if the generated team CLAUDE.md has been regenerated
        (because the project root CLAUDE.md changed) since the last
        image build, the team image is stale even though the manifest
        `updated` timestamp hasn't moved."""
        teams_dir = tmp_path
        generated = teams_dir / ".generated"
        generated.mkdir()
        claude_md = generated / "team-a-CLAUDE.md"
        claude_md.write_text("# Team A\n")
        # Force mtime well past the image_built timestamp.
        future_mtime = datetime(2030, 1, 1, tzinfo=timezone.utc).timestamp()
        import os

        os.utime(claude_md, (future_mtime, future_mtime))

        manifest_path = teams_dir / "team-a.yaml"
        manifest_path.write_text("name: team-a\n")
        manifest = {
            "name": "team-a",
            "updated": "2026-04-10T12:00:00",
            "image_built": "2026-04-10T12:00:00",
            "_manifest_path": str(manifest_path),
        }
        assert teams_status_report.staleness(manifest) == "stale"

    def test_current_when_generated_claude_md_missing(
        self, tmp_path: Path
    ) -> None:
        """No generated CLAUDE.md = fall back to manifest/updated comparison."""
        manifest_path = tmp_path / "team-a.yaml"
        manifest_path.write_text("name: team-a\n")
        manifest = {
            "name": "team-a",
            "updated": "2026-04-10T12:00:00",
            "image_built": "2026-04-12T12:00:00",
            "_manifest_path": str(manifest_path),
        }
        assert teams_status_report.staleness(manifest) == "current"


class TestWorkflowUsage:
    def test_counts_team_references(self, tmp_path: Path) -> None:
        wf_dir = tmp_path / "workflows"
        wf_dir.mkdir()
        (wf_dir / "review.yaml").write_text(
            "name: review\nnodes:\n"
            "  - id: sec\n    command: review\n    image: sdlc-worker:sec-team\n"
            "  - id: arch\n    command: review\n    image: sdlc-worker:sec-team\n"
        )
        (wf_dir / "dev.yaml").write_text(
            "name: dev\nnodes:\n"
            "  - id: impl\n    command: impl\n    image: sdlc-worker:dev-team\n"
        )

        usage = teams_status_report.workflow_usage(wf_dir)
        assert usage["sec-team"] == [
            {"workflow": "review", "node": "sec"},
            {"workflow": "review", "node": "arch"},
        ]
        assert usage["dev-team"] == [
            {"workflow": "dev", "node": "impl"},
        ]

    def test_empty_workflows_dir(self, tmp_path: Path) -> None:
        wf_dir = tmp_path / "workflows"
        wf_dir.mkdir()
        assert teams_status_report.workflow_usage(wf_dir) == {}


class TestFleetReport:
    def test_assembles_complete_report(self, tmp_path: Path) -> None:
        teams_dir = tmp_path / "teams"
        teams_dir.mkdir()
        write_manifest(
            teams_dir,
            "sec-team",
            status="active",
            agents="[sdlc-core:architect]",
            skills="[sdlc-core:validate]",
            updated="2026-04-10T12:00:00",
            image_built="2026-04-12T12:00:00",
        )

        wf_dir = tmp_path / "workflows"
        wf_dir.mkdir()
        (wf_dir / "review.yaml").write_text(
            "name: review\nnodes:\n"
            "  - id: sec\n    command: review\n    image: sdlc-worker:sec-team\n"
        )

        report = teams_status_report.fleet_report(
            teams_dir=teams_dir,
            workflows_dir=wf_dir,
        )
        assert report["team_count"] == 1
        assert report["teams"][0]["name"] == "sec-team"
        assert report["teams"][0]["staleness"] == "current"
        assert report["teams"][0]["workflow_count"] == 1
