"""Turn state machine, betting rounds, blinds, side pots, showdown.
See docs/design-server.md for the full spec this implements.
"""

from __future__ import annotations

from .hand_eval import best_hand, describe
from .models import BettingRound, Deck, Player, PlayerStatus, Pot, Table


class ActionError(Exception):
    """Raised for any illegal action request. The caller (API layer) turns
    this into a 409 with {"error": str(exc)} and leaves state untouched —
    game_engine functions never partially mutate state before raising."""


def _hand_seats(table: Table) -> list[int]:
    """Seats participating in THIS hand (i.e. not SITTING_OUT), in seat order."""
    return [
        s
        for s in table.seated_seats_in_order()
        if table.players[s].status != PlayerStatus.SITTING_OUT
    ]


def _next_seat(seats: list[int], from_seat: int) -> int:
    idx = seats.index(from_seat)
    return seats[(idx + 1) % len(seats)]


def _first_actor_from(table: Table, seats: list[int], start_seat: int) -> int | None:
    """First seat at/after start_seat (inclusive) whose status is ACTIVE
    (can still act this round). None if no such seat exists."""
    n = len(seats)
    start_idx = seats.index(start_seat)
    for i in range(n):
        seat = seats[(start_idx + i) % n]
        if table.players[seat].status == PlayerStatus.ACTIVE:
            return seat
    return None


def start_new_hand(table: Table, deck: Deck | None = None) -> Table:
    if table.hand_in_progress:
        raise ActionError("a hand is already in progress")

    for player in table.players.values():
        if player.status == PlayerStatus.SITTING_OUT:
            continue
        if player.stack <= 0:
            player.status = PlayerStatus.SITTING_OUT
        else:
            player.reset_for_new_hand()

    seats = _hand_seats(table)
    if len(seats) < 2:
        raise ActionError("need at least 2 players with chips to start a hand")

    if table.button_seat is None or table.button_seat not in seats:
        table.button_seat = seats[0]
    else:
        table.button_seat = _next_seat(seats, table.button_seat)

    table.community_cards = []
    table.pots = []
    table.last_action_log = []
    table.last_showdown = []
    # Fresh shuffled deck, unless a deck (e.g. a test double) is injected.
    table.deck = deck if deck is not None else table.deck.__class__()
    table.hand_in_progress = True
    table.last_aggressor = None

    heads_up = len(seats) == 2
    if heads_up:
        sb_seat = table.button_seat
        bb_seat = _next_seat(seats, sb_seat)
    else:
        sb_seat = _next_seat(seats, table.button_seat)
        bb_seat = _next_seat(seats, sb_seat)

    _post_blind(table, sb_seat, table.small_blind)
    _post_blind(table, bb_seat, table.big_blind)

    for seat in seats:
        table.players[seat].hole_cards = table.deck.deal(2)

    table.betting_round = BettingRound.PREFLOP
    table.current_bet = table.big_blind
    table.min_raise = table.big_blind
    first_to_act = _next_seat(seats, bb_seat)
    table.current_actor = _first_actor_from(table, seats, first_to_act)
    table.last_aggressor = bb_seat

    _maybe_end_hand_early(table)
    return table


def _post_blind(table: Table, seat: int, amount: int) -> None:
    player = table.players[seat]
    add = min(amount, player.stack)
    player.stack -= add
    player.current_bet += add
    player.total_committed += add
    if player.stack == 0:
        player.status = PlayerStatus.ALL_IN
    table.last_action_log.append(f"seat {seat} posts blind {add}")


def submit_action(
    table: Table, seat: int, action: str, amount: int | None = None
) -> Table:
    if not table.hand_in_progress:
        raise ActionError("no hand in progress")
    if table.current_actor != seat:
        raise ActionError("not your turn")

    player = table.players[seat]
    if player.status != PlayerStatus.ACTIVE:
        raise ActionError("player cannot act")

    to_call = table.current_bet - player.current_bet

    if action == "fold":
        player.status = PlayerStatus.FOLDED
        table.last_action_log.append(f"seat {seat} folds")

    elif action == "check":
        if to_call != 0:
            raise ActionError("cannot check, facing a bet")
        table.last_action_log.append(f"seat {seat} checks")

    elif action == "call":
        if to_call <= 0:
            raise ActionError("nothing to call, use check")
        add = min(to_call, player.stack)
        player.stack -= add
        player.current_bet += add
        player.total_committed += add
        if player.stack == 0:
            player.status = PlayerStatus.ALL_IN
        table.last_action_log.append(f"seat {seat} calls {add}")

    elif action == "bet":
        if table.current_bet != 0:
            raise ActionError("cannot bet, must call/raise/fold")
        _apply_wager(table, player, amount, is_raise=False)
        table.last_action_log.append(f"seat {seat} bets {player.current_bet}")

    elif action == "raise":
        if table.current_bet == 0:
            raise ActionError("cannot raise, must bet")
        _apply_wager(table, player, amount, is_raise=True)
        table.last_action_log.append(f"seat {seat} raises to {player.current_bet}")

    else:
        raise ActionError(f"unknown action: {action}")

    player.has_acted_this_round = True
    _advance(table)
    return table


def _apply_wager(
    table: Table, player: Player, amount: int | None, is_raise: bool
) -> None:
    if amount is None:
        raise ActionError("amount required")

    max_reachable = player.current_bet + player.stack
    target = min(amount, max_reachable)
    is_all_in = target == max_reachable and player.stack > 0

    if not is_raise:
        min_target = min(table.big_blind, max_reachable)
        if target < min_target:
            raise ActionError(f"bet below minimum {min_target}")
    else:
        min_target = min(table.current_bet + table.min_raise, max_reachable)
        if target < min_target:
            raise ActionError(f"raise below minimum {min_target}")

    increment = target - player.current_bet
    if increment <= 0:
        raise ActionError("wager must increase current bet")

    player.stack -= increment
    player.current_bet = target
    player.total_committed += increment
    if player.stack == 0:
        player.status = PlayerStatus.ALL_IN

    raise_size = target - table.current_bet
    full_raise = raise_size >= table.min_raise
    if raise_size > 0:
        if full_raise or not is_all_in:
            table.min_raise = max(table.min_raise, raise_size)
            table.current_bet = target
            table.last_aggressor = player.seat
            _reset_acted_except(table, player.seat)
        else:
            # Short all-in raise (design-server.md "Short all-in raise"):
            # does not reopen action for players who already matched the
            # previous current_bet, and does not raise min_raise. It DOES
            # raise current_bet so later-to-act players still owe up to it.
            table.current_bet = target
    elif not is_raise:
        # first bet this round (table.current_bet was 0)
        table.current_bet = target
        table.min_raise = max(table.big_blind, target)
        table.last_aggressor = player.seat
        _reset_acted_except(table, player.seat)


def _reset_acted_except(table: Table, seat: int) -> None:
    for s, p in table.players.items():
        if s != seat and p.status == PlayerStatus.ACTIVE:
            p.has_acted_this_round = False


def _betting_round_complete(table: Table) -> bool:
    for player in table.players.values():
        if player.status != PlayerStatus.ACTIVE:
            continue
        if not player.has_acted_this_round:
            return False
        if player.current_bet != table.current_bet:
            return False
    return True


def _advance(table: Table) -> None:
    if _maybe_end_hand_early(table):
        return

    if not _betting_round_complete(table):
        seats = _hand_seats(table)
        nxt = _next_seat(seats, table.current_actor)
        table.current_actor = _first_actor_from(table, seats, nxt)
        if table.current_actor is None:
            _advance_betting_round(table)
        return

    _advance_betting_round(table)


def _maybe_end_hand_early(table: Table) -> bool:
    remaining = table.non_folded_seats()
    if len(remaining) <= 1:
        _finish_hand(table, awarded_seats=remaining)
        return True
    return False


def _count_can_still_act(table: Table) -> int:
    return sum(1 for p in table.players.values() if p.status == PlayerStatus.ACTIVE)


def _advance_betting_round(table: Table) -> None:
    for p in table.players.values():
        p.current_bet = 0
        p.has_acted_this_round = False
    table.current_bet = 0
    table.min_raise = table.big_blind

    order = {
        BettingRound.PREFLOP: BettingRound.FLOP,
        BettingRound.FLOP: BettingRound.TURN,
        BettingRound.TURN: BettingRound.RIVER,
        BettingRound.RIVER: BettingRound.SHOWDOWN,
    }
    deal_counts = {BettingRound.FLOP: 3, BettingRound.TURN: 1, BettingRound.RIVER: 1}

    next_round = order[table.betting_round]
    if next_round in deal_counts:
        table.community_cards.extend(table.deck.deal(deal_counts[next_round]))
    table.betting_round = next_round
    table.last_action_log.append(f"-- {next_round.value} --")

    if next_round == BettingRound.SHOWDOWN:
        _finish_hand(table, awarded_seats=None)
        return

    if _count_can_still_act(table) < 2:
        # Everyone remaining is all-in (or only one can act): deal out the
        # rest of the board with no further betting, straight to showdown.
        table.current_actor = None
        _advance_betting_round(table)
        return

    # First ACTIVE seat strictly after the button.
    seats = _hand_seats(table)
    nxt = _next_seat(seats, table.button_seat)
    table.current_actor = _first_actor_from(table, seats, nxt)


def _side_pots(table: Table) -> list[Pot]:
    """See docs/design-server.md "Side-pot allocation algorithm"."""
    contributions = {
        s: p.total_committed for s, p in table.players.items() if p.total_committed > 0
    }
    if not contributions:
        return []
    levels = sorted(set(contributions.values()))
    pots: list[Pot] = []
    previous_level = 0
    for level in levels:
        layer_players = [s for s, c in contributions.items() if c >= level]
        layer_amount = (level - previous_level) * len(layer_players)
        if layer_amount > 0:
            eligible = {
                s
                for s in layer_players
                if table.players[s].status != PlayerStatus.FOLDED
            }
            pots.append(Pot(amount=layer_amount, eligible_seats=eligible))
        previous_level = level
    return pots


def _finish_hand(table: Table, awarded_seats: list[int] | None = None) -> None:
    table.pots = _side_pots(table)
    table.last_showdown = []

    if awarded_seats is not None:
        # Fold-out: the sole remaining player wins every pot outright.
        winner = awarded_seats[0] if awarded_seats else None
        for pot in table.pots:
            if winner is not None:
                table.players[winner].stack += pot.amount
        if winner is not None:
            table.last_action_log.append(
                f"seat {winner} wins {sum(p.amount for p in table.pots)} (all others folded)"
            )
    else:
        scores: dict[int, tuple] = {}
        for seat in table.non_folded_seats():
            player = table.players[seat]
            score = best_hand(player.hole_cards, table.community_cards)
            scores[seat] = score
            table.last_showdown.append(
                {
                    "seat": seat,
                    "hole_cards": [c.to_dict() for c in player.hole_cards],
                    "hand_category": describe(score),
                }
            )

        for pot in table.pots:
            eligible = [s for s in pot.eligible_seats if s in scores]
            if not eligible:
                continue
            # INJECTED BUG: should be max() -- picks the worst eligible hand instead of the best.
            best_score = min(scores[s] for s in eligible)
            winners = sorted(s for s in eligible if scores[s] == best_score)
            share = pot.amount // len(winners)
            remainder = pot.amount - share * len(winners)
            # Odd chips go to the first winning seat clockwise from the
            # button (design-server.md), approximated here by seat order
            # starting from the button — deterministic tie-break.
            seats = _hand_seats(table)
            ordered_winners = sorted(
                winners,
                key=lambda s: (seats.index(s) - seats.index(table.button_seat))
                % len(seats),
            )
            for i, w in enumerate(ordered_winners):
                table.players[w].stack += share + (remainder if i == 0 else 0)
            table.last_action_log.append(
                f"pot of {pot.amount} won by seat(s) {ordered_winners}"
            )

    table.hand_in_progress = False
    table.betting_round = BettingRound.SHOWDOWN
    table.current_actor = None
