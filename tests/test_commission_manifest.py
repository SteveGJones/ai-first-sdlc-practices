"""Tests for plugins.sdlc-core.scripts.commission.manifest."""
from pathlib import Path

import pytest

from sdlc_core_scripts.commission.manifest import (
    BundleManifest,
    ManifestValidationError,
    parse_manifest,
)


def test_parse_manifest_minimal_valid(tmp_path: Path) -> None:
    """A manifest with only required fields parses successfully."""
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(
        "schema_version: 1\n"
        "name: single-team\n"
        "version: 0.1.0\n"
        "supported_levels: [prototype, production]\n"
        "description: Standard team SDLC\n"
    )

    manifest = parse_manifest(manifest_path)

    assert isinstance(manifest, BundleManifest)
    assert manifest.name == "single-team"
    assert manifest.version == "0.1.0"
    assert manifest.supported_levels == ["prototype", "production"]
    assert manifest.depends_on == ["sdlc-core"]  # default
    assert manifest.agents == []
    assert manifest.skills == []


def test_parse_manifest_missing_required_field(tmp_path: Path) -> None:
    """Missing a required field raises ManifestValidationError."""
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(
        "schema_version: 1\n"
        "name: single-team\n"
        "supported_levels: [prototype]\n"
        "description: missing version field\n"
    )

    with pytest.raises(ManifestValidationError, match="version"):
        parse_manifest(manifest_path)


def test_parse_manifest_unknown_option_name(tmp_path: Path) -> None:
    """An unknown option name raises ManifestValidationError."""
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(
        "schema_version: 1\n"
        "name: not-a-real-option\n"
        "version: 0.1.0\n"
        "supported_levels: [production]\n"
        "description: Bogus\n"
    )

    with pytest.raises(ManifestValidationError, match="not-a-real-option"):
        parse_manifest(manifest_path)


def test_parse_manifest_unsupported_level(tmp_path: Path) -> None:
    """An unsupported level raises ManifestValidationError."""
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(
        "schema_version: 1\n"
        "name: single-team\n"
        "version: 0.1.0\n"
        "supported_levels: [unrealistic-tier]\n"
        "description: Bogus\n"
    )

    with pytest.raises(ManifestValidationError, match="unrealistic-tier"):
        parse_manifest(manifest_path)


def test_parse_manifest_with_phase_e_reserved_fields(tmp_path: Path) -> None:
    """Reserved Phase E fields parse without validation but are preserved on the dataclass."""
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(
        "schema_version: 1\n"
        "name: assured\n"
        "version: 0.1.0\n"
        "supported_levels: [enterprise]\n"
        "description: Assured bundle\n"
        "decomposition_support: true\n"
        "id_format: positional\n"
        "paths_split_supported: true\n"
        "known_violations_field: true\n"
        "anaemic_context_opt_out: true\n"
    )

    manifest = parse_manifest(manifest_path)

    assert manifest.decomposition_support is True
    assert manifest.id_format == "positional"
    assert manifest.paths_split_supported is True
    assert manifest.known_violations_field is True
    assert manifest.anaemic_context_opt_out is True


def test_parse_manifest_malformed_yaml_raises_validation_error(tmp_path: Path) -> None:
    """A malformed YAML manifest raises ManifestValidationError, not YAMLError."""
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text("not: valid: yaml: at: all:\n  - bad")

    with pytest.raises(ManifestValidationError, match="not valid YAML"):
        parse_manifest(manifest_path)


def test_parse_manifest_invalid_id_format(tmp_path: Path) -> None:
    """An invalid id_format value raises ManifestValidationError."""
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(
        "schema_version: 1\n"
        "name: assured\n"
        "version: 0.1.0\n"
        "supported_levels: [enterprise]\n"
        "description: Bogus id_format\n"
        "id_format: bogus-format\n"
    )

    with pytest.raises(ManifestValidationError, match="id_format"):
        parse_manifest(manifest_path)
