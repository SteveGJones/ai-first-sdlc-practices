# Texas Hold'em Poker System — Stage 1 Architecture

## Executive Summary

This document describes the architecture for a client/server Texas Hold'em poker game. The system decomposes into a stateful server (REST API, game engine) and a thin client (web UI) that mirrors the server's state. The server is the single source of truth for all game logic; the client is a read-only view (except for action submission) that enforces hole-card privacy through query parameters.

## System Decomposition

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      CLIENT LAYER                       │
├─────────────────────────────────────────────────────────┤
│  • React/Preact UI                                      │
│  • REST HTTP client (polling or Fetch API)              │
│  • State synchronization & hole-card privacy            │
│  • Action button rendering & submission                 │
│  • Deep-linking support (?table=X&seat=Y)              │
└───────────────┬───────────────────────────────────────┘
                │ REST API (fixed interface)
                │ • POST /tables, /players, /start, /actions
                │ • GET /tables/{id}/state?seat={seat}
                │ • CORS enabled
                │
┌───────────────▼───────────────────────────────────────┐
│                    SERVER LAYER                        │
├─────────────────────────────────────────────────────────┤
│  HTTP/REST Framework (FastAPI or Starlette)            │
│  ├─ CORS middleware (permissive)                       │
│  ├─ Route handlers (5 endpoints)                       │
│  └─ Hole-card filtering by seat parameter              │
│                                                         │
│  Game Engine (core logic)                              │
│  ├─ Table state & player management                    │
│  ├─ Betting round state machine                        │
│  ├─ Turn enforcement (who can act)                     │
│  ├─ Action validation & execution                      │
│  ├─ Pot & side-pot calculation                         │
│  ├─ Hand evaluation & showdown logic                   │
│  └─ Last action logging                                │
└─────────────────────────────────────────────────────────┘
```

### Server Components (Detailed)

#### 1. HTTP/REST API Handler
- **Language**: Python (FastAPI recommended for type safety + automatic CORS)
- **Responsibilities**:
  - Accept HTTP requests for all 5 fixed endpoints
  - Delegate game logic to the game engine
  - Filter hole cards in responses based on `seat` query parameter
  - Return 200 with new state on success
  - Return 4xx with error detail on illegal action (action not executed, state unchanged)
  - Send CORS headers on all responses

#### 2. Table Manager
- **Responsibilities**:
  - Maintain list of active tables (in-memory map keyed by `table_id`)
  - Track small blind, big blind per table
  - Manage player seats (0-indexed, up to 10 seats typical)
  - Allocate seat numbers in `POST /players`
  - Serialize/deserialize table state to JSON response shape

#### 3. Betting Round State Machine
- **Responsibilities**:
  - Determine current betting round: preflop, flop, turn, river, or showdown
  - Track `current_actor` (which seat acts next)
  - Determine legal actions for the current actor (fold, check, call, bet, raise)
  - Validate bet amounts (respects `min_raise` and current bet)
  - Transition rounds when:
    - All non-folded players have matched the current bet and no one is all-in, OR
    - All active players except one have folded, OR
    - All active players are all-in
  - Track `current_bet` (highest bet in this round) and `min_raise` (minimum legal raise increment)

#### 4. Pot & Side-Pot Calculator
- **Responsibilities**:
  - Maintain single pot when all players have equal stacks
  - Calculate side pots when players are all-in with unequal amounts
  - Track eligible seats for each pot (only seats that contributed to that pot level)
  - Update pots after each action and round transition
  - Seed pots from blind posting and antes

#### 5. Hand Evaluator
- **Responsibilities**:
  - Rank individual 5-card poker hands (pair, two pair, trips, straight, flush, full house, quads, straight flush)
  - Compare hands to determine winner at showdown
  - Handle split pots (identical best hands)
  - Evaluate from 7 cards (2 hole + 5 community) when community cards available

#### 6. Game State Container
- **Responsibilities**:
  - Serialize the complete game state to the fixed JSON response shape
  - Normalize hole cards based on viewing seat (null for non-visible cards)
  - Maintain action log (last N actions, at least the most recent 1)
  - Track which seats reached showdown
  - Track player stacks, committed amounts (reset per round / per hand)

### Client Components (Detailed)

#### 1. UI Framework
- **Language**: HTML/CSS/JavaScript (React/Preact optional for state management)
- **Responsibilities**:
  - Render table visual (seats, community cards, pots, action buttons)
  - Display each player's stack, current-round bet, total-hand commitment
  - Show hole cards (visible for own seat, redacted for others until showdown)
  - Render action buttons with `disabled` state reflecting current actor
  - Render action log

#### 2. REST Client
- **Responsibilities**:
  - Fetch initial state via `GET /state?seat={seat}` on page load
  - Poll state periodically (or use Fetch + wait pattern)
  - Submit actions via `POST /actions` with seat and action data
  - Handle 4xx errors (show validation error to player, do not update state)
  - Track table_id and seat from URL params or app state

#### 3. State Mirror
- **Responsibilities**:
  - Maintain `data-testid` attributes that exactly mirror JSON state
  - Update DOM attributes on every state fetch
  - Separate concerns: DOM rendering is free-form, but `data-*` attributes are normative
  - This allows the test harness to verify state via CSS selectors without parsing text

#### 4. Deep-Link Handler
- **Responsibilities**:
  - Parse URL query params `?table={table_id}&seat={seat}`
  - Use parsed values to fetch initial state
  - Allow direct bookmarking of a player's table view

## Technology Stack

### Server
- **Runtime**: Python 3.10+ (or higher)
- **Web Framework**: FastAPI (provides CORS middleware, automatic OpenAPI docs, type validation)
  - *Alternative*: Starlette + manual route handlers (more minimal)
- **Game Logic**: Pure Python (no external game library; hand evaluation and pot math implemented from scratch)
- **State Storage**: In-memory (dictionaries/objects), no persistent database required
- **Concurrency**: Async/await for HTTP handlers; use asyncio locks or thread-safe structures if multiple requests arrive for the same table simultaneously

### Client
- **Runtime**: Browser (Chrome, Firefox, Safari, Edge)
- **Framework**: Vanilla JavaScript + HTML/CSS (or React/Preact for state management)
  - *No external game library needed; game state is read from server*
- **HTTP Client**: Fetch API (built-in, no external dependency)
- **State Sync**: Polling (simple, works without WebSocket) or Fetch + await pattern

### Deployment
- **Containerization**: Docker
- **Orchestration**: Docker Compose (optional client service)
- **Health Check**: `GET /healthz` → 200 (any body)

## Wire Protocol & Communication

### Protocol Choice: REST (Fixed) + Optional WebSocket (Internal)

**Fixed Interface (HARNESS-CONTRACT.md):**
- All responses must be deliverable via HTTP REST
- Five endpoints required (create table, add player, start hand, submit action, get state)
- Hole-card privacy enforced via `seat` query parameter on `GET /state`
- CORS required for browser-based client

**Optional Enhancement (Internal Design):**
- Could add WebSocket layer for real-time updates to reduce client polling
- WebSocket not required by harness, but reduces latency if implemented
- If used, WebSocket messages must remain compatible with the same state JSON shape
- Server could push state updates to all connected clients when game progresses

### State Consistency Model

- **Server is authoritative**: all game logic runs on server
- **Client is view-only**: reads state, submits actions, receives new state
- **Idempotency**: submitting the same action twice is rejected as illegal (state has changed)
- **Optimistic updates not used**: client waits for server response before updating UI

### Hole-Card Privacy Enforcement

```
GET /state?seat=0 (player at seat 0 requests state)
  → hole_cards visible for seat 0 only
  → hole_cards null for all other seats (unless showdown)

GET /state?seat=1 (player at seat 1 requests state)
  → hole_cards visible for seat 1 only
  → hole_cards null for all other seats (unless showdown)

GET /state?seat=spectator (if allowed, no seats)
  → hole_cards null for all seats
```

## State Ownership & Authority

### Authoritative State: Server

- **Table state**: blinds, button seat, current betting round
- **Player state**: seat, stack, status (active/folded/all_in/sitting_out), current-round bet, total-hand commitment, hole cards
- **Community cards**: dealt order (flop 0-2, turn 3, river 4)
- **Pots**: amounts and eligible seats
- **Current actor**: who must act next
- **Last action log**: sequence of actions taken this hand

### Client Responsibilities (Read & Render)

- Fetch state from server regularly
- Mirror state in DOM attributes for test harness
- Render UI based on fetched state
- Submit actions when player clicks button
- Never assume next state; always fetch to confirm

### Action Processing

1. **Client**: player clicks action button → `POST /actions {seat, action, amount?}`
2. **Server**: validate action legality (turn, legal action, bet amount)
   - If illegal: return 4xx, do not change state
   - If legal: execute action, compute new state, return 200 + new state
3. **Client**: fetch new state, update UI

## Key Architectural Risks & Mitigations

### Risk 1: Turn Enforcement

**Problem**: Multiple clients could submit actions simultaneously, or a player could submit an action after they should no longer be able to.

**Approach**:
- Server maintains strict turn tracking: `current_actor` is a single seat number
- Every action validates `seat == current_actor` before executing
- After an action, immediately advance `current_actor` to the next player
- Use atomic state updates (e.g., Python dict operations with a lock if using threads, or rely on asyncio single-threading)

**Evidence**: Response shape includes `current_actor`, which the harness will verify changes after each action

### Risk 2: Concurrent Requests to the Same Table

**Problem**: Two players might submit actions concurrently for the same table.

**Approach**:
- Simplest: use a single asyncio event loop in Python (default for FastAPI), processing one request at a time sequentially
- Alternatively: use a table-level lock (mutex) in the game engine; acquire before modifying state, release after response generated
- Validation happens inside the locked section; state remains consistent

### Risk 3: Hole-Card Privacy Leakage

**Problem**: Accidentally include hole cards in response for a seat that shouldn't see them.

**Approach**:
- Centralize hole-card filtering in one function: `filter_hole_cards(state, viewing_seat)`
- Apply this filter to all player objects in the response
- Only set `hole_cards` to a value (not null) if:
  - `seat == viewing_seat` (viewing own cards), OR
  - `betting_round == "showdown"` (all cards visible at showdown)
- Default to null for all other cases

### Risk 4: Betting Round Transitions (Complex Logic)

**Problem**: Determining when to end a betting round and move to the next is intricate, especially with all-in scenarios.

**Approach**:
- After each action, check: "Is the betting round over?"
  - All non-folded players have matched the current bet? (no all-ins: yes) → advance round
  - Only one player left (others folded)? → end hand, move to showdown
  - All remaining active players are all-in? → skip to showdown/end
- Separate the round-advancement logic into a dedicated function, tested exhaustively
- Track per-player: have they acted in this round? Have they matched the current bet?

### Risk 5: Side-Pot Calculation with All-In Players

**Problem**: Complex arithmetic when players have different stack sizes and some go all-in.

**Approach**:
- Use a structured algorithm:
  1. Sort all-in amounts (e.g., [10, 50, 100, 500])
  2. For each threshold: create a pot up to that level for players who went all-in there
  3. Remaining players compete for higher pots
- Example: player A bets 10, B bets 50, C bets 100, D bets 100
  - Pot 1: 40 (10 × 4 players)
  - Pot 2: 160 (40 × 4 players)
  - Pot 3: 200 (50 × 2 players, C & D only)
- Test this algorithm against known scenarios (2-way all-in, 3+ way all-in, side pots with different amounts)

### Risk 6: Hand Evaluation Edge Cases

**Problem**: Correctly ranking poker hands, especially with multiple cards to evaluate (7 available, need best 5).

**Approach**:
- Implement from scratch (standard 5-card ranking: high card, pair, two pair, trips, straight, flush, full house, quads, straight flush)
- Generate all 5-card combinations from 7 cards, rank each, return the best
- Handle Ace as both high (14) and low (1) for straights (A-2-3-4-5 wheel, and 10-J-Q-K-A)
- Unit test against known hands and tie-breaking scenarios

## Out of Scope

### 1. Persistent Storage
- Tables and hands exist only in memory for the duration of the server process
- No database persistence required (simplifies architecture for this exercise)
- All state lost on server restart

### 2. Authentication / Authorization
- No player login or identity verification
- Anyone can seat themselves with a name and buy-in amount
- Assumes honest players (no cryptographic verification of actions)

### 3. Advanced Poker Rules Variants
- No mixed games, no pot-limit Omaha, no other variants
- Texas Hold'em only: 2 hole cards + 5 community cards
- Standard hand rankings

### 4. UI Sophistication
- No animated card dealing, realistic poker table graphics, or sound
- Text/simple HTML layout sufficient; test harness only cares about `data-*` attributes
- No mobile responsiveness required (test harness uses desktop browser)

### 5. Replay / History
- No hand history stored or retrievable
- No replaying past hands
- Last action log available only during the current hand

### 6. Multiple Tables / Lobby UI
- Server can host many tables, but no lobby UI for browsing them
- Deep-linking by table_id is the primary discovery mechanism
- No player registry or account system

## Design Decision Rationale

**Why Server is Authoritative:**
- Simplest to enforce turn order and action legality
- No risk of client sending conflicting states
- Easier to reason about consistency

**Why REST (Not WebSocket-Only):**
- Contract is fixed; must use REST
- REST is stateless, easier to scale horizontally if needed later
- Simpler for client (standard HTTP, no WebSocket fallbacks)

**Why No Persistent Database:**
- Exercise is about game logic, not persistence
- In-memory state is fast and sufficient for grading scenarios
- Reduces operational complexity

**Why Minimal Client Framework:**
- Game state is entirely server-driven
- Client is thin — no complex client-side state machine needed
- Vanilla JS sufficient; React adds no value here

## Summary: Key Architectural Invariants

1. **Server validates every action** before executing
2. **Hole cards are never leaked** except to the viewing seat or at showdown
3. **Current actor is tracked precisely** and enforced
4. **Pots and side pots are calculated correctly** and auditable from the state response
5. **Betting round transitions are deterministic** and match poker rules
6. **Hand evaluation is correct** for all edge cases (ties, all-ins, incomplete communities)
7. **State shape is fixed** (HARNESS-CONTRACT.md) and served by all endpoints
8. **CORS is enabled** for browser client compatibility
