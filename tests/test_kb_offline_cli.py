"""Tests for the kb-offline CLI skeleton (in-process, FakeBackend)."""
from __future__ import annotations

import json

from sdlc_knowledge_base_scripts import kb_offline_cli as cli
from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend


def _seed_lib(tmp_path):
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n")
    (lib / "log.md").write_text("# Log\n")
    return lib


def _fake(extract_payload, reduce_payload):
    be = FakeBackend()

    def gen(prompt, schema=None):
        return reduce_payload if "Routed extracts" in prompt else extract_payload

    be.generate = gen  # type: ignore
    return be


def test_cli_ingest_creates_page_and_completes_run(tmp_path):
    lib = _seed_lib(tmp_path)
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
    rc = cli.main(
        ["ingest", str(src), "--library", str(lib), "--backend", "fake", "--timestamp", "2026-06-06T00:00:00Z"],
        backend_override=be,
        allowed_layers=["domain"],
    )
    assert rc == 0
    assert (lib / "topic-one.md").exists()
    runs = json.loads((lib / ".kb-offline" / "runs.json").read_text())
    assert any(r["state"] == "completed" for r in runs["runs"].values())


def test_cli_resume_skips_completed_source(tmp_path):
    lib = _seed_lib(tmp_path)
    src = tmp_path / "s1.md"
    src.write_text("source one")
    extract_payload = json.dumps(
        {
            "source": str(src),
            "findings": ["f"],
            "confidence": "low",
            "targets": [{"new_topic_slug": "t", "title": "T", "finding_idx": [0]}],
        }
    )
    reduce_payload = json.dumps(
        {
            "target_file": "t.md",
            "action": "create",
            "frontmatter": {"layer": "domain", "confidence": "low"},
            "body": "# T",
            "citations": [],
            "cross_refs": [],
            "expected_hash": None,
        }
    )
    be = _fake(extract_payload, reduce_payload)
    args = ["ingest", str(src), "--library", str(lib), "--backend", "fake", "--timestamp", "2026-06-06T00:00:00Z"]
    assert cli.main(args, backend_override=be, allowed_layers=["domain"]) == 0

    def boom(prompt, schema=None):
        if "Routed extracts" in prompt:
            return reduce_payload
        raise AssertionError("extract should be skipped on resume")

    be2 = FakeBackend()
    be2.generate = boom  # type: ignore
    rc = cli.main(args + ["--resume", "latest"], backend_override=be2, allowed_layers=["domain"])
    assert rc == 0
