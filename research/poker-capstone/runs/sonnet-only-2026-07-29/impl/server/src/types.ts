// Protocol and domain types per stage2/design-server.md §2.1, §6.

export type Suit = "S" | "H" | "D" | "C";
// Rank: 2-10, then 11=J, 12=Q, 13=K, 14=A
export type Rank = 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14;

export interface Card {
  rank: Rank;
  suit: Suit;
}

export type Street = "PREFLOP" | "FLOP" | "TURN" | "RIVER" | "SHOWDOWN" | null;

export type SeatStatus =
  | "EMPTY"
  | "SITTING_OUT"
  | "ACTIVE"
  | "FOLDED"
  | "ALL_IN";

export interface Seat {
  seatNo: number;
  playerId: string | null;
  displayName: string | null;
  stack: number;
  betThisStreet: number;
  totalCommittedThisHand: number;
  status: SeatStatus;
  holeCards: Card[] | null; // server-internal only; never serialized wholesale
  consecutiveTimeouts: number;
}

export interface TableConfig {
  tableId: string;
  smallBlind: number;
  bigBlind: number;
  maxSeats: number; // 2-9
  minBuyIn: number;
  maxBuyIn: number;
  actionTimeoutMs: number;
}

export type WireAction = "FOLD" | "CHECK" | "CALL" | "RAISE";

export interface TableState {
  handSeq: number;
  street: Street;
  buttonSeat: number | null;
  seats: Seat[];
  actingSeat: number | null;
  currentBet: number;
  minRaiseSize: number;
  lastFullRaiseSeat: number | null;
  actedThisStreet: Set<number>;
  actionSeq: number;
  actByMs: number | null;
  board: Card[];
  potPreview: number; // sum of totalCommittedThisHand, for display before SETTLE builds real pots
  sbSeat: number | null;
  bbSeat: number | null;
  lastAggressorSeat: number | null; // last seat to bet/raise on the current street (for showdown reveal order)
}

// ---------- Client -> Server ----------

export interface JoinTableMsg {
  type: "JOIN_TABLE";
  tableId: string;
}
export interface SitMsg {
  type: "SIT";
  tableId: string;
  seatNo: number;
  buyIn: number;
  displayName?: string;
}
export interface SitOutMsg {
  type: "SIT_OUT";
  tableId: string;
}
export interface SitInMsg {
  type: "SIT_IN";
  tableId: string;
}
export interface ActionMsg {
  type: "ACTION";
  actionId: string;
  handSeq: number;
  action: WireAction;
  amount?: number;
}
export interface RequestSyncMsg {
  type: "REQUEST_SYNC";
  tableId: string;
}
export interface LeaveTableMsg {
  type: "LEAVE_TABLE";
  tableId: string;
}

export type ClientMessage =
  | JoinTableMsg
  | SitMsg
  | SitOutMsg
  | SitInMsg
  | ActionMsg
  | RequestSyncMsg
  | LeaveTableMsg;

// ---------- Server -> Client ----------

export type RejectReason =
  | "NOT_SEATED"
  | "NOT_ACCEPTING_ACTIONS"
  | "NOT_YOUR_TURN"
  | "ILLEGAL_ACTION"
  | "INVALID_AMOUNT"
  | "STALE_HAND";

export interface PublicSeatView {
  seatNo: number;
  playerId: string | null;
  displayName: string | null;
  stack: number;
  betThisStreet: number;
  status: SeatStatus;
}

export interface TableStateEvent {
  type: "TABLE_STATE";
  tableId: string;
  seats: PublicSeatView[];
  buttonSeat: number | null;
  config: {
    smallBlind: number;
    bigBlind: number;
    maxSeats: number;
    minBuyIn: number;
    maxBuyIn: number;
    actionTimeoutMs: number;
  };
}

export interface HandStartedEvent {
  type: "HAND_STARTED";
  handSeq: number;
  buttonSeat: number;
  sbSeat: number;
  bbSeat: number;
  sbAmount: number;
  bbAmount: number;
}

export interface HoleCardsEvent {
  type: "HOLE_CARDS";
  handSeq: number;
  cards: [Card, Card];
}

export interface TurnStartedEvent {
  type: "TURN_STARTED";
  handSeq: number;
  actionSeq: number;
  seat: number;
  legalActions: WireAction[];
  toCall: number;
  minRaiseTo: number | null;
  maxRaiseTo: number;
  actByMs: number;
}

export interface ActionAppliedEvent {
  type: "ACTION_APPLIED";
  handSeq: number;
  actionSeq: number;
  seat: number;
  action: WireAction;
  amount: number;
  potTotal: number;
  playerStack: number;
  playerBetThisStreet: number;
}

export interface ActionRejectedEvent {
  type: "ACTION_REJECTED";
  actionId: string | null;
  reason: RejectReason;
}

export interface StreetDealtEvent {
  type: "STREET_DEALT";
  handSeq: number;
  street: Exclude<Street, "SHOWDOWN" | null>;
  cards: Card[]; // cumulative board
}

export interface PotResult {
  amount: number;
  eligibleSeats: number[];
  winners: { seat: number; amount: number; handDescription: string }[];
}

export interface ShowdownEvent {
  type: "SHOWDOWN";
  handSeq: number;
  revealedHands: { seat: number; cards: Card[] }[];
  pots: PotResult[];
}

export interface HandCompleteEvent {
  type: "HAND_COMPLETE";
  handSeq: number;
  seats: { seatNo: number; stack: number }[];
}

export interface PlayerDisconnectedEvent {
  type: "PLAYER_DISCONNECTED";
  seatNo: number;
}
export interface PlayerReconnectedEvent {
  type: "PLAYER_RECONNECTED";
  seatNo: number;
}

export interface PlayerSatOutEvent {
  type: "PLAYER_SAT_OUT";
  seatNo: number;
  reason: "REQUESTED" | "TIMEOUT_LIMIT";
}

export interface StateSyncEvent {
  type: "STATE_SYNC";
  tableId: string;
  handSeq: number;
  actionSeq: number;
  street: Street;
  board: Card[];
  buttonSeat: number | null;
  actingSeat: number | null;
  actByMs: number | null;
  potTotal: number;
  seats: PublicSeatView[];
  mySeat: number | null;
  myHoleCards: Card[] | null;
  legalActions: WireAction[] | null;
  toCall: number | null;
  minRaiseTo: number | null;
  maxRaiseTo: number | null;
}

export interface ErrorEvent {
  type: "ERROR";
  code: string;
  message: string;
}

export type ServerEvent =
  | TableStateEvent
  | HandStartedEvent
  | HoleCardsEvent
  | TurnStartedEvent
  | ActionAppliedEvent
  | ActionRejectedEvent
  | StreetDealtEvent
  | ShowdownEvent
  | HandCompleteEvent
  | PlayerDisconnectedEvent
  | PlayerReconnectedEvent
  | PlayerSatOutEvent
  | StateSyncEvent
  | ErrorEvent;
