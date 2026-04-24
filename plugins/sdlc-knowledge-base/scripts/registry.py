"""Registry loading and activation resolution for cross-library kb-query.

Phase A of EPIC #164 — see docs/superpowers/specs/2026-04-24-cross-library-kb-query-design.md.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


CURRENT_REGISTRY_VERSION = 1


@dataclass(frozen=True)
class LibrarySource:
    """A library the skill can dispatch a librarian against."""
    name: str
    type: str  # "filesystem" or "remote-agent"
    path: Optional[str] = None
    description: Optional[str] = None


@dataclass
class GlobalRegistry:
    version: int = CURRENT_REGISTRY_VERSION
    libraries: list[LibrarySource] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def load_global_registry(path: Path) -> GlobalRegistry:
    """Load the user-scope library registry from ~/.sdlc/global-libraries.json.

    Missing file is normal (no external libraries configured).
    Malformed JSON produces a warning and an empty registry.
    Unknown version produces a warning but a best-effort load.
    Duplicate library names produce a warning; first occurrence wins.
    """
    if not path.exists():
        return GlobalRegistry(libraries=[])

    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        return GlobalRegistry(
            libraries=[],
            warnings=[f"Global registry at {path} is malformed: {exc}. External libraries unavailable."],
        )

    if not isinstance(data, dict):
        return GlobalRegistry(
            libraries=[],
            warnings=[f"Global registry at {path} must be a JSON object; got {type(data).__name__}. External libraries unavailable."],
        )

    warnings: list[str] = []
    version = data.get("version", CURRENT_REGISTRY_VERSION)
    if version != CURRENT_REGISTRY_VERSION:
        warnings.append(
            f"Global registry version {version} is unknown (expected {CURRENT_REGISTRY_VERSION}); "
            "attempting best-effort load."
        )

    raw_libraries = data.get("libraries", [])
    if not isinstance(raw_libraries, list):
        warnings.append(f"'libraries' in {path} must be a list; ignoring.")
        raw_libraries = []
    seen_names: set[str] = set()
    libraries: list[LibrarySource] = []
    for entry in raw_libraries:
        if not isinstance(entry, dict):
            warnings.append("Library entry is not an object; skipping.")
            continue
        name = entry.get("name")
        if not name:
            warnings.append("Library entry missing 'name' field; skipping.")
            continue
        if name in seen_names:
            warnings.append(f"Duplicate library name '{name}'; first occurrence wins.")
            continue
        seen_names.add(name)
        libraries.append(
            LibrarySource(
                name=name,
                type=entry.get("type", "filesystem"),
                path=entry.get("path"),
                description=entry.get("description"),
            )
        )

    return GlobalRegistry(version=version, libraries=libraries, warnings=warnings)
