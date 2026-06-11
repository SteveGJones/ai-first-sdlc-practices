"""federation_query_graph end-to-end (FakeBackend, 2 libraries). kb-offline M2b (#211)."""
from __future__ import annotations

import json

from sdlc_knowledge_base_scripts.audit import read_log
from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
from sdlc_knowledge_base_scripts.graphs.federation_query_graph import build_federation_query_graph


def _lib(tmp_path, name, page, body):
    lib = tmp_path / name
    lib.mkdir()
    (lib / "_shelf-index.md").write_text(f"<!-- format_version: 1 -->\n# Shelf\n- {page}\n")
    (lib / page).write_text(f"---\nlayer: evidence\nconfidence: high\n---\n# {page}\n{body}\n")
    return lib


def test_federation_graph_merges_two_libraries(tmp_path):
    local = _lib(tmp_path, "local", "dora.md", "Elite teams deploy multiple times per day.")
    ext = _lib(tmp_path, "acme", "ops.md", "Elite teams deploy multiple times per day.")

    def gen(prompt, schema=None):
        if prompt.startswith("Judge"):
            return '{"status": "supported"}'
        if "Shelf-index" in prompt:
            page = "dora.md" if "dora.md" in prompt else "ops.md"
            return json.dumps({"page_ids": [page]})
        page = "dora.md" if "dora.md" in prompt else "ops.md"
        return json.dumps({"claims": [{"text": "Elite teams deploy multiple times per day.",
                                       "cited_pages": [{"library": "local", "page": page}],
                                       "evidence_spans": [{"page": page,
                                                           "text": "deploy multiple times per day"}]}],
                           "rendered_text": ""})
    be = FakeBackend()
    be.generate = gen
    graph = build_federation_query_graph(be)
    out = graph.invoke(
        {"library_specs": [["local", str(local)], ["acme-kb", str(ext)]],
         "local_project_dir": str(tmp_path), "question": "how often deploy?"},
        config={"configurable": {"thread_id": "fq1"}, "max_concurrency": 2})
    assert out["rendered_text"].count("Elite teams deploy multiple times per day.") == 1
    assert "local" in out["rendered_text"] and "acme-kb" in out["rendered_text"]
    assert out["queried"] == 2
    events = read_log(local / ".kb-offline" / "audit.log")
    handles = {e.source_handle for e in events if e.event_type == "cross_library_query"}
    assert "acme-kb" in handles and "local" not in handles
