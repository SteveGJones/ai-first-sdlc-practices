// All-in and side pots — exact pot-building and payout algorithm per
// design-server.md §5.

import { compareHandValues, evaluateBestHand, type EvaluatedHand } from "./handEvaluator.js";
import type { Card } from "./types.js";

export interface Pot {
  amount: number;
  eligibleSeats: number[];
}

/**
 * §5.2 pot construction algorithm: "layer by shortest stack." Peels off the
 * smallest remaining contribution as one pot layer shared by everyone who
 * put in at least that much; a layer's eligibleSeats excludes anyone who
 * folded (they're still charged in, but can't win it).
 */
export function buildPots(committed: Map<number, number>, folded: Set<number>): Pot[] {
  const remaining = new Map(committed);
  const pots: Pot[] = [];

  while ([...remaining.values()].some((amt) => amt > 0)) {
    const layerSeats = [...remaining.entries()].filter(([, amt]) => amt > 0).map(([s]) => s);
    const capAmount = Math.min(...layerSeats.map((s) => remaining.get(s)!));
    const potSize = capAmount * layerSeats.length;
    const eligible = layerSeats.filter((s) => !folded.has(s));
    pots.push({ amount: potSize, eligibleSeats: eligible });
    for (const s of layerSeats) {
      remaining.set(s, remaining.get(s)! - capAmount);
    }
  }
  return pots;
}

export interface PotWinner {
  seat: number;
  amount: number;
  handDescription: string;
}

export interface AwardedPot extends Pot {
  winners: PotWinner[];
}

/**
 * §5.3 awarding each pot. `sevenCardsBySeat` supplies the 7 evaluable cards
 * (2 hole + 5 board) for every seat that might contest a pot; only looked up
 * when a pot has >1 eligible seat.
 */
export function awardPots(
  pots: Pot[],
  sevenCardsBySeat: Map<number, Card[]>,
  // Retained for interface symmetry with the design doc's odd-chip rule
  // description ("closest to, and clockwise of, buttonSeat"); the actual
  // ordering is precomputed by the caller into seatOrderClockwiseFromButton.
  _buttonSeat: number,
  seatOrderClockwiseFromButton: number[],
): { awarded: AwardedPot[]; stackDeltas: Map<number, number> } {
  const stackDeltas = new Map<number, number>();
  const evalCache = new Map<number, EvaluatedHand>();
  const evalFor = (seat: number): EvaluatedHand => {
    let cached = evalCache.get(seat);
    if (!cached) {
      cached = evaluateBestHand(sevenCardsBySeat.get(seat)!);
      evalCache.set(seat, cached);
    }
    return cached;
  };

  const awarded: AwardedPot[] = [];

  for (const pot of pots) {
    if (pot.amount === 0) continue;

    if (pot.eligibleSeats.length === 1) {
      const seat = pot.eligibleSeats[0]!;
      stackDeltas.set(seat, (stackDeltas.get(seat) ?? 0) + pot.amount);
      const desc = sevenCardsBySeat.has(seat) ? evalFor(seat).description : "uncontested";
      awarded.push({ ...pot, winners: [{ seat, amount: pot.amount, handDescription: desc }] });
      continue;
    }

    let bestValue = evalFor(pot.eligibleSeats[0]!).value;
    for (const seat of pot.eligibleSeats.slice(1)) {
      const v = evalFor(seat).value;
      if (compareHandValues(v, bestValue) > 0) bestValue = v;
    }
    const tiedWinners = pot.eligibleSeats.filter(
      (seat) => compareHandValues(evalFor(seat).value, bestValue) === 0,
    );

    // Odd-chip rule (§5.3.3): split evenly; remainder distributed one chip
    // at a time starting with the tied winner closest to (clockwise of)
    // buttonSeat.
    const base = Math.floor(pot.amount / tiedWinners.length);
    let remainder = pot.amount - base * tiedWinners.length;

    const ordered = seatOrderClockwiseFromButton.filter((s) => tiedWinners.includes(s));
    const winners: PotWinner[] = [];
    for (const seat of ordered) {
      let amount = base;
      if (remainder > 0) {
        amount += 1;
        remainder -= 1;
      }
      stackDeltas.set(seat, (stackDeltas.get(seat) ?? 0) + amount);
      winners.push({ seat, amount, handDescription: evalFor(seat).description });
    }
    awarded.push({ ...pot, winners });
  }

  return { awarded, stackDeltas };
}
