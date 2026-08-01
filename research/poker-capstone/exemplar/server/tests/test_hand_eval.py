"""Golden cases for app.hand_eval, covering all 9 categories plus the
wheel (A-2-3-4-5) straight/straight-flush edge case."""

from app.hand_eval import best_hand, describe, score_five
from app.models import Card

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


def hand(*cards: str) -> list[Card]:
    return [card(c) for c in cards]


def test_royal_flush() -> None:
    sc = score_five(tuple(hand("As", "Ks", "Qs", "Js", "10s")))
    assert describe(sc) == "straight_flush"
    assert sc == (8, 14)


def test_wheel_straight_flush() -> None:
    sc = score_five(tuple(hand("As", "2s", "3s", "4s", "5s")))
    assert sc == (8, 5)


def test_four_of_a_kind() -> None:
    sc = score_five(tuple(hand("9s", "9h", "9d", "9c", "2h")))
    assert sc == (7, 9, 2)


def test_full_house() -> None:
    sc = score_five(tuple(hand("9s", "9h", "9d", "2c", "2h")))
    assert sc == (6, 9, 2)


def test_flush() -> None:
    sc = score_five(tuple(hand("2s", "5s", "9s", "Js", "Ks")))
    assert sc[0] == 5
    assert sc == (5, 13, 11, 9, 5, 2)


def test_wheel_straight_not_flush() -> None:
    sc = score_five(tuple(hand("As", "2h", "3d", "4c", "5s")))
    assert sc == (4, 5)


def test_normal_straight() -> None:
    sc = score_five(tuple(hand("9s", "10h", "Jd", "Qc", "Ks")))
    assert sc == (4, 13)


def test_three_of_a_kind() -> None:
    sc = score_five(tuple(hand("9s", "9h", "9d", "Kc", "2s")))
    assert sc == (3, 9, 13, 2)


def test_two_pair() -> None:
    sc = score_five(tuple(hand("9s", "9h", "2d", "2c", "Ks")))
    assert sc == (2, 9, 2, 13)


def test_one_pair() -> None:
    sc = score_five(tuple(hand("9s", "9h", "2d", "5c", "Ks")))
    assert sc == (1, 9, 13, 5, 2)


def test_high_card() -> None:
    sc = score_five(tuple(hand("2s", "5h", "9d", "Jc", "Ks")))
    assert sc == (0, 13, 11, 9, 5, 2)


def test_best_hand_picks_best_5_of_7() -> None:
    bh = best_hand(hand("As", "Ks"), hand("Qs", "Js", "10s", "2h", "3d"))
    assert describe(bh) == "straight_flush"
    assert bh == (8, 14)


def test_full_house_beats_flush() -> None:
    fh = score_five(tuple(hand("9s", "9h", "9d", "2c", "2h")))
    fl = score_five(tuple(hand("2s", "5s", "9s", "Js", "Ks")))
    assert fh > fl


def test_two_full_houses_compare_by_trips_then_pair() -> None:
    higher = score_five(tuple(hand("Ks", "Kh", "Kd", "2c", "2h")))
    lower = score_five(tuple(hand("Qs", "Qh", "Qd", "As", "Ah")))
    assert higher > lower
