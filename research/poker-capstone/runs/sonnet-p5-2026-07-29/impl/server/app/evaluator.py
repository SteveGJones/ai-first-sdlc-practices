"""Poker hand evaluation.

Best 5-card hand out of 7 cards (2 hole + 5 community), scored as a
comparable tuple (category, tiebreak...) where higher tuples win, per
docs/design-server.md "Hand evaluation".
"""

from __future__ import annotations

from collections import Counter
from itertools import combinations
from typing import Iterable

from .models import Card

CATEGORY_NAMES = [
    "high_card",
    "one_pair",
    "two_pair",
    "three_of_a_kind",
    "straight",
    "flush",
    "full_house",
    "four_of_a_kind",
    "straight_flush",
]


def _score_5(cards: tuple[Card, ...]) -> tuple[int, tuple[int, ...]]:
    ranks = sorted((c.rank for c in cards), reverse=True)
    suits = [c.suit for c in cards]
    is_flush = len(set(suits)) == 1
    rank_set = set(ranks)

    straight_high = None
    if len(rank_set) == 5:
        if rank_set == {14, 2, 3, 4, 5}:
            straight_high = 5
        else:
            high = max(rank_set)
            low = min(rank_set)
            if high - low == 4:
                straight_high = high

    if is_flush and straight_high:
        return (8, (straight_high,))

    counts = Counter(ranks)
    groups = sorted(counts.items(), key=lambda kv: (-kv[1], -kv[0]))
    counts_list = [c for _, c in groups]

    if counts_list[0] == 4:
        quad_rank = groups[0][0]
        kicker = groups[1][0]
        return (7, (quad_rank, kicker))

    if counts_list[0] == 3 and counts_list[1] == 2:
        return (6, (groups[0][0], groups[1][0]))

    if is_flush:
        return (5, tuple(ranks))

    if straight_high:
        return (4, (straight_high,))

    if counts_list[0] == 3:
        trips = groups[0][0]
        kickers = sorted((r for r, c in groups[1:]), reverse=True)
        return (3, (trips, kickers[0], kickers[1]))

    if counts_list[0] == 2 and counts_list[1] == 2:
        pair_ranks = sorted([groups[0][0], groups[1][0]], reverse=True)
        kicker = groups[2][0]
        return (2, (pair_ranks[0], pair_ranks[1], kicker))

    if counts_list[0] == 2:
        pair = groups[0][0]
        kickers = sorted((r for r, c in groups[1:]), reverse=True)
        return (1, (pair, kickers[0], kickers[1], kickers[2]))

    return (0, tuple(ranks))


def evaluate7(cards: Iterable[Card]) -> tuple[tuple[int, tuple[int, ...]], str]:
    """Return (score_tuple, category_name) for the best 5-of-7 hand."""
    cards = tuple(cards)
    assert len(cards) == 7, f"expected 7 cards, got {len(cards)}"
    best: tuple[int, tuple[int, ...]] | None = None
    for combo in combinations(cards, 5):
        score = _score_5(combo)
        if best is None or score > best:
            best = score
    assert best is not None
    return best, CATEGORY_NAMES[best[0]]
