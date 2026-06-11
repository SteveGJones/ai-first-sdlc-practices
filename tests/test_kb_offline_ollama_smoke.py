"""Live Ollama smoke — skipped unless a local daemon + model are present.
Proves OllamaBackend + ingest_graph produce a real extract from a real source."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def _ollama_ready(model="gpt-oss:20b"):
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

    be = OllamaBackend(model="gpt-oss:20b")
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

    be = OllamaBackend(model="gpt-oss:20b")
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
    graph = build_query_graph(OllamaBackend(model="gpt-oss:20b"))
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
    be = OllamaBackend(model="gpt-oss:20b", options={"temperature": 0, "seed": 7, "num_ctx": 8192})
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
