import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, fetchState } from "./api";
import type { TableState } from "./types";

export type ConnectionStatus = "connecting" | "connected" | "reconnecting" | "error";

interface UseTablePollingResult {
  state: TableState | null;
  status: ConnectionStatus;
  lastError: string | null;
  refresh: () => Promise<void>;
}

// design-client.md's Stage 1/2 design specifies a WebSocket push channel
// for the live game loop; docs/HARNESS-CONTRACT.md fixes the wire API this
// client must actually speak to a real server as REST-only (no WS
// endpoint is part of that fixed contract). This client therefore realizes
// the same "the client is a pure projection of the last-received server
// state" principle (design-client.md §1) over polling instead of a socket:
// TableView-equivalent state is only ever replaced wholesale from the
// latest GET /state response, never locally derived or advanced, which
// keeps the client just as "dumb" as the original design requires — only
// the transport differs.
export function useTablePolling(
  tableId: string | null,
  seat: number | null,
  intervalMs = 750,
): UseTablePollingResult {
  const [state, setState] = useState<TableState | null>(null);
  const [status, setStatus] = useState<ConnectionStatus>("connecting");
  const [lastError, setLastError] = useState<string | null>(null);
  const timerRef = useRef<number | null>(null);
  const inFlightRef = useRef(false);

  const refresh = useCallback(async () => {
    if (tableId === null || seat === null) return;
    if (inFlightRef.current) return;
    inFlightRef.current = true;
    try {
      const next = await fetchState(tableId, seat);
      setState(next);
      setStatus("connected");
      setLastError(null);
    } catch (err) {
      setStatus((prev) => (prev === "connected" ? "reconnecting" : "error"));
      setLastError(err instanceof ApiError ? err.detail : String(err));
    } finally {
      inFlightRef.current = false;
    }
  }, [tableId, seat]);

  useEffect(() => {
    if (tableId === null || seat === null) return;
    void refresh();
    timerRef.current = window.setInterval(() => {
      void refresh();
    }, intervalMs);
    return () => {
      if (timerRef.current !== null) window.clearInterval(timerRef.current);
    };
  }, [tableId, seat, intervalMs, refresh]);

  return { state, status, lastError, refresh };
}
