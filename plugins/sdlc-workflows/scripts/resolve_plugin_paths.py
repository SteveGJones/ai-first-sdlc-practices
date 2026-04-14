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


def _load_installed(installed_json: Path) -> dict[str, list[dict[str, str]]]:
    """Load installed_plugins.json and return the plugins mapping.

    The file has two known formats:
    - v2 (current): ``{"version": 2, "plugins": {"name@marketplace": [{"scope": ..., "installPath": ...}]}}``
    - v1 (legacy/tests): ``{"name@marketplace": {"name": ..., "installPath": ...}}``

    Returns a normalised dict: ``key -> [{"installPath": ...}]``
    """
    with installed_json.open() as fh:
        raw = json.load(fh)

    if isinstance(raw, dict) and "version" in raw and "plugins" in raw:
        return raw["plugins"]

    # Legacy / test format: flat dict of key -> entry_dict
    result: dict[str, list[dict[str, str]]] = {}
    for key, val in raw.items():
        if isinstance(val, dict):
            result[key] = [val]
        elif isinstance(val, list):
            result[key] = val
    return result


def _build_name_lookup(
    plugins: dict[str, list[dict[str, str]]],
) -> dict[str, Path]:
    """Build a bare-name -> install path lookup from the plugins dict.

    Keys in installed_plugins.json are ``"name@marketplace"``.
    This builds a lookup by the bare name (part before ``@``).
    If multiple entries exist, the first with a valid path wins.
    """
    lookup: dict[str, Path] = {}
    for key, entries in plugins.items():
        bare_name = key.split("@")[0] if "@" in key else key
        if bare_name in lookup:
            continue
        for entry in entries if isinstance(entries, list) else [entries]:
            install_path = entry.get("installPath")
            if install_path:
                lookup[bare_name] = Path(install_path)
                break
    return lookup


def resolve(plugin_name: str, installed_json: Path) -> Path | None:
    """Resolve a plugin name to its install path.

    Parameters
    ----------
    plugin_name:
        Bare plugin name (e.g. ``"sdlc-core"``) or full key
        (e.g. ``"sdlc-core@ai-first-sdlc"``).
    installed_json:
        Path to the ``installed_plugins.json`` file.

    Returns
    -------
    Path | None
        The resolved directory, or ``None`` if the plugin is not installed.
    """
    plugins = _load_installed(installed_json)
    lookup = _build_name_lookup(plugins)

    # Try bare name first, then full key
    bare = plugin_name.split("@")[0] if "@" in plugin_name else plugin_name
    return lookup.get(bare)


def resolve_all(
    plugin_names: list[str],
    installed_json: Path,
) -> dict[str, Path]:
    """Resolve multiple plugin names to their install paths.

    Parameters
    ----------
    plugin_names:
        List of bare names (e.g. ``["sdlc-core", "mongodb-plugin"]``)
        or full keys.
    installed_json:
        Path to the ``installed_plugins.json`` file.

    Returns
    -------
    dict[str, Path]
        Mapping from plugin name to resolved directory.

    Raises
    ------
    PluginNotFoundError
        If any of the requested plugins are not installed.
    """
    if not plugin_names:
        return {}

    plugins = _load_installed(installed_json)
    lookup = _build_name_lookup(plugins)

    resolved: dict[str, Path] = {}
    missing: list[str] = []

    for name in plugin_names:
        bare = name.split("@")[0] if "@" in name else name
        if bare in lookup:
            resolved[name] = lookup[bare]
        else:
            missing.append(name)

    if missing:
        raise PluginNotFoundError(missing)

    return resolved
