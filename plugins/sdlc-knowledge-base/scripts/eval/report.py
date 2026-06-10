"""Aggregate the 3 pinned runs, gate against ratified thresholds + the variance cap, and
render the persisted report. kb-offline M1c-2 (#211)."""
from __future__ import annotations

import statistics

from . import thresholds

# Absorbs float rounding when an averaged metric lands exactly on its bar. Under pinned
# temperature=0 + fixed seed the 3 runs can be byte-identical, so a metric at its threshold
# (e.g. 0.95 on all 3) sums to 0.9499999999999998 < 0.95 and would spuriously FAIL. Far
# smaller than any real metric step, so it never masks a genuine miss.
_GATE_EPSILON = 1e-9

_GATED_MINIMUMS = {
    "fact_recall": thresholds.FACT_RECALL,
    "routing_recall": thresholds.ROUTING_RECALL,
    "routing_precision": thresholds.ROUTING_PRECISION,
    "abstention_precision": thresholds.ABSTENTION_PRECISION,
    "abstention_recall": thresholds.ABSTENTION_RECALL,
    "verifier_precision": thresholds.CITATION_ENTAILMENT,
    "verifier_recall": 0.95,
    "first_pass_json_validity": thresholds.FIRST_PASS_JSON_VALIDITY,
    "clean_published_support_rate": 1.0,
}
_FLOOR_KEYS = (
    "invalid_mutation_rejection_floor",
    "citation_validity_floor",
    "post_repair_json_validity_floor",
)


def aggregate(runs: list[dict]) -> dict:
    """Per metric across runs: {mean, stddev, runs:[...]}. stddev = sample stddev (0.0 for
    a single run or identical values)."""
    keys = set().union(*(r.keys() for r in runs)) if runs else set()
    out = {}
    for k in keys:
        vals = [r[k] for r in runs if k in r]
        stddev = statistics.stdev(vals) if len(vals) > 1 else 0.0
        out[k] = {"mean": sum(vals) / len(vals), "stddev": stddev, "runs": vals}
    return out


def gate(agg: dict) -> dict:
    """Pass iff every gated metric has mean >= minimum AND stddev <= MAX_METRIC_STDDEV, and
    every safety floor == 1.0 on every run. The mean comparison carries a tiny epsilon
    (_GATE_EPSILON) so a metric landing exactly on its bar across identical pinned runs is
    not failed by float rounding. `failures` is a list of bare metric/floor keys that failed
    (so membership tests work); `failure_details` carries the human-readable reasons."""
    failures = []
    details = []
    for key, minimum in _GATED_MINIMUMS.items():
        m = agg.get(key)
        if m is None:
            failures.append(key)
            details.append(f"{key}: missing")
            continue
        failed = False
        if m["mean"] < minimum - _GATE_EPSILON:
            details.append(f"{key}: mean {m['mean']:.4f} < {minimum}")
            failed = True
        if m["stddev"] > thresholds.MAX_METRIC_STDDEV:
            details.append(f"{key}: stddev {m['stddev']:.4f} > {thresholds.MAX_METRIC_STDDEV}")
            failed = True
        if failed:
            failures.append(key)
    for key in _FLOOR_KEYS:
        m = agg.get(key)
        if m is None:
            failures.append(key)
            details.append(f"{key}: missing")
        elif any(v < 1.0 for v in m["runs"]):
            failures.append(key)
            details.append(f"{key}: breached (a run < 1.0)")
    return {"passed": not failures, "failures": failures, "failure_details": details}


def render_report(agg: dict, verdict: dict, *, model: str, drift: dict | None = None,
                  pin: dict | None = None) -> str:
    """Markdown report: pinned config, per-metric table, safety floors, verdict, and the
    Ollama-default recommendation. `drift` is the optional Anthropic comparison."""
    failed = set(verdict["failures"])
    lines = [f"# kb-offline eval release report — {model}", ""]
    if pin:
        lines += [f"**Pinned config:** `{pin}`", ""]
    lines += ["| metric | min | mean | stddev | runs | pass |", "|---|---|---|---|---|---|"]
    for key, minimum in _GATED_MINIMUMS.items():
        m = agg.get(key, {"mean": float("nan"), "stddev": float("nan"), "runs": []})
        runs_s = ", ".join(f"{v:.3f}" for v in m["runs"])
        lines.append(f"| {key} | {minimum} | {m['mean']:.4f} | {m['stddev']:.4f} | {runs_s} | "
                     f"{'FAIL' if key in failed else 'PASS'} |")
    lines += ["", "**Safety floors (must = 1.0 every run):**"]
    for key in _FLOOR_KEYS:
        m = agg.get(key, {"runs": []})
        lines.append(f"- {key}: {m['runs']}")
    verdict_word = "PASS" if verdict["passed"] else "FAIL"
    lines += ["", f"## Verdict: {verdict_word}"]
    if verdict["failure_details"]:
        lines += ["", "**Failures:**"] + [f"- {d}" for d in verdict["failure_details"]]
    rec = (f"{model} clears both bars — recommend making Ollama the default backend."
           if verdict["passed"]
           else f"{model} does not clear the bars — keep Anthropic as the default backend; "
                "report the gap and/or pull a stronger local model.")
    lines += ["", f"**Ollama-default recommendation:** {rec}"]
    if drift is not None:
        lines += ["", "## Secondary: cloud-vs-local drift (advisory only)", f"`{drift}`"]
    return "\n".join(lines) + "\n"
