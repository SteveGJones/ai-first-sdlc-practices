// REST facade — HARNESS-CONTRACT.md (normative, fixed wire API). This is
// the only externally-observable surface the stage-4 harness drives; all
// design-server.md algorithms (turn state machine, side pots, hand
// evaluation) live behind it in engine.ts, untouched by this file.

import express, { NextFunction, Request, Response } from 'express';
import { PokerError } from './types';
import { RestAction, Table } from './engine';

const app = express();

// Permissive CORS on every REST response — HARNESS-CONTRACT.md "Cross-origin
// access (CORS)" section. The harness's browser-based client verification
// loads a client on one host-mapped port and fetches this server on another;
// without these headers the browser blocks the request before it ever
// reaches a route handler, regardless of how correct the REST logic is.
// Implemented as plain middleware (no `cors` package) to avoid adding a
// dependency for what is otherwise three header writes.
app.use((req, res, next) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, PATCH, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', '*');
  if (req.method === 'OPTIONS') {
    res.status(204).end();
    return;
  }
  next();
});

app.use(express.json());

const tables = new Map<string, Table>();

function getTableOrThrow(id: string): Table {
  const table = tables.get(id);
  if (!table) {
    throw new PokerError('TABLE_NOT_FOUND', `no table with id ${id}`, 404);
  }
  return table;
}

function parseSeatQuery(raw: unknown): number | null {
  if (raw === undefined) {
    throw new PokerError('SEAT_REQUIRED', 'seat query parameter is required', 422);
  }
  const n = Number(raw);
  if (!Number.isInteger(n)) {
    throw new PokerError('INVALID_SEAT', 'seat query parameter must be an integer', 422);
  }
  return n;
}

app.get('/healthz', (_req, res) => {
  res.status(200).json({ status: 'ok' });
});

app.post('/tables', (req, res) => {
  const { small_blind, big_blind } = req.body ?? {};
  if (!Number.isFinite(small_blind) || !Number.isFinite(big_blind) || small_blind <= 0 || big_blind <= 0) {
    throw new PokerError('INVALID_BLINDS', 'small_blind and big_blind must be positive numbers', 400);
  }
  const table = new Table(Math.trunc(small_blind), Math.trunc(big_blind));
  tables.set(table.id, table);
  res.status(200).json({ table_id: table.id });
});

app.post('/tables/:id/players', (req, res) => {
  const table = getTableOrThrow(req.params.id);
  const { name, buy_in } = req.body ?? {};
  if (typeof name !== 'string' || name.length === 0) {
    throw new PokerError('INVALID_NAME', 'name is required', 400);
  }
  const seat = table.addPlayer(name, buy_in);
  res.status(200).json({ seat });
});

app.post('/tables/:id/start', (req, res) => {
  const table = getTableOrThrow(req.params.id);
  table.startHand();
  res.status(200).json(table.toStateView(null));
});

const VALID_ACTIONS: RestAction[] = ['fold', 'check', 'call', 'bet', 'raise'];

app.post('/tables/:id/actions', (req, res) => {
  const table = getTableOrThrow(req.params.id);
  const { seat, action, amount } = req.body ?? {};
  if (!Number.isInteger(seat)) {
    throw new PokerError('INVALID_SEAT', 'seat is required and must be an integer', 400);
  }
  if (typeof action !== 'string' || !VALID_ACTIONS.includes(action as RestAction)) {
    throw new PokerError('INVALID_ACTION', `action must be one of ${VALID_ACTIONS.join(', ')}`, 400);
  }
  table.applyAction(seat, action as RestAction, amount);
  res.status(200).json(table.toStateView(null));
});

app.get('/tables/:id/state', (req, res) => {
  const table = getTableOrThrow(req.params.id);
  const seat = parseSeatQuery(req.query.seat);
  res.status(200).json(table.toStateView(seat));
});

// Centralized error handling — PokerError carries its own HTTP status and
// a stable machine-readable `code`; anything else is a 500.
// eslint-disable-next-line @typescript-eslint/no-unused-vars
app.use((err: unknown, _req: Request, res: Response, _next: NextFunction) => {
  if (err instanceof PokerError) {
    res.status(err.httpStatus).json({ error: err.code, detail: err.message });
    return;
  }
  // eslint-disable-next-line no-console
  console.error(err);
  res.status(500).json({ error: 'INTERNAL_ERROR', detail: 'unexpected server error' });
});

// Express 4 doesn't catch synchronous throws inside route handlers unless
// wrapped; wrap every handler registration above by catching here via a
// process-wide guard as a defense-in-depth measure (routes above throw
// PokerError synchronously and Express 4 *does* forward sync throws from
// a route handler to error middleware, but we keep this belt-and-braces
// for any unexpected runtime error).
process.on('unhandledRejection', (reason) => {
  // eslint-disable-next-line no-console
  console.error('Unhandled rejection:', reason);
});

const PORT = process.env.PORT ? Number(process.env.PORT) : 8000;
app.listen(PORT, () => {
  // eslint-disable-next-line no-console
  console.log(`Poker capstone server listening on :${PORT}`);
});

export default app;
