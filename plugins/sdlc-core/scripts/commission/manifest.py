"""Bundle manifest parsing and validation for the option bundle contract.

Reads `manifest.yaml` from a bundle directory and returns a validated
`BundleManifest`. Rejects manifests with missing required fields, unknown
option names, or unsupported levels.

Reserved Phase E fields (decomposition_support, id_format,
paths_split_supported, known_violations_field, anaemic_context_opt_out)
are preserved on the dataclass but not semantically validated; that's
Phase E's job.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


VALID_OPTIONS = {"solo", "single-team", "programme", "assured"}
VALID_LEVELS = {"prototype", "production", "enterprise"}
VALID_ID_FORMATS = {"positional", "named"}


class ManifestValidationError(Exception):
    """Raised when a bundle manifest fails validation."""


@dataclass
class BundleManifest:
    """Parsed and validated bundle manifest."""

    schema_version: int
    name: str
    version: str
    supported_levels: list[str]
    description: str
    depends_on: list[str] = field(default_factory=lambda: ["sdlc-core"])
    agents: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    templates: list[str] = field(default_factory=list)
    validators: dict = field(default_factory=dict)

    # Reserved Phase E fields
    decomposition_support: bool = False
    id_format: Optional[str] = None
    paths_split_supported: bool = False
    known_violations_field: bool = False
    anaemic_context_opt_out: bool = False


def parse_manifest(path: Path) -> BundleManifest:
    """Parse and validate a bundle manifest at the given path."""
    if not path.exists():
        raise ManifestValidationError(f"Manifest file not found: {path}")

    try:
        raw = yaml.safe_load(path.read_text())
    except yaml.YAMLError as e:
        raise ManifestValidationError(f"Manifest is not valid YAML: {path}: {e}") from e
    if not isinstance(raw, dict):
        raise ManifestValidationError(
            f"Manifest must be a YAML mapping at top level: {path}"
        )

    # Required fields
    for required in (
        "schema_version",
        "name",
        "version",
        "supported_levels",
        "description",
    ):
        if required not in raw:
            raise ManifestValidationError(
                f"Manifest missing required field '{required}': {path}"
            )

    # Validate name
    if raw["name"] not in VALID_OPTIONS:
        raise ManifestValidationError(
            f"Manifest 'name' must be one of {sorted(VALID_OPTIONS)}, "
            f"got: {raw['name']}"
        )

    # Validate levels
    levels = raw["supported_levels"]
    if not isinstance(levels, list) or not levels:
        raise ManifestValidationError(
            f"Manifest 'supported_levels' must be a non-empty list: {path}"
        )
    for level in levels:
        if level not in VALID_LEVELS:
            raise ManifestValidationError(
                f"Manifest level '{level}' not in {sorted(VALID_LEVELS)}: {path}"
            )

    # Validate id_format if present
    if "id_format" in raw and raw["id_format"] not in VALID_ID_FORMATS:
        raise ManifestValidationError(
            f"Manifest 'id_format' must be one of {sorted(VALID_ID_FORMATS)}, "
            f"got: {raw['id_format']}"
        )

    return BundleManifest(
        schema_version=raw["schema_version"],
        name=raw["name"],
        version=raw["version"],
        supported_levels=raw["supported_levels"],
        description=raw["description"],
        depends_on=raw.get("depends_on", ["sdlc-core"]),
        agents=raw.get("agents", []),
        skills=raw.get("skills", []),
        templates=raw.get("templates", []),
        validators=raw.get("validators", {}),
        decomposition_support=raw.get("decomposition_support", False),
        id_format=raw.get("id_format"),
        paths_split_supported=raw.get("paths_split_supported", False),
        known_violations_field=raw.get("known_violations_field", False),
        anaemic_context_opt_out=raw.get("anaemic_context_opt_out", False),
    )
