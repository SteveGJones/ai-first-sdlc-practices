"""Tests for kb-offline prompts + pipeline."""
from __future__ import annotations

import json

from sdlc_knowledge_base_scripts import prompts
from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
from sdlc_knowledge_base_scripts.pipeline import extract


def test_extract_fragment_is_nonempty_constant():
    assert isinstance(prompts.EXTRACT_FRAGMENT, str)
    assert "JSON" in prompts.EXTRACT_FRAGMENT
    assert "targets" in prompts.EXTRACT_FRAGMENT


def test_reduce_fragment_states_constraints():
    assert "exactly one file" in prompts.REDUCE_FRAGMENT.lower()


def _shelf(tmp_path):
    s = tmp_path / "_shelf-index.md"
    s.write_text("<!-- format_version: 1 -->\n# Shelf\n- topic.md\n")
    return s


def test_extract_parses_valid_json(tmp_path):
    src = tmp_path / "a.md"
    src.write_text("source text")
    payload = json.dumps({"source": "a.md", "findings": ["f"], "confidence": "medium",
                          "targets": [{"file": "topic.md", "finding_idx": [0]}]})
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: payload  # type: ignore
    result = extract(str(src), _shelf(tmp_path), backend=be)
    assert result.findings == ["f"]
    assert result.targets[0].file == "topic.md"


def test_extract_repairs_then_succeeds(tmp_path):
    src = tmp_path / "a.md"
    src.write_text("source text")
    good = json.dumps({"source": "a.md", "findings": ["f"], "confidence": "low", "targets": []})
    seq = ["not json at all", good]
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: seq.pop(0)  # type: ignore
    result = extract(str(src), _shelf(tmp_path), backend=be, max_repairs=1)
    assert result.confidence.value == "low"


def test_extract_fails_after_repair_budget(tmp_path):
    src = tmp_path / "a.md"
    src.write_text("x")
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: "still not json"  # type: ignore
    import pytest
    with pytest.raises(ValueError):
        extract(str(src), _shelf(tmp_path), backend=be, max_repairs=1)
