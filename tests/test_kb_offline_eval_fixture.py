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


def test_full_fixture_meets_release_spec():
    pages = _page_names(SUITE / "library")
    # _shelf-index.md / log.md / _index.md are infra, not content
    content_pages = {p for p in pages if p not in {"_shelf-index.md", "log.md", "_index.md"}}
    assert len(content_pages) >= 12, "full library should have >=12 content pages"
    assert (SUITE / "library" / "_shelf-index.md").is_file(), "library needs a _shelf-index.md"
    qs = load_questions(SUITE / "questions.jsonl")
    assert len(qs) >= 80, f"need >=80 questions, have {len(qs)}"
    no_ev = [q for q in qs if q.no_evidence]
    assert len(no_ev) >= 20, f"need >=20 no-evidence questions, have {len(no_ev)}"
    ids = [q.id for q in qs]
    assert len(ids) == len(set(ids)), "duplicate question ids"
    for q in qs:
        for t in q.expected_routing_targets:
            assert t in content_pages, f"{q.id} routes to unknown page {t}"
        if q.no_evidence:
            assert not q.expected_routing_targets and not q.expected_facts

    labels = load_verifier_labels(SUITE / "verifier_labels.jsonl")
    assert len(labels) >= 20, f"need >=20 verifier labels, have {len(labels)}"
    statuses = {lb.gold_status for lb in labels}
    assert {"supported", "partial", "unsupported"} <= statuses, "need all 3 gold statuses"

    def norm(s):
        return " ".join(s.lower().split())
    page_text = {p.name: norm((SUITE / "library" / p.name).read_text(encoding="utf-8"))
                 for p in (SUITE / "library").glob("*.md")}
    for lb in labels:
        if lb.gold_status == "supported":
            for sp in lb.evidence_spans:
                assert sp.page in page_text, f"{lb.id} cites unknown page {sp.page}"
                assert norm(sp.text) in page_text[sp.page], \
                    f"{lb.id} supported span not verbatim in {sp.page}"


def test_full_fixture_fact_questions_are_answerable():
    """Every non-abstention question's expected_facts must appear (normalized) in its
    routing-target page bodies — else the live fact-recall metric would measure fixture
    bugs, not the model."""
    def norm(s):
        return " ".join(s.lower().split())
    lib = SUITE / "library"
    page_text = {p.name: norm(p.read_text(encoding="utf-8")) for p in lib.glob("*.md")}
    broken = []
    for q in load_questions(SUITE / "questions.jsonl"):
        if q.no_evidence:
            continue
        corpus = " ".join(page_text.get(t, "") for t in q.expected_routing_targets)
        for fact in q.expected_facts:
            if norm(fact) not in corpus:
                broken.append(f"{q.id}: {fact!r} not in {q.expected_routing_targets}")
    assert not broken, "unanswerable fact questions:\n" + "\n".join(broken)
