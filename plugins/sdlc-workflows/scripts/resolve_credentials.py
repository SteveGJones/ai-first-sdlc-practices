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
import os
import subprocess
import tempfile
from pathlib import Path

import yaml

KEYCHAIN_SERVICE = "Claude Code-credentials"
CREDENTIAL_VOLUME = "sdlc-claude-credentials"
CONFIG_FILE = ".archon/credentials.yaml"
CONTAINER_CRED_PATH = "/home/sdlc/.claude/.credentials.json"


def _try_keychain(work_dir: Path) -> dict | None:
    """Tier 1: Extract credentials from macOS Keychain."""
    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return None

        cred_json = result.stdout.strip()
        if not cred_json:
            return None

        parsed = json.loads(cred_json)
        if "claudeAiOauth" not in parsed:
            return None

        temp_file = work_dir / ".sdlc-cred-temp.json"
        temp_file.write_text(cred_json)
        os.chmod(temp_file, 0o600)

        return {
            "tier": "keychain",
            "mount_args": f"{temp_file}:{CONTAINER_CRED_PATH}:ro",
            "message": "Credentials from macOS Keychain",
            "cleanup": str(temp_file),
        }
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        return None


def _try_volume() -> dict | None:
    """Tier 2: Check for Docker credential volume."""
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

        return {
            "tier": "volume",
            "mount_args": f"{CREDENTIAL_VOLUME}:/home/sdlc/.claude-creds:ro",
            "message": f"Credentials from Docker volume: {CREDENTIAL_VOLUME}",
            "cleanup": None,
        }
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def _try_config(project_dir: Path) -> dict | None:
    """Tier 3: Check for .archon/credentials.yaml config."""
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
            return None

        return {
            "tier": "config",
            "mount_args": f"{cred_file}:{CONTAINER_CRED_PATH}:ro",
            "message": f"Credentials from config: {cred_path}",
            "cleanup": None,
        }
    except (yaml.YAMLError, OSError):
        return None


def resolve(
    work_dir: Path,
    project_dir: Path,
) -> dict:
    """Resolve credentials using the three-tier fallback."""
    result = _try_keychain(work_dir)
    if result:
        return result

    result = _try_volume()
    if result:
        return result

    result = _try_config(project_dir)
    if result:
        return result

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

    parser = argparse.ArgumentParser(description="Resolve Claude Code credentials")
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    work_dir = Path(tempfile.mkdtemp(prefix="sdlc-cred-"))
    result = resolve(work_dir, args.project_dir)

    if args.json:
        print(json_mod.dumps(result, indent=2))
    else:
        print(f"Tier: {result['tier']}")
        print(f"  {result['message']}")

    cleanup_path = result.get("cleanup")
    if cleanup_path:
        Path(cleanup_path).unlink(missing_ok=True)
    try:
        work_dir.rmdir()
    except OSError:
        pass


if __name__ == "__main__":
    main()
