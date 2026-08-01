// Game Engine: per-table authoritative state machine implementing
// design-server.md §1 (hand lifecycle), §2 (turn enforcement), §3 (blinds/
// button), §4 (dealing/evaluation), §5 (pots/payout).
//
// One instance per table. All public methods run synchronously to
// completion (no awaits mid-mutation), which is what gives the "processes
// its inbound queue strictly one message at a time" guarantee from §2.3.1 —
// Node's single-threaded event loop means a synchronous call cannot be
// interleaved with another synchronous call.

import { randomInt, randomUUID } from "node:crypto";
import { newShuffledDeck } from "./deck.js";
import { evaluateBestHand } from "./handEvaluator.js";
import { awardPots, buildPots } from "./pots.js";
import type {
  Card,
  RejectReason,
  Seat,
  ServerEvent,
  TableConfig,
  TableState,
  WireAction,
} from "./types.js";

export interface EngineIO {
  /** Broadcasts an event to every connected seat/observer at the table. */
  broadcastToTable(event: ServerEvent): void;
  /** Sends an event only to the connection currently occupying this seat, if any. */
  sendToSeat(seatNo: number, event: ServerEvent): void;
}

interface ActionRecord {
  actionId: string;
  result: { type: "APPLIED" } | { type: "REJECTED"; reason: RejectReason };
}

export class GameEngine {
  readonly config: TableConfig;
  readonly state: TableState;
  private readonly io: EngineIO;
  private deck: Card[] = [];
  /** actionId ledger per seat, cleared each hand — §2.7 idempotency. */
  private appliedActions = new Map<number, ActionRecord[]>();
  private pendingSitOut = new Set<number>();
  private pendingLeave = new Set<number>();
  private turnTimer: NodeJS.Timeout | null = null;
  /** Populated at each SETTLE; read back by the REST facade's GET /state. */
  private lastShowdown: { seat: number; holeCards: Card[]; handCategory: string }[] = [];

  constructor(config: TableConfig, io: EngineIO) {
    this.config = config;
    this.io = io;
    this.state = {
      handSeq: 0,
      street: null,
      buttonSeat: null,
      seats: Array.from({ length: config.maxSeats }, (_, seatNo) => emptySeat(seatNo)),
      actingSeat: null,
      currentBet: 0,
      minRaiseSize: config.bigBlind,
      lastFullRaiseSeat: null,
      actedThisStreet: new Set<number>(),
      actionSeq: 0,
      actByMs: null,
      board: [],
      potPreview: 0,
      sbSeat: null,
      bbSeat: null,
      lastAggressorSeat: null,
    };
  }

  // ---------------------------------------------------------------------
  // Public API surface used by TableManager
  // ---------------------------------------------------------------------

  getLastShowdown(): { seat: number; holeCards: Card[]; handCategory: string }[] {
    return this.lastShowdown;
  }

  publicTableStateEvent(): ServerEvent {
    return {
      type: "TABLE_STATE",
      tableId: this.config.tableId,
      seats: this.state.seats.map(publicSeatView),
      buttonSeat: this.state.buttonSeat,
      config: {
        smallBlind: this.config.smallBlind,
        bigBlind: this.config.bigBlind,
        maxSeats: this.config.maxSeats,
        minBuyIn: this.config.minBuyIn,
        maxBuyIn: this.config.maxBuyIn,
        actionTimeoutMs: this.config.actionTimeoutMs,
      },
    };
  }

  sit(seatNo: number, playerId: string, displayName: string, buyIn: number): RejectReason | null {
    const seat = this.state.seats[seatNo];
    if (!seat || seat.status !== "EMPTY") return "ILLEGAL_ACTION";
    if (buyIn < this.config.minBuyIn || buyIn > this.config.maxBuyIn) return "INVALID_AMOUNT";
    seat.playerId = playerId;
    seat.displayName = displayName;
    seat.stack = buyIn;
    seat.status = "ACTIVE";
    seat.betThisStreet = 0;
    seat.totalCommittedThisHand = 0;
    seat.holeCards = null;
    seat.consecutiveTimeouts = 0;
    this.io.broadcastToTable(this.publicTableStateEvent());
    // Note: does NOT auto-start a hand here. Callers that want "hand starts
    // automatically once 2 players are seated" (the WS/client UX) call
    // tryStartHand() themselves right after a successful sit() — see
    // TableManager's SIT handler. This split lets a REST-driven caller sit
    // players without an implicit deal, then explicitly control dealing via
    // tryStartHand() (POST /tables/{id}/start).
    return null;
  }

  requestSitOut(seatNo: number): void {
    if (this.state.street === null) {
      this.applySitOutNow(seatNo, "REQUESTED");
    } else {
      this.pendingSitOut.add(seatNo);
    }
  }

  requestSitIn(seatNo: number): void {
    const seat = this.state.seats[seatNo];
    if (!seat || seat.status !== "SITTING_OUT") return;
    seat.status = "ACTIVE";
    this.pendingSitOut.delete(seatNo);
    this.io.broadcastToTable(this.publicTableStateEvent());
    this.tryStartHand();
  }

  requestLeave(seatNo: number): void {
    const seat = this.state.seats[seatNo];
    if (!seat) return;
    if (this.state.street === null || seat.status !== "ACTIVE") {
      this.clearSeat(seatNo);
    } else {
      this.pendingLeave.add(seatNo);
    }
  }

  handleDisconnect(seatNo: number): void {
    this.io.broadcastToTable({ type: "PLAYER_DISCONNECTED", seatNo });
  }

  handleReconnect(seatNo: number): void {
    this.io.broadcastToTable({ type: "PLAYER_RECONNECTED", seatNo });
  }

  stateSyncFor(seatNo: number | null): ServerEvent {
    const seat = seatNo !== null ? this.state.seats[seatNo] : null;
    const isActingSeat = seatNo !== null && this.state.actingSeat === seatNo;
    const legal = isActingSeat ? this.legalActions(seatNo!) : null;
    const range = isActingSeat ? this.legalRaiseRange(seatNo!) : null;
    return {
      type: "STATE_SYNC",
      tableId: this.config.tableId,
      handSeq: this.state.handSeq,
      actionSeq: this.state.actionSeq,
      street: this.state.street,
      board: this.state.board,
      buttonSeat: this.state.buttonSeat,
      actingSeat: this.state.actingSeat,
      actByMs: this.state.actByMs,
      potTotal: this.currentPotTotal(),
      seats: this.state.seats.map(publicSeatView),
      mySeat: seatNo,
      myHoleCards: seat?.holeCards ?? null,
      legalActions: legal,
      toCall: isActingSeat && seat ? this.state.currentBet - seat.betThisStreet : null,
      minRaiseTo: range?.min ?? null,
      maxRaiseTo: range?.max ?? null,
    };
  }

  /**
   * Core entry point for §2.3's seven-step validation pipeline. Returns a
   * synchronous applied/rejected result (in addition to the ACTION_REJECTED
   * side-channel sent via EngineIO for WS clients) so a caller with no live
   * socket — e.g. the REST facade — can still learn the outcome directly.
   */
  submitAction(
    seatNo: number,
    actionId: string,
    handSeq: number,
    action: WireAction,
    amount: number | undefined,
  ): { applied: true } | { applied: false; reason: RejectReason } {
    // Idempotency replay (§2.7) — checked before anything else so a retried
    // submit never re-runs game logic.
    const history = this.appliedActions.get(seatNo) ?? [];
    const existing = history.find((r) => r.actionId === actionId);
    if (existing) {
      if (existing.result.type === "REJECTED") {
        this.io.sendToSeat(seatNo, { type: "ACTION_REJECTED", actionId, reason: existing.result.reason });
        return { applied: false, reason: existing.result.reason };
      }
      // APPLIED replays are implicit: the seat can re-derive state via REQUEST_SYNC;
      // we still avoid reapplying game logic.
      return { applied: true };
    }

    const reject = (reason: RejectReason): { applied: false; reason: RejectReason } => {
      history.push({ actionId, result: { type: "REJECTED", reason } });
      this.appliedActions.set(seatNo, history);
      this.io.sendToSeat(seatNo, { type: "ACTION_REJECTED", actionId, reason });
      return { applied: false, reason };
    };

    if (handSeq !== this.state.handSeq) return reject("STALE_HAND");
    if (this.state.street === null || this.state.street === "SHOWDOWN") {
      return reject("NOT_ACCEPTING_ACTIONS");
    }
    if (this.state.actingSeat !== seatNo) return reject("NOT_YOUR_TURN");

    const legal = this.legalActions(seatNo);
    if (!legal.includes(action)) return reject("ILLEGAL_ACTION");

    if (action === "RAISE") {
      const range = this.legalRaiseRange(seatNo);
      const seat = this.state.seats[seatNo]!;
      const allInAmount = seat.stack + seat.betThisStreet;
      if (
        amount === undefined ||
        amount > allInAmount ||
        (amount < range.min && amount !== allInAmount)
      ) {
        return reject("INVALID_AMOUNT");
      }
    }

    history.push({ actionId, result: { type: "APPLIED" } });
    this.appliedActions.set(seatNo, history);
    this.applyAction(seatNo, action, amount);
    return { applied: true };
  }

  /** Wall-clock timeout firing — §2.8. */
  private onTurnTimeout(seatNo: number): void {
    if (this.state.actingSeat !== seatNo) return;
    const seat = this.state.seats[seatNo]!;
    const toCall = this.state.currentBet - seat.betThisStreet;
    const action: WireAction = toCall === 0 ? "CHECK" : "FOLD";
    const actionId = randomUUID();
    const history = this.appliedActions.get(seatNo) ?? [];
    history.push({ actionId, result: { type: "APPLIED" } });
    this.appliedActions.set(seatNo, history);
    seat.consecutiveTimeouts += 1;
    this.applyAction(seatNo, action, undefined);
    if (seat.consecutiveTimeouts >= 3 && seat.status !== "EMPTY") {
      this.pendingSitOut.add(seatNo);
      if (this.state.street === null) this.applySitOutNow(seatNo, "TIMEOUT_LIMIT");
    }
  }

  // ---------------------------------------------------------------------
  // §2.4 / §2.5 — legal actions and legal raise range
  // ---------------------------------------------------------------------

  legalActions(seatNo: number): WireAction[] {
    const seat = this.state.seats[seatNo];
    if (!seat) return [];
    const toCall = this.state.currentBet - seat.betThisStreet;
    const actions: WireAction[] = ["FOLD"];
    if (toCall === 0) actions.push("CHECK");
    if (toCall > 0) actions.push("CALL");
    if (this.state.currentBet === 0 && seat.stack > 0) actions.push("RAISE"); // BET, wire-modeled as RAISE
    if (this.state.currentBet > 0 && toCall < seat.stack) actions.push("RAISE");
    return actions;
  }

  private legalRaiseRange(seatNo: number): { min: number; max: number } {
    const seat = this.state.seats[seatNo]!;
    const max = seat.stack + seat.betThisStreet;
    const min = Math.min(this.state.currentBet + this.state.minRaiseSize, max);
    return { min, max };
  }

  // ---------------------------------------------------------------------
  // Action application + §2.6 turn advancement / round closure
  // ---------------------------------------------------------------------

  private applyAction(seatNo: number, action: WireAction, amount: number | undefined): void {
    const seat = this.state.seats[seatNo]!;
    const toCall = this.state.currentBet - seat.betThisStreet;
    let wasFullRaise = false;

    switch (action) {
      case "FOLD":
        seat.status = "FOLDED";
        break;
      case "CHECK":
        break;
      case "CALL": {
        const pay = Math.min(toCall, seat.stack);
        seat.stack -= pay;
        seat.betThisStreet += pay;
        seat.totalCommittedThisHand += pay;
        if (seat.stack === 0) seat.status = "ALL_IN";
        break;
      }
      case "RAISE": {
        const newTotal = amount!;
        const increment = newTotal - seat.betThisStreet;
        seat.stack -= increment;
        seat.betThisStreet = newTotal;
        seat.totalCommittedThisHand += increment;
        const isFull = newTotal - this.state.currentBet >= this.state.minRaiseSize;
        if (isFull) {
          this.state.minRaiseSize = newTotal - this.state.currentBet;
          this.state.lastFullRaiseSeat = seatNo;
          wasFullRaise = true;
        }
        this.state.currentBet = newTotal;
        this.state.lastAggressorSeat = seatNo;
        if (seat.stack === 0) seat.status = "ALL_IN";
        break;
      }
    }

    this.state.actionSeq += 1;
    this.io.broadcastToTable({
      type: "ACTION_APPLIED",
      handSeq: this.state.handSeq,
      actionSeq: this.state.actionSeq,
      seat: seatNo,
      action,
      amount: action === "RAISE" ? amount! : action === "CALL" ? seat.betThisStreet : 0,
      potTotal: this.currentPotTotal(),
      playerStack: seat.stack,
      playerBetThisStreet: seat.betThisStreet,
    });

    // §2.6 step 1
    if (wasFullRaise) {
      this.state.actedThisStreet = new Set([seatNo]);
    } else {
      this.state.actedThisStreet.add(seatNo);
    }

    // §2.6 step 2 — everyone else folded
    const nonFolded = this.state.seats.filter((s) => s.status !== "FOLDED" && s.status !== "EMPTY" && s.status !== "SITTING_OUT");
    if (action === "FOLD" && nonFolded.length === 1) {
      this.state.actingSeat = null;
      this.settle();
      return;
    }

    this.advanceTurn();
  }

  private advanceTurn(): void {
    this.clearTurnTimer();

    const activeSeats = this.state.seats.filter((s) => s.status === "ACTIVE");
    const roundClosed =
      activeSeats.length === 0 ||
      activeSeats.every((s) => s.betThisStreet === this.state.currentBet && this.state.actedThisStreet.has(s.seatNo));

    if (roundClosed) {
      this.state.actingSeat = null;
      this.state.actByMs = null;
      this.advanceStreet();
      return;
    }

    const next = this.nextSeatToAct();
    if (next === null) {
      // No one left who both needs to act and can act (defensive fallback).
      this.state.actingSeat = null;
      this.state.actByMs = null;
      this.advanceStreet();
      return;
    }

    this.beginTurn(next);
  }

  /** Sets actingSeat, starts the turn clock, and broadcasts TURN_STARTED. */
  private beginTurn(seatNo: number): void {
    this.state.actingSeat = seatNo;
    this.state.actByMs = Date.now() + this.config.actionTimeoutMs;
    const legal = this.legalActions(seatNo);
    const range = this.legalRaiseRange(seatNo);
    const seat = this.state.seats[seatNo]!;
    this.io.broadcastToTable({
      type: "TURN_STARTED",
      handSeq: this.state.handSeq,
      actionSeq: this.state.actionSeq,
      seat: seatNo,
      legalActions: legal,
      toCall: this.state.currentBet - seat.betThisStreet,
      minRaiseTo: range.min,
      maxRaiseTo: range.max,
      actByMs: this.state.actByMs,
    });
    this.turnTimer = setTimeout(() => this.onTurnTimeout(seatNo), this.config.actionTimeoutMs);
  }

  /**
   * Finds the first seat needing action starting from (and including)
   * `candidateFirst`, walking clockwise via nextSeatToAct()'s skip rules, and
   * begins that seat's turn. Used whenever the "first to act" seat is known
   * by rule (UTG, first-active-after-button, heads-up SB) rather than
   * derived from the previous actingSeat.
   */
  private seedTurnFrom(candidateFirst: number): void {
    this.state.actingSeat = candidateFirst === 0 ? this.config.maxSeats - 1 : candidateFirst - 1;
    const seeded = this.nextSeatToAct();
    if (seeded === null) {
      this.state.actingSeat = null;
      this.settle();
      return;
    }
    this.beginTurn(seeded);
  }

  private nextSeatToAct(): number | null {
    const start = this.state.actingSeat;
    if (start === null) return null;
    for (let i = 1; i <= this.config.maxSeats; i++) {
      const candidate = (start + i) % this.config.maxSeats;
      const seat = this.state.seats[candidate]!;
      if (seat.status !== "ACTIVE") continue;
      if (seat.betThisStreet === this.state.currentBet && this.state.actedThisStreet.has(candidate)) continue;
      return candidate;
    }
    return null;
  }

  private advanceStreet(): void {
    for (const s of this.state.seats) {
      s.betThisStreet = 0;
    }
    this.state.currentBet = 0;
    this.state.minRaiseSize = this.config.bigBlind;
    this.state.actedThisStreet = new Set<number>();
    this.state.lastAggressorSeat = null;

    const activeCount = this.state.seats.filter((s) => s.status === "ACTIVE").length;

    if (this.state.street === "PREFLOP") {
      this.dealCommunity(3, "FLOP");
    } else if (this.state.street === "FLOP") {
      this.dealCommunity(1, "TURN");
    } else if (this.state.street === "TURN") {
      this.dealCommunity(1, "RIVER");
    } else if (this.state.street === "RIVER") {
      this.state.street = "SHOWDOWN";
      this.settle();
      return;
    }

    if (activeCount < 2) {
      // Everyone left is all-in (or exactly one active + rest all-in): deal
      // remaining streets face-up with no betting, per §2.6 step 4.
      if (this.state.street === "SHOWDOWN") {
        this.settle();
      } else {
        this.advanceStreet();
      }
      return;
    }

    const first = this.firstToActPostflop();
    if (first === null) {
      this.settle();
      return;
    }
    this.seedTurnFrom(first);
  }

  private firstToActPostflop(): number | null {
    if (this.state.buttonSeat === null) return null;
    for (let i = 1; i <= this.config.maxSeats; i++) {
      const candidate = (this.state.buttonSeat + i) % this.config.maxSeats;
      const seat = this.state.seats[candidate]!;
      if (seat.status === "ACTIVE") return candidate;
    }
    return null;
  }

  private dealCommunity(count: number, street: Exclude<TableState["street"], "SHOWDOWN" | null | "PREFLOP">): void {
    for (let i = 0; i < count; i++) {
      const card = this.deck.pop();
      if (card) this.state.board.push(card);
    }
    this.state.street = street;
    this.io.broadcastToTable({
      type: "STREET_DEALT",
      handSeq: this.state.handSeq,
      street,
      cards: [...this.state.board],
    });
  }

  // ---------------------------------------------------------------------
  // §5 — SETTLE: pot construction + payout
  // ---------------------------------------------------------------------

  private settle(): void {
    this.clearTurnTimer();
    this.state.street = "SHOWDOWN";

    const committed = new Map<number, number>();
    const folded = new Set<number>();
    for (const seat of this.state.seats) {
      if (seat.totalCommittedThisHand > 0) committed.set(seat.seatNo, seat.totalCommittedThisHand);
      if (seat.status === "FOLDED") folded.add(seat.seatNo);
    }

    const pots = buildPots(committed, folded);

    const contestants = this.state.seats.filter(
      (s) => committed.has(s.seatNo) && s.status !== "FOLDED",
    );
    const sevenCardsBySeat = new Map<number, Card[]>();
    for (const seat of contestants) {
      if (seat.holeCards && seat.holeCards.length === 2) {
        sevenCardsBySeat.set(seat.seatNo, [...seat.holeCards, ...this.state.board]);
      }
    }

    // Recorded for callers with no live socket (REST facade) to read back
    // after the fact — "reached showdown" means ≥2 non-folded contestants
    // had chips in; a fold-out hand (everyone but one folded) leaves this
    // empty, matching the harness contract.
    this.lastShowdown =
      contestants.length > 1
        ? contestants.map((s) => ({
            seat: s.seatNo,
            holeCards: s.holeCards ? [...s.holeCards] : [],
            handCategory: sevenCardsBySeat.has(s.seatNo)
              ? evaluateBestHand(sevenCardsBySeat.get(s.seatNo)!).categoryName
              : "",
          }))
        : [];

    const seatOrderClockwiseFromButton = this.clockwiseOrderFromButton();
    const { awarded, stackDeltas } = awardPots(
      pots,
      sevenCardsBySeat,
      this.state.buttonSeat ?? 0,
      seatOrderClockwiseFromButton,
    );

    for (const [seatNo, delta] of stackDeltas) {
      const seat = this.state.seats[seatNo]!;
      seat.stack += delta;
    }

    const revealedHands = contestants
      .filter((s) => pots.some((p) => p.eligibleSeats.length > 1 && p.eligibleSeats.includes(s.seatNo)))
      .map((s) => ({ seat: s.seatNo, cards: s.holeCards! }));

    this.io.broadcastToTable({
      type: "SHOWDOWN",
      handSeq: this.state.handSeq,
      revealedHands,
      pots: awarded.map((p) => ({
        amount: p.amount,
        eligibleSeats: p.eligibleSeats,
        winners: p.winners,
      })),
    });

    this.io.broadcastToTable({
      type: "HAND_COMPLETE",
      handSeq: this.state.handSeq,
      seats: this.state.seats.map((s) => ({ seatNo: s.seatNo, stack: s.stack })),
    });

    // Reset to WAITING_FOR_PLAYERS / apply queued seat changes, then maybe
    // start the next hand.
    this.state.street = null;
    this.state.actingSeat = null;
    this.state.actByMs = null;
    this.state.board = [];
    this.state.currentBet = 0;
    this.state.minRaiseSize = this.config.bigBlind;
    this.state.actedThisStreet = new Set<number>();
    this.state.lastAggressorSeat = null;
    this.state.potPreview = 0;

    for (const seat of this.state.seats) {
      seat.betThisStreet = 0;
      seat.totalCommittedThisHand = 0;
      seat.holeCards = null;
      if (seat.status === "FOLDED" || seat.status === "ALL_IN") {
        seat.status = seat.stack > 0 ? "ACTIVE" : "SITTING_OUT";
      }
    }

    for (const seatNo of this.pendingLeave) this.clearSeat(seatNo);
    this.pendingLeave.clear();
    for (const seatNo of this.pendingSitOut) this.applySitOutNow(seatNo, "REQUESTED");
    this.pendingSitOut.clear();

    this.io.broadcastToTable(this.publicTableStateEvent());
    this.tryStartHand();
  }

  private clockwiseOrderFromButton(): number[] {
    const button = this.state.buttonSeat ?? 0;
    const order: number[] = [];
    for (let i = 0; i < this.config.maxSeats; i++) {
      order.push((button + i) % this.config.maxSeats);
    }
    return order;
  }

  // ---------------------------------------------------------------------
  // §1 / §3 — hand start, button rotation, blinds
  // ---------------------------------------------------------------------

  /**
   * Starts a new hand if the table is between hands and has ≥2 eligible
   * seats. Public so callers can control dealing explicitly (REST
   * `POST /tables/{id}/start`) as well as implicitly (WS: called right
   * after a successful SIT, and again after each hand settles).
   */
  tryStartHand(): boolean {
    if (this.state.street !== null) return false;
    const eligible = this.state.seats.filter((s) => s.status === "ACTIVE" && s.stack > 0);
    if (eligible.length < 2) return false;
    this.startHand();
    return true;
  }

  private startHand(): void {
    this.state.handSeq += 1;
    this.state.actionSeq = 0; // §6.3: actionSeq resets to 0 at each HAND_STARTED
    this.appliedActions.clear();

    const eligible = this.state.seats.filter((s) => s.status === "ACTIVE" && s.stack > 0);

    // Button rotation — §3.
    if (this.state.buttonSeat === null) {
      const idx = randomInt(0, eligible.length);
      this.state.buttonSeat = eligible[idx]!.seatNo;
    } else {
      let next = this.state.buttonSeat;
      for (let i = 1; i <= this.config.maxSeats; i++) {
        const candidate = (this.state.buttonSeat + i) % this.config.maxSeats;
        const seat = this.state.seats[candidate]!;
        if (seat.status === "ACTIVE" && seat.stack > 0) {
          next = candidate;
          break;
        }
      }
      this.state.buttonSeat = next;
    }

    const headsUp = eligible.length === 2;
    let sbSeat: number;
    let bbSeat: number;
    if (headsUp) {
      sbSeat = this.state.buttonSeat;
      bbSeat = this.nextEligibleSeat(sbSeat, eligible);
    } else {
      sbSeat = this.nextEligibleSeat(this.state.buttonSeat, eligible);
      bbSeat = this.nextEligibleSeat(sbSeat, eligible);
    }
    this.state.sbSeat = sbSeat;
    this.state.bbSeat = bbSeat;

    // Reset per-hand seat fields.
    for (const seat of this.state.seats) {
      seat.betThisStreet = 0;
      seat.totalCommittedThisHand = 0;
      seat.holeCards = null;
      if (seat.status === "FOLDED" || seat.status === "ALL_IN") seat.status = "ACTIVE";
    }

    this.postBlind(sbSeat, this.config.smallBlind);
    this.postBlind(bbSeat, this.config.bigBlind);

    this.state.currentBet = this.config.bigBlind;
    this.state.minRaiseSize = this.config.bigBlind;
    this.state.lastFullRaiseSeat = bbSeat;
    this.state.actedThisStreet = new Set<number>();
    this.state.board = [];
    this.state.street = "PREFLOP";
    this.state.lastAggressorSeat = null;

    // Deal hole cards — §4.1: two passes starting from the seat clockwise of the button.
    this.deck = newShuffledDeck();
    const dealOrder = this.dealOrderFromButton(eligible.map((s) => s.seatNo));
    for (const seatNo of dealOrder) this.state.seats[seatNo]!.holeCards = [];
    for (let pass = 0; pass < 2; pass++) {
      for (const seatNo of dealOrder) {
        const card = this.deck.pop()!;
        this.state.seats[seatNo]!.holeCards!.push(card);
      }
    }

    this.io.broadcastToTable({
      type: "HAND_STARTED",
      handSeq: this.state.handSeq,
      buttonSeat: this.state.buttonSeat,
      sbSeat,
      bbSeat,
      sbAmount: this.config.smallBlind,
      bbAmount: this.config.bigBlind,
    });
    for (const seatNo of dealOrder) {
      const cards = this.state.seats[seatNo]!.holeCards as [Card, Card];
      this.io.sendToSeat(seatNo, { type: "HOLE_CARDS", handSeq: this.state.handSeq, cards });
    }

    // First to act preflop: heads-up it's the button/SB; otherwise UTG (next
    // occupied seat clockwise of BB) — §3.
    const firstToAct = headsUp ? sbSeat : this.nextEligibleSeat(bbSeat, eligible);
    this.seedTurnFrom(firstToAct);
  }

  private postBlind(seatNo: number, amount: number): void {
    const seat = this.state.seats[seatNo]!;
    const pay = Math.min(amount, seat.stack);
    seat.stack -= pay;
    seat.betThisStreet += pay;
    seat.totalCommittedThisHand += pay;
    if (seat.stack === 0) seat.status = "ALL_IN";
  }

  private nextEligibleSeat(fromSeatNo: number, eligible: Seat[]): number {
    const eligibleSet = new Set(eligible.map((s) => s.seatNo));
    for (let i = 1; i <= this.config.maxSeats; i++) {
      const candidate = (fromSeatNo + i) % this.config.maxSeats;
      if (eligibleSet.has(candidate)) return candidate;
    }
    return fromSeatNo;
  }

  private dealOrderFromButton(eligibleSeatNos: number[]): number[] {
    const set = new Set(eligibleSeatNos);
    const order: number[] = [];
    if (this.state.buttonSeat === null) return eligibleSeatNos;
    for (let i = 1; i <= this.config.maxSeats; i++) {
      const candidate = (this.state.buttonSeat + i) % this.config.maxSeats;
      if (set.has(candidate)) order.push(candidate);
    }
    return order;
  }

  // ---------------------------------------------------------------------
  // Misc helpers
  // ---------------------------------------------------------------------

  private currentPotTotal(): number {
    return this.state.seats.reduce((sum, s) => sum + s.totalCommittedThisHand, 0);
  }

  private clearTurnTimer(): void {
    if (this.turnTimer) {
      clearTimeout(this.turnTimer);
      this.turnTimer = null;
    }
  }

  private applySitOutNow(seatNo: number, reason: "REQUESTED" | "TIMEOUT_LIMIT"): void {
    const seat = this.state.seats[seatNo];
    if (!seat || seat.status === "EMPTY") return;
    seat.status = "SITTING_OUT";
    this.pendingSitOut.delete(seatNo);
    this.io.broadcastToTable({ type: "PLAYER_SAT_OUT", seatNo, reason });
    this.io.broadcastToTable(this.publicTableStateEvent());
  }

  private clearSeat(seatNo: number): void {
    this.state.seats[seatNo] = emptySeat(seatNo);
    this.pendingLeave.delete(seatNo);
    this.io.broadcastToTable(this.publicTableStateEvent());
  }
}

function emptySeat(seatNo: number): Seat {
  return {
    seatNo,
    playerId: null,
    displayName: null,
    stack: 0,
    betThisStreet: 0,
    totalCommittedThisHand: 0,
    status: "EMPTY",
    holeCards: null,
    consecutiveTimeouts: 0,
  };
}

function publicSeatView(seat: Seat) {
  return {
    seatNo: seat.seatNo,
    playerId: seat.playerId,
    displayName: seat.displayName,
    stack: seat.stack,
    betThisStreet: seat.betThisStreet,
    status: seat.status,
  };
}

// Re-exported for anyone constructing sevenCardsBySeat externally (tests, etc.)
export { evaluateBestHand };
