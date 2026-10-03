// Types mirroring the fixed REST response shape from
// docs/HARNESS-CONTRACT.md "Response shape". The client never invents its
// own notion of these fields; it is a verbatim passthrough per
// design-client.md.

export interface Card {
  rank: number; // 2-14, 14 = Ace
  suit: string; // any consistent string per HARNESS-CONTRACT; normalized
  // for display via normalizeSuit() in cards.ts
}

export type PlayerStatus = "active" | "folded" | "all_in" | "sitting_out";

export interface PlayerState {
  seat: number;
  stack: number;
  status: PlayerStatus;
  current_bet: number;
  total_committed: number;
  hole_cards: [Card, Card] | null;
}

export interface Pot {
  amount: number;
  eligible_seats: number[];
}

export interface ShowdownEntry {
  seat: number;
  hole_cards: [Card, Card];
  hand_category: string;
}

export type BettingRound =
  | "preflop"
  | "flop"
  | "turn"
  | "river"
  | "showdown"
  | null;

export interface TableState {
  table_id: string;
  small_blind: number;
  big_blind: number;
  button_seat: number | null;
  betting_round: BettingRound;
  community_cards: Card[];
  pots: Pot[];
  current_bet: number;
  min_raise: number;
  current_actor: number | null;
  hand_in_progress: boolean;
  last_action_log: string[];
  last_showdown: ShowdownEntry[];
  players: PlayerState[];
}

export type ActionType = "fold" | "check" | "call" | "bet" | "raise";

export interface ActionRequest {
  seat: number;
  action: ActionType;
  amount?: number;
}
