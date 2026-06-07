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


def test_cli_ingest_rejected_proposal_reports_and_nonzero(tmp_path):
    lib = _seed_lib(tmp_path)
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
    rc = cli.main(
        ["ingest", str(src), "--library", str(lib), "--backend", "fake", "--timestamp", "2026-06-06T00:00:00Z"],
        backend_override=be,
        allowed_layers=["evidence"],
    )
    assert rc == 1  # nothing committed, work attempted
    assert not (lib / "t.md").exists()
    runs = json.loads((lib / ".kb-offline" / "runs.json").read_text())
    assert any(r["state"] == "completed_with_errors" for r in runs["runs"].values())


def test_cli_unknown_resume_id_fails_fast(tmp_path):
    lib = _seed_lib(tmp_path)
    src = tmp_path / "s1.md"
    src.write_text("x")
    be = FakeBackend()
    be.generate = lambda prompt, schema=None: (_ for _ in ()).throw(AssertionError("no work"))  # type: ignore
    import pytest

    with pytest.raises(SystemExit):
        cli.main(
            [
                "ingest",
                str(src),
                "--library",
                str(lib),
                "--backend",
                "fake",
                "--resume",
                "deadbeef",
                "--timestamp",
                "2026-06-06T00:00:00Z",
            ],
            backend_override=be,
            allowed_layers=["domain"],
        )


def test_cli_init_creates_structure(tmp_path):
    lib = tmp_path / "lib"
    rc = cli.main(["init", "--library", str(lib)])
    assert rc == 0
    assert (lib / "_shelf-index.md").exists()
    assert (lib / "log.md").exists()
    assert (lib / ".kb-offline").exists()


def test_console_entry_point_importable():
    from sdlc_knowledge_base_scripts.kb_offline_cli import main as entry
    assert callable(entry)


def test_pyproject_declares_pydantic_and_script():
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib
    from pathlib import Path
    pp = Path(__file__).resolve().parents[1] / "plugins/sdlc-knowledge-base/pyproject.toml"
    data = tomllib.loads(pp.read_text())
    assert any("pydantic" in d for d in data["project"]["dependencies"])
    assert "kb-offline" in data["project"]["scripts"]
