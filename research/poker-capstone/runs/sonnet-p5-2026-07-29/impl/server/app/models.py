"""Core data model types, per docs/design-server.md "Data model"."""

from __future__ import annotations

from dataclasses import dataclass, field

SUITS = ["s", "h", "d", "c"]
RANKS = list(range(2, 15))  # 2..14, 14 = Ace

STATUS_ACTIVE = "active"
STATUS_FOLDED = "folded"
STATUS_ALL_IN = "all_in"
STATUS_SITTING_OUT = "sitting_out"

ROUND_PREFLOP = "preflop"
ROUND_FLOP = "flop"
ROUND_TURN = "turn"
ROUND_RIVER = "river"
ROUND_SHOWDOWN = "showdown"

ROUND_ORDER = [ROUND_PREFLOP, ROUND_FLOP, ROUND_TURN, ROUND_RIVER, ROUND_SHOWDOWN]


@dataclass(frozen=True)
class Card:
    rank: int  # 2..14, 14 = Ace
    suit: str  # one of SUITS

    def to_dict(self) -> dict:
        return {"rank": self.rank, "suit": self.suit}


def make_deck() -> list[Card]:
    return [Card(rank=r, suit=s) for s in SUITS for r in RANKS]


@dataclass
class Player:
    seat: int
    name: str
    stack: int
    hole_cards: list[Card] | None = None
    status: str = STATUS_SITTING_OUT
    current_bet: int = 0
    total_committed: int = 0
    has_acted_this_round: bool = False


@dataclass
class ActionError(Exception):
    status_code: int
    message: str

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.message
