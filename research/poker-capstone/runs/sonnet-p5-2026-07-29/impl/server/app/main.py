"""REST API surface, per docs/HARNESS-CONTRACT.md."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .game import Table, new_table_id
from .models import ActionError

app = FastAPI(title="poker-capstone server")

TABLES: dict[str, Table] = {}


def _get_table(table_id: str) -> Table:
    table = TABLES.get(table_id)
    if table is None:
        raise HTTPException(status_code=404, detail="no such table")
    return table


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


class CreateTableRequest(BaseModel):
    small_blind: int
    big_blind: int


@app.post("/tables")
def create_table(body: CreateTableRequest):
    table_id = new_table_id()
    TABLES[table_id] = Table(table_id, body.small_blind, body.big_blind)
    return {"table_id": table_id}


class AddPlayerRequest(BaseModel):
    name: str
    buy_in: int


@app.post("/tables/{table_id}/players")
def add_player(table_id: str, body: AddPlayerRequest):
    table = _get_table(table_id)
    seat = table.add_player(body.name, body.buy_in)
    return {"seat": seat}


@app.post("/tables/{table_id}/start")
def start_hand(table_id: str):
    table = _get_table(table_id)
    try:
        table.start_hand()
    except ActionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return JSONResponse(table.get_state(seat=None))


class ActionRequest(BaseModel):
    seat: int
    action: str
    amount: int | None = None


@app.post("/tables/{table_id}/actions")
def submit_action(table_id: str, body: ActionRequest):
    table = _get_table(table_id)
    try:
        table.apply_action(body.seat, body.action, body.amount)
    except ActionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return JSONResponse(table.get_state(seat=None))


@app.get("/tables/{table_id}/state")
def get_state(table_id: str, seat: int = Query(...)):
    table = _get_table(table_id)
    if seat not in table.players:
        raise HTTPException(status_code=404, detail="no such seat")
    return JSONResponse(table.get_state(seat=seat))
