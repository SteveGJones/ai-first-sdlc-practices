"""Registry loading and activation resolution for cross-library kb-query.

Phase A of EPIC #164 — see
docs/superpowers/specs/2026-04-24-cross-library-kb-query-design.md.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


CURRENT_REGISTRY_VERSION = 1

KNOWN_LIBRARY_TYPES = {"filesystem", "remote-agent"}


def _coerce_version(
    raw_version: object, context_label: str, warnings: list[str]
) -> int:
    """Coerce raw_version to int, appending a warning for non-int inputs.

    Returns CURRENT_REGISTRY_VERSION as a fallback for non-coercible values.
    Emits a warning when the type isn't int (including string-coerced ints
    like "1"), so callers can see when the schema is being loose.
    """
    try:
        version = int(raw_version)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        warnings.append(
            f"{context_label}: version field must be an integer, "
            f"got {type(raw_version).__name__}; "
            f"treating as {CURRENT_REGISTRY_VERSION}."
        )
        return CURRENT_REGISTRY_VERSION
    if not isinstance(raw_version, int):
        warnings.append(
            f"{context_label}: version field must be an integer, "
            f"got {type(raw_version).__name__}; "
            f"treating as {version}."
        )
    return version


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
            warnings=[
                f"Global registry at {path} is malformed: {exc}. "
                "External libraries unavailable."
            ],
        )

    if not isinstance(data, dict):
        return GlobalRegistry(
            libraries=[],
            warnings=[
                f"Global registry at {path} must be a JSON object; "
                f"got {type(data).__name__}. External libraries unavailable."
            ],
        )

    warnings: list[str] = []

    raw_version = data.get("version", CURRENT_REGISTRY_VERSION)
    version = _coerce_version(raw_version, "Global registry", warnings)
    if version != CURRENT_REGISTRY_VERSION:
        warnings.append(
            f"Global registry version {version} is unknown "
            f"(expected {CURRENT_REGISTRY_VERSION}); "
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
        raw_type = entry.get("type", "filesystem")
        if raw_type not in KNOWN_LIBRARY_TYPES:
            warnings.append(
                f"Library '{name}' has unknown type '{raw_type}'; skipping."
            )
            continue
        seen_names.add(name)
        libraries.append(
            LibrarySource(
                name=name,
                type=raw_type,
                path=entry.get("path"),
                description=entry.get("description"),
            )
        )

    return GlobalRegistry(version=version, libraries=libraries, warnings=warnings)


@dataclass
class ProjectActivation:
    version: int = CURRENT_REGISTRY_VERSION
    activated_sources: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def load_project_activation(path: Path) -> ProjectActivation:
    """Load project-level activation from .sdlc/libraries.json.

    Missing file is normal (local-only). Malformed JSON produces a
    warning and empty activation. Unknown names are validated later
    against the global registry, not here.
    """
    if not path.exists():
        return ProjectActivation(activated_sources=[])

    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        return ProjectActivation(
            activated_sources=[],
            warnings=[
                f"Project activation at {path} is malformed: {exc}. "
                "No external libraries activated."
            ],
        )

    if not isinstance(data, dict):
        return ProjectActivation(
            activated_sources=[],
            warnings=[
                f"Project activation at {path} must be a JSON object; "
                f"got {type(data).__name__}. No external libraries activated."
            ],
        )

    warnings: list[str] = []

    raw_version = data.get("version", CURRENT_REGISTRY_VERSION)
    version = _coerce_version(raw_version, "Project activation", warnings)
    if version != CURRENT_REGISTRY_VERSION:
        warnings.append(
            f"Project activation version {version} is unknown "
            f"(expected {CURRENT_REGISTRY_VERSION})."
        )

    sources = data.get("activated_sources", [])
    if not isinstance(sources, list):
        return ProjectActivation(
            version=version,
            activated_sources=[],
            warnings=warnings
            + [f"'activated_sources' must be a list, got {type(sources).__name__}."],
        )

    return ProjectActivation(
        version=version, activated_sources=list(sources), warnings=warnings
    )


@dataclass
class DispatchList:
    """Result of resolving activated sources into a dispatch list."""

    sources: list[LibrarySource] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    is_empty_error: bool = (
        False  # True when no local + no externals → user-facing error
    )


def resolve_dispatch_list(
    global_registry: GlobalRegistry,
    activation: ProjectActivation,
    project_library_path: Path,
) -> DispatchList:
    """Resolve activated source names against the global registry.

    Prepends an implicit `local` source when project_library_path exists.
    Skips unknown names with warnings. Skips remote-agent types with
    warnings (deferred to future EPIC). Returns is_empty_error=True when
    no sources resolve at all (callers should emit the kb-init recommendation).
    """
    warnings: list[str] = []
    sources: list[LibrarySource] = []

    # Implicit local source if library directory exists
    if project_library_path.exists() and project_library_path.is_dir():
        sources.append(
            LibrarySource(
                name="local", type="filesystem", path=str(project_library_path)
            )
        )

    # Index global registry by name
    by_name = {lib.name: lib for lib in global_registry.libraries}

    for name in activation.activated_sources:
        entry = by_name.get(name)
        if entry is None:
            warnings.append(
                f"Activated source '{name}' not found in global registry. Skipping."
            )
            continue
        if entry.type == "remote-agent":
            warnings.append(
                f"Source '{name}' is type 'remote-agent' "
                "(planned for future release). Skipping."
            )
            continue
        if entry.type != "filesystem":
            warnings.append(
                f"Source '{name}' has unknown type '{entry.type}'. Skipping."
            )
            continue
        sources.append(entry)

    return DispatchList(
        sources=sources,
        warnings=warnings,
        is_empty_error=(len(sources) == 0),
    )
