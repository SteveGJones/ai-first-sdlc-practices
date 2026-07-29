# Detailed design: server (exemplar)

**Stage:** 2 (Detailed design) — poker capstone exemplar
**Depends on:** `architecture.md`

This is the design a model in **spec-fidelity mode** receives verbatim and
implements against. It must be precise enough that two independent,
correct implementations behave identically on every scripted scenario the
stage-4 harness runs.

## Data model

```
Card       = (rank: 2..14, suit: one of ♠♥♦♣)   # 14 = Ace
Deck       = 52 unique Cards, server-side only, shuffled with os.urandom-seeded RNG
Player     = {
  seat: int, name: str, stack: int (chips),
  hole_cards: [Card, Card] | None,               # None until dealt
  status: ACTIVE | FOLDED | ALL_IN | SITTING_OUT,
  current_bet: int,                               # chips committed THIS betting round
  total_committed: int,                            # chips committed THIS HAND (all rounds) — side-pot input
  has_acted_this_round: bool,
}
Pot        = { amount: int, eligible_seats: set[int] }   # one main pot + 0..N side pots
Table      = {
  table_id: str, players: dict[seat -> Player], button_seat: int,
  community_cards: [Card] (0, 3, 4, or 5),
  betting_round: PREFLOP | FLOP | TURN | RIVER | SHOWDOWN,
  pots: [Pot],
  current_bet: int,             # highest current_bet among active players THIS round
  min_raise: int,                # smallest legal raise INCREMENT this round
  current_actor: seat | None,
  last_aggressor: seat | None,   # seat whose bet/raise players must act on
  small_blind: int, big_blind: int,
}
```

## Turn state machine

**Invariant (the one this whole design exists to guarantee):** the server
accepts an action **only** from `table.current_actor`. Any other seat's
action request is rejected with `403` and the state is unchanged. This is
checked before any other validation.

### Hand lifecycle

```
NEW_HAND
  -> post blinds (seat left of button = SB, next = BB; heads-up: button = SB)
  -> deal 2 hole cards to each ACTIVE/SITTING_OUT->ACTIVE player
  -> betting_round = PREFLOP, current_actor = seat left of BB (UTG)
  -> current_bet = big_blind, min_raise = big_blind

BETTING_ROUND (PREFLOP | FLOP | TURN | RIVER)
  each ACTIVE player in turn order (clockwise from current_actor) must:
    FOLD    -> status = FOLDED, removed from pot eligibility going forward
    CHECK   -> only legal if current_bet == this player's current_bet
    CALL    -> chips_to_add = current_bet - player.current_bet
               if chips_to_add >= player.stack: player goes ALL_IN for stack
    BET     -> only legal if current_bet == 0 this round; amount >= big_blind
    RAISE   -> only legal if current_bet > 0; new_bet - current_bet >= min_raise
               (unless the raise is an all-in for less — see "short all-in raise" below)
    (BET/RAISE that would exceed the player's stack is capped at all-in)
  round ends when: every non-folded, non-all-in player has has_acted_this_round == True
                    AND every non-folded player's current_bet == current_bet
                    (or is ALL_IN for less)
  on round end: reset has_acted_this_round for all, reset current_bet = 0,
                min_raise = big_blind, advance betting_round, deal next
                community card(s) (FLOP: 3, TURN: 1, RIVER: 1),
                current_actor = first ACTIVE player left of button
  EXCEPTION: if <=1 non-folded player remains at any point, hand ends
             immediately (no further betting/dealing) -> that player wins
             every pot without a showdown.
  EXCEPTION: if every remaining non-folded player is ALL_IN (no one left
             who can act), deal all remaining community cards immediately
             (no further betting) and go straight to SHOWDOWN.

SHOWDOWN
  -> reveal hole cards of every non-folded player
  -> evaluate best 5-card hand for each (see Hand evaluation)
  -> resolve each pot independently, richest-to-poorest side pot first is
     NOT required by this design (order doesn't affect the result — each
     pot's eligible set is fixed at pot-creation time); for each pot, the
     winner(s) are the eligible player(s) with the best hand; split equally
     on a tie (odd chips go to the first winning seat clockwise from the
     button — standard convention, deterministic)
  -> chips paid to stacks, hand ends, button advances to next ACTIVE seat
```

### Short all-in raise (does not reopen full action)

If a player goes all-in for **less** than a full legal raise (e.g. current
bet is 100, min raise is 100 so a legal raise must reach >=200, but a
player only has 150 total and goes all-in for 150), this is a **short
all-in raise**: it does not increase `min_raise`, and does not re-open
betting for players who have already acted and called the full previous
bet (they are not "un-acted" by this short raise — they may still call the
extra chips into a new side pot, but the raise itself doesn't grant them a
fresh full-raise option again). Concretely: `min_raise` only increases to
`(new_all_in_total - previous current_bet)` if that amount is `>=` the
current `min_raise`; otherwise `min_raise` is unchanged and
`has_acted_this_round` is **not** reset for players who already matched
the previous `current_bet`. `current_bet` itself still rises to the
all-in total either way (so later-to-act players still owe up to that
total to call).

## Side-pot allocation algorithm

Run once, when the hand reaches showdown (or ends early by fold-out — a
degenerate case of the same algorithm with one eligible winner).

```
contributions = {seat: player.total_committed for every seat that posted
                  any chips this hand, folded or not — a folded player's
                  chips stay in the pot they contributed to, they are just
                  not eligible to WIN any pot}
levels = sorted(unique(contributions.values()))
pots = []
previous_level = 0
for level in levels:
    layer_players = [seat for seat, c in contributions.items() if c >= level]
    layer_amount = (level - previous_level) * len(layer_players)
    if layer_amount > 0:
        eligible = [seat for seat in layer_players
                    if players[seat].status != FOLDED]
        pots.append(Pot(amount=layer_amount, eligible_seats=set(eligible)))
    previous_level = level
```

This produces one pot per distinct contribution level (the "main pot" is
simply the first/smallest layer that includes every contributor; each
subsequent layer is a side pot restricted to the players who contributed
at least that much). A pot with zero eligible winners cannot occur (the
richest-remaining contributor at any level, if non-folded, is always
eligible for every layer up to their own contribution).

## Hand evaluation

Best 5-card hand out of the player's 2 hole cards + 5 community cards
(evaluated only for non-folded players still in at showdown). Standard
9-category ranking, each hand reduced to a comparable tuple
`(category, tiebreak_values...)` where higher tuples win (Python tuple
comparison, left-to-right):

```
8  Straight flush   (high_card_rank,)
7  Four of a kind   (quad_rank, kicker_rank)
6  Full house       (trips_rank, pair_rank)
5  Flush            (rank1, rank2, rank3, rank4, rank5) descending
4  Straight         (high_card_rank,)                      # A-2-3-4-5 = "wheel", high=5
3  Three of a kind  (trips_rank, kicker1, kicker2) descending kickers
2  Two pair         (high_pair_rank, low_pair_rank, kicker)
1  One pair         (pair_rank, kicker1, kicker2, kicker3) descending
0  High card         (rank1, rank2, rank3, rank4, rank5) descending
```

Algorithm: generate all C(7,5)=21 five-card combinations from the 7 cards,
score each against the table above, take the maximum tuple
`(category, *tiebreak)`. Ace counts high (14) everywhere except the
wheel straight (A-2-3-4-5), where it also counts low — check for the wheel
as a special case (ranks `{14,2,3,4,5}`) since a naive "5 consecutive
ranks" check misses it.

## API contract

### REST

- `POST /tables` → create a table. Body: `{small_blind, big_blind}`.
  Returns `{table_id}`.
- `POST /tables/{id}/players` → seat a player. Body: `{name, buy_in}`.
  Returns `{seat}`.
- `POST /tables/{id}/start` → deal a new hand (requires >=2 seated
  players). No body.
- `POST /tables/{id}/actions` → submit an action. Body:
  `{seat, action: "fold"|"check"|"call"|"bet"|"raise", amount?: int}`
  (`amount` required for `bet`/`raise`, the **total** the player's bet
  reaches this round, not the increment). Returns the new table state on
  success, `409` with `{error: reason}` if illegal (wrong turn, illegal
  action for current state, amount doesn't meet min).
- `GET /tables/{id}/state?seat={seat}` → current state, hole cards visible
  only for `seat` (or all-folded/showdown reveals everyone's).

### WebSocket

- `WS /tables/{id}/ws?seat={seat}` → server pushes the full state (same
  redaction rule as `GET .../state`) after every action and after every
  hand-lifecycle transition (deal, round advance, showdown, payout).

## What the stage-4 harness will check

(Non-normative for implementers, but stated here so the design isn't
graded in a vacuum.) At minimum: a scripted multi-hand game asserts pot
math sums correctly, the correct hand wins at showdown, out-of-turn
actions are rejected (`403`/`409`, state unchanged), and a short-all-in
scenario produces the correct number of side pots with correct eligible
sets.
