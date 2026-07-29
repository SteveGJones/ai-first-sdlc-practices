"""API-level tests via FastAPI's TestClient — the REST surface a stage-4
harness (or a model's own client) actually drives. See
docs/design-server.md "API contract"."""

from fastapi.testclient import TestClient

from app.main import CONNECTIONS, TABLES, app


def _reset():
    TABLES.clear()
    CONNECTIONS.clear()


def test_create_table_seat_and_start_hand():
    _reset()
    client = TestClient(app)

    r = client.post("/tables", json={"small_blind": 1, "big_blind": 2})
    assert r.status_code == 200
    table_id = r.json()["table_id"]

    r = client.post(
        f"/tables/{table_id}/players", json={"name": "alice", "buy_in": 100}
    )
    assert r.status_code == 200
    assert r.json()["seat"] == 0

    r = client.post(f"/tables/{table_id}/players", json={"name": "bob", "buy_in": 100})
    assert r.json()["seat"] == 1

    r = client.post(f"/tables/{table_id}/start")
    assert r.status_code == 200
    state = r.json()
    assert state["hand_in_progress"] is True
    assert state["betting_round"] == "preflop"
    assert state["current_actor"] is not None


def test_action_rejected_out_of_turn_returns_409():
    _reset()
    client = TestClient(app)
    table_id = client.post("/tables", json={"small_blind": 1, "big_blind": 2}).json()[
        "table_id"
    ]
    client.post(f"/tables/{table_id}/players", json={"name": "alice", "buy_in": 100})
    client.post(f"/tables/{table_id}/players", json={"name": "bob", "buy_in": 100})
    state = client.post(f"/tables/{table_id}/start").json()
    actor = state["current_actor"]
    wrong_seat = 1 - actor

    r = client.post(
        f"/tables/{table_id}/actions",
        json={"seat": wrong_seat, "action": "call"},
    )
    assert r.status_code == 409
    assert "not your turn" in r.json()["detail"]


def test_full_hand_via_api_to_showdown_or_fold():
    _reset()
    client = TestClient(app)
    table_id = client.post("/tables", json={"small_blind": 1, "big_blind": 2}).json()[
        "table_id"
    ]
    client.post(f"/tables/{table_id}/players", json={"name": "alice", "buy_in": 100})
    client.post(f"/tables/{table_id}/players", json={"name": "bob", "buy_in": 100})
    state = client.post(f"/tables/{table_id}/start").json()

    # Drive to completion with checks/calls only (no raises) — hand ends
    # either at showdown or stays hand_in_progress False once resolved.
    for _ in range(50):
        state = client.get(f"/tables/{table_id}/state").json()
        if not state["hand_in_progress"]:
            break
        actor = state["current_actor"]
        my_bet = next(p["current_bet"] for p in state["players"] if p["seat"] == actor)
        action = "check" if my_bet == state["current_bet"] else "call"
        r = client.post(
            f"/tables/{table_id}/actions", json={"seat": actor, "action": action}
        )
        assert r.status_code == 200, r.json()
        state = r.json()

    final = client.get(f"/tables/{table_id}/state").json()
    assert final["hand_in_progress"] is False
    total_chips = sum(p["stack"] for p in final["players"])
    assert total_chips == 200  # no chips created or destroyed


def test_hole_cards_hidden_from_other_seat():
    _reset()
    client = TestClient(app)
    table_id = client.post("/tables", json={"small_blind": 1, "big_blind": 2}).json()[
        "table_id"
    ]
    client.post(f"/tables/{table_id}/players", json={"name": "alice", "buy_in": 100})
    client.post(f"/tables/{table_id}/players", json={"name": "bob", "buy_in": 100})
    client.post(f"/tables/{table_id}/start")

    state_as_seat0 = client.get(f"/tables/{table_id}/state", params={"seat": 0}).json()
    seat0 = next(p for p in state_as_seat0["players"] if p["seat"] == 0)
    seat1 = next(p for p in state_as_seat0["players"] if p["seat"] == 1)
    assert seat0["hole_cards"] is not None
    assert seat1["hole_cards"] is None
