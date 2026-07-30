"""Table / hand state machine, per docs/design-server.md.

Implements: turn state machine, betting rounds, blinds/button, short
all-in-raise handling, side-pot allocation, and hand evaluation wiring.
"""

from __future__ import annotations

import random
import uuid

from .evaluator import evaluate7
from .models import (
    ROUND_FLOP,
    ROUND_ORDER,
    ROUND_PREFLOP,
    ROUND_RIVER,
    ROUND_SHOWDOWN,
    ROUND_TURN,
    STATUS_ACTIVE,
    STATUS_ALL_IN,
    STATUS_FOLDED,
    STATUS_SITTING_OUT,
    ActionError,
    Card,
    Player,
    make_deck,
)

VALID_ACTIONS = {"fold", "check", "call", "bet", "raise"}


class Table:
    def __init__(self, table_id: str, small_blind: int, big_blind: int):
        self.table_id = table_id
        self.small_blind = small_blind
        self.big_blind = big_blind

        self.players: dict[int, Player] = {}
        self._next_seat = 0

        self.button_seat: int | None = None
        self.community_cards: list[Card] = []
        self.betting_round: str = ROUND_PREFLOP
        self.current_bet: int = 0
        self.min_raise: int = big_blind
        self.current_actor: int | None = None
        self.last_aggressor: int | None = None

        self.hand_in_progress: bool = False
        self.hand_seats: set[int] = set()
        self.deck: list[Card] = []
        self.last_showdown: list[dict] = []
        self.last_hand_was_showdown: bool = False

        self._rng = random.Random()
        self._rng.seed(int.from_bytes(__import__("os").urandom(16), "big"))

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def add_player(self, name: str, buy_in: int) -> int:
        seat = self._next_seat
        self._next_seat += 1
        self.players[seat] = Player(seat=seat, name=name, stack=buy_in, status=STATUS_SITTING_OUT)
        return seat

    # ------------------------------------------------------------------
    # Seat-order helpers
    # ------------------------------------------------------------------

    def _sorted_seats(self) -> list[int]:
        return sorted(self.players.keys())

    def _next_seat_matching(self, from_seat: int, predicate) -> int | None:
        """First seat, clockwise strictly after from_seat, satisfying predicate."""
        seats = self._sorted_seats()
        if not seats:
            return None
        if from_seat in seats:
            start_idx = seats.index(from_seat) + 1
        else:
            start_idx = 0
        n = len(seats)
        for i in range(n):
            candidate = seats[(start_idx + i) % n]
            if predicate(candidate):
                return candidate
        return None

    def _next_seat_with_chips(self, from_seat: int) -> int:
        result = self._next_seat_matching(from_seat, lambda s: self.players[s].stack > 0)
        return result if result is not None else from_seat

    # ------------------------------------------------------------------
    # Hand lifecycle
    # ------------------------------------------------------------------

    def start_hand(self) -> None:
        eligible = [s for s in self._sorted_seats() if self.players[s].stack > 0]
        if len(eligible) < 2:
            raise ActionError(400, "need at least 2 players with chips to start a hand")

        for seat, player in self.players.items():
            if player.stack > 0:
                player.status = STATUS_ACTIVE
            else:
                player.status = STATUS_SITTING_OUT
            player.hole_cards = None
            player.current_bet = 0
            player.total_committed = 0
            player.has_acted_this_round = False

        self.hand_seats = set(eligible)

        if self.button_seat is None or self.button_seat not in eligible:
            self.button_seat = min(eligible)

        self.deck = make_deck()
        self._rng.shuffle(self.deck)

        self.community_cards = []
        self.betting_round = ROUND_PREFLOP
        self.last_showdown = []
        self.last_hand_was_showdown = False
        self.last_aggressor = None

        # Deal 2 hole cards to each dealt-in player.
        for seat in sorted(self.hand_seats):
            self.players[seat].hole_cards = [self.deck.pop(), self.deck.pop()]

        # Determine blind seats.
        if len(eligible) == 2:
            sb_seat = self.button_seat
            bb_seat = self._next_seat_matching(self.button_seat, lambda s: s in self.hand_seats)
        else:
            sb_seat = self._next_seat_matching(self.button_seat, lambda s: s in self.hand_seats)
            bb_seat = self._next_seat_matching(sb_seat, lambda s: s in self.hand_seats)

        assert sb_seat is not None and bb_seat is not None

        self._post_blind(sb_seat, self.small_blind)
        self._post_blind(bb_seat, self.big_blind)

        self.current_bet = self.players[bb_seat].current_bet
        self.min_raise = self.big_blind

        # current_actor = seat left of BB (UTG).
        first_actor = self._next_seat_matching(
            bb_seat, lambda s: s in self.hand_seats and self.players[s].status == STATUS_ACTIVE
        )
        self.current_actor = first_actor
        self.hand_in_progress = True

        if first_actor is None:
            # Everyone is already all-in from blinds (extreme short stacks).
            self._runout_and_resolve()

    def _post_blind(self, seat: int, amount: int) -> None:
        player = self.players[seat]
        post = min(amount, player.stack)
        player.stack -= post
        player.current_bet += post
        player.total_committed += post
        if player.stack == 0:
            player.status = STATUS_ALL_IN

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def apply_action(self, seat: int, action: str, amount: int | None) -> None:
        if not self.hand_in_progress:
            raise ActionError(403, "no hand in progress")
        if seat not in self.players:
            raise ActionError(404, "no such seat")
        if action not in VALID_ACTIONS:
            raise ActionError(400, f"unknown action: {action}")

        # Invariant: only current_actor may act. Checked first, before any
        # other validation.
        if self.current_actor != seat:
            raise ActionError(403, "not your turn")

        player = self.players[seat]
        if player.status != STATUS_ACTIVE:
            raise ActionError(403, "not your turn")

        if action == "fold":
            self._apply_fold(player)
        elif action == "check":
            self._apply_check(player)
        elif action == "call":
            self._apply_call(player)
        elif action == "bet":
            self._apply_bet(player, amount)
        elif action == "raise":
            self._apply_raise(player, amount)

        self._advance(seat)

    def _apply_fold(self, player: Player) -> None:
        player.status = STATUS_FOLDED
        player.has_acted_this_round = True

    def _apply_check(self, player: Player) -> None:
        if self.current_bet != player.current_bet:
            raise ActionError(400, "cannot check: a bet is outstanding")
        player.has_acted_this_round = True

    def _apply_call(self, player: Player) -> None:
        chips_to_add = self.current_bet - player.current_bet
        if chips_to_add < 0:
            chips_to_add = 0
        if chips_to_add >= player.stack and chips_to_add > 0:
            add = player.stack
            player.current_bet += add
            player.total_committed += add
            player.stack = 0
            player.status = STATUS_ALL_IN
        else:
            player.stack -= chips_to_add
            player.current_bet += chips_to_add
            player.total_committed += chips_to_add
        player.has_acted_this_round = True

    def _apply_bet(self, player: Player, amount: int | None) -> None:
        if self.current_bet != 0:
            raise ActionError(400, "cannot bet: a bet is already outstanding, use raise")
        if amount is None or amount <= 0:
            raise ActionError(400, "bet requires a positive amount")

        effective = min(amount, player.stack)
        if effective <= 0:
            raise ActionError(400, "insufficient chips to bet")

        is_full_bet = effective >= self.big_blind
        is_all_in = effective == player.stack
        if not is_full_bet and not is_all_in:
            raise ActionError(400, f"bet below minimum ({self.big_blind})")

        player.stack -= effective
        player.current_bet = effective
        player.total_committed += effective
        if player.stack == 0:
            player.status = STATUS_ALL_IN

        self.current_bet = effective
        self.last_aggressor = player.seat
        player.has_acted_this_round = True

        if is_full_bet:
            self.min_raise = effective
            self._reset_others_acted(player.seat)

    def _apply_raise(self, player: Player, amount: int | None) -> None:
        if self.current_bet <= 0:
            raise ActionError(400, "cannot raise: no bet to raise, use bet")
        if amount is None:
            raise ActionError(400, "raise requires an amount")

        max_reachable = player.stack + player.current_bet
        effective = min(amount, max_reachable)
        if effective <= self.current_bet:
            raise ActionError(400, "raise must exceed the current bet")

        prev_current_bet = self.current_bet
        increment = effective - prev_current_bet
        is_full_raise = increment >= self.min_raise
        is_all_in = effective == max_reachable
        if not is_full_raise and not is_all_in:
            raise ActionError(400, f"raise below minimum increment ({self.min_raise})")

        chips_needed = effective - player.current_bet
        player.stack -= chips_needed
        player.total_committed += chips_needed
        player.current_bet = effective
        if player.stack == 0:
            player.status = STATUS_ALL_IN

        self.current_bet = effective
        self.last_aggressor = player.seat
        player.has_acted_this_round = True

        if is_full_raise:
            self.min_raise = increment
            self._reset_others_acted(player.seat)
        else:
            # Short all-in raise: does not reopen action for players who
            # already matched the previous current_bet.
            if increment >= self.min_raise:
                self.min_raise = increment

    def _reset_others_acted(self, actor_seat: int) -> None:
        for s in self.hand_seats:
            if s == actor_seat:
                continue
            p = self.players[s]
            if p.status == STATUS_ACTIVE:
                p.has_acted_this_round = False

    # ------------------------------------------------------------------
    # Round / hand advancement
    # ------------------------------------------------------------------

    def _non_folded_seats(self) -> list[int]:
        return [s for s in sorted(self.hand_seats) if self.players[s].status != STATUS_FOLDED]

    def _determine_next_actor(self, after_seat: int) -> int | None:
        def needs_to_act(s: int) -> bool:
            p = self.players[s]
            if p.status != STATUS_ACTIVE:
                return False
            return not (p.has_acted_this_round and p.current_bet == self.current_bet)

        seats = sorted(self.hand_seats)
        if after_seat in seats:
            start_idx = seats.index(after_seat) + 1
        else:
            start_idx = 0
        n = len(seats)
        for i in range(n):
            candidate = seats[(start_idx + i) % n]
            if needs_to_act(candidate):
                return candidate
        return None

    def _advance(self, acted_seat: int) -> None:
        non_folded = self._non_folded_seats()
        if len(non_folded) <= 1:
            self._resolve_hand(showdown=False)
            return

        next_actor = self._determine_next_actor(acted_seat)
        if next_actor is not None:
            self.current_actor = next_actor
            return

        # Betting round complete.
        active_can_act = [s for s in non_folded if self.players[s].status == STATUS_ACTIVE]
        if not active_can_act:
            self._runout_and_resolve()
            return

        self._advance_betting_round()

    def _advance_betting_round(self) -> None:
        for s in self.hand_seats:
            self.players[s].current_bet = 0
            self.players[s].has_acted_this_round = False
        self.current_bet = 0
        self.min_raise = self.big_blind
        self.last_aggressor = None

        idx = ROUND_ORDER.index(self.betting_round)
        next_round = ROUND_ORDER[idx + 1]

        if next_round == ROUND_FLOP:
            self._deal_community(3)
        elif next_round == ROUND_TURN:
            self._deal_community(1)
        elif next_round == ROUND_RIVER:
            self._deal_community(1)

        self.betting_round = next_round

        if next_round == ROUND_SHOWDOWN:
            self._resolve_hand(showdown=True)
            return

        non_folded = self._non_folded_seats()
        active_can_act = [s for s in non_folded if self.players[s].status == STATUS_ACTIVE]
        if not active_can_act:
            self._runout_and_resolve()
            return

        first_actor = self._next_seat_matching(
            self.button_seat,
            lambda s: s in self.hand_seats and self.players[s].status == STATUS_ACTIVE,
        )
        self.current_actor = first_actor
        if first_actor is None:
            self._runout_and_resolve()

    def _deal_community(self, n: int) -> None:
        for _ in range(n):
            self.community_cards.append(self.deck.pop())

    def _runout_and_resolve(self) -> None:
        """All remaining non-folded players are all-in: deal remaining
        community cards immediately (no further betting) and go to
        showdown."""
        while len(self.community_cards) < 5:
            self._deal_community(5 - len(self.community_cards))
        self.betting_round = ROUND_SHOWDOWN
        self.current_actor = None
        self._resolve_hand(showdown=True)

    # ------------------------------------------------------------------
    # Pots / showdown
    # ------------------------------------------------------------------

    def compute_pots(self) -> list[dict]:
        contributions = {
            s: self.players[s].total_committed
            for s in self.hand_seats
            if self.players[s].total_committed > 0
        }
        levels = sorted(set(contributions.values()))
        pots: list[dict] = []
        previous_level = 0
        for level in levels:
            layer_players = [s for s, c in contributions.items() if c >= level]
            layer_amount = (level - previous_level) * len(layer_players)
            if layer_amount > 0:
                eligible = {s for s in layer_players if self.players[s].status != STATUS_FOLDED}
                pots.append({"amount": layer_amount, "eligible_seats": eligible})
            previous_level = level
        return pots

    def _clockwise_order_from_button(self) -> dict[int, int]:
        seats = sorted(self.hand_seats)
        n = len(seats)
        if self.button_seat in seats:
            start_idx = seats.index(self.button_seat)
        else:
            start_idx = 0
        order = {}
        for i in range(n):
            seat = seats[(start_idx + i) % n]
            order[seat] = i
        return order

    def _resolve_hand(self, showdown: bool) -> None:
        pots = self.compute_pots()
        non_folded = self._non_folded_seats()

        hand_scores: dict[int, tuple[int, tuple[int, ...]]] = {}
        last_showdown: list[dict] = []
        if showdown:
            for s in non_folded:
                cards = self.players[s].hole_cards + self.community_cards
                score, category = evaluate7(cards)
                hand_scores[s] = score
                last_showdown.append(
                    {
                        "seat": s,
                        "hole_cards": [c.to_dict() for c in self.players[s].hole_cards],
                        "hand_category": category,
                    }
                )

        order_index = self._clockwise_order_from_button()

        for pot in pots:
            eligible = pot["eligible_seats"]
            if not eligible:
                continue
            if len(eligible) == 1 or not showdown:
                if showdown:
                    best = max(hand_scores[s] for s in eligible)
                    winners = [s for s in eligible if hand_scores[s] == best]
                else:
                    winners = [s for s in eligible if s in non_folded]
                    if not winners:
                        winners = list(eligible)
            else:
                best = max(hand_scores[s] for s in eligible)
                winners = [s for s in eligible if hand_scores[s] == best]

            winners_sorted = sorted(winners, key=lambda s: order_index.get(s, 0))
            n_winners = len(winners_sorted)
            share = pot["amount"] // n_winners
            remainder = pot["amount"] - share * n_winners
            for i, w in enumerate(winners_sorted):
                extra = 1 if i < remainder else 0
                self.players[w].stack += share + extra

        self.last_showdown = last_showdown
        self.last_hand_was_showdown = showdown
        self.hand_in_progress = False
        self.current_actor = None

        self.button_seat = self._next_seat_with_chips(self.button_seat)

    # ------------------------------------------------------------------
    # State serialization
    # ------------------------------------------------------------------

    def get_state(self, seat: int | None = None) -> dict:
        pots = self.compute_pots()

        players_out = []
        for s in sorted(self.players.keys()):
            p = self.players[s]
            reveal = (seat is not None and seat == s) or (
                self.last_hand_was_showdown and p.status != STATUS_FOLDED
            )
            hole_cards = None
            if p.hole_cards is not None and reveal:
                hole_cards = [c.to_dict() for c in p.hole_cards]
            players_out.append(
                {
                    "seat": p.seat,
                    "name": p.name,
                    "stack": p.stack,
                    "status": p.status,
                    "current_bet": p.current_bet,
                    "total_committed": p.total_committed,
                    "hole_cards": hole_cards,
                }
            )

        return {
            "hand_in_progress": self.hand_in_progress,
            "current_actor": self.current_actor,
            "current_bet": self.current_bet,
            "button_seat": self.button_seat,
            "community_cards": [c.to_dict() for c in self.community_cards],
            "pots": [
                {"amount": p["amount"], "eligible_seats": sorted(p["eligible_seats"])}
                for p in pots
            ],
            "last_showdown": self.last_showdown,
            "players": players_out,
            "betting_round": self.betting_round,
            "small_blind": self.small_blind,
            "big_blind": self.big_blind,
            "min_raise": self.min_raise,
            "table_id": self.table_id,
        }


def new_table_id() -> str:
    return uuid.uuid4().hex
