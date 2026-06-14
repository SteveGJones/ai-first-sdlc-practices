"""Accelerated discovery / reduced-shelf tests. kb-offline M3b (#211)."""
from __future__ import annotations

import numpy as np

from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
from sdlc_knowledge_base_scripts.embeddings import EmbeddingStore, IndexRow, Provenance
from sdlc_knowledge_base_scripts.retrieval import accelerated_candidates


def _store(vectors, page_ids):
    rows = [IndexRow(page_id=p, content_hash=f"h{i}") for i, p in enumerate(page_ids)]
    prov = Provenance(model="fake-embed", dims=len(vectors[0]), normalization="l2", corpus_hash="c")
    return EmbeddingStore.from_rows(np.array(vectors, dtype=np.float32), rows, prov)


def _lib_with_shelf(tmp_path, entries):
    lib = tmp_path / "library"
    lib.mkdir()
    shelf = "<!-- format_version: 1 -->\n# Shelf Index\n\nIntro prose.\n" + "".join(
        f"- {pid} — about {pid}\n" for pid in entries)
    (lib / "_shelf-index.md").write_text(shelf, encoding="utf-8")
    return lib


def test_accelerated_candidates_returns_topk_and_reduced_shelf(tmp_path):
    lib = _lib_with_shelf(tmp_path, ["a.md", "b.md", "c.md"])
    store = _store([[1, 0, 0], [0, 1, 0], [0, 0, 1]], ["a.md", "b.md", "c.md"])
    be = FakeBackend()
    be.embed = lambda texts: [[0.0, 1.0, 0.1]]
    page_ids, reduced = accelerated_candidates("q", str(lib), store, backend=be, k=2)
    assert page_ids[0] == "b.md" and len(page_ids) == 2
    assert "# Shelf Index" in reduced and "Intro prose." in reduced
    assert "b.md" in reduced
    excluded = ({"a.md", "b.md", "c.md"} - set(page_ids)).pop()
    assert f"- {excluded}" not in reduced


def test_reduced_shelf_synthesizes_entry_when_shelf_has_no_bullet(tmp_path):
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf Index\n", encoding="utf-8")
    store = _store([[1, 0, 0]], ["a.md"])
    be = FakeBackend()
    be.embed = lambda texts: [[1.0, 0.0, 0.0]]
    page_ids, reduced = accelerated_candidates("q", str(lib), store, backend=be, k=1)
    assert page_ids == ["a.md"]
    assert "a.md" in reduced


def test_score_recall_at_k_over_built_index(tmp_path):
    from sdlc_knowledge_base_scripts.eval.runner import score_recall_at_k
    from sdlc_knowledge_base_scripts.eval.suite import EvalQuestion
    store = _store([[1, 0], [0, 1]], ["a.md", "b.md"])
    qs = [EvalQuestion(id="q1", question="alpha", kind="fact", expected_facts=[],
                       expected_routing_targets=["a.md"], no_evidence=False),
          EvalQuestion(id="q2", question="none", kind="abstention", expected_facts=[],
                       expected_routing_targets=[], no_evidence=True)]
    be = FakeBackend()
    be.embed = lambda texts: [[1.0, 0.0]]
    r = score_recall_at_k(str(tmp_path), qs, store, backend=be, k=1)
    assert r == 1.0


def test_reduced_shelf_exact_id_match_no_substring_collision(tmp_path):
    # candidate "a.md" must NOT match the "data.md" entry (substring collision)
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text(
        "<!-- format_version: 1 -->\n# Shelf Index\n\n- data.md — about data\n- a.md — about a\n",
        encoding="utf-8")
    store = _store([[1, 0], [0, 1]], ["data.md", "a.md"])
    be = FakeBackend()
    be.embed = lambda texts: [[0.0, 1.0]]      # nearest a.md
    page_ids, reduced = accelerated_candidates("q", str(lib), store, backend=be, k=1)
    assert page_ids == ["a.md"]
    assert "about a" in reduced                # a.md's OWN entry chosen
    assert "about data" not in reduced         # NOT data.md's entry (no substring collision)
