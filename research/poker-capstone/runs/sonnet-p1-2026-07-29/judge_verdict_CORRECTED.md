# P1 judge verdict — corrected

The raw judge output (`judge_verdict.json`) scored F1 as **INCORRECT**.
Verification against the actual source (`game_engine.py::submit_action`)
found the ground-truth fact F1 itself was wrong — it claimed the turn
check happens "before any other validation," but the real code checks
`hand_in_progress` first, then the turn. The candidate's documentation
correctly reported the real order; the fact list was miscalibrated.
`docs/P1-GROUND-TRUTH-FACTS.md` F1 corrected in place, dated and
cross-referenced back here — see this repo's convention of recording
corrections rather than silently editing history.

## Corrected tally

**14 CORRECT, 0 INCORRECT, 1 OMITTED** (of 15 facts) — F1 reclassified
CORRECT, everything else unchanged from the raw verdict.

The one remaining gap (F6, OMITTED) is real and stands: the
documentation correctly states that a short all-in raise doesn't reopen
action for players who already matched the previous bet, but never
states the other two required parts of that rule (min_raise is not
increased; current_bet still rises to the new target). Partial credit
for the hardest rule in the spec, not a wrong claim — an omission, not
an error.

## Why this matters for the P1 mechanism itself

This is the same class of finding as the REST harness and client
contract bugs found earlier this session: **every new grading mechanism
built this session had a real bug in the grading infrastructure itself**,
caught only by actually running it against real output, not by writing
it carefully and trusting it. A ground-truth fact list is not
self-evidently correct just because the person writing it also wrote the
code — it needs the same "run it, don't just read it" discipline as
everything else in this project.
