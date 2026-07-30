// Game Engine — design-server.md §1-§5: hand lifecycle, turn enforcement,
// blinds/button rotation, dealing, hand evaluation dispatch, and side-pot
// settlement. One Table instance is the sole authority for its own state
// (Stage 1 architecture.md §6.2) — every mutation happens synchronously
// within a single Node.js event-loop turn, so there is never a window
// where two actions can race against the same `actingSeat`.

import { randomUUID, randomInt } from 'crypto';
import { Card, Pot, PokerError, Seat, SeatStatus, ShowdownEntry, Street } from './types';
import { newShuffledDeck } from './deck';
import { compareHandValues, evaluateBestHand } from './evaluator';
import { buildPots } from './pots';

const MAX_SEATS = 9;
const LOG_CAP = 20;

export type RestAction = 'fold' | 'check' | 'call' | 'bet' | 'raise';

export interface StateView {
  table_id: string;
  small_blind: number;
  big_blind: number;
  button_seat: number | null;
  betting_round: string | null;
  community_cards: Card[];
  pots: { amount: number; eligible_seats: number[] }[];
  current_bet: number;
  min_raise: number;
  current_actor: number | null;
  hand_in_progress: boolean;
  last_action_log: string[];
  last_showdown: { seat: number; hole_cards: Card[]; hand_category: string }[];
  players: {
    seat: number;
    stack: number;
    status: string;
    current_bet: number;
    total_committed: number;
    hole_cards: Card[] | null;
  }[];
}

export class Table {
  readonly id: string;
  readonly smallBlind: number;
  readonly bigBlind: number;
  readonly seats: Seat[];

  handSeq = 0;
  street: Street | null = null;
  buttonSeat: number | null = null;
  actingSeat: number | null = null;
  currentBet = 0;
  minRaiseSize: number;
  lastFullRaiseSeat: number | null = null;
  actedThisStreet: Set<number> = new Set();
  handInProgress = false;

  deck: Card[] = [];
  communityCards: Card[] = [];
  pots: Pot[] = [];
  lastShowdown: ShowdownEntry[] = [];
  lastActionLog: string[] = [];

  constructor(smallBlind: number, bigBlind: number) {
    this.id = randomUUID();
    this.smallBlind = smallBlind;
    this.bigBlind = bigBlind;
    this.minRaiseSize = bigBlind;
    this.seats = [];
    for (let i = 0; i < MAX_SEATS; i++) {
      this.seats.push({
        seatNo: i,
        playerId: null,
        displayName: null,
        stack: 0,
        betThisStreet: 0,
        totalCommittedThisHand: 0,
        status: 'EMPTY',
        holeCards: null,
      });
    }
  }

  private log(message: string) {
    this.lastActionLog.push(message);
    if (this.lastActionLog.length > LOG_CAP) {
      this.lastActionLog = this.lastActionLog.slice(-LOG_CAP);
    }
  }

  // ---- Seating ----------------------------------------------------------

  addPlayer(name: string, buyIn: number): number {
    if (!Number.isFinite(buyIn) || buyIn <= 0) {
      throw new PokerError('INVALID_BUY_IN', 'buy_in must be a positive integer');
    }
    const seat = this.seats.find((s) => s.status === 'EMPTY');
    if (!seat) {
      throw new PokerError('TABLE_FULL', 'no empty seats available', 400);
    }
    seat.playerId = randomUUID();
    seat.displayName = name;
    seat.stack = Math.trunc(buyIn);
    seat.betThisStreet = 0;
    seat.totalCommittedThisHand = 0;
    seat.status = 'ACTIVE';
    seat.holeCards = null;
    return seat.seatNo;
  }

  // ---- Hand lifecycle -----------------------------------------------------

  private eligibleForHand(): Seat[] {
    return this.seats.filter((s) => s.status !== 'EMPTY' && s.status !== 'SITTING_OUT' && s.stack > 0);
  }

  private nextOccupiedSeatFrom(fromSeatNo: number, predicate: (s: Seat) => boolean): number | null {
    for (let step = 1; step <= MAX_SEATS; step++) {
      const seatNo = (fromSeatNo + step) % MAX_SEATS;
      const seat = this.seats[seatNo];
      if (predicate(seat)) return seatNo;
    }
    return null;
  }

  private nextActiveSeatFrom(fromSeatNo: number): number | null {
    return this.nextOccupiedSeatFrom(fromSeatNo, (s) => s.status === 'ACTIVE');
  }

  startHand(): void {
    if (this.handInProgress) {
      throw new PokerError('HAND_IN_PROGRESS', 'a hand is already in progress', 400);
    }
    const eligible = this.eligibleForHand();
    if (eligible.length < 2) {
      throw new PokerError('NOT_ENOUGH_PLAYERS', 'at least 2 seated players with chips are required', 400);
    }

    this.handSeq += 1;
    this.communityCards = [];
    this.lastShowdown = [];
    this.deck = newShuffledDeck();
    this.currentBet = 0;
    this.minRaiseSize = this.bigBlind;
    this.actedThisStreet = new Set();
    this.lastFullRaiseSeat = null;

    for (const s of this.seats) {
      if (s.status === 'EMPTY' || s.status === 'SITTING_OUT') continue;
      s.betThisStreet = 0;
      s.totalCommittedThisHand = 0;
      s.holeCards = null;
      s.status = 'ACTIVE';
    }

    // Button rotation — design-server.md §3.
    if (this.buttonSeat === null) {
      const idx = randomInt(0, eligible.length);
      this.buttonSeat = eligible[idx].seatNo;
    } else {
      const next = this.nextOccupiedSeatFrom(
        this.buttonSeat,
        (s) => s.status !== 'EMPTY' && s.status !== 'SITTING_OUT' && s.stack > 0,
      );
      this.buttonSeat = next ?? this.buttonSeat;
    }

    const headsUp = eligible.length === 2;
    let sbSeat: number;
    let bbSeat: number;
    if (headsUp) {
      sbSeat = this.buttonSeat;
      bbSeat = eligible.find((s) => s.seatNo !== this.buttonSeat)!.seatNo;
    } else {
      sbSeat = this.nextOccupiedSeatFrom(this.buttonSeat, (s) => s.status === 'ACTIVE')!;
      bbSeat = this.nextOccupiedSeatFrom(sbSeat, (s) => s.status === 'ACTIVE')!;
    }

    this.postBlind(sbSeat, this.smallBlind);
    this.postBlind(bbSeat, this.bigBlind);
    this.currentBet = Math.max(this.seats[sbSeat].betThisStreet, this.seats[bbSeat].betThisStreet);

    this.log(
      `Hand ${this.handSeq} started. Button=seat${this.buttonSeat}, SB=seat${sbSeat}(${this.smallBlind}), BB=seat${bbSeat}(${this.bigBlind})`,
    );

    // Deal hole cards — two passes, starting clockwise of the button.
    const inHandSeats = this.seats.filter((s) => s.status === 'ACTIVE' || s.status === 'ALL_IN');
    const dealOrder: number[] = [];
    let cursor = this.buttonSeat;
    for (let i = 0; i < MAX_SEATS; i++) {
      cursor = (cursor + 1) % MAX_SEATS;
      if (inHandSeats.some((s) => s.seatNo === cursor)) dealOrder.push(cursor);
    }
    for (let pass = 0; pass < 2; pass++) {
      for (const seatNo of dealOrder) {
        const card = this.deck.pop()!;
        this.seats[seatNo].holeCards = this.seats[seatNo].holeCards ?? [];
        this.seats[seatNo].holeCards!.push(card);
      }
    }
    this.log(`Hole cards dealt to seats [${dealOrder.join(', ')}]`);

    this.street = 'PREFLOP';
    this.handInProgress = true;
    this.recomputePots();

    // First actor preflop — design-server.md §3.
    const preflopFirst = headsUp
      ? this.seats[this.buttonSeat].status === 'ACTIVE'
        ? this.buttonSeat
        : this.nextActiveSeatFrom(this.buttonSeat)
      : this.nextActiveSeatFrom(bbSeat);

    this.openBettingRound(preflopFirst);
  }

  private postBlind(seatNo: number, blindAmount: number) {
    const seat = this.seats[seatNo];
    const amount = Math.min(blindAmount, seat.stack);
    seat.stack -= amount;
    seat.betThisStreet = amount;
    seat.totalCommittedThisHand = amount;
    if (seat.stack === 0) seat.status = 'ALL_IN';
  }

  // Opens a betting round given the intended first actor. If no ACTIVE
  // seat can act (everyone remaining is ALL_IN or FOLDED), chains straight
  // through the remaining streets with no betting, then settles — per
  // design-server.md §2.6 step 4's "zero ACTIVE seats" rule and §1's
  // all-in-runout note.
  private openBettingRound(intendedFirstActor: number | null): void {
    const activeSeats = this.seats.filter((s) => s.status === 'ACTIVE');
    if (activeSeats.length === 0 || intendedFirstActor === null) {
      this.dealRemainingStreetsAndSettle();
      return;
    }
    this.actingSeat = intendedFirstActor;
    this.log(`Turn: seat ${this.actingSeat} to act (${this.street})`);
  }

  private dealRemainingStreetsAndSettle(): void {
    while (this.communityCards.length < 5) {
      this.dealNextStreetCards();
    }
    this.street = 'SHOWDOWN';
    this.actingSeat = null;
    this.settle();
  }

  private dealNextStreetCards(): void {
    if (this.street === 'PREFLOP') {
      this.communityCards.push(...this.drawN(3));
      this.street = 'FLOP';
    } else if (this.street === 'FLOP') {
      this.communityCards.push(...this.drawN(1));
      this.street = 'TURN';
    } else if (this.street === 'TURN') {
      this.communityCards.push(...this.drawN(1));
      this.street = 'RIVER';
    }
    this.log(`Street ${this.street}: board = [${this.communityCards.map(cardStr).join(', ')}]`);
  }

  private drawN(n: number): Card[] {
    const cards: Card[] = [];
    for (let i = 0; i < n; i++) cards.push(this.deck.pop()!);
    return cards;
  }

  // ---- Action validation & application — design-server.md §2.3-§2.6 -------

  legalActionsFor(seat: Seat): Set<RestAction> {
    const toCall = this.currentBet - seat.betThisStreet;
    const legal = new Set<RestAction>(['fold']);
    if (toCall === 0) legal.add('check');
    if (toCall > 0) legal.add('call');
    if (this.currentBet === 0 && seat.stack > 0) legal.add('bet');
    if (this.currentBet > 0 && toCall < seat.stack) legal.add('raise');
    return legal;
  }

  applyAction(seatNo: number, action: RestAction, amount: number | undefined): void {
    if (!this.handInProgress || this.street === null || this.street === 'SHOWDOWN') {
      throw new PokerError('NOT_ACCEPTING_ACTIONS', 'no betting round is currently open', 409);
    }
    const seat = this.seats[seatNo];
    if (!seat || seat.status === 'EMPTY') {
      throw new PokerError('NOT_SEATED', `seat ${seatNo} is not seated`, 400);
    }
    if (seatNo !== this.actingSeat) {
      throw new PokerError('NOT_YOUR_TURN', `it is seat ${this.actingSeat}'s turn, not seat ${seatNo}'s`, 409);
    }
    const legal = this.legalActionsFor(seat);
    if (!legal.has(action)) {
      throw new PokerError(
        'ILLEGAL_ACTION',
        `${action} is not legal for seat ${seatNo} right now (legal: ${[...legal].join(',')})`,
        400,
      );
    }

    let wasFullRaise = false;

    switch (action) {
      case 'fold': {
        seat.status = 'FOLDED';
        this.log(`Seat ${seatNo} folds`);
        break;
      }
      case 'check': {
        this.log(`Seat ${seatNo} checks`);
        break;
      }
      case 'call': {
        const toCall = this.currentBet - seat.betThisStreet;
        const payAmount = Math.min(toCall, seat.stack);
        seat.stack -= payAmount;
        seat.betThisStreet += payAmount;
        seat.totalCommittedThisHand += payAmount;
        if (seat.stack === 0) seat.status = 'ALL_IN';
        this.log(`Seat ${seatNo} calls ${payAmount}${seat.status === 'ALL_IN' ? ' (all-in)' : ''}`);
        break;
      }
      case 'bet':
      case 'raise': {
        if (amount === undefined || !Number.isFinite(amount)) {
          throw new PokerError('INVALID_AMOUNT', 'amount is required for bet/raise', 400);
        }
        const amt = Math.trunc(amount);
        const maxAmount = seat.stack + seat.betThisStreet;
        const minFull = this.currentBet + this.minRaiseSize;
        if (amt <= this.currentBet) {
          throw new PokerError('INVALID_AMOUNT', `amount ${amt} does not exceed current bet ${this.currentBet}`, 400);
        }
        if (amt > maxAmount) {
          throw new PokerError('INVALID_AMOUNT', `amount ${amt} exceeds seat's available chips (${maxAmount})`, 400);
        }
        if (amt < minFull && amt !== maxAmount) {
          throw new PokerError(
            'INVALID_AMOUNT',
            `amount ${amt} is below the minimum raise-to of ${minFull} (and is not an all-in)`,
            400,
          );
        }
        const increment = amt - this.currentBet;
        wasFullRaise = increment >= this.minRaiseSize;
        const delta = amt - seat.betThisStreet;
        seat.stack -= delta;
        seat.betThisStreet = amt;
        seat.totalCommittedThisHand += delta;
        if (seat.stack === 0) seat.status = 'ALL_IN';
        this.currentBet = amt;
        if (wasFullRaise) {
          this.minRaiseSize = increment;
          this.lastFullRaiseSeat = seatNo;
          this.actedThisStreet = new Set([seatNo]);
        }
        this.log(
          `Seat ${seatNo} ${action}s to ${amt}${seat.status === 'ALL_IN' ? ' (all-in)' : ''}${
            wasFullRaise ? '' : ' (incomplete/short all-in raise)'
          }`,
        );
        break;
      }
    }

    if (!((action === 'bet' || action === 'raise') && wasFullRaise)) {
      this.actedThisStreet.add(seatNo);
    }

    this.recomputePots();
    this.advanceAfterAction(seatNo);
  }

  private inHandSeats(): Seat[] {
    return this.seats.filter((s) => s.status === 'ACTIVE' || s.status === 'FOLDED' || s.status === 'ALL_IN');
  }

  private advanceAfterAction(actedSeatNo: number): void {
    const nonFolded = this.inHandSeats().filter((s) => s.status !== 'FOLDED');
    if (nonFolded.length === 1) {
      this.street = 'SHOWDOWN';
      this.actingSeat = null;
      this.settle();
      return;
    }

    const activeSeats = this.inHandSeats().filter((s) => s.status === 'ACTIVE');
    const roundClosed =
      activeSeats.length === 0 ||
      activeSeats.every((s) => s.betThisStreet === this.currentBet && this.actedThisStreet.has(s.seatNo));

    if (roundClosed) {
      this.currentBet = 0;
      this.minRaiseSize = this.bigBlind;
      this.actedThisStreet = new Set();
      this.lastFullRaiseSeat = null;
      for (const s of this.seats) s.betThisStreet = 0;

      if (this.street === 'RIVER') {
        this.street = 'SHOWDOWN';
        this.actingSeat = null;
        this.recomputePots();
        this.settle();
        return;
      }
      this.dealNextStreetCards();
      this.recomputePots();
      const firstPostflop = this.nextActiveSeatFrom(this.buttonSeat!);
      this.openBettingRound(firstPostflop);
    } else {
      this.actingSeat = this.nextActiveSeatFrom(actedSeatNo);
      this.log(`Turn: seat ${this.actingSeat} to act (${this.street})`);
    }
  }

  // ---- Settlement — design-server.md §5 ----------------------------------

  private recomputePots(): void {
    const committed = new Map<number, number>();
    for (const s of this.seats) {
      if (s.status !== 'EMPTY' && s.totalCommittedThisHand > 0) {
        committed.set(s.seatNo, s.totalCommittedThisHand);
      }
    }
    const folded = new Set(this.seats.filter((s) => s.status === 'FOLDED').map((s) => s.seatNo));
    this.pots = buildPots(committed, folded);
  }

  private orderClockwiseFromButton(seatNos: number[]): number[] {
    const button = this.buttonSeat ?? 0;
    return [...seatNos].sort((a, b) => {
      const da = (a - button - 1 + MAX_SEATS) % MAX_SEATS;
      const db = (b - button - 1 + MAX_SEATS) % MAX_SEATS;
      return da - db;
    });
  }

  private settle(): void {
    this.recomputePots();
    const nonFolded = this.inHandSeats().filter((s) => s.status !== 'FOLDED');
    let showdown: ShowdownEntry[] = [];

    if (nonFolded.length === 1) {
      const winner = nonFolded[0];
      const total = this.pots.reduce((sum, p) => sum + p.amount, 0);
      winner.stack += total;
      this.log(`Seat ${winner.seatNo} wins ${total} uncontested (all others folded)`);
    } else {
      const values = new Map(nonFolded.map((s) => [s.seatNo, evaluateBestHand([...s.holeCards!, ...this.communityCards])]));
      for (const pot of this.pots) {
        const eligible = pot.eligibleSeats.filter((sn) => values.has(sn));
        if (eligible.length === 0) continue;
        if (eligible.length === 1) {
          this.seats[eligible[0]].stack += pot.amount;
          continue;
        }
        let best = values.get(eligible[0])!;
        for (const sn of eligible) {
          const v = values.get(sn)!;
          if (compareHandValues(v, best) > 0) best = v;
        }
        const winners = eligible.filter((sn) => compareHandValues(values.get(sn)!, best) === 0);
        const share = Math.floor(pot.amount / winners.length);
        let remainder = pot.amount - share * winners.length;
        const ordered = this.orderClockwiseFromButton(winners);
        for (const sn of ordered) {
          let amt = share;
          if (remainder > 0) {
            amt += 1;
            remainder -= 1;
          }
          this.seats[sn].stack += amt;
        }
      }
      showdown = nonFolded.map((s) => ({
        seat: s.seatNo,
        holeCards: s.holeCards!,
        handCategory: values.get(s.seatNo)!.categoryName,
      }));
      this.log(
        `Showdown: ${showdown.map((e) => `seat ${e.seat} (${e.handCategory})`).join(', ')}`,
      );
    }

    this.lastShowdown = showdown;

    for (const s of this.seats) {
      if (s.status === 'EMPTY') continue;
      s.betThisStreet = 0;
      s.status = s.stack === 0 ? 'SITTING_OUT' : 'ACTIVE';
    }

    this.currentBet = 0;
    this.minRaiseSize = this.bigBlind;
    this.actedThisStreet = new Set();
    this.lastFullRaiseSeat = null;
    this.actingSeat = null;
    this.handInProgress = false;
    // NOTE: deliberately do NOT recompute this.pots here — seat statuses
    // were just reset (FOLDED -> ACTIVE for next hand), so recomputing now
    // would corrupt eligibility in the frozen post-hand snapshot. `this.pots`
    // from the recomputePots() call at the top of settle() is the correct,
    // final record of this hand's pot layers and stays as-is until the next
    // startHand() overwrites it.
  }

  // ---- Response shape — HARNESS-CONTRACT.md ------------------------------

  toStateView(requestingSeat: number | null): StateView {
    const revealed = new Set(this.lastShowdown.map((e) => e.seat));
    return {
      table_id: this.id,
      small_blind: this.smallBlind,
      big_blind: this.bigBlind,
      button_seat: this.buttonSeat,
      betting_round: this.street ? (this.street.toLowerCase() as string) : null,
      community_cards: this.communityCards,
      pots: this.pots.map((p) => ({ amount: p.amount, eligible_seats: p.eligibleSeats })),
      current_bet: this.currentBet,
      min_raise: this.minRaiseSize,
      current_actor: this.actingSeat,
      hand_in_progress: this.handInProgress,
      last_action_log: this.lastActionLog.slice(-LOG_CAP),
      last_showdown: this.lastShowdown.map((e) => ({
        seat: e.seat,
        hole_cards: e.holeCards,
        hand_category: e.handCategory,
      })),
      players: this.seats
        .filter((s) => s.status !== 'EMPTY')
        .map((s) => ({
          seat: s.seatNo,
          stack: s.stack,
          status: statusToWire(s.status),
          current_bet: s.betThisStreet,
          total_committed: s.totalCommittedThisHand,
          hole_cards: s.seatNo === requestingSeat || revealed.has(s.seatNo) ? s.holeCards : null,
        })),
    };
  }
}

function statusToWire(status: SeatStatus): string {
  switch (status) {
    case 'ACTIVE':
      return 'active';
    case 'FOLDED':
      return 'folded';
    case 'ALL_IN':
      return 'all_in';
    case 'SITTING_OUT':
      return 'sitting_out';
    default:
      return 'sitting_out';
  }
}

function cardStr(c: Card): string {
  return `${c.rank}${c.suit}`;
}
