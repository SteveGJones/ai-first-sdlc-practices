// Deck construction and shuffling — design-server.md §4.1: a standard
// 52-card deck, shuffled server-side per hand with a cryptographically
// suitable RNG, never seeded from anything client-observable.

import { randomInt } from 'crypto';
import { Card, Suit } from './types';

const SUITS: Suit[] = ['s', 'h', 'd', 'c'];

export function buildDeck(): Card[] {
  const deck: Card[] = [];
  for (const suit of SUITS) {
    for (let rank = 2; rank <= 14; rank++) {
      deck.push({ rank, suit });
    }
  }
  return deck;
}

// Fisher-Yates shuffle using crypto.randomInt (not Math.random) so hand
// outcomes cannot be predicted or reproduced by an observer.
export function shuffle(deck: Card[]): Card[] {
  const cards = deck.slice();
  for (let i = cards.length - 1; i > 0; i--) {
    const j = randomInt(0, i + 1);
    [cards[i], cards[j]] = [cards[j], cards[i]];
  }
  return cards;
}

export function newShuffledDeck(): Card[] {
  return shuffle(buildDeck());
}
