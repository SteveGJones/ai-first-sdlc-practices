"""Shared pytest configuration.

Registers the ``sdlc_workflows_scripts`` package so tests can import
plugin scripts with a real package name:

    from sdlc_workflows_scripts import resolve_credentials

The scripts live under ``plugins/sdlc-workflows/scripts/`` -- a path
that isn't a valid Python identifier, so we bind the directory to a
clean package name at import time.  This replaces the earlier
``plugins_sdlc_workflows_scripts.py`` shim at the repo root.

If a real Python environment is later adopted, the plugin carries a
``pyproject.toml`` and can be installed editable with
``pip install -e plugins/sdlc-workflows/`` -- which registers the
same package name under the same layout.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_SCRIPTS_DIR = (
    Path(__file__).resolve().parent.parent
    / "plugins"
    / "sdlc-workflows"
    / "scripts"
)

_PACKAGE_NAME = "sdlc_workflows_scripts"

if _PACKAGE_NAME not in sys.modules:
    init_py = _SCRIPTS_DIR / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        _PACKAGE_NAME,
        init_py,
        submodule_search_locations=[str(_SCRIPTS_DIR)],
    )
    if spec is None or spec.loader is None:
        msg = f"Could not load package spec for {_PACKAGE_NAME} from {init_py}"
        raise RuntimeError(msg)
    package = importlib.util.module_from_spec(spec)
    sys.modules[_PACKAGE_NAME] = package
    spec.loader.exec_module(package)
