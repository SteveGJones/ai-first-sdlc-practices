"""Pure eval-trace helpers (#211): derive per-stage invocation/attempt/accepted from a
per-question (or per-label) RecordingBackend record slice, and classify select drops.
No model calls, no I/O — testable in isolation."""
from __future__ import annotations

_MODEL_FAIL_PREFIXES = ("select failed after", "synthesize failed after")


def derive_model_calls(records: list[dict], *, errored: bool, error_msg: str) -> list[dict]:
    """Annotate a record slice (stateless {stage, first_pass, json_parse_ok, elapsed_ms, raw})
    with stage_invocation, repair_attempt, accepted. A first_pass call opens a new invocation
    of its stage; a non-first_pass call continues it. accepted = the last call of each
    invocation that the pipeline used (positional):
      - success: every invocation's last call;
      - select/synthesize repair-exhaustion error: every invocation's last call EXCEPT the
        terminal invocation (the failed stage);
      - any other (non-model) error: every invocation's last call (model stages completed)."""
    out = []
    inv_counter: dict[str, int] = {}
    cur_attempt: dict[tuple, int] = {}
    for rec in records:
        stage = rec["stage"]
        if rec["first_pass"]:
            inv_counter[stage] = inv_counter.get(stage, 0) + 1
            cur_attempt[(stage, inv_counter[stage])] = 1
        else:
            inv = inv_counter.get(stage, 1)
            inv_counter.setdefault(stage, inv)
            cur_attempt[(stage, inv)] = cur_attempt.get((stage, inv), 1) + 1
        inv = inv_counter.get(stage, 1)
        out.append({**rec, "stage_invocation": inv,
                    "repair_attempt": cur_attempt[(stage, inv)], "accepted": False})

    last_idx: dict[tuple, int] = {}
    for i, c in enumerate(out):
        last_idx[(c["stage"], c["stage_invocation"])] = i

    model_fail = errored and error_msg.startswith(_MODEL_FAIL_PREFIXES)
    terminal_key = (out[-1]["stage"], out[-1]["stage_invocation"]) if out else None
    for key, idx in last_idx.items():
        if model_fail and key == terminal_key:
            continue
        out[idx]["accepted"] = True
    return out
