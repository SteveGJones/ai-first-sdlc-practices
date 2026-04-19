#!/usr/bin/env python3
"""Resolve Claude Code credentials for containerised workflow runs.

Three-tier fallback:
  1. macOS Keychain (zero-config)
  2. Docker volume (sdlc-claude-credentials)
  3. Explicit config (.archon/credentials.yaml)

Public API
----------
resolve(work_dir, project_dir) -> dict
    Returns {"tier": str, "mount_args": str|None, "message": str}
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import time
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

KEYCHAIN_SERVICE = "Claude Code-credentials"
CREDENTIAL_VOLUME = "sdlc-claude-credentials"
CONFIG_FILE = ".archon/credentials.yaml"
CONTAINER_CRED_PATH = "/home/sdlc/.claude-creds/.credentials.json"

# S-M-6 / AC-I-8: emit a specific warning when Claude Code credentials
# are within this many seconds of expiring, so workflow runs that are
# about to take longer than the token lifetime can log in first rather
# than see a generic "authentication_error" partway through.
CREDENTIAL_EXPIRY_WARNING_SECONDS = 300  # five minutes


def _check_credential_freshness(cred_payload: dict) -> tuple[bool, str | None]:
    """Inspect a parsed credentials JSON payload for freshness.

    Returns ``(is_valid, diagnostic)`` where ``is_valid`` is False when
    the token is already expired, and ``diagnostic`` is a specific
    human-readable message (or None when the token is comfortably
    fresh).  The field path mirrors Claude Code's OAuth structure:
    ``claudeAiOauth.expiresAt`` (milliseconds since epoch).
    """
    oauth = cred_payload.get("claudeAiOauth")
    if not isinstance(oauth, dict):
        return True, None
    expires_at_ms = oauth.get("expiresAt")
    if not isinstance(expires_at_ms, (int, float)):
        return True, None
    expires_at_s = expires_at_ms / 1000.0
    remaining = expires_at_s - time.time()
    if remaining <= 0:
        return False, (
            "Claude Code credentials have expired. "
            "Run `claude /login` to refresh before starting a workflow."
        )
    if remaining < CREDENTIAL_EXPIRY_WARNING_SECONDS:
        return True, (
            f"Claude Code credentials expire in {int(remaining)}s. "
            "Run `claude /login` now if this workflow is long-running."
        )
    return True, None


def _try_keychain(work_dir: Path) -> dict | None:
    """Tier 1: Extract credentials from macOS Keychain."""
    logger.debug("Credential resolver: trying keychain tier")
    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            logger.debug("Keychain lookup returned non-zero; tier skipped")
            return None

        cred_json = result.stdout.strip()
        if not cred_json:
            return None

        parsed = json.loads(cred_json)
        if "claudeAiOauth" not in parsed:
            return None

        is_fresh, freshness_msg = _check_credential_freshness(parsed)
        if not is_fresh:
            # Expired token: surface a specific diagnostic and refuse
            # to hand back a mount.  The caller will see tier="stale"
            # and can show the message instead of a generic auth error
            # deep in the container.
            logger.warning(
                "Keychain credentials expired — refusing to use",
                extra={"tier": "keychain"},
            )
            return {
                "tier": "stale",
                "mount_args": None,
                "message": freshness_msg or "Credentials expired.",
                "cleanup": None,
            }

        temp_file = work_dir / ".sdlc-cred-temp.json"
        temp_file.write_text(cred_json)
        os.chmod(temp_file, 0o600)

        log_extra = {"tier": "keychain", "has_mount": True}
        if freshness_msg:
            log_extra["expiry_warning"] = freshness_msg
            logger.warning(
                "Keychain credentials near expiry",
                extra={"tier": "keychain"},
            )
        logger.info("Credential tier selected", extra=log_extra)
        return {
            "tier": "keychain",
            "mount_args": f"{temp_file}:{CONTAINER_CRED_PATH}:ro",
            "message": "Credentials from macOS Keychain"
            + (f" (WARNING: {freshness_msg})" if freshness_msg else ""),
            "cleanup": str(temp_file),
        }
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(
            "Keychain tier unavailable",
            extra={"error": type(e).__name__},
        )
        return None


def _try_volume() -> dict | None:
    """Tier 2: Check for Docker credential volume."""
    logger.debug("Credential resolver: trying docker-volume tier")
    try:
        result = subprocess.run(
            ["docker", "volume", "inspect", CREDENTIAL_VOLUME],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return None

        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "-v", f"{CREDENTIAL_VOLUME}:/data:ro",
                "--entrypoint", "test",
                "alpine", "-f", "/data/.credentials.json",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return None

        logger.info(
            "Credential tier selected",
            extra={"tier": "volume", "volume_name": CREDENTIAL_VOLUME},
        )
        return {
            "tier": "volume",
            "mount_args": f"{CREDENTIAL_VOLUME}:/home/sdlc/.claude-creds:ro",
            "message": f"Credentials from Docker volume: {CREDENTIAL_VOLUME}",
            "cleanup": None,
        }
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.warning(
            "Docker-volume tier unavailable",
            extra={"error": type(e).__name__},
        )
        return None


def _try_config(project_dir: Path) -> dict | None:
    """Tier 3: Check for .archon/credentials.yaml config."""
    logger.debug("Credential resolver: trying config tier")
    config_path = project_dir / CONFIG_FILE
    if not config_path.exists():
        return None

    try:
        with config_path.open() as fh:
            config = yaml.safe_load(fh)

        cred_path = config.get("credential_path")
        if not cred_path:
            return None

        cred_file = Path(cred_path)
        if not cred_file.exists():
            logger.warning(
                "Config tier credential_path missing on disk",
                extra={"config_path": str(config_path)},
            )
            return None

        logger.info(
            "Credential tier selected",
            extra={"tier": "config", "config_path": str(config_path)},
        )
        return {
            "tier": "config",
            "mount_args": f"{cred_file}:{CONTAINER_CRED_PATH}:ro",
            "message": f"Credentials from config: {cred_path}",
            "cleanup": None,
        }
    except (yaml.YAMLError, OSError) as e:
        logger.error(
            "Config tier read failed",
            extra={"config_path": str(config_path), "error": type(e).__name__},
            exc_info=True,
        )
        return None


def resolve(
    work_dir: Path,
    project_dir: Path,
) -> dict:
    """Resolve credentials using the three-tier fallback."""
    logger.info(
        "Credential resolve start",
        extra={"project_dir": str(project_dir)},
    )
    result = _try_keychain(work_dir)
    if result:
        return result

    result = _try_volume()
    if result:
        return result

    result = _try_config(project_dir)
    if result:
        return result

    logger.warning("Credential resolve exhausted all tiers; no credentials available")
    return {
        "tier": "none",
        "mount_args": None,
        "message": (
            "No credentials found. Options:\n"
            "  1. Log in to Claude Code on this Mac (uses Keychain automatically)\n"
            "  2. Run login.sh to create a Docker credential volume\n"
            "  3. Create .archon/credentials.yaml with credential_path"
        ),
        "cleanup": None,
    }


def main() -> None:
    """CLI entry point — report which credential tier is active."""
    import argparse
    import json as json_mod
    import tempfile

    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    logger.info("resolve_credentials CLI start")

    parser = argparse.ArgumentParser(description="Resolve Claude Code credentials")
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    work_dir = Path(tempfile.mkdtemp(prefix="sdlc-cred-"))
    result = resolve(work_dir, args.project_dir)

    if args.json:
        # When outputting JSON, do NOT clean up temp files — the caller
        # needs the credential file to still exist for docker volume mounts.
        # The caller is responsible for cleanup (the path is in result["cleanup"]).
        print(json_mod.dumps(result, indent=2))
    else:
        print(f"Tier: {result['tier']}")
        print(f"  {result['message']}")
        # Clean up temp files for interactive usage
        cleanup_path = result.get("cleanup")
        if cleanup_path:
            Path(cleanup_path).unlink(missing_ok=True)
        try:
            work_dir.rmdir()
        except OSError:
            pass


if __name__ == "__main__":
    main()
