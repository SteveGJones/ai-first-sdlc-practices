// Poker Capstone — Stage 3 server implementation.
// Types follow design-server.md §2.1 (TableState / Seat) plus the fields
// needed to satisfy HARNESS-CONTRACT.md's response shape.

export type Suit = 's' | 'h' | 'd' | 'c';

export interface Card {
  rank: number; // 2..14, 14 = Ace
  suit: Suit;
}

export type SeatStatus = 'EMPTY' | 'SITTING_OUT' | 'ACTIVE' | 'FOLDED' | 'ALL_IN';

export type Street = 'PREFLOP' | 'FLOP' | 'TURN' | 'RIVER' | 'SHOWDOWN';

export interface Seat {
  seatNo: number;
  playerId: string | null;
  displayName: string | null;
  stack: number;
  betThisStreet: number;
  totalCommittedThisHand: number;
  status: SeatStatus;
  holeCards: Card[] | null;
}

export interface Pot {
  amount: number;
  eligibleSeats: number[];
}

export interface ShowdownEntry {
  seat: number;
  holeCards: Card[];
  handCategory: string;
}

export class PokerError extends Error {
  code: string;
  httpStatus: number;

  constructor(code: string, message: string, httpStatus = 400) {
    super(message);
    this.code = code;
    this.httpStatus = httpStatus;
  }
}
