"""Playwright driver for the client — reads ONLY data-testid/data-*
attributes per docs/CLIENT-TEST-CONTRACT.md, never rendered text or CSS
selectors, so this script stays fixed regardless of how any particular
client actually looks. Mirrors harness/scenarios.py's structure: create
via the fixed REST API, then drive/observe via the fixed client contract.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field

from playwright.sync_api import Browser, Page, sync_playwright


class BrowserScenarioError(Exception):
    """A scenario could not be driven to completion at all (page failed to
    load, a required element never appeared) — distinct from an assertion
    failure recorded in a ScenarioResult."""


@dataclass
class ScenarioResult:
    name: str
    passed: bool
    details: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# REST helpers (table setup only — never used to drive gameplay in this
# module; that's the whole point of testing the CLIENT)
# ---------------------------------------------------------------------------


def _rest(
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


def _rest_ok(base_url: str, method: str, path: str, body: dict | None = None) -> dict:
    status, resp = _rest(base_url, method, path, body)
    if status >= 400:
        raise BrowserScenarioError(
            f"{method} {path} unexpectedly failed ({status}): {resp}"
        )
    return resp


# ---------------------------------------------------------------------------
# Contract-attribute readers
# ---------------------------------------------------------------------------


def read_table_mirror(page: Page) -> dict:
    el = page.locator('[data-testid="table"]')
    hand_in_progress = el.get_attribute("data-hand-in-progress")
    current_actor = el.get_attribute("data-current-actor")
    return {
        "hand_in_progress": hand_in_progress == "true",
        "current_actor": int(current_actor) if current_actor else None,
        "current_bet": int(el.get_attribute("data-current-bet") or 0),
        "button_seat": int(el.get_attribute("data-button-seat") or -1),
    }


def read_seat_mirror(page: Page, seat: int) -> dict:
    el = page.locator(f'[data-testid="seat-{seat}"]')
    if el.count() == 0:
        raise BrowserScenarioError(f"seat-{seat} element not found")
    return {
        "status": el.get_attribute("data-status"),
        "stack": int(el.get_attribute("data-stack") or 0),
        "current_bet": int(el.get_attribute("data-current-bet") or 0),
        "total_committed": int(el.get_attribute("data-total-committed") or 0),
    }


def read_hole_card(page: Page, seat: int, slot: int) -> dict:
    el = page.locator(f'[data-testid="seat-{seat}-hole-card-{slot}"]')
    if el.count() == 0:
        raise BrowserScenarioError(f"seat-{seat}-hole-card-{slot} element not found")
    hidden = el.get_attribute("data-hidden") == "true"
    rank = el.get_attribute("data-rank")
    suit = el.get_attribute("data-suit")
    return {"hidden": hidden, "rank": int(rank) if rank else None, "suit": suit}


def is_action_enabled(page: Page, testid: str) -> bool:
    el = page.locator(f'[data-testid="{testid}"]')
    return el.count() > 0 and el.is_enabled()


def click_action(page: Page, testid: str) -> None:
    page.locator(f'[data-testid="{testid}"]').click()


def fill_bet_amount(page: Page, amount: int) -> None:
    page.locator('[data-testid="bet-amount-input"]').fill(str(amount))


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------


def _setup_heads_up_hand(base_url: str) -> tuple[str, dict]:
    """Create a table, seat 2 players, start a hand — via REST, never the
    client's own lobby UI (see CLIENT-TEST-CONTRACT.md "URL contract")."""
    table_id = _rest_ok(
        base_url, "POST", "/tables", {"small_blind": 1, "big_blind": 2}
    )["table_id"]
    _rest_ok(
        base_url,
        "POST",
        f"/tables/{table_id}/players",
        {"name": "alice", "buy_in": 100},
    )
    _rest_ok(
        base_url, "POST", f"/tables/{table_id}/players", {"name": "bob", "buy_in": 100}
    )
    state = _rest_ok(base_url, "POST", f"/tables/{table_id}/start")
    return table_id, state


def _open_seat_pages(
    browser: Browser, client_url: str, table_id: str, seats: list[int]
) -> dict[int, Page]:
    pages: dict[int, Page] = {}
    for seat in seats:
        context = browser.new_context()
        page = context.new_page()
        page.goto(
            f"{client_url}/?table={table_id}&seat={seat}", wait_until="networkidle"
        )
        # CLIENT-TEST-CONTRACT.md: "the visible page can look like
        # anything" — the mirror element only has to be present in the
        # DOM with correct data-* attributes, not CSS-visible.
        page.wait_for_selector('[data-testid="table"]', state="attached", timeout=10_000)
        pages[seat] = page
    return pages


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------


def scenario_hole_card_privacy(pages: dict[int, Page]) -> ScenarioResult:
    """Each seat's own page must show only that seat's own hole cards
    (data-hidden=false with real rank/suit); every other seat's hole
    cards on that page must be data-hidden=true."""
    mismatches = []
    for viewer_seat, page in pages.items():
        for other_seat in pages:
            for slot in (0, 1):
                card = read_hole_card(page, other_seat, slot)
                should_be_visible = other_seat == viewer_seat
                if card["hidden"] == should_be_visible:
                    mismatches.append(
                        {
                            "viewer_seat": viewer_seat,
                            "card_owner_seat": other_seat,
                            "slot": slot,
                            "expected_hidden": not should_be_visible,
                            "actual": card,
                        }
                    )
                if should_be_visible and (card["rank"] is None or card["suit"] is None):
                    mismatches.append(
                        {
                            "viewer_seat": viewer_seat,
                            "card_owner_seat": other_seat,
                            "slot": slot,
                            "error": "own card visible but rank/suit missing",
                        }
                    )
    return ScenarioResult(
        name="hole_card_privacy",
        passed=not mismatches,
        details={"mismatches": mismatches},
    )


def scenario_turn_gated_controls(pages: dict[int, Page]) -> ScenarioResult:
    """Action controls must be enabled only on the current actor's own
    page, disabled on every other seat's page."""
    any_page = next(iter(pages.values()))
    table = read_table_mirror(any_page)
    current_actor = table["current_actor"]

    mismatches = []
    for seat, page in pages.items():
        should_be_enabled = seat == current_actor
        for testid in ("action-fold", "action-check-call", "action-bet-raise"):
            enabled = is_action_enabled(page, testid)
            if enabled != should_be_enabled:
                mismatches.append(
                    {
                        "seat": seat,
                        "testid": testid,
                        "expected_enabled": should_be_enabled,
                        "actual_enabled": enabled,
                    }
                )
    return ScenarioResult(
        name="turn_gated_controls",
        passed=not mismatches,
        details={"current_actor": current_actor, "mismatches": mismatches},
    )


def scenario_action_propagates(
    pages: dict[int, Page], timeout_s: float = 10.0
) -> ScenarioResult:
    """Clicking an action on the current actor's page must update every
    seat's mirror — not just the actor's own page — within a bounded
    time. This is the one check that exercises real-time sync, not just
    correct initial render."""
    any_page = next(iter(pages.values()))
    before = read_table_mirror(any_page)
    actor_seat = before["current_actor"]
    if actor_seat is None or actor_seat not in pages:
        return ScenarioResult(
            name="action_propagates",
            passed=False,
            details={"error": f"no valid current_actor to act with: {before}"},
        )

    actor_page = pages[actor_seat]
    actor_mirror = read_seat_mirror(actor_page, actor_seat)
    to_call = before["current_bet"] - actor_mirror["current_bet"]
    testid = "action-check-call"  # design-client.md: single control, check when nothing owed, call otherwise
    if not is_action_enabled(actor_page, testid):
        return ScenarioResult(
            name="action_propagates",
            passed=False,
            details={
                "error": f"{testid} not enabled for current actor seat {actor_seat}"
            },
        )
    click_action(actor_page, testid)

    deadline = time.time() + timeout_s
    per_seat_final: dict[int, dict] = {}
    while time.time() < deadline:
        per_seat_final = {seat: read_table_mirror(page) for seat, page in pages.items()}
        if all(m["current_actor"] != actor_seat for m in per_seat_final.values()):
            break
        time.sleep(0.25)

    all_agree = (
        len({json.dumps(m, sort_keys=True) for m in per_seat_final.values()}) == 1
    )
    advanced = all(m["current_actor"] != actor_seat for m in per_seat_final.values())
    return ScenarioResult(
        name="action_propagates",
        passed=all_agree and advanced,
        details={
            "acted_seat": actor_seat,
            "to_call_was": to_call,
            "before": before,
            "after_per_seat": per_seat_final,
            "all_pages_agree": all_agree,
            "turn_advanced_everywhere": advanced,
        },
    )


def run_all(base_url: str, client_url: str) -> dict:
    table_id, _ = _setup_heads_up_hand(base_url)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            pages = _open_seat_pages(browser, client_url, table_id, [0, 1])
            results = [
                scenario_hole_card_privacy(pages),
                scenario_turn_gated_controls(pages),
                scenario_action_propagates(pages),
            ]
        finally:
            browser.close()
    return {
        "passed": all(r.passed for r in results),
        "scenarios": [
            {"name": r.name, "passed": r.passed, "details": r.details} for r in results
        ],
    }
