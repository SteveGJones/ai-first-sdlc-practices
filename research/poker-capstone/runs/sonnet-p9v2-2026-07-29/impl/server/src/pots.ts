// Side-pot construction — design-server.md §5.2, "layer by shortest
// stack": each iteration peels off the smallest remaining contribution as
// one pot layer shared by everyone who put in at least that much.

import { Pot } from './types';

export function buildPots(committed: Map<number, number>, folded: Set<number>): Pot[] {
  const remaining = new Map(committed);
  const pots: Pot[] = [];

  while ([...remaining.values()].some((amount) => amount > 0)) {
    const layerSeats = [...remaining.entries()]
      .filter(([, amt]) => amt > 0)
      .map(([seat]) => seat);
    const capAmount = Math.min(...layerSeats.map((s) => remaining.get(s)!));
    const potSize = capAmount * layerSeats.length;
    const eligible = layerSeats.filter((s) => !folded.has(s));
    pots.push({ amount: potSize, eligibleSeats: eligible.sort((a, b) => a - b) });
    for (const s of layerSeats) {
      remaining.set(s, remaining.get(s)! - capAmount);
    }
  }

  return pots;
}
