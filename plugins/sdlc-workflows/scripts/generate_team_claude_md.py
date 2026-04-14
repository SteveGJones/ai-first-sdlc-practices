#!/usr/bin/env python3
"""Generate team-specific CLAUDE.md files from team manifests.

Produces a Markdown document that establishes team identity, lists available
agents and skills, and includes constraints.  Descriptions are sanitised
to block prompt-injection attempts via directive language.
"""

from __future__ import annotations

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Sanitisation
# ---------------------------------------------------------------------------

DIRECTIVE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(
        r"(?i)\b(ignore|override|disregard|bypass|skip|do not follow)\b"
        r".*\b(instructions?|constraints?|rules?|previous|above)\b"
    ),
    re.compile(
        r"(?i)\b(you are free|you have full access|no restrictions?|unrestricted)\b"
    ),
]

_SANITISED_NOTICE = "[description removed: failed sanitisation]"


def sanitise_description(text: str | None) -> str:
    """Return *text* unchanged if clean, or a sanitisation notice if tainted.

    Checks for directive language that could hijack the team's operating
    context.  Returns an empty string for ``None`` or empty input.
    """
    if text is None:
        return ""
    if not text:
        return ""
    for pattern in DIRECTIVE_PATTERNS:
        if pattern.search(text):
            return _SANITISED_NOTICE
    return text


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------


def _agent_display_name(qualified: str) -> str:
    """Extract the display name from a qualified agent reference.

    ``sdlc-team-security:security-architect`` -> ``security-architect``
    """
    if ":" in qualified:
        return qualified.split(":", 1)[1]
    return qualified


def _skill_display_name(qualified: str) -> str:
    """Extract the display name from a qualified skill reference.

    ``sdlc-core:validate`` -> ``validate``
    """
    if ":" in qualified:
        return qualified.split(":", 1)[1]
    return qualified


def generate(
    manifest: dict[str, object],
    agent_descriptions: dict[str, str],
    skill_descriptions: dict[str, str],
) -> str:
    """Generate a team CLAUDE.md string from *manifest* and lookup dicts.

    Parameters
    ----------
    manifest:
        Parsed team manifest dictionary.
    agent_descriptions:
        Map of qualified agent name to human-readable description.
    skill_descriptions:
        Map of qualified skill name to human-readable description.

    Returns
    -------
    str
        The generated Markdown content.
    """
    name: str = str(manifest.get("name", "unnamed-team"))
    raw_description: str | None = manifest.get("description")  # type: ignore[assignment]
    description = sanitise_description(raw_description)

    agents: list[str] = list(manifest.get("agents", []))  # type: ignore[arg-type]
    skills: list[str] = list(manifest.get("skills", []))  # type: ignore[arg-type]

    lines: list[str] = []

    # Header
    lines.append(f"# Team: {name}")
    lines.append("")
    if description:
        lines.append(description)
        lines.append("")

    # Role
    lines.append("## Role")
    lines.append("")
    lines.append(
        f"You are operating as part of the **{name}** delegation team."
    )
    lines.append(
        "Your available specialists and capabilities are listed below."
    )
    lines.append("Stay within your team's scope.")
    lines.append("")

    # Agents
    lines.append("## Available Agents")
    lines.append("")
    if agents:
        for agent_ref in agents:
            display = _agent_display_name(agent_ref)
            desc = agent_descriptions.get(agent_ref, "")
            if desc:
                lines.append(f"- {display} -- {desc}")
            else:
                lines.append(f"- {display}")
    else:
        lines.append("_No agents configured._")
    lines.append("")

    # Skills
    lines.append("## Available Skills")
    lines.append("")
    if skills:
        for skill_ref in skills:
            display = _skill_display_name(skill_ref)
            desc = skill_descriptions.get(skill_ref, "")
            if desc:
                lines.append(f"- {display} -- {desc}")
            else:
                lines.append(f"- {display}")
    else:
        lines.append("_No skills configured._")
    lines.append("")

    # Constraints
    lines.append("## Constraints")
    lines.append("")
    lines.append(
        "- Focus on your team's domain."
        " Do not produce recommendations outside your scope."
    )
    lines.append(
        "- Use the agents and skills listed above. They are your team."
    )
    lines.append("- Follow the project rules in CONSTITUTION.md.")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Concatenation
# ---------------------------------------------------------------------------


def concatenate(project_claude_path: Path, team_md: str) -> str:
    """Combine a project CLAUDE.md with generated team context.

    The project rules appear first, followed by a separator, then the
    team-specific section.

    Parameters
    ----------
    project_claude_path:
        Path to the existing project CLAUDE.md.
    team_md:
        Generated team Markdown content (from :func:`generate`).

    Returns
    -------
    str
        The combined Markdown document.
    """
    project_content = project_claude_path.read_text()
    separator = "\n\n---\n\n<!-- BEGIN GENERATED TEAM CONTEXT -->\n\n"
    return project_content.rstrip() + separator + team_md
