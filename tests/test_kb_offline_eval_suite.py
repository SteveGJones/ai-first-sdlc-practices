"""Suite loader tests. kb-offline M1c-2 (#211)."""
from __future__ import annotations

from sdlc_knowledge_base_scripts.eval.suite import load_questions, load_verifier_labels


def test_load_questions(tmp_path):
    p = tmp_path / "questions.jsonl"
    p.write_text(
        '{"id":"q1","question":"how often deploy?","kind":"fact",'
        '"expected_facts":["multiple per day"],"expected_routing_targets":["dora.md"],'
        '"no_evidence":false}\n'
        '{"id":"q2","question":"what is X?","kind":"abstention","expected_facts":[],'
        '"expected_routing_targets":[],"no_evidence":true}\n',
        encoding="utf-8",
    )
    qs = load_questions(p)
    assert [q.id for q in qs] == ["q1", "q2"]
    assert qs[0].kind == "fact" and qs[0].expected_routing_targets == ["dora.md"]
    assert qs[1].no_evidence is True
    assert qs[0].expected_layer is None


def test_load_verifier_labels(tmp_path):
    p = tmp_path / "verifier_labels.jsonl"
    p.write_text(
        '{"id":"v1","claim_text":"cost fell 30%",'
        '"cited_pages":[{"library":"local","page":"dora.md"}],'
        '"evidence_spans":[{"page":"dora.md","text":"cost fell 30%"}],'
        '"gold_status":"supported"}\n',
        encoding="utf-8",
    )
    labels = load_verifier_labels(p)
    assert labels[0].id == "v1" and labels[0].gold_status == "supported"
    assert labels[0].cited_pages[0].page == "dora.md"


def test_load_questions_skips_blank_lines(tmp_path):
    p = tmp_path / "questions.jsonl"
    p.write_text('{"id":"q1","question":"q","kind":"fact","expected_facts":[],'
                 '"expected_routing_targets":[],"no_evidence":false}\n\n', encoding="utf-8")
    assert len(load_questions(p)) == 1
