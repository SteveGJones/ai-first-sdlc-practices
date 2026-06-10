"""Aggregate + gate + render tests (CI; no models). kb-offline M1c-2 (#211)."""
from __future__ import annotations

from sdlc_knowledge_base_scripts.eval.report import aggregate, gate, render_report


def _run(fact, routing_r, routing_p, abst_p, abst_r, ver_p, ver_r, json_v, floor=1.0):
    return {
        "fact_recall": fact, "routing_recall": routing_r, "routing_precision": routing_p,
        "abstention_precision": abst_p, "abstention_recall": abst_r,
        "verifier_precision": ver_p, "verifier_recall": ver_r,
        "first_pass_json_validity": json_v, "clean_published_support_rate": 1.0,
        "invalid_mutation_rejection_floor": floor, "citation_validity_floor": floor,
        "post_repair_json_validity_floor": floor,
    }


def test_aggregate_reports_mean_and_stddev():
    runs = [_run(0.86, 0.92, 0.82, 0.96, 0.91, 0.99, 0.96, 0.96),
            _run(0.88, 0.91, 0.81, 0.96, 0.92, 0.99, 0.96, 0.97),
            _run(0.90, 0.93, 0.83, 0.97, 0.90, 0.98, 0.95, 0.96)]
    agg = aggregate(runs)
    assert abs(agg["fact_recall"]["mean"] - 0.88) < 1e-9
    assert agg["fact_recall"]["stddev"] < 0.05
    assert agg["fact_recall"]["runs"] == [0.86, 0.88, 0.90]


def test_gate_passes_when_means_clear_and_variance_low():
    runs = [_run(0.86, 0.92, 0.82, 0.96, 0.91, 0.99, 0.96, 0.96),
            _run(0.88, 0.91, 0.81, 0.96, 0.92, 0.99, 0.96, 0.97),
            _run(0.90, 0.93, 0.83, 0.97, 0.90, 0.98, 0.95, 0.96)]
    verdict = gate(aggregate(runs))
    assert verdict["passed"] is True


def test_gate_fails_on_high_variance_even_if_mean_clears():
    runs = [_run(0.99, 0.92, 0.82, 0.96, 0.91, 0.99, 0.96, 0.96),
            _run(0.99, 0.91, 0.81, 0.96, 0.92, 0.99, 0.96, 0.97),
            _run(0.70, 0.93, 0.83, 0.97, 0.90, 0.98, 0.95, 0.96)]
    verdict = gate(aggregate(runs))
    assert verdict["passed"] is False
    assert "fact_recall" in verdict["failures"]


def test_gate_fails_when_safety_floor_below_one_on_any_run():
    runs = [_run(0.90, 0.95, 0.85, 0.97, 0.95, 0.99, 0.97, 0.99),
            _run(0.90, 0.95, 0.85, 0.97, 0.95, 0.99, 0.97, 0.99, floor=0.98),
            _run(0.90, 0.95, 0.85, 0.97, 0.95, 0.99, 0.97, 0.99)]
    verdict = gate(aggregate(runs))
    assert verdict["passed"] is False
    assert any("floor" in f for f in verdict["failures"])


def test_render_report_contains_verdict_and_recommendation():
    runs = [_run(0.90, 0.95, 0.85, 0.97, 0.95, 0.99, 0.97, 0.99)] * 3
    agg = aggregate(runs)
    text = render_report(agg, gate(agg), model="gpt-oss:20b")
    assert "gpt-oss:20b" in text
    assert "PASS" in text
    assert "default" in text.lower()
