"""Tests for provenance/layer filtering + publication policy."""
from __future__ import annotations

from sdlc_knowledge_base_scripts.contracts import Answer, Claim, EntailmentStatus, PageRef, Span
from sdlc_knowledge_base_scripts.provenance import filter_pages, known_page_ids
from sdlc_knowledge_base_scripts.publication import publish


def _page(tmp_path, name, layer, confidence):
    (tmp_path / name).write_text(f"---\nlayer: {layer}\nconfidence: {confidence}\n---\n# {name}\n")


def test_filter_by_layer(tmp_path):
    _page(tmp_path, "a.md", "evidence", "high")
    _page(tmp_path, "b.md", "domain", "high")
    kept = filter_pages(tmp_path, ["a.md", "b.md"], layer="evidence", min_confidence=None)
    assert kept == ["a.md"]


def test_filter_by_min_confidence(tmp_path):
    _page(tmp_path, "a.md", "domain", "low")
    _page(tmp_path, "b.md", "domain", "high")
    kept = filter_pages(tmp_path, ["a.md", "b.md"], layer=None, min_confidence="medium")
    assert kept == ["b.md"]   # low < medium dropped


def test_publish_policy_splits_claims():
    def claim(text, status):
        c = Claim(text=text, cited_pages=[PageRef(library="local", page="a.md")],
                  evidence_spans=[Span(page="a.md", text="x")])
        c.entailment_status = status
        return c
    ans = Answer(claims=[
        claim("supported one", EntailmentStatus.supported),
        claim("partial one", EntailmentStatus.partial),
        claim("unsupported one", EntailmentStatus.unsupported),
    ], rendered_text="")
    rendered, rejected = publish(ans)
    assert "supported one" in rendered
    assert "partial one" in rendered and "partially supported" in rendered.lower()
    assert "unsupported one" not in rendered
    assert any("unsupported one" in r["text"] for r in rejected)


def test_known_page_ids_roots_only_excludes_index_files(tmp_path):
    (tmp_path / "dora.md").write_text("x", encoding="utf-8")
    (tmp_path / "ci-cd.md").write_text("x", encoding="utf-8")
    (tmp_path / "_shelf-index.md").write_text("x", encoding="utf-8")
    (tmp_path / "log.md").write_text("x", encoding="utf-8")
    (tmp_path / "_index.md").write_text("x", encoding="utf-8")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "nested.md").write_text("x", encoding="utf-8")  # nested must NOT be known
    assert known_page_ids(tmp_path) == {"dora.md", "ci-cd.md"}
