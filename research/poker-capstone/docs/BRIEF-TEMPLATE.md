# Task brief (template for full-autonomy-mode runs)

Build a client/server poker game.

- The server is the dealer and judge of the hands: it deals cards, judges
  who wins each hand, and handles the pot.
- The client is a web application where people can view the game and take
  their actions (e.g. betting).
- The server must correctly enforce turn order — a player can only act
  when it's their turn.

## Fixed technical constraints (not part of the design — a given interface
you must satisfy regardless of how you design everything else)

Your server must expose the exact REST API and be packaged exactly as
specified in `docs/HARNESS-CONTRACT.md` (read that file — it will be
provided at a path alongside this brief). This is analogous to a fixed
function signature in a coding exercise: everything *behind* this API —
your turn-enforcement mechanism, betting rounds, side-pot math, hand
evaluation, tech stack — is entirely your own design choice. Only the
external HTTP surface and container packaging are fixed, because an
external test harness needs a uniform way to drive and grade any
implementation.

If you are also submitting a client, it must expose the fixed
data-attribute mirror and URL deep-link contract specified in
`docs/CLIENT-TEST-CONTRACT.md` (also provided alongside this brief) —
same principle, applied to the DOM: framework, layout, styling, and
visible copy are entirely your own choice, only the `data-testid`/
`data-*` surface a driver reads is fixed.

---

**Provenance note:** added 2026-07-29 after the first Sonnet-only
verification run surfaced a real gap — a model's own (equally valid)
choice of wire protocol (WebSocket-message-based, not REST) left the
stage-4 harness with no way to drive it. See
`retrospectives/237-council-poker-capstone.md` and
`docs/HARNESS-CONTRACT.md` for the full story. The
`runs/sonnet-only-2026-07-29/brief.md` used for that run predates this
fix and did not include this section — worth knowing if comparing its
Stage 2 output against a later run's.

**Second provenance note:** the client contract paragraph above was
added later the same day, after P7/P8 cross-pairing found that same
run's client predated `CLIENT-TEST-CONTRACT.md` entirely (it didn't
exist yet when that run's Stage 3 happened) and so carried no
`data-testid` attributes at all — not a design defect, just a contract
that didn't exist yet when the brief was issued. See the "P7/P8 v2"
section of the retrospective.
