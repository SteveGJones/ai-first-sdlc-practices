// HTTP + WebSocket server. Exposes:
//   - GET /healthz            liveness/readiness probe for the container
//   - GET/WS /ws              the single per-connection WebSocket from
//                              stage1/architecture.md §4, carrying the
//                              design-server.md §6 message contract.
//   - REST routes under /tables — the fixed harness contract from
//                              docs/HARNESS-CONTRACT.md (see restApi.ts).
//
// Player identity (design-server.md §2.2's "connectionId ⇄ playerId") is
// established with a `pid` cookie set on the WebSocket upgrade response:
// the browser resends it automatically on every reconnect, which is what
// lets §2.9 reconnection resolve a returning player back to their seat
// without requiring any login UI or client-side change. The REST facade
// bypasses this entirely — its routes address seats directly by number, as
// the harness contract requires, with no session/cookie concept.

import { randomUUID } from "node:crypto";
import { createServer, type IncomingMessage, type Server as HttpServer } from "node:http";
import { WebSocketServer, type WebSocket } from "ws";
import { handleRestRequest } from "./restApi.js";
import { TableManager, type DefaultConfigFactory } from "./tableManager.js";

const PID_COOKIE = "pid";

function parseCookies(header: string | undefined): Record<string, string> {
  const out: Record<string, string> = {};
  if (!header) return out;
  for (const part of header.split(";")) {
    const eq = part.indexOf("=");
    if (eq === -1) continue;
    const key = part.slice(0, eq).trim();
    const value = part.slice(eq + 1).trim();
    if (key) out[key] = decodeURIComponent(value);
  }
  return out;
}

export interface CreateServerOptions {
  defaultConfig: DefaultConfigFactory;
}

export function createPokerServer(options: CreateServerOptions): HttpServer {
  const tableManager = new TableManager(options.defaultConfig);

  const httpServer = createServer((req, res) => {
    if (req.method === "GET" && req.url === "/healthz") {
      res.writeHead(200, { "content-type": "application/json" });
      res.end(JSON.stringify({ status: "ok" }));
      return;
    }

    handleRestRequest(req, res, tableManager)
      .then((handled) => {
        if (handled) return;
        res.writeHead(404, { "content-type": "application/json" });
        res.end(JSON.stringify({ error: "not_found" }));
      })
      .catch((err: unknown) => {
        if (res.headersSent) return;
        res.writeHead(500, { "content-type": "application/json" });
        res.end(JSON.stringify({ error: err instanceof Error ? err.message : "internal_error" }));
      });
  });

  const wss = new WebSocketServer({ noServer: true });

  // Injects Set-Cookie into the WS upgrade response so the identity cookie
  // is established on first connect without any extra HTTP round trip.
  wss.on("headers", (headers: string[], req: IncomingMessage) => {
    const cookies = parseCookies(req.headers.cookie);
    if (!cookies[PID_COOKIE]) {
      const pid = randomUUID();
      (req as IncomingMessage & { __assignedPid?: string }).__assignedPid = pid;
      headers.push(`Set-Cookie: ${PID_COOKIE}=${pid}; Path=/; Max-Age=2592000; SameSite=Lax`);
    }
  });

  httpServer.on("upgrade", (req, socket, head) => {
    if (req.url !== "/ws" && !req.url?.startsWith("/ws?")) {
      socket.destroy();
      return;
    }
    wss.handleUpgrade(req, socket, head, (ws) => {
      wss.emit("connection", ws, req);
    });
  });

  wss.on("connection", (ws: WebSocket, req: IncomingMessage) => {
    const cookies = parseCookies(req.headers.cookie);
    const playerId = cookies[PID_COOKIE] ?? (req as IncomingMessage & { __assignedPid?: string }).__assignedPid ?? randomUUID();
    const displayName = `Player-${playerId.slice(0, 4)}`;

    tableManager.registerConnection(ws, playerId, displayName);

    ws.on("message", (data) => {
      tableManager.handleRawMessage(ws, data.toString());
    });
    ws.on("close", () => {
      tableManager.removeConnection(ws);
    });
    ws.on("error", () => {
      // 'close' fires right after; cleanup happens there.
    });
  });

  return httpServer;
}
