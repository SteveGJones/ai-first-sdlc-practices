"""End-to-end `eval smoke` via FakeBackend (CI). kb-offline M1c-2 (#211)."""
from __future__ import annotations

import json

from sdlc_knowledge_base_scripts import kb_offline_cli as cli
from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend


def test_cli_eval_smoke_runs_and_reports(capsys):
    be = FakeBackend()

    def gen(prompt, schema=None):
        if prompt.startswith("Judge"):
            return '{"status": "supported"}'
        if "Shelf-index" in prompt:
            return json.dumps({"page_ids": ["dora.md"]}) if "deploy" in prompt else json.dumps({"page_ids": []})
        return json.dumps({"claims": [], "rendered_text": ""})
    be.generate = gen
    rc = cli.main(["eval", "smoke", "--backend", "fake"], backend_override=be)
    assert rc == 0
    out = capsys.readouterr().out
    assert "fact_recall" in out
    assert "smoke" in out.lower()


def test_cli_eval_release_writes_md_and_json_sidecar(tmp_path):
    import json as _j
    from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend

    be = FakeBackend()

    def gen(prompt, schema=None):
        if prompt.startswith("Judge"):
            return '{"status": "supported"}'
        if "Shelf-index" in prompt:
            return _j.dumps({"page_ids": ["dora.md"]}) if "deploy" in prompt else _j.dumps({"page_ids": []})
        return _j.dumps({"claims": [], "rendered_text": ""})
    be.generate = gen
    report_dir = tmp_path / "out"
    # release over the smoke suite for speed; backend_override short-circuits to the fake
    rc = cli.main(["eval", "release", "--suite", "plugins/sdlc-knowledge-base/eval/suite/smoke",
                   "--backend", "fake", "--model", "gpt-oss:20b", "--runs", "1",
                   "--report-dir", str(report_dir), "--stamp", "20260610T000000Z"],
                  backend_override=be)
    md = report_dir / "release-gpt-oss_20b-20260610T000000Z.md"
    js = report_dir / "release-gpt-oss_20b-20260610T000000Z.json"
    assert md.is_file() and js.is_file()
    data = _j.loads(js.read_text())
    assert data["model"] == "gpt-oss:20b" and data["stamp"] == "20260610T000000Z"
    assert "metrics" in data and "verdict" in data
    assert rc in (0, 1)   # gate verdict either way; both files must exist regardless
