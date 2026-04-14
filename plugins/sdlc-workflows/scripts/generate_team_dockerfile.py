#!/usr/bin/env python3
"""Generate team-specific Dockerfiles from team manifests.

Reads a team manifest YAML, resolves plugin install paths via
``installed_plugins.json``, and produces a Dockerfile that:

1. Uses ``sdlc-worker:full`` as a source layer (``COPY --from``).
2. Uses ``sdlc-worker:base`` as the runtime base.
3. Copies ONLY the listed agent files and skill directories (additive, no prune).
4. Copies ``plugin.json`` for each listed plugin.
5. Copies ``installed_plugins.json``.
6. Copies local agents/skills from the project.
7. Makes plugins read-only (``chmod -R a-w``).
8. Bakes in the generated team ``CLAUDE.md``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

# Allow sibling import when run as a script.
_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

import resolve_plugin_paths  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_IMAGE_PLUGINS_ROOT = "/home/sdlc/.claude/plugins"
_IMAGE_CACHE_PREFIX = f"{_IMAGE_PLUGINS_ROOT}/cache"
_IMAGE_WORKSPACE = "/workspace"


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def find_agent_file(plugin_path: Path, agent_name: str) -> Path | None:
    """Find an agent Markdown file inside a plugin's ``agents/`` directory.

    Searches for ``<agent_name>.md`` (case-insensitive) in the plugin's
    ``agents/`` directory.

    Parameters
    ----------
    plugin_path:
        Root directory of the plugin on the host filesystem.
    agent_name:
        The unqualified agent name (e.g. ``security-architect``).

    Returns
    -------
    Path | None
        Absolute path to the agent ``.md`` file, or ``None`` if not found.
    """
    agents_dir = plugin_path / "agents"
    if not agents_dir.is_dir():
        return None

    # Direct match first
    candidate = agents_dir / f"{agent_name}.md"
    if candidate.exists():
        return candidate

    # Case-insensitive fallback
    lower_name = f"{agent_name}.md".lower()
    for child in agents_dir.iterdir():
        if child.name.lower() == lower_name and child.is_file():
            return child

    return None


def find_skill_dir(plugin_path: Path, skill_name: str) -> Path | None:
    """Find a skill directory (containing ``SKILL.md``) inside a plugin.

    Parameters
    ----------
    plugin_path:
        Root directory of the plugin on the host filesystem.
    skill_name:
        The unqualified skill name (e.g. ``validate``).

    Returns
    -------
    Path | None
        Absolute path to the skill directory, or ``None`` if not found.
    """
    skills_dir = plugin_path / "skills"
    if not skills_dir.is_dir():
        return None

    candidate = skills_dir / skill_name
    if candidate.is_dir() and (candidate / "SKILL.md").exists():
        return candidate

    # Case-insensitive fallback
    lower_name = skill_name.lower()
    for child in skills_dir.iterdir():
        if child.name.lower() == lower_name and child.is_dir():
            if (child / "SKILL.md").exists():
                return child

    return None


def _host_to_image_rel(host_path: Path, plugins_root: Path) -> str:
    """Convert a host filesystem path to the relative path inside the image.

    The host plugin cache might be at ``~/.claude/plugins/cache/...``, while
    inside the Docker image it lives under ``/home/sdlc/.claude/plugins/cache/...``.
    This function computes the relative part from the cache root and returns
    the absolute image path.

    Parameters
    ----------
    host_path:
        Absolute path on the host (inside the plugins cache).
    plugins_root:
        The host plugins root directory (parent of ``cache/``).

    Returns
    -------
    str
        Absolute path inside the Docker image.
    """
    # Find the 'cache' component in the host path and compute relative from there
    cache_dir = plugins_root / "cache"
    if str(host_path).startswith(str(cache_dir)):
        rel = host_path.relative_to(cache_dir)
        return f"{_IMAGE_CACHE_PREFIX}/{rel}"

    # Fallback: try relative to plugins_root
    try:
        rel = host_path.relative_to(plugins_root)
        return f"{_IMAGE_PLUGINS_ROOT}/{rel}"
    except ValueError:
        # Last resort: use the path basename components from 'cache' onwards
        parts = host_path.parts
        for idx, part in enumerate(parts):
            if part == "cache":
                rel_parts = parts[idx:]
                return f"{_IMAGE_PLUGINS_ROOT}/{'/'.join(rel_parts)}"
        # Cannot determine relative path — return as-is (will cause build error)
        return str(host_path)


def _image_path_for_plugin(plugin_path: Path, plugins_root: Path) -> str:
    """Return the image-side base directory for a plugin.

    Parameters
    ----------
    plugin_path:
        Host filesystem path to the plugin root.
    plugins_root:
        Host plugins root directory.

    Returns
    -------
    str
        Absolute path inside the Docker image for the plugin root.
    """
    return _host_to_image_rel(plugin_path, plugins_root)


def _infer_plugins_root(plugin_paths: dict[str, Path]) -> Path:
    """Infer the host plugins root from resolved plugin paths.

    Walks up from a resolved plugin path to find the ``plugins`` directory
    that contains the ``cache/`` subdirectory.

    Parameters
    ----------
    plugin_paths:
        Mapping from plugin key to host path.

    Returns
    -------
    Path
        The inferred plugins root directory on the host.
    """
    if not plugin_paths:
        return Path.home() / ".claude" / "plugins"

    sample = next(iter(plugin_paths.values()))
    # Walk up until we find a directory that has 'cache' as a child or
    # whose name is 'plugins'
    current = sample
    while current != current.parent:
        if current.name == "cache":
            return current.parent
        if current.name == "plugins":
            return current
        current = current.parent

    return Path.home() / ".claude" / "plugins"


# ---------------------------------------------------------------------------
# Dockerfile generation
# ---------------------------------------------------------------------------


def generate(
    manifest_path: Path,
    installed_json: Path,
    team_claude_md_path: Path,
    output_path: Path,
) -> str:
    """Generate a Dockerfile for a team image from a manifest.

    Parameters
    ----------
    manifest_path:
        Path to the team manifest YAML.
    installed_json:
        Path to ``installed_plugins.json``.
    team_claude_md_path:
        Path to the pre-generated team ``CLAUDE.md`` file.
    output_path:
        Where to write the generated Dockerfile.

    Returns
    -------
    str
        The generated Dockerfile content.
    """
    with manifest_path.open() as fh:
        manifest: dict[str, object] = yaml.safe_load(fh)

    team_name: str = str(manifest.get("name", "unnamed-team"))
    plugin_keys: list[str] = [str(p) for p in manifest.get("plugins", [])]  # type: ignore[union-attr]
    agent_refs: list[str] = list(manifest.get("agents", []) or [])  # type: ignore[arg-type]
    skill_refs: list[str] = list(manifest.get("skills", []) or [])  # type: ignore[arg-type]

    # Resolve plugin install paths
    plugin_paths = resolve_plugin_paths.resolve_all(plugin_keys, installed_json)
    plugins_root = _infer_plugins_root(plugin_paths)

    lines: list[str] = []
    lines.append(f"# Auto-generated Dockerfile for team: {team_name}")
    lines.append("# DO NOT EDIT — regenerate with generate_team_dockerfile.py")
    lines.append("")
    lines.append("FROM sdlc-worker:full AS plugin-source")
    lines.append("FROM sdlc-worker:base")
    lines.append("")

    # -- Plugin metadata (.claude-plugin/ directories) -------------------------
    for plugin_key in plugin_keys:
        plugin_path = plugin_paths[plugin_key]
        image_base = _image_path_for_plugin(plugin_path, plugins_root)
        short_name = plugin_key.split("@")[0] if "@" in plugin_key else plugin_key

        lines.append(f"# Plugin: {short_name} — plugin metadata")
        lines.append(
            f"COPY --from=plugin-source {image_base}/.claude-plugin/ \\"
        )
        lines.append(f"     {image_base}/.claude-plugin/")
        lines.append("")

    # -- Agents (additive copy — only listed files) ----------------------------
    plugin_agents: list[tuple[str, str]] = []
    local_agents: list[str] = []

    for agent_ref in agent_refs:
        if agent_ref.startswith("local:"):
            local_agents.append(agent_ref.removeprefix("local:"))
        else:
            parts = agent_ref.rsplit(":", 1)
            if len(parts) == 2:
                plugin_agents.append((parts[0], parts[1]))

    if plugin_agents:
        lines.append("# Agents (additive copy — only listed files)")
        for plugin_key, agent_name in plugin_agents:
            plugin_path = plugin_paths[plugin_key]
            agent_file = find_agent_file(plugin_path, agent_name)
            if agent_file is None:
                lines.append(
                    f"# WARNING: agent '{agent_name}' not found in {plugin_key}"
                )
                continue
            image_agent = _host_to_image_rel(agent_file, plugins_root)
            lines.append(f"COPY --from=plugin-source {image_agent} \\")
            lines.append(f"     {image_agent}")
        lines.append("")

    # -- Skills (additive copy — only listed directories) ----------------------
    plugin_skills: list[tuple[str, str]] = []
    local_skills: list[str] = []

    for skill_ref in skill_refs:
        if skill_ref.startswith("local:"):
            local_skills.append(skill_ref.removeprefix("local:"))
        else:
            parts = skill_ref.rsplit(":", 1)
            if len(parts) == 2:
                plugin_skills.append((parts[0], parts[1]))

    if plugin_skills:
        lines.append("# Skills (additive copy — only listed directories)")
        for plugin_key, skill_name in plugin_skills:
            plugin_path = plugin_paths[plugin_key]
            skill_dir = find_skill_dir(plugin_path, skill_name)
            if skill_dir is None:
                lines.append(
                    f"# WARNING: skill '{skill_name}' not found in {plugin_key}"
                )
                continue
            image_skill = _host_to_image_rel(skill_dir, plugins_root)
            lines.append(f"COPY --from=plugin-source {image_skill}/ \\")
            lines.append(f"     {image_skill}/")
        lines.append("")

    # -- Local agents and skills (from project, not from plugin-source) --------
    if local_agents:
        lines.append("# Local agents (from project)")
        for local_path in local_agents:
            lines.append(f"COPY {local_path} {_IMAGE_WORKSPACE}/{local_path}")
        lines.append("")

    if local_skills:
        lines.append("# Local skills (from project)")
        for local_path in local_skills:
            lines.append(f"COPY {local_path}/ {_IMAGE_WORKSPACE}/{local_path}/")
        lines.append("")

    # -- Plugin registry -------------------------------------------------------
    lines.append("# Plugin registry")
    lines.append(
        f"COPY --from=plugin-source {_IMAGE_PLUGINS_ROOT}/installed_plugins.json \\"
    )
    lines.append(f"     {_IMAGE_PLUGINS_ROOT}/installed_plugins.json")
    lines.append("")

    # -- Switch to root for ownership / permission operations -------------------
    # The base image ends with USER sdlc, so we need root for chmod/chown.
    lines.append("# Switch to root for file permission operations")
    lines.append("USER root")
    lines.append("")

    # -- Make plugins read-only ------------------------------------------------
    lines.append("# Make plugins read-only — prevents runtime plugin installation")
    lines.append(f"RUN chmod -R a-w {_IMAGE_PLUGINS_ROOT}/")
    lines.append("")

    # -- Team CLAUDE.md --------------------------------------------------------
    lines.append("# Team CLAUDE.md")
    # The build context is the project root, so reference the CLAUDE.md
    # by its path relative to the project root.  The build script places
    # it in .archon/teams/.generated/<name>-CLAUDE.md.
    lines.append(f"COPY {team_claude_md_path} {_IMAGE_WORKSPACE}/CLAUDE.md")
    lines.append(f"RUN chown sdlc:sdlc {_IMAGE_WORKSPACE}/CLAUDE.md")
    lines.append("")

    # -- Final runtime settings ------------------------------------------------
    lines.append("USER sdlc")
    lines.append(f"WORKDIR {_IMAGE_WORKSPACE}")
    lines.append("")

    content = "\n".join(lines)

    # Write the Dockerfile
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content)

    return content


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry point for generate_team_dockerfile."""
    parser = argparse.ArgumentParser(
        description="Generate a team-specific Dockerfile from a team manifest."
    )
    parser.add_argument(
        "manifest",
        type=Path,
        help="Path to the team manifest YAML file.",
    )
    parser.add_argument(
        "--installed-plugins",
        type=Path,
        required=True,
        help="Path to installed_plugins.json.",
    )
    parser.add_argument(
        "--team-claude-md",
        type=Path,
        required=True,
        help="Path to the pre-generated team CLAUDE.md file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output path for the generated Dockerfile.",
    )

    args = parser.parse_args()

    if not args.manifest.exists():
        print(f"ERROR: Manifest not found: {args.manifest}", file=sys.stderr)
        sys.exit(1)

    if not args.installed_plugins.exists():
        print(
            f"ERROR: installed_plugins.json not found: {args.installed_plugins}",
            file=sys.stderr,
        )
        sys.exit(1)

    content = generate(
        manifest_path=args.manifest,
        installed_json=args.installed_plugins,
        team_claude_md_path=args.team_claude_md,
        output_path=args.output,
    )

    print(f"Generated Dockerfile: {args.output}")
    print(f"  Lines: {len(content.splitlines())}")


if __name__ == "__main__":
    main()
