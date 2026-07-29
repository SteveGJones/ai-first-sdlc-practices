"""FastAPI app implementing the REST + WebSocket API contract in
docs/design-server.md "API contract". In-memory table store — no
database, no auth, no persistence across restarts (out of scope per
docs/architecture.md "Multi-table / multi-game scope")."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .game_engine import ActionError, start_new_hand, submit_action
from .models import Deck, Player, Table

app = FastAPI(title="poker-capstone-exemplar")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

TABLES: dict[str, Table] = {}
CONNECTIONS: dict[str, list[WebSocket]] = {}


def _get_table(table_id: str) -> Table:
    table = TABLES.get(table_id)
    if table is None:
        raise HTTPException(status_code=404, detail="table not found")
    return table


async def _broadcast(table: Table) -> None:
    sockets = CONNECTIONS.get(table.table_id, [])
    stale: list[WebSocket] = []
    for ws in sockets:
        seat = getattr(ws, "_poker_seat", None)
        try:
            await ws.send_json(table.to_dict(viewer_seat=seat))
        except Exception:
            stale.append(ws)
    for ws in stale:
        sockets.remove(ws)


class CreateTableRequest(BaseModel):
    small_blind: int = 1
    big_blind: int = 2


class SeatPlayerRequest(BaseModel):
    name: str
    buy_in: int


class ActionRequest(BaseModel):
    seat: int
    action: str
    amount: int | None = None


@app.post("/tables")
def create_table(req: CreateTableRequest) -> dict[str, str]:
    if req.small_blind <= 0 or req.big_blind <= 0 or req.big_blind < req.small_blind:
        raise HTTPException(status_code=400, detail="invalid blinds")
    table_id = uuid.uuid4().hex[:12]
    TABLES[table_id] = Table(
        table_id=table_id,
        small_blind=req.small_blind,
        big_blind=req.big_blind,
        deck=Deck(),
    )
    CONNECTIONS[table_id] = []
    return {"table_id": table_id}


@app.post("/tables/{table_id}/players")
def seat_player(table_id: str, req: SeatPlayerRequest) -> dict[str, int]:
    table = _get_table(table_id)
    if req.buy_in <= 0:
        raise HTTPException(status_code=400, detail="buy_in must be positive")
    if table.hand_in_progress:
        raise HTTPException(status_code=409, detail="cannot seat mid-hand")
    seat = 0
    while seat in table.players:
        seat += 1
    table.players[seat] = Player(seat=seat, name=req.name, stack=req.buy_in)
    return {"seat": seat}


@app.post("/tables/{table_id}/start")
async def start_hand(table_id: str) -> dict[str, Any]:
    table = _get_table(table_id)
    try:
        start_new_hand(table)
    except ActionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    await _broadcast(table)
    return table.to_dict(viewer_seat=None)


@app.post("/tables/{table_id}/actions")
async def post_action(table_id: str, req: ActionRequest) -> dict[str, Any]:
    table = _get_table(table_id)
    try:
        submit_action(table, req.seat, req.action, req.amount)
    except ActionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    await _broadcast(table)
    return table.to_dict(viewer_seat=req.seat)


@app.get("/tables/{table_id}/state")
def get_state(table_id: str, seat: int | None = None) -> dict[str, Any]:
    table = _get_table(table_id)
    return table.to_dict(viewer_seat=seat)


@app.websocket("/tables/{table_id}/ws")
async def table_ws(
    websocket: WebSocket, table_id: str, seat: int | None = None
) -> None:
    table = TABLES.get(table_id)
    if table is None:
        await websocket.close(code=4404)
        return
    await websocket.accept()
    websocket._poker_seat = seat  # type: ignore[attr-defined]
    CONNECTIONS.setdefault(table_id, []).append(websocket)
    try:
        await websocket.send_json(table.to_dict(viewer_seat=seat))
        while True:
            # This socket is push-only from the server's side; the client
            # never sends game commands over it (those go through REST —
            # see docs/architecture.md "Why WebSocket + REST"). We still
            # need to await something to detect disconnects.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        conns = CONNECTIONS.get(table_id, [])
        if websocket in conns:
            conns.remove(websocket)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
