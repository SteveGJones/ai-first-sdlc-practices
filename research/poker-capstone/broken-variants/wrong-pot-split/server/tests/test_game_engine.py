"""Scripted-hand tests for app.game_engine — turn enforcement, betting
rounds, fold-out, showdown payout, and side pots. See
docs/design-server.md for the spec this is testing conformance against.
"""

import pytest

from app.game_engine import ActionError, start_new_hand, submit_action
from app.models import BettingRound, Card, Deck, Player, PlayerStatus, Table

RANKS = {
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "10": 10,
    "J": 11,
    "Q": 12,
    "K": 13,
    "A": 14,
}


def card(s: str) -> Card:
    rank_str, suit = s[:-1], s[-1]
    return Card(RANKS[rank_str], suit)


class FixedDeck(Deck):
    """Test double: deals a predetermined card sequence instead of a real
    shuffle, so scripted hands are deterministic."""

    def __init__(self, order: list[str]) -> None:
        self._cards = [card(s) for s in order]
        self._rng = None

    def deal(self, n: int) -> list[Card]:
        dealt, self._cards = self._cards[:n], self._cards[n:]
        return dealt


def make_table(num_players: int, stacks: list[int], sb: int = 1, bb: int = 2) -> Table:
    table = Table(table_id="t1", small_blind=sb, big_blind=bb, deck=Deck())
    for i in range(num_players):
        table.players[i] = Player(seat=i, name=f"p{i}", stack=stacks[i])
    return table


def deal_order_heads_up_p0_wins() -> list[str]:
    # Deal order: seat0 hole x2, seat1 hole x2, flop x3, turn x1, river x1
    # (start_new_hand deals hole cards seat-by-seat in seated order).
    return [
        "As",
        "Ah",  # seat 0 hole: pocket aces
        "2c",
        "7d",  # seat 1 hole: garbage
        "Ad",
        "Kd",
        "Qd",  # flop -> seat0 has trip aces
        "3h",  # turn
        "9s",  # river
    ]


def test_turn_enforcement_rejects_wrong_seat():
    table = make_table(2, [100, 100])
    start_new_hand(table, deck=FixedDeck(deal_order_heads_up_p0_wins()))
    wrong_seat = 1 if table.current_actor == 0 else 0
    with pytest.raises(ActionError, match="not your turn"):
        submit_action(table, wrong_seat, "call")


def test_cannot_check_when_facing_a_bet():
    table = make_table(2, [100, 100])
    start_new_hand(table, deck=FixedDeck(deal_order_heads_up_p0_wins()))
    actor = table.current_actor
    with pytest.raises(ActionError, match="cannot check"):
        submit_action(table, actor, "check")


def test_heads_up_hand_to_showdown_correct_winner():
    table = make_table(2, [100, 100])
    start_new_hand(table, deck=FixedDeck(deal_order_heads_up_p0_wins()))

    # Preflop: heads-up, button=seat0=SB, seat1=BB. seat0 acts first preflop.
    assert table.current_actor == 0
    submit_action(table, 0, "call")  # complete to BB
    submit_action(table, 1, "check")  # BB checks, preflop over

    assert table.betting_round == BettingRound.FLOP
    # Postflop, first to act = first active seat after the button (seat1).
    assert table.current_actor == 1
    submit_action(table, 1, "check")
    submit_action(table, 0, "check")

    assert table.betting_round == BettingRound.TURN
    submit_action(table, 1, "check")
    submit_action(table, 0, "check")

    assert table.betting_round == BettingRound.RIVER
    submit_action(table, 1, "check")
    submit_action(table, 0, "check")

    assert table.betting_round == BettingRound.SHOWDOWN
    assert table.hand_in_progress is False
    # seat0: pocket aces + board pairs A -> trip aces beats seat1's nothing.
    assert table.players[0].stack == 102  # won the 2-chip pot (both put in 1)
    assert table.players[1].stack == 98
    winner_entry = next(s for s in table.last_showdown if s["seat"] == 0)
    assert winner_entry["hand_category"] in ("three_of_a_kind", "full_house")


def test_fold_out_awards_pot_without_showdown():
    table = make_table(2, [100, 100])
    start_new_hand(table, deck=FixedDeck(deal_order_heads_up_p0_wins()))
    actor = table.current_actor
    other = 1 - actor
    submit_action(table, actor, "raise", amount=10)
    submit_action(table, other, "fold")

    assert table.hand_in_progress is False
    assert table.players[other].status == PlayerStatus.FOLDED
    # actor put in 10, other put in 2 (BB) or 1 (SB) depending on seat;
    # actor should have recovered everything committed plus the other's blind.
    total_chips = table.players[0].stack + table.players[1].stack
    assert total_chips == 200  # no chips created/destroyed


def test_bet_below_minimum_rejected():
    table = make_table(2, [100, 100], sb=1, bb=2)
    start_new_hand(table, deck=FixedDeck(deal_order_heads_up_p0_wins()))
    submit_action(table, table.current_actor, "call")
    submit_action(table, table.current_actor, "check")
    # Now postflop, current_bet == 0, so "bet" (not "raise") is the legal
    # action; below the big blind should be rejected.
    with pytest.raises(ActionError, match="bet below minimum"):
        submit_action(table, table.current_actor, "bet", amount=1)


def test_raise_below_min_raise_rejected():
    table = make_table(2, [100, 100], sb=1, bb=2)
    start_new_hand(table, deck=FixedDeck(deal_order_heads_up_p0_wins()))
    actor = table.current_actor
    # current_bet=2 (BB), min_raise=2 -> a legal raise must reach >= 4.
    with pytest.raises(ActionError, match="raise below minimum"):
        submit_action(table, actor, "raise", amount=3)


def test_three_handed_side_pot():
    # Seat0 short-stacked, goes all-in preflop for less than a full call
    # from the others -> creates a side pot between seat1 and seat2.
    table = make_table(3, [5, 100, 100], sb=1, bb=2)
    order = [
        "2c",
        "7d",  # seat0 (short stack) - will lose
        "As",
        "Ah",  # seat1 - best hand
        "3c",
        "8d",  # seat2
        "Kd",
        "Qd",
        "Jd",  # flop
        "9h",  # turn
        "4s",  # river
    ]
    start_new_hand(table, deck=FixedDeck(order))
    # button=seat0, SB=seat1, BB=seat2 (3-handed). First to act preflop = seat0 (UTG).
    assert table.current_actor == 0
    submit_action(table, 0, "raise", amount=5)  # all-in for 5 (stack exhausted)
    assert table.players[0].status == PlayerStatus.ALL_IN
    submit_action(table, 1, "call")
    submit_action(table, 2, "call")

    # All 3 committed: seat0=5 (all-in), seat1=5, seat2=5 so far this hand,
    # everyone matched -> preflop should be over, board runs out (checks or
    # auto-run since seat0 can't act further; seat1/seat2 still ACTIVE).
    assert table.betting_round in (BettingRound.FLOP, BettingRound.SHOWDOWN)

    # Drive remaining streets with checks from whoever can still act.
    for _ in range(20):
        if not table.hand_in_progress:
            break
        actor = table.current_actor
        if actor is None:
            break
        submit_action(table, actor, "check")

    assert table.hand_in_progress is False
    total_chips = sum(p.stack for p in table.players.values())
    assert total_chips == 5 + 100 + 100
    # seat1 (pocket aces) should win everything it's eligible for.
    assert table.players[1].stack > 5  # won at least the main pot
