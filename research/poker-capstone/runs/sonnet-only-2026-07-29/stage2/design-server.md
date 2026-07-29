# Poker Capstone — Server Detailed Design (Stage 2)

## 0. Scope and inputs

This document details the **Game Engine** and **Table Manager** components
from Stage 1 (`stage1/architecture.md`) to a level precise enough to
implement without further clarification. It assumes the Stage 1 decisions
as locked: server-authoritative, WebSocket-based, one serially-processed
Game Engine instance per table, Node.js/TypeScript. No code is included —
this is behavior, data shape, and algorithm specification.

**Variant chosen:** No-Limit Texas Hold'em, 2–9 seats per table. This is
the variant that best exercises every requirement in the brief (turn
enforcement, all-in/side-pot handling, hand judging) and is what Stage 1's
message examples (`RAISE`/`minRaise`) already assume.

Table configuration, fixed at table creation and out of scope for
per-hand logic: `smallBlind`, `bigBlind` (`bigBlind = 2 × smallBlind`),
`maxSeats` (2–9), `minBuyIn`/`maxBuyIn` (in chips), `actionTimeoutMs`.

## 1. Hand lifecycle (top-level state machine)

Each table's Game Engine is, at the top level, a state machine over one
hand at a time:

```
WAITING_FOR_PLAYERS
      │  (≥2 seated, not sitting-out, stack > 0)
      ▼
HAND_STARTING          (rotate button, post blinds, shuffle, deal hole cards)
      ▼
BETTING_ROUND(PREFLOP)  ──┐
      ▼                   │ if ≤1 non-folded player remains at any point,
DEAL_FLOP                 │ jump straight to SETTLE (skip remaining streets,
      ▼                   │ no further betting or card dealing needed since
BETTING_ROUND(FLOP)  ─────┤ there is nothing to contest)
      ▼                   │
DEAL_TURN                 │
      ▼                   │
BETTING_ROUND(TURN)  ─────┤
      ▼                   │
DEAL_RIVER                │
      ▼                   │
BETTING_ROUND(RIVER) ─────┤
      ▼                   │
SHOWDOWN  ◄────────────────┘   (only reached if ≥2 players remain after RIVER)
      ▼
SETTLE                  (build pots, judge, pay out — §4/§5)
      ▼
HAND_COMPLETE            (broadcast results, update stacks/ledger)
      ▼
WAITING_FOR_PLAYERS  (or straight into next HAND_STARTING if ≥2 players
                       remain with chips)
```

If all but one player fold at any point in any betting round, the engine
transitions directly to `SETTLE` (no showdown reveal is required — the
sole remaining player wins every pot uncontested; other players' hole
cards are never revealed or transmitted).

The engine also allows exactly one asynchronous transition out of
`WAITING_FOR_PLAYERS`, `HAND_COMPLETE`, or between hands: players may
`SIT`/`SIT_OUT`/leave. These never interrupt a hand in progress — seat
changes requested mid-hand are queued and applied only once the engine
returns to `WAITING_FOR_PLAYERS`/`HAND_STARTING`.

## 2. Turn enforcement — the state machine in detail

This is the mechanism the brief calls out explicitly, so it is specified
precisely.

### 2.1 Per-table authoritative state relevant to turn order

```
TableState {
  handSeq: int                     // increments once per hand
  street: PREFLOP | FLOP | TURN | RIVER | SHOWDOWN | null
  buttonSeat: int
  seats: Seat[]                    // fixed array indexed by seat number
  actingSeat: int | null           // null when no betting round is open
  currentBet: int                  // highest total bet-this-street across all seats
  minRaiseSize: int                // smallest legal raise increment right now
  lastFullRaiseSeat: int | null    // seat that made the last FULL raise (see §2.5)
  actedThisStreet: Set<int>        // seats that have acted since street/last full raise opened
  actionSeq: int                   // increments on every accepted action, table-wide
  actByMs: int | null              // deadline for actingSeat's current turn
}

Seat {
  seatNo: int
  playerId: string | null
  stack: int
  betThisStreet: int
  totalCommittedThisHand: int      // across all streets, reset each hand
  status: EMPTY | SITTING_OUT | ACTIVE | FOLDED | ALL_IN
}
```

`actingSeat` is the single field that answers "whose turn is it." It is
never inferred from message order or client claims — it is server state,
mutated only by the engine itself.

### 2.2 Identity binding (precondition for every message)

At connect time the Connection Layer performs auth and records
`connectionId ⇄ playerId`. When a player sits at a table, the Table
Manager records `playerId ⇄ (tableId, seatNo)`. Every inbound `ACTION`
message is attributed to a seat by looking up
`connectionId → playerId → seatNo` on the server side — the message body
never carries a seat number the server trusts. If a connection has no
seat mapping at the target table, the message is rejected
(`NOT_SEATED`) before it reaches the engine at all.

### 2.3 Action validation pipeline (runs for every inbound `ACTION`)

Applied **in this order**, as preconditions; the first failing check
rejects the message with **zero effect** on state (no partial mutation,
nothing to roll back):

1. **Table/engine reachable and processing serially** — the Table Manager
   routes the message to the one Game Engine instance for this table,
   which processes its inbound queue strictly one message at a time. This
   is what makes every check below race-free: there is no way for two
   `ACTION`s to be "in flight" against the same `actingSeat` value.
2. **Resolve seat from connection** (§2.2). Fail → `NOT_SEATED`.
3. **`street` is a betting street** (not `null`, not `SHOWDOWN`/`SETTLE`).
   Fail → `NOT_ACCEPTING_ACTIONS`.
4. **`resolvedSeat == actingSeat`.** Fail → `NOT_YOUR_TURN`. This is the
   core turn-enforcement check.
5. **`actionId` not already applied for this seat this hand** (idempotency
   — see §2.6). Duplicate → re-send the original `ACTION_APPLIED`/
   `ACTION_REJECTED` outcome without reapplying.
6. **`action` is a member of `legalActions(actingSeat)`** as computed by
   §2.4. Fail → `ILLEGAL_ACTION`.
7. **For `BET`/`RAISE`: `amount` is within the legal range** computed by
   §2.5. Fail → `INVALID_AMOUNT`.

Only after all seven checks pass does the engine mutate `TableState`,
increment `actionSeq`, and broadcast `ACTION_APPLIED`.

### 2.4 Computing `legalActions(seat)`

Let `toCall = currentBet - seat.betThisStreet`.

- `FOLD` — always legal for the acting seat (a player may always fold,
  even when checking is free).
- `CHECK` — legal iff `toCall == 0`.
- `CALL` — legal iff `toCall > 0`. If `seat.stack <= toCall`, a `CALL`
  commits the player's entire remaining stack and immediately sets
  `status = ALL_IN` (a short all-in call, not a full call — this is
  legal and distinct from a raise).
- `BET` — legal iff `currentBet == 0` (no one has bet yet this street)
  and `seat.stack > 0`.
- `RAISE` — legal iff `currentBet > 0`, `toCall < seat.stack` (i.e. the
  player has more chips than a call would cost, otherwise it can only be
  a `CALL`, not a `RAISE`), and `seat.stack > toCall` obviously implies
  chips remain to raise with.

`BET` and `RAISE` are modeled as one wire action (`RAISE` with an
`amount` = the seat's new total `betThisStreet`, matching Stage 1's
message shape) whose legality/range differs only in whether `currentBet`
is currently zero. The server, not the client, decides which of `BET`/
`RAISE` semantics apply based on `currentBet`.

### 2.5 Legal raise amount, minimum-raise rule, and the incomplete-raise exception

- `minRaiseSize` starts each street at `bigBlind` and is updated to the
  size of the last **full** raise (see below) each time one occurs.
- A legal `RAISE` amount (new total `betThisStreet`) must satisfy
  `amount >= currentBet + minRaiseSize`, **unless** the player is going
  all-in for less (`amount == seat.stack + seat.betThisStreet <
  currentBet + minRaiseSize`), which is always allowed as a special case
  (a player can never be prevented from moving all-in).
- **Full raise vs. incomplete (short) all-in raise:** a raise is *full*
  if its increment over `currentBet` is `>= minRaiseSize`; it is
  *incomplete* if it is an all-in for less than that. A full raise:
  - updates `currentBet` to the new amount,
  - sets `minRaiseSize` to the size of the raise increment
    (`newAmount - previousCurrentBet`),
  - sets `lastFullRaiseSeat = actingSeat`,
  - **reopens the action**: clears `actedThisStreet` back to just
    `{actingSeat}`, so every other non-folded, non-all-in player must act
    again.

  An *incomplete* all-in raise:
  - updates `currentBet` to the new (higher) amount so subsequent players
    owe the new `toCall`,
  - does **not** change `minRaiseSize`,
  - does **not** reopen action for players who already acted at the
    previous `currentBet` level and are only facing the extra partial
    increment — standard cardroom rule: a player cannot be forced to
    fold/reraise for a raise smaller than the legal minimum. Concretely:
    those already-acted players still owe the new `toCall` to continue
    (call the higher amount or fold) but are **not** required to have the
    option to re-raise off that short all-in; the engine still asks them
    to act (they must call the new amount or fold), it simply does not
    re-treat this as a fresh full raise for the purpose of who gets
    another *raising* opportunity beyond call/fold. In practice this only
    matters for a corner case (a second short all-in over the first) and
    is handled by the same `minRaiseSize` bookkeeping — implementers may
    simplify by tracking it exactly as described without needing a
    separate flag, since `actedThisStreet` clearing is driven solely by
    whether the raise was full.
- `RAISE`/`BET` amount must always be `<= seat.stack + seat.betThisStreet`
  (cannot bet more than the stack); the maximum is effectively "all-in."

### 2.6 Turn advancement and betting-round closure

After a valid action is applied:

1. Add `actingSeat` to `actedThisStreet` (or reset it to `{actingSeat}`
   if this action was a full raise, per §2.5).
2. If the action was `FOLD` and only one non-folded seat remains
   table-wide → transition immediately to `SETTLE` (§1); `actingSeat`
   becomes `null`.
3. Otherwise compute the next candidate seat by walking seats clockwise
   from `actingSeat + 1` (wrapping), **skipping** any seat whose status is
   `FOLDED`, `ALL_IN`, `EMPTY`, or `SITTING_OUT`.
4. **Round-closure check** — the betting round ends (no next seat needs
   to act) when, for every seat with status `ACTIVE`:
   `seat.betThisStreet == currentBet` **and** `seat ∈ actedThisStreet`.
   (A round with zero `ACTIVE` seats left, i.e. everyone remaining is
   `ALL_IN` or folded, also closes immediately — no further betting is
   possible; the engine deals all remaining streets face-up back-to-back
   with no betting, then goes to `SHOWDOWN`.)
5. If the round is closed: set `actingSeat = null`, `actByMs = null`,
   transition to `DEAL_<next street>` or `SHOWDOWN`/`SETTLE` per §1, reset
   `currentBet = 0`, `minRaiseSize = bigBlind`, `betThisStreet = 0` for
   all seats, and clear `actedThisStreet` for the new street.
6. Otherwise: set `actingSeat` to the seat found in step 3, set
   `actByMs = now + actionTimeoutMs`, and broadcast `TURN_STARTED`.

This is a pure function of current `TableState` — there is no separate
"who's next" table or lookup that could drift from the seat array.

### 2.7 Action idempotency

Each `ACTION` message carries a client-generated `actionId` (UUID). The
engine keeps a small per-seat, per-hand set of `actionId`s it has already
applied (cleared at `HAND_STARTING`). A duplicate `actionId` from the
same seat is **not reapplied**; the engine replays the original result
message. This makes retried submits (flaky connection, client resending
after a timeout with no visible ack) safe.

### 2.8 Turn timeout — server-driven, not client-trusted

If no valid `ACTION` arrives from `actingSeat` by `actByMs`, the engine
itself (on its own timer, not waiting for any client) applies a default
action as if that seat had submitted it: `CHECK` if legal (`toCall==0`),
else `FOLD`. This goes through the same turn-advancement logic in §2.6
(it is simply an internally-sourced action that trivially passes the
turn/legality checks because the engine is applying it as the current
`actingSeat`). After **3 consecutive timeouts** for the same player
across hands, the engine marks that seat `SITTING_OUT` and excludes it
from future `HAND_STARTING` deals until the player explicitly sends
`SIT_IN`.

### 2.9 Reconnection

On reconnect, the client sends `REQUEST_SYNC`; the server responds with a
fresh, per-recipient `STATE_SYNC` computed from current `TableState` —
never from anything cached about a previous session. `actingSeat`,
`actByMs`, and `legalActions` for the reconnecting player (if it's their
turn) are included so the UI can immediately re-enable the action panel
correctly. Turn state is never "resumed" client-side.

## 3. Blinds and dealer button rotation

- `buttonSeat` starts at a random occupied seat when the table's first
  hand begins.
- At each `HAND_STARTING`: `buttonSeat` advances to the next occupied
  seat (status `ACTIVE`, `stack > 0`) clockwise from the previous
  `buttonSeat`, wrapping around the seat array. A seat that busted
  (`stack == 0`) or is `SITTING_OUT` is skipped for button purposes.
- **3+ players:** small blind = next occupied seat clockwise from
  `buttonSeat`; big blind = next occupied seat clockwise from the small
  blind. Both post automatically (forced, not a player-submitted
  `ACTION`) as part of `HAND_STARTING`, before any hole cards are dealt.
  A blind less than the full amount is posted (and the seat goes
  `ALL_IN`) if the seat's stack is smaller than the blind.
- **Heads-up (exactly 2 active seats):** the button **is** the small
  blind (posts SB and acts first preflop, last on every subsequent
  street); the other seat is the big blind. This is the standard
  heads-up exception and must be special-cased explicitly rather than
  falling out of the general "next seat" rule.
- After blinds are posted, `currentBet = bigBlind`, `minRaiseSize =
  bigBlind`, and the first `actingSeat` preflop is the next occupied seat
  clockwise from the big blind (i.e., "under the gun"); heads-up, it is
  the button/SB (acting first preflop, per the exception above).
  Postflop streets, the first `actingSeat` is always the first occupied,
  non-folded, non-all-in seat clockwise from `buttonSeat`.

## 4. Dealing and hand evaluation

### 4.1 Deck and dealing

- A standard 52-card deck is shuffled server-side per hand using a
  cryptographically-suitable RNG (never seeded from anything
  client-observable). The deck is entirely server-internal state; it is
  never serialized to any client message except as individual revealed
  cards.
- Hole cards: two cards dealt to each `ACTIVE` seat, one at a time in two
  passes starting from the seat immediately clockwise of `buttonSeat`
  (SB in a 3+-handed game), matching standard cardroom dealing order.
  Each seat's hole cards are sent **only** to that seat's connection (see
  §6 of the message contract) — this is a per-recipient projection
  computed at send time, not a broadcast with client-side filtering.
- Community cards: 3 (flop), then 1 (turn), then 1 (river), burn-and-deal
  is not modeled as a separate mechanic (no observable difference to
  correctness at this scope); cards are simply drawn from the
  already-shuffled deck in order and are public — broadcast to all
  seats identically.

### 4.2 Hand evaluation ("the judge")

At `SETTLE`, for every seat still eligible for at least one pot (see §5),
the engine evaluates the best 5-card hand from that seat's 2 hole cards +
the 5 community cards:

1. Enumerate all `C(7,5) = 21` five-card combinations of the seat's 7
   available cards.
2. Score each 5-card combination as a comparable tuple:
   `(category, tiebreak₁, tiebreak₂, ...)` where `category` is one of the
   9 standard categories ranked `STRAIGHT_FLUSH(8) > FOUR_OF_A_KIND(7) >
   FULL_HOUSE(6) > FLUSH(5) > STRAIGHT(4) > THREE_OF_A_KIND(3) >
   TWO_PAIR(2) > ONE_PAIR(1) > HIGH_CARD(0)`, and the tiebreak values are
   the relevant card ranks in descending significance (e.g. for
   `TWO_PAIR`: higher pair rank, lower pair rank, kicker rank).
   `A-2-3-4-5` ("the wheel") is recognized as a `STRAIGHT`/
   `STRAIGHT_FLUSH` with the ace counted **low** (straight value 5-high),
   in addition to ace normally counting high for `A-K-Q-J-T`.
3. Take the maximum-scoring combination (lexicographic tuple comparison)
   as that seat's best hand for the whole 7-card set.
4. The seat's final comparable value is this tuple; two seats' hands
   compare equal (a tie/chop) iff their tuples are equal element-for-
   element, not merely same category.

This tuple-comparison approach is chosen over a precomputed lookup table
(e.g. Cactus Kev) for design-doc clarity and because raw performance is
not a constraint at this scale (evaluating 21 combinations per
contesting player, at most 9 players, once per hand, is trivial cost).
An implementer may swap in a lookup-table evaluator later behind the same
`evaluateBestHand(sevenCards) -> ComparableHandValue` interface without
changing anything else in this design.

## 5. All-in and side pots — exact pot-building and payout algorithm

This is the other mechanism the brief calls out explicitly (via
handling players who commit different amounts), so it is fully specified.

### 5.1 Inputs at `SETTLE`

- `totalCommittedThisHand[seat]` for every seat that put **any** chips
  into the pot this hand — this includes folded players (their chips
  stay in the pot; they just aren't eligible to win any of it) and
  excludes seats that never entered the hand.
- `foldedSeats` — set of seats with status `FOLDED`.
- (Seats with `totalCommittedThisHand == 0`, i.e. never dealt in / sat
  out the hand, are excluded entirely from pot construction.)

### 5.2 Pot construction algorithm

```
function buildPots(committed: Map<seat, int>, folded: Set<seat>) -> Pot[]:
    remaining = copy(committed)          // mutable working copy
    pots = []
    while any(amount > 0 for amount in remaining.values()):
        layerSeats = [s for s, amt in remaining.items() if amt > 0]
        capAmount   = min(remaining[s] for s in layerSeats)
        potSize     = capAmount * len(layerSeats)
        eligible    = [s for s in layerSeats if s not in folded]
        pots.append(Pot(amount: potSize, eligibleSeats: eligible))
        for s in layerSeats:
            remaining[s] -= capAmount
    // Adjacent pots with identical eligibleSeats sets may be merged
    // for display purposes only; payout logic treats each layer
    // independently regardless of merging.
    return pots
```

This is the standard "layer by shortest stack" construction: each
iteration peels off the smallest remaining contribution as one pot layer
shared by everyone who put in at least that much, and the win-eligibility
of each layer is exactly the set of contributors to that layer who did
not fold. A player who folds is still charged into every layer their
chips reached, but is never in `eligibleSeats` for any layer, which is
what "forfeits any claim on the pot" means mechanically.

**Worked example** — 4 players, all in this hand:
- A contributes 100 total, then folds after (still committed 100).
- B goes all-in for 60.
- C contributes 200 total.
- D contributes 200 total.

`committed = {A:100, B:60, C:200, D:200}`, `folded = {A}`.

Iteration 1: `layerSeats = [A,B,C,D]`, `capAmount = 60` → pot of `240`
(`60×4`), `eligible = [B,C,D]` (A folded). Remaining: `{A:40, B:0,
C:140, D:140}`.

Iteration 2: `layerSeats = [A,C,D]`, `capAmount = 40` → pot of `120`
(`40×3`), `eligible = [C,D]` (A folded, B already fully accounted for in
layer 1 and has `0` left so is excluded from this layer). Remaining:
`{A:0, C:100, D:100}`.

Iteration 3: `layerSeats = [C,D]`, `capAmount = 100` → pot of `200`,
`eligible = [C,D]`. Remaining: `{C:0, D:0}` → loop ends.

Result: **Pot 1 = 240** eligible `[B,C,D]`; **Pot 2 = 120** eligible
`[C,D]`; **Pot 3 = 200** eligible `[C,D]` (mergeable for display with Pot
2 into one 320 side pot since eligibility sets match, but kept separate
here to show the algorithm's raw output). Total across pots = 560 =
100+60+200+200, confirming no chips are lost or duplicated.

### 5.3 Awarding each pot

For each pot (order does not affect the outcome, since pots don't
interact):

1. If `eligibleSeats.length == 1`, that seat wins the entire pot amount
   — no evaluation needed (this is the common "everyone else folded"
   case and also occurs for isolated side pots when only one non-folded
   player contributed to that layer).
2. Otherwise, evaluate (§4.2) every seat in `eligibleSeats` and find the
   maximum comparable hand value(s). All seats whose value equals the
   maximum **tie** and split that pot's `amount` evenly.
3. **Odd-chip rule:** if `amount` does not divide evenly among the tied
   winners, distribute the remainder one chip at a time, starting with
   the tied winner closest to (and clockwise of) `buttonSeat`, until the
   remainder is exhausted. This is the standard cardroom convention for
   indivisible remainders and guarantees a fully deterministic,
   auditable result with no chips created or destroyed.
4. Each awarded amount is added to the winner's `stack`.

### 5.4 Showdown reveal order and mucking

- Cards are revealed only for seats that reach `SHOWDOWN` un-folded (a
  folded seat's cards are **never** sent to any client at any point,
  consistent with §6.3 of Stage 1).
- Reveal order: the seat that made the last aggressive action (bet/raise)
  on the river reveals first (or, if the river had no betting, the first
  active seat clockwise from the button); subsequent seats reveal in
  clockwise order. This ordering affects only the client-facing
  `SHOWDOWN` event's presentation, not the pot math above, which is
  computed independent of reveal order.
- Every seat's revealed cards, its best-hand category description, and
  the pot-by-pot winner breakdown from §5.3 are included in the
  `SHOWDOWN` event so the client can render the full result without
  further requests.

## 6. Message contract

All messages are JSON envelopes with a `type` discriminator, sent over
the single per-connection WebSocket established in Stage 1 §4. Every
server→client message that reflects committed state carries `handSeq`
and, where applicable, `actionSeq`, so clients can detect gaps (see
Client Design §2).

### 6.1 Client → Server

| `type` | Fields | When legal |
|---|---|---|
| `JOIN_TABLE` | `tableId` | any time after connect/auth |
| `SIT` | `tableId`, `seatNo`, `buyIn` | seat is `EMPTY`, `minBuyIn <= buyIn <= maxBuyIn` |
| `SIT_OUT` | `tableId` | player's own seat, any time (applied at next `HAND_STARTING` if hand in progress) |
| `SIT_IN` | `tableId` | player's own seat, status `SITTING_OUT` |
| `ACTION` | `actionId` (uuid), `handSeq`, `action` (`FOLD`\|`CHECK`\|`CALL`\|`RAISE`), `amount` (int, required for `RAISE`, new total bet-this-street) | see §2.3 validation pipeline |
| `REQUEST_SYNC` | `tableId` | any time (e.g. after reconnect) |
| `LEAVE_TABLE` | `tableId` | player's own seat, not mid-hand-as-`ACTIVE` (queued otherwise) |

`ACTION.handSeq` must match the engine's current `handSeq`; a mismatch
(stale client) is rejected with `STALE_HAND` — this catches a client
that queued an action against a hand that has since ended.

### 6.2 Server → Client

All events include `handSeq`; betting-round events additionally include
`actionSeq`. Fields marked **(private)** are computed per-recipient and
never appear in any other seat's copy of the same logical event.

| `type` | Fields | Recipients |
|---|---|---|
| `TABLE_STATE` | `seats[]` (seatNo, playerId/displayName, stack, status), `buttonSeat`, config | all, on join/seat change |
| `HAND_STARTED` | `handSeq`, `buttonSeat`, `sbSeat`, `bbSeat`, `sbAmount`, `bbAmount` | all seats at table |
| `HOLE_CARDS` | `cards: [Card, Card]` **(private)** | only the owning seat's connection |
| `TURN_STARTED` | `handSeq`, `actionSeq`, `seat`, `legalActions[]`, `toCall`, `minRaiseTo`, `maxRaiseTo` (= stack + betThisStreet), `actByMs` | all (so every client can render whose turn it is; only the acting seat's client enables its action panel) |
| `ACTION_APPLIED` | `handSeq`, `actionSeq`, `seat`, `action`, `amount`, `potTotal`, `playerStack`, `playerBetThisStreet` | all |
| `ACTION_REJECTED` | `actionId`, `reason` (`NOT_SEATED`\|`NOT_ACCEPTING_ACTIONS`\|`NOT_YOUR_TURN`\|`ILLEGAL_ACTION`\|`INVALID_AMOUNT`\|`STALE_HAND`) | only the submitting connection |
| `STREET_DEALT` | `handSeq`, `street`, `cards[]` (cumulative board) | all |
| `SHOWDOWN` | `handSeq`, `revealedHands: [{seat, cards}]`, `pots: [{amount, eligibleSeats, winners: [{seat, amount, handDescription}]}]` | all — but `revealedHands` only ever contains seats that did not fold |
| `HAND_COMPLETE` | `handSeq`, `seats: [{seatNo, stack}]` | all |
| `PLAYER_DISCONNECTED` / `PLAYER_RECONNECTED` | `seatNo` | all |
| `PLAYER_SAT_OUT` | `seatNo`, `reason` (`REQUESTED`\|`TIMEOUT_LIMIT`) | all |
| `STATE_SYNC` | full per-recipient table snapshot (seats, stacks, board, pot, `actingSeat`, own hole cards if any, `handSeq`, `actionSeq`) | requester only, computed fresh from current authoritative state |
| `ERROR` | `code`, `message` | only the offending connection (protocol-level errors, e.g. malformed JSON, distinct from `ACTION_REJECTED`'s game-rule rejections) |

### 6.3 Ordering and gap detection

Every event that mutates visible state increments `actionSeq` (reset to 0
at each `HAND_STARTED`). A client that observes a `TURN_STARTED` or
`ACTION_APPLIED` whose `actionSeq` is not exactly one greater than the
last one it saw (for the current `handSeq`) has missed a message (e.g.
brief disconnect) and must issue `REQUEST_SYNC` rather than attempt to
reconstruct state from the gap — this is a client-side responsibility
detailed in the Client Design document, but the sequencing guarantee
that makes it possible is provided here, on the server side, by
incrementing `actionSeq` exactly once per state-mutating event, in the
single serial processing order of the table's Game Engine.
