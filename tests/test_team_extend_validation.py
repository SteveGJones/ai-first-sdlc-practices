#!/usr/bin/env python3
"""Tests for team_extend validation in workflow-team checker."""

import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent.parent / "tools" / "validation"))
import check_workflow_teams  # noqa: E402


def write_yaml(parent: Path, name: str, content: str) -> Path:
    parent.mkdir(parents=True, exist_ok=True)
    path = parent / name
    path.write_text(content)
    return path


class TestTeamExtendValidation:
    def test_valid_extend_passes(self, tmp_path: Path) -> None:
        """team_extend with agents from an installed plugin passes."""
        write_yaml(
            tmp_path / "workflows",
            "dev.yaml",
            "name: dev\nnodes:\n"
            "  - id: impl\n    command: impl\n"
            "    image: sdlc-worker:dev-team\n"
            "    team_extend:\n"
            "      agents:\n"
            "        - sec-plugin:security-architect\n",
        )
        write_yaml(
            tmp_path / "teams",
            "dev-team.yaml",
            "schema_version: '1.0'\nname: dev-team\n"
            "status: active\nplugins: [sdlc-core]\n",
        )

        plugin_dir = tmp_path / "plugins" / "cache" / "mkt" / "sec-plugin" / "1.0"
        (plugin_dir / "agents").mkdir(parents=True)
        (plugin_dir / "agents" / "security-architect.md").write_text(
            "---\nname: security-architect\n---\n"
        )
        (plugin_dir / ".claude-plugin").mkdir(parents=True)
        (plugin_dir / ".claude-plugin" / "plugin.json").write_text("{}")

        installed_json = tmp_path / "installed_plugins.json"
        installed_json.write_text(json.dumps({
            "sec-plugin@mkt": {
                "name": "sec-plugin",
                "installPath": str(plugin_dir),
            },
        }))

        errors = check_workflow_teams.validate(
            workflows_dir=tmp_path / "workflows",
            teams_dir=tmp_path / "teams",
            installed_json=installed_json,
        )
        assert errors == []

    def test_extend_with_nonexistent_agent_fails(self, tmp_path: Path) -> None:
        """team_extend referencing an agent not in any plugin fails."""
        write_yaml(
            tmp_path / "workflows",
            "dev.yaml",
            "name: dev\nnodes:\n"
            "  - id: impl\n    command: impl\n"
            "    image: sdlc-worker:dev-team\n"
            "    team_extend:\n"
            "      agents:\n"
            "        - ghost-plugin:phantom-agent\n",
        )
        write_yaml(
            tmp_path / "teams",
            "dev-team.yaml",
            "schema_version: '1.0'\nname: dev-team\n"
            "status: active\nplugins: [sdlc-core]\n",
        )

        installed_json = tmp_path / "installed_plugins.json"
        installed_json.write_text(json.dumps({}))

        errors = check_workflow_teams.validate(
            workflows_dir=tmp_path / "workflows",
            teams_dir=tmp_path / "teams",
            installed_json=installed_json,
        )
        assert len(errors) == 1
        assert "ghost-plugin:phantom-agent" in errors[0]

    def test_no_team_extend_no_extra_validation(self, tmp_path: Path) -> None:
        """Nodes without team_extend are not affected by this check."""
        write_yaml(
            tmp_path / "workflows",
            "review.yaml",
            "name: review\nnodes:\n"
            "  - id: sec\n    command: review\n"
            "    image: sdlc-worker:sec-team\n",
        )
        write_yaml(
            tmp_path / "teams",
            "sec-team.yaml",
            "schema_version: '1.0'\nname: sec-team\n"
            "status: active\nplugins: [sdlc-core]\n",
        )

        errors = check_workflow_teams.validate(
            workflows_dir=tmp_path / "workflows",
            teams_dir=tmp_path / "teams",
        )
        assert errors == []
