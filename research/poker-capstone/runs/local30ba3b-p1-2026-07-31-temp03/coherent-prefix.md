# Texas Hold'em Poker Server Implementation Documentation

## Overview

This implementation implements a Texas Hold'em poker game server with the following components:

1. **Data Models**: `Card`, `Deck`, `Player`, `Pot`, and `Table`
2. **Game Logic**: Hand evaluation, betting logic, and hand management
3. **API Layer**: REST and WebSocket endpoints for table management and gameplay

## Data Models

### Card

- Represents a single playing card with rank (2-14) and suit (s, h, d, c)
- Rank mapping: 2-14 (2, 3, ..., 10, J, Q, K, A)
- Suit: one of "s", "h", "d", "c" (spades, hearts, diamonds, clubs)
- String representation format: "rank suit" (e.g., "A s", "K h")

### Deck

- Contains 52 cards (52 cards in standard deck)
- Cards are shuffled using the provided random number generator or default Python random
- Cards are dealt in order from the top of the deck

### Player

- Represents a player at the table with seat number, name, stack, and game state
- `status` can be one of:
  - ACTIVE: Player can act in current betting round
  - FOLDED: Player folded and cannot act further in this hand
  - ALL_IN: Player has no chips left and can only call or fold
  - SITTING_OUT: Player is not participating in current hand
- `hole_cards` is None until dealt cards are dealt
- `current_bet` is the amount bet in current betting round
- `total_committed` is the total amount committed to the pot in this hand
- `has_acted_this_round` tracks whether player has acted in current betting round

### Pot

- Represents pot information with amount and eligible seats
- Pot is created for each pot level in the pot allocation algorithm

### Table

- Contains table state including players, community cards, pot information, and game state
- `hand_in_progress` indicates whether a hand is currently being played
- `betting_round` indicates the current stage of the hand (preflop, flop, turn, river, or showdown)
- `current_actor` is the seat number of the player whose turn it is to act
- `last_aggressor` is the seat of the last player who raised

## Game Logic

### Hand Evaluation

The implementation uses the standard Texas Hold'em hand evaluation rules:

1. **Hand evaluation order**: High card, one pair, two pair, three of a kind, straight, flush, full house, four of a kind, straight flush

2. **Hand evaluation rules**:
   - A straight can be formed with A-2-3-4-5 (wheel)
   - A flush is five cards of the same suit
   - A straight flush is a straight with all cards of the same suit
   - A straight flush beats a flush, flush beats a straight, etc.

3. **Hand evaluation tie-breaking rules**:
   - High card: highest card wins
   - One pair: higher pair wins
   - Two pair: higher pair wins, then higher kicker
   - Three of a kind: higher three of a kind wins
   - Straight: higher high card wins
   - Flush: higher high card wins
   - Full house: higher three of a kind wins, then higher pair wins
   - Four of a kind: higher four of a kind wins
   - Straight flush: higher high card wins

### Betting Logic

#### Blinds

- Small blind is half the big blind amount
- Big blind is the full blind amount
- Small blind is posted by the seat to the left of the button
- Big blind is posted by the seat to the right of the button

#### Betting Rounds

1. **Preflop**: Players receive two hole cards each
2. **F Flop**: Three community cards are dealt face-up
3. **Turn**: One additional community card is dealt
4. **River**: One additional community card is dealt
5. **Showdown**: All remaining players reveal their hands

#### Betting Rules

- Betting rounds are completed when all active players have acted
- Players can fold, check, call, bet, or raise
- Minimum raise is the big blind amount
- Minimum bet is the big blind amount
- Players can bet or raise any amount up to their stack
- Players can call any amount up to the current bet
- Players can fold to fold out of the hand

#### Pot Allocation

- Pot allocation follows the standard pot allocation algorithm:
  - Pot is created for each pot level in the pot allocation algorithm