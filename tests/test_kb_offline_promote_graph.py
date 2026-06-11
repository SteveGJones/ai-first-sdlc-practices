"""promote_graph end-to-end tests (FakeBackend). kb-offline M2a (#211)."""
from __future__ import annotations

import json

from sdlc_knowledge_base_scripts.answers import save_answer
from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
from sdlc_knowledge_base_scripts.contracts import Answer, Claim, EntailmentStatus, PageRef, Span
from sdlc_knowledge_base_scripts.graphs.promote_graph import build_promote_graph
from sdlc_knowledge_base_scripts.provenance import page_frontmatter


def _lib(tmp_path):
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n- dora.md\n")
    (lib / "dora.md").write_text("---\nlayer: evidence\nconfidence: medium\n---\n# DORA\n"
                                 "Elite teams deploy multiple times per day.\n")
    return lib


def _save_supported(lib):
    c = Claim(text="Elite teams deploy multiple times per day.",
              cited_pages=[PageRef(library="local", page="dora.md")],
              evidence_spans=[Span(page="dora.md", text="deploy multiple times per day")])
    c.entailment_status = EntailmentStatus.supported
    ans = Answer(claims=[c], rendered_text="Elite teams deploy multiple times per day.")
    return save_answer(str(lib), "how often do elite teams deploy?", ans,
                       libraries=["local"], page_ids=["dora.md"])


def _draft_backend():
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: json.dumps(
        {"body": "# Deploy Frequency\n\nElite teams deploy multiple times per day."})
    return be


def test_promote_graph_creates_marked_page(tmp_path):
    lib = _lib(tmp_path)
    ref = _save_supported(lib)
    graph = build_promote_graph(_draft_backend())
    out = graph.invoke(
        {"library_path": str(lib), "ref": ref, "target_file": "deploy-frequency.md",
         "action": "create", "layer": None, "confidence": None, "run_id": "promote-1"},
        config={"configurable": {"thread_id": "promote-1"}})
    assert out["committed"] == 1
    page = lib / "deploy-frequency.md"
    assert page.is_file()
    fm = page_frontmatter(str(lib), "deploy-frequency.md")
    assert fm["provenance"] == "promoted"
    assert fm["derived_from"] == ref
    assert fm["sources"] == ["dora.md"]
    assert fm["confidence"] == "medium"
    assert fm["layer"] == "evidence"
    assert "deploy-frequency.md" in (lib / "_shelf-index.md").read_text()


def test_promote_graph_zero_supported_is_graceful(tmp_path):
    lib = _lib(tmp_path)
    c = Claim(text="x", cited_pages=[PageRef(library="local", page="dora.md")],
              evidence_spans=[Span(page="dora.md", text="absent text")])
    c.entailment_status = EntailmentStatus.unsupported
    ref = save_answer(str(lib), "q?", Answer(claims=[c], rendered_text="x"),
                      libraries=["local"], page_ids=["dora.md"])
    graph = build_promote_graph(_draft_backend())
    out = graph.invoke(
        {"library_path": str(lib), "ref": ref, "target_file": "x.md", "action": "create",
         "layer": None, "confidence": None, "run_id": "promote-2"},
        config={"configurable": {"thread_id": "promote-2"}})
    assert out["committed"] == 0 and out.get("failed")
    assert not (lib / "x.md").exists()


def test_promote_graph_rejects_out_of_library_target(tmp_path):
    lib = _lib(tmp_path)
    ref = _save_supported(lib)
    graph = build_promote_graph(_draft_backend())
    out = graph.invoke(
        {"library_path": str(lib), "ref": ref, "target_file": "../escape.md",
         "action": "create", "layer": None, "confidence": None, "run_id": "promote-3"},
        config={"configurable": {"thread_id": "promote-3"}})
    assert out["committed"] == 0 and out["rejected"] == 1
    assert not (tmp_path / "escape.md").exists()
