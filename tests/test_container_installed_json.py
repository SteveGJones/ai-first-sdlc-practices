#!/usr/bin/env python3
"""Tests for generate_container_installed_json — host-to-container path rewriting."""

import json
from pathlib import Path

from sdlc_workflows_scripts import generate_team_dockerfile


class TestContainerInstalledJson:
    def test_rewrites_v2_paths(self, tmp_path: Path) -> None:
        """V2 format installPath values are rewritten to container paths."""
        host_json = tmp_path / "installed_plugins.json"
        host_json.write_text(json.dumps({
            "version": 2,
            "plugins": {
                "sdlc-core@ai-first-sdlc": [
                    {
                        "scope": "global",
                        "installPath": "/Users/alice/.claude/plugins/cache/ai-first-sdlc/sdlc-core/1.0.0",
                        "version": "1.0.0",
                    }
                ],
            },
        }))
        plugins_root = Path("/Users/alice/.claude/plugins")
        output = tmp_path / "rewritten.json"

        generate_team_dockerfile.generate_container_installed_json(
            host_json, plugins_root, output,
        )

        result = json.loads(output.read_text())
        path = result["plugins"]["sdlc-core@ai-first-sdlc"][0]["installPath"]
        assert path == "/home/sdlc/.claude/plugins/cache/ai-first-sdlc/sdlc-core/1.0.0"

    def test_rewrites_v1_paths(self, tmp_path: Path) -> None:
        """V1 (flat) format installPath values are rewritten."""
        host_json = tmp_path / "installed_plugins.json"
        host_json.write_text(json.dumps({
            "sdlc-core@mkt": {
                "name": "sdlc-core",
                "installPath": "/Users/bob/.claude/plugins/cache/mkt/sdlc-core/2.0.0",
            },
        }))
        plugins_root = Path("/Users/bob/.claude/plugins")
        output = tmp_path / "rewritten.json"

        generate_team_dockerfile.generate_container_installed_json(
            host_json, plugins_root, output,
        )

        result = json.loads(output.read_text())
        path = result["sdlc-core@mkt"]["installPath"]
        assert path == "/home/sdlc/.claude/plugins/cache/mkt/sdlc-core/2.0.0"

    def test_preserves_other_fields(self, tmp_path: Path) -> None:
        """Non-path fields are preserved unchanged."""
        host_json = tmp_path / "installed_plugins.json"
        host_json.write_text(json.dumps({
            "version": 2,
            "plugins": {
                "my-plugin@mkt": [
                    {
                        "scope": "global",
                        "installPath": "/Users/carol/.claude/plugins/cache/mkt/my-plugin/1.0.0",
                        "version": "1.0.0",
                        "installedAt": "2026-04-10",
                    }
                ],
            },
        }))
        plugins_root = Path("/Users/carol/.claude/plugins")
        output = tmp_path / "rewritten.json"

        generate_team_dockerfile.generate_container_installed_json(
            host_json, plugins_root, output,
        )

        result = json.loads(output.read_text())
        entry = result["plugins"]["my-plugin@mkt"][0]
        assert entry["scope"] == "global"
        assert entry["version"] == "1.0.0"
        assert entry["installedAt"] == "2026-04-10"


class TestDockerfileHardening:
    """Asserts that the generated Dockerfile contains required security
    hardening directives (S-I-2 / Phase 2 recommendation #2 extended).

    Covers the static surface.  A matching runtime smoke test (a
    ``touch`` attempt against the locked directories) lives under
    ``tests/integration/workforce-smoke/`` — covered in Session 5.
    """

    def _write_minimal_manifest(self, tmp_path: Path) -> tuple[Path, Path, Path]:
        manifest = tmp_path / "manifest.yaml"
        manifest.write_text(
            "schema_version: '1.0'\n"
            "name: test-team\n"
            "description: test\n"
            "status: active\n"
            "plugins: []\n"
            "agents: []\n"
            "skills: []\n"
            "context: []\n"
        )
        installed = tmp_path / "installed_plugins.json"
        installed.write_text('{"version": 2, "plugins": {}}')
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("# Test team\n")
        return manifest, installed, claude_md

    def test_dockerfile_locks_plugins_dir(self, tmp_path: Path) -> None:
        manifest, installed, claude_md = self._write_minimal_manifest(tmp_path)
        output = tmp_path / "Dockerfile.team"
        content = generate_team_dockerfile.generate(
            manifest_path=manifest,
            installed_json=installed,
            team_claude_md_path=claude_md,
            output_path=output,
        )
        assert "chmod -R a-w /home/sdlc/.claude/plugins/" in content

    def test_dockerfile_locks_user_agents_dir(self, tmp_path: Path) -> None:
        """S-I-2: ~/.claude/agents must be write-locked so a runtime
        prompt cannot drop a new agent definition."""
        manifest, installed, claude_md = self._write_minimal_manifest(tmp_path)
        output = tmp_path / "Dockerfile.team"
        content = generate_team_dockerfile.generate(
            manifest_path=manifest,
            installed_json=installed,
            team_claude_md_path=claude_md,
            output_path=output,
        )
        assert "/home/sdlc/.claude/agents" in content
        assert "chmod -R a-w" in content
        # Ensure the agents directory is covered by a chmod -R a-w
        # (appears in a chmod line, not just a mkdir line).
        chmod_lines = [
            line for line in content.splitlines()
            if "chmod -R a-w" in line and "/home/sdlc/.claude/agents" in line
        ]
        assert chmod_lines, "No chmod -R a-w covering /home/sdlc/.claude/agents"

    def test_dockerfile_locks_user_skills_dir(self, tmp_path: Path) -> None:
        """S-I-2: ~/.claude/skills must be write-locked likewise."""
        manifest, installed, claude_md = self._write_minimal_manifest(tmp_path)
        output = tmp_path / "Dockerfile.team"
        content = generate_team_dockerfile.generate(
            manifest_path=manifest,
            installed_json=installed,
            team_claude_md_path=claude_md,
            output_path=output,
        )
        chmod_lines = [
            line for line in content.splitlines()
            if "chmod -R a-w" in line and "/home/sdlc/.claude/skills" in line
        ]
        assert chmod_lines, "No chmod -R a-w covering /home/sdlc/.claude/skills"
