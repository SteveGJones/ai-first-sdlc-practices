# Poker Capstone — Client Detailed Design (Stage 2)

## 0. Scope and inputs

This document details the **Web Client** component from Stage 1
(`stage1/architecture.md`) against the exact message contract fixed in
`stage2/design-server.md` §6. It assumes the Stage 1 decision that the
client holds **no independent game logic** — it is a renderer of
server-pushed state plus a submitter of action intents. Every message
type, field name, and turn-enforcement mechanism referenced below is
defined in the server design document and must match it exactly; the
client never invents its own notion of legality.

## 1. Client architecture: single authoritative local store

The client keeps exactly one client-side state object, `TableView`,
which is a **pure projection of the last-received server messages** —
never independently derived or advanced. It is implemented as a reducer
(`applyServerEvent(state, event) -> newState`) driven only by inbound
`ServerEvent`s from §6.2 of the server design. No other code path is
allowed to mutate `TableView`.

```
TableView {
  handSeq: int
  actionSeq: int
  street: PREFLOP | FLOP | TURN | RIVER | SHOWDOWN | null
  board: Card[]                 // 0-5 community cards, as revealed so far
  potTotal: int
  seats: SeatView[]             // seatNo, displayName, stack, betThisStreet,
                                 // status, isMe
  buttonSeat: int
  actingSeat: int | null
  actByMs: int | null
  legalActionsForMe: Action[]   // only populated when actingSeat == mySeat
  toCall: int
  minRaiseTo: int
  maxRaiseTo: int
  myHoleCards: Card[] | null    // see §4 — never any other seat's cards
  showdown: ShowdownView | null // only set while displaying SHOWDOWN results
  pendingAction: { actionId, action, amount } | null   // see §3.2
  connectionStatus: CONNECTED | RECONNECTING | DESYNCED
}
```

`TableView` is rebuilt from scratch by `STATE_SYNC` (full snapshot,
replace-not-merge) and incrementally updated by every other event type,
per the mapping in §2.

## 2. Staying in sync with server state

### 2.1 Event-driven, replace-on-gap

The client subscribes to the WebSocket and applies inbound events in
arrival order (the socket already guarantees ordering per Stage 1 §4.2).
Handling per event type:

- `TABLE_STATE` → replace `seats`/`buttonSeat`.
- `HAND_STARTED` → reset `board=[]`, `potTotal=0`, per-seat
  `betThisStreet=0`/`status=ACTIVE`, `showdown=null`, set `handSeq`,
  `actionSeq=0`, clear `myHoleCards` (fresh hand).
- `HOLE_CARDS` → set `myHoleCards` (this event is only ever received for
  the client's own seat — see §4).
- `TURN_STARTED` → set `actingSeat`, `actByMs`; if
  `event.seat == mySeat`, populate `legalActionsForMe`, `toCall`,
  `minRaiseTo`, `maxRaiseTo` from the event; otherwise clear those four
  fields (they are meaningless — and must not be shown as actionable —
  when it isn't this client's turn).
- `ACTION_APPLIED` → update the acting seat's `stack`/`betThisStreet`,
  `potTotal`; if `event.seat == mySeat` and it matches
  `pendingAction.actionId`'s action/amount, clear `pendingAction`
  (resolve the optimistic UI state — see §3.2).
- `ACTION_REJECTED` → if it matches `pendingAction.actionId`, clear
  `pendingAction` and surface `event.reason` as a transient inline
  message near the action panel (never a full-screen error — this is a
  routine, expected outcome, e.g. a click that raced a timeout-driven
  auto-fold).
- `STREET_DEALT` → append `event.cards` to `board`, reset all seats'
  `betThisStreet=0` for the new street's display (matches server-side
  reset in design-server.md §2.6 step 5).
- `SHOWDOWN` → set `showdown` to the event payload (revealed hands, pot
  breakdown, winners) for rendering; `actingSeat=null`.
- `HAND_COMPLETE` → update final `seats[].stack` from the event; leave
  `showdown` populated for a short display period (client-local timer,
  purely presentational) before the UI clears it on the next
  `HAND_STARTED`.
- `PLAYER_DISCONNECTED`/`PLAYER_RECONNECTED`/`PLAYER_SAT_OUT` → update
  the affected seat's displayed status badge only.
- `STATE_SYNC` → **discard the entire current `TableView` and rebuild it
  from the snapshot.** This is the only "patch the whole thing" case;
  every other event above is an incremental update.
- `ERROR` → surface as a transient toast; does not mutate `TableView`.

### 2.2 Gap detection drives resync, never local reconstruction

Every incoming event that carries `actionSeq` is checked: if
`event.actionSeq != TableView.actionSeq + 1` (for the same `handSeq`), or
if `event.handSeq` doesn't match what the client expects (e.g. jumped
without a `HAND_STARTED` in between), the client does **not** attempt to
interpolate or guess the missing state. It immediately:

1. Sets `connectionStatus = DESYNCED`,
2. Sends `REQUEST_SYNC`,
3. On receiving `STATE_SYNC`, rebuilds `TableView` wholesale and sets
   `connectionStatus = CONNECTED`.

This is the client-side half of the sequencing contract defined in
`design-server.md` §6.3.

### 2.3 Reconnection

On WebSocket close, the client shows a "Reconnecting…" banner
(`connectionStatus = RECONNECTING`) and attempts reconnect with backoff.
On successful reconnect it re-authenticates and immediately sends
`REQUEST_SYNC` — it never resumes rendering from whatever `TableView` it
had before the drop, since server state may have advanced arbitrarily far
(the design-server.md §2.8 timeout mechanism may have auto-folded the
player, a full hand may have completed, etc.). `TableView` is only
trusted again once a fresh `STATE_SYNC` has been applied.

## 3. Submitting player actions

### 3.1 Action panel gating

The action panel (Fold / Check / Call / Bet-Raise-with-slider) is
rendered as **enabled** if and only if `TableView.actingSeat == mySeat`
and `TableView.legalActionsForMe` is non-empty; otherwise it is rendered
disabled/hidden with a "waiting for [seat]'s action" indicator instead.
This is explicitly a UX convenience, not a security boundary — per Stage
1 §7 and server design §2.3, the server independently re-derives and
enforces legality on every submitted `ACTION` regardless of what the
client's UI allowed the user to click. The client must not assume a
disabled button prevents an action from ever being sent (e.g. a stale
render racing a `TURN_STARTED` that just passed the turn on); it relies
on the server's rejection path (§3.3) as the real backstop.

Only the buttons corresponding to `legalActionsForMe` are shown as
enabled: e.g. if `toCall == 0`, `CHECK` is offered (not a zero-amount
"Call"); if `toCall > 0`, `CALL` (labeled with the exact `toCall` amount)
is offered instead of `CHECK`. The bet/raise slider, when `BET`/`RAISE`
is legal, is bounded to `[minRaiseTo, maxRaiseTo]` from the last
`TURN_STARTED` addressed to this seat, with the upper bound clearly
labeled "All-in" when the slider is at `maxRaiseTo`.

### 3.2 Submission flow and optimistic UI

On click, the client:

1. Generates a fresh `actionId` (UUID).
2. Sends `{ type: "ACTION", actionId, handSeq: TableView.handSeq, action,
   amount? }`.
3. Sets `pendingAction = { actionId, action, amount }` and immediately
   disables the action panel (prevents double-submit on double-click)
   and shows a "waiting for server…" spinner state on the clicked
   button.
4. Does **not** update stack/pot/board optimistically — those numbers
   are only ever updated by `ACTION_APPLIED` (§2.1). The only thing the
   optimistic state changes is disabling further input and showing
   pending status; it never predicts or displays a game-state outcome
   before the server confirms it.
5. On matching `ACTION_APPLIED`: clear `pendingAction`; the panel
   re-disables anyway because `TURN_STARTED` for the next seat will have
   already arrived or will shortly, clearing `legalActionsForMe`.
6. On matching `ACTION_REJECTED`: clear `pendingAction`, re-enable the
   panel (if it's still this client's turn per current `TableView`),
   and show the rejection reason inline (mapped to a short human string,
   e.g. `NOT_YOUR_TURN` → "That wasn't your turn — the table has moved
   on."; `INVALID_AMOUNT` → "Bet must be between {minRaiseTo} and
   {maxRaiseTo}.").
7. If no response arrives within a client-side UI timeout (e.g. 5s) —
   distinct from and shorter than the server's `actionTimeoutMs` — the
   client shows a "still waiting…" indicator but does **not** resend
   automatically (the `actionId` idempotency guarantee in
   design-server.md §2.7 means a manual resend by the user, or an
   eventual reconnect + resync, is always safe; auto-resend is avoided
   to keep behavior simple and predictable).

### 3.3 The action panel is not the enforcement mechanism

To restate plainly, because it's the most important integration
contract between the two documents: the client may only ever *ask* the
server to apply an action. Nothing in the client can cause a card to be
dealt, a pot to change, or a turn to advance — those effects only ever
originate from a server broadcast (§2.1). A compromised or hand-edited
client can send arbitrary `ACTION` messages at arbitrary times; the
worst it can do is generate `ACTION_REJECTED` responses, because the
server's validation pipeline (design-server.md §2.3) re-checks turn,
legality, and amount independently of anything the client displayed.

## 4. Turn display

- The acting seat (`TableView.actingSeat`) is highlighted with a
  distinct visual treatment (e.g. glowing border) on **every** connected
  client's view of the table, not just the acting player's — all seats
  need to see whose turn it is, per `TURN_STARTED` being broadcast to
  `all` (design-server.md §6.2).
- A countdown ring/bar around the acting seat's avatar is driven by
  `actByMs`: `remainingMs = actByMs - Date.now()`, recomputed on a local
  animation-frame or 250ms interval tick — this is a **pure display
  countdown**, not a control that can cause anything to happen
  client-side; if the client's countdown reaches zero before the server
  acts, the display simply shows "0:00" and waits — the actual timeout
  action is applied server-side and arrives as an ordinary
  `ACTION_APPLIED`/`TURN_STARTED` pair like any other action
  (design-server.md §2.8). No client-side clock is ever treated as
  authoritative for whether a timeout occurred.
- Only the local player, when `actingSeat == mySeat`, additionally sees
  the enabled action panel (§3.1) and a more prominent "Your turn"
  callout/sound cue.

## 5. Hole cards — visibility rules

This is the other integration point that must be exactly right.

- The client renders **exactly two card slots per occupied seat** at all
  times during a hand: for `TableView.seats[s].isMe`, if `myHoleCards`
  is set, render the two actual cards; for every other seat, always
  render generic card-back placeholders — **never** any value, even a
  ciphered/masked one — because the server never transmits another
  seat's hole cards to this client in the first place (design-server.md
  §4.1, §5.4: hole-card and fold-mucking are server-side, per-recipient
  projections). There is structurally nothing for the client to
  accidentally leak, but the client is still written defensively: the
  hole-card rendering component only ever reads from
  `TableView.myHoleCards`, and no other in-memory structure on the
  client ever holds a `Card` value attributed to a seat that isn't
  `isMe`, except the one exception below.
- **The one exception — showdown reveals:** when `TableView.showdown` is
  populated, `showdown.revealedHands` (from the `SHOWDOWN` event) may
  legitimately contain other seats' cards — but *only* for seats that
  did not fold, and *only* because the server explicitly chose to reveal
  them as part of judging the hand (design-server.md §5.4). The client
  renders these face-up only for the seats listed in
  `showdown.revealedHands`; any seat not listed there (folded before
  showdown) keeps its card-back placeholder and its cards are never
  shown, because the server never sent them.
- The client never requests, caches, or infers another player's hole
  cards through any side channel (e.g. no "reveal my cards" broadcast is
  echoed back to other clients client-side — each client only ever
  learns its own cards from its own private `HOLE_CARDS` event).
- On `HAND_STARTED`, `myHoleCards` is cleared until the next
  `HOLE_CARDS` event for this client arrives, so a fold-then-immediately-
  render-next-hand transition can never display stale cards from a
  previous hand.

## 6. Pot and bet display

- **Total pot:** `TableView.potTotal`, shown prominently at table
  center; updated only from `ACTION_APPLIED.potTotal` (§2.1) — never
  computed client-side by summing bets, to avoid any drift from the
  server's authoritative figure.
- **Per-seat current bet:** each seat shows a small chip-stack graphic
  labeled with `seats[s].betThisStreet`, reset to 0 visually at the start
  of each new street (`STREET_DEALT`) to match the server's own reset
  (design-server.md §2.6 step 5) — the client does not invent a separate
  "total this street" figure; it mirrors server state exactly.
- **Stack size:** each seat shows `seats[s].stack`, updated on every
  `ACTION_APPLIED` for that seat and on `HAND_COMPLETE`.
- **To-call indicator:** when it is this client's turn, the action panel
  shows `toCall` explicitly on the Call button (e.g. "Call 40") rather
  than a bare "Call", sourced from the same `TURN_STARTED` event that
  gated the panel (§2.1, §3.1) — never independently computed from
  `currentBet - myBetThisStreet` client-side, even though that would be
  arithmetically equivalent, because the rule in this design is that
  every number the client displays for legality/amounts is a verbatim
  passthrough of a server-provided field, not a client-side recomputation
  that could silently diverge if the two documents' formulas ever drift.
- **Side pots at showdown:** `showdown.pots[]` (each with `amount`,
  `eligibleSeats`, and `winners`) is rendered as a labeled list ("Main
  pot: 240 → Player C", "Side pot: 120 → split Player C / Player D") —
  a direct rendering of the server's pot-by-pot breakdown from
  design-server.md §5, with no client-side pot-splitting logic
  whatsoever.
- **All-in indicator:** a seat with `status == ALL_IN` gets a distinct
  badge/overlay on its stack (now necessarily 0) so it's visually clear
  why that seat isn't acting on later streets.

## 7. Summary of the client/server integration contract

| Concern | Client behavior | Server guarantee it relies on |
|---|---|---|
| Whose turn | Highlight `actingSeat` from `TURN_STARTED`, broadcast to all | design-server.md §2.6 broadcasts every turn change |
| Enabling my action panel | Enabled iff `actingSeat==mySeat` | Purely a convenience; server re-validates independently (§2.3) |
| Submitting an action | Send `ACTION` with fresh `actionId`; never mutate local state ahead of confirmation | Idempotent apply (§2.7), authoritative accept/reject (§2.3) |
| Hole card privacy | Render only `myHoleCards`; never store/display another seat's cards pre-showdown | Server never transmits another seat's cards except via `SHOWDOWN.revealedHands` for non-folded seats (§4.1, §5.4) |
| Pot/bet numbers | Verbatim passthrough of server fields, never recomputed | `ACTION_APPLIED`/`STREET_DEALT`/`SHOWDOWN` carry authoritative totals (§6.2) |
| Staying in sync | Rebuild wholesale from `STATE_SYNC` on any `actionSeq`/`handSeq` gap or reconnect | Strictly incrementing `actionSeq` per table, serial processing (§2.6, §6.3) |
