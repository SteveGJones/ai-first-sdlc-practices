// Hand evaluation ("the judge") — design-server.md §4.2.
//
// For a 7-card set, enumerate all C(7,5)=21 five-card combinations, score
// each as a comparable (category, tiebreak...) tuple, and take the max.
// Straight-flush/straight recognizes the wheel (A-2-3-4-5, ace low).
// Chosen for design-doc clarity over a lookup-table evaluator, per §4.2 —
// 21 combinations x <=9 players once per hand is trivial cost.

import { Card } from './types';

export interface ComparableHandValue {
  category: number; // 0..8, higher is better
  tiebreak: number[]; // descending significance
  categoryName: string;
}

const CATEGORY_NAMES = [
  'high_card',
  'one_pair',
  'two_pair',
  'three_of_a_kind',
  'straight',
  'flush',
  'full_house',
  'four_of_a_kind',
  'straight_flush',
];

function combinations<T>(items: T[], k: number): T[][] {
  const results: T[][] = [];
  const combo: T[] = [];
  function recurse(start: number) {
    if (combo.length === k) {
      results.push(combo.slice());
      return;
    }
    for (let i = start; i < items.length; i++) {
      combo.push(items[i]);
      recurse(i + 1);
      combo.pop();
    }
  }
  recurse(0);
  return results;
}

function scoreFiveCardHand(cards: Card[]): ComparableHandValue {
  const sortedRanksDesc = cards.map((c) => c.rank).sort((a, b) => b - a);
  const uniqueRanksDesc = [...new Set(sortedRanksDesc)];

  const isFlush = new Set(cards.map((c) => c.suit)).size === 1;

  let straightHigh: number | null = null;
  if (uniqueRanksDesc.length === 5) {
    if (uniqueRanksDesc[0] - uniqueRanksDesc[4] === 4) {
      straightHigh = uniqueRanksDesc[0];
    } else if (uniqueRanksDesc.join(',') === '14,5,4,3,2') {
      // the wheel: A-2-3-4-5, ace counts low, straight value is 5-high
      straightHigh = 5;
    }
  }

  const counts = new Map<number, number>();
  for (const r of sortedRanksDesc) {
    counts.set(r, (counts.get(r) ?? 0) + 1);
  }
  const groups = [...counts.entries()]
    .map(([rank, count]) => ({ rank, count }))
    .sort((a, b) => b.count - a.count || b.rank - a.rank);

  if (straightHigh !== null && isFlush) {
    return { category: 8, tiebreak: [straightHigh], categoryName: CATEGORY_NAMES[8] };
  }
  if (groups[0].count === 4) {
    return {
      category: 7,
      tiebreak: [groups[0].rank, groups[1].rank],
      categoryName: CATEGORY_NAMES[7],
    };
  }
  if (groups[0].count === 3 && groups[1].count === 2) {
    return {
      category: 6,
      tiebreak: [groups[0].rank, groups[1].rank],
      categoryName: CATEGORY_NAMES[6],
    };
  }
  if (isFlush) {
    return { category: 5, tiebreak: sortedRanksDesc, categoryName: CATEGORY_NAMES[5] };
  }
  if (straightHigh !== null) {
    return { category: 4, tiebreak: [straightHigh], categoryName: CATEGORY_NAMES[4] };
  }
  if (groups[0].count === 3) {
    const kickers = groups.slice(1).map((g) => g.rank);
    return {
      category: 3,
      tiebreak: [groups[0].rank, ...kickers],
      categoryName: CATEGORY_NAMES[3],
    };
  }
  if (groups[0].count === 2 && groups[1].count === 2) {
    const highPair = Math.max(groups[0].rank, groups[1].rank);
    const lowPair = Math.min(groups[0].rank, groups[1].rank);
    return {
      category: 2,
      tiebreak: [highPair, lowPair, groups[2].rank],
      categoryName: CATEGORY_NAMES[2],
    };
  }
  if (groups[0].count === 2) {
    const kickers = groups.slice(1).map((g) => g.rank);
    return {
      category: 1,
      tiebreak: [groups[0].rank, ...kickers],
      categoryName: CATEGORY_NAMES[1],
    };
  }
  return { category: 0, tiebreak: sortedRanksDesc, categoryName: CATEGORY_NAMES[0] };
}

export function compareHandValues(a: ComparableHandValue, b: ComparableHandValue): number {
  if (a.category !== b.category) return a.category - b.category;
  const len = Math.max(a.tiebreak.length, b.tiebreak.length);
  for (let i = 0; i < len; i++) {
    const av = a.tiebreak[i] ?? 0;
    const bv = b.tiebreak[i] ?? 0;
    if (av !== bv) return av - bv;
  }
  return 0;
}

export function evaluateBestHand(sevenCards: Card[]): ComparableHandValue {
  if (sevenCards.length < 5) {
    throw new Error('evaluateBestHand requires at least 5 cards');
  }
  const fiveCardCombos = combinations(sevenCards, 5);
  let best = scoreFiveCardHand(fiveCardCombos[0]);
  for (let i = 1; i < fiveCardCombos.length; i++) {
    const candidate = scoreFiveCardHand(fiveCardCombos[i]);
    if (compareHandValues(candidate, best) > 0) {
      best = candidate;
    }
  }
  return best;
}
