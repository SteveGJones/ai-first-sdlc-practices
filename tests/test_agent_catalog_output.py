"""The agent-catalog generator output must already satisfy the pre-commit hooks.

.github/workflows/agent-catalog-update.yml regenerates AGENT-CATALOG.json and
AGENT-INDEX.md and commits them to main. With ``pre-commit run --all-files`` a
blocking CI check, output that the whitespace/JSON hooks would rewrite turns
the next unrelated PR red.
"""

import importlib.util
import json
import sys
from pathlib import Path
from typing import Tuple

import pytest

_REPO = Path(__file__).resolve().parents[1]
_SCRIPT = _REPO / "tools" / "automation" / "build-agent-catalog.py"
spec = importlib.util.spec_from_file_location("build_agent_catalog", _SCRIPT)
assert spec is not None and spec.loader is not None
build_agent_catalog = importlib.util.module_from_spec(spec)
sys.modules["build_agent_catalog"] = build_agent_catalog
spec.loader.exec_module(build_agent_catalog)

_AGENT = """\
---
name: demo-agent
description: A demo agent for the catalog test.
examples:
  - context: Reviewing a pull request
---

# Demo Agent

Demo body about python and testing.
"""


def _generate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Tuple[str, str]:
    agent_dir = tmp_path / "agents" / "core"
    agent_dir.mkdir(parents=True)
    (agent_dir / "demo-agent.md").write_text(_AGENT)
    monkeypatch.chdir(tmp_path)
    build_agent_catalog.build_catalog()
    return (
        (tmp_path / "AGENT-CATALOG.json").read_text(encoding="utf-8"),
        (tmp_path / "AGENT-INDEX.md").read_text(encoding="utf-8"),
    )


def _assert_hook_clean(text: str) -> None:
    assert text.endswith("\n")
    assert not text.endswith("\n\n")
    for line in text.splitlines():
        assert line == line.rstrip(), f"trailing whitespace: {line!r}"


def test_catalog_json_is_a_fixed_point_of_the_json_hook(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    text, _ = _generate(tmp_path, monkeypatch)
    _assert_hook_clean(text)
    assert text == json.dumps(json.loads(text), indent=2, ensure_ascii=False) + "\n"


def test_index_markdown_is_a_fixed_point_of_the_whitespace_hooks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, index = _generate(tmp_path, monkeypatch)
    assert "demo-agent" in index
    _assert_hook_clean(index)
