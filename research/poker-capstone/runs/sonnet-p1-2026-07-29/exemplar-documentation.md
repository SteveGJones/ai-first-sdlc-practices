# Texas Hold'em Poker Server — Technical Documentation

This document describes the implementation in `server/app/{models,hand_eval,game_engine,main}.py`. It is derived directly from reading the source, not from any external spec.

## 1. Architecture / component responsibilities

The server is a single-process, in-memory FastAPI application with four layers:

- **`models.py`** — pure data model. `Card` (frozen dataclass, `rank` 2–14 with 14=Ace, `suit` one of `s`/`h`/`d`/`c`), `Deck` (shuffles a `full_deck()` of 52 cards and deals from the front; comment notes it is "server-side only" and card order must never be exposed to clients), `Player` (seat, stack, hole cards, `PlayerStatus`, per-round/per-hand bet tracking, `has_acted_this_round` flag), `Pot` (amount + eligible seat set), and `Table` (the aggregate root: seating, button, board, betting round, pots, current-bet/min-raise/current-actor bookkeeping, deck, and a rolling action log). `Table.to_dict(viewer_seat)` is the sole state-serialization path and is where hole-card privacy is enforced (see §7).
- **`hand_eval.py`** — pure functions, no state. Scores a 5-card hand into a comparable tuple `(category, *tiebreakers)`, and picks the best 5-of-7 (or best 5-of-N) combination for a player.
- **`game_engine.py`** — the state machine. `start_new_hand` (button/blind rotation, dealing) and `submit_action` (fold/check/call/bet/raise) are the two public entry points; all other functions are internal helpers for turn advancement, round-completion detection, side-pot computation, and hand resolution. Raises `ActionError` for any illegal request; the docstring guarantees these functions "never partially mutate state before raising" — validation happens before any state is touched (though see the correctness note in §3 about `bet`/`raise` ordering).
- **`main.py`** — FastAPI HTTP + WebSocket layer. Holds `TABLES: dict[str, Table]` and `CONNECTIONS: dict[str, dict[WebSocket, int|None]]` as global in-memory stores — no database, no auth, no persistence across restarts. Translates `ActionError` into HTTP 409. WebSocket connections are push-only (server → client); all game commands go through REST endpoints, and the socket's only job is to broadcast state and detect disconnects (the receive loop just calls `receive_text()` and discards the result).

Data flow for an action: `POST /tables/{id}/actions` → `submit_action()` mutates the `Table` in place → `_broadcast()` pushes a per-viewer-seat `to_dict()` snapshot to every open WebSocket for that table → the same snapshot (for the acting seat) is also returned synchronously in the HTTP response.

## 2. REST API surface

All game endpoints operate on a single in-memory `Table` keyed by a 12-hex-char `table_id` (`uuid.uuid4().hex[:12]`).

| Method & path | Request body | Response | Notes |
|---|---|---|---|
| `POST /tables` | `{small_blind: int=1, big_blind: int=2}` | `{table_id: str}` | 400 if `small_blind<=0`, `big_blind<=0`, or `big_blind<small_blind`. Creates an empty `Table` with a fresh `Deck`. |
| `POST /tables/{table_id}/players` | `{name: str, buy_in: int}` | `{seat: int}` | 404 if table missing, 400 if `buy_in<=0`, 409 if a hand is currently in progress. Seat number is the smallest non-negative integer not already occupied. |
| `POST /tables/{table_id}/start` | *(none)* | full table state dict (viewer_seat=None) | 409 via `ActionError` if a hand is already running or fewer than 2 eligible players. Starts a new hand, then broadcasts state to all connected sockets. |
| `POST /tables/{table_id}/actions` | `{seat: int, action: str, amount: int\|None}` | full table state dict (viewer_seat=req.seat) | `action` ∈ `fold\|check\|call\|bet\|raise`. 409 via `ActionError` for any illegal action (wrong turn, wrong player status, bad amount, etc.), with body `{"detail": "<message>"}` (FastAPI's standard `HTTPException` shape). Broadcasts state on success. |
| `GET /tables/{table_id}/state?seat=<int\|omitted>` | — | full table state dict | Read-only snapshot; `seat` query param controls hole-card visibility exactly as `viewer_seat` does elsewhere. |
| `WS /tables/{table_id}/ws?seat=<int\|omitted>` | — | pushes table state dict on connect and after every state change | Closes with code 4404 if the table doesn't exist. Server never reads client-sent frames as commands. |
| `GET /healthz` | — | `{"status": "ok"}` | Liveness check. |

**Table state dict shape** (`Table.to_dict`): `table_id`, `small_blind`, `big_blind`, `button_seat`, `community_cards` (list of `{rank, suit}`), `betting_round` (`preflop|flop|turn|river|showdown|null`), `pots` (list of `{amount, eligible_seats}`), `current_bet`, `min_raise`, `current_actor` (seat or null), `hand_in_progress`, `players` (list of per-seat `{seat, name, stack, status, current_bet, total_committed, hole_cards}` — see §7 for `hole_cards` visibility), `last_action_log` (last 20 entries), `last_showdown` (list of `{seat, hole_cards, hand_category}`, populated only after a showdown).

## 3. Turn enforcement

**Whose turn it is** — `table.current_actor` is a single seat number (or `None`) stored on `Table` and is the sole source of truth. `submit_action` first checks `if table.current_actor != seat: raise ActionError("not your turn")`. It is set:
- At hand start: the first `ACTIVE` seat starting from the seat after the big blind (`_first_actor_from`).
- After each action: `_advance()` recomputes it by scanning forward from the next seat, skipping any seat whose status is not `ACTIVE` (folded, all-in, or sitting out never get to act).
- At the start of each new betting round: the first `ACTIVE` seat strictly after the button (`_next_seat(seats, table.button_seat)` then `_first_actor_from`) — i.e. action always resets to left-of-button post-flop, regardless of who acted last.

**What makes an action legal** (`submit_action`, checked in order):
1. A hand must be in progress (`table.hand_in_progress`).
2. It must be that seat's turn (`table.current_actor == seat`).
3. The player's status must be `ACTIVE` (folded/all-in/sitting-out players cannot act — this would also normally be structurally impossible since `current_actor` only ever points at `ACTIVE` seats, but it's checked defensively).
4. Per-action rules, computed from `to_call = table.current_bet - player.current_bet`:
   - `fold`: always legal.
   - `check`: legal only if `to_call == 0`.
   - `call`: legal only if `to_call > 0`; amount added is `min(to_call, player.stack)` (i.e. a short call is allowed and forces `ALL_IN` if it exhausts the stack).
   - `bet`: legal only if `table.current_bet == 0` (no outstanding bet to call/raise instead); target must be at least `min(table.big_blind, max_reachable)` where `max_reachable = player.current_bet + player.stack` (i.e. the minimum is capped so a short-stacked player can still go all-in for less than a full bet).
   - `raise`: legal only if `table.current_bet != 0`; target must be at least `min(table.current_bet + table.min_raise, max_reachable)`, again capped by the player's stack for a short all-in raise.
   - Any wager whose computed `increment = target - player.current_bet` is `<= 0` raises `ActionError("wager must increase current bet")`.
   - Unknown action strings raise `ActionError(f"unknown action: {action}")`.

Note: `_apply_wager` validates and mutates state in the same pass (it deducts `player.stack` etc. before any subsequent code could fail) — the module docstring's claim that engine functions "never partially mutate state before raising" holds because all the raising checks in `_apply_wager` happen before the mutating lines; the mutation only happens once the target amount is already known-legal.

**Betting-round completion** (`_betting_round_complete`): true iff every player with status `ACTIVE` has both (a) `has_acted_this_round == True` and (b) `current_bet == table.current_bet`. Any wager that establishes a new `current_bet` (a real bet/raise, i.e. `full_raise or not is_all_in`) resets `has_acted_this_round = False` for every other `ACTIVE` player via `_reset_acted_except`, forcing them to act again. `_advance()` calls this after every action; if incomplete, it hands the turn to the next `ACTIVE` seat; if no such seat exists (everyone left is done acting), it force-advances the round anyway; if complete, it calls `_advance_betting_round`.

**Early hand termination**: after every action, `_maybe_end_hand_early` checks `table.non_folded_seats()`; if ≤1 remains, the hand ends immediately and that player is awarded all pots (see §4/§5), independent of whether the betting round was otherwise "complete".

**All-in fast-forward**: `_advance_betting_round` deals the next street, then checks `_count_can_still_act()` (players still `ACTIVE`, i.e. not folded/all-in). If fewer than 2 players can still act, it sets `current_actor = None` and recurses straight into the next round — dealing out the rest of the board with no further betting until showdown. This is how "everyone is all-in" hands skip directly to showdown.

## 4. Side-pot / all-in handling

`_side_pots(table)` is called once at hand end (`_finish_hand`), operating purely on `player.total_committed` (cumulative amount each player has put into the pot across all streets, not just the current round):

1. Collect `contributions = {seat: total_committed}` for every player who committed anything.
2. `levels = sorted(set(contributions.values()))` — the distinct all-in stakes (e.g. a player who went all-in for 30, another who committed 30 as well, and others who committed 100 would produce levels `[30, 100]`).
3. Walk levels from lowest to highest. At each `level`, `layer_players` = everyone whose contribution is `>= level`. The pot layer's size is `(level - previous_level) * len(layer_players)` — i.e. every player still "in" at this level contributes the incremental slice between the previous level and this one.
4. `eligible_seats` for that layer pot = the subset of `layer_players` who have not folded (folded players' chips still count toward pot *size* but they're excluded from *eligibility* to win it).
5. Zero-size layers (`layer_amount == 0`, e.g. a duplicate level) are skipped, not appended as an empty pot.

This produces a main pot plus one side pot per distinct all-in stake, each carrying its own `eligible_seats`, correctly handling multiple simultaneous all-ins at different stack depths.

**Awarding pots** (`_finish_hand`): iterates `table.pots` in order. For each pot, restrict `eligible` to seats that reached showdown (`scores` — folded players never get a score); find `best_score = max(...)` among eligible scores; `winners` = all eligible seats matching that best score (tuple equality → ties are supported and split the pot). `share = pot.amount // len(winners)`, `remainder = pot.amount - share*len(winners)`. Winners are ordered by seat distance clockwise from the button (`(seats.index(s) - seats.index(button)) % len(seats)`), and the **odd remainder chip(s) go to the first winner in that clockwise-from-button order** — a deterministic tie-break, called out in the code comment as an "approximat[ion]" of the documented rule (first winning seat clockwise from the button) using hand-seat order rather than full table seat order.

**Fold-out short-circuit**: if the hand ends because everyone else folded (`awarded_seats` passed with 0 or 1 seats from `_maybe_end_hand_early`), side pots are still computed via `_side_pots` for bookkeeping/logging, but the sole remaining player is simply awarded the full amount of every pot outright — no hand evaluation or eligibility filtering occurs in this branch. If `awarded_seats` is empty (a table edge case with zero non-folded players — not expected in normal play, but structurally reachable), `winner` is `None` and nothing is paid out.

## 5. Hand evaluation (`hand_eval.py`)

`best_hand(hole_cards, community_cards)`: concatenates hole + community cards and takes the `max()` of `score_five(combo)` over every 5-card `combinations()` of them — i.e. brute-force best-5-of-7 (or best-5-of-N if fewer than 7 cards are supplied; the docstring notes real showdown hands always reach a full 7, but the function tolerates fewer, raising `ValueError` only if there are fewer than 5 total).

`score_five` returns a tuple `(category, *tiebreakers)` where category is one of 9 integers `HIGH_CARD..STRAIGHT_FLUSH` (`range(9)`), and Python tuple comparison does the ranking (`max()` across candidate hands directly finds the best one — higher category always outranks all tiebreakers of a lower category since it's compared first).

Notable logic / edge cases:
- **Wheel straight (A-2-3-4-5)**: handled explicitly in `_straight_high` — `if ranks_desc == [14, 5, 4, 3, 2]: return 5`. The Ace counts low and the straight's rank for comparison purposes is 5, not 14, so a wheel straight is correctly the *lowest* straight, not the highest, and (per the ranking) a wheel straight cannot also be conflated with a "5-high broadway" straight. Ordinary straights are detected by checking all 4 consecutive gaps equal 1 in the 5 sorted-descending distinct ranks.
- **Straight flush check happens before quads/full-house checks** and is independent of the general straight/flush code paths — `if is_flush and straight_high is not None: return (STRAIGHT_FLUSH, straight_high)` is evaluated first, using the same wheel-aware `_straight_high` helper (so a steel-wheel A-2-3-4-5 suited is correctly a straight flush with tiebreak 5).
- **Category ordering by group-count pattern**: after ruling out straight flush, checks are: quads (`[4,1]`) → full house (`[3,2]`) → flush → straight → trips (`[3,1,1]`) → two pair (`[2,2,1]`) → one pair (`[2,1,1,1]`) → high card. This ordering matters because e.g. a flush must be checked before straight (a 5-card flush that isn't also a straight still beats a straight), and both must be checked after quads/full house since those outrank flush regardless of suit/sequence.
- **Kicker ordering**: for two pair, the tiebreak tuple is `(TWO_PAIR, higher_pair_rank, lower_pair_rank, kicker)` — pairs are explicitly sorted descending rather than relying on `groups`' insertion order, so a pocket-pair vs. board-pair scenario is compared correctly. For flush and high card, all 5 ranks are included in descending order as the full tiebreak tuple (`(FLUSH, *ranks)`), so a flush's tiebreak legitimately compares every card, not just the top one.
- `distinct_ranks` uses `sorted(set(ranks), reverse=True)`; `straight_high` is only computed `if len(distinct_ranks) == 5` — this correctly prevents e.g. a 4-of-a-kind's 4 identical ranks + 1 kicker from being mistaken for straight material (fewer than 5 distinct ranks can never form a straight).

`describe(score)` maps `score[0]` back to a human-readable string (`"straight_flush"`, `"four_of_a_kind"`, etc.) via `CATEGORY_NAMES`, used to populate `last_showdown` entries.

## 6. Blinds and dealer button

**Button rotation** (`start_new_hand`): on the very first hand (`button_seat is None` or the stored button seat is no longer in the hand, e.g. that player left/busted), the button is assigned to the first seat in `_hand_seats(table)` order (numerically lowest occupied, non-sitting-out seat). Otherwise it moves to `_next_seat(seats, table.button_seat)` — the next occupied seat in numeric seat order, wrapping around. `_hand_seats` excludes only `SITTING_OUT` players (busted players — `stack<=0` — are moved to `SITTING_OUT` at the top of `start_new_hand` before this list is built, so they're automatically skipped for button/blind purposes going forward).

**Blind posting**:
- **Heads-up (exactly 2 hand-eligible seats)**: the *button* posts the small blind, and the other player posts the big blind (`sb_seat = table.button_seat; bb_seat = _next_seat(seats, sb_seat)`). This is the standard heads-up convention where the button is also the small blind.
- **3+ players**: small blind is the seat after the button, big blind is the seat after that (`sb_seat = _next_seat(seats, table.button_seat); bb_seat = _next_seat(seats, sb_seat)`) — normal ring-game blind assignment.

`_post_blind` deducts `min(amount, player.stack)` from the player's stack (so a short-stacked blind post is allowed and immediately sets that player `ALL_IN` if it exhausts their stack — there is no minimum-stack requirement to post a blind).

**First actor preflop**: `first_to_act = _next_seat(seats, bb_seat)` — the seat after the big blind — regardless of heads-up or full-ring, i.e. standard "under the gun" order preflop. (In heads-up this means the big blind — the non-button player — acts second and, because the button also posted the small blind and there are only two hand seats, `_next_seat(seats, bb_seat)` wraps back to the button/small-blind seat, so the button/SB acts first preflop, consistent with standard heads-up rules where SB acts first preflop and last postflop.)

**Postflop first actor**: always the first `ACTIVE` seat strictly after the button (`_advance_betting_round`), for every round after preflop, in both heads-up and multi-way — this reverses the heads-up order for the flop/turn/river relative to preflop (in heads-up, the big blind/non-button player now acts first postflop), matching standard button-relative post-flop action order.

`table.last_aggressor` is set to the big-blind seat at hand start (`table.last_aggressor = bb_seat`) and updated to whoever makes a full bet/raise thereafter; it is tracked but not read anywhere else in these four files (no visible consumer of `last_aggressor` in `game_engine.py` beyond assignment) — it appears to be state maintained for a purpose not exercised in this code (e.g. reserved for future use or an API consumer).

## 7. Hole card privacy

Enforced in exactly one place: `Player.public_dict(reveal_hole_cards)`, called from `Table.to_dict(viewer_seat)`:

```python
self.players[s].public_dict(reveal_hole_cards=(s == viewer_seat or showdown))
```

where `showdown = self.betting_round == BettingRound.SHOWDOWN`. So for each player `s` being serialized, hole cards are included (`[c.to_dict() for c in self.hole_cards]`) if and only if:
- the viewer *is* that seat (`s == viewer_seat`) — a player always sees their own cards, or
- the hand has reached showdown (`betting_round == SHOWDOWN`) — at showdown, **everyone's** (non-folded, since only non-folded players have entries in `last_showdown`/still hold `hole_cards`) hole cards become visible to all viewers, matching a real-table showdown reveal.

Otherwise `hole_cards` is `None` in the serialized dict, even if the underlying `Player.hole_cards` list is populated server-side.

`viewer_seat` is supplied per-request/per-connection:
- REST `POST /start`: `viewer_seat=None` — nobody's cards are revealed except via showdown (this is a broadcast-style response with no specific viewer, e.g. no seat has "self" cards revealed).
- REST `POST /actions`: `viewer_seat=req.seat` — the acting player's own response reveals only their own cards (plus anyone else's if showdown).
- REST `GET /state?seat=`: caller-supplied `seat` query param, defaulting to `None` if omitted (no self-reveal, showdown-only).
- WebSocket: `seat` is captured once at connect time from the query string and stored in `CONNECTIONS[table_id][websocket] = seat` — each socket's broadcast payload is built individually per-connection via `table.to_dict(viewer_seat=seat)` in `_broadcast`, so different clients connected to the same table see different, correctly-scoped payloads from the same underlying state.

Card order/identity in the deck (`Deck._cards`, a private attribute) is never serialized anywhere — the `models.py` comment states the deck is "Server-side only. Never expose card order/remaining cards to clients," and indeed no endpoint or `to_dict` method exposes it. There is no authentication tying a WebSocket/HTTP caller to a seat — `viewer_seat`/`seat` is simply a caller-declared query/body parameter, so hole-card privacy is enforced only against a *claimed* seat, not a cryptographically or session-verified one; anyone who knows or guesses another player's seat number can request `GET /state?seat=<that seat>` and see their hole cards. This is a real gap in the privacy model as implemented (no auth layer exists anywhere in `main.py`).
