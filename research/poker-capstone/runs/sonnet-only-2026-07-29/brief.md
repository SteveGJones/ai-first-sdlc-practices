# Task brief

**Historical note (added 2026-07-29, after this brief was already used
for stages 1-2):** this run predates the fixed-wire-API-contract
requirement now in `docs/BRIEF-TEMPLATE.md` /
`docs/HARNESS-CONTRACT.md` — Sonnet's Stage 2 chose its own
WebSocket-message protocol, which is a perfectly valid design choice this
brief didn't rule out, but left stage 4 unable to drive it without a
retrofit. See `retrospectives/237-council-poker-capstone.md` for the full
story. Kept as originally used, not edited, so the historical record
stays accurate.

---

Build a client/server poker game.

- The server is the dealer and judge of the hands: it deals cards, judges
  who wins each hand, and handles the pot.
- The client is a web application where people can view the game and take
  their actions (e.g. betting).
- The server must correctly enforce turn order — a player can only act
  when it's their turn.
