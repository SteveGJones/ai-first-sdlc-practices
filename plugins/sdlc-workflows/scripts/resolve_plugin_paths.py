#!/usr/bin/env python3
"""Resolve plugin names to installed filesystem paths.

Claude Code stores plugins at:
    ~/.claude/plugins/cache/<marketplace>/<plugin-name>/<version>/

The mapping is persisted in ``installed_plugins.json`` with keys like
``"sdlc-core@ai-first-sdlc"`` and ``installPath`` values pointing to
the real directory on disk.

Public API
----------
resolve(plugin_name, installed_json) -> Path | None
    Single plugin lookup.

resolve_all(plugin_names, installed_json) -> dict[str, Path]
    Bulk lookup.  Raises ``PluginNotFoundError`` if any are missing.
"""

from __future__ import annotations

import json
from pathlib import Path


class PluginNotFoundError(Exception):
    """Raised when one or more required plugins cannot be resolved.

    Attributes
    ----------
    missing : list[str]
        Plugin keys that could not be found in installed_plugins.json.
    """

    def __init__(self, missing: list[str]) -> None:
        self.missing = missing
        names = ", ".join(missing)
        super().__init__(f"Plugins not found in installed_plugins.json: {names}")


def _load_installed(installed_json: Path) -> dict[str, dict[str, str]]:
    """Load and return the installed_plugins.json content."""
    with installed_json.open() as fh:
        data: dict[str, dict[str, str]] = json.load(fh)
    return data


def resolve(plugin_name: str, installed_json: Path) -> Path | None:
    """Resolve a single plugin key to its install path.

    Parameters
    ----------
    plugin_name:
        Key in the form ``"<name>@<marketplace>"``.
    installed_json:
        Path to the ``installed_plugins.json`` file.

    Returns
    -------
    Path | None
        The resolved directory, or ``None`` if the plugin is not installed.
    """
    data = _load_installed(installed_json)
    entry = data.get(plugin_name)
    if entry is None:
        return None
    install_path = entry.get("installPath")
    if install_path is None:
        return None
    return Path(install_path)


def resolve_all(
    plugin_names: list[str],
    installed_json: Path,
) -> dict[str, Path]:
    """Resolve multiple plugin keys to their install paths.

    Parameters
    ----------
    plugin_names:
        List of keys in the form ``"<name>@<marketplace>"``.
    installed_json:
        Path to the ``installed_plugins.json`` file.

    Returns
    -------
    dict[str, Path]
        Mapping from plugin key to resolved directory.

    Raises
    ------
    PluginNotFoundError
        If any of the requested plugins are not installed.
    """
    if not plugin_names:
        return {}

    data = _load_installed(installed_json)
    resolved: dict[str, Path] = {}
    missing: list[str] = []

    for name in plugin_names:
        entry = data.get(name)
        if entry is None or "installPath" not in entry:
            missing.append(name)
        else:
            resolved[name] = Path(entry["installPath"])

    if missing:
        raise PluginNotFoundError(missing)

    return resolved
