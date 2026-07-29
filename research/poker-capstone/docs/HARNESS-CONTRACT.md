# Harness contract (normative, applies to EVERY submission)

Found necessary after a real gap surfaced during the 2026-07-29 Sonnet
first-verification run: the stage-4 harness (`harness/scenarios.py`) drives
any implementation entirely over REST, but the fairness-preserving design
for full-autonomy mode originally left the wire protocol as the model's own
choice — which is genuinely a fine, valid design decision for a model to
make (Sonnet's own run chose a WebSocket-message protocol instead), but
left the harness with no uniform way to drive an arbitrary implementation.

**The fix: the wire API is a fixed constraint, same status as the
packaging contract, in every mode (full-autonomy and spec-fidelity
alike).** A model designing this system still owns every genuinely
interesting design decision — the turn-enforcement state machine, betting
round structure, side-pot math, hand evaluation approach, tech stack — but
the HTTP surface below is given, not designed, exactly the way "must run
in a Docker container named `server` on port 8000" is given rather than
designed. This is analogous to a real engineering constraint: an
internal service can be built any way its owner likes, but a fixed
external API it must expose for other systems (here: the grading harness)
to integrate with isn't optional.

## Packaging

- `docker-compose.yml` at the implementation root.
- A service literally named `server`, container port `8000`, serving
  `GET /healthz` → `200` once ready (any body).
- If a client is submitted, its service must be named `client`. Not
  required — stage 4 tests the server's API surface directly.

## REST API (must be implemented exactly, in addition to whatever
internal protocol the design otherwise uses)

- `POST /tables` — body `{small_blind, big_blind}` → `{table_id}`.
- `POST /tables/{id}/players` — body `{name, buy_in}` → `{seat}`.
- `POST /tables/{id}/start` — no body. Deals a new hand (requires ≥2
  seated players). Returns the new state (see "Response shape" below).
- `POST /tables/{id}/actions` — body
  `{seat, action: "fold"|"check"|"call"|"bet"|"raise", amount?: int}`
  (`amount` is the **total** the bet reaches this round, not the
  increment). `200` + new state on success; `4xx` + `{"detail"|"error":
  reason}` if illegal (wrong turn, illegal action for current betting
  state, amount below minimum) — **and the state must be left
  unchanged** on rejection.
- `GET /tables/{id}/state?seat={seat}` — current state, hole cards
  redacted for every seat except `seat` (all seats' hole cards are
  visible once a hand reaches showdown).

## Response shape (every endpoint above that returns state)

The harness's cross-validation (`harness/oracle.py` +
`harness/scenarios.py`) reads these exact fields — omitting any of them
makes a hand un-scoreable, which is scored as a stage-4 failure, not
skipped:

```
{
  "hand_in_progress": bool,
  "current_actor": int | null,
  "current_bet": int,
  "button_seat": int,
  "community_cards": [{"rank": int (2-14, 14=Ace), "suit": str}, ...],
  "pots": [{"amount": int, "eligible_seats": [int, ...]}, ...],
  "last_showdown": [
    {"seat": int, "hole_cards": [{"rank": int, "suit": str}, {"rank": int, "suit": str}],
     "hand_category": str}   // present only for seats that reached showdown; empty list on a fold-out hand
  ],
  "players": [
    {"seat": int, "stack": int, "status": "active"|"folded"|"all_in"|"sitting_out",
     "current_bet": int,      // chips this seat has put in THIS betting round only, reset to 0 when the round advances (preflop -> flop -> ...)
     "total_committed": int   // chips this seat has put in THIS hand, across all betting rounds, reset to 0 at the start of each new hand
    }, ...
  ]
}
```

`suit` may be any consistent string values (the oracle only compares them
for equality within a hand, e.g. for flush detection — it does not care
whether you use `"s"` or `"SPADES"`).

## Why this is fixed and not left to Stage 2's design

Every genuinely graded design decision — the algorithms in
`docs/design-server.md`'s "Turn state machine", "Side-pot allocation
algorithm", and "Hand evaluation" sections — lives entirely behind this
API, invisible to it. Fixing the wire shape doesn't remove any of the
hard design/implementation work; it only removes the (real, but
uninteresting for grading purposes) design freedom of choosing *how
results get reported to an external test harness*, the same way a coding
interview fixes a function signature without dictating the algorithm
inside it.
