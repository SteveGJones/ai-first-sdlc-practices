"""Fixture structural-validation tests. kb-offline M1c-2 (#211)."""
from __future__ import annotations

from pathlib import Path

from sdlc_knowledge_base_scripts.eval.suite import load_questions, load_verifier_labels

SUITE = Path("plugins/sdlc-knowledge-base/eval/suite")
SMOKE = SUITE / "smoke"


def _page_names(lib: Path) -> set[str]:
    return {p.name for p in lib.glob("*.md")}


def test_smoke_fixture_is_consistent():
    pages = _page_names(SMOKE / "library")
    assert pages, "smoke library has no pages"
    qs = load_questions(SMOKE / "questions.jsonl")
    assert len(qs) >= 5
    for q in qs:
        for t in q.expected_routing_targets:
            assert t in pages, f"{q.id} routes to unknown page {t}"
    labels = load_verifier_labels(SMOKE / "verifier_labels.jsonl")
    assert len(labels) >= 3
    assert any(lb.gold_status == "unsupported" for lb in labels)
