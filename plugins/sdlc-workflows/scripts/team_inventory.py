#!/usr/bin/env python3
"""Discover available agents and skills from installed plugins.

Walks each plugin's ``agents/`` and ``skills/`` directories to build
a structured inventory.  Used by ``manage-teams`` (to show what's
available during team creation) and ``teams-status`` (to report
"available but not included").

Public API
----------
discover_plugin_agents(plugin_path) -> list[dict]
discover_plugin_skills(plugin_path) -> list[dict]
discover_all(installed_json) -> dict[str, dict]
available_but_not_included(installed_json, team_plugins, team_agents) -> dict
"""

from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path

# Allow sibling import when run as a script.
_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

logger = logging.getLogger(__name__)

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)


def _parse_frontmatter(text: str) -> dict[str, str]:
    """Extract key: value pairs from YAML frontmatter."""
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}
    result: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            result[key.strip()] = val.strip().strip("'\"")
    return result


def discover_plugin_agents(plugin_path: Path) -> list[dict[str, str]]:
    """Discover agents in a plugin's ``agents/`` directory.

    Returns a list of dicts with ``name`` and ``description`` keys.
    """
    logger.debug("Discovering agents", extra={"plugin_path": str(plugin_path)})
    agents_dir = plugin_path / "agents"
    if not agents_dir.is_dir():
        return []

    agents: list[dict[str, str]] = []
    for md_file in sorted(agents_dir.glob("*.md")):
        text = md_file.read_text()
        fm = _parse_frontmatter(text)
        name = fm.get("name", md_file.stem)
        description = fm.get("description", "")
        agents.append({"name": name, "description": description})
    logger.debug(
        "Plugin agent discovery complete",
        extra={"plugin_path": str(plugin_path), "count": len(agents)},
    )
    return agents


def discover_plugin_skills(plugin_path: Path) -> list[dict[str, str]]:
    """Discover skills in a plugin's ``skills/`` directory.

    A valid skill is a subdirectory containing ``SKILL.md``.
    Returns a list of dicts with ``name`` and ``description`` keys.
    """
    logger.debug("Discovering skills", extra={"plugin_path": str(plugin_path)})
    skills_dir = plugin_path / "skills"
    if not skills_dir.is_dir():
        return []

    skills: list[dict[str, str]] = []
    for child in sorted(skills_dir.iterdir()):
        skill_md = child / "SKILL.md"
        if child.is_dir() and skill_md.exists():
            text = skill_md.read_text()
            fm = _parse_frontmatter(text)
            name = fm.get("name", child.name)
            description = fm.get("description", "")
            skills.append({"name": name, "description": description})
    logger.debug(
        "Plugin skill discovery complete",
        extra={"plugin_path": str(plugin_path), "count": len(skills)},
    )
    return skills


def discover_all(
    installed_json: Path,
) -> dict[str, dict[str, list[dict[str, str]]]]:
    """Build a complete inventory of agents and skills from all installed plugins.

    Parameters
    ----------
    installed_json:
        Path to ``installed_plugins.json``.

    Returns
    -------
    dict
        ``{plugin_name: {"agents": [...], "skills": [...]}}``
        Plugins whose install path doesn't exist are silently skipped.
    """
    logger.info(
        "Building plugin inventory",
        extra={"installed_json": str(installed_json)},
    )
    with installed_json.open() as fh:
        raw = json.load(fh)

    entries: dict[str, dict[str, str]] = {}
    if isinstance(raw, dict) and "version" in raw and "plugins" in raw:
        for key, val_list in raw["plugins"].items():
            if isinstance(val_list, list) and val_list:
                entries[key] = val_list[0]
            elif isinstance(val_list, dict):
                entries[key] = val_list
    else:
        for key, val in raw.items():
            if isinstance(val, dict):
                entries[key] = val
            elif isinstance(val, list) and val:
                entries[key] = val[0]

    inventory: dict[str, dict[str, list[dict[str, str]]]] = {}
    for key, entry in entries.items():
        install_path = entry.get("installPath")
        if not install_path:
            continue
        plugin_path = Path(install_path)
        if not plugin_path.is_dir():
            continue

        bare_name = key.split("@")[0] if "@" in key else key
        inventory[bare_name] = {
            "agents": discover_plugin_agents(plugin_path),
            "skills": discover_plugin_skills(plugin_path),
        }

    return inventory


def available_but_not_included(
    installed_json: Path,
    team_plugins: list[str],
    team_agents: list[str],
) -> dict[str, list[dict[str, str]]]:
    """Find agents and skills available in team plugins but not on the team.

    Parameters
    ----------
    installed_json:
        Path to ``installed_plugins.json``.
    team_plugins:
        Plugin names listed in the team manifest.
    team_agents:
        Qualified agent references (``plugin:agent``) in the team manifest.

    Returns
    -------
    dict
        ``{"agents": [{"qualified": "plugin:agent", "description": "..."}]}``
    """
    logger.debug(
        "Computing available-but-not-included set",
        extra={"team_plugins_count": len(team_plugins), "team_agents_count": len(team_agents)},
    )
    inventory = discover_all(installed_json)

    included_agents: set[str] = set()
    for ref in team_agents:
        if ":" in ref and not ref.startswith("local:"):
            included_agents.add(ref)

    available_agents: list[dict[str, str]] = []
    for plugin_name in team_plugins:
        bare = plugin_name.split("@")[0] if "@" in plugin_name else plugin_name
        if bare not in inventory:
            continue
        for agent in inventory[bare]["agents"]:
            qualified = f"{bare}:{agent['name']}"
            if qualified not in included_agents:
                available_agents.append({
                    "qualified": qualified,
                    "description": agent.get("description", ""),
                })

    return {"agents": available_agents}


def main() -> None:
    """CLI entry point — print plugin inventory or available-but-not-included."""
    import argparse

    import yaml as yaml_mod

    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    logger.info("team_inventory CLI start")
    parser = argparse.ArgumentParser(description="Plugin inventory discovery")
    parser.add_argument(
        "--installed-json",
        type=Path,
        default=Path.home() / ".claude" / "plugins" / "installed_plugins.json",
    )
    parser.add_argument(
        "--team-manifest",
        type=Path,
        default=None,
        help="Show available-but-not-included for a specific team manifest.",
    )
    args = parser.parse_args()

    import json as json_mod

    if args.team_manifest:
        with args.team_manifest.open() as fh:
            manifest = yaml_mod.safe_load(fh)
        plugins = [str(p) for p in manifest.get("plugins", [])]
        agents = [str(a) for a in manifest.get("agents", [])]
        result = available_but_not_included(args.installed_json, plugins, agents)
        print(json_mod.dumps(result, indent=2))
    else:
        inv = discover_all(args.installed_json)
        print(json_mod.dumps(inv, indent=2))


if __name__ == "__main__":
    main()
