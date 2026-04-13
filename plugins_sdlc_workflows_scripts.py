"""Import shim -- allows tests to import plugin scripts by dotted path."""

import importlib.util
import sys
from pathlib import Path

_scripts = Path(__file__).parent / "plugins" / "sdlc-workflows" / "scripts"
for py in _scripts.glob("*.py"):
    name = py.stem
    spec = importlib.util.spec_from_file_location(name, py)
    mod = importlib.util.module_from_spec(spec)
    if spec.loader is not None:
        spec.loader.exec_module(mod)
    setattr(sys.modules[__name__], name, mod)
