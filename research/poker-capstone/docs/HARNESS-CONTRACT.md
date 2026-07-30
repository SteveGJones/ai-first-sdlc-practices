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

## Cross-origin access (CORS)

The server must send permissive CORS headers (`Access-Control-Allow-
Origin: *` or equivalent — allow any origin, any method, any header) on
every REST response. The harness's browser-based client verification
(`harness/client_verify.py`) loads a client on one host-mapped port and
that client fetches the server on a different one; without CORS enabled,
every fetch is blocked by the browser before it reaches your handler at
all, regardless of how correct the REST logic itself is. The exemplar
server enables this via `CORSMiddleware(allow_origins=["*"], ...)`.

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
  visible once a hand reaches showdown). **`seat` is a required query
  parameter, not optional** — every caller, including the harness,
  must always supply it (see "Rollout note" below for why this is
  called out explicitly).

## Response shape (every endpoint above that returns state)

The harness's cross-validation (`harness/oracle.py` +
`harness/scenarios.py`) reads these exact fields — omitting any of them
makes a hand un-scoreable, which is scored as a stage-4 failure, not
skipped:

This is the COMPLETE field list — every field a compliant server's state
response must include, audited field-by-field against the exemplar's own
`Table.to_dict()` on 2026-07-29 after two rounds of finding fields missing
here that a real client actually needed (see "Rollout note" below).

```
{
  "table_id": str,
  "small_blind": int,
  "big_blind": int,
  "button_seat": int | null,       // null only before the first hand has ever started
  "betting_round": "preflop"|"flop"|"turn"|"river"|"showdown"|null,
  "community_cards": [{"rank": int (2-14, 14=Ace), "suit": str}, ...],
  "pots": [{"amount": int, "eligible_seats": [int, ...]}, ...],
  "current_bet": int,
  "min_raise": int,                // smallest legal raise INCREMENT this round — needed for client-side bet-sizing UI, not just server-side validation
  "current_actor": int | null,
  "hand_in_progress": bool,
  "last_action_log": [str, ...],   // most recent entries, newest last; a compliant server may cap this list's length (the exemplar keeps the last 20) but must include at least the single most recent entry
  "last_showdown": [
    {"seat": int, "hole_cards": [{"rank": int, "suit": str}, {"rank": int, "suit": str}],
     "hand_category": str}   // present only for seats that reached showdown; empty list on a fold-out hand
  ],
  "players": [
    {"seat": int, "stack": int, "status": "active"|"folded"|"all_in"|"sitting_out",
     "current_bet": int,      // chips this seat has put in THIS betting round only, reset to 0 when the round advances (preflop -> flop -> ...)
     "total_committed": int,  // chips this seat has put in THIS hand, across all betting rounds, reset to 0 at the start of each new hand
     "hole_cards": [{"rank": int, "suit": str}, {"rank": int, "suit": str}] | null
       // this is THE hole-card-privacy mechanism: null unless this seat's
       // hole cards are visible to the requesting viewer (their own seat,
       // or any seat once the hand reaches showdown) — see "What the
       // stage-4 harness will check" for how this gets exercised
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

## Rollout note — this document has had real gaps, found the hard way

Each found by a model actually trying to implement or consume this
contract, not by us re-reading it more carefully:

- 2026-07-29: `players[].current_bet` was missing entirely — the
  Sonnet-only Phase 3 verification's server, built exactly to the
  then-current spec, crashed the harness with a `KeyError` the harness
  itself never anticipated either.
- 2026-07-29: `players[].hole_cards` was missing — the P6 spec-fidelity
  client build correctly noticed the hole-card-privacy mechanism itself
  had no documented field to carry it, and made a reasonable assumption
  rather than guessing wrong silently.
- 2026-07-29, same pass: a full field-by-field audit against the
  exemplar's actual `Table.to_dict()` found `table_id`, `small_blind`,
  `big_blind`, `betting_round`, `min_raise`, and `last_action_log` were
  all real response fields never listed here — `min_raise` specifically
  flagged by the same P6 client build as needed for bet-sizing UI it
  otherwise had to guess at.
- 2026-07-29, P5 verification: the harness itself called
  `GET /tables/{id}/state` without a `seat` query param in four
  scenarios (relying on the exemplar's own, undocumented choice to
  treat a missing `seat` as "spectator view, no hole cards revealed").
  The P5 spec-fidelity server, built only from this contract, made
  `seat` a required parameter and correctly rejected the un-parameterized
  call with `422` — a reasonable reading the contract didn't rule out.
  Fixed by making the harness always pass `seat` explicitly and by
  stating the requirement here, rather than by changing P5's server:
  the harness's assumption was the bug, not the candidate's.

- 2026-07-29, P9-v2 self-pairing verification: a from-scratch server
  implementation (built correctly to every field/behavior this document
  specified at the time) still couldn't serve its own paired client —
  the browser blocked every fetch with a CORS error, because nothing
  here ever said CORS was required. The exemplar has always silently
  depended on it. Fixed by adding the "Cross-origin access" section
  above; the implementation was then asked to add the now-documented
  requirement, the same way the original P9 run's server added the
  `current_bet` field once that gap was found — a contract-clarity fix,
  not a backfill of the model's own logic.

Treat this document as version-controlled and fallible, not as a fixed
oracle — if a future implementation surfaces another gap, fix it here
the same way, with the finding recorded rather than silently patched.
