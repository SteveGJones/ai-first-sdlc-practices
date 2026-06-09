"""Tests for the ingest_graph (FakeBackend; no live model)."""

from __future__ import annotations

import json

from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
from sdlc_knowledge_base_scripts.graphs.ingest_graph import build_ingest_graph


def _seed(tmp_path):
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n")
    (lib / "log.md").write_text("# Log\n")
    return lib


def _fake(extract_payload, reduce_payload):
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: (reduce_payload if "Routed extracts" in prompt else extract_payload)
    return be


def test_ingest_graph_runs_end_to_end(tmp_path):
    lib = _seed(tmp_path)
    src = tmp_path / "s1.md"
    src.write_text("source one")
    extract_payload = json.dumps(
        {
            "source": str(src),
            "findings": ["finding one"],
            "confidence": "medium",
            "targets": [{"new_topic_slug": "topic-one", "title": "Topic One", "finding_idx": [0]}],
        }
    )
    reduce_payload = json.dumps(
        {
            "target_file": "topic-one.md",
            "action": "create",
            "frontmatter": {"layer": "domain", "confidence": "medium"},
            "body": "# Topic One\n- finding one",
            "citations": [],
            "cross_refs": [],
            "expected_hash": None,
        }
    )
    be = _fake(extract_payload, reduce_payload)
    graph = build_ingest_graph(be, allowed_layers=["domain"])
    state = {
        "library_path": str(lib),
        "source_spec": str(src),
        "run_id": "run-1",
    }
    result = graph.invoke(state, config={"configurable": {"thread_id": "run-1"}})
    assert (lib / "topic-one.md").exists()
    assert result["committed"] == 1
    assert "topic-one.md" in (lib / "_shelf-index.md").read_text()


def test_rejected_proposal_counted_not_committed(tmp_path):
    lib = _seed(tmp_path)
    src = tmp_path / "s1.md"
    src.write_text("source one")
    extract_payload = json.dumps(
        {
            "source": str(src),
            "findings": ["f"],
            "confidence": "medium",
            "targets": [{"new_topic_slug": "t", "title": "T", "finding_idx": [0]}],
        }
    )
    # reduce proposes layer 'domain' but allowed_layers is ['evidence'] -> validator rejects
    reduce_payload = json.dumps(
        {
            "target_file": "t.md",
            "action": "create",
            "frontmatter": {"layer": "domain", "confidence": "medium"},
            "body": "# T",
            "citations": [],
            "cross_refs": [],
            "expected_hash": None,
        }
    )
    be = _fake(extract_payload, reduce_payload)
    graph = build_ingest_graph(be, allowed_layers=["evidence"])
    out = graph.invoke(
        {"library_path": str(lib), "source_spec": str(src), "run_id": "r1"}, config={"configurable": {"thread_id": "r1"}}
    )
    assert out["rejected"] == 1 and out["committed"] == 0
    assert not (lib / "t.md").exists()


def test_idempotent_create_skip_not_counted_on_rerun(tmp_path):
    lib = _seed(tmp_path)
    src = tmp_path / "s1.md"
    src.write_text("source one")
    extract_payload = json.dumps(
        {
            "source": str(src),
            "findings": ["f"],
            "confidence": "low",
            "targets": [{"new_topic_slug": "topic", "title": "Topic", "finding_idx": [0]}],
        }
    )
    reduce_payload = json.dumps(
        {
            "target_file": "topic.md",
            "action": "create",
            "frontmatter": {"layer": "domain", "confidence": "low"},
            "body": "# Topic",
            "citations": [],
            "cross_refs": [],
            "expected_hash": None,
        }
    )
    be = _fake(extract_payload, reduce_payload)
    g1 = build_ingest_graph(be, allowed_layers=["domain"])
    out1 = g1.invoke(
        {"library_path": str(lib), "source_spec": str(src), "run_id": "r1"}, config={"configurable": {"thread_id": "r1"}}
    )
    assert out1["committed"] == 1
    # second run (new run_id): extract skipped (file exists), reduce re-proposes create -> CommitConflict+exists -> SKIPPED
    be2 = _fake(extract_payload, reduce_payload)
    g2 = build_ingest_graph(be2, allowed_layers=["domain"])
    out2 = g2.invoke(
        {"library_path": str(lib), "source_spec": str(src), "run_id": "r2"}, config={"configurable": {"thread_id": "r2"}}
    )
    assert out2["conflicts"] == 0  # idempotent skip, not a counted conflict
    assert (lib / "topic.md").exists()


def test_reextract_skipped_on_second_run(tmp_path):
    lib = _seed(tmp_path)
    src = tmp_path / "s1.md"
    src.write_text("source one")
    extract_payload = json.dumps(
        {
            "source": str(src),
            "findings": ["f"],
            "confidence": "low",
            "targets": [{"new_topic_slug": "topic", "title": "Topic", "finding_idx": [0]}],
        }
    )
    reduce_payload = json.dumps(
        {
            "target_file": "topic.md",
            "action": "create",
            "frontmatter": {"layer": "domain", "confidence": "low"},
            "body": "# Topic",
            "citations": [],
            "cross_refs": [],
            "expected_hash": None,
        }
    )
    be = _fake(extract_payload, reduce_payload)
    build_ingest_graph(be, allowed_layers=["domain"]).invoke(
        {"library_path": str(lib), "source_spec": str(src), "run_id": "r1"}, config={"configurable": {"thread_id": "r1"}}
    )
    # second run: extract file exists -> extract() must NOT be called again
    calls = {"n": 0}

    def counting(prompt, schema=None):
        if "Routed extracts" not in prompt:
            calls["n"] += 1
        return reduce_payload if "Routed extracts" in prompt else extract_payload

    be2 = _fake(extract_payload, reduce_payload)
    be2.generate = counting
    build_ingest_graph(be2, allowed_layers=["domain"]).invoke(
        {"library_path": str(lib), "source_spec": str(src), "run_id": "r2"}, config={"configurable": {"thread_id": "r2"}}
    )
    assert calls["n"] == 0  # extract skipped (resume idempotency)


def test_fence_error_counted_as_conflict(tmp_path, monkeypatch):
    import sdlc_knowledge_base_scripts.graphs._reduce as red
    from sdlc_knowledge_base_scripts.mutation import FenceError

    lib = _seed(tmp_path)
    src = tmp_path / "s1.md"
    src.write_text("source one")
    extract_payload = json.dumps(
        {
            "source": str(src),
            "findings": ["f"],
            "confidence": "low",
            "targets": [{"new_topic_slug": "topic", "title": "Topic", "finding_idx": [0]}],
        }
    )
    reduce_payload = json.dumps(
        {
            "target_file": "topic.md",
            "action": "create",
            "frontmatter": {"layer": "domain", "confidence": "low"},
            "body": "# Topic",
            "citations": [],
            "cross_refs": [],
            "expected_hash": None,
        }
    )

    def boom(*a, **k):
        raise FenceError("fenced")

    monkeypatch.setattr(red, "commit_mutation", boom)
    be = _fake(extract_payload, reduce_payload)
    out = build_ingest_graph(be, allowed_layers=["domain"]).invoke(
        {"library_path": str(lib), "source_spec": str(src), "run_id": "r1"}, config={"configurable": {"thread_id": "r1"}}
    )
    assert out["conflicts"] == 1 and out["committed"] == 0


def test_sqlite_checkpoint_path_branch(tmp_path):
    lib = _seed(tmp_path)
    src = tmp_path / "s1.md"
    src.write_text("source one")
    extract_payload = json.dumps(
        {
            "source": str(src),
            "findings": ["f"],
            "confidence": "low",
            "targets": [{"new_topic_slug": "topic", "title": "Topic", "finding_idx": [0]}],
        }
    )
    reduce_payload = json.dumps(
        {
            "target_file": "topic.md",
            "action": "create",
            "frontmatter": {"layer": "domain", "confidence": "low"},
            "body": "# Topic",
            "citations": [],
            "cross_refs": [],
            "expected_hash": None,
        }
    )
    be = _fake(extract_payload, reduce_payload)
    ckpt = lib / ".kb-offline" / "ckpt.sqlite"
    graph = build_ingest_graph(be, allowed_layers=["domain"], checkpoint_path=ckpt)
    out = graph.invoke(
        {"library_path": str(lib), "source_spec": str(src), "run_id": "r1"}, config={"configurable": {"thread_id": "r1"}}
    )
    assert out["committed"] == 1
    assert ckpt.exists()  # SqliteSaver wired correctly (sqlite3.connect path)
