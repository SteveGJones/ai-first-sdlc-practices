# Architecture: Texas Hold'em client/server (exemplar)

**Stage:** 1 (Architecture) — poker capstone exemplar, `research/poker-capstone`
**Author:** Claude (Sonnet 5)
**Status:** Reference implementation

## Goal

A client/server No-Limit Texas Hold'em poker game. The server is the sole
authority on game state: it evaluates hands, enforces turn order, and owns
the pot. The client is a thin presentation layer — it renders whatever state
the server publishes and submits player actions; it holds no game logic of
its own and cannot be trusted to enforce rules (an adversarial client could
send any request — the server must reject anything invalid regardless of
what a well-behaved client would never send).

## Components

```
┌─────────────┐        WebSocket (state push)        ┌──────────────┐
│   Client     │ ◄──────────────────────────────────  │              │
│ (static      │                                       │    Server    │
│  HTML/JS,    │        REST (player actions)          │  (FastAPI +  │
│  served by   │ ──────────────────────────────────►  │  in-memory   │
│  nginx)      │                                       │  game state) │
└─────────────┘                                       └──────────────┘
```

- **Server** — single process, in-memory game state (no database; a hand of
  poker is short-lived and this is a reference/test artifact, not a
  production service that needs to survive a restart). Owns:
  - The deck, shuffling, and dealing (server-side RNG only — a client never
    sees another player's hole cards).
  - Turn enforcement (a state machine — see `design-server.md`).
  - Pot/side-pot accounting.
  - Hand evaluation and showdown resolution.
  - Broadcasting state to every connected client after each action.
- **Client** — a static single-page app. Connects to the server's WebSocket
  endpoint to receive state pushes and renders the table, players' visible
  chips/bets, community cards, and the acting player's own hole cards (never
  another player's). Submits actions (`fold`/`check`/`call`/`bet`/`raise`)
  via REST calls to the server; the server is what decides whether an action
  is legal, not the client.

## Why WebSocket + REST, not WebSocket-only or REST-only

- **State push needs to be real-time and multi-recipient** — every seated
  player's client must see the same table state converge immediately after
  any action (whose turn it is, new community cards, pot size). A pure
  polling/REST-only design would mean either high-latency polling or a lot
  of wasted requests. WebSocket is the natural fit for server→client push.
- **Actions are simple, infrequent, request/response operations** — a
  player's bet/fold/call is naturally a single REST call with a clear
  success/failure response (was this action legal right now?), not a
  streaming operation. Mixing action submission into the WebSocket channel
  would complicate request/response semantics (correlating a submitted
  action with its accept/reject) for no real benefit.
- This split is also what makes **stage-4 testing tractable**: a test
  harness can drive the whole game via REST calls alone (never needing to
  parse a client's rendering) and independently assert on the WebSocket
  broadcast stream to check the server published the state it should have.

## Tech stack

- **Server**: Python 3.12, FastAPI (native WebSocket support, async,
  minimal boilerplate for a project this size), `uvicorn` as the ASGI
  server. No database — in-memory `Table`/`Game` objects, one process.
- **Client**: vanilla HTML/CSS/JS, no build step, no framework. A poker
  table UI does not need a component framework to be correct, and keeping
  the client build-free means "does the client's Dockerfile work" tests
  packaging, not a build pipeline.
- **Packaging**: one container per component (server: Python+uvicorn;
  client: nginx serving static files), orchestrated by `docker-compose.yml`.
  The client's nginx container does **not** proxy to the server — the
  client JS talks to the server directly over the browser's own network
  path (server allows CORS from any origin; this is a local test artifact,
  not a deployed service, so no auth/CORS hardening is in scope here).

## Data flow — one player action

1. Player's browser sends `POST /tables/{id}/actions` with `{seat, action,
   amount?}`.
2. Server validates: is it this seat's turn? Is this action legal given the
   current bet/round/player stack? (Full rule set in `design-server.md`.)
3. If legal: server mutates game state (chip movement, pot update, advance
   to next actor or next betting round or showdown), else returns 4xx with
   a reason.
4. Server broadcasts the new state to every connected WebSocket client for
   that table (each player's payload redacts other players' hole cards).
5. Every client re-renders from the pushed state.

## Multi-table / multi-game scope

A single server process can host multiple tables (a `table_id` in every
route), each with independent state. Out of scope for this exemplar:
authentication, persistence across server restarts, spectator mode, chat.
These don't affect what's being measured (architecture/design/build/run
capability) and would only add surface area to the stage-4 harness without
adding signal.

## Turn enforcement — the one thing this architecture exists to get right

Turn enforcement is not a UI convention (a "please don't click out of
turn" affordance) — it's a server-side invariant enforced identically
regardless of what the client does. See `design-server.md` §Turn state
machine for the full state machine; the property this architecture
guarantees is: **the server rejects any action from any seat other than
`table.current_actor`, unconditionally**, including a legal-looking action
type from a player who simply hasn't been dealt the turn yet.
