"""Data models for Texas Hold'em poker."""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Set, Dict


class Suit(str, Enum):
    SPADES = "s"
    HEARTS = "h"
    DIAMONDS = "d"
    CLUBS = "c"


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
class Card:
    """A playing card with rank (2-14, where 14=Ace) and suit."""
    rank: int  # 2-14, 14 = Ace
    suit: Suit

    def __hash__(self):
        return hash((self.rank, self.suit))

    def __eq__(self, other):
        if not isinstance(other, Card):
            return False
        return self.rank == other.rank and self.suit == other.suit

    def to_dict(self):
        return {"rank": self.rank, "suit": self.suit.value}


@dataclass
class Player:
    """A player at the table."""
    seat: int
    name: str
    stack: int  # chips not yet committed
    status: PlayerStatus = PlayerStatus.ACTIVE
    hole_cards: Optional[List[Card]] = None  # None until dealt
    current_bet: int = 0  # chips committed THIS betting round
    total_committed: int = 0  # chips committed THIS HAND (all rounds)
    has_acted_this_round: bool = False

    def to_dict(self, show_hole_cards: bool = False):
        """Convert player to dict, optionally hiding hole cards."""
        hole_cards = None
        if show_hole_cards and self.hole_cards:
            hole_cards = [card.to_dict() for card in self.hole_cards]

        return {
            "seat": self.seat,
            "stack": self.stack,
            "status": self.status.value,
            "current_bet": self.current_bet,
            "total_committed": self.total_committed,
            "hole_cards": hole_cards,
        }


@dataclass
class Pot:
    """A pot (main or side) in the game."""
    amount: int
    eligible_seats: Set[int]


@dataclass
class Table:
    """A poker table with game state."""
    table_id: str
    small_blind: int
    big_blind: int
    players: Dict[int, Player] = field(default_factory=dict)
    button_seat: Optional[int] = None
    community_cards: List[Card] = field(default_factory=list)
    betting_round: Optional[BettingRound] = None
    pots: List[Pot] = field(default_factory=list)
    current_bet: int = 0
    min_raise: int = 0
    current_actor: Optional[int] = None
    last_aggressor: Optional[int] = None
    hand_in_progress: bool = False
    last_action_log: List[str] = field(default_factory=list)
    last_showdown: List[Dict] = field(default_factory=list)

    def add_action_log(self, message: str):
        """Add an action to the log, keeping only last 20."""
        self.last_action_log.append(message)
        if len(self.last_action_log) > 20:
            self.last_action_log = self.last_action_log[-20:]

    def to_dict(self, requesting_seat: Optional[int] = None):
        """Convert table state to dict, redacting hole cards appropriately."""
        # Determine if hole cards should be shown
        show_hole_cards = self.betting_round == BettingRound.SHOWDOWN

        players_list = []
        for seat in sorted(self.players.keys()):
            player = self.players[seat]
            should_show = show_hole_cards or (requesting_seat is not None and requesting_seat == seat)
            players_list.append(player.to_dict(show_hole_cards=should_show))

        return {
            "table_id": self.table_id,
            "small_blind": self.small_blind,
            "big_blind": self.big_blind,
            "button_seat": self.button_seat,
            "betting_round": self.betting_round.value if self.betting_round else None,
            "community_cards": [card.to_dict() for card in self.community_cards],
            "pots": [
                {
                    "amount": pot.amount,
                    "eligible_seats": sorted(list(pot.eligible_seats)),
                }
                for pot in self.pots
            ],
            "current_bet": self.current_bet,
            "min_raise": self.min_raise,
            "current_actor": self.current_actor,
            "hand_in_progress": self.hand_in_progress,
            "last_action_log": self.last_action_log,
            "last_showdown": self.last_showdown,
            "players": players_list,
        }
