# Broken variants

Deliberately-broken copies of the exemplar, used to prove the stage-4
harness (`harness/`) actually catches real bugs rather than always
passing. Each variant introduces exactly one targeted bug, documented
inline at the change site with an `INJECTED BUG` comment, so the harness
run against it can be checked for the *specific* failure the bug should
cause, not just "did it fail."

## `wrong-pot-split`

`server/app/game_engine.py::_finish_hand` — `best_score = min(...)`
instead of `max(...)`, so every showdown pot is awarded to the *worst*
eligible hand instead of the best. Verified 2026-07-29: the harness
correctly fails `basic_multihand` and `short_all_in_side_pot` (the
payout-cross-validation scenarios) with mismatch details naming the
exact seats/amounts, while `turn_enforcement` — unrelated to this bug —
still passes. That's the harness working correctly: failing on the
assertion the bug actually violates, not silently or on the wrong one.

## `leaky-hole-cards`

`client/app.js` — the hole-card `data-hidden` attribute is hardcoded to
`"false"` regardless of whether real card data was sent, falsely
claiming every seat's hole cards are visible to every viewer. Proves
`client_verify`'s Playwright driver (`harness/browser_scenarios.py`)
catches a client-side privacy bug specifically — `hole_card_privacy`
fails with per-seat/slot mismatch details, `turn_gated_controls` and
`action_propagates` (unrelated) still pass. See its own `README.md` for
detail.
