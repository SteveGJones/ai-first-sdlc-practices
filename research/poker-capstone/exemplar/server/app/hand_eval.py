"""Best 5-of-7 Texas Hold'em hand evaluation. See docs/design-server.md
"Hand evaluation" for the category table and tie-break rules this
implements.
"""

from __future__ import annotations

from collections import Counter
from itertools import combinations

from .models import Card

# Category indices, low to high — the score tuple's first element.
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


def _straight_high(ranks_desc: list[int]) -> int | None:
    """ranks_desc: 5 distinct ranks, descending. Returns the straight's high
    card rank if these 5 form a straight (wheel A-2-3-4-5 counts, high=5),
    else None."""
    if ranks_desc == [14, 5, 4, 3, 2]:
        return 5
    if all(ranks_desc[i] - ranks_desc[i + 1] == 1 for i in range(4)):
        return ranks_desc[0]
    return None


def score_five(cards: tuple[Card, Card, Card, Card, Card]) -> tuple:
    """Score exactly 5 cards. Returns (category, *tiebreak) — higher tuple wins."""
    ranks = sorted((c.rank for c in cards), reverse=True)
    suits = [c.suit for c in cards]
    is_flush = len(set(suits)) == 1
    distinct_ranks = sorted(set(ranks), reverse=True)
    straight_high = _straight_high(distinct_ranks) if len(distinct_ranks) == 5 else None

    if is_flush and straight_high is not None:
        return (STRAIGHT_FLUSH, straight_high)

    counts = Counter(ranks)
    # groups: list of (count, rank) sorted by count desc, then rank desc
    groups = sorted(counts.items(), key=lambda kv: (-kv[1], -kv[0]))
    group_counts = [c for _, c in groups]

    if group_counts == [4, 1]:
        quad_rank = groups[0][0]
        kicker = groups[1][0]
        return (QUADS, quad_rank, kicker)

    if group_counts == [3, 2]:
        return (FULL_HOUSE, groups[0][0], groups[1][0])

    if is_flush:
        return (FLUSH, *ranks)

    if straight_high is not None:
        return (STRAIGHT, straight_high)

    if group_counts == [3, 1, 1]:
        trips_rank = groups[0][0]
        kickers = sorted((r for r, c in groups[1:]), reverse=True)
        return (TRIPS, trips_rank, *kickers)

    if group_counts == [2, 2, 1]:
        pair_ranks = sorted((r for r, c in groups if c == 2), reverse=True)
        kicker = next(r for r, c in groups if c == 1)
        return (TWO_PAIR, pair_ranks[0], pair_ranks[1], kicker)

    if group_counts == [2, 1, 1, 1]:
        pair_rank = groups[0][0]
        kickers = sorted((r for r, c in groups[1:]), reverse=True)
        return (ONE_PAIR, pair_rank, *kickers)

    return (HIGH_CARD, *ranks)


def best_hand(hole_cards: list[Card], community_cards: list[Card]) -> tuple:
    """Best 5-card score from hole + community (2 + 5 = 7 for a full board,
    fewer community cards supported for completeness though a real hand
    always reaches showdown with all 5)."""
    all_cards = list(hole_cards) + list(community_cards)
    if len(all_cards) < 5:
        raise ValueError("need at least 5 cards to score a hand")
    return max(score_five(combo) for combo in combinations(all_cards, 5))


def describe(score: tuple) -> str:
    return CATEGORY_NAMES[score[0]]
