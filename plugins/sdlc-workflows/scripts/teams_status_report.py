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

import logging
from datetime import datetime, timezone
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


def load_manifests(teams_dir: Path) -> list[dict]:
    """Load all team manifest YAML files from *teams_dir*.

    Skips subdirectories (e.g. ``.generated/``). Each returned dict is
    augmented with a ``_manifest_path`` key so downstream callers can
    reach the team's generated CLAUDE.md for mtime-based staleness
    checks (SA-M-5). The key is prefixed with an underscore to mark it
    as internal metadata — it is not part of the manifest schema.
    """
    logger.debug("Loading team manifests", extra={"teams_dir": str(teams_dir)})
    if not teams_dir.is_dir():
        logger.info("Teams directory does not exist", extra={"teams_dir": str(teams_dir)})
        return []
    manifests: list[dict] = []
    for yaml_file in sorted(teams_dir.glob("*.yaml")):
        with yaml_file.open() as fh:
            data = yaml.safe_load(fh)
        if isinstance(data, dict):
            data["_manifest_path"] = str(yaml_file)
            manifests.append(data)
    logger.info(
        "Loaded team manifests",
        extra={"teams_dir": str(teams_dir), "manifest_count": len(manifests)},
    )
    return manifests


def _generated_claude_mtime(manifest: dict) -> str | None:
    """Return ISO-formatted mtime of the team's generated CLAUDE.md, if any.

    The generated file lives at ``<teams_dir>/.generated/<name>-CLAUDE.md``
    and is produced by ``generate_team_claude_md.py`` during
    ``build-team.sh``. If the project's root CLAUDE.md has been edited
    since the last image build, the generated team CLAUDE.md will also
    be newer — so its mtime is the right staleness input, not the
    project root's own CLAUDE.md.
    """
    manifest_path_str = manifest.get("_manifest_path")
    if not manifest_path_str:
        return None
    manifest_path = Path(manifest_path_str)
    name = manifest.get("name")
    if not name:
        return None
    generated = manifest_path.parent / ".generated" / f"{name}-CLAUDE.md"
    if not generated.is_file():
        return None
    mtime = datetime.fromtimestamp(generated.stat().st_mtime, tz=timezone.utc)
    return mtime.isoformat()


def staleness(manifest: dict) -> str:
    """Determine staleness of a team image.

    Returns ``"current"``, ``"stale"``, or ``"not_built"``.

    A team is stale when any of:
      - the manifest's ``updated`` timestamp is newer than ``image_built``
      - the generated team CLAUDE.md mtime is newer than ``image_built``
        (SA-M-5 — picks up drift from the project root's CLAUDE.md,
        which is concatenated into the generated file at build time).
    """
    name = manifest.get("name", "unknown")
    updated = manifest.get("updated")
    image_built = manifest.get("image_built")
    claude_mtime = _generated_claude_mtime(manifest)
    logger.debug(
        "Evaluating team staleness",
        extra={
            "team": name,
            "updated": str(updated),
            "image_built": str(image_built),
            "generated_claude_mtime": str(claude_mtime),
        },
    )

    if not image_built:
        logger.info("Team image status: not_built", extra={"team": name})
        return "not_built"

    if str(updated) > str(image_built):
        logger.info(
            "Team image status: stale (manifest updated)",
            extra={"team": name},
        )
        return "stale"
    if claude_mtime and claude_mtime > str(image_built):
        logger.info(
            "Team image status: stale (generated CLAUDE.md newer than image)",
            extra={"team": name},
        )
        return "stale"
    logger.debug("Team image status: current", extra={"team": name})
    return "current"


def workflow_usage(
    workflows_dir: Path,
) -> dict[str, list[dict[str, str]]]:
    """Map team names to their workflow node references.

    Returns ``{team_name: [{"workflow": name, "node": node_id}]}``.
    """
    logger.debug(
        "Scanning workflows for team references",
        extra={"workflows_dir": str(workflows_dir)},
    )
    if not workflows_dir.is_dir():
        logger.info(
            "Workflows directory does not exist",
            extra={"workflows_dir": str(workflows_dir)},
        )
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

    logger.info(
        "Workflow usage map built",
        extra={"team_count": len(usage)},
    )
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
    logger.info(
        "Assembling fleet report",
        extra={"teams_dir": str(teams_dir), "workflows_dir": str(workflows_dir)},
    )
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

    workflow_count = len(set(
        ref["workflow"]
        for t in teams
        for ref in t["workflow_refs"]
    ))
    logger.info(
        "Fleet report assembled",
        extra={"team_count": len(teams), "workflow_count": workflow_count},
    )
    return {
        "team_count": len(teams),
        "workflow_count": workflow_count,
        "teams": teams,
    }


def main() -> None:
    """CLI entry point for teams_status_report."""
    import argparse

    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    logger.info("teams_status_report CLI start")

    parser = argparse.ArgumentParser(description="Generate fleet status report")
    parser.add_argument(
        "--teams-dir", type=Path, default=Path(".archon/teams"),
    )
    parser.add_argument(
        "--workflows-dir", type=Path, default=Path(".archon/workflows"),
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    import json as json_mod
    report = fleet_report(args.teams_dir, args.workflows_dir)
    if args.json:
        print(json_mod.dumps(report, indent=2, default=str))
    else:
        print(f"Teams: {report['team_count']}, Workflows: {report['workflow_count']}")
        for team in report["teams"]:
            print(
                f"  {team['name']:30s} {team['status']:10s} "
                f"{team['agent_count']} agents  {team['skill_count']} skills  "
                f"{team['staleness']:10s} {team['workflow_count']} wf"
            )


if __name__ == "__main__":
    main()
