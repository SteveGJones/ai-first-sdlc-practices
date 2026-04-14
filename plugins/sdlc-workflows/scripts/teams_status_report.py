#!/usr/bin/env python3
"""Generate fleet status data for delegation teams.

Reads team manifests from ``.archon/teams/``, checks staleness via
timestamp comparison, maps workflow references, and assembles a
structured report.

Public API
----------
load_manifests(teams_dir) -> list[dict]
staleness(manifest) -> str
workflow_usage(workflows_dir) -> dict[str, list[dict]]
fleet_report(teams_dir, workflows_dir) -> dict
"""

from __future__ import annotations

from pathlib import Path

import yaml


def load_manifests(teams_dir: Path) -> list[dict]:
    """Load all team manifest YAML files from *teams_dir*.

    Skips subdirectories (e.g. ``.generated/``).
    """
    if not teams_dir.is_dir():
        return []
    manifests: list[dict] = []
    for yaml_file in sorted(teams_dir.glob("*.yaml")):
        with yaml_file.open() as fh:
            data = yaml.safe_load(fh)
        if isinstance(data, dict):
            manifests.append(data)
    return manifests


def staleness(manifest: dict) -> str:
    """Determine staleness of a team image.

    Returns ``"current"``, ``"stale"``, or ``"not_built"``.
    """
    updated = manifest.get("updated")
    image_built = manifest.get("image_built")

    if not image_built:
        return "not_built"

    if str(updated) > str(image_built):
        return "stale"
    return "current"


def workflow_usage(
    workflows_dir: Path,
) -> dict[str, list[dict[str, str]]]:
    """Map team names to their workflow node references.

    Returns ``{team_name: [{"workflow": name, "node": node_id}]}``.
    """
    if not workflows_dir.is_dir():
        return {}

    usage: dict[str, list[dict[str, str]]] = {}

    for wf_path in sorted(workflows_dir.glob("*.yaml")):
        with wf_path.open() as fh:
            data = yaml.safe_load(fh)
        if not isinstance(data, dict):
            continue

        wf_name = data.get("name", wf_path.stem)
        nodes = data.get("nodes", [])
        if not isinstance(nodes, list):
            continue

        for node in nodes:
            if not isinstance(node, dict):
                continue
            image = node.get("image")
            if not image or ":" not in str(image):
                continue
            _, _, team_name = str(image).partition(":")
            if team_name == "base":
                continue
            usage.setdefault(team_name, []).append({
                "workflow": str(wf_name),
                "node": str(node.get("id", "<unknown>")),
            })

    return usage


def _count_list(manifest: dict, key: str) -> int:
    """Count items in a manifest list field, handling None/missing."""
    val = manifest.get(key)
    if isinstance(val, list):
        return len(val)
    return 0


def fleet_report(
    teams_dir: Path,
    workflows_dir: Path,
) -> dict:
    """Assemble a complete fleet status report.

    Returns a dict with ``team_count``, ``workflow_count``, and
    ``teams`` (list of per-team status dicts).
    """
    manifests = load_manifests(teams_dir)
    usage = workflow_usage(workflows_dir)

    teams: list[dict] = []
    for manifest in manifests:
        name = str(manifest.get("name", "unknown"))
        refs = usage.get(name, [])
        teams.append({
            "name": name,
            "status": str(manifest.get("status", "unknown")),
            "agent_count": _count_list(manifest, "agents"),
            "skill_count": _count_list(manifest, "skills"),
            "staleness": staleness(manifest),
            "workflow_count": len(refs),
            "workflow_refs": refs,
            "updated": manifest.get("updated"),
            "image_built": manifest.get("image_built"),
        })

    return {
        "team_count": len(teams),
        "workflow_count": len(set(
            ref["workflow"]
            for t in teams
            for ref in t["workflow_refs"]
        )),
        "teams": teams,
    }
