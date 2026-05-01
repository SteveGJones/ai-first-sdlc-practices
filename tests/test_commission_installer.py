"""Tests for plugins.sdlc-core.scripts.commission.installer."""
from pathlib import Path

import pytest

from sdlc_core_scripts.commission.installer import (
    BundleInstallationError,
    install_bundle,
    InstallationResult,
)
from sdlc_core_scripts.commission.manifest import parse_manifest


REPO_ROOT = Path(__file__).parent.parent
SAMPLE_BUNDLE = REPO_ROOT / "skills/commission/templates/sample-bundle"


def test_install_bundle_into_empty_project_creates_expected_files(
    tmp_path: Path,
) -> None:
    """Installing the sample bundle into an empty project creates the expected files."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    manifest = parse_manifest(SAMPLE_BUNDLE / "manifest.yaml")
    result = install_bundle(SAMPLE_BUNDLE, project_dir, manifest)

    assert isinstance(result, InstallationResult)
    assert (project_dir / "CONSTITUTION.md").exists()
    assert (project_dir / ".claude" / "agents" / "sample-agent.md").exists()
    assert (project_dir / ".claude" / "skills" / "sample-skill" / "SKILL.md").exists()
    assert (project_dir / ".sdlc" / "templates" / "feature-proposal.md").exists()


def test_install_bundle_returns_list_of_installed_paths(tmp_path: Path) -> None:
    """The installer returns a list of paths it created so the caller can audit."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    manifest = parse_manifest(SAMPLE_BUNDLE / "manifest.yaml")

    result = install_bundle(SAMPLE_BUNDLE, project_dir, manifest)

    assert len(result.installed_paths) >= 4  # constitution + agent + skill + template
    assert any(p.name == "CONSTITUTION.md" for p in result.installed_paths)
    assert any(p.name == "sample-agent.md" for p in result.installed_paths)


def test_install_bundle_does_not_overwrite_existing_constitution_without_flag(
    tmp_path: Path,
) -> None:
    """If CONSTITUTION.md already exists, installer refuses without overwrite=True."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "CONSTITUTION.md").write_text("# Existing constitution\n")

    manifest = parse_manifest(SAMPLE_BUNDLE / "manifest.yaml")

    with pytest.raises(BundleInstallationError, match="CONSTITUTION.md"):
        install_bundle(SAMPLE_BUNDLE, project_dir, manifest, overwrite=False)


def test_install_bundle_overwrite_true_replaces_existing_constitution(
    tmp_path: Path,
) -> None:
    """If overwrite=True, existing CONSTITUTION.md is replaced."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "CONSTITUTION.md").write_text("# Existing constitution\n")

    manifest = parse_manifest(SAMPLE_BUNDLE / "manifest.yaml")
    install_bundle(SAMPLE_BUNDLE, project_dir, manifest, overwrite=True)

    new_text = (project_dir / "CONSTITUTION.md").read_text()
    assert "Sample Bundle Constitution" in new_text


def test_install_bundle_missing_bundle_raises(tmp_path: Path) -> None:
    """Installing a bundle whose source dir does not exist raises."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    bogus_bundle = tmp_path / "no-such-bundle"

    with pytest.raises(BundleInstallationError, match="bundle directory not found"):
        install_bundle(
            bogus_bundle,
            project_dir,
            parse_manifest(SAMPLE_BUNDLE / "manifest.yaml"),
        )


def test_install_bundle_manifest_declares_missing_agent_raises(tmp_path: Path) -> None:
    """Manifest declares an agent file that doesn't exist in the bundle → raises."""
    bundle_dir = tmp_path / "bundle"
    bundle_dir.mkdir()
    (bundle_dir / "manifest.yaml").write_text(
        "schema_version: 1\n"
        "name: single-team\n"
        "version: 0.1.0\n"
        "supported_levels: [production]\n"
        "description: Mock\n"
        "agents:\n"
        "  - missing-agent.md\n"
    )
    (bundle_dir / "agents").mkdir()  # dir exists but file does not
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    manifest = parse_manifest(bundle_dir / "manifest.yaml")

    with pytest.raises(BundleInstallationError, match="agent"):
        install_bundle(bundle_dir, project_dir, manifest)


def test_install_bundle_manifest_declares_missing_skill_raises(tmp_path: Path) -> None:
    """Manifest declares a skill dir that doesn't exist in the bundle → raises."""
    bundle_dir = tmp_path / "bundle"
    bundle_dir.mkdir()
    (bundle_dir / "manifest.yaml").write_text(
        "schema_version: 1\n"
        "name: single-team\n"
        "version: 0.1.0\n"
        "supported_levels: [production]\n"
        "description: Mock\n"
        "skills:\n"
        "  - missing-skill\n"
    )
    (bundle_dir / "skills").mkdir()  # dir exists but skill subdir does not
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    manifest = parse_manifest(bundle_dir / "manifest.yaml")

    with pytest.raises(BundleInstallationError, match="skill"):
        install_bundle(bundle_dir, project_dir, manifest)


def test_install_bundle_manifest_declares_missing_template_raises(
    tmp_path: Path,
) -> None:
    """Manifest declares a template file that doesn't exist in the bundle → raises."""
    bundle_dir = tmp_path / "bundle"
    bundle_dir.mkdir()
    (bundle_dir / "manifest.yaml").write_text(
        "schema_version: 1\n"
        "name: single-team\n"
        "version: 0.1.0\n"
        "supported_levels: [production]\n"
        "description: Mock\n"
        "templates:\n"
        "  - missing-template.md\n"
    )
    (bundle_dir / "templates").mkdir()  # dir exists but file does not
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    manifest = parse_manifest(bundle_dir / "manifest.yaml")

    with pytest.raises(BundleInstallationError, match="template"):
        install_bundle(bundle_dir, project_dir, manifest)


def test_install_bundle_rejects_path_traversal_in_agent_name(tmp_path: Path) -> None:
    """A manifest declaring an agent name with .. is rejected."""
    bundle_dir = tmp_path / "bundle"
    bundle_dir.mkdir()
    (bundle_dir / "manifest.yaml").write_text(
        "schema_version: 1\n"
        "name: single-team\n"
        "version: 0.1.0\n"
        "supported_levels: [production]\n"
        "description: Mock\n"
        "agents:\n"
        "  - ../escape.md\n"
    )
    (bundle_dir / "agents").mkdir()
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    manifest = parse_manifest(bundle_dir / "manifest.yaml")

    with pytest.raises(BundleInstallationError, match="path separator"):
        install_bundle(bundle_dir, project_dir, manifest)


def test_validate_safe_dst_rejects_path_outside_project_dir(tmp_path: Path) -> None:
    """Direct test of the _validate_safe_dst helper (defence-in-depth layer 2).

    The path-traversal regression test above exercises the name guard
    (layer 1). This test exercises the dst guard (layer 2) directly,
    in case a future refactor weakens the name guard.
    """
    from sdlc_core_scripts.commission.installer import _validate_safe_dst

    project_dir = tmp_path / "project"
    project_dir.mkdir()

    # Path that resolves outside project_dir
    escape_path = project_dir / ".." / "escape.md"

    with pytest.raises(BundleInstallationError, match="Refusing to write outside"):
        _validate_safe_dst(project_dir, escape_path)


def test_validate_safe_dst_accepts_path_inside_project_dir(tmp_path: Path) -> None:
    """The dst guard accepts paths that resolve inside project_dir."""
    from sdlc_core_scripts.commission.installer import _validate_safe_dst

    project_dir = tmp_path / "project"
    project_dir.mkdir()

    # Both an existing-parent path and a not-yet-created descendant should pass
    safe_path = project_dir / ".claude" / "agents" / "ok.md"
    _validate_safe_dst(project_dir, safe_path)  # should not raise

    # The project_dir itself is also not "outside" (resolves equal)
    _validate_safe_dst(project_dir, project_dir)  # should not raise
