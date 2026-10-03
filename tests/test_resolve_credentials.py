#!/usr/bin/env python3
"""Tests for resolve_credentials — three-tier credential fallback."""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from sdlc_workflows_scripts import resolve_credentials

pytestmark = pytest.mark.credentials


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


class TestCleanupContract:
    """The SKILL.md cleanup trap relies on a stable cleanup-field contract.

    - Keychain tier creates a temp credential file and MUST return its path
      so the caller can delete it (also verified by the ``rm -f`` in the trap).
    - Volume and config tiers MUST return cleanup=None: the caller's trap
      calls ``rm -f`` which must be a no-op for these tiers.
    - tier=none MUST return cleanup=None.
    """

    def test_keychain_returns_cleanup_path_to_existing_file(
        self, tmp_path: Path
    ) -> None:
        """Keychain tier: cleanup points to the temp file that actually exists."""
        cred_json = json.dumps({"claudeAiOauth": {"accessToken": "t"}})
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout=cred_json, stderr=""
            )
            result = resolve_credentials.resolve(
                work_dir=tmp_path,
                project_dir=tmp_path,
            )
        assert result["tier"] == "keychain"
        cleanup = result["cleanup"]
        assert cleanup is not None
        assert Path(cleanup).exists(), (
            "Keychain tier's cleanup path must point to an existing file "
            "so the SKILL.md trap's rm -f has something to remove."
        )

    def test_config_tier_cleanup_is_none(self, tmp_path: Path) -> None:
        """Config tier: caller supplies the file → no cleanup owned by us."""
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
        assert result["cleanup"] is None

    def test_none_tier_cleanup_is_none(self, tmp_path: Path) -> None:
        """tier=none: nothing to clean up."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout="", stderr=""
            )
            result = resolve_credentials.resolve(
                work_dir=tmp_path,
                project_dir=tmp_path,
            )
        assert result["tier"] == "none"
        assert result["cleanup"] is None

    def test_cleanup_removes_keychain_temp_file(self, tmp_path: Path) -> None:
        """Caller using result['cleanup'] can safely delete the temp file.

        Simulates what the SKILL.md trap does: Path(cleanup).unlink.
        """
        cred_json = json.dumps({"claudeAiOauth": {"accessToken": "t"}})
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout=cred_json, stderr=""
            )
            result = resolve_credentials.resolve(
                work_dir=tmp_path,
                project_dir=tmp_path,
            )
        cleanup_path = Path(result["cleanup"])
        assert cleanup_path.exists()
        cleanup_path.unlink(missing_ok=True)
        assert not cleanup_path.exists(), (
            "After cleanup, the temp file must be gone — this is the "
            "contract the SKILL.md trap depends on."
        )


class TestCredentialFreshness:
    """S-M-6 / AC-I-8: surface a specific message for stale tokens.

    The keychain tier should refuse to hand back already-expired
    credentials (tier=stale) rather than letting the container fail
    with a generic authentication_error.  Near-expiry tokens produce a
    warning in the message but remain usable.
    """

    def test_expired_token_returns_stale_tier(self, tmp_path: Path) -> None:
        import time as _time
        past_ms = int((_time.time() - 3600) * 1000)  # expired 1 hour ago
        cred_json = json.dumps(
            {"claudeAiOauth": {"accessToken": "t", "expiresAt": past_ms}}
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout=cred_json, stderr=""
            )
            result = resolve_credentials.resolve(
                work_dir=tmp_path,
                project_dir=tmp_path,
            )
        assert result["tier"] == "stale"
        assert result["mount_args"] is None
        assert "expired" in result["message"].lower()
        assert "claude /login" in result["message"].lower()

    def test_near_expiry_token_carries_warning(self, tmp_path: Path) -> None:
        import time as _time
        soon_ms = int((_time.time() + 60) * 1000)  # 60 seconds remaining
        cred_json = json.dumps(
            {"claudeAiOauth": {"accessToken": "t", "expiresAt": soon_ms}}
        )
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
        assert "WARNING" in result["message"]
        assert "expire" in result["message"].lower()

    def test_fresh_token_no_warning(self, tmp_path: Path) -> None:
        import time as _time
        far_ms = int((_time.time() + 7200) * 1000)  # 2 hours remaining
        cred_json = json.dumps(
            {"claudeAiOauth": {"accessToken": "t", "expiresAt": far_ms}}
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout=cred_json, stderr=""
            )
            result = resolve_credentials.resolve(
                work_dir=tmp_path,
                project_dir=tmp_path,
            )
        assert result["tier"] == "keychain"
        assert "WARNING" not in result["message"]

    def test_missing_expiresat_still_works(self, tmp_path: Path) -> None:
        """Older credential files without expiresAt must still resolve."""
        cred_json = json.dumps({"claudeAiOauth": {"accessToken": "t"}})
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout=cred_json, stderr=""
            )
            result = resolve_credentials.resolve(
                work_dir=tmp_path,
                project_dir=tmp_path,
            )
        assert result["tier"] == "keychain"
