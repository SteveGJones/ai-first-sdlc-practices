"""Federation query tests. kb-offline M2b (#211)."""
from __future__ import annotations

import json

from sdlc_knowledge_base_scripts.audit import VALID_EVENT_TYPES
from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend
from sdlc_knowledge_base_scripts.contracts import EntailmentStatus
from sdlc_knowledge_base_scripts.federation import query_one_library


def test_cross_library_query_is_a_valid_event_type():
    assert "cross_library_query" in VALID_EVENT_TYPES


def _lib(tmp_path, name, page, body):
    lib = tmp_path / name
    lib.mkdir()
    (lib / "_shelf-index.md").write_text(f"<!-- format_version: 1 -->\n# Shelf\n- {page}\n")
    (lib / page).write_text(f"---\nlayer: evidence\nconfidence: high\n---\n# {page}\n{body}\n")
    return lib


def test_query_one_library_returns_verified_answer(tmp_path):
    lib = _lib(tmp_path, "doracorp", "dora.md", "Elite teams deploy multiple times per day.")

    def gen(prompt, schema=None):
        if prompt.startswith("Judge"):
            return '{"status": "supported"}'
        if "Shelf-index" in prompt:
            return json.dumps({"page_ids": ["dora.md"]})
        return json.dumps({"claims": [{"text": "Elite teams deploy multiple times per day.",
                                       "cited_pages": [{"library": "local", "page": "dora.md"}],
                                       "evidence_spans": [{"page": "dora.md",
                                                           "text": "deploy multiple times per day"}]}],
                           "rendered_text": ""})
    be = FakeBackend()
    be.generate = gen
    answer, page_ids = query_one_library(str(lib), "how often deploy?", backend=be, priming=None)
    assert page_ids == ["dora.md"]
    assert answer.claims[0].entailment_status == EntailmentStatus.supported
