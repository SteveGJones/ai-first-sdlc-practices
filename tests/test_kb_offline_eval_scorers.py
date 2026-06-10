"""Scorer-correctness tests (CI; no models). kb-offline M1c-2 (#211)."""
from __future__ import annotations

from sdlc_knowledge_base_scripts.eval.harness import (
    clean_published_support_rate,
    first_pass_json_validity,
    verifier_accuracy,
)
from sdlc_knowledge_base_scripts.eval import thresholds


def test_max_metric_stddev_ratified():
    assert thresholds.MAX_METRIC_STDDEV == 0.05


def test_verifier_accuracy_supported_class_precision_recall():
    rows = [
        {"predicted_status": "supported", "gold_status": "supported"},   # TP
        {"predicted_status": "supported", "gold_status": "partial"},     # FP
        {"predicted_status": "partial", "gold_status": "supported"},     # FN
        {"predicted_status": "unsupported", "gold_status": "unsupported"},
    ]
    precision, recall = verifier_accuracy(rows)
    assert precision == 0.5   # 1 TP / 2 predicted-supported
    assert recall == 0.5      # 1 TP / 2 gold-supported


def test_verifier_accuracy_empty_is_vacuously_one():
    assert verifier_accuracy([]) == (1.0, 1.0)


def test_first_pass_json_validity():
    rows = [
        {"first_pass": True, "valid_json": True},
        {"first_pass": True, "valid_json": False},
        {"first_pass": False, "valid_json": True},   # repair call — ignored
    ]
    assert first_pass_json_validity(rows) == 0.5   # of 2 first-pass calls, 1 valid


def test_clean_published_support_rate():
    rows = [
        {"published_uncaveated": True, "status": "supported"},
        {"published_uncaveated": True, "status": "supported"},
        {"published_uncaveated": False, "status": "partial"},   # caveated — ignored
    ]
    assert clean_published_support_rate(rows) == 1.0


def test_clean_published_support_rate_detects_leak():
    rows = [
        {"published_uncaveated": True, "status": "supported"},
        {"published_uncaveated": True, "status": "partial"},   # a leak: drops below 1.0
    ]
    assert clean_published_support_rate(rows) == 0.5
