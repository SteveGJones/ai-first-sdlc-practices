// Table Manager: owns all GameEngine instances, connection identity
// (connectionId ⇄ playerId ⇄ (tableId, seatNo) — design-server.md §2.2),
// and routes inbound ClientMessages to the right table's engine. Tables are
// created lazily on first reference to a tableId (the design doc specifies
// no lobby/admin API, only that tables pre-exist with fixed config).

import type { WebSocket } from "ws";
import { GameEngine, type EngineIO } from "./engine.js";
import { toWireEvent } from "./wireProtocol.js";
import type { ClientMessage, ServerEvent, TableConfig } from "./types.js";

interface ConnectionState {
  connectionId: string;
  playerId: string;
  displayName: string;
  ws: WebSocket;
  /** Table this connection most recently sat at — resolves table-less ACTION messages. */
  currentTableId: string | null;
}

export type DefaultConfigFactory = (tableId: string) => TableConfig;

export class TableManager {
  private readonly tables = new Map<string, GameEngine>();
  private readonly tableWatchers = new Map<string, Set<WebSocket>>();
  private readonly connections = new Map<WebSocket, ConnectionState>();
  private readonly connectionsByPlayer = new Map<string, Set<WebSocket>>();
  /** playerId -> tableId -> seatNo, persisted across reconnects (§2.9). */
  private readonly seatByPlayerTable = new Map<string, Map<string, number>>();

  constructor(private readonly defaultConfig: DefaultConfigFactory) {}

  // ---------------------------------------------------------------------
  // Connection lifecycle
  // ---------------------------------------------------------------------

  registerConnection(ws: WebSocket, playerId: string, displayName: string): void {
    const connectionId = `${playerId}:${Date.now()}:${Math.random().toString(36).slice(2)}`;
    const knownTables = this.seatByPlayerTable.get(playerId);
    const currentTableId = knownTables && knownTables.size > 0 ? [...knownTables.keys()][0]! : null;

    this.connections.set(ws, { connectionId, playerId, displayName, ws, currentTableId });
    let sockets = this.connectionsByPlayer.get(playerId);
    if (!sockets) {
      sockets = new Set();
      this.connectionsByPlayer.set(playerId, sockets);
    }
    const isReconnect = sockets.size > 0 || (knownTables?.size ?? 0) > 0;
    sockets.add(ws);

    if (currentTableId !== null) {
      const engine = this.tables.get(currentTableId);
      const seatNo = knownTables!.get(currentTableId)!;
      this.watch(currentTableId, ws);
      if (engine && isReconnect) engine.handleReconnect(seatNo);
    }
  }

  removeConnection(ws: WebSocket): void {
    const conn = this.connections.get(ws);
    if (!conn) return;
    this.connections.delete(ws);
    this.connectionsByPlayer.get(conn.playerId)?.delete(ws);
    for (const watchers of this.tableWatchers.values()) watchers.delete(ws);

    if (conn.currentTableId !== null) {
      const remaining = this.connectionsByPlayer.get(conn.playerId);
      const stillConnected = remaining && remaining.size > 0;
      if (!stillConnected) {
        const engine = this.tables.get(conn.currentTableId);
        const seatNo = this.seatByPlayerTable.get(conn.playerId)?.get(conn.currentTableId);
        if (engine && seatNo !== undefined) engine.handleDisconnect(seatNo);
      }
    }
  }

  // ---------------------------------------------------------------------
  // Inbound message handling
  // ---------------------------------------------------------------------

  handleRawMessage(ws: WebSocket, raw: string): void {
    const conn = this.connections.get(ws);
    if (!conn) return;

    let msg: ClientMessage;
    try {
      msg = JSON.parse(raw) as ClientMessage;
    } catch {
      this.send(ws, { type: "ERROR", code: "MALFORMED_JSON", message: "Message body is not valid JSON." });
      return;
    }
    if (typeof msg !== "object" || msg === null || typeof (msg as { type?: unknown }).type !== "string") {
      this.send(ws, { type: "ERROR", code: "MALFORMED_MESSAGE", message: "Missing or invalid 'type' field." });
      return;
    }

    try {
      this.dispatch(conn, msg);
    } catch (err) {
      this.send(ws, {
        type: "ERROR",
        code: "INTERNAL_ERROR",
        message: err instanceof Error ? err.message : "Unexpected server error.",
      });
    }
  }

  private dispatch(conn: ConnectionState, msg: ClientMessage): void {
    switch (msg.type) {
      case "JOIN_TABLE": {
        const engine = this.getOrCreateTable(msg.tableId);
        this.watch(msg.tableId, conn.ws);
        this.send(conn.ws, engine.publicTableStateEvent());
        return;
      }

      case "SIT": {
        const engine = this.getOrCreateTable(msg.tableId);
        this.watch(msg.tableId, conn.ws);
        const rejection = engine.sit(msg.seatNo, conn.playerId, msg.displayName ?? conn.displayName, msg.buyIn);
        if (rejection) {
          this.send(conn.ws, { type: "ACTION_REJECTED", actionId: null, reason: rejection });
          return;
        }
        this.rememberSeat(conn.playerId, msg.tableId, msg.seatNo);
        conn.currentTableId = msg.tableId;
        // WS/client UX: a hand starts automatically once ≥2 players are
        // seated (design-server.md §1's WAITING_FOR_PLAYERS transition).
        // REST-driven tables don't get this — see GameEngine.tryStartHand's
        // doc comment — because the harness controls dealing explicitly via
        // POST /tables/{id}/start.
        engine.tryStartHand();
        return;
      }

      case "SIT_OUT": {
        const engine = this.tables.get(msg.tableId);
        const seatNo = this.seatFor(conn.playerId, msg.tableId);
        if (engine && seatNo !== undefined) engine.requestSitOut(seatNo);
        return;
      }

      case "SIT_IN": {
        const engine = this.tables.get(msg.tableId);
        const seatNo = this.seatFor(conn.playerId, msg.tableId);
        if (engine && seatNo !== undefined) engine.requestSitIn(seatNo);
        return;
      }

      case "ACTION": {
        const tableId = conn.currentTableId;
        const engine = tableId ? this.tables.get(tableId) : undefined;
        const seatNo = tableId ? this.seatFor(conn.playerId, tableId) : undefined;
        if (!engine || seatNo === undefined) {
          this.send(conn.ws, { type: "ACTION_REJECTED", actionId: msg.actionId, reason: "NOT_SEATED" });
          return;
        }
        engine.submitAction(seatNo, msg.actionId, msg.handSeq, msg.action, msg.amount);
        return;
      }

      case "REQUEST_SYNC": {
        const engine = this.getOrCreateTable(msg.tableId);
        this.watch(msg.tableId, conn.ws);
        const seatNo = this.seatFor(conn.playerId, msg.tableId) ?? null;
        this.send(conn.ws, engine.stateSyncFor(seatNo));
        return;
      }

      case "LEAVE_TABLE": {
        const engine = this.tables.get(msg.tableId);
        const seatNo = this.seatFor(conn.playerId, msg.tableId);
        if (engine && seatNo !== undefined) {
          engine.requestLeave(seatNo);
          this.forgetSeat(conn.playerId, msg.tableId);
          if (conn.currentTableId === msg.tableId) conn.currentTableId = null;
        }
        this.unwatch(msg.tableId, conn.ws);
        return;
      }

      default: {
        const _exhaustive: never = msg;
        void _exhaustive;
      }
    }
  }

  // ---------------------------------------------------------------------
  // Table registry + EngineIO wiring
  // ---------------------------------------------------------------------

  getOrCreateTable(tableId: string): GameEngine {
    return this.tables.get(tableId) ?? this.instantiate(tableId, this.defaultConfig(tableId));
  }

  /** Explicit-config table creation for the REST facade (POST /tables). */
  createTable(tableId: string, config: TableConfig): GameEngine {
    if (this.tables.has(tableId)) {
      throw new Error(`table '${tableId}' already exists`);
    }
    return this.instantiate(tableId, config);
  }

  getTable(tableId: string): GameEngine | undefined {
    return this.tables.get(tableId);
  }

  private instantiate(tableId: string, config: TableConfig): GameEngine {
    const io: EngineIO = {
      broadcastToTable: (event) => this.broadcastToTable(tableId, event),
      sendToSeat: (seatNo, event) => this.sendToSeat(tableId, seatNo, event),
    };
    const engine = new GameEngine(config, io);
    this.tables.set(tableId, engine);
    return engine;
  }

  private broadcastToTable(tableId: string, event: ServerEvent): void {
    const targets = new Set<WebSocket>(this.tableWatchers.get(tableId) ?? []);
    const engine = this.tables.get(tableId);
    if (engine) {
      for (const seat of engine.state.seats) {
        if (!seat.playerId) continue;
        for (const ws of this.connectionsByPlayer.get(seat.playerId) ?? []) targets.add(ws);
      }
    }
    for (const ws of targets) this.send(ws, event);
  }

  private sendToSeat(tableId: string, seatNo: number, event: ServerEvent): void {
    const engine = this.tables.get(tableId);
    const seat = engine?.state.seats[seatNo];
    if (!seat?.playerId) return;
    for (const ws of this.connectionsByPlayer.get(seat.playerId) ?? []) this.send(ws, event);
  }

  private send(ws: WebSocket, event: ServerEvent): void {
    if (ws.readyState !== ws.OPEN) return;
    ws.send(JSON.stringify(toWireEvent(event)));
  }

  private watch(tableId: string, ws: WebSocket): void {
    let set = this.tableWatchers.get(tableId);
    if (!set) {
      set = new Set();
      this.tableWatchers.set(tableId, set);
    }
    set.add(ws);
  }

  private unwatch(tableId: string, ws: WebSocket): void {
    this.tableWatchers.get(tableId)?.delete(ws);
  }

  private rememberSeat(playerId: string, tableId: string, seatNo: number): void {
    let byTable = this.seatByPlayerTable.get(playerId);
    if (!byTable) {
      byTable = new Map();
      this.seatByPlayerTable.set(playerId, byTable);
    }
    byTable.set(tableId, seatNo);
  }

  private forgetSeat(playerId: string, tableId: string): void {
    this.seatByPlayerTable.get(playerId)?.delete(tableId);
  }

  private seatFor(playerId: string, tableId: string): number | undefined {
    return this.seatByPlayerTable.get(playerId)?.get(tableId);
  }
}
