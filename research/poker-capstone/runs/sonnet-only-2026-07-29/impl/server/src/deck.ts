import { randomInt } from "node:crypto";
import type { Card, Rank, Suit } from "./types.js";

const SUITS: Suit[] = ["S", "H", "D", "C"];
const RANKS: Rank[] = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14];

/** Builds a fresh, ordered 52-card deck. */
export function freshDeck(): Card[] {
  const deck: Card[] = [];
  for (const suit of SUITS) {
    for (const rank of RANKS) {
      deck.push({ rank, suit });
    }
  }
  return deck;
}

/**
 * Fisher-Yates shuffle using a cryptographically-suitable RNG
 * (node:crypto randomInt), per design-server.md §4.1: "shuffled server-side
 * per hand using a cryptographically-suitable RNG (never seeded from
 * anything client-observable)".
 */
export function shuffle(deck: Card[]): Card[] {
  const result = deck.slice();
  for (let i = result.length - 1; i > 0; i--) {
    const j = randomInt(0, i + 1);
    const tmp = result[i]!;
    result[i] = result[j]!;
    result[j] = tmp;
  }
  return result;
}

export function newShuffledDeck(): Card[] {
  return shuffle(freshDeck());
}
