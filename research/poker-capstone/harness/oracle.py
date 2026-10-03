"""Independent hand-evaluation + pot-reconstruction oracle for the stage-4
harness. Deliberately has ZERO dependency on any implementation under
test (including the exemplar) — this is the harness's own trusted judge,
not a reuse of code that might itself be the thing under test. See
exemplar/docs/design-server.md "What the stage-4 harness will check" for
why cross-validation against an oracle, rather than one scripted outcome,
is the design.

Cards are represented as plain (rank: int, suit: str) tuples here — no
shared dataclass with any implementation under test, on purpose.
"""

from __future__ import annotations

from collections import Counter
from itertools import combinations

(
    HIGH_CARD,
    ONE_PAIR,
    TWO_PAIR,
    TRIPS,
    STRAIGHT,
    FLUSH,
    FULL_HOUSE,
    QUADS,
    STRAIGHT_FLUSH,
) = range(9)

CATEGORY_NAMES = {
    HIGH_CARD: "high_card",
    ONE_PAIR: "one_pair",
    TWO_PAIR: "two_pair",
    TRIPS: "three_of_a_kind",
    STRAIGHT: "straight",
    FLUSH: "flush",
    FULL_HOUSE: "full_house",
    QUADS: "four_of_a_kind",
    STRAIGHT_FLUSH: "straight_flush",
}

Card = tuple[int, str]  # (rank 2..14, suit)


def _straight_high(ranks_desc: list[int]) -> int | None:
    if ranks_desc == [14, 5, 4, 3, 2]:
        return 5
    if all(ranks_desc[i] - ranks_desc[i + 1] == 1 for i in range(4)):
        return ranks_desc[0]
    return None


def score_five(cards: tuple[Card, Card, Card, Card, Card]) -> tuple:
    ranks = sorted((r for r, _ in cards), reverse=True)
    suits = [s for _, s in cards]
    is_flush = len(set(suits)) == 1
    distinct_ranks = sorted(set(ranks), reverse=True)
    straight_high = _straight_high(distinct_ranks) if len(distinct_ranks) == 5 else None

    if is_flush and straight_high is not None:
        return (STRAIGHT_FLUSH, straight_high)

    counts = Counter(ranks)
    groups = sorted(counts.items(), key=lambda kv: (-kv[1], -kv[0]))
    group_counts = [c for _, c in groups]

    if group_counts == [4, 1]:
        return (QUADS, groups[0][0], groups[1][0])
    if group_counts == [3, 2]:
        return (FULL_HOUSE, groups[0][0], groups[1][0])
    if is_flush:
        return (FLUSH, *ranks)
    if straight_high is not None:
        return (STRAIGHT, straight_high)
    if group_counts == [3, 1, 1]:
        kickers = sorted((r for r, c in groups[1:]), reverse=True)
        return (TRIPS, groups[0][0], *kickers)
    if group_counts == [2, 2, 1]:
        pair_ranks = sorted((r for r, c in groups if c == 2), reverse=True)
        kicker = next(r for r, c in groups if c == 1)
        return (TWO_PAIR, pair_ranks[0], pair_ranks[1], kicker)
    if group_counts == [2, 1, 1, 1]:
        kickers = sorted((r for r, c in groups[1:]), reverse=True)
        return (ONE_PAIR, groups[0][0], *kickers)
    return (HIGH_CARD, *ranks)


def best_hand(hole_cards: list[Card], community_cards: list[Card]) -> tuple:
    all_cards = list(hole_cards) + list(community_cards)
    if len(all_cards) < 5:
        raise ValueError("need at least 5 cards to score a hand")
    return max(score_five(combo) for combo in combinations(all_cards, 5))


def describe(score: tuple) -> str:
    return CATEGORY_NAMES[score[0]]


def reconstruct_pots(
    contributions: dict[int, int], folded_seats: set[int]
) -> list[dict]:
    """Independent side-pot reconstruction from raw per-seat contribution
    totals — mirrors the algorithm in design-server.md "Side-pot allocation
    algorithm" but is a from-scratch reimplementation, not a call into any
    implementation under test. Returns [{"amount": int, "eligible_seats":
    set[int]}, ...]."""
    contributions = {s: c for s, c in contributions.items() if c > 0}
    if not contributions:
        return []
    levels = sorted(set(contributions.values()))
    pots: list[dict] = []
    previous_level = 0
    for level in levels:
        layer_players = [s for s, c in contributions.items() if c >= level]
        layer_amount = (level - previous_level) * len(layer_players)
        if layer_amount > 0:
            eligible = {s for s in layer_players if s not in folded_seats}
            pots.append({"amount": layer_amount, "eligible_seats": eligible})
        previous_level = level
    return pots


def expected_payouts(
    contributions: dict[int, int],
    folded_seats: set[int],
    showdown_hands: dict[int, tuple],  # seat -> best_hand score (already computed)
    button_seat: int,
    hand_seats: list[int],  # seated order, used for the odd-chip tie-break below
) -> dict[int, int]:
    """Given contributions, who folded, and each non-folded seat's best-hand
    score, return the expected {seat: chips_won} the server's payout should
    match exactly (a hand that ended by fold-out has exactly one entry in
    showdown_hands by convention — see scenarios.py).

    Odd-chip tie-break on a split pot matches design-server.md exactly
    (first winning seat clockwise from the button) — this must agree with
    the spec's documented convention, or the harness would fail a correct
    implementation on a legitimate tie-break choice rather than a real bug.
    """
    pots = reconstruct_pots(contributions, folded_seats)
    payouts: dict[int, int] = {}
    for pot in pots:
        eligible = [s for s in pot["eligible_seats"] if s in showdown_hands]
        if not eligible:
            continue
        best = max(showdown_hands[s] for s in eligible)
        winners = [s for s in eligible if showdown_hands[s] == best]
        share = pot["amount"] // len(winners)
        remainder = pot["amount"] - share * len(winners)
        ordered_winners = sorted(
            winners,
            key=lambda s: (hand_seats.index(s) - hand_seats.index(button_seat))
            % len(hand_seats),
        )
        for i, w in enumerate(ordered_winners):
            payouts[w] = payouts.get(w, 0) + share + (remainder if i == 0 else 0)
    return payouts
