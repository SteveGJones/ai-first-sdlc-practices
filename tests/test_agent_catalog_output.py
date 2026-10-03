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


def _make_plugin(root: Path, name: str, with_agent: bool) -> None:
    plugin = root / "plugins" / name
    (plugin / ".claude-plugin").mkdir(parents=True)
    (plugin / ".claude-plugin" / "plugin.json").write_text("{}\n")
    if with_agent:
        (plugin / "agents").mkdir()
        (plugin / "agents" / f"{name}-agent.md").write_text(_AGENT)


def _generate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Tuple[str, str]:
    agent_dir = tmp_path / "agents" / "core"
    agent_dir.mkdir(parents=True)
    (agent_dir / "demo-agent.md").write_text(_AGENT)
    (agent_dir / "second-agent.md").write_text(_AGENT)
    _make_plugin(tmp_path, "plug-a", with_agent=True)
    _make_plugin(tmp_path, "plug-b", with_agent=False)
    _make_plugin(tmp_path, "plug-c", with_agent=True)
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


def _notes() -> str:
    return build_agent_catalog.NOTES_PATH.read_text(encoding="utf-8")


def test_index_contains_both_hand_written_notes_verbatim(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, index = _generate(tmp_path, monkeypatch)
    note, bundles = _notes().strip("\n").split("\n\n")
    assert note.startswith("> **Note:** This catalog indexes agent files")
    assert bundles.startswith("> **SDLC method bundles")
    # The placeholders are filled; everything else is byte-for-byte the source.
    assert "{{" not in index
    expected_note = (
        note.replace("{{published}}", "2")
        .replace("{{plugins}}", "3")
        .replace("{{shipping}}", "2")
    )
    assert expected_note in index
    assert bundles in index
    assert index.index(expected_note) < index.index(bundles)
    assert index.index(bundles) < index.index("## Agents by Category")


def test_index_counts_line_matches_the_catalog_data(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    text, index = _generate(tmp_path, monkeypatch)
    catalog = json.loads(text)
    assert catalog["total_agents"] == 4
    assert (
        "*Total catalog entries: 4 | 2 in the `agents/` source directory | "
        "2 published in plugins (across 3 plugins; 2 ship agents)*"
    ) in index.splitlines()
    assert "*Generated: " + catalog["generated"] + "*" in index.splitlines()
    assert "Total Agents" not in index
    assert "manual notes re-added" not in index


def test_catalog_json_is_exactly_the_hook_format(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    text, _ = _generate(tmp_path, monkeypatch)
    obj = json.loads(text)
    assert text == json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def test_index_has_single_trailing_newline_and_no_trailing_whitespace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, index = _generate(tmp_path, monkeypatch)
    _assert_hook_clean(index)
    assert index.endswith("\n") and not index.endswith("\n\n")


def test_committed_index_notes_match_the_notes_source() -> None:
    """The committed AGENT-INDEX.md carries the notes the generator emits."""
    index = (_REPO / "AGENT-INDEX.md").read_text(encoding="utf-8")
    _, bundles = _notes().strip("\n").split("\n\n")
    assert bundles in index


def test_fallback_parser_warns_on_stderr_when_pyyaml_is_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    monkeypatch.setattr(build_agent_catalog, "yaml", None)
    _generate(tmp_path, monkeypatch)
    err = capsys.readouterr().err
    assert "WARNING" in err
    assert "PyYAML" in err
    assert "degraded" in err


def test_no_fallback_warning_when_pyyaml_is_available(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    pytest.importorskip("yaml")
    _generate(tmp_path, monkeypatch)
    assert "PyYAML" not in capsys.readouterr().err


def test_workflow_installs_pyyaml_before_running_the_generator() -> None:
    workflow = (_REPO / ".github" / "workflows" / "agent-catalog-update.yml").read_text(
        encoding="utf-8"
    )
    generator_step = "python tools/automation/build-agent-catalog.py"
    assert "pip install pyyaml" in workflow
    assert workflow.index("pip install pyyaml") < workflow.index(generator_step)
