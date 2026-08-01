import { createPokerServer } from "./server.js";
import type { TableConfig } from "./types.js";

const PORT = Number(process.env.PORT ?? 8000);

const SMALL_BLIND = Number(process.env.SMALL_BLIND ?? 1);
const BIG_BLIND = Number(process.env.BIG_BLIND ?? 2);
const MAX_SEATS = Number(process.env.MAX_SEATS ?? 9);
const MIN_BUY_IN = Number(process.env.MIN_BUY_IN ?? 40);
const MAX_BUY_IN = Number(process.env.MAX_BUY_IN ?? 400);
const ACTION_TIMEOUT_MS = Number(process.env.ACTION_TIMEOUT_MS ?? 30000);

// Tables are created lazily on first reference (JOIN_TABLE / SIT /
// REQUEST_SYNC) and all share this fixed configuration — the design doc
// treats table config as "fixed at table creation," and this capstone
// scope has no table-admin API, so every table a client names gets the
// same standard-stakes config.
const defaultConfig = (tableId: string): TableConfig => ({
  tableId,
  smallBlind: SMALL_BLIND,
  bigBlind: BIG_BLIND,
  maxSeats: MAX_SEATS,
  minBuyIn: MIN_BUY_IN,
  maxBuyIn: MAX_BUY_IN,
  actionTimeoutMs: ACTION_TIMEOUT_MS,
});

const server = createPokerServer({ defaultConfig });

server.listen(PORT, () => {
  // eslint-disable-next-line no-console
  console.log(`poker-capstone-server listening on :${PORT} (GET /healthz, WS /ws)`);
});

process.on("SIGTERM", () => {
  server.close(() => process.exit(0));
});
process.on("SIGINT", () => {
  server.close(() => process.exit(0));
});
