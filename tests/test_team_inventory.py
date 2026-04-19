#!/usr/bin/env python3
"""Tests for team_inventory — plugin agent and skill discovery."""

import json
from pathlib import Path

from sdlc_workflows_scripts import team_inventory


class TestDiscoverPluginAgents:
    def test_finds_agents_in_plugin(self, tmp_path: Path) -> None:
        """Agents are discovered from a plugin's agents/ directory."""
        plugin_dir = tmp_path / "cache" / "mkt" / "my-plugin" / "1.0.0"
        agents_dir = plugin_dir / "agents"
        agents_dir.mkdir(parents=True)
        (agents_dir / "security-architect.md").write_text(
            "---\nname: security-architect\n"
            "description: OWASP and threat modelling\n---\n"
        )
        (agents_dir / "compliance-auditor.md").write_text(
            "---\nname: compliance-auditor\n"
            "description: Regulatory compliance checks\n---\n"
        )

        result = team_inventory.discover_plugin_agents(plugin_dir)
        assert len(result) == 2
        names = {a["name"] for a in result}
        assert names == {"security-architect", "compliance-auditor"}

    def test_extracts_description_from_frontmatter(self, tmp_path: Path) -> None:
        plugin_dir = tmp_path / "plugin"
        agents_dir = plugin_dir / "agents"
        agents_dir.mkdir(parents=True)
        (agents_dir / "architect.md").write_text(
            "---\nname: architect\n"
            "description: System architecture design\n---\n\nBody text."
        )

        result = team_inventory.discover_plugin_agents(plugin_dir)
        assert result[0]["description"] == "System architecture design"

    def test_empty_agents_dir(self, tmp_path: Path) -> None:
        plugin_dir = tmp_path / "plugin"
        (plugin_dir / "agents").mkdir(parents=True)
        result = team_inventory.discover_plugin_agents(plugin_dir)
        assert result == []

    def test_no_agents_dir(self, tmp_path: Path) -> None:
        plugin_dir = tmp_path / "plugin"
        plugin_dir.mkdir(parents=True)
        result = team_inventory.discover_plugin_agents(plugin_dir)
        assert result == []


class TestDiscoverPluginSkills:
    def test_finds_skills_in_plugin(self, tmp_path: Path) -> None:
        plugin_dir = tmp_path / "plugin"
        skill_dir = plugin_dir / "skills" / "validate"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\nname: validate\n"
            "description: Run validation pipeline\n---\n"
        )

        result = team_inventory.discover_plugin_skills(plugin_dir)
        assert len(result) == 1
        assert result[0]["name"] == "validate"
        assert result[0]["description"] == "Run validation pipeline"

    def test_skips_dirs_without_skill_md(self, tmp_path: Path) -> None:
        plugin_dir = tmp_path / "plugin"
        (plugin_dir / "skills" / "broken").mkdir(parents=True)
        result = team_inventory.discover_plugin_skills(plugin_dir)
        assert result == []


class TestDiscoverAll:
    def test_full_inventory(self, tmp_path: Path) -> None:
        """discover_all builds a complete inventory from installed_plugins.json."""
        plugin_a = tmp_path / "cache" / "mkt" / "plugin-a" / "1.0.0"
        (plugin_a / "agents").mkdir(parents=True)
        (plugin_a / "agents" / "agent-x.md").write_text(
            "---\nname: agent-x\ndescription: Agent X\n---\n"
        )
        (plugin_a / "skills" / "skill-y").mkdir(parents=True)
        (plugin_a / "skills" / "skill-y" / "SKILL.md").write_text(
            "---\nname: skill-y\ndescription: Skill Y\n---\n"
        )
        (plugin_a / ".claude-plugin").mkdir(parents=True)
        (plugin_a / ".claude-plugin" / "plugin.json").write_text("{}")

        plugin_b = tmp_path / "cache" / "mkt" / "plugin-b" / "2.0.0"
        (plugin_b / "agents").mkdir(parents=True)
        (plugin_b / "agents" / "agent-z.md").write_text(
            "---\nname: agent-z\ndescription: Agent Z\n---\n"
        )
        (plugin_b / ".claude-plugin").mkdir(parents=True)
        (plugin_b / ".claude-plugin" / "plugin.json").write_text("{}")

        installed = {
            "plugin-a@mkt": {"name": "plugin-a", "installPath": str(plugin_a)},
            "plugin-b@mkt": {"name": "plugin-b", "installPath": str(plugin_b)},
        }
        installed_json = tmp_path / "installed_plugins.json"
        installed_json.write_text(json.dumps(installed))

        result = team_inventory.discover_all(installed_json)
        assert "plugin-a" in result
        assert "plugin-b" in result
        assert len(result["plugin-a"]["agents"]) == 1
        assert len(result["plugin-a"]["skills"]) == 1
        assert len(result["plugin-b"]["agents"]) == 1
        assert len(result["plugin-b"]["skills"]) == 0

    def test_missing_plugin_path_skipped(self, tmp_path: Path) -> None:
        """Plugins whose installPath doesn't exist are skipped."""
        installed = {
            "ghost@mkt": {"name": "ghost", "installPath": "/nonexistent/path"},
        }
        installed_json = tmp_path / "installed_plugins.json"
        installed_json.write_text(json.dumps(installed))

        result = team_inventory.discover_all(installed_json)
        assert result == {}


class TestInventoryForTeam:
    def test_available_but_not_included(self, tmp_path: Path) -> None:
        """Reports agents available in a plugin but not in the team manifest."""
        plugin_dir = tmp_path / "cache" / "mkt" / "sec-plugin" / "1.0.0"
        (plugin_dir / "agents").mkdir(parents=True)
        (plugin_dir / "agents" / "architect.md").write_text(
            "---\nname: architect\ndescription: Arch\n---\n"
        )
        (plugin_dir / "agents" / "auditor.md").write_text(
            "---\nname: auditor\ndescription: Audit\n---\n"
        )
        (plugin_dir / "agents" / "privacy.md").write_text(
            "---\nname: privacy\ndescription: Privacy\n---\n"
        )
        (plugin_dir / ".claude-plugin").mkdir(parents=True)
        (plugin_dir / ".claude-plugin" / "plugin.json").write_text("{}")

        installed = {
            "sec-plugin@mkt": {
                "name": "sec-plugin",
                "installPath": str(plugin_dir),
            },
        }
        installed_json = tmp_path / "installed_plugins.json"
        installed_json.write_text(json.dumps(installed))

        team_agents = ["sec-plugin:architect"]

        available = team_inventory.available_but_not_included(
            installed_json=installed_json,
            team_plugins=["sec-plugin"],
            team_agents=team_agents,
        )
        names = {a["qualified"] for a in available["agents"]}
        assert "sec-plugin:auditor" in names
        assert "sec-plugin:privacy" in names
        assert "sec-plugin:architect" not in names
