"""M0 end-to-end: CLI ingest via FakeBackend proves the foundation composes —
extract -> route -> reduce -> validate -> commit (journal+fence+CAS) -> recover/reindex."""
from __future__ import annotations

import json

from sdlc_knowledge_base_scripts import kb_offline_cli as cli
from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend


def test_m0_end_to_end(tmp_path):
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n")
    (lib / "log.md").write_text("# Log\n")
    src = tmp_path / "s1.md"
    src.write_text("a source about widgets")

    extract_payload = json.dumps({"source": str(src), "findings": ["widgets matter"],
                                  "confidence": "medium",
                                  "targets": [{"new_topic_slug": "widgets", "title": "Widgets",
                                               "finding_idx": [0]}]})
    reduce_payload = json.dumps({"target_file": "widgets.md", "action": "create",
                                 "frontmatter": {"layer": "domain", "confidence": "medium"},
                                 "body": "# Widgets\n- widgets matter",
                                 "citations": [], "cross_refs": [], "expected_hash": None})
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: (  # type: ignore
        reduce_payload if "Routed extracts" in prompt else extract_payload)

    rc = cli.main(["ingest", str(src), "--library", str(lib), "--backend", "fake",
                   "--timestamp", "2026-06-06T00:00:00Z"],
                  backend_override=be, allowed_layers=["domain"])
    assert rc == 0
    page = lib / "widgets.md"
    assert page.exists() and "widgets matter" in page.read_text()
    assert "widgets.md" in (lib / "_shelf-index.md").read_text()
    journal = list((lib / ".kb-offline" / "journal").glob("*.json"))
    assert any(json.loads(p.read_text()).get("stage") == "committed" for p in journal)
