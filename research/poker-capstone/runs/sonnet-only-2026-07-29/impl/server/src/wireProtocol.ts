// Translates the engine's internal Card representation
// (Suit "S"|"H"|"D"|"C", Rank 2-14) into the wire format the client
// (impl/client/src/types/protocol.ts) actually expects on the JSON wire
// (Suit "CLUBS"|"DIAMONDS"|"HEARTS"|"SPADES", Rank "2".."9"|"T"|"J"|"Q"|"K"|"A").
//
// The design doc (§4.1) deliberately leaves the exact Card encoding to the
// implementer; this module is the single seam where that choice is made,
// so the engine can keep using compact internal types everywhere else.

import type { Card, ServerEvent } from "./types.js";

const SUIT_WIRE: Record<Card["suit"], string> = {
  S: "SPADES",
  H: "HEARTS",
  D: "DIAMONDS",
  C: "CLUBS",
};

const RANK_WIRE: Record<number, string> = {
  2: "2",
  3: "3",
  4: "4",
  5: "5",
  6: "6",
  7: "7",
  8: "8",
  9: "9",
  10: "T",
  11: "J",
  12: "Q",
  13: "K",
  14: "A",
};

function wireCard(card: Card): { rank: string; suit: string } {
  return { rank: RANK_WIRE[card.rank]!, suit: SUIT_WIRE[card.suit] };
}

function wireCards(cards: Card[]): { rank: string; suit: string }[] {
  return cards.map(wireCard);
}

/** Deep-converts every Card-bearing field of a ServerEvent to wire format. */
export function toWireEvent(event: ServerEvent): unknown {
  switch (event.type) {
    case "HOLE_CARDS":
      return { ...event, cards: wireCards(event.cards) };
    case "STREET_DEALT":
      return { ...event, cards: wireCards(event.cards) };
    case "SHOWDOWN":
      return {
        ...event,
        revealedHands: event.revealedHands.map((h) => ({ seat: h.seat, cards: wireCards(h.cards) })),
      };
    case "STATE_SYNC":
      return {
        ...event,
        board: wireCards(event.board),
        myHoleCards: event.myHoleCards ? wireCards(event.myHoleCards) : null,
      };
    default:
      return event;
  }
}
