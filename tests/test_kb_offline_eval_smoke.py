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
