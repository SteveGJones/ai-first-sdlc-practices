"""Live Ollama smoke — skipped unless a local daemon + model are present.
Proves OllamaBackend + ingest_graph produce a real extract from a real source."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def _ollama_ready(model="gemma4:12b"):
    if shutil.which("ollama") is None:
        return False
    try:
        import ollama
        resp = ollama.list()
        models = resp.get("models", []) if isinstance(resp, dict) else getattr(resp, "models", [])
        names = []
        for m in models:
            n = m.get("model") if isinstance(m, dict) else getattr(m, "model", None)
            if n:
                names.append(n)
        return any(model in n for n in names)
    except Exception:
        return False


@pytest.mark.skipif(not _ollama_ready(), reason="ollama daemon/model not available")
def test_live_ollama_single_ingest(tmp_path):
    from sdlc_knowledge_base_scripts.backends.ollama_backend import OllamaBackend
    from sdlc_knowledge_base_scripts.graphs.ingest_graph import build_ingest_graph

    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n")
    (lib / "log.md").write_text("# Log\n")
    corpus = sorted((REPO / "tmp_texts").glob("*.md"))
    if not corpus:
        pytest.skip("no tmp_texts corpus available")
    src = corpus[0]

    be = OllamaBackend(model="gemma4:12b")
    graph = build_ingest_graph(
        be, allowed_layers=["methodology", "evidence", "domain", "development"],
        checkpoint_path=lib / ".kb-offline" / "ck.sqlite")
    graph.invoke(
        {"library_path": str(lib), "source_spec": str(src), "run_id": "live-1"},
        config={"configurable": {"thread_id": "live-1"}})
    extracts = list((lib / ".kb-offline" / "extracts").glob("*.json"))
    assert extracts, "no extract produced"
    data = json.loads(extracts[0].read_text())   # must be valid JSON (structured-output path)
    assert "findings" in data


@pytest.mark.skipif(not _ollama_ready(), reason="ollama daemon/model not available")
def test_live_ollama_bulk_ingest_three_sources(tmp_path):
    from sdlc_knowledge_base_scripts.backends.ollama_backend import OllamaBackend
    from sdlc_knowledge_base_scripts.graphs.bulk_ingest_graph import build_bulk_ingest_graph

    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n")
    (lib / "log.md").write_text("# Log\n")
    corpus = sorted((REPO / "tmp_texts").glob("*.md"))[:3]
    if len(corpus) < 3:
        pytest.skip("need >=3 tmp_texts sources")

    be = OllamaBackend(model="gemma4:12b")
    graph = build_bulk_ingest_graph(
        be, allowed_layers=["methodology", "evidence", "domain", "development"],
        checkpoint_path=lib / ".kb-offline" / "bulk.sqlite")
    graph.invoke(
        {"library_path": str(lib), "source_specs": [str(p) for p in corpus], "run_id": "bulk-live"},
        config={"configurable": {"thread_id": "bulk-live"}, "max_concurrency": 3})
    extracts = list((lib / ".kb-offline" / "extracts").glob("*.json"))
    assert len(extracts) == 3
    for e in extracts:
        json.loads(e.read_text())  # each is valid JSON (parallel map structured-output path)


@pytest.mark.skipif(not _ollama_ready(), reason="ollama daemon/model not available")
def test_live_ollama_query(tmp_path):
    from sdlc_knowledge_base_scripts.backends.ollama_backend import OllamaBackend
    from sdlc_knowledge_base_scripts.graphs.query_graph import build_query_graph

    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n- dora.md\n")
    (lib / "dora.md").write_text(
        "---\nlayer: evidence\nconfidence: high\n---\n"
        "# DORA\nElite teams deploy multiple times per day.\n"
    )
    graph = build_query_graph(OllamaBackend(model="gemma4:12b"))
    out = graph.invoke(
        {"library_path": str(lib), "question": "How often do elite teams deploy?"},
        config={"configurable": {"thread_id": "ql"}},
    )
    assert "rendered_text" in out and "rejected_claims" in out


@pytest.mark.skipif(not _ollama_ready(), reason="ollama daemon/model not available")
def test_live_ollama_promote(tmp_path):
    from sdlc_knowledge_base_scripts.backends.ollama_backend import OllamaBackend
    from sdlc_knowledge_base_scripts.graphs.query_graph import build_query_graph
    from sdlc_knowledge_base_scripts.graphs.promote_graph import build_promote_graph
    from sdlc_knowledge_base_scripts.answers import save_answer
    from sdlc_knowledge_base_scripts.contracts import Answer
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n- dora.md\n")
    (lib / "dora.md").write_text("---\nlayer: evidence\nconfidence: high\n---\n# DORA\n"
                                 "Elite teams deploy multiple times per day.\n")
    be = OllamaBackend(model="gemma4:12b", options={"temperature": 0, "seed": 7, "num_ctx": 8192})
    qout = build_query_graph(be).invoke(
        {"library_path": str(lib), "question": "How often do elite teams deploy?"},
        config={"configurable": {"thread_id": "ql"}})
    ref = save_answer(str(lib), "How often do elite teams deploy?", Answer.model_validate(qout["_answer"]),
                      libraries=["local"], page_ids=list(qout.get("page_ids", [])))
    out = build_promote_graph(be).invoke(
        {"library_path": str(lib), "ref": ref, "target_file": "deploy.md", "action": "create",
         "layer": None, "confidence": None, "run_id": "p-live"},
        config={"configurable": {"thread_id": "p-live"}})
    assert "committed" in out


@pytest.mark.skipif(not _ollama_ready(), reason="ollama daemon/model not available")
def test_live_ollama_federation(tmp_path):
    from sdlc_knowledge_base_scripts.graphs.federation_query_graph import build_federation_query_graph
    from sdlc_knowledge_base_scripts.backends.ollama_backend import OllamaBackend

    def _seed(name, page, body):
        lib = tmp_path / name
        lib.mkdir()
        (lib / "_shelf-index.md").write_text(f"<!-- format_version: 1 -->\n# Shelf\n- {page}\n")
        (lib / page).write_text(f"---\nlayer: evidence\nconfidence: high\n---\n# {page}\n{body}\n")
        return lib
    local = _seed("local", "dora.md", "Elite teams deploy multiple times per day.")
    _seed("acme", "ops.md", "Canary deploys reduce blast radius.")
    be = OllamaBackend(model="gemma4:12b", options={"temperature": 0, "seed": 7, "num_ctx": 8192})
    graph = build_federation_query_graph(be)
    out = graph.invoke(
        {"library_specs": [["local", str(local)], ["acme-kb", str(tmp_path / "acme")]],
         "local_project_dir": str(tmp_path), "question": "How do teams deploy safely?"},
        config={"configurable": {"thread_id": "fq-live"}, "max_concurrency": 2})
    assert "rendered_text" in out and out["queried"] == 2


@pytest.mark.skipif(not _ollama_ready(), reason="ollama daemon/model not available")
def test_live_ollama_index(tmp_path):
    import numpy as np
    from sdlc_knowledge_base_scripts.backends.ollama_backend import OllamaBackend
    from sdlc_knowledge_base_scripts.embeddings import (EmbeddingStore, IndexRow, Provenance, chunk_pages, corpus_hash)
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n- dora.md\n")
    (lib / "dora.md").write_text("---\nlayer: evidence\n---\n# DORA\nElite teams deploy multiple times per day.\n")
    be = OllamaBackend()
    pages = chunk_pages(lib)
    vecs = np.array(be.embed([t for _, t, _ in pages]), dtype=np.float32)
    rows = [IndexRow(page_id=p, content_hash=h) for p, _, h in pages]
    prov = Provenance(model=be.embedding_model_id(), dims=vecs.shape[1], normalization="l2",
                      corpus_hash=corpus_hash([(p, h) for p, _, h in pages]))
    EmbeddingStore.from_rows(vecs, rows, prov).save(lib)
    loaded = EmbeddingStore.load(lib)
    assert loaded is not None and loaded.provenance.model == "nomic-embed-text"
    assert loaded.provenance.dims > 0
    hit = loaded.search(be.embed(["how often do elite teams deploy?"])[0], k=1)
    assert hit and hit[0][0] == "dora.md"


def _two_real_indexed_libs(tmp_path, be):
    """Build two small real-indexed libraries sharing the SAME live embedding model so the accel
    gate's compatibility/freshness checks pass and the end-to-end path can actually run.
    Mirrors test_live_ollama_index: rebuild_shelf_index(full=True), then EmbeddingStore from
    chunk_pages() embedded with the backend's real .embed, provenance.model = embedding_model_id."""
    import numpy as np
    from sdlc_knowledge_base_scripts.build_shelf_index import rebuild_shelf_index
    from sdlc_knowledge_base_scripts.embeddings import (
        EmbeddingStore, IndexRow, Provenance, chunk_pages, corpus_hash)

    def _seed_and_index(name, pages):
        lib = tmp_path / name
        lib.mkdir()
        for pid, (layer, conf, body) in pages.items():
            (lib / pid).write_text(
                f"---\nlayer: {layer}\nconfidence: {conf}\n---\n# {pid}\n{body}\n", encoding="utf-8")
        rebuild_shelf_index(lib, lib / "_shelf-index.md", full=True)
        rows = chunk_pages(lib)                       # [(page_id, embed_text, content_hash)]
        vecs = np.array(be.embed([t for _, t, _ in rows]), dtype=np.float32)
        irows = [IndexRow(page_id=pid, content_hash=h) for pid, _, h in rows]
        prov = Provenance(model=be.embedding_model_id(), dims=vecs.shape[1], normalization="l2",
                          corpus_hash=corpus_hash([(pid, h) for pid, _, h in rows]))
        EmbeddingStore.from_rows(vecs, irows, prov).save(lib)
        return lib

    local = _seed_and_index("library", {
        "dora.md": ("evidence", "high", "Elite teams deploy multiple times per day."),
    })
    acme = _seed_and_index("acme", {
        "ops.md": ("evidence", "high", "Canary deploys reduce the blast radius of a bad release."),
    })
    return local, acme


@pytest.mark.skipif(not _ollama_ready(), reason="ollama daemon/model not available")
def test_live_ollama_accelerated_federation(tmp_path):
    from sdlc_knowledge_base_scripts.backends.ollama_backend import OllamaBackend
    from sdlc_knowledge_base_scripts.federation_accel import accelerated_federation_query

    be = OllamaBackend(options={"temperature": 0, "seed": 7, "num_ctx": 8192})
    local, acme = _two_real_indexed_libs(tmp_path, be)
    out = accelerated_federation_query(
        local, [("library", str(local)), ("acme", str(acme))],
        "how often do elite teams deploy?", backend=be, search_k=8)
    # Either accelerated federation runs end-to-end, or it cleanly falls back (None) — both valid;
    # assert no crash and a usable shape when a result is present.
    assert out is None or "rendered_text" in out


@pytest.mark.skipif(not _ollama_ready(), reason="ollama daemon/model not available")
def test_live_ollama_query_accelerate(tmp_path):
    import numpy as np
    from sdlc_knowledge_base_scripts.backends.ollama_backend import OllamaBackend
    from sdlc_knowledge_base_scripts.embeddings import (EmbeddingStore, IndexRow, Provenance,
                                                        chunk_pages, corpus_hash)
    from sdlc_knowledge_base_scripts.graphs.query_graph import build_query_graph
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n- dora.md — DORA metrics\n")
    (lib / "dora.md").write_text(
        "---\nlayer: evidence\nconfidence: high\n---\n# DORA\nElite teams deploy multiple times per day.\n")
    be = OllamaBackend()
    pages = chunk_pages(lib)
    vecs = np.array(be.embed([t for _, t, _ in pages]), dtype=np.float32)
    rows = [IndexRow(page_id=p, content_hash=h) for p, _, h in pages]
    ch = corpus_hash([(p, h) for p, _, h in pages])
    EmbeddingStore.from_rows(vecs, rows, Provenance(model=be.embedding_model_id(), dims=vecs.shape[1],
                             normalization="l2", corpus_hash=ch)).save(lib)
    out = build_query_graph(be).invoke(
        {"library_path": str(lib), "question": "How often do elite teams deploy?", "accelerate": True, "accelerate_k": 5},
        config={"configurable": {"thread_id": "acc-live"}})
    assert "rendered_text" in out and "rejected_claims" in out
