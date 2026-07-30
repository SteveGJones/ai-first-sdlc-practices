# Texas Hold'em Poker Server — Technical Implementation Documentation

**Based on:** exemplar/server/app/ (models.py, hand_eval.py, game_engine.py, main.py)

**Scope:** Single-table, in-memory implementation. No database, no persistence, no authentication. Table state is transient (lost on server restart). Designed for experimentation and testing.

---

## 1. Architecture & Component Responsibilities

The implementation is organized into four layers:

### 1.1 models.py — Data Structures

**Responsibility:** Defines all immutable poker game entities and table state.

**Key classes:**

- **Card** (immutable dataclass)
  - `rank: int` — 2 through 14 (14 = Ace)
  - `suit: str` — one of `"s"`, `"h"`, `"d"`, `"c"` (spades, hearts, diamonds, clubs)
  - Methods: `__str__()` returns rank name + suit (e.g., "As", "Kh"), `to_dict()` returns `{"rank": int, "suit": str}`

- **Deck** (server-side only)
  - Manages shuffled card stock (52 cards initially)
  - `deal(n: int)` — removes and returns the first n cards; raises `ValueError("deck exhausted")` if fewer than n remain
  - Never exposed to clients — order and remaining count are secret

- **Player** (mutable dataclass)
  - `seat: int` — unique seat identifier at this table
  - `name: str` — player name (no validation)
  - `stack: int` — chips available for betting (decreases as player wagers, increases when winning pots)
  - `hole_cards: list[Card] | None` — two private cards dealt at start of hand; `None` between hands
  - `status: PlayerStatus` — one of `ACTIVE`, `FOLDED`, `ALL_IN`, `SITTING_OUT`
  - `current_bet: int` — amount wagered in current betting round (reset to 0 at start of each round)
  - `total_committed: int` — cumulative amount wagered across all rounds of current hand (used for side-pot calculation)
  - `has_acted_this_round: bool` — whether this player has taken an action in the current betting round
  - Method: `public_dict(reveal_hole_cards: bool)` — returns serializable dict; hole_cards are `None` unless `reveal_hole_cards=True`
  - Method: `reset_for_new_hand()` — clears hole_cards, current_bet, total_committed, has_acted_this_round; sets status to `ACTIVE` (unless `SITTING_OUT`)

- **Pot** (immutable dataclass)
  - `amount: int` — chips in this pot
  - `eligible_seats: set[int]` — seats that contributed to this pot and did not fold (eligible to win)
  - Method: `to_dict()` — returns `{"amount": int, "eligible_seats": sorted list}`

- **Table** (mutable dataclass)
  - `table_id: str` — unique identifier (generated as 12-char hex UUID)
  - `small_blind: int`, `big_blind: int` — blinds in chips
  - `players: dict[int, Player]` — seated players keyed by seat number
  - `button_seat: int | None` — current button position (dealer marker); moves after each hand
  - `community_cards: list[Card]` — flop (3), turn (1), river (1) dealt progressively
  - `betting_round: BettingRound | None` — current phase (PREFLOP/FLOP/TURN/RIVER/SHOWDOWN) or `None` when no hand
  - `pots: list[Pot]` — side pots; computed at showdown
  - `current_bet: int` — highest bet/raise facing players this round (players must match or all-in to continue)
  - `min_raise: int` — minimum raise size (initially big blind; resets to big blind each round; updates when a full raise occurs)
  - `current_actor: int | None` — seat of player whose turn it is; `None` when no action needed
  - `last_aggressor: int | None` — seat of player who made last bet/raise (used to end round if all others fold/all-in)
  - `deck: Deck | None` — current deck (set at hand start, `None` between hands)
  - `hand_in_progress: bool` — whether a hand is running (seats cannot be added mid-hand)
  - `last_action_log: list[str]` — recent actions (capped at 20 entries on serialization); format: `"seat N folds"`, `"seat N calls X"`, `"-- flop --"`, etc.
  - `last_showdown: list[dict]` — hand results from most recent showdown; each entry: `{"seat": int, "hole_cards": [{rank, suit}, ...], "hand_category": str}`

  - Method: `public_dict(viewer_seat: int | None)` — serializes entire table state for an observer; hole cards visible only to the viewer (if they have a seat) or to all during showdown
  - Method: `active_seats()` — seats with status `ACTIVE` or `ALL_IN` (can still win pots)
  - Method: `non_folded_seats()` — seats with status != `FOLDED` (eligible for current hand)

**Enums:**
- `PlayerStatus`: `ACTIVE`, `FOLDED`, `ALL_IN`, `SITTING_OUT` (string enum, serialized as `.value`)
- `BettingRound`: `PREFLOP`, `FLOP`, `TURN`, `RIVER`, `SHOWDOWN` (string enum)

---

### 1.2 hand_eval.py — Hand Scoring

**Responsibility:** Evaluates and compares poker hands. Uses best-5-of-7 selection (hole cards + community cards).

**Hand categories** (ordered by rank strength):
- 0 = `HIGH_CARD` — no pairs or straights; tie-break by ranks descending
- 1 = `ONE_PAIR` — tie-break by pair rank, then kickers descending
- 2 = `TWO_PAIR` — tie-break by high pair, low pair, kicker
- 3 = `TRIPS` (three of a kind) — tie-break by trips rank, kickers descending
- 4 = `STRAIGHT` — tie-break by high card; Ace-low straight (wheel: 5-4-3-2-A) has high card 5, NOT 14
- 5 = `FLUSH` — tie-break by ranks descending
- 6 = `FULL_HOUSE` — tie-break by trips rank, pair rank
- 7 = `QUADS` (four of a kind) — tie-break by quads rank, kicker
- 8 = `STRAIGHT_FLUSH` — tie-break by high card (wheel = 5)

**Key functions:**

- `score_five(cards: tuple[Card, ...]) -> tuple` — scores exactly 5 cards
  - Returns tuple: `(category_int, *tiebreak_values)`
  - Tuples are compared lexicographically: higher category always beats lower; within category, tiebreak values compared left-to-right
  - Wheel special case: ranks [14, 5, 4, 3, 2] are detected as straight with high card 5 (not 14)

- `best_hand(hole_cards: list[Card], community_cards: list[Card]) -> tuple` — finds best scoring 5-card combination from 7 cards
  - Raises `ValueError("need at least 5 cards to score a hand")` if fewer than 5 cards total
  - Returns same tuple format as `score_five()`

- `describe(score: tuple) -> str` — converts category int to human-readable name (e.g., "straight", "full_house")

**Comparison:** Higher score tuple always wins (first element is category; higher category beats lower; within category, lexicographic comparison of tiebreak values). Ties in all tiebreak values result in equal hands.

---

### 1.3 game_engine.py — Turn State Machine & Betting

**Responsibility:** Enforces legal actions, manages betting rounds, computes pots, runs hand conclusion.

**Core functions:**

- `start_new_hand(table: Table, deck: Deck | None = None) -> Table`
  - Raises `ActionError("a hand is already in progress")` if `table.hand_in_progress == True`
  - Raises `ActionError("need at least 2 players with chips to start a hand")` if fewer than 2 active players
  - Marks as sitting out any player with `stack <= 0`
  - Advances button (clockwise, wrapping): first button is first-seated player; subsequent buttons move to next active player
  - Posts blinds: in heads-up (2 players), button posts small blind; other posts big blind; in 3+ players, small blind is next seat after button, big blind is next after that
  - Blind posting uses `_post_blind()`, which subtracts min(blind_amount, player.stack) from stack, adds to current_bet and total_committed; marks player ALL_IN if stack reaches 0
  - Deals 2 hole cards to each active player
  - Sets `betting_round = PREFLOP`, `current_bet = big_blind`, `min_raise = big_blind`
  - First to act: seat after big blind (heads-up: small blind acts first preflop)
  - Sets `current_actor` to first ACTIVE player at/after that position
  - Calls `_maybe_end_hand_early()` (ends if only 1 non-folded player remains)
  - Returns table

- `submit_action(table: Table, seat: int, action: str, amount: int | None = None) -> Table`
  - **Pre-flight checks (raise `ActionError` for violations):**
    - No hand in progress → `"no hand in progress"`
    - Not current actor → `"not your turn"`
    - Player not ACTIVE → `"player cannot act"` (covers FOLDED, ALL_IN, SITTING_OUT)
  
  - **Action processing:**
    - `action="fold"`: Sets player status to FOLDED; logs action
    - `action="check"`: Requires `to_call == 0` (no bet facing); raises `ActionError("cannot check, facing a bet")` otherwise; logs
    - `action="call"`: Requires `to_call > 0`; raises `ActionError("nothing to call, use check")` if `to_call <= 0`; calls `min(to_call, player.stack)` (may result in all-in); logs actual amount called
    - `action="bet"`: Requires `current_bet == 0` (no bet yet this round); raises `ActionError("cannot bet, must call/raise/fold")` otherwise; calls `_apply_wager(amount, is_raise=False)`; logs "bets X"
    - `action="raise"`: Requires `current_bet > 0`; raises `ActionError("cannot raise, must bet")` if no bet facing; calls `_apply_wager(amount, is_raise=True)`; logs "raises to X"
    - Unknown action → `ActionError(f"unknown action: {action}")`
  
  - Sets `has_acted_this_round = True`
  - Calls `_advance()` to progress the hand
  - Returns table

- `_apply_wager(table: Table, player: Player, amount: int | None, is_raise: bool) -> None`
  - Calculates max reachable: `current_bet + stack`
  - Target bet: `min(amount, max_reachable)` (player goes all-in if target exceeds remaining stack)
  - **Minimum bet validation (raises `ActionError`):**
    - If **not** a raise: min is `min(big_blind, max_reachable)` (player can bet as little as big blind, or all-in with less)
    - If **is** a raise: min is `min(current_bet + min_raise, max_reachable)`
    - If target < min → `ActionError(f"raise below minimum {min_target}")`
  - Increment: `target - current_bet` (amount to add); must be > 0 or `ActionError("wager must increase current bet")`
  - Deducts increment from stack, sets `current_bet = target`, adds to `total_committed`
  - If stack reaches 0, sets status to ALL_IN
  - **Raise logic:**
    - `raise_size = target - table.current_bet`
    - `full_raise = (raise_size >= table.min_raise)`
    - If `raise_size > 0`:
      - If `full_raise` OR (not `is_all_in`): updates `min_raise`, `current_bet`, `last_aggressor`, and resets `has_acted_this_round` for other ACTIVE players
      - Else (short all-in raise): updates `current_bet` only (so later players still owe the all-in amount), does NOT reset others' acted flags or update `min_raise`
    - Else if **not** is_raise (first bet): updates `current_bet`, sets `min_raise = max(big_blind, target)`, sets `last_aggressor`, resets others' acted flags

- `_betting_round_complete(table: Table) -> bool`
  - Returns `True` if **all** conditions hold:
    - Every ACTIVE player has `has_acted_this_round == True`
    - Every ACTIVE player has `current_bet == table.current_bet`
  - Otherwise `False`

- `_advance(table: Table) -> None`
  - Calls `_maybe_end_hand_early()` — if hand ends (≤1 non-folded player), returns
  - If betting round incomplete:
    - Moves to next seat clockwise
    - Finds first ACTIVE player at/after that position
    - If found, sets `current_actor` to that seat; returns
    - Else (no one left to act), calls `_advance_betting_round()`
  - Else (betting round complete), calls `_advance_betting_round()`

- `_advance_betting_round(table: Table) -> None`
  - Resets all players: `current_bet = 0`, `has_acted_this_round = False`
  - Resets table: `current_bet = 0`, `min_raise = big_blind`
  - Transitions betting round: PREFLOP → FLOP → TURN → RIVER → SHOWDOWN
  - If transitioning to FLOP/TURN/RIVER: deals cards (3 for flop, 1 each for turn/river)
  - Sets `betting_round = next_round`
  - Logs `"-- {round_name} --"`
  - **If SHOWDOWN reached:** calls `_finish_hand(awarded_seats=None)` and returns
  - **If fewer than 2 ACTIVE players remain:** sets `current_actor = None`, recursively calls `_advance_betting_round()` to deal out remaining community cards and reach showdown with no further betting
  - **Otherwise:** finds first ACTIVE player clockwise from button, sets `current_actor`

- `_maybe_end_hand_early(table: Table) -> bool`
  - Counts non-folded players
  - If ≤ 1: calls `_finish_hand(awarded_seats=[remaining_seat])` and returns `True`
  - Else returns `False`

- `_finish_hand(table: Table, awarded_seats: list[int] | None = None) -> None`
  - Computes `table.pots = _side_pots(table)` (see next function)
  - Clears `table.last_showdown = []`

  - **If `awarded_seats` is not None (fold-out):**
    - Winner is `awarded_seats[0]` (or `None` if list is empty, though this shouldn't occur)
    - Awards each pot to winner: `table.players[winner].stack += pot.amount`
    - Logs: `"seat {winner} wins {total_pot} (all others folded)"`
  
  - **Else (showdown):**
    - Scores each non-folded player's best hand from hole cards + community cards
    - Appends to `last_showdown`: `{"seat": int, "hole_cards": [card dicts], "hand_category": describe(score)}`
    - For each pot:
      - Filters eligible seats to those in `pot.eligible_seats` that have hole cards (i.e., non-folded)
      - If no eligible: pot is unclaimed (should not happen in normal play)
      - Finds best score among eligible
      - Winners: all eligible seats with that best score
      - Divides pot: `share = pot.amount // len(winners)`, `remainder = pot.amount - share * len(winners)`
      - Awards remainder (odd chip) deterministically: to first winner clockwise from button (approximated by ordering winners by seat index relative to button)
      - Each winner gets `share` (plus odd chip if first winner)
      - Logs: `"pot of {amount} won by seat(s) [list of winners]"`
  
  - Sets `hand_in_progress = False`, `betting_round = SHOWDOWN`, `current_actor = None`

- `_side_pots(table: Table) -> list[Pot]`
  - Computes side pots based on all-in players (algorithm per design-server.md)
  - Collects contributions: `{seat: total_committed}` for each player who wagered
  - If no contributions, returns `[]`
  - Sorts distinct contribution levels
  - For each level (in order):
    - Layer players: those with `total_committed >= level`
    - Layer amount: `(level - previous_level) * len(layer_players)` (chips in this layer)
    - Eligible seats: layer players minus FOLDED players
    - Creates pot if amount > 0
    - Updates previous_level
  - Returns list of pots (in order of contribution levels)

---

### 1.4 main.py — FastAPI REST & WebSocket API

**Responsibility:** Exposes table operations via HTTP and WebSocket. Maintains in-memory table store and broadcast connections.

**Global state:**
- `TABLES: dict[str, Table]` — all tables, keyed by table_id
- `CONNECTIONS: dict[str, dict[WebSocket, int | None]]` — per-table WebSocket connections; value is seat number or `None` for spectators

**Core functions:**

- `_get_table(table_id: str) -> Table` — retrieves table or raises `HTTPException(status_code=404, detail="table not found")`

- `_broadcast(table: Table) -> None` — async; sends current table state to all connected WebSockets for that table
  - Iterates over sockets: sends `table.to_dict(viewer_seat=seat)` to each
  - Removes stale sockets (those that raise exceptions during send)

---

## 2. REST API Surface

All endpoints are synchronous REST (POST/GET) except WebSocket. CORS is enabled (allow all origins/methods/headers).

### 2.1 POST /tables

**Request body (JSON):**
```json
{
  "small_blind": 1,
  "big_blind": 2
}
```
- Both fields optional; defaults shown
- Validation: `small_blind > 0`, `big_blind > 0`, `big_blind >= small_blind`
- If invalid: `HTTPException(status_code=400, detail="invalid blinds")`

**Response (200 OK):**
```json
{
  "table_id": "abcdef123456"
}
```
- Table created in empty state (no players, no hand in progress)

---

### 2.2 POST /tables/{table_id}/players

**Path:** `table_id` (string) — table identifier from /tables response

**Request body (JSON):**
```json
{
  "name": "Alice",
  "buy_in": 1000
}
```
- `name`: string, no max length or validation (e.g., whitespace allowed)
- `buy_in`: integer; must be `> 0` or `HTTPException(status_code=400, detail="buy_in must be positive")`

**Precondition:** No hand in progress on table
- If hand is running: `HTTPException(status_code=409, detail="cannot seat mid-hand")`

**Behavior:**
- Assigns next available seat (0, 1, 2, ...) in order
- Creates player with `status=ACTIVE`, `stack=buy_in`, `hole_cards=None`, all action counters reset

**Response (200 OK):**
```json
{
  "seat": 0
}
```
- Returns assigned seat number

**Error cases:**
- Table not found: `HTTPException(status_code=404, detail="table not found")`

---

### 2.3 POST /tables/{table_id}/start

**Path:** `table_id`

**Request body:** (none)

**Behavior:**
- Calls `start_new_hand(table)` via `game_engine`
- On success: broadcasts updated table state to all WebSocket subscribers; returns state

**Response (200 OK):**
```json
{
  "table_id": "...",
  "small_blind": 1,
  "big_blind": 2,
  "button_seat": 0,
  "community_cards": [],
  "betting_round": "preflop",
  "pots": [],
  "current_bet": 2,
  "min_raise": 2,
  "current_actor": 2,
  "hand_in_progress": true,
  "players": [
    {
      "seat": 0,
      "name": "Alice",
      "stack": 999,
      "status": "active",
      "current_bet": 1,
      "total_committed": 1,
      "hole_cards": null
    },
    ...
  ],
  "last_action_log": ["seat 0 posts blind 1", "seat 1 posts blind 2"],
  "last_showdown": []
}
```

**Error cases:**
- Table not found: `HTTPException(status_code=404, detail="table not found")`
- Hand already in progress: `HTTPException(status_code=409, detail="a hand is already in progress")`
- Fewer than 2 active players: `HTTPException(status_code=409, detail="need at least 2 players with chips to start a hand")`

---

### 2.4 POST /tables/{table_id}/actions

**Path:** `table_id`

**Request body (JSON):**
```json
{
  "seat": 0,
  "action": "fold",
  "amount": null
}
```
or
```json
{
  "seat": 0,
  "action": "call",
  "amount": null
}
```
or
```json
{
  "seat": 0,
  "action": "raise",
  "amount": 100
}
```

- `seat`: int — seat submitting action
- `action`: string — one of `"fold"`, `"check"`, `"call"`, `"bet"`, `"raise"`
- `amount`: int | null — required for `"bet"` and `"raise"`, ignored for others

**Behavior:**
- Calls `submit_action(table, seat, action, amount)`
- On success: broadcasts updated state to WebSocket subscribers; returns viewer-specific state
- On `ActionError`: raises `HTTPException(status_code=409, detail=str(exc))`

**Response (200 OK):**
Same structure as /start, but with `viewer_seat=req.seat` (hole cards visible for the acting player only, unless in showdown)

**Error cases (all return 409):**
- Table not found: `HTTPException(status_code=404, detail="table not found")`
- No hand in progress: `ActionError("no hand in progress")`
- Not your turn: `ActionError("not your turn")`
- Player cannot act: `ActionError("player cannot act")`
- Check facing a bet: `ActionError("cannot check, facing a bet")`
- Nothing to call: `ActionError("nothing to call, use check")`
- Cannot bet when facing bet: `ActionError("cannot bet, must call/raise/fold")`
- Cannot raise when no bet: `ActionError("cannot raise, must bet")`
- Wager below minimum: `ActionError(f"raise below minimum {min}")`
- Wager does not increase bet: `ActionError("wager must increase current bet")`
- Unknown action: `ActionError(f"unknown action: {action}")`

---

### 2.5 GET /tables/{table_id}/state

**Path:** `table_id`

**Query params:**
- `seat` (optional, int | None) — viewer's seat; if provided, only that seat's hole cards are visible (unless in showdown)

**Response (200 OK):**
Same structure as /start response, but with `viewer_seat=seat` parameter applied to hole card visibility

**Error cases:**
- Table not found: `HTTPException(status_code=404, detail="table not found")`

---

### 2.6 WebSocket /tables/{table_id}/ws

**Path:** `table_id`

**Query params:**
- `seat` (optional, int | None) — viewer's seat

**Behavior:**
- Accepts WebSocket connection; immediately sends initial table state
- WebSocket is **push-only from server** (no game commands accepted over it)
- Remains open until client disconnects
- On client disconnect: removes connection from registry
- If table not found: closes connection immediately with code 4404

**Messages sent to client:**
- Initial message: `table.to_dict(viewer_seat=seat)`
- After any action on table (POST /start or POST /actions): updated state is broadcast to all connected sockets on that table
- Each message is a complete table state JSON (same structure as GET /state)

**Note:** Game commands (actions) are submitted via POST /actions, not WebSocket. WebSocket is for live updates only.

---

## 3. Turn Enforcement

### 3.1 Whose Turn Is It?

The server tracks `table.current_actor` (seat number) or `None` if no action needed.

**Turn calculation:**
- At hand start: first to act is next seat clockwise from big blind (heads-up) or big blind (3+ players); specifically, the first ACTIVE player at/after that position
- After each action: turn advances to next seat clockwise among ACTIVE players at/after the current actor
- If no ACTIVE player remains to act (all others are ALL_IN or FOLDED): betting round advances
- When betting round completes (all ACTIVE players matched current bet): transitions to next round, finding first ACTIVE player clockwise from button

### 3.2 Legal Actions — Order of Checks

When `submit_action(table, seat, action, amount)` is called:

1. **Is a hand in progress?**
   - If not: raise `ActionError("no hand in progress")`

2. **Is it this player's turn?**
   - If `table.current_actor != seat`: raise `ActionError("not your turn")`

3. **Can this player act?**
   - If `table.players[seat].status != ACTIVE`: raise `ActionError("player cannot act")`
   - (This covers FOLDED, ALL_IN, SITTING_OUT)

4. **Is the action legal for the current situation?**
   - Calculate `to_call = table.current_bet - player.current_bet`
   - **For `"check"`:** `to_call == 0` required; else raise `ActionError("cannot check, facing a bet")`
   - **For `"call"`:** `to_call > 0` required; else raise `ActionError("nothing to call, use check")`
   - **For `"bet"`:** `table.current_bet == 0` required; else raise `ActionError("cannot bet, must call/raise/fold")`
   - **For `"raise"`:** `table.current_bet > 0` required; else raise `ActionError("cannot raise, must bet")`
   - **For `"fold"`:** always legal (no check)

5. **For bets and raises: is the amount valid?**
   - Calculated via `_apply_wager()` (see below)

### 3.3 Bet/Raise Sizing Rules

Applied in `_apply_wager(table, player, amount, is_raise)`:

- **Max reachable:** `player.current_bet + player.stack` (total player can put in this round)
- **Target:** `min(amount, max_reachable)` (player can request more than they have; they go all-in)

- **Minimum bet** (if `is_raise=False`, i.e., first bet of round):
  - Min is `min(table.big_blind, max_reachable)`
  - Validation: `target >= min` or raise `ActionError(f"bet below minimum {min_target}")`

- **Minimum raise** (if `is_raise=True`):
  - Min is `min(table.current_bet + table.min_raise, max_reachable)`
  - Validation: `target >= min` or raise `ActionError(f"raise below minimum {min_target}")`

- **Increment check:**
  - `increment = target - player.current_bet`
  - Must be `> 0` or raise `ActionError("wager must increase current bet")`

### 3.4 All-In Handling

- A player is all-in when their wager brings `stack` to 0 or raises it above player's remaining stack
- All-in players cannot act further; their status becomes `ALL_IN`
- All-in players' actions **do not** reopen betting unless their raise is a "full raise" (see below)

### 3.5 Short All-In Raise Logic

When a player goes all-in with a raise that is smaller than `table.min_raise` (a "short all-in raise"):
- `table.current_bet` is updated (so later players still owe the all-in amount)
- `table.min_raise` is **not** updated
- Other players' `has_acted_this_round` flags are **not** reset (they have completed their action vs. the prior current_bet)
- If a later player re-raises, **that** becomes a full raise, and normal raise logic applies

Example: player A bets 100 (min_raise now 100), player B raises to 150 (full raise, all-in with 50 left). Later player C now owes 150 to stay in but A's bet of 100 does not reopen action for players who already matched 100.

---

## 4. Betting Rounds & Side-Pot Handling

### 4.1 Betting Round Progression

Sequence: PREFLOP → FLOP → TURN → RIVER → SHOWDOWN

**Round completion:** A betting round ends when:
- Every ACTIVE player has taken an action this round (`has_acted_this_round = True`)
- Every ACTIVE player's `current_bet` equals `table.current_bet`

**All players all-in exception:** If during a round, fewer than 2 players can still act (all others are ALL_IN or FOLDED), the rest of the community cards are dealt automatically (no further betting) and the hand moves straight to showdown.

### 4.2 Card Dealing

- **Preflop:** 0 community cards (start of hand)
- **Flop:** 3 community cards dealt when entering flop betting round
- **Turn:** 1 community card dealt when entering turn betting round
- **River:** 1 community card dealt when entering river betting round
- **Showdown:** no cards dealt; hands are evaluated (5 from community, 2 from hole cards; best 5 selected)

### 4.3 Side-Pot Calculation Algorithm

Computed in `_side_pots(table)` at showdown or fold-out:

1. Build contributions map: `{seat: total_committed}` for each player who wagered > 0
2. Extract sorted list of distinct contribution levels
3. For each level (in ascending order):
   - **Layer players:** seats with `total_committed >= level`
   - **Layer amount:** `(level - previous_level) * count(layer_players)`
   - **Eligible seats:** layer players excluding FOLDED players
   - If layer amount > 0, create pot with amount and eligible seats
   - Update `previous_level = level`
4. Return list of pots (in contribution order)

**Example:**
- Seat 0: total_committed 100 (all-in)
- Seat 1: total_committed 250 (all-in)
- Seat 2: total_committed 500 (betting continues)
- Seats 0 and 1 are ACTIVE; Seat 0 folds

Levels: [100, 250, 500]
- Level 100: layer_players [0,1,2], amount = (100-0)*3 = 300, eligible (non-folded) [1,2] → Pot 1: 300, eligible [1,2]
- Level 250: layer_players [1,2], amount = (250-100)*2 = 300, eligible [1,2] → Pot 2: 300, eligible [1,2]
- Level 500: layer_players [2], amount = (500-250)*1 = 250, eligible [2] → Pot 3: 250, eligible [2]

**Key:** A player who folds is excluded from eligible seats of pots they contributed to. A player who is all-in can only win pots they contributed to.

### 4.4 Odd Chip Distribution

When a pot is split among multiple winners (tie), the remainder (pot % winners) goes to the first winner clockwise from the button.

Implementation: Sorts winners by `(seat_index - button_index) % hand_seats_count`, awards remainder to first in sorted order.

---

## 5. Hand Evaluation

### 5.1 Hand Categories

Poker hands are ranked 0–8 (higher wins):

| Rank | Name | Description | Tiebreak |
|------|------|-------------|----------|
| 0 | High Card | No pairs, no straight/flush | Ranks descending |
| 1 | One Pair | Two cards of same rank | Pair rank, then kickers desc |
| 2 | Two Pair | Two different pairs | High pair, low pair, kicker |
| 3 | Three of a Kind | Three cards of same rank | Trips rank, kickers desc |
| 4 | Straight | Five consecutive ranks | High card (wheel=5) |
| 5 | Flush | Five cards of same suit | Ranks descending |
| 6 | Full House | Three of a kind + pair | Trips rank, pair rank |
| 7 | Four of a Kind | Four cards of same rank | Quads rank, kicker |
| 8 | Straight Flush | Straight + flush | High card (wheel=5) |

### 5.2 Tiebreak Rules (Lexicographic)

Hands are compared as tuples `(category, tiebreak1, tiebreak2, ...)`.

- **Straight and Straight Flush special case:** High card is 5 for wheel (A-2-3-4-5), not 14
  - Wheel detection: if ranks are [14, 5, 4, 3, 2] (when sorted descending and distinct), it's a wheel with high card 5
  - This means a wheel (5-high) loses to a 6-high straight, but beats a high card

- **Full House:** Trips rank is primary (higher trips beats lower); pair rank breaks ties
- **Two Pair:** Higher pair first; lower pair second; kicker last
- **Flush / High Card:** All kickers (ranks) included in descending order; lexicographic comparison decides winner

**Example:** Pair of Kings with Q-J-9 kickers beats pair of Kings with Q-J-8 kickers (tiebreak at third element)

### 5.3 Hand Selection

- `best_hand(hole_cards, community_cards)` evaluates all possible 5-card combinations from the 7 available (hole + community)
- `combinations(all_cards, 5)` generates 21 possible hands
- `max()` compares scores lexicographically; highest tuple wins
- Returns the best score tuple (not the cards themselves)

---

## 6. Hole-Card Privacy

### 6.1 Visibility Rules

Hole cards are visible in `player.public_dict()` output when `reveal_hole_cards=True`.

- **During hand (PREFLOP through RIVER):**
  - A player sees their own hole cards only (if `viewer_seat == player.seat`)
  - All other players' hole cards are `None`
  - Spectators (no seat) see all hole cards as `None`

- **During SHOWDOWN betting round:**
  - All players' hole cards are revealed to all viewers
  - Spectators see all hole cards
  - Once `betting_round == SHOWDOWN`, `reveal_hole_cards=True` for all seats

### 6.2 Implementation

In `Table.to_dict(viewer_seat)`:
```python
showdown = (self.betting_round == BettingRound.SHOWDOWN)
for seat in all_seats:
    player_dict = players[seat].public_dict(
        reveal_hole_cards=(seat == viewer_seat or showdown)
    )
```

- If `viewer_seat` is None, only showdown reveals cards
- If `viewer_seat` matches the player's seat, that player always sees their own cards (before and during showdown)

### 6.3 last_showdown Field

After showdown (hand conclusion), the `last_showdown` field contains:
```json
[
  {
    "seat": 0,
    "hole_cards": [{"rank": 14, "suit": "s"}, {"rank": 13, "suit": "h"}],
    "hand_category": "pair"
  },
  ...
]
```
This is always populated at showdown, regardless of viewer seat (permanent record).

---

## 7. State Serialization (public_dict)

Every table state response is a complete JSON snapshot:

```json
{
  "table_id": "abc123",
  "small_blind": 1,
  "big_blind": 2,
  "button_seat": 0,
  "community_cards": [
    {"rank": 10, "suit": "s"},
    {"rank": 9, "suit": "h"},
    {"rank": 8, "suit": "d"}
  ],
  "betting_round": "flop",
  "pots": [
    {"amount": 500, "eligible_seats": [0, 1]}
  ],
  "current_bet": 50,
  "min_raise": 50,
  "current_actor": 1,
  "hand_in_progress": true,
  "players": [
    {
      "seat": 0,
      "name": "Alice",
      "stack": 900,
      "status": "active",
      "current_bet": 50,
      "total_committed": 150,
      "hole_cards": null
    },
    {
      "seat": 1,
      "name": "Bob",
      "stack": 1100,
      "status": "active",
      "current_bet": 0,
      "total_committed": 100,
      "hole_cards": [
        {"rank": 14, "suit": "s"},
        {"rank": 13, "suit": "h"}
      ]
    }
  ],
  "last_action_log": [
    "seat 0 posts blind 1",
    "seat 1 posts blind 2",
    "seat 0 calls 1",
    "seat 1 checks",
    "-- flop --",
    "seat 1 bets 50",
    "seat 0 raises to 100"
  ],
  "last_showdown": []
}
```

- `last_action_log` is capped at 20 most recent entries
- `last_showdown` is a list populated only after showdown
- `hole_cards` for each player is `None` unless revealed (to that viewer or at showdown)

---

## 8. Error Handling Summary

All game errors (illegal actions) are caught by `game_engine.ActionError` and converted to HTTP 409 by the FastAPI layer:

```python
except ActionError as exc:
    raise HTTPException(status_code=409, detail=str(exc)) from exc
```

**Common 409 error messages:**
- `"no hand in progress"` — no active hand
- `"not your turn"` — wrong seat
- `"player cannot act"` — player is not ACTIVE
- `"cannot check, facing a bet"` — no check option
- `"nothing to call, use check"` — no bet to call
- `"cannot bet, must call/raise/fold"` — facing existing bet
- `"cannot raise, must bet"` — no bet to raise
- `"raise below minimum {amount}"` or `"bet below minimum {amount}"` — insufficient wager
- `"wager must increase current bet"` — wager is not an increase
- `"a hand is already in progress"` — can't start when running
- `"need at least 2 players with chips to start a hand"` — insufficient players
- `"cannot seat mid-hand"` — can't seat during active hand (409 for POST /players)
- `"unknown action: {action}"` — unrecognized action string
- `"amount required"` — bet/raise with no amount

**404 errors:**
- `"table not found"` — table_id does not exist

**400 errors:**
- `"invalid blinds"` — blind configuration invalid (≤0, big < small)
- `"buy_in must be positive"` — buy_in ≤ 0

---

## 9. Critical Implementation Notes

### 9.1 No Persistence

Tables exist only in memory (`TABLES` dict). Server restart loses all tables.

### 9.2 No Authentication

Any client can seat players, join tables, submit actions on any seat. No seat ownership or identity verification.

### 9.3 Deck Sharing

One deck per hand; deck is instantiated at hand start (shuffled fresh) and discarded after showdown.

### 9.4 Button Movement

Button advances after each hand, moving clockwise through active players. On first hand, button is lowest-seated player; thereafter, next active player.

### 9.5 min_raise Tracking

- Initialized to big blind
- Reset to big blind at start of each betting round
- Updated to `max(current_min_raise, raise_size)` when a **full** raise occurs (raise_size >= current_min_raise)
- Not updated for short all-in raises

### 9.6 Heads-Up (2 players)

- Button posts small blind and acts first preflop (unusual in some variants but specified here)
- Button acts last in flop/turn/river

### 9.7 Sequence of Side Pots

Pots are computed at the moment `_finish_hand()` is called (on fold-out or at showdown), based on final `total_committed` values. They are not recomputed during hand; only the final tally matters.

---

## 10. Example: Complete Hand Flow

1. **Create table:** POST /tables → `table_id: "abc123"`
2. **Seat players:** POST /tables/abc123/players (Alice, 1000), (Bob, 1000)
3. **Start hand:** POST /tables/abc123/start
   - Blinds posted (Alice button 1, Bob big 2)
   - Hole cards dealt
   - Alice to act (button, heads-up)
4. **Alice calls:** POST /tables/abc123/actions (seat=0, action="call", amount=None)
   - Alice's stack: 999, current_bet: 1
   - Bob to act
5. **Bob checks:** POST /tables/abc123/actions (seat=1, action="check")
   - Preflop ends
6. **Flop dealt:** 3 community cards
   - Bob to act first (button is Alice; next is Bob)
7. **Bob bets 50:** POST /tables/abc123/actions (seat=1, action="bet", amount=50)
   - Bob's current_bet: 50, Alice owes 50 to stay
8. **Alice raises to 150:** POST /tables/abc123/actions (seat=0, action="raise", amount=150)
   - Alice's current_bet: 150, min_raise updated to 100
   - Bob's `has_acted_this_round` reset
9. **Bob folds:** POST /tables/abc123/actions (seat=1, action="fold")
   - Bob's status: FOLDED
   - Alice wins; hand ends
10. **last_showdown:** empty (fold-out, no showdown)
11. **Stack states:** Alice 1050 (won 50), Bob 950

---

## 11. Data Type Reference

### Card
```python
@dataclass(frozen=True)
class Card:
    rank: int  # 2-14
    suit: str  # "s", "h", "d", "c"
```

### Player
```python
@dataclass
class Player:
    seat: int
    name: str
    stack: int
    hole_cards: list[Card] | None = None
    status: PlayerStatus = PlayerStatus.ACTIVE
    current_bet: int = 0
    total_committed: int = 0
    has_acted_this_round: bool = False
```

### Pot
```python
@dataclass
class Pot:
    amount: int
    eligible_seats: set[int]
```

### Table (key fields)
```python
@dataclass
class Table:
    table_id: str
    small_blind: int
    big_blind: int
    players: dict[int, Player]
    button_seat: int | None
    community_cards: list[Card]
    betting_round: BettingRound | None
    pots: list[Pot]
    current_bet: int
    min_raise: int
    current_actor: int | None
    last_aggressor: int | None
    deck: Deck | None
    hand_in_progress: bool
    last_action_log: list[str]
    last_showdown: list[dict]
```

---

## 12. Testing & Validation

### To build a compatible client:
1. Implement HTTP client for REST endpoints (POST /tables, /players, /start, /actions; GET /state)
2. Subscribe to WebSocket for live state updates
3. Always check current_actor before submitting actions; only that seat can act
4. Validate action legality on client side to prevent failed requests (optional but recommended for UX)
5. Parse hole card visibility based on viewer_seat and betting_round
6. Handle all 404/409/400 errors gracefully

### To build a test suite:
1. Create table via POST /tables
2. Seat players via POST /players (test multi-player scenarios)
3. Verify game state progression (preflop → flop → turn → river → showdown)
4. Verify bet/raise validation (underbet, overbet, all-in edge cases)
5. Verify side-pot calculation (all-in scenarios with multiple players)
6. Verify hand evaluation (all 9 categories, tie-breaks)
7. Verify hole-card privacy (on-demand vs showdown visibility)
8. Test fold-out scenarios (hand ends early)
9. Test blind posting (heads-up vs 3+ players)
10. Test button movement across multiple hands

---

**Document generated:** 2026-07-29  
**Source files analyzed:** models.py, hand_eval.py, game_engine.py, main.py  
**Scope:** Complete technical reference for external system implementation or testing
