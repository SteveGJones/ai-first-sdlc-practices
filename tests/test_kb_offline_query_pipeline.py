"""Tests for kb-offline query pipeline ops (select/synthesize)."""
from __future__ import annotations

import json
from pathlib import Path

from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
from sdlc_knowledge_base_scripts.pipeline import select


def _shelf(tmp_path):
    s = tmp_path / "_shelf-index.md"
    s.write_text("<!-- format_version: 1 -->\n# Shelf\n- a.md\n- b.md\n")
    return s


def test_select_returns_known_page_ids(tmp_path):
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: json.dumps({"page_ids": ["a.md", "b.md"]})
    res = select("q", _shelf(tmp_path), backend=be, known_pages={"a.md", "b.md"})
    assert res.page_ids == ["a.md", "b.md"]


def test_select_drops_unknown_page_ids(tmp_path):
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: json.dumps({"page_ids": ["a.md", "ghost.md"]})
    res = select("q", _shelf(tmp_path), backend=be, known_pages={"a.md", "b.md"})
    assert res.page_ids == ["a.md"]
