# Detailed design: client (exemplar)

**Stage:** 2 (Detailed design) — poker capstone exemplar
**Depends on:** `architecture.md`, `design-server.md` (API contract)

The client holds **no game logic**. Every rule (whose turn it is, what
actions are legal, who won) is decided by the server; the client's job is
to render whatever the server last pushed and to submit action requests,
handling rejection gracefully (the server is the source of truth, so a
`409` from an action just means: re-render from the last known-good state,
show the error, don't guess).

## Views

1. **Lobby** — create a table (small/big blind) or join an existing one by
   `table_id` + seat with a name and buy-in. Minimal — this exists so the
   app is usable end-to-end, not a polished product.
2. **Table view** — the whole game:
   - Community cards (0–5, revealed progressively as `betting_round`
     advances).
   - Each seated player: name, stack, current bet this round, status
     (folded/all-in shown visually), dealer button marker.
   - This client's own hole cards (only ever the ones the server sent for
     `seat` — the server never sends another seat's hole cards to a
     non-showdown request, so the client cannot leak what it was never
     given).
   - Pot total(s) — if there are side pots, show each with its amount (the
     eligible-seats detail is available from state but not essential UI;
     showing the amounts is enough for a human to follow along).
   - Action bar, enabled **only** when `current_actor == this client's
     seat` per the last-received state: Fold / Check-or-Call (label
     depends on whether a call is owed) / Bet-or-Raise (amount input,
     min/max derived from state: min = `current_bet + min_raise` or
     `big_blind` if `current_bet == 0`, max = player's stack).
   - A simple log/toast for the last action taken by any player (from
     the WebSocket stream), so a human watching can follow the hand.

## State sync

- On loading the table view, `GET /tables/{id}/state?seat={seat}` for the
  initial render, then open `WS /tables/{id}/ws?seat={seat}` for all
  subsequent updates — every message on the socket **replaces** the
  client's local state wholesale (the client never diffs or merges; the
  server's push is always the full current state, which sidesteps any
  possible client-side state-drift bugs).
- If the socket disconnects, show a reconnecting indicator and retry with
  backoff; on reconnect, re-fetch via `GET .../state` before resubscribing
  (covers whatever happened while disconnected).

## Action submission

- Clicking an action button never mutates local state directly — it fires
  `POST /tables/{id}/actions` and waits. On success, the response body
  *is* the new state (apply it immediately, don't wait for the WS push —
  the WS message will arrive too and is idempotent to apply again). On
  `409`, show the server's `error` message and leave the UI as it was
  before the click (don't optimistically disable/grey anything that
  turned out to be illegal).
- The action bar is disabled the instant a request is in flight, to
  prevent a double-submit racing two actions for the same turn.

## Implementation notes

- No framework, no build step: `index.html` + `app.js` + `style.css`,
  served as static files. `app.js` uses `fetch` for REST and the native
  `WebSocket` API — no dependency beyond the browser itself.
- Layout: an oval/circle of seats around a center area showing community
  cards + pot(s), a standard poker-table visual convention that makes
  "whose turn is it" and "who's the button" legible at a glance (button
  marker + a highlighted border on the current actor's seat).
