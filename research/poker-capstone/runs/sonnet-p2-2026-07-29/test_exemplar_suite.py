"""Regression suite for the Texas Hold'em game engine (models/hand_eval/game_engine).

Written from a read of the source only. Focus areas, in order of how much a
bug here would actually cost real money:

  1. Hand evaluation correctness (category ordering, kickers, wheel straights,
     "best 5 of 7/6" selection).
  2. Turn enforcement (only the current actor may act; illegal actions raise
     and leave state untouched).
  3. Betting round progression (blinds, min-raise sizing, action reopening,
     short all-in semantics, auto-runout when everyone is all-in).
  4. Showdown / payout correctness: single pots, multi-way side pots with
     partial eligibility, split-pot remainder assignment, fold-outs, and
     chip conservation (nothing created or destroyed across a hand).

Dealing is randomized by default (`Deck` shuffles on construction), so every
scripted-hand test below drives `start_new_hand`/`submit_action` with a
`ScriptedDeck` test double that deals cards in a caller-chosen fixed order.
"""

from __future__ import annotations

import pytest

from app.models import (
    Card,
    Deck,
    Player,
    PlayerStatus,
    BettingRound,
    Pot,
    Table,
)
from app.hand_eval import (
    score_five,
    best_hand,
    describe,
    HIGH_CARD,
    ONE_PAIR,
    TWO_PAIR,
    TRIPS,
    STRAIGHT,
    FLUSH,
    FULL_HOUSE,
    QUADS,
    STRAIGHT_FLUSH,
    CATEGORY_NAMES,
)
from app.game_engine import (
    start_new_hand,
    submit_action,
    ActionError,
    _side_pots,
    _hand_seats,
)


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

_RANK_LOOKUP = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
    "10": 10, "J": 11, "Q": 12, "K": 13, "A": 14,
}


def C(spec: str) -> Card:
    """Parse a shorthand like 'Kc', '10d', 'Ah' into a Card."""
    rank_str, suit = spec[:-1], spec[-1]
    return Card(_RANK_LOOKUP[rank_str], suit)


def cards(*specs: str) -> list[Card]:
    return [C(s) for s in specs]


class ScriptedDeck(Deck):
    """Deterministic Deck test-double: deals from a fixed, caller-supplied
    list in order, instead of a shuffled 52-card deck. Overrides __init__
    completely so the real Deck's shuffle never runs."""

    def __init__(self, ordered_cards: list[Card]):  # noqa: super not called on purpose
        self._cards = list(ordered_cards)

    def deal(self, n: int) -> list[Card]:
        if n > len(self._cards):
            raise ValueError("deck exhausted")
        dealt, self._cards = self._cards[:n], self._cards[n:]
        return dealt


def make_table(
    num_players: int,
    small_blind: int = 10,
    big_blind: int = 20,
    stacks: dict[int, int] | None = None,
    table_id: str = "t1",
) -> Table:
    stacks = stacks if stacks is not None else {i: 1000 for i in range(num_players)}
    players = {
        i: Player(seat=i, name=f"p{i}", stack=stacks[i]) for i in range(num_players)
    }
    return Table(table_id=table_id, small_blind=small_blind, big_blind=big_blind, players=players)


def total_chips(table: Table) -> int:
    """Sum of stacks + whatever is still committed in front of players +
    whatever is sitting in table.pots. Used to assert chip conservation."""
    return (
        sum(p.stack for p in table.players.values())
        + sum(p.current_bet for p in table.players.values())
        + sum(pot.amount for pot in table.pots)
    )


# ===========================================================================
# 1. Hand evaluation (hand_eval.py)
# ===========================================================================


class TestScoreFive:
    def test_high_card(self):
        score = score_five(cards("2c", "5d", "9h", "Js", "Kc"))
        assert score == (HIGH_CARD, 13, 11, 9, 5, 2)

    def test_one_pair_with_kickers_sorted_desc(self):
        score = score_five(cards("9c", "9d", "Kc", "4h", "2s"))
        assert score == (ONE_PAIR, 9, 13, 4, 2)

    def test_two_pair_kicker_is_the_singleton(self):
        score = score_five(cards("Kc", "Kd", "4h", "4s", "9c"))
        assert score == (TWO_PAIR, 13, 4, 9)

    def test_two_pair_higher_pair_ranked_first_regardless_of_card_order(self):
        # Same cards, shuffled input order -> identical score.
        a = score_five(cards("4h", "Kc", "9c", "4s", "Kd"))
        b = score_five(cards("Kd", "4s", "Kc", "9c", "4h"))
        assert a == b == (TWO_PAIR, 13, 4, 9)

    def test_trips_kickers_sorted_desc(self):
        score = score_five(cards("7c", "7d", "7h", "Kc", "3s"))
        assert score == (TRIPS, 7, 13, 3)

    def test_straight(self):
        score = score_five(cards("6c", "7d", "8h", "9s", "10c"))
        assert score == (STRAIGHT, 10)

    def test_wheel_straight_ace_plays_low(self):
        score = score_five(cards("Ac", "2d", "3h", "4s", "5c"))
        assert score == (STRAIGHT, 5)

    def test_six_high_straight_beats_wheel(self):
        wheel = score_five(cards("Ac", "2d", "3h", "4s", "5c"))
        six_high = score_five(cards("2c", "3d", "4h", "5s", "6c"))
        assert six_high > wheel

    def test_almost_straight_is_not_a_straight(self):
        # Gap at 5: 2,3,4,6,7 -- must not be misdetected as a straight.
        score = score_five(cards("2c", "3d", "4h", "6s", "7c"))
        assert score[0] == HIGH_CARD

    def test_flush(self):
        score = score_five(cards("2c", "5c", "9c", "Jc", "Kc"))
        assert score == (FLUSH, 13, 11, 9, 5, 2)

    def test_full_house_trips_rank_then_pair_rank(self):
        score = score_five(cards("7c", "7d", "7h", "4s", "4c"))
        assert score == (FULL_HOUSE, 7, 4)

    def test_full_house_beats_flush(self):
        fh = score_five(cards("7c", "7d", "7h", "4s", "4c"))
        fl = score_five(cards("2c", "5c", "9c", "Jc", "Kc"))
        assert fh > fl

    def test_quads_with_kicker(self):
        score = score_five(cards("9c", "9d", "9h", "9s", "Kc"))
        assert score == (QUADS, 9, 13)

    def test_straight_flush(self):
        score = score_five(cards("6c", "7c", "8c", "9c", "10c"))
        assert score == (STRAIGHT_FLUSH, 10)

    def test_wheel_straight_flush(self):
        score = score_five(cards("Ac", "2c", "3c", "4c", "5c"))
        assert score == (STRAIGHT_FLUSH, 5)

    def test_low_straight_flush_beats_high_quads(self):
        # Category ordinal must dominate the tiebreak values no matter how
        # low the straight flush is or how high the quads' kicker is.
        low_sf = score_five(cards("Ac", "2c", "3c", "4c", "5c"))
        high_quads = score_five(cards("Ah", "As", "Ad", "Ac", "Kd"))
        assert low_sf > high_quads

    def test_category_ordering_is_monotonic(self):
        ordered = [
            score_five(cards("2c", "5d", "9h", "Js", "Kc")),          # high card
            score_five(cards("9c", "9d", "Kc", "4h", "2s")),          # one pair
            score_five(cards("Kc", "Kd", "4h", "4s", "9c")),          # two pair
            score_five(cards("7c", "7d", "7h", "Kc", "3s")),          # trips
            score_five(cards("6c", "7d", "8h", "9s", "10c")),         # straight
            score_five(cards("2c", "5c", "9c", "Jc", "Kc")),          # flush
            score_five(cards("7c", "7d", "7h", "4s", "4c")),          # full house
            score_five(cards("9c", "9d", "9h", "9s", "Kc")),          # quads
            score_five(cards("6c", "7c", "8c", "9c", "10c")),         # straight flush
        ]
        assert ordered == sorted(ordered)
        assert len(set(s[0] for s in ordered)) == 9  # every category hit once


class TestDescribe:
    @pytest.mark.parametrize("category", list(CATEGORY_NAMES.keys()))
    def test_describe_maps_every_category(self, category):
        assert describe((category,)) == CATEGORY_NAMES[category]


class TestBestHand:
    def test_picks_best_five_of_seven(self):
        # Hole cards make only a pair; the board has an independent straight
        # that must be selected instead.
        hole = cards("2c", "2d")
        board = cards("6h", "7h", "8h", "9s", "10c")
        score = best_hand(hole, board)
        assert score == (STRAIGHT, 10)

    def test_picks_best_two_pair_among_three_pairs(self):
        # 7 cards contain three separate pairs (9s, 5s, 3s); the best hand
        # must use the two highest pairs plus the best remaining kicker,
        # not just "the first two pairs found".
        hole = cards("9c", "9d")
        board = cards("5h", "5d", "3c", "3s", "Kc")
        score = best_hand(hole, board)
        assert score == (TWO_PAIR, 9, 5, 13)

    def test_quads_from_seven_cards_with_best_kicker(self):
        hole = cards("9c", "9d")
        board = cards("9h", "9s", "Kc", "Qd", "2c")
        score = best_hand(hole, board)
        assert score == (QUADS, 9, 13)

    def test_best_five_of_six_flush_cards_drops_lowest(self):
        # 6 clubs available (2 hole + 4 board); the best flush must use the
        # top 5 ranks and drop the lowest, not an arbitrary 5.
        hole = cards("2c", "3c")
        board = cards("5c", "9c", "Kc", "7c", "8h")
        score = best_hand(hole, board)
        assert score == (FLUSH, 13, 9, 7, 5, 3)

    def test_straight_using_both_hole_cards(self):
        hole = cards("6h", "7d")
        board = cards("8c", "9s", "10d", "Kc", "Ac")
        score = best_hand(hole, board)
        assert score == (STRAIGHT, 10)

    def test_raises_with_fewer_than_five_cards(self):
        with pytest.raises(ValueError):
            best_hand(cards("2c", "3d"), cards("4h"))


# ===========================================================================
# 2. Turn enforcement & illegal actions
# ===========================================================================


class TestTurnEnforcement:
    def test_cannot_act_when_no_hand_in_progress(self):
        table = make_table(2)
        with pytest.raises(ActionError, match="no hand in progress"):
            submit_action(table, 0, "check")

    def test_cannot_act_out_of_turn(self):
        table = make_table(3)
        start_new_hand(table, deck=ScriptedDeck(cards(
            "2c", "3c", "4c", "5c", "6c", "7c",
        )))
        actor = table.current_actor
        other = next(s for s in table.players if s != actor)
        stacks_before = {s: p.stack for s, p in table.players.items()}
        with pytest.raises(ActionError, match="not your turn"):
            submit_action(table, other, "check")
        # State must be untouched after a rejected action.
        assert table.current_actor == actor
        assert {s: p.stack for s, p in table.players.items()} == stacks_before

    def test_non_active_player_cannot_act_even_if_targeted_directly(self):
        # Whitebox check of the defensive status guard in submit_action:
        # force current_actor onto a folded seat and confirm it's rejected.
        table = make_table(3)
        start_new_hand(table, deck=ScriptedDeck(cards(
            "2c", "3c", "4c", "5c", "6c", "7c",
        )))
        folded_seat = table.current_actor
        submit_action(table, folded_seat, "fold")
        assert table.players[folded_seat].status == PlayerStatus.FOLDED
        table.current_actor = folded_seat  # force illegal state
        with pytest.raises(ActionError, match="player cannot act"):
            submit_action(table, folded_seat, "check")

    def test_check_rejected_when_facing_a_bet(self):
        table = make_table(3)
        start_new_hand(table, deck=ScriptedDeck(cards(
            "2c", "3c", "4c", "5c", "6c", "7c",
        )))
        # Preflop, current_bet == big_blind, first actor owes a call.
        with pytest.raises(ActionError, match="cannot check, facing a bet"):
            submit_action(table, table.current_actor, "check")

    def test_call_rejected_when_nothing_to_call(self):
        table = make_table(3)
        start_new_hand(table, deck=ScriptedDeck(cards(
            "2c", "3c", "4c", "5c", "6c", "7c",
        )))
        # UTG calls, button calls, BB is left facing to_call == 0.
        submit_action(table, table.current_actor, "call")
        submit_action(table, table.current_actor, "call")
        bb_seat = table.current_actor
        with pytest.raises(ActionError, match="nothing to call, use check"):
            submit_action(table, bb_seat, "call")

    def test_bet_rejected_when_facing_existing_bet(self):
        table = make_table(3)
        start_new_hand(table, deck=ScriptedDeck(cards(
            "2c", "3c", "4c", "5c", "6c", "7c",
        )))
        with pytest.raises(ActionError, match="cannot bet, must call/raise/fold"):
            submit_action(table, table.current_actor, "bet", amount=40)

    def test_raise_rejected_when_no_bet_to_raise(self):
        table = make_table(2)
        start_new_hand(table, deck=ScriptedDeck(cards("2c", "3c", "4c", "5c", "6c", "7c", "8h")))
        # Get to a fresh street where current_bet == 0.
        submit_action(table, table.current_actor, "call")  # SB completes
        submit_action(table, table.current_actor, "check")  # BB checks -> flop
        with pytest.raises(ActionError, match="cannot raise, must bet"):
            submit_action(table, table.current_actor, "raise", amount=40)

    def test_unknown_action_rejected(self):
        table = make_table(2)
        start_new_hand(table, deck=ScriptedDeck(cards("2c", "3c", "4c", "5c")))
        with pytest.raises(ActionError, match="unknown action"):
            submit_action(table, table.current_actor, "all_in_shuffle")

    def test_bet_amount_required(self):
        table = make_table(2)
        start_new_hand(table, deck=ScriptedDeck(cards("2c", "3c", "4c", "5c", "6c", "7c", "8h")))
        submit_action(table, table.current_actor, "call")
        submit_action(table, table.current_actor, "check")
        with pytest.raises(ActionError, match="amount required"):
            submit_action(table, table.current_actor, "bet", amount=None)

    def test_bet_below_minimum_rejected(self):
        table = make_table(2)
        start_new_hand(table, deck=ScriptedDeck(cards("2c", "3c", "4c", "5c", "6c", "7c", "8h")))
        submit_action(table, table.current_actor, "call")
        submit_action(table, table.current_actor, "check")
        with pytest.raises(ActionError, match="bet below minimum"):
            submit_action(table, table.current_actor, "bet", amount=5)  # < big blind (20)

    def test_raise_below_minimum_rejected_when_player_has_enough_stack(self):
        table = make_table(3)
        start_new_hand(table, deck=ScriptedDeck(cards(
            "2c", "3c", "4c", "5c", "6c", "7c",
        )))
        # current_bet=20, min_raise=20 preflop -> raising to 30 is a
        # 10-chip raise, below the 20 minimum, and the player has plenty of
        # stack so this cannot be excused as an all-in.
        with pytest.raises(ActionError, match="raise below minimum"):
            submit_action(table, table.current_actor, "raise", amount=30)

    def test_all_in_for_less_than_big_blind_is_allowed(self):
        table = make_table(2, stacks={0: 15, 1: 1000})
        # Heads-up: seat 0 is button/SB (posts 10, leaving 5), seat 1 is BB.
        start_new_hand(table, deck=ScriptedDeck(cards("2c", "3c", "4c", "5c")))
        actor = table.current_actor
        assert actor == 0
        # Seat 0 has only 5 chips left behind a 10-chip current_bet; going
        # all-in for "20" should be capped and accepted even though it is
        # far below the big blind.
        submit_action(table, actor, "raise", amount=20)
        assert table.players[0].status == PlayerStatus.ALL_IN
        assert table.players[0].stack == 0


# ===========================================================================
# 3. Betting round progression
# ===========================================================================


class TestBettingProgression:
    def test_blinds_posted_and_first_actor_three_handed(self):
        table = make_table(3, small_blind=10, big_blind=20)
        start_new_hand(table, deck=ScriptedDeck(cards(
            "2c", "3c", "4c", "5c", "6c", "7c",
        )))
        assert table.button_seat == 0
        assert table.players[1].current_bet == 10  # SB
        assert table.players[2].current_bet == 20  # BB
        assert table.betting_round == BettingRound.PREFLOP
        assert table.current_bet == 20
        assert table.min_raise == 20
        # 3-handed: first to act is the seat after BB, wrapping to the
        # button (seat 0), since everyone but blinds is "UTG" here.
        assert table.current_actor == 0
        assert table.last_aggressor == 2

    def test_heads_up_button_posts_small_blind_and_acts_first(self):
        table = make_table(2, small_blind=10, big_blind=20)
        start_new_hand(table, deck=ScriptedDeck(cards("2c", "3c", "4c", "5c")))
        assert table.button_seat == 0
        assert table.players[0].current_bet == 10  # button posts SB
        assert table.players[1].current_bet == 20  # BB
        assert table.current_actor == 0  # button/SB acts first heads-up

    def test_big_blind_gets_option_to_act_even_after_calls(self):
        table = make_table(3)
        start_new_hand(table, deck=ScriptedDeck(cards(
            "2c", "3c", "4c", "5c", "6c", "7c", "8h", "9h", "10h",
        )))
        submit_action(table, table.current_actor, "call")  # UTG/button calls
        submit_action(table, table.current_actor, "call")  # SB calls
        bb_seat = table.current_actor
        assert bb_seat == 2
        assert table.betting_round == BettingRound.PREFLOP  # not advanced yet
        submit_action(table, bb_seat, "check")  # BB's option
        assert table.betting_round == BettingRound.FLOP

    def test_full_raise_reopens_action_for_everyone(self):
        table = make_table(3)
        start_new_hand(table, deck=ScriptedDeck(cards(
            "2c", "3c", "4c", "5c", "6c", "7c", "8h", "9h", "10h",
        )))
        button = table.current_actor
        submit_action(table, button, "raise", amount=60)
        sb_seat = table.current_actor
        submit_action(table, sb_seat, "call")
        bb_seat = table.current_actor
        # BB had already "acted" only in the sense of posting a blind; the
        # raise must force them to act again.
        assert table.players[bb_seat].has_acted_this_round is False
        submit_action(table, bb_seat, "call")
        assert table.betting_round == BettingRound.FLOP

    def test_flop_action_starts_left_of_button(self):
        table = make_table(3)
        start_new_hand(table, deck=ScriptedDeck(cards(
            "2c", "3c", "4c", "5c", "6c", "7c", "8h", "9h", "10h",
        )))
        submit_action(table, table.current_actor, "call")   # button calls
        submit_action(table, table.current_actor, "call")   # SB calls
        submit_action(table, table.current_actor, "check")  # BB's option
        # everyone matched preflop -> flop dealt
        assert table.betting_round == BettingRound.FLOP
        assert len(table.community_cards) == 3
        # first actor postflop is the first active seat after the button (0)
        assert table.current_actor == 1

    def test_short_all_in_raise_does_not_reopen_or_bump_min_raise(self):
        # seat0=button (deep stack), seat1=SB (deep), seat2=BB (short: 140).
        table = make_table(3, small_blind=10, big_blind=20, stacks={0: 1000, 1: 1000, 2: 140})
        start_new_hand(table, deck=ScriptedDeck(cards(
            "2c", "3c", "4c", "5c", "6c", "7c",
        )))
        button = table.current_actor
        assert button == 0
        submit_action(table, 0, "raise", amount=100)  # full raise: 20 -> 100
        assert table.current_bet == 100
        assert table.min_raise == 80
        assert table.last_aggressor == 0

        sb_seat = table.current_actor
        assert sb_seat == 1
        submit_action(table, 1, "call")  # seat1 matches 100, has_acted True

        bb_seat = table.current_actor
        assert bb_seat == 2
        # seat2 has 120 behind a 20 current_bet -> max_reachable 140, which
        # is less than a full raise (100 + 80 = 180). Requesting a big
        # amount must be capped to an all-in "short" raise.
        submit_action(table, 2, "raise", amount=10_000)
        assert table.players[2].status == PlayerStatus.ALL_IN
        assert table.players[2].stack == 0
        assert table.players[2].current_bet == 140
        # Short all-in raise bumps current_bet but NOT min_raise, and does
        # not become the new last_aggressor.
        assert table.current_bet == 140
        assert table.min_raise == 80
        assert table.last_aggressor == 0
        # seat1 already matched the old current_bet (100) and had acted;
        # they must still owe the extra 40 to reach 140, so action returns
        # to them (not "reopened" with a fresh full-raise right, but they
        # are not skipped either since their committed amount no longer
        # matches table.current_bet).
        assert table.current_actor == 0  # next active seat after seat2

    def test_all_in_runout_skips_remaining_betting(self):
        table = make_table(2, small_blind=10, big_blind=20)
        start_new_hand(table, deck=ScriptedDeck(cards(
            "2c", "3c", "4c", "5c",             # hole cards
            "6c", "7c", "8c", "9c", "10c",       # flop + turn + river
        )))
        actor = table.current_actor
        submit_action(table, actor, "raise", amount=1000)  # shoves
        other = table.current_actor
        submit_action(table, other, "call")  # also all-in
        # No further betting is possible -- hand should run straight to
        # showdown, dealing flop+turn+river automatically.
        assert table.hand_in_progress is False
        assert table.betting_round == BettingRound.SHOWDOWN
        assert len(table.community_cards) == 5
        assert table.current_actor is None


class TestStartNewHandValidation:
    def test_cannot_start_when_hand_already_in_progress(self):
        table = make_table(2)
        start_new_hand(table, deck=ScriptedDeck(cards("2c", "3c", "4c", "5c")))
        with pytest.raises(ActionError, match="already in progress"):
            start_new_hand(table, deck=ScriptedDeck(cards("6c", "7c", "8c", "9c")))

    def test_cannot_start_with_fewer_than_two_funded_players(self):
        table = make_table(2, stacks={0: 1000, 1: 0})
        with pytest.raises(ActionError, match="at least 2 players"):
            start_new_hand(table, deck=ScriptedDeck(cards("2c", "3c", "4c", "5c")))
        # The broke player should have been marked sitting out as a
        # side effect, even though the hand couldn't start.
        assert table.players[1].status == PlayerStatus.SITTING_OUT

    def test_button_rotates_heads_up_across_hands(self):
        table = make_table(2, stacks={0: 1000, 1: 1000})
        start_new_hand(table, deck=ScriptedDeck(cards("2c", "3c", "4c", "5c")))
        assert table.button_seat == 0
        submit_action(table, table.current_actor, "fold")  # end hand 1 fast
        assert table.hand_in_progress is False

        start_new_hand(table, deck=ScriptedDeck(cards("6c", "7c", "8c", "9c")))
        assert table.button_seat == 1

    def test_button_resets_to_lowest_seat_if_previous_button_sat_out(self):
        table = make_table(3, stacks={0: 1000, 1: 1000, 2: 1000})
        start_new_hand(table, deck=ScriptedDeck(cards(
            "2c", "3c", "4c", "5c", "6c", "7c",
        )))
        assert table.button_seat == 0
        # Bust seat 0 out and end the hand via a fold-out so we can start a
        # fresh hand.
        submit_action(table, table.current_actor, "fold")
        while table.hand_in_progress:
            submit_action(table, table.current_actor, "fold")
        table.players[0].stack = 0
        start_new_hand(table, deck=ScriptedDeck(cards(
            "2c", "3c", "4c", "5c", "6c", "7c",
        )))
        assert table.players[0].status == PlayerStatus.SITTING_OUT
        # seat 0 (previous button) is no longer in the hand -> button
        # resets to the lowest seated seat still playing.
        assert table.button_seat == 1


# ===========================================================================
# 4. Showdown & payout correctness -- the money code
# ===========================================================================


class TestSidePotsPure:
    """Direct unit tests of the pot-splitting algorithm, independent of the
    turn engine, so failures here point straight at _side_pots."""

    def test_single_pot_when_all_contributions_equal(self):
        table = make_table(3)
        for s, amt in ((0, 100), (1, 100), (2, 100)):
            table.players[s].total_committed = amt
        pots = _side_pots(table)
        assert len(pots) == 1
        assert pots[0].amount == 300
        assert pots[0].eligible_seats == {0, 1, 2}

    def test_three_way_all_in_produces_layered_side_pots(self):
        table = make_table(3)
        table.players[0].total_committed = 100
        table.players[1].total_committed = 300
        table.players[2].total_committed = 500
        pots = _side_pots(table)
        assert [p.amount for p in pots] == [300, 400, 200]
        assert pots[0].eligible_seats == {0, 1, 2}
        assert pots[1].eligible_seats == {1, 2}
        assert pots[2].eligible_seats == {2}
        assert sum(p.amount for p in pots) == 900

    def test_folded_player_contributes_dead_money_but_is_not_eligible(self):
        # Player 0 put in 500 then folded; players 1 and 2 are still live.
        table = make_table(3)
        table.players[0].total_committed = 500
        table.players[0].status = PlayerStatus.FOLDED
        table.players[1].total_committed = 500
        table.players[2].total_committed = 200
        pots = _side_pots(table)
        assert [p.amount for p in pots] == [600, 600]
        # First layer: everyone contributed >= 200, but seat 0 is folded.
        assert pots[0].eligible_seats == {1, 2}
        # Second layer: only seats 0 and 1 reached 500, seat 0 is folded.
        assert pots[1].eligible_seats == {1}
        assert sum(p.amount for p in pots) == 1200 == 500 + 500 + 200

    def test_no_pot_when_nobody_has_committed_chips(self):
        table = make_table(2)
        assert _side_pots(table) == []


class TestShowdownPayoutEndToEnd:
    def test_three_way_all_in_with_side_pots_pays_correct_winners(self):
        """seat0 covers everyone (1000) but has the weakest hand; seat1 is
        short-stacked (50) but has the best hand; seat2 is in between (200).

        Expected pots (see TestSidePotsPure for the pure-math version):
          pot A: 150, eligible {0,1,2} -> seat1 (best hand overall) wins.
          pot B: 300, eligible {0,2}   -> seat2 beats seat0, wins.
          pot C: 800, eligible {0}     -> seat0 wins by default (sole
                                           eligible player), despite having
                                           the worst hand at the table.

        Final stacks must be 800 / 150 / 300 and total chips in play must
        be unchanged (1250) -- nothing created or destroyed.
        """
        table = make_table(3, small_blind=10, big_blind=20, stacks={0: 1000, 1: 50, 2: 200})
        deck = ScriptedDeck(cards(
            "3h", "4s",     # seat0 hole -> ends up one pair of 2s
            "Kc", "Kh",     # seat1 hole -> ends up two pair, kings up
            "Qc", "Qs",     # seat2 hole -> ends up two pair, queens up
            "2c", "2d", "7h",  # flop
            "9s",              # turn
            "Jc",              # river
        ))
        start_new_hand(table, deck=deck)
        starting_total = 1000 + 50 + 200

        assert table.current_actor == 0
        submit_action(table, 0, "raise", amount=1000)  # seat0 shoves
        assert table.current_actor == 1
        submit_action(table, 1, "call")  # seat1 all-in for 50
        assert table.current_actor == 2
        submit_action(table, 2, "call")  # seat2 all-in for 200

        assert table.hand_in_progress is False
        assert table.betting_round == BettingRound.SHOWDOWN
        assert table.community_cards == cards("2c", "2d", "7h", "9s", "Jc")

        assert table.players[0].stack == 800
        assert table.players[1].stack == 150
        assert table.players[2].stack == 300
        assert sum(p.stack for p in table.players.values()) == starting_total == 1250

        categories = {row["seat"]: row["hand_category"] for row in table.last_showdown}
        assert categories[0] == "one_pair"
        assert categories[1] == "two_pair"
        assert categories[2] == "two_pair"

    def test_split_pot_with_odd_chip_goes_to_first_winner_clockwise_from_button(self):
        """seat1 and seat2 end the hand with an exact tie (both play ace-
        queen-high one pair of kings off a paired board); seat0 has a
        strictly worse hand and contributes to the pot without winning any
        of it. Pot is 303 (odd), so the 1-chip remainder must go to
        whichever tied winner sits first clockwise from the button (seat0),
        i.e. seat1.
        """
        table = make_table(
            3, small_blind=50, big_blind=101, stacks={0: 1000, 1: 1000, 2: 1000}
        )
        deck = ScriptedDeck(cards(
            "6c", "5s",     # seat0 hole -> weaker one pair (kings, 7-6-5)
            "Ah", "Qh",     # seat1 hole -> one pair kings, A-Q-7 kicker
            "As", "Qs",     # seat2 hole -> identical rank tie with seat1
            "Kc", "Kd", "7h",  # flop: pairs the board with kings
            "3s",              # turn
            "2c",              # river
        ))
        start_new_hand(table, deck=deck)
        assert table.button_seat == 0

        # Preflop: button calls, SB calls, BB checks.
        submit_action(table, 0, "call")
        submit_action(table, 1, "call")
        submit_action(table, 2, "check")
        assert table.betting_round == BettingRound.FLOP

        # Flop/turn/river: everyone checks it down.
        for _ in range(3):
            for _ in range(3):
                submit_action(table, table.current_actor, "check")

        assert table.hand_in_progress is False
        assert table.betting_round == BettingRound.SHOWDOWN
        assert table.community_cards == cards("Kc", "Kd", "7h", "3s", "2c")

        assert table.players[0].stack == 899   # contributed 101, won nothing
        assert table.players[1].stack == 1051  # 899 + 151 share + 1 remainder
        assert table.players[2].stack == 1050  # 899 + 151 share
        assert sum(p.stack for p in table.players.values()) == 3000

    def test_fold_out_awards_entire_pot_to_sole_remaining_player(self):
        table = make_table(3, small_blind=10, big_blind=20)
        start_new_hand(table, deck=ScriptedDeck(cards(
            "2c", "3c", "4c", "5c", "6c", "7c",
        )))
        button = table.current_actor
        submit_action(table, button, "raise", amount=60)
        sb_seat = table.current_actor
        submit_action(table, sb_seat, "fold")
        bb_seat = table.current_actor

        assert table.hand_in_progress is True  # still 2 live players
        submit_action(table, bb_seat, "fold")

        assert table.hand_in_progress is False
        assert table.betting_round == BettingRound.SHOWDOWN
        assert table.current_actor is None
        assert table.last_showdown == []  # no showdown reveal on a fold-out

        winner = button
        # winner collects blinds + the raise + BB's call, everyone else's
        # stacks reflect only what they put in before folding.
        total_after = sum(p.stack for p in table.players.values())
        assert total_after == 3000  # 3 x 1000, chip-conserving

    def test_fold_out_before_any_postflop_action_never_deals_community_cards(self):
        table = make_table(2, small_blind=10, big_blind=20)
        start_new_hand(table, deck=ScriptedDeck(cards("2c", "3c", "4c", "5c")))
        submit_action(table, table.current_actor, "fold")
        assert table.community_cards == []
        assert table.hand_in_progress is False

    def test_heads_up_fold_out_winner_gets_both_blinds(self):
        table = make_table(2, small_blind=10, big_blind=20, stacks={0: 500, 1: 500})
        start_new_hand(table, deck=ScriptedDeck(cards("2c", "3c", "4c", "5c")))
        # seat0 is button/SB and acts first heads-up.
        assert table.current_actor == 0
        submit_action(table, 0, "fold")
        assert table.players[1].stack == 510  # 500 - 20(BB) + 30 (both blinds)
        assert table.players[0].stack == 490  # 500 - 10(SB)
        assert sum(p.stack for p in table.players.values()) == 1000

    def test_deeper_stack_reclaims_uncontested_side_pot_layer(self):
        # seat0 (button/SB, 1000 stack) shoves and is called by seat1 (BB,
        # only 300 deep). seat0's hand also happens to be the best, so this
        # checks two things at once: the "uncalled" excess above seat1's
        # all-in amount must return to seat0 as an uncontested side-pot
        # layer, AND seat0 must also win the contested layer below it.
        table = make_table(2, small_blind=10, big_blind=20, stacks={0: 1000, 1: 300})
        deck = ScriptedDeck(cards(
            "Ac", "Ad",   # seat0: pocket aces
            "2c", "7d",   # seat1: garbage
            "Ah", "5s", "9c",  # flop: trips aces for seat0
            "2d",
            "3h",
        ))
        start_new_hand(table, deck=deck)
        submit_action(table, table.current_actor, "raise", amount=1000)  # seat0 all-in for 1000
        submit_action(table, table.current_actor, "call")  # seat1 all-in for 300 (capped)

        pots = _side_pots(table)
        assert [p.amount for p in pots] == [600, 700]
        assert pots[0].eligible_seats == {0, 1}
        assert pots[1].eligible_seats == {0}  # only seat0 reached this layer

        # seat0 wins the contested 600 pot (better hand) AND reclaims the
        # uncontested 700 layer -> everything.
        assert table.players[0].stack == 1300
        assert table.players[1].stack == 0
        assert sum(p.stack for p in table.players.values()) == 1300


# ===========================================================================
# 5. Basic model behaviour sanity checks
# ===========================================================================


class TestModels:
    def test_player_reset_for_new_hand_clears_transient_state(self):
        p = Player(seat=0, name="a", stack=100, hole_cards=cards("2c", "3d"),
                   current_bet=50, total_committed=50, has_acted_this_round=True)
        p.reset_for_new_hand()
        assert p.hole_cards is None
        assert p.current_bet == 0
        assert p.total_committed == 0
        assert p.has_acted_this_round is False
        assert p.status == PlayerStatus.ACTIVE

    def test_reset_for_new_hand_preserves_sitting_out(self):
        p = Player(seat=0, name="a", stack=100, status=PlayerStatus.SITTING_OUT)
        p.reset_for_new_hand()
        assert p.status == PlayerStatus.SITTING_OUT

    def test_active_seats_excludes_folded_and_sitting_out(self):
        table = make_table(3)
        table.players[1].status = PlayerStatus.FOLDED
        table.players[2].status = PlayerStatus.SITTING_OUT
        assert table.active_seats() == [0]

    def test_non_folded_seats_includes_all_in(self):
        table = make_table(3)
        table.players[1].status = PlayerStatus.ALL_IN
        table.players[2].status = PlayerStatus.FOLDED
        assert table.non_folded_seats() == [0, 1]

    def test_non_folded_seats_also_includes_sitting_out_players(self):
        # Pinning test for a real sharp edge: non_folded_seats() only
        # excludes FOLDED, so a SITTING_OUT player at the table (who never
        # gets dealt into the hand) still counts toward
        # _maybe_end_hand_early's "how many are still contesting" check.
        # If this behaviour ever changes, fold-out detection at a table
        # with sitting-out players changes with it -- worth pinning down
        # explicitly rather than discovering it via a flaky end-to-end test.
        table = make_table(3)
        table.players[2].status = PlayerStatus.SITTING_OUT
        assert table.non_folded_seats() == [0, 1, 2]

    def test_deck_deal_raises_when_exhausted(self):
        deck = ScriptedDeck(cards("2c", "3c"))
        with pytest.raises(ValueError, match="deck exhausted"):
            deck.deal(3)

    def test_hand_seats_excludes_sitting_out_but_keeps_folded(self):
        table = make_table(3)
        table.players[1].status = PlayerStatus.SITTING_OUT
        table.players[2].status = PlayerStatus.FOLDED
        assert _hand_seats(table) == [0, 2]
