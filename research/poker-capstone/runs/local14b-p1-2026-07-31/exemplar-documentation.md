# Texas Hold'em Poker Server Documentation

## Overview

This document provides a comprehensive technical overview of the Texas Hold'em poker server implementation. The server is built using Python and FastAPI, and it includes models, hand evaluation, game engine, and a RESTful API with WebSocket support. The server handles the entire lifecycle of a poker game, including player management, betting rounds, and showdowns.

## Models

### Card

- **Attributes**:
  - `rank`: An integer representing the card rank (2-14, where 14 is Ace).
  - `suit`: A string representing the card suit (s, h, d, c for spades, hearts, diamonds, clubs).

- **Methods**:
  - `__str__`: Returns a string representation of the card (e.g., "As" for Ace of Spades).
  - `to_dict`: Returns a dictionary representation of the card.

### Deck

- **Attributes**:
  - `_rng`: A random number generator.
  - `_cards`: A list of `Card` objects representing the deck.

- **Methods**:
  - `__init__`: Initializes the deck with a shuffled set of cards.
  - `deal`: Deals a specified number of cards from the deck.

### PlayerStatus

- **Enum Values**:
  - `ACTIVE`: The player is actively participating in the current hand.
  - `FOLDED`: The player has folded the current hand.
  - `ALL_IN`: The player has bet all their chips.
  - `SITTING_OUT`: The player is not participating in the current hand.

### BettingRound

- **Enum Values**:
  - `PREFLOP`: The pre-flop betting round.
  - `FLOP`: The flop betting round.
  - `TURN`: The turn betting round.
  - `RIVER`: The river betting round.
  - `SHOWDOWN`: The showdown round.

### Player

- **Attributes**:
  - `seat`: An integer representing the player's seat number.
  - `name`: A string representing the player's name.
  - `stack`: An integer representing the player's chip stack.
  - `hole_cards`: A list of `Card` objects representing the player's hole cards.
  - `status`: A `PlayerStatus` enum value representing the player's status.
  - `current_bet`: An integer representing the player's current bet.
  - `total_committed`: An integer representing the total amount committed by the player.
  - `has_acted_this_round`: A boolean indicating whether the player has acted in the current betting round.

- **Methods**:
  - `reset_for_new_hand`: Resets the player's state for a new hand.
  - `public_dict`: Returns a dictionary representation of the player, optionally revealing the hole cards.

### Pot

- **Attributes**:
  - `amount`: An integer representing the amount in the pot.
  - `eligible_seats`: A set of integers representing the seats eligible to win the pot.

- **Methods**:
  - `to_dict`: Returns a dictionary representation of the pot.

### Table

- **Attributes**:
  - `table_id`: A string representing the table's unique identifier.
  - `small_blind`: An integer representing the small blind amount.
  - `big_blind`: An integer representing the big blind amount.
  - `players`: A dictionary mapping seat numbers to `Player` objects.
  - `button_seat`: An integer representing the seat of the button.
  - `community_cards`: A list of `Card` objects representing the community cards.
  - `betting_round`: A `BettingRound` enum value representing the current betting round.
  - `pots`: A list of `Pot` objects representing the pots.
  - `current_bet`: An integer representing the current bet amount.
  - `min_raise`: An integer representing the minimum raise amount.
  - `current_actor`: An integer representing the seat of the current actor.
  - `last_aggressor`: An integer representing the seat of the last aggressor.
  - `deck`: A `Deck` object representing the deck.
  - `hand_in_progress`: A boolean indicating whether a hand is in progress.
  - `last_action_log`: A list of strings representing the last action log.
  - `last_showdown`: A list of dictionaries representing the last showdown.

- **Methods**:
  - `seated_seats_in_order`: Returns a list of seated seats in order.
  - `active_seats`: Returns a list of active seats.
  - `non_folded_seats`: Returns a list of non-folded seats.
  - `to_dict`: Returns a dictionary representation of the table.

## Hand Evaluation

### score_five

- **Function**: Evaluates the best 5-card hand from a given set of 5 cards.
- **Returns**: A tuple representing the hand category and tie-breakers.

### best_hand

- **Function**: Determines the best 5-card hand from a given set of hole cards and community cards.
- **Returns**: A tuple representing the best hand category and tie-breakers.

### describe

- **Function**: Returns a string description of the hand category.

## Game Engine

### start_new_hand

- **Function**: Starts a new hand on the table.
- **Parameters**:
  - `table`: A `Table` object.
  - `deck`: An optional `Deck` object.
- **Returns**: The updated `Table` object.

### submit_action

- **Function**: Submits an action (fold, check, call, bet, raise) for a player.
- **Parameters**:
  - `table`: A `Table` object.
  - `seat`: An integer representing the player's seat.
  - `action`: A string representing the action.
  - `amount`: An optional integer representing the amount for bet or raise actions.
- **Returns**: The updated `Table` object.

### _post_blind

- **Function**: Posts a blind for a player.
- **Parameters**:
  - `table`: A `Table` object.
  - `seat`: An integer representing the player's seat.
  - `amount`: An integer representing the blind amount.

### _apply_wager

- **Function**: Applies a wager (bet or raise) for a player.
- **Parameters**:
  - `table`: A `Table` object.
  - `player`: A `Player` object.
  - `amount`: An integer representing the wager amount.
  - `is_raise`: A boolean indicating whether the action is a raise.

### _advance

- **Function**: Advances the game state.
- **Parameters**:
  - `table`: A `Table` object.

### _maybe_end_hand_early

- **Function**: Checks if the hand can be ended early.
- **Parameters**:
  - `table`: A `Table` object.
- **Returns**: A boolean indicating whether the hand can be ended early.

### _advance_betting_round

- **Function**: Advances to the next betting round.
- **Parameters**:
  - `table`: A `Table` object.

### _side_pots

- **Function**: Allocates side pots.
- **Parameters**:
  - `table`: A `Table` object.
- **Returns**: A list of `Pot` objects.

### _finish_hand

- **Function**: Finishes the hand and distributes the pots.
- **Parameters**:
  - `table`: A `Table` object.
  - `awarded_seats`: An optional list of integers representing the seats of the winners.

## API Endpoints

### /tables

- **POST**: Creates a new table.
- **Parameters**:
  - `small_blind`: An integer representing the small blind amount.
  - `big_blind`: An integer representing the big blind amount.
- **Returns**: A dictionary containing the table ID.

### /tables/{table_id}/players

- **POST**: Seats a player at the table.
- **Parameters**:
  - `name`: A string representing the player's name.
  - `buy_in`: An integer representing the player's buy-in amount.
- **Returns**: A dictionary containing the seat number.

### /tables/{table_id}/start

- **POST**: Starts a new hand on the table.
- **Returns**: A dictionary representing the table state.

### /tables/{table_id}/actions

- **POST**: Submits an action for a player.
- **Parameters**:
  - `seat`: An integer representing the player's seat.
  - `action`: A string representing the action.
  - `amount`: An optional integer representing the amount for bet or raise actions.
- **Returns**: A dictionary representing the table state.

### /tables/{table_id}/state

- **GET**: Retrieves the current state of the table.
- **Parameters**:
  - `seat`: An optional integer representing the viewer's seat.
- **Returns**: A dictionary representing the table state.

### /tables/{table_id}/ws

- **WebSocket**: Provides WebSocket support for real-time updates.
- **Parameters**:
  - `seat`: An optional integer representing the viewer's seat.

### /healthz

- **GET**: Checks the health of the server.
- **Returns**: A dictionary containing the status.

## Edge Cases and Implementation Choices

1. **Deck Initialization**: The deck is shuffled upon initialization, ensuring randomness.
2. **Blind Posting**: Blinds are posted in the correct order, with the small blind followed by the big blind.
3. **Action Validation**: Actions are validated based on the current state of the game, ensuring that illegal actions are rejected.
4. **Side Pot Allocation**: Side pots are allocated based on the contributions of players, ensuring that players with smaller contributions are not left out.
5. **Showdown**: The showdown is handled correctly, with the best hand winning the pots, and odd chips distributed to the first winning seat clockwise from the button.

This documentation provides a comprehensive overview of the Texas Hold'em poker server implementation, detailing its behavior, rules, and edge cases.