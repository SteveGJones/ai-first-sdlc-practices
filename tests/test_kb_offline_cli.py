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
