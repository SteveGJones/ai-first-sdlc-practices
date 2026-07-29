# `leaky-hole-cards`

Deliberately-broken client (server unmodified) proving `client_verify`'s
Playwright driver catches a real client-side privacy bug, not just server
bugs. One injected change in `client/app.js`: the hole-card
`data-hidden` attribute is hardcoded to `"false"` regardless of whether
real card data was actually sent — falsely claiming every seat's hole
cards are visible to every viewer.

Verified 2026-07-29: `hole_card_privacy` fails with precise per-seat/slot
mismatch details; `turn_gated_controls` and `action_propagates` — both
unrelated to this bug — still pass. See
`retrospectives/237-council-poker-capstone.md`.
