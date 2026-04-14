#!/usr/bin/env python3
"""Tests for generate_container_installed_json — host-to-container path rewriting."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import plugins_sdlc_workflows_scripts as scripts  # noqa: E402

generate_team_dockerfile = scripts.generate_team_dockerfile


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
