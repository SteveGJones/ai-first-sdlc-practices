# Poker Capstone — System Architecture (Stage 1)

## 1. Scope of this document

This is the architecture stage of a four-stage exercise. It covers system
components, how they communicate, why that communication approach was
chosen, the tech stack and rationale, and how turn enforcement is addressed
architecturally (mechanisms, not the full betting-rule state machine — that
is Stage 2 design work). No code is included.

## 2. Goals derived from the brief

- The **server** is the single source of truth: it deals cards, evaluates
  hands, and owns the pot. Clients never determine game outcomes.
- The **client** is a web application: players view the table and submit
  actions (bet/call/raise/fold/check) through a browser.
- The server must **enforce turn order**: an action is only accepted if it
  comes from the player whose turn it currently is. This must hold even
  against a malicious or buggy client — enforcement lives entirely on the
  server, never trusted to the client.

These constraints drive every decision below: authoritative server,
thin/untrusted client, and a communication channel that lets the server
push state changes the instant they happen (since "whose turn is it" is
inherently a live, push-driven fact, not something clients should have to
poll for).

## 3. Component overview

```
                        ┌─────────────────────────────┐
                        │         Game Server          │
                        │                               │
  ┌───────────┐         │  ┌─────────────────────────┐ │
  │  Browser  │  WS/TLS │  │   Connection / Session   │ │
  │  Client A ├─────────┼──┤   Layer (auth, socket    │ │
  │ (React UI)│         │  │   ↔ player identity map) │ │
  └───────────┘         │  └────────────┬────────────┘ │
                        │               │               │
  ┌───────────┐         │  ┌────────────▼────────────┐ │
  │  Browser  │  WS/TLS │  │      Table Manager        │ │
  │  Client B ├─────────┼──┤  (one instance per active │ │
  │ (React UI)│         │  │   table/hand)             │ │
  └───────────┘         │  └────────────┬────────────┘ │
                        │               │               │
        ...             │  ┌────────────▼────────────┐ │
                        │  │   Game Engine (per table) │ │
  ┌───────────┐         │  │  - Deck / RNG             │ │
  │  Browser  │  WS/TLS │  │  - Turn Order State        │ │
  │  Client N ├─────────┼──┤    Machine                 │ │
  │ (React UI)│         │  │  - Betting Round Logic     │ │
  └───────────┘         │  │  - Hand Evaluator (judge)  │ │
                        │  │  - Pot / Side-Pot Manager  │ │
                        │  └────────────┬────────────┘ │
                        │               │               │
                        │  ┌────────────▼────────────┐ │
                        │  │   Persistence / Log       │ │
                        │  │  (hand history, chip      │ │
                        │  │   ledger, reconnection     │ │
                        │  │   state)                   │ │
                        │  └───────────────────────────┘ │
                        └───────────────────────────────┘
```

### 3.1 Web Client (browser application)

- Renders table state: community cards, each player's stack/bet/status,
  pot size, whose turn it is, and a countdown for the acting player.
- Renders the local player's hole cards (sent only to that player — see
  §6.3).
- Offers an action panel (fold / check / call / bet / raise with a sizing
  control) that is **only enabled when the server has told this client it
  is its player's turn**. This is a UX convenience, not a security
  control — see §7.
- Contains **no game logic**: it does not compute legal actions, does not
  validate bet sizes, does not decide who wins a hand, and does not
  advance turn order locally. It is a renderer of server-pushed state plus
  a form that submits intents. This keeps the trust boundary crisp: even a
  fully compromised or hand-modified client cannot act out of turn or
  influence hand outcomes, because it has no authority to begin with.

### 3.2 Game Server

Logically one service, split internally into responsibilities that map
directly onto the brief's three server duties (deal, judge, handle the
pot) plus the connective tissue needed to run a live multiplayer game:

- **Connection/Session Layer** — authenticates each WebSocket connection,
  binds it to a stable player identity, and maps `connection ⇄ player ⇄
  seat` so every inbound message can be attributed to exactly one player.
  Handles reconnect (a dropped socket must not desync the game).
- **Table Manager** — owns the set of active tables, seats players,
  starts/ends hands, and routes each inbound client message to the correct
  table's Game Engine instance. Ensures one player only ever occupies one
  seat at a given table.
- **Game Engine** (one logical instance per table, single-threaded per
  table) — the dealer and judge:
  - Deck/RNG: shuffles and deals using a server-side, non-client-visible
    RNG.
  - **Turn Order State Machine**: the authoritative record of whose turn
    it is, whose turn is next, and which actions are legal for the
    current actor. This is the component directly responsible for turn
    enforcement (detailed in §7).
  - Betting Round Logic: tracks bets/calls/raises per street.
  - Hand Evaluator: judges the winning hand(s) at showdown.
  - Pot/Side-Pot Manager: tracks the pot and any side pots from all-ins,
    and pays out the judged winner(s).
- **Persistence/Log** — durable hand history and a chip ledger (so a
  server restart or crash doesn't erase who owns what), plus enough
  per-table state to let a reconnecting client resync instantly. This can
  start as an embedded store (e.g. SQLite) and does not need to be a
  separate networked service for this exercise's scale.

Running one Game Engine instance per table, each processing its inbound
messages one at a time (no concurrent mutation of a single table's state),
is what makes turn enforcement and pot integrity trivial to reason about —
there is never a race between two "simultaneous" actions on the same hand.

## 4. Communication protocol

### 4.1 Choice: WebSocket as the primary channel, plain HTTPS for the rest

- **WebSocket (`wss://`)** carries everything that happens *during* a hand:
  server → client state broadcasts (deal, bets, turn changes, showdown)
  and client → server action intents (fold/check/call/bet/raise).
- **HTTPS/REST** (or simply static hosting) is used for the parts that
  aren't part of the live game loop: serving the client bundle, initial
  login/identity, and fetching hand-history/lobby data that doesn't need
  push updates.

### 4.2 Why WebSocket for the game loop

- **Server-initiated push is required, not optional.** The defining fact
  a client needs — "it is now your turn" — is generated by the server at
  an unpredictable time (as soon as the previous player acts). Polling
  (repeated HTTP GET) would either add latency (poll interval) or waste
  resources (tight polling), and turn-based games are latency-sensitive
  enough (players expect the UI to update the instant it's their turn)
  that push is the natural fit.
- **Ordered, single, persistent connection.** WebSocket gives an ordered
  byte stream per connection, so "deal community card" then "advance
  turn" then "you may act" naturally arrive in the order the server sent
  them, without needing to build ordering/dedup on top of an
  HTTP-request/response model.
- **Low overhead, bidirectional, low latency** after the initial
  handshake — no repeated HTTP header/TLS-handshake cost per message, and
  no round-trip per action beyond the action itself.
- **Natural session anchor.** A live socket is a convenient place to hang
  "this connection is player X, seated at table Y" — the same object
  the Connection Layer authenticates once at connect time and reuses for
  every message, rather than re-authenticating on every REST call. It
  also gives a clean disconnect signal (socket close) the server can use
  to mark a player as sitting-out or start a disconnect timer.

Alternatives considered and rejected for the live channel:
- **Plain HTTP polling / long-polling** — works, but adds either latency
  or wasted load, and reinvents ordering/session semantics WebSocket gives
  for free. Rejected as strictly worse for a real-time turn-based game.
- **Server-Sent Events (SSE) + HTTP POST for actions** — SSE gives
  server→client push over plain HTTP, which is simpler infra-wise (no
  protocol upgrade) and would work. It was considered a close second, but
  was set aside because it splits one logical duplex conversation into
  two independent channels (a persistent GET stream and separate POSTs),
  which makes it harder to guarantee "the player's action was
  processed as part of the same turn that state update reflects" and
  complicates auth binding across two channels. WebSocket keeps action-in
  and state-out on one ordered, already-authenticated pipe.
- **gRPC/bidirectional streaming** — a reasonable choice for a
  backend-to-backend system, but adds a code-generation/tooling step for
  marginal benefit here, and browser support requires a proxy
  (grpc-web), adding infrastructure complexity the plain-WebSocket
  approach avoids for a browser-first client.

### 4.3 Message shape

Messages are small, typed JSON envelopes in both directions (chosen over a
binary protocol such as Protobuf because payloads are tiny — cards, seat
numbers, chip amounts, short enums — and human-readable messages make this
much easier to inspect/debug/test, which matters more here than the
marginal serialization efficiency gain would):

Client → Server (`ClientMessage`):
```json
{ "type": "ACTION", "actionId": "uuid", "action": "RAISE", "amount": 200 }
```
`actionId` is a client-generated idempotency token so a retried submit
(e.g. after a flaky connection) isn't double-applied.

Server → Client (`ServerEvent`), examples:
```json
{ "type": "TURN_STARTED", "seat": 3, "legalActions": ["FOLD","CALL","RAISE"],
  "minRaise": 40, "toCall": 20, "actByMs": 1690000000000 }
{ "type": "ACTION_APPLIED", "seat": 3, "action": "CALL", "amount": 20, "pot": 140 }
{ "type": "ACTION_REJECTED", "reason": "NOT_YOUR_TURN", "actionId": "uuid" }
{ "type": "STATE_SYNC", "table": { "...full snapshot for reconnect..." } }
```
Every state-changing event carries enough of a version/sequence marker
(e.g. a monotonically increasing `handSeq`/`actionSeq`) that a client can
detect it has fallen behind and request a full `STATE_SYNC` rather than
trying to apply out-of-order deltas — important for the reconnect case
and for keeping the client an intentionally "dumb" renderer.

## 5. Tech stack and rationale

| Layer | Choice | Why |
|---|---|---|
| Server language/runtime | **Node.js + TypeScript** | Single language across client and server reduces context-switching and lets the message-envelope types be shared (a `shared/protocol.ts` package imported by both), which directly reduces the risk of client/server drifting on what a message means. Node's event loop suits many-concurrent-socket, low-CPU-per-message workloads like a card table well. TypeScript gives static typing over the WebSocket message contract, catching a large class of protocol mistakes at compile time rather than at the table. |
| WebSocket library | **`ws`** (server) | Minimal, well-established, unopinionated WebSocket implementation; the application defines its own message envelope on top rather than adopting a heavier framework's own event/room abstraction, keeping the turn-enforcement logic fully visible in application code rather than hidden in library behavior. |
| Client framework | **React + TypeScript** | Table state is naturally a tree of view state (seats, cards, pot, active-seat highlight) that re-renders on each server push — a good fit for a component-driven, state-in/UI-out framework. Shares the TypeScript protocol types with the server. |
| Server-side game state | **In-memory per-table state, single-threaded per table** | The Game Engine per table is the authority; keeping its state in memory (backed by the persistence layer for durability, §3.2) avoids the complexity and latency of round-tripping every action through an external database before responding — a poker action needs to be validated and applied in milliseconds. |
| Durability | **SQLite (or equivalent embedded relational store)** | Sufficient for hand history, chip ledger, and reconnect state at this exercise's scale; avoids standing up a separate database service. The persistence interface is still isolated behind a small module so it could be swapped for Postgres if the system needed to scale beyond a single process later. |
| Transport security | **TLS (`wss://` / `https://`) everywhere** | Player actions and hole cards must not be observable or spoofable in transit. |

Rejected alternatives, briefly: a Python backend (e.g. FastAPI +
`websockets`) was a reasonable alternative and would satisfy every
architectural requirement equally well — it was set aside mainly to get
the shared-type benefit of one language across client and server, which
has an outsized benefit specifically for the "don't let client and server
disagree about the message contract" concern that keeps turn enforcement
correct. A traditional request/response-only web framework (e.g. plain
REST + polling) was rejected per §4.2.

## 6. State ownership and visibility

### 6.1 Server as sole authority

All game state — deck contents, whose turn it is, current bet, pot,
each player's stack and cards — lives only on the server. The client
holds a *read-only projection* of the subset of that state it is allowed
to see, rebuilt from `ServerEvent`s. There is no client-side "commit" of
game state; the client optimistically shows its own request as pending
until the server confirms or rejects it (`ACTION_APPLIED` /
`ACTION_REJECTED`), never applies it unilaterally as fact.

### 6.2 One Game Engine instance owns one table

Because each table's Game Engine processes its inbound action queue
serially, there is a single, unambiguous place where "what is the current
state" is decided — no distributed consensus problem, no two servers
racing to decide who acted first. This scales horizontally by table
(different tables can run on different processes/nodes behind the
Connection Layer) without needing cross-node coordination for a single
hand.

### 6.3 Private information

Hole cards are part of each player's *private* view. The server sends
each connected client a *player-scoped* projection of table state —
`STATE_SYNC` and card-dealt events are computed per-recipient, so a given
socket only ever receives its own hole cards, never another seat's,
until showdown (when contested hands are revealed as part of the judged
result). This is enforced server-side by construction: the server simply
never puts another player's cards into a given client's message, rather
than sending everything and relying on the client to hide it — a client
that can see data it shouldn't display is not a viable trust boundary.

## 7. Turn enforcement at the architectural level

Turn enforcement is treated as a **server-side authorization check that
runs in front of the game engine on every inbound action**, not as a rule
the client is trusted to follow. Three architectural elements combine to
guarantee it:

1. **Identity is bound to the connection, not the message.** The
   Connection Layer establishes `socket ⇄ player ⇄ seat` once at
   connect/auth time. An inbound `ACTION` message is never trusted to say
   "I am seat 3" — the server already knows, from which socket the bytes
   arrived on, which seat is submitting the action. This closes off the
   most obvious spoofing vector (a client claiming to be a different
   seat).

2. **The Turn Order State Machine is the single, serial gate every action
   passes through.** Each table's Game Engine keeps an explicit "acting
   seat" field as part of its authoritative state. When an `ACTION`
   message arrives:
   - It is routed (via the Table Manager) to that table's Game Engine.
   - The engine checks `message.seat(from connection) == engine.actingSeat`
     before doing anything else.
   - If they don't match, the action is rejected outright
     (`ACTION_REJECTED { reason: "NOT_YOUR_TURN" }`) and has **zero effect**
     on game state — no partial application, no state mutation attempted
     first and rolled back second. The check is a precondition, not a
     post-hoc validation.
   - Because a single table's actions are processed one at a time (§6.2),
     there is no window where two actions from different seats could both
     be "in flight" and race to be accepted — the engine finishes
     evaluating action *N* (and updates `actingSeat` to the next player)
     before it looks at action *N+1*, so "is it your turn" is always
     checked against current, not stale, state.

3. **The client is architecturally unable to skip this gate.** Because
   the client holds no independent game state and every action is a
   message that must transit the server (§3.1, §6.1), there is no
   client-side code path that can apply a "raise" locally and just tell
   the server about it after the fact. The server doesn't need to trust
   that a well-behaved client only *sends* actions on its turn (though
   the UI also disables the action panel out-of-turn, as a UX nicety
   described in §3.1) — even if a modified or malicious client sends an
   action at the wrong time, the check in point 2 stops it before it can
   affect the deck, the pot, or any other player's view.

Two additional architectural supports for correct turn order:

- **Turn timeout is server-driven.** `TURN_STARTED` carries `actByMs`; if
  no valid action arrives from the acting seat by that time, the Game
  Engine itself (not the client) advances turn order via a default action
  (typically auto-fold or auto-check if checking is legal). This prevents
  a disconnected or stalling client from being able to freeze the whole
  table indefinitely, and keeps "who is allowed to act now" a fact the
  server alone decides, on its own clock.
- **Reconnection re-derives, never trusts, turn state.** On reconnect the
  server sends a fresh `STATE_SYNC` computed from its own authoritative
  state (§4.3); the client never resumes from locally cached state about
  whose turn it believed it was.

## 8. Summary of key decisions

- **Server-authoritative architecture**: server deals, judges, and holds
  the pot; the browser client is a state renderer plus an intent-submitter
  with no independent game logic — directly satisfying the brief's split
  of responsibilities.
- **WebSocket as the live-game channel**, HTTPS for static/non-live
  concerns, chosen because turn-based push notifications ("it's your
  turn") are a core, latency-sensitive requirement that a persistent,
  ordered, bidirectional connection serves better than polling or a
  split SSE+POST design.
- **Node.js/TypeScript + React**, sharing one protocol-type definition
  across client and server, chosen to minimize the risk of client/server
  drift on the message contract that turn enforcement depends on.
- **One serially-processed Game Engine per table** as the single
  authority for turn order, betting, and pot state, which is what makes
  the turn-enforcement guarantee in §7 possible to state simply and
  implement without races: identity is bound at the connection, turn is
  checked as a precondition on every action, and the client has no path
  around that check.
