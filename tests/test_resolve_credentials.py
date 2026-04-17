#!/usr/bin/env python3
"""Tests for resolve_credentials — three-tier credential fallback."""

import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import plugins_sdlc_workflows_scripts as scripts  # noqa: E402

resolve_credentials = scripts.resolve_credentials


class TestKeychainTier:
    def test_extracts_from_keychain_on_macos(self, tmp_path: Path) -> None:
        """Tier 1: macOS Keychain extraction succeeds."""
        cred_json = json.dumps({"claudeAiOauth": {"accessToken": "test"}})
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout=cred_json, stderr=""
            )
            result = resolve_credentials.resolve(
                work_dir=tmp_path,
                project_dir=tmp_path,
            )
        assert result["tier"] == "keychain"
        assert result["mount_args"] is not None
        assert ".credentials.json" in result["mount_args"]

    def test_keychain_fails_gracefully(self, tmp_path: Path) -> None:
        """Tier 1: Keychain fails → falls through to next tier."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=44, stdout="", stderr="not found"
            )
            result = resolve_credentials.resolve(
                work_dir=tmp_path,
                project_dir=tmp_path,
            )
        assert result["tier"] != "keychain"


class TestVolumeTier:
    def test_volume_found(self, tmp_path: Path) -> None:
        """Tier 2: Docker volume exists and has credentials."""
        with patch("subprocess.run") as mock_run:
            def side_effect(*args, **kwargs):
                cmd = args[0] if args else kwargs.get("args", [])
                if "security" in cmd:
                    return MagicMock(returncode=44, stdout="", stderr="")
                if "docker" in cmd and "inspect" in cmd:
                    return MagicMock(returncode=0, stdout="[]", stderr="")
                if "docker" in cmd and "run" in cmd:
                    return MagicMock(returncode=0, stdout="exists", stderr="")
                return MagicMock(returncode=1, stdout="", stderr="")
            mock_run.side_effect = side_effect
            result = resolve_credentials.resolve(
                work_dir=tmp_path,
                project_dir=tmp_path,
            )
        assert result["tier"] == "volume"

    def test_volume_missing(self, tmp_path: Path) -> None:
        """Tier 2: Volume doesn't exist → falls through."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout="", stderr="not found"
            )
            result = resolve_credentials.resolve(
                work_dir=tmp_path,
                project_dir=tmp_path,
            )
        assert result["tier"] != "volume"


class TestConfigTier:
    def test_config_file_found(self, tmp_path: Path) -> None:
        """Tier 3: .archon/credentials.yaml exists with valid path."""
        cred_file = tmp_path / "my-creds.json"
        cred_file.write_text('{"claudeAiOauth": {}}')
        config_dir = tmp_path / ".archon"
        config_dir.mkdir()
        (config_dir / "credentials.yaml").write_text(
            f"credential_path: {cred_file}\n"
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout="", stderr=""
            )
            result = resolve_credentials.resolve(
                work_dir=tmp_path,
                project_dir=tmp_path,
            )
        assert result["tier"] == "config"
        assert str(cred_file) in result["mount_args"]

    def test_config_missing_file(self, tmp_path: Path) -> None:
        """Tier 3: Config references nonexistent file → tier=none."""
        config_dir = tmp_path / ".archon"
        config_dir.mkdir()
        (config_dir / "credentials.yaml").write_text(
            "credential_path: /nonexistent/path.json\n"
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout="", stderr=""
            )
            result = resolve_credentials.resolve(
                work_dir=tmp_path,
                project_dir=tmp_path,
            )
        assert result["tier"] == "none"


class TestNoneTier:
    def test_all_tiers_fail(self, tmp_path: Path) -> None:
        """All tiers fail → tier=none with instructions."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout="", stderr=""
            )
            result = resolve_credentials.resolve(
                work_dir=tmp_path,
                project_dir=tmp_path,
            )
        assert result["tier"] == "none"
        assert result["mount_args"] is None
        assert "message" in result
