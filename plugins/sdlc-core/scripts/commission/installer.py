"""Bundle installer — copies a bundle's contents into a project directory.

The installer copies:
- CONSTITUTION.md from bundle root → project root
- agents/<name>.md from bundle → project/.claude/agents/<name>.md
- skills/<name>/SKILL.md from bundle → project/.claude/skills/<name>/SKILL.md
- templates/<name>.md from bundle → project/.sdlc/templates/<name>.md

By default, refuses to overwrite an existing CONSTITUTION.md (the most
likely existing artefact). Other files are overwritten if present.
Pass overwrite=True to replace an existing constitution.

The installer does NOT modify .sdlc/team-config.json — that's the
recorder's job (called separately by the skill).
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path

from .manifest import BundleManifest


class BundleInstallationError(Exception):
    """Raised when bundle installation cannot proceed."""


def _validate_safe_dst(project_dir: Path, dst: Path) -> None:
    """Raise if dst is not safely inside project_dir. Defence-in-depth against
    path-traversal in manifest-supplied filenames (e.g. "../etc/passwd")."""
    project_resolved = project_dir.resolve()
    dst_resolved = dst.resolve()
    if (
        dst_resolved != project_resolved
        and project_resolved not in dst_resolved.parents
    ):
        raise BundleInstallationError(
            f"Refusing to write outside project_dir: {dst} (resolves to {dst_resolved}; "
            f"project_dir is {project_resolved})"
        )


def _validate_manifest_entry_name(kind: str, name: str) -> None:
    """Raise if a manifest-declared file/dir name is unsafe.

    `kind` is "agent" / "skill" / "template" — used for error messages.
    """
    if not name or name in (".", ".."):
        raise BundleInstallationError(
            f"Invalid {kind} name in manifest: {name!r} (empty or relative-dir reference)"
        )
    if "/" in name or "\\" in name or "\x00" in name:
        raise BundleInstallationError(
            f"Invalid {kind} name in manifest: {name!r} (contains path separator or null byte)"
        )


@dataclass
class InstallationResult:
    """Audit log of what install_bundle did."""

    bundle_name: str
    installed_paths: list[Path] = field(default_factory=list)


def install_bundle(
    bundle_dir: Path,
    project_dir: Path,
    manifest: BundleManifest,
    overwrite: bool = False,
) -> InstallationResult:
    """Install bundle contents into project_dir.

    Returns an InstallationResult listing every path created/overwritten.
    """
    if not bundle_dir.exists() or not bundle_dir.is_dir():
        raise BundleInstallationError(f"bundle directory not found: {bundle_dir}")

    result = InstallationResult(bundle_name=manifest.name)

    # 1. Constitution
    src_constitution = bundle_dir / "CONSTITUTION.md"
    dst_constitution = project_dir / "CONSTITUTION.md"
    if src_constitution.exists():
        _validate_safe_dst(project_dir, dst_constitution)
        if dst_constitution.exists() and not overwrite:
            raise BundleInstallationError(
                f"CONSTITUTION.md already exists at {dst_constitution}; "
                "pass overwrite=True to replace"
            )
        shutil.copy2(src_constitution, dst_constitution)
        result.installed_paths.append(dst_constitution)

    # 2. Agents
    agents_src = bundle_dir / "agents"
    agents_dst = project_dir / ".claude" / "agents"
    for agent_name in manifest.agents:
        _validate_manifest_entry_name("agent", agent_name)
        src = agents_src / agent_name
        dst = agents_dst / agent_name
        _validate_safe_dst(project_dir, dst)
        if not src.exists():
            raise BundleInstallationError(
                f"Manifest declares agent {agent_name} but file not found at {src}"
            )
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        result.installed_paths.append(dst)

    # 3. Skills
    skills_src = bundle_dir / "skills"
    skills_dst = project_dir / ".claude" / "skills"
    for skill_name in manifest.skills:
        _validate_manifest_entry_name("skill", skill_name)
        src_dir = skills_src / skill_name
        dst_dir = skills_dst / skill_name
        _validate_safe_dst(project_dir, dst_dir)
        if not src_dir.exists() or not src_dir.is_dir():
            raise BundleInstallationError(
                f"Manifest declares skill {skill_name} but directory "
                f"not found at {src_dir}"
            )
        if dst_dir.exists():
            shutil.rmtree(dst_dir)
        shutil.copytree(src_dir, dst_dir)
        # Track every file we created
        for installed in dst_dir.rglob("*"):
            if installed.is_file():
                result.installed_paths.append(installed)

    # 4. Templates
    templates_src = bundle_dir / "templates"
    templates_dst = project_dir / ".sdlc" / "templates"
    for template_name in manifest.templates:
        _validate_manifest_entry_name("template", template_name)
        src = templates_src / template_name
        dst = templates_dst / template_name
        _validate_safe_dst(project_dir, dst)
        if not src.exists():
            raise BundleInstallationError(
                f"Manifest declares template {template_name} but file "
                f"not found at {src}"
            )
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        result.installed_paths.append(dst)

    return result
