#!/usr/bin/env python3
"""Tests for resolve_plugin_paths — plugin name to filesystem path resolution."""

import json
import sys
from pathlib import Path

import pytest

# Insert repo root so the import shim is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import plugins_sdlc_workflows_scripts as scripts  # noqa: E402

resolve_plugin_paths = scripts.resolve_plugin_paths


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def make_installed_plugins(
    tmp_path: Path,
    plugins: list[tuple[str, str, str]],
) -> Path:
    """Create a mock installed_plugins.json with real directories.

    Each tuple is (plugin_name, marketplace, version).
    Returns the *directory* containing installed_plugins.json.
    """
    installed: dict[str, dict[str, str]] = {}
    for name, marketplace, version in plugins:
        plugin_dir = tmp_path / "cache" / marketplace / name / version
        plugin_dir.mkdir(parents=True)
        (plugin_dir / ".claude-plugin").mkdir()
        (plugin_dir / ".claude-plugin" / "plugin.json").write_text("{}")
        (plugin_dir / "agents").mkdir()
        (plugin_dir / "skills").mkdir()
        key = f"{name}@{marketplace}"
        installed[key] = {
            "name": name,
            "marketplace": marketplace,
            "version": version,
            "installPath": str(plugin_dir),
        }
    json_path = tmp_path / "installed_plugins.json"
    json_path.write_text(json.dumps(installed))
    return tmp_path


# ---------------------------------------------------------------------------
# resolve() — single plugin lookup
# ---------------------------------------------------------------------------


class TestResolveSingle:
    """Tests for resolve_plugin_paths.resolve()."""

    def test_resolve_existing_plugin(self, tmp_path: Path) -> None:
        """A known plugin should resolve to its install path."""
        root = make_installed_plugins(
            tmp_path,
            [("sdlc-core", "ai-first-sdlc", "1.0.0")],
        )
        json_path = root / "installed_plugins.json"
        result = resolve_plugin_paths.resolve("sdlc-core@ai-first-sdlc", json_path)
        assert result is not None
        assert result.is_dir()
        assert (result / ".claude-plugin" / "plugin.json").exists()

    def test_resolve_missing_plugin_returns_none(self, tmp_path: Path) -> None:
        """An unknown plugin should return None."""
        root = make_installed_plugins(
            tmp_path,
            [("sdlc-core", "ai-first-sdlc", "1.0.0")],
        )
        json_path = root / "installed_plugins.json"
        result = resolve_plugin_paths.resolve("nonexistent@marketplace", json_path)
        assert result is None

    def test_resolve_empty_json(self, tmp_path: Path) -> None:
        """Resolving against an empty installed_plugins.json returns None."""
        root = make_installed_plugins(tmp_path, [])
        json_path = root / "installed_plugins.json"
        result = resolve_plugin_paths.resolve("sdlc-core@ai-first-sdlc", json_path)
        assert result is None

    def test_resolve_returns_path_object(self, tmp_path: Path) -> None:
        """Return type should be pathlib.Path, not str."""
        root = make_installed_plugins(
            tmp_path,
            [("sdlc-core", "ai-first-sdlc", "1.0.0")],
        )
        json_path = root / "installed_plugins.json"
        result = resolve_plugin_paths.resolve("sdlc-core@ai-first-sdlc", json_path)
        assert isinstance(result, Path)


# ---------------------------------------------------------------------------
# resolve_all() — bulk lookup
# ---------------------------------------------------------------------------


class TestResolveAll:
    """Tests for resolve_plugin_paths.resolve_all()."""

    def test_resolve_all_happy_path(self, tmp_path: Path) -> None:
        """All listed plugins resolve successfully."""
        root = make_installed_plugins(
            tmp_path,
            [
                ("sdlc-core", "ai-first-sdlc", "1.0.0"),
                ("sdlc-team-common", "ai-first-sdlc", "1.0.0"),
            ],
        )
        json_path = root / "installed_plugins.json"
        result = resolve_plugin_paths.resolve_all(
            ["sdlc-core@ai-first-sdlc", "sdlc-team-common@ai-first-sdlc"],
            json_path,
        )
        assert len(result) == 2
        assert "sdlc-core@ai-first-sdlc" in result
        assert "sdlc-team-common@ai-first-sdlc" in result
        for path in result.values():
            assert isinstance(path, Path)
            assert path.is_dir()

    def test_resolve_all_raises_on_missing(self, tmp_path: Path) -> None:
        """Should raise PluginNotFoundError listing the missing plugins."""
        root = make_installed_plugins(
            tmp_path,
            [("sdlc-core", "ai-first-sdlc", "1.0.0")],
        )
        json_path = root / "installed_plugins.json"
        with pytest.raises(resolve_plugin_paths.PluginNotFoundError) as exc_info:
            resolve_plugin_paths.resolve_all(
                ["sdlc-core@ai-first-sdlc", "nonexistent@marketplace"],
                json_path,
            )
        assert "nonexistent@marketplace" in exc_info.value.missing

    def test_resolve_all_multiple_missing(self, tmp_path: Path) -> None:
        """PluginNotFoundError.missing should contain all missing names."""
        root = make_installed_plugins(tmp_path, [])
        json_path = root / "installed_plugins.json"
        with pytest.raises(resolve_plugin_paths.PluginNotFoundError) as exc_info:
            resolve_plugin_paths.resolve_all(
                ["a@m", "b@m"],
                json_path,
            )
        assert set(exc_info.value.missing) == {"a@m", "b@m"}

    def test_resolve_all_empty_list(self, tmp_path: Path) -> None:
        """Resolving an empty list should return an empty dict."""
        root = make_installed_plugins(tmp_path, [])
        json_path = root / "installed_plugins.json"
        result = resolve_plugin_paths.resolve_all([], json_path)
        assert result == {}

    def test_plugin_not_found_error_is_exception(self) -> None:
        """PluginNotFoundError should be a subclass of Exception."""
        assert issubclass(resolve_plugin_paths.PluginNotFoundError, Exception)

    def test_plugin_not_found_error_has_missing_attribute(self) -> None:
        """PluginNotFoundError should have a .missing list attribute."""
        err = resolve_plugin_paths.PluginNotFoundError(["a", "b"])
        assert err.missing == ["a", "b"]

    def test_plugin_not_found_error_message(self) -> None:
        """PluginNotFoundError should have a useful string representation."""
        err = resolve_plugin_paths.PluginNotFoundError(["a@m", "b@m"])
        msg = str(err)
        assert "a@m" in msg
        assert "b@m" in msg
