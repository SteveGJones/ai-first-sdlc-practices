#!/usr/bin/env python3
"""Tests for validate_team_manifest — team manifest schema validation."""

import json
import textwrap
from pathlib import Path

import pytest

from sdlc_workflows_scripts import validate_team_manifest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_MANIFEST = textwrap.dedent("""\
    schema_version: "1.0"
    name: full-stack-team
    description: A full-stack development team.
    status: active
    plugins:
      - sdlc-core@ai-first-sdlc
      - sdlc-team-common@ai-first-sdlc
    agents:
      - sdlc-core@ai-first-sdlc:architect
      - sdlc-team-common@ai-first-sdlc:researcher
    skills:
      - sdlc-core@ai-first-sdlc:validate
    context:
      - CLAUDE.md
""")


def make_installed_plugins(
    tmp_path: Path,
    plugins: list[tuple[str, str, str]],
) -> Path:
    """Create a mock installed_plugins.json with real directories.

    Each tuple is (plugin_name, marketplace, version).
    Returns the directory containing installed_plugins.json.
    """
    installed: dict[str, dict[str, str]] = {}
    for name, marketplace, version in plugins:
        plugin_dir = tmp_path / "cache" / marketplace / name / version
        plugin_dir.mkdir(parents=True, exist_ok=True)
        (plugin_dir / ".claude-plugin").mkdir(exist_ok=True)
        (plugin_dir / ".claude-plugin" / "plugin.json").write_text("{}")
        (plugin_dir / "agents").mkdir(exist_ok=True)
        (plugin_dir / "skills").mkdir(exist_ok=True)
        key = f"{name}@{marketplace}"
        installed[key] = {
            "name": name,
            "marketplace": marketplace,
            "version": version,
            "installPath": str(plugin_dir),
        }
    json_path = tmp_path / "installed_plugins.json"
    json_path.write_text(json.dumps(installed))
    return tmp_path


def write_manifest(tmp_path: Path, content: str, filename: str = "team.yaml") -> Path:
    """Write a manifest YAML to tmp_path and return its path."""
    manifest_path = tmp_path / filename
    manifest_path.write_text(content)
    return manifest_path


def setup_valid_env(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Create a fully valid test environment.

    Returns (manifest_path, installed_json, project_root).
    """
    plugins_dir = tmp_path / "plugins"
    make_installed_plugins(
        plugins_dir,
        [
            ("sdlc-core", "ai-first-sdlc", "1.0.0"),
            ("sdlc-team-common", "ai-first-sdlc", "1.0.0"),
        ],
    )
    installed_json = plugins_dir / "installed_plugins.json"

    project_root = tmp_path / "project"
    project_root.mkdir(exist_ok=True)
    (project_root / "CLAUDE.md").write_text("# Gateway")

    manifest_path = write_manifest(project_root, VALID_MANIFEST)
    return manifest_path, installed_json, project_root


# ---------------------------------------------------------------------------
# Valid manifests
# ---------------------------------------------------------------------------


class TestValidManifest:
    """A fully valid manifest should produce zero errors."""

    def test_valid_manifest_returns_empty_list(self, tmp_path: Path) -> None:
        manifest_path, installed_json, project_root = setup_valid_env(tmp_path)
        errors = validate_team_manifest.validate(
            manifest_path, installed_json, project_root
        )
        assert errors == []

    def test_valid_manifest_minimal(self, tmp_path: Path) -> None:
        """Minimal valid manifest: required fields only, no agents/skills/context."""
        plugins_dir = tmp_path / "plugins"
        make_installed_plugins(
            plugins_dir,
            [("sdlc-core", "ai-first-sdlc", "1.0.0")],
        )
        installed_json = plugins_dir / "installed_plugins.json"
        project_root = tmp_path / "project"
        project_root.mkdir()

        content = textwrap.dedent("""\
            schema_version: "1.0"
            name: minimal-team
            status: active
            plugins:
              - sdlc-core@ai-first-sdlc
        """)
        manifest_path = write_manifest(project_root, content)
        errors = validate_team_manifest.validate(
            manifest_path, installed_json, project_root
        )
        assert errors == []


# ---------------------------------------------------------------------------
# Required fields
# ---------------------------------------------------------------------------


class TestRequiredFields:
    """Validation rules 1-2: required fields and schema_version."""

    def test_missing_schema_version(self, tmp_path: Path) -> None:
        manifest_path, installed_json, project_root = setup_valid_env(tmp_path)
        content = VALID_MANIFEST.replace('schema_version: "1.0"\n', "")
        manifest_path.write_text(content)
        errors = validate_team_manifest.validate(
            manifest_path, installed_json, project_root
        )
        assert any("schema_version" in e for e in errors)

    def test_missing_name(self, tmp_path: Path) -> None:
        manifest_path, installed_json, project_root = setup_valid_env(tmp_path)
        content = VALID_MANIFEST.replace("name: full-stack-team\n", "")
        manifest_path.write_text(content)
        errors = validate_team_manifest.validate(
            manifest_path, installed_json, project_root
        )
        assert any("name" in e for e in errors)

    def test_missing_status(self, tmp_path: Path) -> None:
        manifest_path, installed_json, project_root = setup_valid_env(tmp_path)
        content = VALID_MANIFEST.replace("status: active\n", "")
        manifest_path.write_text(content)
        errors = validate_team_manifest.validate(
            manifest_path, installed_json, project_root
        )
        assert any("status" in e for e in errors)

    def test_missing_plugins(self, tmp_path: Path) -> None:
        manifest_path, installed_json, project_root = setup_valid_env(tmp_path)
        # Remove the plugins block entirely
        lines = VALID_MANIFEST.split("\n")
        filtered = [
            line
            for line in lines
            if not line.startswith("plugins:")
            and not (line.startswith("  - ") and "@" in line and ":" not in line)
        ]
        manifest_path.write_text("\n".join(filtered))
        errors = validate_team_manifest.validate(
            manifest_path, installed_json, project_root
        )
        assert any("plugins" in e for e in errors)

    def test_wrong_schema_version(self, tmp_path: Path) -> None:
        manifest_path, installed_json, project_root = setup_valid_env(tmp_path)
        content = VALID_MANIFEST.replace('schema_version: "1.0"', 'schema_version: "2.0"')
        manifest_path.write_text(content)
        errors = validate_team_manifest.validate(
            manifest_path, installed_json, project_root
        )
        assert any("schema_version" in e and "1.0" in e for e in errors)


# ---------------------------------------------------------------------------
# Name validation (Docker tag)
# ---------------------------------------------------------------------------


class TestNameValidation:
    """Validation rule 3: name must be a valid Docker tag component."""

    def test_valid_names(self, tmp_path: Path) -> None:
        valid_names = ["my-team", "team1", "a", "full-stack-dev-2"]
        for name in valid_names:
            manifest_path, installed_json, project_root = setup_valid_env(tmp_path)
            content = VALID_MANIFEST.replace("name: full-stack-team", f"name: {name}")
            manifest_path.write_text(content)
            errors = validate_team_manifest.validate(
                manifest_path, installed_json, project_root
            )
            name_errors = [e for e in errors if "name" in e.lower() and "docker" in e.lower()]
            assert name_errors == [], f"Name {name!r} should be valid but got: {name_errors}"

    def test_uppercase_rejected(self, tmp_path: Path) -> None:
        manifest_path, installed_json, project_root = setup_valid_env(tmp_path)
        content = VALID_MANIFEST.replace("name: full-stack-team", "name: UpperCase")
        manifest_path.write_text(content)
        errors = validate_team_manifest.validate(
            manifest_path, installed_json, project_root
        )
        assert any("name" in e.lower() for e in errors)

    def test_spaces_rejected(self, tmp_path: Path) -> None:
        manifest_path, installed_json, project_root = setup_valid_env(tmp_path)
        content = VALID_MANIFEST.replace("name: full-stack-team", "name: has spaces")
        manifest_path.write_text(content)
        errors = validate_team_manifest.validate(
            manifest_path, installed_json, project_root
        )
        assert any("name" in e.lower() for e in errors)

    def test_empty_name_rejected(self, tmp_path: Path) -> None:
        manifest_path, installed_json, project_root = setup_valid_env(tmp_path)
        content = VALID_MANIFEST.replace("name: full-stack-team", 'name: ""')
        manifest_path.write_text(content)
        errors = validate_team_manifest.validate(
            manifest_path, installed_json, project_root
        )
        assert any("name" in e.lower() for e in errors)


# ---------------------------------------------------------------------------
# Status validation
# ---------------------------------------------------------------------------


class TestStatusValidation:
    """Validation rule 4: status must be one of the allowed values."""

    @pytest.mark.parametrize(
        "status",
        ["active", "ephemeral", "inactive", "decommissioned"],
    )
    def test_valid_statuses(self, tmp_path: Path, status: str) -> None:
        manifest_path, installed_json, project_root = setup_valid_env(tmp_path)
        content = VALID_MANIFEST.replace("status: active", f"status: {status}")
        manifest_path.write_text(content)
        errors = validate_team_manifest.validate(
            manifest_path, installed_json, project_root
        )
        status_errors = [e for e in errors if "status" in e.lower()]
        assert status_errors == [], f"Status {status!r} should be valid"

    def test_invalid_status(self, tmp_path: Path) -> None:
        manifest_path, installed_json, project_root = setup_valid_env(tmp_path)
        content = VALID_MANIFEST.replace("status: active", "status: paused")
        manifest_path.write_text(content)
        errors = validate_team_manifest.validate(
            manifest_path, installed_json, project_root
        )
        assert any("status" in e.lower() for e in errors)


# ---------------------------------------------------------------------------
# Plugin resolution
# ---------------------------------------------------------------------------


class TestPluginResolution:
    """Validation rule 5: every plugin must resolve via installed_plugins.json."""

    def test_uninstalled_plugin_detected(self, tmp_path: Path) -> None:
        plugins_dir = tmp_path / "plugins"
        make_installed_plugins(
            plugins_dir,
            [("sdlc-core", "ai-first-sdlc", "1.0.0")],
        )
        installed_json = plugins_dir / "installed_plugins.json"
        project_root = tmp_path / "project"
        project_root.mkdir()
        (project_root / "CLAUDE.md").write_text("# Gateway")

        content = textwrap.dedent("""\
            schema_version: "1.0"
            name: test-team
            status: active
            plugins:
              - sdlc-core@ai-first-sdlc
              - nonexistent@marketplace
        """)
        manifest_path = write_manifest(project_root, content)
        errors = validate_team_manifest.validate(
            manifest_path, installed_json, project_root
        )
        assert any("nonexistent@marketplace" in e for e in errors)


# ---------------------------------------------------------------------------
# Agent / skill orphan detection
# ---------------------------------------------------------------------------


class TestOrphanDetection:
    """Validation rule 6: non-local agents/skills must reference a listed plugin."""

    def test_agent_referencing_unlisted_plugin(self, tmp_path: Path) -> None:
        manifest_path, installed_json, project_root = setup_valid_env(tmp_path)
        content = textwrap.dedent("""\
            schema_version: "1.0"
            name: test-team
            status: active
            plugins:
              - sdlc-core@ai-first-sdlc
            agents:
              - sdlc-team-common@ai-first-sdlc:researcher
        """)
        manifest_path.write_text(content)
        errors = validate_team_manifest.validate(
            manifest_path, installed_json, project_root
        )
        assert any("sdlc-team-common@ai-first-sdlc" in e and "orphan" in e.lower() for e in errors)

    def test_skill_referencing_unlisted_plugin(self, tmp_path: Path) -> None:
        manifest_path, installed_json, project_root = setup_valid_env(tmp_path)
        content = textwrap.dedent("""\
            schema_version: "1.0"
            name: test-team
            status: active
            plugins:
              - sdlc-core@ai-first-sdlc
            skills:
              - sdlc-team-common@ai-first-sdlc:deploy
        """)
        manifest_path.write_text(content)
        errors = validate_team_manifest.validate(
            manifest_path, installed_json, project_root
        )
        assert any("sdlc-team-common@ai-first-sdlc" in e and "orphan" in e.lower() for e in errors)

    def test_local_agent_not_flagged_as_orphan(self, tmp_path: Path) -> None:
        manifest_path, installed_json, project_root = setup_valid_env(tmp_path)
        local_agent = project_root / "agents" / "custom.md"
        local_agent.parent.mkdir(parents=True)
        local_agent.write_text("# Custom agent")
        content = textwrap.dedent("""\
            schema_version: "1.0"
            name: test-team
            status: active
            plugins:
              - sdlc-core@ai-first-sdlc
            agents:
              - local:agents/custom.md
        """)
        manifest_path.write_text(content)
        errors = validate_team_manifest.validate(
            manifest_path, installed_json, project_root
        )
        orphan_errors = [e for e in errors if "orphan" in e.lower()]
        assert orphan_errors == []


# ---------------------------------------------------------------------------
# Local path resolution
# ---------------------------------------------------------------------------


class TestLocalPaths:
    """Validation rule 7: local: paths must resolve to existing files."""

    def test_local_agent_file_missing(self, tmp_path: Path) -> None:
        manifest_path, installed_json, project_root = setup_valid_env(tmp_path)
        content = textwrap.dedent("""\
            schema_version: "1.0"
            name: test-team
            status: active
            plugins:
              - sdlc-core@ai-first-sdlc
            agents:
              - local:agents/missing.md
        """)
        manifest_path.write_text(content)
        errors = validate_team_manifest.validate(
            manifest_path, installed_json, project_root
        )
        assert any("missing.md" in e for e in errors)

    def test_local_skill_file_missing(self, tmp_path: Path) -> None:
        manifest_path, installed_json, project_root = setup_valid_env(tmp_path)
        content = textwrap.dedent("""\
            schema_version: "1.0"
            name: test-team
            status: active
            plugins:
              - sdlc-core@ai-first-sdlc
            skills:
              - local:skills/missing.md
        """)
        manifest_path.write_text(content)
        errors = validate_team_manifest.validate(
            manifest_path, installed_json, project_root
        )
        assert any("missing.md" in e for e in errors)

    def test_local_agent_file_exists(self, tmp_path: Path) -> None:
        manifest_path, installed_json, project_root = setup_valid_env(tmp_path)
        local_agent = project_root / "agents" / "custom.md"
        local_agent.parent.mkdir(parents=True)
        local_agent.write_text("# Custom agent")
        content = textwrap.dedent("""\
            schema_version: "1.0"
            name: test-team
            status: active
            plugins:
              - sdlc-core@ai-first-sdlc
            agents:
              - local:agents/custom.md
        """)
        manifest_path.write_text(content)
        errors = validate_team_manifest.validate(
            manifest_path, installed_json, project_root
        )
        local_errors = [e for e in errors if "local" in e.lower() and "custom" in e]
        assert local_errors == []

    def test_local_agent_path_traversal_rejected(self, tmp_path: Path) -> None:
        """CR-M-1: ``local: ../../etc/passwd`` must be rejected."""
        manifest_path, installed_json, project_root = setup_valid_env(tmp_path)
        content = textwrap.dedent("""\
            schema_version: "1.0"
            name: test-team
            status: active
            plugins:
              - sdlc-core@ai-first-sdlc
            agents:
              - local:../../etc/passwd
        """)
        manifest_path.write_text(content)
        errors = validate_team_manifest.validate(
            manifest_path, installed_json, project_root
        )
        assert any(
            "escapes project root" in e for e in errors
        ), f"Expected path-traversal rejection, got: {errors}"

    def test_local_skill_path_traversal_rejected(self, tmp_path: Path) -> None:
        """CR-M-1: path traversal also rejected for skills."""
        manifest_path, installed_json, project_root = setup_valid_env(tmp_path)
        content = textwrap.dedent("""\
            schema_version: "1.0"
            name: test-team
            status: active
            plugins:
              - sdlc-core@ai-first-sdlc
            skills:
              - local:../secrets/private
        """)
        manifest_path.write_text(content)
        errors = validate_team_manifest.validate(
            manifest_path, installed_json, project_root
        )
        assert any("escapes project root" in e for e in errors)

    def test_context_path_traversal_rejected(self, tmp_path: Path) -> None:
        """CR-M-1: context files also validated for traversal."""
        manifest_path, installed_json, project_root = setup_valid_env(tmp_path)
        content = textwrap.dedent("""\
            schema_version: "1.0"
            name: test-team
            status: active
            plugins:
              - sdlc-core@ai-first-sdlc
            context:
              - ../../../../etc/shadow
        """)
        manifest_path.write_text(content)
        errors = validate_team_manifest.validate(
            manifest_path, installed_json, project_root
        )
        assert any("escapes project root" in e for e in errors)


# ---------------------------------------------------------------------------
# Context file existence
# ---------------------------------------------------------------------------


class TestContextFiles:
    """Validation rule 8: every context file must exist in the project root."""

    def test_context_file_missing(self, tmp_path: Path) -> None:
        manifest_path, installed_json, project_root = setup_valid_env(tmp_path)
        content = textwrap.dedent("""\
            schema_version: "1.0"
            name: test-team
            status: active
            plugins:
              - sdlc-core@ai-first-sdlc
            context:
              - NONEXISTENT.md
        """)
        manifest_path.write_text(content)
        errors = validate_team_manifest.validate(
            manifest_path, installed_json, project_root
        )
        assert any("NONEXISTENT.md" in e for e in errors)

    def test_context_file_exists(self, tmp_path: Path) -> None:
        manifest_path, installed_json, project_root = setup_valid_env(tmp_path)
        (project_root / "CLAUDE.md").write_text("# Gateway")
        content = textwrap.dedent("""\
            schema_version: "1.0"
            name: test-team
            status: active
            plugins:
              - sdlc-core@ai-first-sdlc
            context:
              - CLAUDE.md
        """)
        manifest_path.write_text(content)
        errors = validate_team_manifest.validate(
            manifest_path, installed_json, project_root
        )
        context_errors = [e for e in errors if "context" in e.lower() and "CLAUDE.md" in e]
        assert context_errors == []


# ---------------------------------------------------------------------------
# Reserved forward-compat fields (SA-M-4)
# ---------------------------------------------------------------------------


class TestReservedFields:
    """The ``group:`` field is reserved for future use: accepted, no runtime effect."""

    def test_group_string_accepted_without_error(self, tmp_path: Path) -> None:
        manifest_path, installed_json, project_root = setup_valid_env(tmp_path)
        content = textwrap.dedent("""\
            schema_version: "1.0"
            name: test-team
            status: active
            plugins:
              - sdlc-core@ai-first-sdlc
            group: platform-engineering
        """)
        manifest_path.write_text(content)
        errors = validate_team_manifest.validate(
            manifest_path, installed_json, project_root
        )
        assert errors == []

    def test_group_empty_string_rejected(self, tmp_path: Path) -> None:
        manifest_path, installed_json, project_root = setup_valid_env(tmp_path)
        content = textwrap.dedent("""\
            schema_version: "1.0"
            name: test-team
            status: active
            plugins:
              - sdlc-core@ai-first-sdlc
            group: "   "
        """)
        manifest_path.write_text(content)
        errors = validate_team_manifest.validate(
            manifest_path, installed_json, project_root
        )
        assert any("group" in e.lower() for e in errors)

    def test_group_non_string_rejected(self, tmp_path: Path) -> None:
        manifest_path, installed_json, project_root = setup_valid_env(tmp_path)
        content = textwrap.dedent("""\
            schema_version: "1.0"
            name: test-team
            status: active
            plugins:
              - sdlc-core@ai-first-sdlc
            group: 42
        """)
        manifest_path.write_text(content)
        errors = validate_team_manifest.validate(
            manifest_path, installed_json, project_root
        )
        assert any("group" in e.lower() for e in errors)


# ---------------------------------------------------------------------------
# Return type
# ---------------------------------------------------------------------------


class TestReturnType:
    """validate() must return a list of strings."""

    def test_returns_list(self, tmp_path: Path) -> None:
        manifest_path, installed_json, project_root = setup_valid_env(tmp_path)
        result = validate_team_manifest.validate(
            manifest_path, installed_json, project_root
        )
        assert isinstance(result, list)

    def test_error_items_are_strings(self, tmp_path: Path) -> None:
        manifest_path, installed_json, project_root = setup_valid_env(tmp_path)
        # Force errors
        content = VALID_MANIFEST.replace('schema_version: "1.0"', 'schema_version: "9.9"')
        manifest_path.write_text(content)
        result = validate_team_manifest.validate(
            manifest_path, installed_json, project_root
        )
        assert len(result) > 0
        for item in result:
            assert isinstance(item, str)


# ---------------------------------------------------------------------------
# YAML parsing edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Edge cases for manifest parsing."""

    def test_invalid_yaml(self, tmp_path: Path) -> None:
        manifest_path, installed_json, project_root = setup_valid_env(tmp_path)
        manifest_path.write_text("{{invalid yaml::")
        errors = validate_team_manifest.validate(
            manifest_path, installed_json, project_root
        )
        assert len(errors) > 0
        assert any("yaml" in e.lower() or "parse" in e.lower() for e in errors)

    def test_empty_file(self, tmp_path: Path) -> None:
        manifest_path, installed_json, project_root = setup_valid_env(tmp_path)
        manifest_path.write_text("")
        errors = validate_team_manifest.validate(
            manifest_path, installed_json, project_root
        )
        assert len(errors) > 0

    def test_plugins_not_a_list(self, tmp_path: Path) -> None:
        manifest_path, installed_json, project_root = setup_valid_env(tmp_path)
        content = textwrap.dedent("""\
            schema_version: "1.0"
            name: test-team
            status: active
            plugins: not-a-list
        """)
        manifest_path.write_text(content)
        errors = validate_team_manifest.validate(
            manifest_path, installed_json, project_root
        )
        assert any("plugins" in e.lower() and "list" in e.lower() for e in errors)
