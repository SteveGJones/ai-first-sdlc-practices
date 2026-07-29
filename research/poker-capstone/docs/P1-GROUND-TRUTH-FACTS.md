# P1 ground-truth facts (judge reference — never shown to the model under test)

Specific, checkable claims about the exemplar's *actual implementation*
(`exemplar/server/app/{models,hand_eval,game_engine,main}.py`), extracted
by re-reading the current source, not copied from the design docs (which
could themselves have drifted — see P10). Used by a judge subagent to
grade a candidate's documentation for **factual accuracy**, distinct from
the deterministic checklist's topic-coverage-only check
(`harness/doc_fidelity.py`).

Each fact has an id for reference in a judge verdict.

## Turn enforcement

- **F1**: `submit_action` checks, in order: (1) a hand must be in
  progress (`table.hand_in_progress`), THEN (2) the acting `seat` must
  equal `table.current_actor`, raising `ActionError` ("no hand in
  progress" / "not your turn" respectively) — no partial state mutation
  happens before either check.
  **Corrected 2026-07-29**: this fact originally (incorrectly) claimed
  the turn check happens "before any other validation." A P1 judge run
  penalized a candidate's documentation as INCORRECT for correctly
  reporting the real order (hand-in-progress, then turn) — verified
  against the actual source and fixed here; the candidate was right, the
  fact was wrong. See `retrospectives/237-council-poker-capstone.md`.
- **F2**: A player whose `status` is not `ACTIVE` (folded/all-in/sitting-
  out) cannot act even if somehow addressed — checked immediately after
  the turn check (i.e. third in the overall order, after F1's two
  checks).

## Betting round closure

- **F3**: A betting round is complete when every seat with status
  `ACTIVE` has both (a) `has_acted_this_round == True` and (b)
  `current_bet == table.current_bet`. Folded and all-in seats are exempt
  from this check.
- **F4**: When a player bets or raises, `has_acted_this_round` is reset
  to `False` for every *other* `ACTIVE` seat (`_reset_acted_except`) —
  reopening the round for them, EXCEPT in the short-all-in-raise case
  (F6).

## Short all-in raise (the one genuinely subtle rule)

- **F5**: A raise's size is `target - table.current_bet`. It counts as a
  "full" raise if that size is `>= table.min_raise`.
- **F6**: A raise that is BOTH an all-in (uses the player's entire
  remaining stack) AND smaller than a full raise (`raise_size <
  table.min_raise`) does **not** reset other players' `has_acted_this_round`
  and does **not** increase `table.min_raise` — but it DOES still raise
  `table.current_bet` to the new (higher) target, so later-to-act players
  still owe up to that amount to call.

## Side pots

- **F7**: Side pots are computed by layering distinct contribution levels
  (`total_committed` per seat): for each ascending level, one pot layer
  of size `(level - previous_level) * count_of_seats_who_reached_that_level`,
  with eligibility = seats at that level minus folded seats.
- **F8**: A folded player's chips remain in whichever pot layer(s) they
  contributed to (the pot amount includes them) — they are just excluded
  from `eligible_seats`, so they cannot win that chip back.
- **F9**: On a tie for a pot, it splits evenly; any odd remainder chip
  goes to the tied winner closest to the button in clockwise seat order
  (not, e.g., lowest seat number, or the first-to-act order).

## Hand evaluation

- **F10**: Best hand is the max-scoring 5-card combination out of all
  C(7,5)=21 combinations of the 2 hole cards + up to 5 community cards.
- **F11**: The A-2-3-4-5 "wheel" straight is recognized as a straight
  (and straight flush, if suited) with the Ace counting LOW — i.e. this
  is a special case, not something a naive "5 consecutive ranks" check
  catches (Ace is rank 14 everywhere else).
- **F12**: There are exactly 9 standard hand categories, standard
  poker ranking order (high card lowest, straight flush highest).

## Blinds / button

- **F13**: In a 3+ handed hand, small blind = seat immediately clockwise
  of the button, big blind = next seat after that, first to act preflop
  = next seat after the big blind. **In heads-up (exactly 2 seats), this
  is different**: the button itself posts the small blind, and is also
  the first to act preflop — the other seat is the big blind.

## API / privacy

- **F14**: The server exposes both a REST API (create table, seat
  player, start hand, submit action, get state) and a push-only
  WebSocket (state broadcast after every change) — actions are only ever
  submitted via REST, never over the WebSocket.
- **F15**: A given state response reveals a seat's hole cards only to
  that seat itself, UNLESS the hand has reached showdown, in which case
  every non-folded seat's hole cards become visible to everyone.
