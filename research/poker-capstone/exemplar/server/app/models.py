"""Data model — Card, Deck, Player, Pot, Table. See docs/design-server.md."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum

RANK_NAMES = {
    2: "2",
    3: "3",
    4: "4",
    5: "5",
    6: "6",
    7: "7",
    8: "8",
    9: "9",
    10: "10",
    11: "J",
    12: "Q",
    13: "K",
    14: "A",
}
SUITS = ("s", "h", "d", "c")  # spades, hearts, diamonds, clubs


@dataclass(frozen=True)
class Card:
    rank: int  # 2..14, 14 = Ace
    suit: str  # one of SUITS

    def __str__(self) -> str:
        return f"{RANK_NAMES[self.rank]}{self.suit}"

    def to_dict(self) -> dict:
        return {"rank": self.rank, "suit": self.suit}


def full_deck() -> list[Card]:
    return [Card(rank, suit) for rank in range(2, 15) for suit in SUITS]


class Deck:
    """Server-side only. Never expose card order/remaining cards to clients."""

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng or random.Random()
        self._cards = full_deck()
        self._rng.shuffle(self._cards)

    def deal(self, n: int) -> list[Card]:
        if n > len(self._cards):
            raise ValueError("deck exhausted")
        dealt, self._cards = self._cards[:n], self._cards[n:]
        return dealt


class PlayerStatus(str, Enum):
    ACTIVE = "active"
    FOLDED = "folded"
    ALL_IN = "all_in"
    SITTING_OUT = "sitting_out"


class BettingRound(str, Enum):
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"


@dataclass
class Player:
    seat: int
    name: str
    stack: int
    hole_cards: list[Card] | None = None
    # A newly-seated player is eligible for the next hand.
    status: PlayerStatus = PlayerStatus.ACTIVE
    current_bet: int = 0
    total_committed: int = 0
    has_acted_this_round: bool = False

    def reset_for_new_hand(self) -> None:
        self.hole_cards = None
        self.current_bet = 0
        self.total_committed = 0
        self.has_acted_this_round = False
        if self.status != PlayerStatus.SITTING_OUT:
            self.status = PlayerStatus.ACTIVE

    def public_dict(self, reveal_hole_cards: bool) -> dict:
        return {
            "seat": self.seat,
            "name": self.name,
            "stack": self.stack,
            "status": self.status.value,
            "current_bet": self.current_bet,
            "total_committed": self.total_committed,
            "hole_cards": (
                [c.to_dict() for c in self.hole_cards]
                if reveal_hole_cards and self.hole_cards
                else None
            ),
        }


@dataclass
class Pot:
    amount: int
    eligible_seats: set[int]

    def to_dict(self) -> dict:
        return {"amount": self.amount, "eligible_seats": sorted(self.eligible_seats)}


@dataclass
class Table:
    table_id: str
    small_blind: int
    big_blind: int
    players: dict[int, Player] = field(default_factory=dict)
    button_seat: int | None = None
    community_cards: list[Card] = field(default_factory=list)
    betting_round: BettingRound | None = None
    pots: list[Pot] = field(default_factory=list)
    current_bet: int = 0
    min_raise: int = 0
    current_actor: int | None = None
    last_aggressor: int | None = None
    deck: Deck | None = None
    hand_in_progress: bool = False
    last_action_log: list[str] = field(default_factory=list)
    last_showdown: list[dict] = field(default_factory=list)

    def seated_seats_in_order(self) -> list[int]:
        return sorted(self.players.keys())

    def active_seats(self) -> list[int]:
        return [
            s
            for s in self.seated_seats_in_order()
            if self.players[s].status in (PlayerStatus.ACTIVE, PlayerStatus.ALL_IN)
        ]

    def non_folded_seats(self) -> list[int]:
        return [
            s
            for s in self.seated_seats_in_order()
            if self.players[s].status != PlayerStatus.FOLDED
        ]

    def to_dict(self, viewer_seat: int | None) -> dict:
        showdown = self.betting_round == BettingRound.SHOWDOWN
        return {
            "table_id": self.table_id,
            "small_blind": self.small_blind,
            "big_blind": self.big_blind,
            "button_seat": self.button_seat,
            "community_cards": [c.to_dict() for c in self.community_cards],
            "betting_round": self.betting_round.value if self.betting_round else None,
            "pots": [p.to_dict() for p in self.pots],
            "current_bet": self.current_bet,
            "min_raise": self.min_raise,
            "current_actor": self.current_actor,
            "hand_in_progress": self.hand_in_progress,
            "players": [
                self.players[s].public_dict(
                    reveal_hole_cards=(s == viewer_seat or showdown)
                )
                for s in self.seated_seats_in_order()
            ],
            "last_action_log": self.last_action_log[-20:],
            "last_showdown": self.last_showdown,
        }
