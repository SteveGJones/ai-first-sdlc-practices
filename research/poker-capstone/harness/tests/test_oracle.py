"""Golden cases for the harness's independent oracle — deliberately
duplicated from exemplar/server/tests/test_hand_eval.py rather than
shared, since the oracle must stand alone (see oracle.py's module
docstring)."""

from harness.oracle import (
    best_hand,
    describe,
    expected_payouts,
    reconstruct_pots,
    score_five,
)

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


def card(s: str) -> tuple[int, str]:
    rank_str, suit = s[:-1], s[-1]
    return (RANKS[rank_str], suit)


def hand(*cards: str) -> list[tuple[int, str]]:
    return [card(c) for c in cards]


def test_royal_flush() -> None:
    sc = score_five(tuple(hand("As", "Ks", "Qs", "Js", "10s")))
    assert describe(sc) == "straight_flush"
    assert sc == (8, 14)


def test_wheel_straight() -> None:
    sc = score_five(tuple(hand("As", "2h", "3d", "4c", "5s")))
    assert sc == (4, 5)


def test_full_house_beats_flush() -> None:
    fh = score_five(tuple(hand("9s", "9h", "9d", "2c", "2h")))
    fl = score_five(tuple(hand("2s", "5s", "9s", "Js", "Ks")))
    assert fh > fl


def test_best_hand_picks_best_5_of_7() -> None:
    bh = best_hand(hand("As", "Ks"), hand("Qs", "Js", "10s", "2h", "3d"))
    assert describe(bh) == "straight_flush"


def test_reconstruct_pots_no_all_in_is_single_pot() -> None:
    pots = reconstruct_pots({0: 10, 1: 10, 2: 10}, folded_seats=set())
    assert len(pots) == 1
    assert pots[0]["amount"] == 30
    assert pots[0]["eligible_seats"] == {0, 1, 2}


def test_reconstruct_pots_short_all_in_creates_side_pot() -> None:
    # seat0 all-in for 5, seat1 and seat2 both put in 20.
    pots = reconstruct_pots({0: 5, 1: 20, 2: 20}, folded_seats=set())
    assert len(pots) == 2
    main, side = pots
    assert main["amount"] == 15  # 5 * 3 players
    assert main["eligible_seats"] == {0, 1, 2}
    assert side["amount"] == 30  # (20-5) * 2 players
    assert side["eligible_seats"] == {1, 2}


def test_reconstruct_pots_folded_seat_excluded_from_eligibility_not_amount() -> None:
    # seat0 folded after committing 10; seat1/seat2 committed 10 each.
    pots = reconstruct_pots({0: 10, 1: 10, 2: 10}, folded_seats={0})
    assert len(pots) == 1
    assert pots[0]["amount"] == 30  # folded chips stay in the pot
    assert pots[0]["eligible_seats"] == {1, 2}  # but can't win it


def test_expected_payouts_simple_heads_up() -> None:
    payouts = expected_payouts(
        contributions={0: 10, 1: 10},
        folded_seats=set(),
        showdown_hands={0: (8, 14), 1: (1, 9, 13, 5, 2)},  # seat0 straight flush wins
        button_seat=0,
        hand_seats=[0, 1],
    )
    assert payouts == {0: 20}


def test_expected_payouts_side_pot_different_winners() -> None:
    # seat0 all-in for 5 with the best hand overall -> wins main pot only.
    # seat1 wins the side pot between seat1/seat2.
    payouts = expected_payouts(
        contributions={0: 5, 1: 20, 2: 20},
        folded_seats=set(),
        showdown_hands={0: (8, 14), 1: (3, 9, 13, 2), 2: (1, 5, 4, 3, 2)},
        button_seat=0,
        hand_seats=[0, 1, 2],
    )
    assert payouts[0] == 15  # main pot
    assert payouts[1] == 30  # side pot (better hand than seat2)
    assert 2 not in payouts


def test_expected_payouts_split_pot_odd_chip_goes_clockwise_from_button() -> None:
    payouts = expected_payouts(
        contributions={0: 11, 1: 10},
        folded_seats=set(),
        showdown_hands={0: (1, 9, 13, 5, 2), 1: (1, 9, 13, 5, 2)},
        button_seat=0,
        hand_seats=[0, 1],
    )
    # main pot (level 10) = 20, split evenly 10/10; side pot (level 11-10)=1*1=1
    # only seat0 eligible for the side pot (only contributor at that level).
    assert payouts[0] == 11
    assert payouts[1] == 10
