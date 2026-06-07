"""Eval metric functions (issue #211, M0 skeleton). M1 wires these to a frozen release
suite (75-100 questions, >=20 no-evidence, pinned config, 3 runs)."""
from __future__ import annotations


def fact_recall(rows: list[dict]) -> float:
    """Macro-averaged recall of expected facts across questions."""
    if not rows:
        return 0.0
    per_q = []
    for r in rows:
        expected = set(r["expected"])
        found = set(r["found"])
        per_q.append(len(expected & found) / len(expected) if expected else 1.0)
    return sum(per_q) / len(per_q)


def routing_scores(rows: list[dict]) -> tuple[float, float]:
    """Micro recall + precision of routing targets across rows."""
    tp = fn = fp = 0
    for r in rows:
        expected, predicted = set(r["expected"]), set(r["predicted"])
        tp += len(expected & predicted)
        fn += len(expected - predicted)
        fp += len(predicted - expected)
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    precision = tp / (tp + fp) if (tp + fp) else 1.0
    return recall, precision


def abstention_scores(rows: list[tuple[bool, bool]]) -> tuple[float, float]:
    """rows = (should_abstain, did_abstain). Returns (precision, recall) of abstention."""
    tp = sum(1 for s, d in rows if s and d)
    predicted = sum(1 for _, d in rows if d)
    actual = sum(1 for s, _ in rows if s)
    precision = tp / predicted if predicted else 1.0
    recall = tp / actual if actual else 1.0
    return precision, recall
