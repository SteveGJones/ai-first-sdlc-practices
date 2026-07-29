"""Scripted scenarios driven entirely over the REST API in
exemplar/docs/design-server.md, cross-validated against harness.oracle.
Card-independent by design (the harness cannot force a deal) — outcomes
are validated by re-deriving the expected result from what the server
itself revealed, not by asserting one pre-scripted hand."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field

from . import oracle


class ScenarioError(Exception):
    """A scenario could not even be driven to completion (unexpected 4xx/5xx
    on a request the scenario expected to succeed) — distinct from an
    assertion failure recorded in a ScenarioResult."""


@dataclass
class ScenarioResult:
    name: str
    passed: bool
    details: dict = field(default_factory=dict)


def _request(
    base_url: str, method: str, path: str, body: dict | None = None
) -> tuple[int, dict]:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        base_url + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"} if data else {},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read() or b"{}")


def _post_ok(base_url: str, path: str, body: dict | None = None) -> dict:
    status, resp = _request(base_url, "POST", path, body)
    if status >= 400:
        raise ScenarioError(f"POST {path} unexpectedly failed ({status}): {resp}")
    return resp


def _create_table(base_url: str, small_blind: int, big_blind: int) -> str:
    return _post_ok(
        base_url, "/tables", {"small_blind": small_blind, "big_blind": big_blind}
    )["table_id"]


def _seat(base_url: str, table_id: str, name: str, buy_in: int) -> int:
    return _post_ok(
        base_url, f"/tables/{table_id}/players", {"name": name, "buy_in": buy_in}
    )["seat"]


def _cross_validate_hand(pre_hand_stacks: dict[int, int], final_state: dict) -> dict:
    """Returns {"ok": bool, "detail": ...} comparing the server's actual
    per-seat payout against the oracle's independently-derived expectation."""
    contributions = {p["seat"]: p["total_committed"] for p in final_state["players"]}
    folded_seats = {
        p["seat"] for p in final_state["players"] if p["status"] == "folded"
    }
    total_pot = sum(contributions.values())

    if final_state["last_showdown"]:
        showdown_hands = {}
        community = [(c["rank"], c["suit"]) for c in final_state["community_cards"]]
        for entry in final_state["last_showdown"]:
            hole = [(c["rank"], c["suit"]) for c in entry["hole_cards"]]
            showdown_hands[entry["seat"]] = oracle.best_hand(hole, community)
        hand_seats = sorted(p["seat"] for p in final_state["players"])
        expected = oracle.expected_payouts(
            contributions,
            folded_seats,
            showdown_hands,
            button_seat=final_state["button_seat"],
            hand_seats=hand_seats,
        )
    else:
        non_folded = [
            p["seat"] for p in final_state["players"] if p["status"] != "folded"
        ]
        if len(non_folded) != 1:
            return {
                "ok": False,
                "detail": f"fold-out hand but {len(non_folded)} non-folded seats",
            }
        expected = {non_folded[0]: total_pot}

    actual = {
        p["seat"]: p["stack"] - pre_hand_stacks[p["seat"]] + contributions[p["seat"]]
        for p in final_state["players"]
    }
    # Normalize: a seat absent from `expected` won 0.
    mismatches = {}
    for seat in actual:
        exp = expected.get(seat, 0)
        if actual[seat] != exp:
            mismatches[seat] = {"expected": exp, "actual": actual[seat]}
    return {"ok": not mismatches, "detail": mismatches}


def _drive_hand(
    base_url: str, table_id: str, pre_hand_stacks: dict[int, int], state: dict
) -> dict:
    # pre_hand_stacks MUST be captured before /start was called — /start's
    # own response already reflects blinds posted, and total_committed
    # (used below) also counts blinds, so deriving pre_hand_stacks from the
    # /start response would double-count them.
    for _ in range(500):
        if not state["hand_in_progress"]:
            break
        actor = state["current_actor"]
        me = next(p for p in state["players"] if p["seat"] == actor)
        to_call = state["current_bet"] - me["current_bet"]
        action = "check" if to_call == 0 else "call"
        state = _post_ok(
            base_url, f"/tables/{table_id}/actions", {"seat": actor, "action": action}
        )
    else:
        raise ScenarioError("hand did not complete within 500 actions")
    return _cross_validate_hand(pre_hand_stacks, state)


def scenario_basic_multihand(
    base_url: str, num_players: int = 3, num_hands: int = 5
) -> ScenarioResult:
    table_id = _create_table(base_url, small_blind=1, big_blind=2)
    for i in range(num_players):
        _seat(base_url, table_id, f"p{i}", buy_in=100)

    hand_reports = []
    total_before_all = num_players * 100
    for _ in range(num_hands):
        _, pre_state = _request(base_url, "GET", f"/tables/{table_id}/state")
        pre_hand_stacks = {p["seat"]: p["stack"] for p in pre_state["players"]}
        state = _post_ok(base_url, f"/tables/{table_id}/start")
        hand_reports.append(_drive_hand(base_url, table_id, pre_hand_stacks, state))

    final_status, final_state = _request(base_url, "GET", f"/tables/{table_id}/state")
    total_after_all = sum(p["stack"] for p in final_state["players"])
    chip_conservation_ok = total_after_all == total_before_all
    payouts_ok = all(r["ok"] for r in hand_reports)

    return ScenarioResult(
        name="basic_multihand",
        passed=chip_conservation_ok and payouts_ok,
        details={
            "chip_conservation_ok": chip_conservation_ok,
            "total_before": total_before_all,
            "total_after": total_after_all,
            "hands": hand_reports,
        },
    )


def scenario_turn_enforcement(base_url: str) -> ScenarioResult:
    table_id = _create_table(base_url, small_blind=1, big_blind=2)
    _seat(base_url, table_id, "p0", 100)
    _seat(base_url, table_id, "p1", 100)
    state = _post_ok(base_url, f"/tables/{table_id}/start")
    actor = state["current_actor"]
    wrong_seat = next(p["seat"] for p in state["players"] if p["seat"] != actor)

    status, body = _request(
        base_url,
        "POST",
        f"/tables/{table_id}/actions",
        {"seat": wrong_seat, "action": "call"},
    )
    rejected = status >= 400

    _, state_after = _request(base_url, "GET", f"/tables/{table_id}/state")
    unchanged = state_after["current_actor"] == actor

    return ScenarioResult(
        name="turn_enforcement",
        passed=rejected and unchanged,
        details={"status": status, "body": body, "state_unchanged": unchanged},
    )


def scenario_short_all_in_side_pot(base_url: str) -> ScenarioResult:
    """3-handed, seat0 has a tiny stack -> forced short all-in preflop,
    seat1/seat2 both call more -> guaranteed side pot, entirely via
    controlled actions (card-independent)."""
    table_id = _create_table(base_url, small_blind=1, big_blind=2)
    seats = {}
    for name, stack in [("short", 5), ("p1", 100), ("p2", 100)]:
        seats[name] = _seat(base_url, table_id, name, stack)

    _, pre_state = _request(base_url, "GET", f"/tables/{table_id}/state")
    pre_hand_stacks = {p["seat"]: p["stack"] for p in pre_state["players"]}
    state = _post_ok(base_url, f"/tables/{table_id}/start")

    short_seat = seats["short"]
    first_actor = state["current_actor"]
    state = _post_ok(
        base_url,
        f"/tables/{table_id}/actions",
        {"seat": first_actor, "action": "raise", "amount": 5},
    )
    # After the short stack's all-in, p1/p2 both call to match it — that
    # alone leaves everyone's total_committed EQUAL (no side pot: a side
    # pot needs contributions ABOVE the short stack's all-in total). So on
    # every later street, whichever of p1/p2 acts first with current_bet==0
    # bets again, forcing more chips in between the two players still able
    # to act (short_seat is ALL_IN and skipped) — guaranteeing a genuine
    # side pot regardless of the random cards.
    for _ in range(30):
        if not state["hand_in_progress"]:
            break
        actor = state["current_actor"]
        me = next(p for p in state["players"] if p["seat"] == actor)
        to_call = state["current_bet"] - me["current_bet"]
        if to_call == 0 and actor != short_seat and me["stack"] > 0:
            action, amount = "bet", 10
        else:
            action, amount = ("check" if to_call == 0 else "call"), None
        body = {"seat": actor, "action": action}
        if amount is not None:
            body["amount"] = amount
        state = _post_ok(base_url, f"/tables/{table_id}/actions", body)
    else:
        raise ScenarioError(
            "short_all_in_side_pot hand did not complete within 30 actions"
        )

    side_pot_created = bool(state.get("pots")) and len(state["pots"]) >= 2

    cross = _cross_validate_hand(pre_hand_stacks, state)
    return ScenarioResult(
        name="short_all_in_side_pot",
        passed=cross["ok"] and side_pot_created,
        details={
            "cross_validation": cross,
            "side_pot_created": side_pot_created,
            "pots": state.get("pots"),
        },
    )


def run_all(base_url: str) -> dict:
    results = [
        scenario_turn_enforcement(base_url),
        scenario_basic_multihand(base_url),
        scenario_short_all_in_side_pot(base_url),
    ]
    return {
        "passed": all(r.passed for r in results),
        "scenarios": [
            {"name": r.name, "passed": r.passed, "details": r.details} for r in results
        ],
    }
