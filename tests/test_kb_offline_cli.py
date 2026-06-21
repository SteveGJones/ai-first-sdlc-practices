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


def test_pyproject_declares_offline_extra():
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib
    from pathlib import Path

    pp = Path(__file__).resolve().parents[1] / "plugins/sdlc-knowledge-base/pyproject.toml"
    data = tomllib.loads(pp.read_text())
    extra = data["project"]["optional-dependencies"]["offline"]
    joined = " ".join(extra)
    assert "langgraph" in joined
    assert "langgraph-checkpoint-sqlite" in joined
    assert "ollama" in joined
    assert "langchain-ollama" not in joined


def test_make_backend_ollama_strict_offline_default():
    from sdlc_knowledge_base_scripts import kb_offline_cli as c
    from sdlc_knowledge_base_scripts.backends.ollama_backend import OllamaBackend

    be = c._make_backend("ollama", None)
    assert isinstance(be, OllamaBackend)
    assert be.host == "http://localhost:11434"


def test_cli_releases_lock_and_marks_failed_on_graph_error(tmp_path):
    # If the graph raises mid-run, the CLI must release the lock and set run 'failed'
    import json as _j
    from sdlc_knowledge_base_scripts import kb_offline_cli as cli
    from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend

    lib = _seed_lib(tmp_path)
    src = tmp_path / "s1.md"
    src.write_text("source one")
    # extract returns valid JSON, but make reduce raise a non-conflict error inside the graph
    extract_payload = _j.dumps(
        {
            "source": str(src),
            "findings": ["f"],
            "confidence": "low",
            "targets": [{"new_topic_slug": "t", "title": "T", "finding_idx": [0]}],
        }
    )
    be = FakeBackend()

    def gen(prompt, schema=None):
        if "Routed extracts" in prompt:
            raise RuntimeError("boom in reduce")
        return extract_payload

    be.generate = gen
    import pytest

    with pytest.raises(RuntimeError):
        cli.main(
            ["ingest", str(src), "--library", str(lib), "--backend", "fake", "--timestamp", "2026-06-07T00:00:00Z"],
            backend_override=be,
            allowed_layers=["domain"],
        )
    # lock must be released (no lock.json left), run marked failed, and a NEW run can acquire
    assert not (lib / ".kb-offline" / "lock.json").exists(), "lock leaked after graph error"
    runs = _j.loads((lib / ".kb-offline" / "runs.json").read_text())
    assert any(r["state"] == "failed" for r in runs["runs"].values())


def test_cli_ingest_bulk_creates_pages(tmp_path):
    import json as _j
    import re
    from sdlc_knowledge_base_scripts import kb_offline_cli as cli
    from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend

    lib = _seed_lib(tmp_path)
    srcs = []
    for i in range(2):
        p = tmp_path / f"s{i}.md"
        p.write_text(f"source {i}")
        srcs.append(p)

    def gen(prompt, schema=None):
        if "Routed extracts" in prompt:
            m = re.search(r"Target file: (\S+)", prompt)
            tfile = m.group(1) if m else "t.md"
            return _j.dumps(
                {
                    "target_file": tfile,
                    "action": "create",
                    "frontmatter": {"layer": "domain", "confidence": "low"},
                    "body": "# x",
                    "citations": [],
                    "cross_refs": [],
                    "expected_hash": None,
                }
            )
        for s in srcs:
            if str(s) in prompt:
                slug = s.stem.lower()
                return _j.dumps(
                    {
                        "source": str(s),
                        "findings": ["f"],
                        "confidence": "low",
                        "targets": [{"new_topic_slug": slug, "title": slug, "finding_idx": [0]}],
                    }
                )
        return _j.dumps({"source": "?", "findings": [], "confidence": "low", "targets": []})

    be = FakeBackend()
    be.generate = gen
    rc = cli.main(
        [
            "ingest-bulk",
            str(tmp_path / "*.md"),
            "--library",
            str(lib),
            "--backend",
            "fake",
            "--parallel",
            "4",
            "--timestamp",
            "2026-06-08T00:00:00Z",
        ],
        backend_override=be,
        allowed_layers=["domain"],
    )
    assert rc == 0
    runs = _j.loads((lib / ".kb-offline" / "runs.json").read_text())
    assert any(r["state"] in ("completed", "completed_with_errors") for r in runs["runs"].values())
    # both sources' pages created
    pages = {p.name for p in lib.glob("*.md")} - {"_shelf-index.md", "log.md"}
    assert len(pages) == 2


def test_cli_ingest_bulk_clamps_parallel_and_cleans_up_on_error(tmp_path):
    import json as _j
    from sdlc_knowledge_base_scripts import kb_offline_cli as cli
    from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend

    lib = _seed_lib(tmp_path)
    s = tmp_path / "s0.md"
    s.write_text("source 0")
    extract_payload = _j.dumps(
        {
            "source": str(s),
            "findings": ["f"],
            "confidence": "low",
            "targets": [{"new_topic_slug": "t", "title": "t", "finding_idx": [0]}],
        }
    )
    be = FakeBackend()

    def gen(prompt, schema=None):
        if "Routed extracts" in prompt:
            raise RuntimeError("boom in reduce")
        return extract_payload

    be.generate = gen
    import pytest

    with pytest.raises(RuntimeError):
        cli.main(
            [
                "ingest-bulk",
                str(s),
                "--library",
                str(lib),
                "--backend",
                "fake",
                "--parallel",
                "999",
                "--timestamp",
                "2026-06-08T00:00:00Z",
            ],
            backend_override=be,
            allowed_layers=["domain"],
        )
    assert not (lib / ".kb-offline" / "lock.json").exists(), "lock leaked"
    runs = _j.loads((lib / ".kb-offline" / "runs.json").read_text())
    assert any(r["state"] == "failed" for r in runs["runs"].values())


def test_cli_query_prints_answer(tmp_path, capsys):
    import json as _j
    from sdlc_knowledge_base_scripts import kb_offline_cli as cli
    from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend

    lib = _seed_lib(tmp_path)
    (lib / "a.md").write_text("---\nlayer: evidence\nconfidence: high\n---\n# A\ncost fell 30%\n")
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n- a.md\n")

    def gen(prompt, schema=None):
        if prompt.startswith("Judge"):
            return '{"status": "supported"}'
        if "Shelf-index" in prompt:
            return _j.dumps({"page_ids": ["a.md"]})
        return _j.dumps(
            {
                "claims": [
                    {
                        "text": "Cost fell 30%.",
                        "cited_pages": [{"library": "local", "page": "a.md"}],
                        "evidence_spans": [{"page": "a.md", "text": "cost fell 30%"}],
                    }
                ],
                "rendered_text": "",
            }
        )

    be = FakeBackend()
    be.generate = gen
    rc = cli.main(
        ["query", "what about cost?", "--library", str(lib), "--backend", "fake"],
        backend_override=be,
    )
    assert rc == 0
    assert "Cost fell 30%." in capsys.readouterr().out


def test_cli_query_save_persists_ref(tmp_path, capsys):
    import json as _j
    from sdlc_knowledge_base_scripts import kb_offline_cli as cli
    from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
    from sdlc_knowledge_base_scripts.answers import load_answer
    lib = _seed_lib(tmp_path)
    (lib / "a.md").write_text("---\nlayer: evidence\nconfidence: high\n---\n# A\ncost fell 30%\n")
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n- a.md\n")

    def gen(prompt, schema=None):
        if prompt.startswith("Judge"):
            return '{"status": "supported"}'
        if "Shelf-index" in prompt:
            return _j.dumps({"page_ids": ["a.md"]})
        return _j.dumps({"claims": [{"text": "Cost fell 30%.",
                                     "cited_pages": [{"library": "local", "page": "a.md"}],
                                     "evidence_spans": [{"page": "a.md", "text": "cost fell 30%"}]}],
                         "rendered_text": ""})
    be = FakeBackend()
    be.generate = gen
    rc = cli.main(["query", "what about cost?", "--library", str(lib), "--backend", "fake", "--save"],
                  backend_override=be)
    assert rc == 0
    out = capsys.readouterr().out
    assert "saved:" in out
    ref = out.split("saved:")[1].split()[0].strip()
    saved = load_answer(str(lib), ref)
    assert saved.answer.claims[0].text == "Cost fell 30%."


def test_cli_promote_creates_page(tmp_path, capsys):
    import json as _j
    from sdlc_knowledge_base_scripts import kb_offline_cli as cli
    from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
    from sdlc_knowledge_base_scripts.answers import save_answer
    from sdlc_knowledge_base_scripts.contracts import Answer, Claim, EntailmentStatus, PageRef, Span
    lib = _seed_lib(tmp_path)
    (lib / "dora.md").write_text("---\nlayer: evidence\nconfidence: high\n---\n# DORA\n"
                                 "Elite teams deploy multiple times per day.\n")
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n- dora.md\n")
    c = Claim(text="Elite teams deploy multiple times per day.",
              cited_pages=[PageRef(library="local", page="dora.md")],
              evidence_spans=[Span(page="dora.md", text="deploy multiple times per day")])
    c.entailment_status = EntailmentStatus.supported
    ref = save_answer(str(lib), "how often deploy?", Answer(claims=[c], rendered_text="..."),
                      libraries=["local"], page_ids=["dora.md"])

    be = FakeBackend()
    be.generate = lambda prompt, schema=None: _j.dumps({"body": "# Deploy\n\nElite teams deploy multiple times per day."})
    rc = cli.main(["promote", ref, "--new", "deploy", "--library", str(lib),
                   "--backend", "fake", "--timestamp", "20260611T000000Z"], backend_override=be)
    assert rc == 0
    assert (lib / "deploy.md").is_file()
    assert "promoted 1" in capsys.readouterr().out


def test_cli_query_libraries_federates(tmp_path, capsys):
    import json as _j
    from sdlc_knowledge_base_scripts import kb_offline_cli as cli
    from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend

    def _seed(name, page, body):
        lib = tmp_path / name
        lib.mkdir()
        (lib / "_shelf-index.md").write_text(f"<!-- format_version: 1 -->\n# Shelf\n- {page}\n")
        (lib / page).write_text(f"---\nlayer: evidence\nconfidence: high\n---\n# {page}\n{body}\n")
        return lib
    local = _seed("local", "dora.md", "Elite teams deploy multiple times per day.")
    ext = _seed("acme", "ops.md", "Use canary deploys for safety.")

    def gen(prompt, schema=None):
        if prompt.startswith("Judge"):
            return '{"status": "supported"}'
        if "Shelf-index" in prompt:
            return _j.dumps({"page_ids": ["dora.md"]}) if "dora.md" in prompt else _j.dumps({"page_ids": ["ops.md"]})
        if "dora.md" in prompt:
            return _j.dumps({"claims": [{"text": "Elite teams deploy multiple times per day.",
                                         "cited_pages": [{"library": "local", "page": "dora.md"}],
                                         "evidence_spans": [{"page": "dora.md", "text": "deploy multiple times per day"}]}],
                             "rendered_text": ""})
        return _j.dumps({"claims": [{"text": "Use canary deploys for safety.",
                                     "cited_pages": [{"library": "local", "page": "ops.md"}],
                                     "evidence_spans": [{"page": "ops.md", "text": "canary deploys for safety"}]}],
                         "rendered_text": ""})
    be = FakeBackend()
    be.generate = gen
    rc = cli.main(["query", "how do teams deploy?", "--library", str(local),
                   "--libraries", "acme-kb", "--backend", "fake"],
                  backend_override=be, library_specs_override=[["local", str(local)], ["acme-kb", str(ext)]])
    assert rc == 0
    out = capsys.readouterr().out
    assert "queried 2 libraries" in out
    assert "Use canary deploys for safety." in out and "acme-kb" in out


def test_cli_federation_passes_project_root_for_priming(tmp_path, monkeypatch):
    # Regression: local_project_dir must be the PROJECT ROOT (parent of the library
    # dir), not the library dir itself — otherwise build_priming_bundle looks for
    # <library>/CLAUDE.md and <library>/library/_shelf-index.md and priming is silently
    # a no-op in the real CLI path.
    from sdlc_knowledge_base_scripts import kb_offline_cli as cli
    from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
    from sdlc_knowledge_base_scripts.graphs import federation_query_graph as fqg

    project = tmp_path / "proj"
    project.mkdir()
    lib = project / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n- dora.md\n")
    (lib / "dora.md").write_text("---\nlayer: evidence\nconfidence: high\n---\n# DORA\nx\n")

    captured = {}

    class _StubGraph:
        def invoke(self, state, config=None):
            captured["local_project_dir"] = state["local_project_dir"]
            return {"rendered_text": "", "rejected_claims": [], "_answer": {"claims": []},
                    "queried": 1, "deduped": 0}

    monkeypatch.setattr(fqg, "build_federation_query_graph", lambda *a, **k: _StubGraph())
    be = FakeBackend()
    rc = cli.main(["query", "q?", "--library", str(lib), "--libraries", "acme-kb", "--backend", "fake"],
                  backend_override=be, library_specs_override=[["local", str(lib)]])
    assert rc == 0
    assert captured["local_project_dir"] == str(project)  # project root, not the library dir


def test_cli_lint_reports_and_exit_code(tmp_path, capsys):
    from datetime import datetime, timedelta, timezone
    from sdlc_knowledge_base_scripts import kb_offline_cli as cli
    from sdlc_knowledge_base_scripts.registry import LibrarySource

    def _lib(name, rebuilt_days_ago, page_body):
        lib = tmp_path / name
        lib.mkdir()
        rebuilt = (datetime.now(timezone.utc) - timedelta(days=rebuilt_days_ago)).isoformat()
        (lib / "_shelf-index.md").write_text(f"<!-- format_version: 1 -->\n<!-- last_rebuilt: {rebuilt} -->\n# Shelf\n")
        (lib / "a.md").write_text(page_body)
        return lib
    local = _lib("local", 1, "---\nlayer: evidence\nconfidence: high\ncross_references: []\n---\n# A\n")
    corp = _lib("corp-x", 200, "---\nlayer: evidence\nconfidence: high\ncross_references: []\n---\n# A\n")
    sources = [LibrarySource(name="local", type="filesystem", path=str(local)),
               LibrarySource(name="corp-x", type="filesystem", path=str(corp))]
    rc = cli.main(["lint", "--library", str(local), "--libraries", "corp-x"], sources_override=sources)
    out = capsys.readouterr().out
    assert "corp-x" in out and "STALE" in out
    assert rc == 1


def test_cli_lint_clean_exits_zero(tmp_path, capsys):
    from datetime import datetime, timedelta, timezone
    from sdlc_knowledge_base_scripts import kb_offline_cli as cli
    from sdlc_knowledge_base_scripts.registry import LibrarySource
    lib = tmp_path / "local"
    lib.mkdir()
    rebuilt = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    (lib / "_shelf-index.md").write_text(f"<!-- format_version: 1 -->\n<!-- last_rebuilt: {rebuilt} -->\n# Shelf\n")
    (lib / "a.md").write_text("---\nlayer: evidence\nconfidence: high\ncross_references: []\n---\n# A\n")
    rc = cli.main(["lint", "--library", str(lib)],
                  sources_override=[LibrarySource(name="local", type="filesystem", path=str(lib))])
    assert rc == 0
    assert "clean" in capsys.readouterr().out.lower()


def test_cli_index_builds_and_is_incremental(tmp_path, capsys):
    from sdlc_knowledge_base_scripts import kb_offline_cli as cli
    from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
    from sdlc_knowledge_base_scripts.embeddings import EmbeddingStore
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n")
    (lib / "a.md").write_text("---\nlayer: evidence\n---\n# A\nAlpha content.\n")
    (lib / "b.md").write_text("# B\nBeta content.\n")
    be = FakeBackend()
    rc = cli.main(["index", "--library", str(lib), "--backend", "fake"], backend_override=be)
    assert rc == 0
    out = capsys.readouterr().out
    assert "indexed" in out.lower() and "2" in out
    store = EmbeddingStore.load(lib)
    assert store is not None and {r.page_id for r in store.rows} == {"a.md", "b.md"}
    assert store.provenance.model == "fake-embed"
    rc2 = cli.main(["index", "--library", str(lib), "--backend", "fake"], backend_override=be)
    assert rc2 == 0
    assert "0 re-embedded" in capsys.readouterr().out


def test_cli_index_removed_count(tmp_path, capsys):
    """Deleting a page produces an exact removed=1 in the summary, not a conflated count."""
    from sdlc_knowledge_base_scripts import kb_offline_cli as cli
    from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n")
    (lib / "a.md").write_text("# A\nAlpha content.\n")
    (lib / "b.md").write_text("# B\nBeta content.\n")
    be = FakeBackend()
    rc = cli.main(["index", "--library", str(lib), "--backend", "fake"], backend_override=be)
    assert rc == 0
    capsys.readouterr()  # discard initial build output

    # Remove b.md and re-index — should report exactly 1 removed
    (lib / "b.md").unlink()
    rc2 = cli.main(["index", "--library", str(lib), "--backend", "fake"], backend_override=be)
    assert rc2 == 0
    out = capsys.readouterr().out
    assert "1 removed" in out, f"expected '1 removed' in: {out!r}"


def test_cli_index_rejects_anthropic(tmp_path):
    import pytest
    from sdlc_knowledge_base_scripts import kb_offline_cli as cli
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "a.md").write_text("# A\n")
    with pytest.raises(SystemExit, match="does not support embeddings"):
        cli.main(["index", "--library", str(lib), "--backend", "anthropic"])


def test_cli_query_accelerate_flag_threads_through(tmp_path, capsys):
    import json as _j
    from sdlc_knowledge_base_scripts import kb_offline_cli as cli
    from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
    lib = _seed_lib(tmp_path)
    (lib / "a.md").write_text("---\nlayer: evidence\nconfidence: high\n---\n# A\ncost fell 30%\n")
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n- a.md\n")

    def gen(prompt, schema=None):
        if prompt.startswith("Judge"):
            return '{"status": "supported"}'
        if "Shelf-index" in prompt:
            return _j.dumps({"page_ids": ["a.md"]})
        return _j.dumps({"claims": [{"text": "Cost fell 30%.",
                                     "cited_pages": [{"library": "local", "page": "a.md"}],
                                     "evidence_spans": [{"page": "a.md", "text": "cost fell 30%"}]}],
                         "rendered_text": ""})
    be = FakeBackend()
    be.generate = gen
    rc = cli.main(["query", "what about cost?", "--library", str(lib), "--backend", "fake", "--accelerate"],
                  backend_override=be)
    assert rc == 0
    assert "Cost fell 30%." in capsys.readouterr().out


def test_accelerate_k_below_one_is_rejected():
    import pytest as _pytest
    from sdlc_knowledge_base_scripts.kb_offline_cli import main
    with _pytest.raises(SystemExit):
        main(["query", "q", "--libraries", "acme", "--accelerate", "--accelerate-k", "0"])


def test_accelerate_routes_to_accel_then_falls_back_to_m2b(tmp_path, monkeypatch, capsys):
    from sdlc_knowledge_base_scripts import kb_offline_cli
    from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend

    calls = {"accel": 0, "m2b": 0}
    captured_kw = {}

    def fake_accel(local_lib, specs, question, **kw):
        calls["accel"] += 1
        captured_kw.update(kw)
        return None                      # force the fallback path

    class _Graph:
        def invoke(self, state, config=None):
            calls["m2b"] += 1
            return {"rendered_text": "FELL BACK", "rejected_claims": [],
                    "_answer": {"claims": []}, "queried": 1, "deduped": 0}

    monkeypatch.setattr("sdlc_knowledge_base_scripts.federation_accel.accelerated_federation_query",
                        fake_accel)
    monkeypatch.setattr(
        "sdlc_knowledge_base_scripts.graphs.federation_query_graph.build_federation_query_graph",
        lambda backend: _Graph())

    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n", encoding="utf-8")
    specs = [["library", str(lib)], ["acme", str(lib)]]
    rc = kb_offline_cli.main(
        ["query", "q", "--library", str(lib), "--libraries", "acme", "--accelerate",
         "--accelerate-k", "7", "--layer", "evidence", "--min-confidence", "medium"],
        backend_override=FakeBackend(), library_specs_override=specs)
    assert rc == 0
    assert calls["accel"] == 1 and calls["m2b"] == 1
    assert "FELL BACK" in capsys.readouterr().out
    # _cmd_query must forward the non-default flags into accelerated_federation_query
    assert captured_kw["search_k"] == 7          # from --accelerate-k 7 (default is 20)
    assert captured_kw["layer"] == "evidence"    # from --layer
    assert captured_kw["min_confidence"] == "medium"  # from --min-confidence


def test_accelerate_uses_accel_result_when_not_none(tmp_path, monkeypatch, capsys):
    from sdlc_knowledge_base_scripts import kb_offline_cli
    from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend

    def fake_accel(local_lib, specs, question, **kw):
        return {"rendered_text": "ACCEL ANSWER", "rejected_claims": [],
                "_answer": {"claims": []}, "queried": 2, "deduped": 0}

    monkeypatch.setattr("sdlc_knowledge_base_scripts.federation_accel.accelerated_federation_query",
                        fake_accel)
    lib = tmp_path / "library"
    lib.mkdir()
    specs = [["library", str(lib)], ["acme", str(lib)]]
    rc = kb_offline_cli.main(
        ["query", "q", "--library", str(lib), "--libraries", "acme", "--accelerate"],
        backend_override=FakeBackend(), library_specs_override=specs)
    assert rc == 0
    assert "ACCEL ANSWER" in capsys.readouterr().out


def _build_store_lib_cli(tmp_path, pages, vectors):
    import numpy as np
    from sdlc_knowledge_base_scripts.build_shelf_index import rebuild_shelf_index
    from sdlc_knowledge_base_scripts.embeddings import (
        EmbeddingStore, IndexRow, Provenance, chunk_pages, corpus_hash)
    lib = tmp_path / "library"
    lib.mkdir()
    for pid, body in pages.items():
        (lib / pid).write_text(f"---\nlayer: evidence\nconfidence: high\n---\n# {pid}\n{body}\n",
                               encoding="utf-8")
    rebuild_shelf_index(lib, lib / "_shelf-index.md", full=True)
    rows = chunk_pages(lib)
    ch = corpus_hash([(pid, h) for pid, _, h in rows])
    dims = len(next(iter(vectors.values())))
    mat = np.array([vectors[pid] for pid, _, _ in rows], dtype=np.float32)
    irows = [IndexRow(page_id=pid, content_hash=h) for pid, _, h in rows]
    EmbeddingStore.from_rows(mat, irows,
                             Provenance(model="m", dims=dims, normalization="l2",
                                        corpus_hash=ch)).save(lib)
    return lib


def test_fingerprint_export_writes_artifact(tmp_path):
    lib = _build_store_lib_cli(tmp_path, {"a.md": "x", "b.md": "y"},
                               {"a.md": [1.0, 0.0], "b.md": [0.0, 1.0]})
    out = tmp_path / "acme.kbfp.json"
    rc = cli.main(["fingerprint", "export", "--library", str(lib), "--tier", "page",
                   "--handle", "acme", "--out", str(out)])
    assert rc == 0 and out.is_file()
    art = json.loads(out.read_text())
    assert art["tier"] == "page" and art["manifest"]["handle"] == "acme"
    assert len(art["vectors"]) == 2


def test_fingerprint_export_requires_tier(tmp_path):
    import pytest as _pytest
    with _pytest.raises(SystemExit):
        cli.main(["fingerprint", "export", "--library", str(tmp_path)])


def test_fingerprint_export_no_store_errors(tmp_path):
    lib = tmp_path / "library"
    lib.mkdir()
    rc = cli.main(["fingerprint", "export", "--library", str(lib), "--tier", "page"])
    assert rc == 1


def test_fingerprint_export_freshness_gate(tmp_path):
    lib = _build_store_lib_cli(tmp_path, {"a.md": "x"}, {"a.md": [1.0, 0.0]})
    (lib / "a.md").write_text("---\nlayer: evidence\nconfidence: high\n---\n# a\nCHANGED\n",
                              encoding="utf-8")          # corpus drifts from the index
    out = tmp_path / "a.kbfp.json"
    assert cli.main(["fingerprint", "export", "--library", str(lib), "--tier", "page",
                     "--out", str(out)]) == 1            # stale -> refuse
    assert cli.main(["fingerprint", "export", "--library", str(lib), "--tier", "page",
                     "--out", str(out), "--allow-stale"]) == 0


# ---------------------------------------------------------------------------
# discover subcommand tests
# ---------------------------------------------------------------------------

def _fake_embed_backend(vec):
    be = FakeBackend()
    be.embed = lambda texts: [list(vec)]      # type: ignore
    return be


def _cli_fp(vectors, *, handle, model="fake-embed", tier="page", owner="Acme", contact=None):
    import numpy as np
    from sdlc_knowledge_base_scripts.embeddings import Provenance
    from sdlc_knowledge_base_scripts.fingerprint import Fingerprint, Manifest
    return Fingerprint(
        tier=tier, manifest=Manifest(handle=handle, owner=owner, contact=contact),
        provenance=Provenance(model=model, dims=len(vectors[0]), normalization="l2", corpus_hash=""),
        vectors=np.array(vectors, dtype=np.float32))


def test_discover_prints_ranked_list(tmp_path, capsys):
    fps = [_cli_fp([[0.0, 0.0, 1.0]], handle="off-topic"),
           _cli_fp([[1.0, 0.0, 0.0]], handle="on-topic", contact="kb@acme.example")]
    rc = cli.main(["discover", "how often deploy?"],
                  backend_override=_fake_embed_backend([1.0, 0.0, 0.0]),
                  fingerprints_override=fps)
    assert rc == 0
    out = capsys.readouterr().out
    # on-topic ranked first, contact + tier rendered
    assert out.index("on-topic") < out.index("off-topic")
    assert "kb@acme.example" in out and "page" in out


def test_discover_no_fingerprints_exits_zero(capsys):
    rc = cli.main(["discover", "q"], backend_override=_fake_embed_backend([1.0, 0.0]),
                  fingerprints_override=[])
    assert rc == 0
    assert "no covering libraries" in capsys.readouterr().out.lower()


def test_discover_requires_embedding_backend():
    class _NoEmbed:                            # like AnthropicBackend: no embedding_model_id
        def generate(self, prompt, schema=None):
            return "{}"
    rc = cli.main(["discover", "q"], backend_override=_NoEmbed(), fingerprints_override=[])
    assert rc == 2


# ---------------------------------------------------------------------------
# eval release trace tests (Task 8)
# ---------------------------------------------------------------------------

def _eval_smoke_gen():
    import json as _j

    def gen(prompt, schema=None):
        if prompt.startswith("Judge"):
            return '{"status": "supported"}'
        if "Shelf-index" in prompt:
            return _j.dumps({"page_ids": ["dora.md"]}) if "deploy" in prompt else _j.dumps({"page_ids": []})
        return _j.dumps({"claims": [], "rendered_text": ""})
    return gen


def test_eval_release_writes_trace_by_default(tmp_path):
    be = FakeBackend()
    be.generate = _eval_smoke_gen()
    rc = cli.main(["eval", "release", "--suite", "plugins/sdlc-knowledge-base/eval/suite/smoke",
                   "--runs", "1", "--stamp", "T1", "--report-dir", str(tmp_path), "--model", "gemma4:12b"],
                  backend_override=be)
    assert rc in (0, 1)
    traces = list(tmp_path.glob("trace-gemma4_12b-T1-run1.jsonl"))
    assert len(traces) == 1
    lines = [json.loads(x) for x in traces[0].read_text().splitlines() if x.strip()]
    assert any(r["type"] == "question" for r in lines)
    assert any(r["type"] == "verifier" for r in lines)


def test_eval_release_no_trace_suppresses(tmp_path):
    be = FakeBackend()
    be.generate = _eval_smoke_gen()
    cli.main(["eval", "release", "--suite", "plugins/sdlc-knowledge-base/eval/suite/smoke",
              "--runs", "1", "--stamp", "T2", "--report-dir", str(tmp_path), "--model", "gemma4:12b",
              "--no-trace"], backend_override=be)
    assert list(tmp_path.glob("trace-*.jsonl")) == []
    assert list(tmp_path.glob("release-gemma4_12b-T2.md"))


def test_cli_query_surfaces_abstention(tmp_path, capsys):
    """A single-library query whose select abstains prints the answer (empty) then
    `[abstained: <reason>]` to stderr and exits 0 (#211, Task 13)."""
    lib = _seed_lib(tmp_path)
    (lib / "a.md").write_text("---\nlayer: evidence\nconfidence: high\n---\n# A\nirrelevant\n")
    (lib / "_shelf-index.md").write_text(
        "<!-- format_version: 1 -->\n# Shelf\n\n## 1. a.md\nLayer: evidence\nTerms: x\n")

    def gen(prompt, schema=None):
        if "Pages:" in prompt or prompt.startswith("Judge"):
            raise AssertionError("must not synthesize/judge after abstain")
        return json.dumps({"page_ids": [], "no_relevant_page": True, "abstention_reason": "nothing fits"})

    be = FakeBackend()
    be.generate = gen
    rc = cli.main(["query", "unrelated?", "--library", str(lib), "--backend", "fake"],
                  backend_override=be)
    assert rc == 0
    err = capsys.readouterr().err
    assert "[abstained: nothing fits]" in err


def test_cli_federation_surfaces_abstention(tmp_path, capsys):
    """When every library abstains, the federated CLI prints the generic federated reason
    to stderr (#211, Task 13)."""
    def _seed(name, page, body):
        lib = tmp_path / name
        lib.mkdir()
        (lib / "_shelf-index.md").write_text(
            f"<!-- format_version: 1 -->\n# Shelf\n\n## 1. {page}\nLayer: evidence\nTerms: x\n")
        (lib / page).write_text(f"---\nlayer: evidence\nconfidence: high\n---\n# {page}\n{body}\n")
        return lib
    local = _seed("local", "dora.md", "Elite teams deploy daily.")
    ext = _seed("acme", "ops.md", "Use canary deploys.")

    def gen(prompt, schema=None):
        if "Pages:" in prompt or prompt.startswith("Judge"):
            raise AssertionError("must not synthesize/judge when all abstain")
        return json.dumps({"page_ids": [], "no_relevant_page": True, "abstention_reason": "nope"})

    be = FakeBackend()
    be.generate = gen
    rc = cli.main(["query", "unrelated?", "--library", str(local),
                   "--libraries", "acme-kb", "--backend", "fake"],
                  backend_override=be, library_specs_override=[["local", str(local)], ["acme-kb", str(ext)]])
    assert rc == 0
    assert "[abstained: no library produced a supported answer]" in capsys.readouterr().err
