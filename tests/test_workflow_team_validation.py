#!/usr/bin/env python3
"""Tests for workflow-team reference validation."""

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent.parent / "tools" / "validation"))
import check_workflow_teams  # noqa: E402


def write_yaml(parent: Path, name: str, content: str) -> Path:
    parent.mkdir(parents=True, exist_ok=True)
    path = parent / name
    path.write_text(content)
    return path


class TestWorkflowTeamValidation:
    def test_valid_reference_passes(self, tmp_path: Path) -> None:
        write_yaml(
            tmp_path / "workflows",
            "review.yaml",
            """\
name: review
nodes:
  - id: security
    command: sdlc-security-review
    image: sdlc-worker:security-team
""",
        )
        write_yaml(
            tmp_path / "teams",
            "security-team.yaml",
            """\
schema_version: "1.0"
name: security-team
status: active
plugins: [sdlc-core]
agents: []
skills: []
""",
        )
        errors = check_workflow_teams.validate(
            workflows_dir=tmp_path / "workflows",
            teams_dir=tmp_path / "teams",
        )
        assert errors == []

    def test_missing_team_manifest_fails(self, tmp_path: Path) -> None:
        write_yaml(
            tmp_path / "workflows",
            "review.yaml",
            """\
name: review
nodes:
  - id: security
    command: sdlc-security-review
    image: sdlc-worker:nonexistent-team
""",
        )
        (tmp_path / "teams").mkdir()
        errors = check_workflow_teams.validate(
            workflows_dir=tmp_path / "workflows",
            teams_dir=tmp_path / "teams",
        )
        assert any("nonexistent-team" in e for e in errors)

    def test_inactive_team_reference_warns(self, tmp_path: Path) -> None:
        write_yaml(
            tmp_path / "workflows",
            "review.yaml",
            """\
name: review
nodes:
  - id: security
    command: sdlc-security-review
    image: sdlc-worker:old-team
""",
        )
        write_yaml(
            tmp_path / "teams",
            "old-team.yaml",
            """\
schema_version: "1.0"
name: old-team
status: inactive
plugins: [sdlc-core]
agents: []
skills: []
""",
        )
        errors = check_workflow_teams.validate(
            workflows_dir=tmp_path / "workflows",
            teams_dir=tmp_path / "teams",
        )
        assert any("inactive" in e.lower() for e in errors)

    def test_base_image_always_valid(self, tmp_path: Path) -> None:
        write_yaml(
            tmp_path / "workflows",
            "review.yaml",
            """\
name: review
nodes:
  - id: validate
    command: sdlc-validate
    image: sdlc-worker:base
""",
        )
        (tmp_path / "teams").mkdir()
        errors = check_workflow_teams.validate(
            workflows_dir=tmp_path / "workflows",
            teams_dir=tmp_path / "teams",
        )
        assert errors == []

    def test_node_without_image_is_valid(self, tmp_path: Path) -> None:
        write_yaml(
            tmp_path / "workflows",
            "review.yaml",
            """\
name: review
nodes:
  - id: validate
    command: sdlc-validate
""",
        )
        (tmp_path / "teams").mkdir()
        errors = check_workflow_teams.validate(
            workflows_dir=tmp_path / "workflows",
            teams_dir=tmp_path / "teams",
        )
        assert errors == []

    def test_ephemeral_team_is_valid(self, tmp_path: Path) -> None:
        write_yaml(
            tmp_path / "workflows",
            "review.yaml",
            """\
name: review
nodes:
  - id: quick
    command: quick-check
    image: sdlc-worker:temp-team
""",
        )
        write_yaml(
            tmp_path / "teams",
            "temp-team.yaml",
            """\
schema_version: "1.0"
name: temp-team
status: ephemeral
plugins: [sdlc-core]
agents: []
skills: []
""",
        )
        errors = check_workflow_teams.validate(
            workflows_dir=tmp_path / "workflows",
            teams_dir=tmp_path / "teams",
        )
        assert errors == []
