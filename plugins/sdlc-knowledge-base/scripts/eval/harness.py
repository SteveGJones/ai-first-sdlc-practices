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


def verifier_accuracy(rows: list[dict]) -> tuple[float, float]:
    """Precision/recall of the verifier's safety-critical `supported` decision against
    gold labels. rows = [{predicted_status, gold_status}] (values: supported/partial/
    unsupported). precision = TP / predicted-supported; recall = TP / gold-supported.
    Empty denominators are vacuously 1.0 (consistent with the other scorers)."""
    tp = sum(1 for r in rows if r["predicted_status"] == "supported" and r["gold_status"] == "supported")
    predicted_supported = sum(1 for r in rows if r["predicted_status"] == "supported")
    gold_supported = sum(1 for r in rows if r["gold_status"] == "supported")
    precision = tp / predicted_supported if predicted_supported else 1.0
    recall = tp / gold_supported if gold_supported else 1.0
    return precision, recall


def first_pass_json_validity(rows: list[dict]) -> float:
    """Fraction of FIRST-attempt model calls whose raw output was valid JSON, before any
    repair. rows = [{first_pass: bool, valid_json: bool}]; repair calls (first_pass False)
    are excluded from both numerator and denominator."""
    first = [r for r in rows if r["first_pass"]]
    if not first:
        return 1.0
    return sum(1 for r in first if r["valid_json"]) / len(first)


def clean_published_support_rate(rows: list[dict]) -> float:
    """Of claims published WITHOUT a caveat, the fraction whose status is `supported`.
    rows = [{published_uncaveated: bool, status: str}]. Tautologically 1.0 under the
    publication policy; a value below 1.0 means a non-supported claim leaked into the
    uncaveated body (a regression). Caveated/unpublished claims are excluded."""
    uncaveated = [r for r in rows if r["published_uncaveated"]]
    if not uncaveated:
        return 1.0
    return sum(1 for r in uncaveated if r["status"] == "supported") / len(uncaveated)


def recall_at_k(rows: list[dict]) -> float:
    """Macro mean over rows of |expected ∩ shortlist| / |expected| (1.0 when expected is empty).
    rows = [{expected: list[str], shortlist: list[str]}]."""
    if not rows:
        return 1.0
    per = []
    for r in rows:
        expected = set(r["expected"])
        if not expected:
            per.append(1.0)
            continue
        per.append(len(expected & set(r["shortlist"])) / len(expected))
    return sum(per) / len(per)
