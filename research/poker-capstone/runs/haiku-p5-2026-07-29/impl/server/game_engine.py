"""Core game logic for Texas Hold'em poker."""

import os
import random
from itertools import combinations
from typing import List, Tuple, Optional
from models import (
    Card,
    Suit,
    Player,
    PlayerStatus,
    BettingRound,
    Table,
    Pot,
)


class GameEngine:
    """Manages game state and logic."""

    def __init__(self):
        self.tables: dict[str, Table] = {}

    def create_table(self, table_id: str, small_blind: int, big_blind: int) -> Table:
        """Create a new table."""
        table = Table(
            table_id=table_id,
            small_blind=small_blind,
            big_blind=big_blind,
        )
        self.tables[table_id] = table
        return table

    def get_table(self, table_id: str) -> Optional[Table]:
        """Get a table by ID."""
        return self.tables.get(table_id)

    def seat_player(self, table: Table, name: str, buy_in: int) -> int:
        """Seat a player at the table. Returns the seat number."""
        # Find next available seat
        seat = 0
        while seat in table.players:
            seat += 1

        player = Player(
            seat=seat,
            name=name,
            stack=buy_in,
            status=PlayerStatus.SITTING_OUT,
        )
        table.players[seat] = player
        table.add_action_log(f"{name} seated at seat {seat}")
        return seat

    def start_hand(self, table: Table) -> None:
        """Start a new hand. Requires at least 2 seated players."""
        # Count seated players
        if len(table.players) < 2:
            raise ValueError("Need at least 2 players to start a hand")

        # Initialize hand
        table.hand_in_progress = True
        table.last_showdown = []
        table.betting_round = BettingRound.PREFLOP
        table.pots = []
        table.community_cards = []
        table.last_action_log = []

        # Move button to next active seat if this is not the first hand
        if table.button_seat is None:
            # First hand: button is at seat 0 (or first active seat)
            active_seats = sorted([s for s in table.players.keys() if table.players[s].status != PlayerStatus.SITTING_OUT])
            table.button_seat = active_seats[0] if active_seats else 0
        else:
            # Move button clockwise to next active seat
            active_seats = sorted([s for s in table.players.keys() if table.players[s].status != PlayerStatus.SITTING_OUT])
            current_idx = active_seats.index(table.button_seat)
            table.button_seat = active_seats[(current_idx + 1) % len(active_seats)]

        # Reset player state for new hand
        for player in table.players.values():
            player.hole_cards = None
            player.current_bet = 0
            player.total_committed = 0
            player.has_acted_this_round = False
            if player.stack > 0:
                player.status = PlayerStatus.ACTIVE
            else:
                player.status = PlayerStatus.SITTING_OUT

        # Post blinds
        active_seats = sorted([s for s in table.players.keys() if table.players[s].status == PlayerStatus.ACTIVE])

        if len(active_seats) == 2:
            # Heads-up: button is small blind
            sb_seat = table.button_seat
            bb_seat = active_seats[1] if active_seats[0] == sb_seat else active_seats[0]
        else:
            # Normal: small blind is left of button
            button_idx = active_seats.index(table.button_seat)
            sb_seat = active_seats[(button_idx + 1) % len(active_seats)]
            bb_seat = active_seats[(button_idx + 2) % len(active_seats)]

        # Post blinds (chips go into current_bet and total_committed)
        sb_player = table.players[sb_seat]
        sb_amount = min(table.small_blind, sb_player.stack)
        sb_player.stack -= sb_amount
        sb_player.current_bet = sb_amount
        sb_player.total_committed = sb_amount

        bb_player = table.players[bb_seat]
        bb_amount = min(table.big_blind, bb_player.stack)
        bb_player.stack -= bb_amount
        bb_player.current_bet = bb_amount
        bb_player.total_committed = bb_amount

        table.current_bet = bb_amount
        table.min_raise = table.big_blind
        table.add_action_log(f"Blinds posted: SB {sb_amount} (seat {sb_seat}), BB {bb_amount} (seat {bb_seat})")

        # Deal hole cards
        deck = self._create_and_shuffle_deck()
        for player in [p for p in table.players.values() if p.status == PlayerStatus.ACTIVE]:
            player.hole_cards = [deck.pop(), deck.pop()]

        # Set current actor to UTG (left of BB)
        utg_idx = (active_seats.index(bb_seat) + 1) % len(active_seats)
        table.current_actor = active_seats[utg_idx]
        table.last_aggressor = bb_seat

        table.add_action_log(f"Hand started. UTG is seat {table.current_actor}")

    def _create_and_shuffle_deck(self) -> List[Card]:
        """Create a shuffled deck."""
        random.seed(int.from_bytes(os.urandom(4), "big"))
        deck = []
        for rank in range(2, 15):  # 2-14 (14 = Ace)
            for suit in Suit:
                deck.append(Card(rank=rank, suit=suit))
        random.shuffle(deck)
        return deck

    def submit_action(
        self,
        table: Table,
        seat: int,
        action: str,
        amount: Optional[int] = None,
    ) -> None:
        """
        Submit an action for a player.

        Raises ValueError with description if action is invalid.
        Important: hand_in_progress is checked BEFORE the actor check.
        """
        if not table.hand_in_progress:
            raise ValueError("No hand in progress")

        if table.current_actor is None:
            raise ValueError("No current actor")

        if seat != table.current_actor:
            raise ValueError(f"Not your turn (current actor is seat {table.current_actor})")

        player = table.players[seat]
        action_lower = action.lower()

        if action_lower == "fold":
            player.status = PlayerStatus.FOLDED
            player.has_acted_this_round = True
            table.add_action_log(f"Seat {seat} ({player.name}) folded")

        elif action_lower == "check":
            if player.current_bet != table.current_bet:
                raise ValueError("Cannot check when there's a bet to call")
            player.has_acted_this_round = True
            table.add_action_log(f"Seat {seat} ({player.name}) checked")

        elif action_lower == "call":
            chips_to_add = table.current_bet - player.current_bet
            if chips_to_add > 0:
                if chips_to_add >= player.stack:
                    # All in
                    chips_to_add = player.stack
                    player.status = PlayerStatus.ALL_IN
                player.stack -= chips_to_add
                player.current_bet += chips_to_add
                player.total_committed += chips_to_add
            player.has_acted_this_round = True
            table.add_action_log(f"Seat {seat} ({player.name}) called {chips_to_add}")

        elif action_lower == "bet":
            if table.current_bet != 0:
                raise ValueError("Cannot bet when there's already a bet this round")
            if amount is None or amount < table.big_blind:
                raise ValueError(f"Bet amount must be at least {table.big_blind}")

            # Cap at stack
            bet_amount = min(amount, player.stack + player.current_bet)
            chips_to_add = bet_amount - player.current_bet

            if chips_to_add >= player.stack:
                # All in
                chips_to_add = player.stack
                player.status = PlayerStatus.ALL_IN
                bet_amount = player.current_bet + chips_to_add

            player.stack -= chips_to_add
            player.current_bet = bet_amount
            player.total_committed += chips_to_add
            table.current_bet = bet_amount
            table.min_raise = table.big_blind
            table.last_aggressor = seat

            # Reset has_acted for other players (they must act again)
            for p in table.players.values():
                if p.seat != seat and p.status in (PlayerStatus.ACTIVE, PlayerStatus.ALL_IN):
                    p.has_acted_this_round = False

            table.add_action_log(f"Seat {seat} ({player.name}) bet {bet_amount}")

        elif action_lower == "raise":
            if table.current_bet == 0:
                raise ValueError("Cannot raise when no one has bet yet (use 'bet' instead)")

            if amount is None:
                raise ValueError("Raise amount required")

            # The amount is the total bet this round, not the increment
            raise_amount = amount
            if raise_amount <= table.current_bet:
                raise ValueError(f"Raise must be at least {table.current_bet + table.min_raise}")

            # Cap at stack
            chips_to_add = raise_amount - player.current_bet
            if chips_to_add > player.stack:
                # All in for less than full raise amount
                chips_to_add = player.stack
                raise_amount = player.current_bet + chips_to_add
                player.status = PlayerStatus.ALL_IN

                # Short all-in raise: check if it's a full raise
                short_raise_amount = raise_amount - table.current_bet
                if short_raise_amount < table.min_raise:
                    # Short all-in: doesn't reopen, min_raise stays same, has_acted not reset
                    pass
                else:
                    # Full raise: reopen action
                    table.min_raise = short_raise_amount
                    for p in table.players.values():
                        if p.seat != seat and p.status in (PlayerStatus.ACTIVE, PlayerStatus.ALL_IN):
                            p.has_acted_this_round = False
            else:
                # Full raise (not all-in)
                raise_increment = raise_amount - table.current_bet
                if raise_increment < table.min_raise:
                    raise ValueError(f"Raise increment must be at least {table.min_raise}")

                player.status = PlayerStatus.ACTIVE
                table.min_raise = raise_increment

                # Reset has_acted for other players
                for p in table.players.values():
                    if p.seat != seat and p.status in (PlayerStatus.ACTIVE, PlayerStatus.ALL_IN):
                        p.has_acted_this_round = False

            player.stack -= chips_to_add
            player.current_bet = raise_amount
            player.total_committed += chips_to_add
            table.current_bet = raise_amount
            table.last_aggressor = seat
            player.has_acted_this_round = True

            table.add_action_log(f"Seat {seat} ({player.name}) raised to {raise_amount}")

        else:
            raise ValueError(f"Unknown action: {action}")

        # Move to next actor or advance round as needed
        self._update_game_state(table)

    def _update_game_state(self, table: Table) -> None:
        """Update game state after an action: check for hand end, advance round, or move to next player."""
        # Check if only one non-folded player remains
        active_unfoldedplayers = [
            p for p in table.players.values()
            if p.status in (PlayerStatus.ACTIVE, PlayerStatus.ALL_IN)
        ]

        if len(active_unfoldedplayers) == 1:
            # Hand ends, winner takes all pots
            self._resolve_hand(table, [active_unfoldedplayers[0].seat])
            return

        # Check if all remaining players are all-in
        can_act = [
            p for p in table.players.values()
            if p.status == PlayerStatus.ACTIVE
        ]

        if len(can_act) == 0 and len(active_unfoldedplayers) > 1:
            # All remaining players are all-in, deal remaining cards and go to showdown
            self._deal_remaining_cards(table)
            table.betting_round = BettingRound.SHOWDOWN
            self._resolve_showdown(table)
            return

        # Check if round should advance
        should_advance = True
        for player in active_unfoldedplayers:
            if not player.has_acted_this_round:
                should_advance = False
                break
            if player.status == PlayerStatus.ACTIVE and player.current_bet != table.current_bet:
                should_advance = False
                break

        if should_advance:
            self._advance_betting_round(table)
        else:
            # Move to next player to act
            self._move_to_next_actor(table)

    def _move_to_next_actor(self, table: Table) -> None:
        """Move to the next player who needs to act."""
        if table.current_actor is None:
            return

        # Get list of players who can still act (not folded, not sitting out)
        can_act_seats = sorted([
            s for s in table.players.keys()
            if table.players[s].status in (PlayerStatus.ACTIVE, PlayerStatus.ALL_IN)
        ])

        if not can_act_seats:
            return

        if len(can_act_seats) == 1:
            # Only one player left, no more action needed
            table.current_actor = None
            return

        # Find the next player after current_actor in order around the table
        all_seats_in_order = sorted(table.players.keys())
        try:
            current_pos = all_seats_in_order.index(table.current_actor)
        except ValueError:
            # Current actor is no longer valid, find first valid player
            table.current_actor = can_act_seats[0]
            return

        # Find next can-act player after current position
        for i in range(1, len(all_seats_in_order)):
            next_pos = (current_pos + i) % len(all_seats_in_order)
            next_seat = all_seats_in_order[next_pos]
            if next_seat in can_act_seats:
                table.current_actor = next_seat
                return

        # Fallback shouldn't happen but just in case
        table.current_actor = can_act_seats[0]

    def _advance_betting_round(self, table: Table) -> None:
        """Advance to the next betting round."""
        # Reset player state
        for player in table.players.values():
            player.has_acted_this_round = False
            player.current_bet = 0

        table.current_bet = 0
        table.min_raise = table.big_blind

        # Advance betting round and deal cards
        if table.betting_round == BettingRound.PREFLOP:
            table.betting_round = BettingRound.FLOP
            deck = self._create_and_shuffle_deck()
            # Remove cards that are in play (hole cards and any community cards already dealt)
            in_play = set()
            for player in table.players.values():
                if player.hole_cards:
                    in_play.update(player.hole_cards)
            for card in table.community_cards:
                in_play.add(card)

            deck = [c for c in deck if c not in in_play]
            table.community_cards.extend([deck.pop(), deck.pop(), deck.pop()])
            table.add_action_log(f"Flop dealt: {', '.join([f'{c.rank}{c.suit.value}' for c in table.community_cards])}")

        elif table.betting_round == BettingRound.FLOP:
            table.betting_round = BettingRound.TURN
            deck = self._create_and_shuffle_deck()
            in_play = set()
            for player in table.players.values():
                if player.hole_cards:
                    in_play.update(player.hole_cards)
            for card in table.community_cards:
                in_play.add(card)

            deck = [c for c in deck if c not in in_play]
            table.community_cards.append(deck.pop())
            table.add_action_log(f"Turn dealt: {table.community_cards[-1].rank}{table.community_cards[-1].suit.value}")

        elif table.betting_round == BettingRound.TURN:
            table.betting_round = BettingRound.RIVER
            deck = self._create_and_shuffle_deck()
            in_play = set()
            for player in table.players.values():
                if player.hole_cards:
                    in_play.update(player.hole_cards)
            for card in table.community_cards:
                in_play.add(card)

            deck = [c for c in deck if c not in in_play]
            table.community_cards.append(deck.pop())
            table.add_action_log(f"River dealt: {table.community_cards[-1].rank}{table.community_cards[-1].suit.value}")

        elif table.betting_round == BettingRound.RIVER:
            table.betting_round = BettingRound.SHOWDOWN
            self._resolve_showdown(table)
            return

        # Set current actor to first active player left of button
        active_seats = sorted([
            s for s in table.players.keys()
            if table.players[s].status in (PlayerStatus.ACTIVE, PlayerStatus.ALL_IN)
        ])

        if not active_seats:
            return

        button_idx = active_seats.index(table.button_seat) if table.button_seat in active_seats else 0
        first_to_act_idx = (button_idx + 1) % len(active_seats)
        table.current_actor = active_seats[first_to_act_idx]

    def _deal_remaining_cards(self, table: Table) -> None:
        """Deal remaining community cards when all players are all-in."""
        deck = self._create_and_shuffle_deck()
        in_play = set()
        for player in table.players.values():
            if player.hole_cards:
                in_play.update(player.hole_cards)
        for card in table.community_cards:
            in_play.add(card)

        deck = [c for c in deck if c not in in_play]

        cards_needed = 5 - len(table.community_cards)
        for _ in range(cards_needed):
            if deck:
                table.community_cards.append(deck.pop())

    def _resolve_showdown(self, table: Table) -> None:
        """Resolve a showdown and pay out winners."""
        # Get non-folded players
        non_folded = [
            p for p in table.players.values()
            if p.status != PlayerStatus.FOLDED
        ]

        # Build side pots
        pots = self._build_side_pots(table)
        table.pots = pots

        # Evaluate hands and record showdown
        showdown_records = []
        hand_scores = {}

        for player in non_folded:
            if player.hole_cards:
                best_hand = self._find_best_hand(player.hole_cards, table.community_cards)
                hand_scores[player.seat] = best_hand
                hand_category = self._hand_category_name(best_hand[0])
                showdown_records.append({
                    "seat": player.seat,
                    "hole_cards": [card.to_dict() for card in player.hole_cards],
                    "hand_category": hand_category,
                })

        table.last_showdown = showdown_records

        # Resolve each pot
        for pot in pots:
            eligible_in_pot = [s for s in pot.eligible_seats if s in hand_scores]

            if not eligible_in_pot:
                continue

            # Find best hand among eligible players
            best_score = None
            winners = []

            for seat in eligible_in_pot:
                score = hand_scores[seat]
                if best_score is None or score > best_score:
                    best_score = score
                    winners = [seat]
                elif score == best_score:
                    winners.append(seat)

            # Split pot among winners
            per_winner = pot.amount // len(winners)
            remainder = pot.amount % len(winners)

            # Sort winners by seat position for deterministic chip distribution
            # Odd chips go to first winning seat clockwise from button
            sorted_winners = sorted(winners)
            button_idx_in_winners = [i for i, s in enumerate(sorted_winners) if s == table.button_seat]

            if button_idx_in_winners:
                first_winner_from_button = sorted_winners[button_idx_in_winners[0]:]
                if not first_winner_from_button:
                    first_winner_from_button = sorted_winners

            for i, winner_seat in enumerate(sorted_winners):
                chips = per_winner
                if i < remainder:
                    chips += 1
                table.players[winner_seat].stack += chips
                table.add_action_log(f"Seat {winner_seat} won {chips} chips")

        table.hand_in_progress = False
        table.current_actor = None
        table.betting_round = BettingRound.SHOWDOWN

    def _build_side_pots(self, table: Table) -> List[Pot]:
        """Build side pots from player contributions."""
        contributions = {}
        for player in table.players.values():
            if player.total_committed > 0:
                contributions[player.seat] = player.total_committed

        if not contributions:
            return []

        levels = sorted(set(contributions.values()))
        pots = []
        previous_level = 0

        for level in levels:
            layer_players = [seat for seat, contrib in contributions.items() if contrib >= level]
            layer_amount = (level - previous_level) * len(layer_players)

            if layer_amount > 0:
                eligible = [
                    seat for seat in layer_players
                    if table.players[seat].status != PlayerStatus.FOLDED
                ]
                pots.append(Pot(amount=layer_amount, eligible_seats=set(eligible)))

            previous_level = level

        return pots

    def _find_best_hand(self, hole_cards: List[Card], community_cards: List[Card]) -> Tuple:
        """Find the best 5-card hand from 7 cards."""
        all_cards = hole_cards + community_cards
        best_hand = None

        for combo in combinations(all_cards, 5):
            hand = self._evaluate_hand(list(combo))
            if best_hand is None or hand > best_hand:
                best_hand = hand

        return best_hand

    def _evaluate_hand(self, cards: List[Card]) -> Tuple:
        """Evaluate a 5-card hand and return a comparable tuple."""
        ranks = sorted([c.rank for c in cards], reverse=True)
        suits = [c.suit for c in cards]

        # Check for flush
        is_flush = len(set(suits)) == 1

        # Check for straight
        is_straight, straight_high = self._check_straight(ranks)

        # Count ranks
        rank_counts = {}
        for rank in ranks:
            rank_counts[rank] = rank_counts.get(rank, 0) + 1

        counts = sorted(rank_counts.values(), reverse=True)
        unique_ranks = sorted(rank_counts.keys(), key=lambda r: (rank_counts[r], r), reverse=True)

        # Determine hand category
        if is_straight and is_flush:
            return (8, straight_high)  # Straight flush
        elif counts == [4, 1]:
            quad_rank = [r for r in unique_ranks if rank_counts[r] == 4][0]
            kicker = [r for r in unique_ranks if rank_counts[r] == 1][0]
            return (7, quad_rank, kicker)  # Four of a kind
        elif counts == [3, 2]:
            trips_rank = [r for r in unique_ranks if rank_counts[r] == 3][0]
            pair_rank = [r for r in unique_ranks if rank_counts[r] == 2][0]
            return (6, trips_rank, pair_rank)  # Full house
        elif is_flush:
            return (5, *ranks)  # Flush
        elif is_straight:
            return (4, straight_high)  # Straight
        elif counts == [3, 1, 1]:
            trips_rank = [r for r in unique_ranks if rank_counts[r] == 3][0]
            kickers = sorted([r for r in unique_ranks if rank_counts[r] == 1], reverse=True)
            return (3, trips_rank, *kickers)  # Three of a kind
        elif counts == [2, 2, 1]:
            pairs = sorted([r for r in unique_ranks if rank_counts[r] == 2], reverse=True)
            kicker = [r for r in unique_ranks if rank_counts[r] == 1][0]
            return (2, pairs[0], pairs[1], kicker)  # Two pair
        elif counts == [2, 1, 1, 1]:
            pair_rank = [r for r in unique_ranks if rank_counts[r] == 2][0]
            kickers = sorted([r for r in unique_ranks if rank_counts[r] == 1], reverse=True)
            return (1, pair_rank, *kickers)  # One pair
        else:
            return (0, *ranks)  # High card

    def _check_straight(self, ranks: List[int]) -> Tuple[bool, int]:
        """Check if ranks form a straight. Returns (is_straight, high_card)."""
        # Check for regular straight
        if ranks == list(range(ranks[0], ranks[0] - 5, -1)):
            return True, ranks[0]

        # Check for wheel (A-2-3-4-5)
        if set(ranks) == {14, 2, 3, 4, 5}:
            return True, 5  # Ace is low in wheel

        return False, 0

    def _hand_category_name(self, category: int) -> str:
        """Convert hand category number to name."""
        categories = {
            0: "High card",
            1: "One pair",
            2: "Two pair",
            3: "Three of a kind",
            4: "Straight",
            5: "Flush",
            6: "Full house",
            7: "Four of a kind",
            8: "Straight flush",
        }
        return categories.get(category, "Unknown")

    def _resolve_hand(self, table: Table, winner_seats: List[int]) -> None:
        """Resolve hand with specific winner(s) (used for fold-out)."""
        # Build side pots even if hand ends early
        pots = self._build_side_pots(table)
        table.pots = pots

        # Calculate eligible winners for each pot
        total_won = 0
        for pot in pots:
            eligible_winners = [s for s in winner_seats if s in pot.eligible_seats]
            if eligible_winners:
                per_winner = pot.amount // len(eligible_winners)
                remainder = pot.amount % len(eligible_winners)

                for i, winner_seat in enumerate(sorted(eligible_winners)):
                    chips = per_winner
                    if i < remainder:
                        chips += 1
                    table.players[winner_seat].stack += chips
                    total_won += chips
                    table.add_action_log(f"Seat {winner_seat} won {chips} chips")

        table.hand_in_progress = False
        table.current_actor = None
        table.last_showdown = []
