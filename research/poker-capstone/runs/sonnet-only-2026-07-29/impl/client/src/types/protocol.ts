/**
 * Wire protocol types shared between client and server, as fixed by
 * stage2/design-server.md §6. The client never invents its own message
 * shapes — every type here mirrors the server design document exactly.
 */

export type Suit = "CLUBS" | "DIAMONDS" | "HEARTS" | "SPADES";
export type Rank =
  | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" | "T" | "J" | "Q" | "K" | "A";

export interface Card {
  rank: Rank;
  suit: Suit;
}

export type Street = "PREFLOP" | "FLOP" | "TURN" | "RIVER" | "SHOWDOWN";

export type SeatStatus = "EMPTY" | "SITTING_OUT" | "ACTIVE" | "FOLDED" | "ALL_IN";

export type ActionType = "FOLD" | "CHECK" | "CALL" | "RAISE";

export type RejectReason =
  | "NOT_SEATED"
  | "NOT_ACCEPTING_ACTIONS"
  | "NOT_YOUR_TURN"
  | "ILLEGAL_ACTION"
  | "INVALID_AMOUNT"
  | "STALE_HAND";

export type SatOutReason = "REQUESTED" | "TIMEOUT_LIMIT";

/** Per-recipient seat summary as carried on TABLE_STATE / STATE_SYNC. */
export interface SeatSummary {
  seatNo: number;
  playerId: string | null;
  displayName: string | null;
  stack: number;
  betThisStreet: number;
  status: SeatStatus;
}

export interface TableConfig {
  smallBlind: number;
  bigBlind: number;
  maxSeats: number;
  minBuyIn: number;
  maxBuyIn: number;
  actionTimeoutMs: number;
}

export interface PotView {
  amount: number;
  eligibleSeats: number[];
  winners?: Array<{ seat: number; amount: number; handDescription: string }>;
}

// ---------------------------------------------------------------------------
// Client -> Server
// ---------------------------------------------------------------------------

export interface JoinTableMessage {
  type: "JOIN_TABLE";
  tableId: string;
}

export interface SitMessage {
  type: "SIT";
  tableId: string;
  seatNo: number;
  buyIn: number;
}

export interface SitOutMessage {
  type: "SIT_OUT";
  tableId: string;
}

export interface SitInMessage {
  type: "SIT_IN";
  tableId: string;
}

export interface ActionMessage {
  type: "ACTION";
  actionId: string;
  handSeq: number;
  action: ActionType;
  amount?: number;
}

export interface RequestSyncMessage {
  type: "REQUEST_SYNC";
  tableId: string;
}

export interface LeaveTableMessage {
  type: "LEAVE_TABLE";
  tableId: string;
}

export type ClientMessage =
  | JoinTableMessage
  | SitMessage
  | SitOutMessage
  | SitInMessage
  | ActionMessage
  | RequestSyncMessage
  | LeaveTableMessage;

// ---------------------------------------------------------------------------
// Server -> Client
// ---------------------------------------------------------------------------

export interface TableStateEvent {
  type: "TABLE_STATE";
  seats: SeatSummary[];
  buttonSeat: number;
  config: TableConfig;
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
  cards: [Card, Card];
}

export interface TurnStartedEvent {
  type: "TURN_STARTED";
  handSeq: number;
  actionSeq: number;
  seat: number;
  legalActions: ActionType[];
  toCall: number;
  minRaiseTo: number;
  maxRaiseTo: number;
  actByMs: number;
}

export interface ActionAppliedEvent {
  type: "ACTION_APPLIED";
  handSeq: number;
  actionSeq: number;
  seat: number;
  action: ActionType;
  amount: number;
  potTotal: number;
  playerStack: number;
  playerBetThisStreet: number;
}

export interface ActionRejectedEvent {
  type: "ACTION_REJECTED";
  actionId: string;
  reason: RejectReason;
}

export interface StreetDealtEvent {
  type: "STREET_DEALT";
  handSeq: number;
  street: Street;
  cards: Card[];
}

export interface ShowdownEvent {
  type: "SHOWDOWN";
  handSeq: number;
  revealedHands: Array<{ seat: number; cards: [Card, Card] }>;
  pots: Array<{
    amount: number;
    eligibleSeats: number[];
    winners: Array<{ seat: number; amount: number; handDescription: string }>;
  }>;
}

export interface HandCompleteEvent {
  type: "HAND_COMPLETE";
  handSeq: number;
  seats: Array<{ seatNo: number; stack: number }>;
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
  reason: SatOutReason;
}

export interface StateSyncEvent {
  type: "STATE_SYNC";
  handSeq: number;
  actionSeq: number;
  street: Street | null;
  board: Card[];
  potTotal: number;
  seats: SeatSummary[];
  buttonSeat: number;
  actingSeat: number | null;
  actByMs: number | null;
  legalActions?: ActionType[];
  toCall?: number;
  minRaiseTo?: number;
  maxRaiseTo?: number;
  myHoleCards: [Card, Card] | null;
  mySeat: number | null;
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

/** Events which carry an actionSeq usable for gap detection (§6.3 / client §2.2). */
export function hasActionSeq(
  event: ServerEvent
): event is (TurnStartedEvent | ActionAppliedEvent | StateSyncEvent) & {
  handSeq: number;
  actionSeq: number;
} {
  return (
    event.type === "TURN_STARTED" ||
    event.type === "ACTION_APPLIED" ||
    event.type === "STATE_SYNC"
  );
}
