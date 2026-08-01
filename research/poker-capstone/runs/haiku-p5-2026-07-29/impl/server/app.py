"""FastAPI application for Texas Hold'em poker server."""

import uuid
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from game_engine import GameEngine
from models import Table


app = FastAPI()

# Add CORS middleware with permissive settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = GameEngine()


class CreateTableRequest(BaseModel):
    small_blind: int
    big_blind: int


class SeatPlayerRequest(BaseModel):
    name: str
    buy_in: int


class ActionRequest(BaseModel):
    seat: int
    action: str
    amount: Optional[int] = None


@app.get("/healthz")
async def healthz():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/tables")
async def create_table(request: CreateTableRequest):
    """Create a new table."""
    table_id = str(uuid.uuid4())[:8]
    engine.create_table(table_id, request.small_blind, request.big_blind)
    return {"table_id": table_id}


@app.post("/tables/{table_id}/players")
async def seat_player(table_id: str, request: SeatPlayerRequest):
    """Seat a player at the table."""
    table = engine.get_table(table_id)
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")

    try:
        seat = engine.seat_player(table, request.name, request.buy_in)
        return {"seat": seat}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/tables/{table_id}/start")
async def start_hand(table_id: str):
    """Start a new hand at the table."""
    table = engine.get_table(table_id)
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")

    try:
        engine.start_hand(table)
        return table.to_dict(requesting_seat=None)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/tables/{table_id}/actions")
async def submit_action(table_id: str, request: ActionRequest):
    """Submit an action for a player."""
    table = engine.get_table(table_id)
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")

    try:
        # Get current state snapshot before action
        state_before = table.to_dict()

        # Submit the action
        engine.submit_action(table, request.seat, request.action, request.amount)

        # Return updated state
        return table.to_dict(requesting_seat=request.seat)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/tables/{table_id}/state")
async def get_state(table_id: str, seat: int = Query(...)):
    """Get the current state of a table."""
    table = engine.get_table(table_id)
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")

    return table.to_dict(requesting_seat=seat)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
