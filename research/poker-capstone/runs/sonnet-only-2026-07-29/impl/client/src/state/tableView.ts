/**
 * TableView: the client's single authoritative local store (design-client.md §1).
 *
 * It is a pure projection of the last-received server messages, rebuilt
 * only via applyServerEvent(). No other code path may mutate it.
 */

import type {
  ActionType,
  Card,
  SeatSummary,
  ServerEvent,
  Street,
  TableConfig,
} from "../types/protocol";

export type ConnectionStatus = "CONNECTED" | "RECONNECTING" | "DESYNCED";

export interface PendingAction {
  actionId: string;
  action: ActionType;
  amount?: number;
}

export interface ShowdownView {
  revealedHands: Array<{ seat: number; cards: [Card, Card] }>;
  pots: Array<{
    amount: number;
    eligibleSeats: number[];
    winners: Array<{ seat: number; amount: number; handDescription: string }>;
  }>;
}

export interface SeatView extends SeatSummary {
  isMe: boolean;
}

export interface TableView {
  tableId: string | null;
  mySeat: number | null;
  config: TableConfig | null;

  handSeq: number;
  actionSeq: number;
  street: Street | null;
  board: Card[];
  potTotal: number;
  seats: SeatView[];
  buttonSeat: number | null;

  actingSeat: number | null;
  actByMs: number | null;
  legalActionsForMe: ActionType[];
  toCall: number;
  minRaiseTo: number;
  maxRaiseTo: number;

  myHoleCards: [Card, Card] | null;
  showdown: ShowdownView | null;
  pendingAction: PendingAction | null;
  connectionStatus: ConnectionStatus;

  lastRejection: { reason: string; at: number } | null;
  lastError: { code: string; message: string; at: number } | null;
}

export function createInitialTableView(tableId: string | null = null): TableView {
  return {
    tableId,
    mySeat: null,
    config: null,
    handSeq: 0,
    actionSeq: 0,
    street: null,
    board: [],
    potTotal: 0,
    seats: [],
    buttonSeat: null,
    actingSeat: null,
    actByMs: null,
    legalActionsForMe: [],
    toCall: 0,
    minRaiseTo: 0,
    maxRaiseTo: 0,
    myHoleCards: null,
    showdown: null,
    pendingAction: null,
    connectionStatus: "CONNECTED",
    lastRejection: null,
    lastError: null,
  };
}

function withMe(seats: SeatSummary[], mySeat: number | null): SeatView[] {
  return seats.map((s) => ({ ...s, isMe: mySeat !== null && s.seatNo === mySeat }));
}

function clearActingFieldsIfNotMe(view: TableView): void {
  view.legalActionsForMe = [];
  view.toCall = 0;
  view.minRaiseTo = 0;
  view.maxRaiseTo = 0;
}

/**
 * The single reducer that may ever mutate TableView, per design-client.md §1.
 * Returns a new TableView; never mutates the input in place.
 */
export function applyServerEvent(prev: TableView, event: ServerEvent): TableView {
  const next: TableView = { ...prev, seats: prev.seats.map((s) => ({ ...s })) };

  switch (event.type) {
    case "TABLE_STATE": {
      next.seats = withMe(event.seats, next.mySeat);
      next.buttonSeat = event.buttonSeat;
      next.config = event.config;
      return next;
    }

    case "HAND_STARTED": {
      next.handSeq = event.handSeq;
      next.actionSeq = 0;
      next.board = [];
      next.potTotal = 0;
      next.buttonSeat = event.buttonSeat;
      next.showdown = null;
      next.myHoleCards = null;
      next.actingSeat = null;
      next.actByMs = null;
      clearActingFieldsIfNotMe(next);
      next.seats = next.seats.map((s) => ({
        ...s,
        betThisStreet: 0,
        status: s.status === "EMPTY" || s.status === "SITTING_OUT" ? s.status : "ACTIVE",
      }));
      return next;
    }

    case "HOLE_CARDS": {
      // This event is only ever delivered to its owning connection.
      next.myHoleCards = event.cards;
      return next;
    }

    case "TURN_STARTED": {
      next.handSeq = event.handSeq;
      next.actionSeq = event.actionSeq;
      next.actingSeat = event.seat;
      next.actByMs = event.actByMs;
      if (next.mySeat !== null && event.seat === next.mySeat) {
        next.legalActionsForMe = event.legalActions;
        next.toCall = event.toCall;
        next.minRaiseTo = event.minRaiseTo;
        next.maxRaiseTo = event.maxRaiseTo;
      } else {
        clearActingFieldsIfNotMe(next);
      }
      return next;
    }

    case "ACTION_APPLIED": {
      next.handSeq = event.handSeq;
      next.actionSeq = event.actionSeq;
      next.potTotal = event.potTotal;
      next.seats = next.seats.map((s) =>
        s.seatNo === event.seat
          ? { ...s, stack: event.playerStack, betThisStreet: event.playerBetThisStreet }
          : s
      );
      if (
        next.mySeat !== null &&
        event.seat === next.mySeat &&
        next.pendingAction !== null &&
        next.pendingAction.action === event.action &&
        (next.pendingAction.amount ?? undefined) === (event.amount ?? undefined)
      ) {
        next.pendingAction = null;
      }
      return next;
    }

    case "ACTION_REJECTED": {
      if (next.pendingAction !== null && next.pendingAction.actionId === event.actionId) {
        next.pendingAction = null;
      }
      next.lastRejection = { reason: event.reason, at: Date.now() };
      return next;
    }

    case "STREET_DEALT": {
      next.handSeq = event.handSeq;
      next.street = event.street;
      next.board = event.cards;
      next.seats = next.seats.map((s) => ({ ...s, betThisStreet: 0 }));
      return next;
    }

    case "SHOWDOWN": {
      next.handSeq = event.handSeq;
      next.street = "SHOWDOWN";
      next.showdown = { revealedHands: event.revealedHands, pots: event.pots };
      next.actingSeat = null;
      next.actByMs = null;
      clearActingFieldsIfNotMe(next);
      return next;
    }

    case "HAND_COMPLETE": {
      next.handSeq = event.handSeq;
      const byNo = new Map(event.seats.map((s) => [s.seatNo, s.stack]));
      next.seats = next.seats.map((s) =>
        byNo.has(s.seatNo) ? { ...s, stack: byNo.get(s.seatNo)! } : s
      );
      // showdown stays populated for a short presentational period; the UI
      // clears it itself on the next HAND_STARTED (design-client.md §2.1).
      return next;
    }

    case "PLAYER_DISCONNECTED": {
      next.seats = next.seats.map((s) =>
        s.seatNo === event.seatNo ? { ...s, status: s.status } : s
      );
      return next;
    }

    case "PLAYER_RECONNECTED": {
      return next;
    }

    case "PLAYER_SAT_OUT": {
      next.seats = next.seats.map((s) =>
        s.seatNo === event.seatNo ? { ...s, status: "SITTING_OUT" } : s
      );
      return next;
    }

    case "STATE_SYNC": {
      // Discard the entire current TableView and rebuild from the snapshot
      // (design-client.md §2.1, §2.2) — the only "replace everything" case.
      const rebuilt = createInitialTableView(next.tableId);
      rebuilt.mySeat = event.mySeat ?? next.mySeat;
      rebuilt.config = next.config;
      rebuilt.handSeq = event.handSeq;
      rebuilt.actionSeq = event.actionSeq;
      rebuilt.street = event.street;
      rebuilt.board = event.board;
      rebuilt.potTotal = event.potTotal;
      rebuilt.buttonSeat = event.buttonSeat;
      rebuilt.actingSeat = event.actingSeat;
      rebuilt.actByMs = event.actByMs;
      rebuilt.myHoleCards = event.myHoleCards;
      rebuilt.seats = withMe(event.seats, rebuilt.mySeat);
      if (rebuilt.mySeat !== null && event.actingSeat === rebuilt.mySeat) {
        rebuilt.legalActionsForMe = event.legalActions ?? [];
        rebuilt.toCall = event.toCall ?? 0;
        rebuilt.minRaiseTo = event.minRaiseTo ?? 0;
        rebuilt.maxRaiseTo = event.maxRaiseTo ?? 0;
      }
      rebuilt.connectionStatus = "CONNECTED";
      return rebuilt;
    }

    case "ERROR": {
      next.lastError = { code: event.code, message: event.message, at: Date.now() };
      return next;
    }

    default: {
      const _exhaustive: never = event;
      return _exhaustive;
    }
  }
}

/** Set this client's own seat number (learned out-of-band, e.g. from a SIT ack or STATE_SYNC). */
export function withMySeat(view: TableView, mySeat: number | null): TableView {
  return {
    ...view,
    mySeat,
    seats: withMe(view.seats, mySeat),
  };
}
