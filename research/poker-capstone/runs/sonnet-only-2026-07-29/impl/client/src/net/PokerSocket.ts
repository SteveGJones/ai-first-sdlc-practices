import type { ClientMessage, ServerEvent } from "../types/protocol";
import { getServerWsUrl } from "./serverConfig";

export type SocketLifecycleListener = (state: "OPEN" | "CLOSED" | "RECONNECTING") => void;
export type ServerEventListener = (event: ServerEvent) => void;

const INITIAL_BACKOFF_MS = 500;
const MAX_BACKOFF_MS = 8000;

/**
 * Thin transport wrapper: owns the single WebSocket connection, retries
 * with exponential backoff on drop, and hands parsed ServerEvents to a
 * listener. It carries no game state and no gap-detection logic itself —
 * that lives one layer up (useTableConnection), per design-client.md §1
 * (the client's single authoritative store is TableView, not the socket).
 */
export class PokerSocket {
  private ws: WebSocket | null = null;
  private backoffMs = INITIAL_BACKOFF_MS;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private closedByUser = false;

  constructor(
    private readonly onEvent: ServerEventListener,
    private readonly onLifecycle: SocketLifecycleListener
  ) {}

  connect(): void {
    this.closedByUser = false;
    this.openSocket();
  }

  private openSocket(): void {
    const url = getServerWsUrl();
    const ws = new WebSocket(url);
    this.ws = ws;

    ws.onopen = () => {
      this.backoffMs = INITIAL_BACKOFF_MS;
      this.onLifecycle("OPEN");
    };

    ws.onmessage = (evt) => {
      try {
        const parsed = JSON.parse(evt.data as string) as ServerEvent;
        this.onEvent(parsed);
      } catch {
        // Malformed frame from the wire: nothing we can safely apply.
        // The gap-detection layer above will notice via REQUEST_SYNC if
        // this caused us to miss meaningful state.
      }
    };

    ws.onclose = () => {
      this.ws = null;
      if (this.closedByUser) {
        this.onLifecycle("CLOSED");
        return;
      }
      this.onLifecycle("RECONNECTING");
      this.scheduleReconnect();
    };

    ws.onerror = () => {
      // onclose will fire right after; reconnect is scheduled there.
    };
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer !== null) return;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      if (!this.closedByUser) this.openSocket();
    }, this.backoffMs);
    this.backoffMs = Math.min(this.backoffMs * 2, MAX_BACKOFF_MS);
  }

  send(message: ClientMessage): boolean {
    if (this.ws === null || this.ws.readyState !== WebSocket.OPEN) return false;
    this.ws.send(JSON.stringify(message));
    return true;
  }

  close(): void {
    this.closedByUser = true;
    if (this.reconnectTimer !== null) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.ws?.close();
    this.ws = null;
  }
}
