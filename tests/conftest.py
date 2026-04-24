"""Shared pytest configuration.

Registers the ``sdlc_workflows_scripts`` package so tests can import
plugin scripts with a real package name:

    from sdlc_workflows_scripts import resolve_credentials

The scripts live under ``plugins/sdlc-workflows/scripts/`` -- a path
that isn't a valid Python identifier, so we bind the directory to a
clean package name at import time.  This replaces the earlier
``plugins_sdlc_workflows_scripts.py`` shim at the repo root.

Also registers ``sdlc_knowledge_base_scripts`` from
``plugins/sdlc-knowledge-base/scripts/`` using the same pattern.

If a real Python environment is later adopted, the plugins carry a
``pyproject.toml`` and can be installed editable with
``pip install -e plugins/<plugin>/`` -- which registers the
same package name under the same layout.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _register_scripts_package(plugin_dir_name: str, package_name: str) -> None:
    """Register a plugin's scripts/ directory as an importable package."""
    if package_name in sys.modules:
        return
    scripts_dir = (
        Path(__file__).resolve().parent.parent
        / "plugins"
        / plugin_dir_name
        / "scripts"
    )
    init_py = scripts_dir / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        package_name,
        init_py,
        submodule_search_locations=[str(scripts_dir)],
    )
    if spec is None or spec.loader is None:
        msg = f"Could not load package spec for {package_name} from {init_py}"
        raise RuntimeError(msg)
    package = importlib.util.module_from_spec(spec)
    sys.modules[package_name] = package
    spec.loader.exec_module(package)


_register_scripts_package("sdlc-workflows", "sdlc_workflows_scripts")
_register_scripts_package("sdlc-knowledge-base", "sdlc_knowledge_base_scripts")
