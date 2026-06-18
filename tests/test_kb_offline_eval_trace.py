"""Pure eval-trace derivation helpers (#211)."""
from __future__ import annotations

from sdlc_knowledge_base_scripts.eval.trace import derive_model_calls


def _rec(stage, first_pass, ok=True):
    return {"stage": stage, "first_pass": first_pass, "json_parse_ok": ok,
            "elapsed_ms": 1.0, "raw": "{}"}


def test_derive_select_repair_then_synth_then_two_judges_success():
    slice_ = [_rec("select", True, ok=False), _rec("select", False), _rec("synthesize", True),
              _rec("judge", True), _rec("judge", True)]
    calls = derive_model_calls(slice_, errored=False, error_msg="")
    assert (calls[0]["stage_invocation"], calls[0]["repair_attempt"]) == (1, 1)
    assert (calls[1]["stage_invocation"], calls[1]["repair_attempt"]) == (1, 2)
    assert (calls[2]["stage_invocation"], calls[2]["repair_attempt"]) == (1, 1)
    assert (calls[3]["stage_invocation"], calls[3]["repair_attempt"]) == (1, 1)
    assert (calls[4]["stage_invocation"], calls[4]["repair_attempt"]) == (2, 1)
    assert [c["accepted"] for c in calls] == [False, True, True, True, True]


def test_derive_accepted_on_select_repair_exhaustion_error():
    slice_ = [_rec("select", True, ok=False), _rec("select", False, ok=False)]
    calls = derive_model_calls(slice_, errored=True, error_msg="select failed after 1 repair(s): ...")
    assert [c["accepted"] for c in calls] == [False, False]


def test_derive_accepted_on_synth_exhaustion_keeps_select_accepted():
    slice_ = [_rec("select", True), _rec("synthesize", True, ok=False), _rec("synthesize", False, ok=False)]
    calls = derive_model_calls(slice_, errored=True, error_msg="synthesize failed after 1 repair(s): ...")
    assert calls[0]["accepted"] is True
    assert calls[1]["accepted"] is False and calls[2]["accepted"] is False


def test_derive_accepted_on_non_model_error_keeps_all_invocation_tails():
    slice_ = [_rec("select", True), _rec("synthesize", True)]
    calls = derive_model_calls(slice_, errored=True, error_msg="publish exploded")
    assert calls[0]["accepted"] is True and calls[1]["accepted"] is True
