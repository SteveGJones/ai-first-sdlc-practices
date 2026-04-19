#!/usr/bin/env python3
"""Generate team-specific CLAUDE.md files from team manifests.

Produces a Markdown document that establishes team identity, lists available
agents and skills, and includes constraints.  Descriptions are sanitised
to block prompt-injection attempts via directive language.
"""

from __future__ import annotations

import logging
import re
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

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

# Cross-model prompt-injection markers.  A plugin author or an attacker
# that landed description text could embed role-switching tokens that
# some model families honour as genuine turn boundaries.  These are
# checked with a simple literal scan (case-insensitive, substring) on
# top of DIRECTIVE_PATTERNS — see sanitise_description.
# S-M-7: Cross-model PI markers.
CROSS_MODEL_MARKERS: tuple[str, ...] = (
    "<|im_start|>",
    "<|im_end|>",
    "<|system|>",
    "<|user|>",
    "<|assistant|>",
    "[INST]",
    "[/INST]",
    "<<SYS>>",
    "<</SYS>>",
    "<|endoftext|>",
    "<|eot_id|>",
    "<|start_header_id|>",
    "<|end_header_id|>",
)

_SANITISED_NOTICE = "[description removed: failed sanitisation]"


def sanitise_description(text: str | None) -> str:
    """Return *text* unchanged if clean, or a sanitisation notice if tainted.

    Checks for directive language and cross-model role-switching markers
    that could hijack the team's operating context.  Returns an empty
    string for ``None`` or empty input.
    """
    if text is None:
        return ""
    if not text:
        return ""
    logger.debug("Sanitising description", extra={"length": len(text)})
    for pattern in DIRECTIVE_PATTERNS:
        if pattern.search(text):
            logger.warning(
                "Description rejected by directive-pattern match — security event",
                extra={"length": len(text)},
            )
            return _SANITISED_NOTICE
    lower_text = text.lower()
    for marker in CROSS_MODEL_MARKERS:
        if marker.lower() in lower_text:
            logger.warning(
                "Description rejected by cross-model marker — security event",
                extra={"length": len(text), "marker": marker},
            )
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
    if raw_description and description != raw_description:
        logger.warning(
            "Team description sanitised — security-relevant event",
            extra={"team": name},
        )

    agents: list[str] = list(manifest.get("agents", []))  # type: ignore[arg-type]
    skills: list[str] = list(manifest.get("skills", []))  # type: ignore[arg-type]
    logger.info(
        "Generating team CLAUDE.md",
        extra={"team": name, "agent_count": len(agents), "skill_count": len(skills)},
    )

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
            raw_desc = agent_descriptions.get(agent_ref, "")
            desc = sanitise_description(raw_desc) if raw_desc else ""
            if raw_desc and desc != raw_desc:
                logger.warning(
                    "Agent description sanitised — security-relevant event",
                    extra={"team": name, "agent": agent_ref},
                )
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
            raw_desc = skill_descriptions.get(skill_ref, "")
            desc = sanitise_description(raw_desc) if raw_desc else ""
            if raw_desc and desc != raw_desc:
                logger.warning(
                    "Skill description sanitised — security-relevant event",
                    extra={"team": name, "skill": skill_ref},
                )
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

    logger.info(
        "Team CLAUDE.md generated",
        extra={"team": name, "line_count": len(lines)},
    )
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
    logger.info(
        "Concatenating project CLAUDE.md with team context",
        extra={"project_claude_path": str(project_claude_path)},
    )
    project_content = project_claude_path.read_text()
    separator = "\n\n---\n\n<!-- BEGIN GENERATED TEAM CONTEXT -->\n\n"
    result = project_content.rstrip() + separator + team_md
    logger.debug(
        "Concatenation complete",
        extra={"total_length": len(result)},
    )
    return result


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    logger.info("generate_team_claude_md CLI start")

    try:
        import yaml
    except ImportError:
        logger.error("PyYAML not installed")
        print("ERROR: PyYAML not installed. Run: pip install pyyaml", file=sys.stderr)
        sys.exit(2)

    parser = argparse.ArgumentParser(description="Generate team CLAUDE.md from manifest")
    parser.add_argument("manifest", type=Path, help="Path to team manifest YAML")
    parser.add_argument("--output", type=Path, required=True, help="Output path for generated CLAUDE.md")
    parser.add_argument("--project-claude", type=Path, help="Project CLAUDE.md to concatenate with")
    args = parser.parse_args()

    with open(args.manifest) as f:
        manifest_data = yaml.safe_load(f)

    content = generate(manifest_data, {}, {})

    if args.project_claude and args.project_claude.exists():
        content = concatenate(args.project_claude, content)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(content)
    print(f"Generated: {args.output}")
