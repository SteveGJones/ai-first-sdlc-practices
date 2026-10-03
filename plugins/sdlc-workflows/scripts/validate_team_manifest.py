#!/usr/bin/env python3
"""Validate team manifests against the SDLC-workflows manifest schema.

A team manifest is a YAML file describing which plugins, agents, skills,
and context files compose a containerised team image.

Schema (v1.0)
-------------
::

    schema_version: "1.0"
    name: <team-name>           # valid Docker tag component
    description: >              # optional
      Human-readable description.
    status: active              # active | ephemeral | inactive | decommissioned
    plugins:
      - <plugin-name>           # must exist in installed_plugins.json
    agents:                     # optional
      - <plugin>:<agent>        # plugin must be in plugins list
      - local:<path>            # local file must exist
    skills:                     # optional
      - <plugin>:<skill>        # plugin must be in plugins list
      - local:<path>            # local file must exist
    context:                    # optional
      - <filename>              # must exist in project root

Public API
----------
validate(manifest_path, installed_json=None, project_root=None) -> list[str]
    Returns a list of error strings.  Empty list means the manifest is valid.
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path
from typing import Any

import yaml

# Allow sibling import when run as a script or from the import shim.
_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

import resolve_plugin_paths  # noqa: E402

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_REQUIRED_FIELDS = ("schema_version", "name", "status", "plugins")
_SUPPORTED_SCHEMA_VERSION = "1.0"
_VALID_STATUSES = {"active", "ephemeral", "inactive", "decommissioned"}
_DOCKER_TAG_RE = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def validate(
    manifest_path: Path,
    installed_json: Path | None = None,
    project_root: Path | None = None,
) -> list[str]:
    """Validate a team manifest YAML file.

    Parameters
    ----------
    manifest_path:
        Path to the YAML manifest file.
    installed_json:
        Path to ``installed_plugins.json``.  If ``None``, plugin resolution
        checks are skipped.
    project_root:
        Project root directory for resolving ``local:`` paths and ``context``
        files.  Defaults to the directory containing *manifest_path*.

    Returns
    -------
    list[str]
        Error messages.  An empty list means the manifest is valid.
    """
    if project_root is None:
        project_root = manifest_path.parent

    logger.info(
        "Team manifest validation start",
        extra={"manifest_path": str(manifest_path), "has_installed_json": installed_json is not None},
    )
    errors: list[str] = []

    # -- Parse YAML --------------------------------------------------------
    try:
        raw = manifest_path.read_text()
        data: Any = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        logger.error(
            "Manifest YAML parse failed",
            extra={"manifest_path": str(manifest_path), "error": type(exc).__name__},
            exc_info=True,
        )
        return [f"YAML parse error: {exc}"]
    except OSError as exc:
        logger.error(
            "Manifest read failed",
            extra={"manifest_path": str(manifest_path), "error": type(exc).__name__},
            exc_info=True,
        )
        return [f"Cannot read manifest: {exc}"]

    if not isinstance(data, dict):
        return ["Manifest must be a YAML mapping (got null or non-mapping)"]

    # -- Required fields ---------------------------------------------------
    for field in _REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    # Early return if structure is too broken to continue
    if errors:
        return errors

    # -- schema_version ----------------------------------------------------
    sv = str(data["schema_version"])
    if sv != _SUPPORTED_SCHEMA_VERSION:
        errors.append(
            f"Unsupported schema_version '{sv}' (expected '{_SUPPORTED_SCHEMA_VERSION}')"
        )

    # -- name (Docker tag component) ---------------------------------------
    name = str(data["name"])
    if not name or not _DOCKER_TAG_RE.match(name):
        errors.append(
            f"Invalid name '{name}': must be a valid Docker tag component "
            "(lowercase alphanumeric, hyphens, dots, underscores; no leading separator)"
        )

    # -- status ------------------------------------------------------------
    status = str(data["status"])
    if status not in _VALID_STATUSES:
        errors.append(
            f"Invalid status '{status}': must be one of {sorted(_VALID_STATUSES)}"
        )

    # -- plugins (must be a list) ------------------------------------------
    plugins_raw = data["plugins"]
    if not isinstance(plugins_raw, list):
        errors.append("Field 'plugins' must be a list of plugin keys")
        return errors

    plugin_keys: list[str] = [str(p) for p in plugins_raw]

    # -- Plugin resolution -------------------------------------------------
    if installed_json is not None:
        try:
            resolve_plugin_paths.resolve_all(plugin_keys, installed_json)
        except resolve_plugin_paths.PluginNotFoundError as exc:
            logger.warning(
                "Plugin resolution failed for manifest",
                extra={
                    "manifest_path": str(manifest_path),
                    "missing_count": len(exc.missing),
                },
            )
            for missing in exc.missing:
                errors.append(f"Plugin not installed: {missing}")

    # -- Agents ------------------------------------------------------------
    agents_raw: list[str] = data.get("agents", []) or []
    if not isinstance(agents_raw, list):
        errors.append("Field 'agents' must be a list")
        agents_raw = []

    resolved_root = project_root.resolve()

    def _within_project_root(p: Path) -> bool:
        """Return True iff *p* resolves to a location inside the project.

        CR-M-1: ``local: ../../etc/passwd`` must be rejected.  We
        resolve to an absolute path first (following symlinks) so
        adversarial ``..`` segments cannot escape the project tree.
        """
        try:
            resolved = (resolved_root / p).resolve()
        except (OSError, RuntimeError) as exc:
            logger.warning(
                "Path resolution failed during project-root check",
                extra={"candidate_path": str(p), "error": type(exc).__name__},
            )
            return False
        try:
            resolved.relative_to(resolved_root)
        except ValueError:
            logger.warning(
                "Path escapes project root (rejected)",
                extra={"candidate_path": str(p), "resolved": str(resolved)},
            )
            return False
        return True

    for agent_ref in agents_raw:
        agent_str = str(agent_ref)
        if agent_str.startswith("local:"):
            rel = Path(agent_str.removeprefix("local:"))
            if not _within_project_root(rel):
                errors.append(
                    f"Local agent path escapes project root: {agent_str}"
                )
                continue
            local_path = project_root / rel
            if not local_path.exists():
                errors.append(f"Local agent file not found: {agent_str}")
        else:
            # Format: plugin_key:agent_name
            parts = agent_str.rsplit(":", 1)
            if len(parts) == 2:
                plugin_key = parts[0]
                if plugin_key not in plugin_keys:
                    errors.append(
                        f"Orphan agent '{agent_str}': plugin '{plugin_key}' "
                        "is not in the plugins list"
                    )

    # -- Skills ------------------------------------------------------------
    skills_raw: list[str] = data.get("skills", []) or []
    if not isinstance(skills_raw, list):
        errors.append("Field 'skills' must be a list")
        skills_raw = []

    for skill_ref in skills_raw:
        skill_str = str(skill_ref)
        if skill_str.startswith("local:"):
            rel = Path(skill_str.removeprefix("local:"))
            if not _within_project_root(rel):
                errors.append(
                    f"Local skill path escapes project root: {skill_str}"
                )
                continue
            local_path = project_root / rel
            if not local_path.exists():
                errors.append(f"Local skill file not found: {skill_str}")
        else:
            # Format: plugin_key:skill_name
            parts = skill_str.rsplit(":", 1)
            if len(parts) == 2:
                plugin_key = parts[0]
                if plugin_key not in plugin_keys:
                    errors.append(
                        f"Orphan skill '{skill_str}': plugin '{plugin_key}' "
                        "is not in the plugins list"
                    )

    # -- Context files -----------------------------------------------------
    context_raw: list[str] = data.get("context", []) or []
    if not isinstance(context_raw, list):
        errors.append("Field 'context' must be a list")
        context_raw = []

    for ctx_file in context_raw:
        rel = Path(str(ctx_file))
        if not _within_project_root(rel):
            errors.append(
                f"Context file path escapes project root: {ctx_file}"
            )
            continue
        ctx_path = project_root / rel
        if not ctx_path.exists():
            errors.append(f"Context file not found: {ctx_file}")

    # -- Reserved forward-compat fields ------------------------------------
    # SA-M-4: `group:` is reserved for future use (team grouping /
    # namespacing across a larger fleet).  Accept it today so authors
    # can declare intent ahead of runtime support; emit a warning
    # instead of an error so a declaration never blocks a build.
    if "group" in data:
        group_value = data["group"]
        if not isinstance(group_value, str) or not group_value.strip():
            errors.append(
                "Field 'group' must be a non-empty string if present"
            )
        else:
            logger.warning(
                "Reserved field 'group' is accepted but has no runtime effect in v1",
                extra={"manifest_name": data.get("name"), "group": group_value},
            )

    return errors


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry point for validate_team_manifest."""
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    logger.info("validate_team_manifest CLI start")
    parser = argparse.ArgumentParser(
        description="Validate a team manifest YAML against the SDLC-workflows schema."
    )
    parser.add_argument(
        "manifest",
        type=Path,
        help="Path to the team manifest YAML file.",
    )
    parser.add_argument(
        "--installed-json",
        type=Path,
        default=None,
        help="Path to installed_plugins.json (skip plugin checks if omitted).",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="Project root for resolving local paths and context files.",
    )
    args = parser.parse_args()

    errors = validate(args.manifest, args.installed_json, args.project_root)
    if errors:
        print(f"FAIL: {len(errors)} error(s) in {args.manifest}")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print(f"OK: {args.manifest} is valid")
        sys.exit(0)


if __name__ == "__main__":
    main()
