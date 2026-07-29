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
