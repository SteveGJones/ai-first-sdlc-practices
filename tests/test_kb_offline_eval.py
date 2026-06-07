"""Tests for the kb-offline eval harness skeleton."""
from __future__ import annotations

from sdlc_knowledge_base_scripts.eval import thresholds
from sdlc_knowledge_base_scripts.eval.harness import (
    abstention_scores,
    fact_recall,
    routing_scores,
)


def test_safety_floors_are_one():
    assert thresholds.INVALID_MUTATION_REJECTION == 1.0
    assert thresholds.CITATION_VALIDITY == 1.0
    assert thresholds.POST_REPAIR_JSON_VALIDITY == 1.0


def test_model_quality_thresholds_match_ratified_values():
    assert thresholds.CITATION_ENTAILMENT == 0.98
    assert thresholds.FACT_RECALL == 0.85
    assert thresholds.ROUTING_RECALL == 0.90
    assert thresholds.ROUTING_PRECISION == 0.80
    assert thresholds.ABSTENTION_PRECISION == 0.95
    assert thresholds.ABSTENTION_RECALL == 0.90
    assert thresholds.FIRST_PASS_JSON_VALIDITY == 0.95


def test_fact_recall_macro_average():
    got = fact_recall(
        [
            {"expected": ["a", "b"], "found": ["a"]},
            {"expected": ["c", "d"], "found": ["c", "d"]},
        ]
    )
    assert abs(got - 0.75) < 1e-9


def test_routing_scores_recall_precision():
    r, p = routing_scores(
        [{"expected": {"x.md", "y.md"}, "predicted": {"x.md", "z.md"}}]
    )
    assert abs(r - 0.5) < 1e-9 and abs(p - 0.5) < 1e-9


def test_abstention_scores():
    prec, rec = abstention_scores([(True, True), (False, True), (True, False)])
    assert abs(prec - 0.5) < 1e-9 and abs(rec - 0.5) < 1e-9
