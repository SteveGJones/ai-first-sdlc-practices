// Hand evaluation ("the judge") per design-server.md §4.2.
//
// Evaluates the best 5-card hand out of a seat's 7 available cards (2 hole +
// 5 board) by enumerating all C(7,5) = 21 combinations, scoring each as a
// comparable tuple (category, tiebreak1, tiebreak2, ...), and taking the max
// by lexicographic tuple comparison. This is the "clarity over raw
// performance" evaluator the design doc calls for; it can be swapped for a
// lookup-table evaluator later behind the same evaluateBestHand() interface.

import type { Card, Rank } from "./types.js";

export const HandCategory = {
  HIGH_CARD: 0,
  ONE_PAIR: 1,
  TWO_PAIR: 2,
  THREE_OF_A_KIND: 3,
  STRAIGHT: 4,
  FLUSH: 5,
  FULL_HOUSE: 6,
  FOUR_OF_A_KIND: 7,
  STRAIGHT_FLUSH: 8,
} as const;

export type HandCategoryValue = (typeof HandCategory)[keyof typeof HandCategory];

const CATEGORY_NAMES: Record<HandCategoryValue, string> = {
  0: "High Card",
  1: "One Pair",
  2: "Two Pair",
  3: "Three of a Kind",
  4: "Straight",
  5: "Flush",
  6: "Full House",
  7: "Four of a Kind",
  8: "Straight Flush",
};

/** Comparable value: [category, tiebreak1, tiebreak2, ...] descending significance. */
export type ComparableHandValue = number[];

export interface EvaluatedHand {
  value: ComparableHandValue;
  bestFive: Card[];
  description: string;
  /** Bare category label (e.g. "Straight", "Two Pair") — no kicker detail. */
  categoryName: string;
}

function combinations<T>(items: T[], k: number): T[][] {
  const results: T[][] = [];
  const combo: T[] = [];
  function recurse(start: number): void {
    if (combo.length === k) {
      results.push(combo.slice());
      return;
    }
    for (let i = start; i < items.length; i++) {
      combo.push(items[i]!);
      recurse(i + 1);
      combo.pop();
    }
  }
  recurse(0);
  return results;
}

/** Detects a straight in a set of unique-descending ranks (Ace counted high or low). */
function straightHigh(uniqueDescRanks: Rank[]): number | null {
  const set = new Set<number>(uniqueDescRanks);
  // Ace-low straight ("the wheel"): A-2-3-4-5, straight value is 5-high.
  const hasWheel = [14, 5, 4, 3, 2].every((r) => set.has(r));
  let best: number | null = hasWheel ? 5 : null;

  for (const high of uniqueDescRanks) {
    if (high < 6) continue; // can't be a normal (non-wheel) straight below 6-high
    let consecutive = true;
    for (let r = high; r > high - 5; r--) {
      if (!set.has(r)) {
        consecutive = false;
        break;
      }
    }
    if (consecutive && (best === null || high > best)) {
      best = high;
    }
  }
  return best;
}

function scoreFive(cards: Card[]): { value: ComparableHandValue; description: string } {
  const ranksDesc = cards.map((c) => c.rank).sort((a, b) => b - a);
  const suits = cards.map((c) => c.suit);
  const isFlush = suits.every((s) => s === suits[0]);

  const uniqueRanksDesc = [...new Set(ranksDesc)].sort((a, b) => b - a) as Rank[];
  const straightHighCard = straightHigh(uniqueRanksDesc);

  const rankCounts = new Map<number, number>();
  for (const r of ranksDesc) rankCounts.set(r, (rankCounts.get(r) ?? 0) + 1);
  // groups sorted by (count desc, rank desc)
  const groups = [...rankCounts.entries()].sort((a, b) => {
    if (b[1] !== a[1]) return b[1] - a[1];
    return b[0] - a[0];
  });
  const counts = groups.map((g) => g[1]);

  if (isFlush && straightHighCard !== null) {
    return {
      value: [HandCategory.STRAIGHT_FLUSH, straightHighCard],
      description: `${CATEGORY_NAMES[8]}, ${straightHighCard}-high`,
    };
  }
  if (counts[0] === 4) {
    const quad = groups[0]![0];
    const kicker = groups[1]![0];
    return {
      value: [HandCategory.FOUR_OF_A_KIND, quad, kicker],
      description: `${CATEGORY_NAMES[7]}, ${quad}s`,
    };
  }
  if (counts[0] === 3 && counts[1] === 2) {
    const trips = groups[0]![0];
    const pair = groups[1]![0];
    return {
      value: [HandCategory.FULL_HOUSE, trips, pair],
      description: `${CATEGORY_NAMES[6]}, ${trips}s over ${pair}s`,
    };
  }
  if (isFlush) {
    return {
      value: [HandCategory.FLUSH, ...ranksDesc],
      description: `${CATEGORY_NAMES[5]}, ${ranksDesc[0]}-high`,
    };
  }
  if (straightHighCard !== null) {
    return {
      value: [HandCategory.STRAIGHT, straightHighCard],
      description: `${CATEGORY_NAMES[4]}, ${straightHighCard}-high`,
    };
  }
  if (counts[0] === 3) {
    const trips = groups[0]![0];
    const kickers = groups.slice(1).map((g) => g[0]);
    return {
      value: [HandCategory.THREE_OF_A_KIND, trips, ...kickers],
      description: `${CATEGORY_NAMES[3]}, ${trips}s`,
    };
  }
  if (counts[0] === 2 && counts[1] === 2) {
    const highPair = Math.max(groups[0]![0], groups[1]![0]);
    const lowPair = Math.min(groups[0]![0], groups[1]![0]);
    const kicker = groups[2]![0];
    return {
      value: [HandCategory.TWO_PAIR, highPair, lowPair, kicker],
      description: `${CATEGORY_NAMES[2]}, ${highPair}s and ${lowPair}s`,
    };
  }
  if (counts[0] === 2) {
    const pair = groups[0]![0];
    const kickers = groups.slice(1).map((g) => g[0]);
    return {
      value: [HandCategory.ONE_PAIR, pair, ...kickers],
      description: `${CATEGORY_NAMES[1]}, ${pair}s`,
    };
  }
  return {
    value: [HandCategory.HIGH_CARD, ...ranksDesc],
    description: `${CATEGORY_NAMES[0]}, ${ranksDesc[0]}-high`,
  };
}

function compareValues(a: ComparableHandValue, b: ComparableHandValue): number {
  const len = Math.max(a.length, b.length);
  for (let i = 0; i < len; i++) {
    const av = a[i] ?? 0;
    const bv = b[i] ?? 0;
    if (av !== bv) return av - bv;
  }
  return 0;
}

/** Evaluates the best 5-card hand out of exactly 7 cards. */
export function evaluateBestHand(sevenCards: Card[]): EvaluatedHand {
  if (sevenCards.length !== 7) {
    throw new Error(`evaluateBestHand requires exactly 7 cards, got ${sevenCards.length}`);
  }
  let best: { value: ComparableHandValue; description: string; five: Card[] } | null = null;
  for (const five of combinations(sevenCards, 5)) {
    const scored = scoreFive(five);
    if (best === null || compareValues(scored.value, best.value) > 0) {
      best = { ...scored, five };
    }
  }
  return {
    value: best!.value,
    bestFive: best!.five,
    description: best!.description,
    categoryName: CATEGORY_NAMES[best!.value[0] as HandCategoryValue],
  };
}

/** Compares two evaluated hand values; >0 if a beats b, <0 if b beats a, 0 if tied. */
export function compareHandValues(a: ComparableHandValue, b: ComparableHandValue): number {
  return compareValues(a, b);
}
