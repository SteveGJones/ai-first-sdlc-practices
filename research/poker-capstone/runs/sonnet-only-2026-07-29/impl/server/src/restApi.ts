// REST facade required by docs/HARNESS-CONTRACT.md — a fixed wire API the
// stage-4 grading harness drives directly over HTTP, layered on top of the
// existing GameEngine/TableManager without touching their internal logic.
//
// Every endpoint here is a thin translation: parse the request, call the
// same public GameEngine/TableManager methods the WS layer already uses,
// and shape the response into the harness's exact JSON contract.

import { randomUUID } from "node:crypto";
import type { IncomingMessage, ServerResponse } from "node:http";
import type { GameEngine } from "./engine.js";
import { buildPots } from "./pots.js";
import type { TableManager } from "./tableManager.js";
import type { Card, SeatStatus, TableConfig, WireAction } from "./types.js";

// REST tables are created without the WS lobby's stakes-tied buy-in bounds
// (the contract's POST /tables/{id}/players body is just {name, buy_in},
// with no min/max) and with a long action timeout so a slow-polling test
// harness never races the server's own turn-timeout clock.
const REST_MIN_BUY_IN = 1;
const REST_MAX_BUY_IN = 1_000_000_000;
const REST_ACTION_TIMEOUT_MS = 10 * 60 * 1000;
const REST_MAX_SEATS = 9;

interface HarnessPlayer {
  seat: number;
  stack: number;
  status: "active" | "folded" | "all_in" | "sitting_out";
  total_committed: number;
  /** Chips this seat has put in THIS betting round only — engine's betThisStreet, reset to 0 each new street. */
  current_bet: number;
}

interface HarnessCard {
  rank: number;
  suit: string;
}

interface HarnessStateResponse {
  hand_in_progress: boolean;
  current_actor: number | null;
  current_bet: number;
  button_seat: number;
  community_cards: HarnessCard[];
  pots: { amount: number; eligible_seats: number[] }[];
  last_showdown: { seat: number; hole_cards: HarnessCard[]; hand_category: string }[];
  players: HarnessPlayer[];
}

const SEAT_STATUS_TO_HARNESS: Record<SeatStatus, HarnessPlayer["status"] | null> = {
  EMPTY: null,
  SITTING_OUT: "sitting_out",
  ACTIVE: "active",
  FOLDED: "folded",
  ALL_IN: "all_in",
};

const HARNESS_ACTION_TO_WIRE: Record<string, WireAction | undefined> = {
  fold: "FOLD",
  check: "CHECK",
  call: "CALL",
  bet: "RAISE",
  raise: "RAISE",
};

function toHarnessCard(card: Card): HarnessCard {
  return { rank: card.rank, suit: card.suit };
}

function buildStateResponse(engine: GameEngine): HarnessStateResponse {
  const state = engine.state;

  const committed = new Map<number, number>();
  const folded = new Set<number>();
  for (const seat of state.seats) {
    if (seat.totalCommittedThisHand > 0) committed.set(seat.seatNo, seat.totalCommittedThisHand);
    if (seat.status === "FOLDED") folded.add(seat.seatNo);
  }
  const pots = committed.size > 0 ? buildPots(committed, folded) : [];

  const players: HarnessPlayer[] = [];
  for (const seat of state.seats) {
    const status = SEAT_STATUS_TO_HARNESS[seat.status];
    if (status === null) continue; // EMPTY seats aren't players
    players.push({
      seat: seat.seatNo,
      stack: seat.stack,
      status,
      total_committed: seat.totalCommittedThisHand,
      current_bet: seat.betThisStreet,
    });
  }

  return {
    hand_in_progress: state.street !== null,
    current_actor: state.actingSeat,
    current_bet: state.currentBet,
    button_seat: state.buttonSeat ?? -1,
    community_cards: state.board.map(toHarnessCard),
    pots: pots.map((p) => ({ amount: p.amount, eligible_seats: p.eligibleSeats })),
    last_showdown: engine.getLastShowdown().map((s) => ({
      seat: s.seat,
      hole_cards: s.holeCards.map(toHarnessCard),
      hand_category: s.handCategory,
    })),
    players,
  };
}

function readJsonBody(req: IncomingMessage): Promise<unknown> {
  return new Promise((resolve, reject) => {
    const chunks: Buffer[] = [];
    req.on("data", (chunk: Buffer) => chunks.push(chunk));
    req.on("end", () => {
      const raw = Buffer.concat(chunks).toString("utf8").trim();
      if (raw === "") {
        resolve({});
        return;
      }
      try {
        resolve(JSON.parse(raw));
      } catch (err) {
        reject(err);
      }
    });
    req.on("error", reject);
  });
}

function sendJson(res: ServerResponse, status: number, body: unknown): void {
  res.writeHead(status, { "content-type": "application/json" });
  res.end(JSON.stringify(body));
}

function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null;
}

let tableCounter = 0;
function nextTableId(): string {
  tableCounter += 1;
  return `rest-table-${tableCounter}-${randomUUID().slice(0, 8)}`;
}

/**
 * Attempts to handle `req` as one of the fixed harness REST routes.
 * Returns true if it did (response already sent), false if the request
 * didn't match any REST route and the caller should fall through to its
 * other handling (e.g. GET /healthz, 404).
 */
export async function handleRestRequest(
  req: IncomingMessage,
  res: ServerResponse,
  tableManager: TableManager,
): Promise<boolean> {
  const method = req.method ?? "GET";
  const url = new URL(req.url ?? "/", "http://localhost");
  const parts = url.pathname.split("/").filter((p) => p.length > 0);

  // POST /tables
  if (method === "POST" && parts.length === 1 && parts[0] === "tables") {
    let body: unknown;
    try {
      body = await readJsonBody(req);
    } catch {
      sendJson(res, 400, { error: "malformed JSON body" });
      return true;
    }
    if (!isRecord(body)) {
      sendJson(res, 400, { error: "expected a JSON object body" });
      return true;
    }
    const smallBlind = Number(body.small_blind);
    const bigBlind = Number(body.big_blind);
    if (!Number.isFinite(smallBlind) || !Number.isFinite(bigBlind) || smallBlind <= 0 || bigBlind <= 0) {
      sendJson(res, 400, { error: "small_blind and big_blind must be positive numbers" });
      return true;
    }
    const tableId = nextTableId();
    const config: TableConfig = {
      tableId,
      smallBlind,
      bigBlind,
      maxSeats: REST_MAX_SEATS,
      minBuyIn: REST_MIN_BUY_IN,
      maxBuyIn: REST_MAX_BUY_IN,
      actionTimeoutMs: REST_ACTION_TIMEOUT_MS,
    };
    tableManager.createTable(tableId, config);
    sendJson(res, 200, { table_id: tableId });
    return true;
  }

  // Every remaining REST route is /tables/{id}/...
  if (parts.length >= 2 && parts[0] === "tables") {
    const tableId = decodeURIComponent(parts[1]!);
    const rest = parts.slice(2);

    // POST /tables/{id}/players
    if (method === "POST" && rest.length === 1 && rest[0] === "players") {
      const engine = tableManager.getTable(tableId);
      if (!engine) {
        sendJson(res, 404, { error: "table not found" });
        return true;
      }
      let body: unknown;
      try {
        body = await readJsonBody(req);
      } catch {
        sendJson(res, 400, { error: "malformed JSON body" });
        return true;
      }
      if (!isRecord(body) || typeof body.name !== "string" || typeof body.buy_in !== "number") {
        sendJson(res, 400, { error: "expected { name: string, buy_in: number }" });
        return true;
      }
      const seatNo = engine.state.seats.find((s) => s.status === "EMPTY")?.seatNo;
      if (seatNo === undefined) {
        sendJson(res, 400, { error: "table is full" });
        return true;
      }
      const playerId = `rest-${tableId}-${seatNo}-${randomUUID()}`;
      const rejection = engine.sit(seatNo, playerId, body.name, body.buy_in);
      if (rejection) {
        sendJson(res, 400, { error: rejection });
        return true;
      }
      sendJson(res, 200, { seat: seatNo });
      return true;
    }

    // POST /tables/{id}/start
    if (method === "POST" && rest.length === 1 && rest[0] === "start") {
      const engine = tableManager.getTable(tableId);
      if (!engine) {
        sendJson(res, 404, { error: "table not found" });
        return true;
      }
      if (engine.state.street === null) {
        const started = engine.tryStartHand();
        if (!started) {
          sendJson(res, 400, { error: "requires at least 2 seated players with chips" });
          return true;
        }
      }
      // Idempotent: if a hand is already in progress (e.g. it auto-chained
      // from a previous hand's settle), just report current state rather
      // than erroring.
      sendJson(res, 200, buildStateResponse(engine));
      return true;
    }

    // POST /tables/{id}/actions
    if (method === "POST" && rest.length === 1 && rest[0] === "actions") {
      const engine = tableManager.getTable(tableId);
      if (!engine) {
        sendJson(res, 404, { error: "table not found" });
        return true;
      }
      let body: unknown;
      try {
        body = await readJsonBody(req);
      } catch {
        sendJson(res, 400, { error: "malformed JSON body" });
        return true;
      }
      if (!isRecord(body) || typeof body.seat !== "number" || typeof body.action !== "string") {
        sendJson(res, 400, { error: "expected { seat: number, action: string, amount?: number }" });
        return true;
      }
      const wireAction = HARNESS_ACTION_TO_WIRE[body.action];
      if (!wireAction) {
        sendJson(res, 400, { error: `unknown action '${body.action}'` });
        return true;
      }
      const amount = typeof body.amount === "number" ? body.amount : undefined;
      const result = engine.submitAction(body.seat, randomUUID(), engine.state.handSeq, wireAction, amount);
      if (!result.applied) {
        sendJson(res, 400, { error: result.reason });
        return true;
      }
      sendJson(res, 200, buildStateResponse(engine));
      return true;
    }

    // GET /tables/{id}/state?seat={seat}
    if (method === "GET" && rest.length === 1 && rest[0] === "state") {
      const engine = tableManager.getTable(tableId);
      if (!engine) {
        sendJson(res, 404, { error: "table not found" });
        return true;
      }
      // `seat` is accepted per the contract's signature; the response shape
      // only ever carries hole cards inside last_showdown, which by poker
      // rules is already public to everyone once a hand reaches showdown —
      // so there is nothing left to redact per-seat in practice.
      sendJson(res, 200, buildStateResponse(engine));
      return true;
    }
  }

  return false;
}
