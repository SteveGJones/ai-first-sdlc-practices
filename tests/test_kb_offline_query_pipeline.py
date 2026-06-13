"""Tests for kb-offline query pipeline ops (select/synthesize)."""
from __future__ import annotations

import json

from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
from sdlc_knowledge_base_scripts.pipeline import select, synthesize


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


def test_select_without_priming_prompt_unchanged(tmp_path):
    from sdlc_knowledge_base_scripts.priming import PrimingBundle  # noqa: F401 (import-shape check)
    captured = {}

    def gen(prompt, schema=None):
        captured["prompt"] = prompt
        return json.dumps({"page_ids": ["a.md"]})
    be = FakeBackend()
    be.generate = gen
    select("q", _shelf(tmp_path), backend=be, known_pages={"a.md"})   # no priming
    assert "PRIMING" not in captured["prompt"]


def test_select_with_priming_prepends_block(tmp_path):
    from sdlc_knowledge_base_scripts.priming import PrimingBundle
    captured = {}

    def gen(prompt, schema=None):
        captured["prompt"] = prompt
        return json.dumps({"page_ids": ["a.md"]})
    be = FakeBackend()
    be.generate = gen
    bundle = PrimingBundle(question="q", local_kb_config_excerpt="Brazilian semiconductor packaging",
                           local_shelf_index_terms=["wirebond", "yield"])
    select("q", _shelf(tmp_path), backend=be, known_pages={"a.md"}, priming=bundle)
    assert "PRIMING" in captured["prompt"]
    assert "Brazilian semiconductor packaging" in captured["prompt"]
    assert "wirebond" in captured["prompt"]


def test_select_uses_shelf_text_when_given(tmp_path):
    captured = {}

    def gen(prompt, schema=None):
        captured["prompt"] = prompt
        return json.dumps({"page_ids": ["a.md"]})
    be = FakeBackend()
    be.generate = gen
    select("q", _shelf(tmp_path), backend=be, known_pages={"a.md"},
           shelf_text="REDUCED-SHELF-MARKER\n- a.md")
    assert "REDUCED-SHELF-MARKER" in captured["prompt"]


def test_select_reads_file_when_shelf_text_none(tmp_path):
    captured = {}

    def gen(prompt, schema=None):
        captured["prompt"] = prompt
        return json.dumps({"page_ids": ["a.md"]})
    be = FakeBackend()
    be.generate = gen
    shelf = _shelf(tmp_path)
    select("q", shelf, backend=be, known_pages={"a.md"})
    assert "REDUCED-SHELF-MARKER" not in captured["prompt"]
    assert "Shelf-index:" in captured["prompt"]


def test_synthesize_returns_claims_and_strips_model_status(tmp_path):
    payload = json.dumps({
        "claims": [{
            "text": "Widgets cut cost 30%.",
            "cited_pages": [{"library": "local", "page": "a.md"}],
            "evidence_spans": [{"page": "a.md", "text": "cost fell 30%"}],
            "entailment_status": "supported",
            "high_impact": True,
        }],
        "rendered_text": "Widgets cut cost 30%.",
    })
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: payload
    ans = synthesize("q", [{"page": "a.md", "content": "cost fell 30%"}], backend=be)
    assert ans.claims[0].text == "Widgets cut cost 30%."
    assert ans.claims[0].entailment_status is None
    assert ans.claims[0].high_impact is False
