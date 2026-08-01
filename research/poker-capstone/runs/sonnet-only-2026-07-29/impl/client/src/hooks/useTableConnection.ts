import { useCallback, useEffect, useRef, useState } from "react";
import type { ActionType, ClientMessage, ServerEvent } from "../types/protocol";
import { hasActionSeq } from "../types/protocol";
import { PokerSocket } from "../net/PokerSocket";
import {
  applyServerEvent,
  createInitialTableView,
  withMySeat,
  type TableView,
} from "../state/tableView";

const UI_ACTION_TIMEOUT_MS = 5000;

function makeActionId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  // Fallback for environments without crypto.randomUUID.
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export interface UseTableConnectionResult {
  view: TableView;
  /** True once no ACTION_APPLIED/ACTION_REJECTED has arrived within the UI-side timeout. */
  pendingTimedOut: boolean;
  join: (tableId: string) => void;
  sit: (tableId: string, seatNo: number, buyIn: number) => void;
  sitOut: (tableId: string) => void;
  sitIn: (tableId: string) => void;
  leaveTable: (tableId: string) => void;
  submitAction: (action: ActionType, amount?: number) => void;
  requestSync: (tableId: string) => void;
}

/**
 * Ties the transport (PokerSocket) to the single-store reducer
 * (applyServerEvent) and implements the gap-detection / resync contract
 * from design-client.md §2.2–2.3 and design-server.md §6.3.
 */
export function useTableConnection(tableId: string): UseTableConnectionResult {
  const [view, setView] = useState<TableView>(() => createInitialTableView(tableId));
  const [pendingTimedOut, setPendingTimedOut] = useState(false);
  const socketRef = useRef<PokerSocket | null>(null);
  const viewRef = useRef(view);
  viewRef.current = view;
  const tableIdRef = useRef(tableId);
  tableIdRef.current = tableId;
  const pendingTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const send = useCallback((message: ClientMessage) => {
    socketRef.current?.send(message);
  }, []);

  const requestSync = useCallback(
    (id: string) => {
      send({ type: "REQUEST_SYNC", tableId: id });
    },
    [send]
  );

  const handleEvent = useCallback(
    (event: ServerEvent) => {
      setView((prev) => {
        // Gap detection (design-client.md §2.2): any event carrying
        // actionSeq must be exactly prev.actionSeq + 1 for the same hand,
        // unless it *is* the resync response (STATE_SYNC), which always
        // wins by replacing state wholesale.
        if (event.type !== "STATE_SYNC" && hasActionSeq(event)) {
          const sameHand = event.handSeq === prev.handSeq;
          const expected = prev.actionSeq + 1;
          if (!sameHand || event.actionSeq !== expected) {
            // Missed a message: do not attempt to interpolate. Mark
            // DESYNCED, ask the server for a fresh snapshot, and drop
            // this event — STATE_SYNC will supersede it shortly.
            requestSync(tableIdRef.current);
            return { ...prev, connectionStatus: "DESYNCED" };
          }
        }
        return applyServerEvent(prev, event);
      });
    },
    [requestSync]
  );

  const handleLifecycle = useCallback(
    (state: "OPEN" | "CLOSED" | "RECONNECTING") => {
      if (state === "OPEN") {
        // Never resume from cached TableView after a reconnect — always
        // re-request a fresh snapshot (design-client.md §2.3).
        setView((prev) => ({ ...prev, connectionStatus: "CONNECTED" }));
        requestSync(tableIdRef.current);
      } else if (state === "RECONNECTING") {
        setView((prev) => ({ ...prev, connectionStatus: "RECONNECTING" }));
      }
    },
    [requestSync]
  );

  useEffect(() => {
    const socket = new PokerSocket(handleEvent, handleLifecycle);
    socketRef.current = socket;
    socket.connect();
    return () => {
      socket.close();
      socketRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // UI-side "still waiting" indicator for a pending action, distinct from
  // and shorter than the server's own action timeout (design-client.md §3.2.7).
  useEffect(() => {
    if (pendingTimerRef.current !== null) {
      clearTimeout(pendingTimerRef.current);
      pendingTimerRef.current = null;
    }
    setPendingTimedOut(false);
    if (view.pendingAction !== null) {
      pendingTimerRef.current = setTimeout(() => {
        setPendingTimedOut(true);
      }, UI_ACTION_TIMEOUT_MS);
    }
    return () => {
      if (pendingTimerRef.current !== null) {
        clearTimeout(pendingTimerRef.current);
        pendingTimerRef.current = null;
      }
    };
  }, [view.pendingAction]);

  const join = useCallback(
    (id: string) => send({ type: "JOIN_TABLE", tableId: id }),
    [send]
  );

  const sit = useCallback(
    (id: string, seatNo: number, buyIn: number) => {
      // Identity, not game outcome: the requested seat becomes "mine" the
      // instant the request is sent, purely so the UI can attribute the
      // right seat once TABLE_STATE/STATE_SYNC confirms it. If the server
      // rejects the SIT (seat taken, bad buy-in, etc.) the next
      // TABLE_STATE/STATE_SYNC corrects this — it is never treated as an
      // authoritative game-state fact ahead of server confirmation.
      setView((prev) => withMySeat(prev, seatNo));
      send({ type: "SIT", tableId: id, seatNo, buyIn });
    },
    [send]
  );

  const sitOut = useCallback((id: string) => send({ type: "SIT_OUT", tableId: id }), [send]);
  const sitIn = useCallback((id: string) => send({ type: "SIT_IN", tableId: id }), [send]);
  const leaveTable = useCallback(
    (id: string) => send({ type: "LEAVE_TABLE", tableId: id }),
    [send]
  );

  const submitAction = useCallback(
    (action: ActionType, amount?: number) => {
      const current = viewRef.current;
      const actionId = makeActionId();
      // Optimistic UI: only disables the panel / shows pending status —
      // never predicts stack/pot/board outcomes (design-client.md §3.2.4).
      setView((prev) => ({ ...prev, pendingAction: { actionId, action, amount } }));
      send({
        type: "ACTION",
        actionId,
        handSeq: current.handSeq,
        action,
        ...(amount !== undefined ? { amount } : {}),
      });
    },
    [send]
  );

  return { view, pendingTimedOut, join, sit, sitOut, sitIn, leaveTable, submitAction, requestSync };
}

/** Helper for wiring up an out-of-band "this is my seat" fact if the app learns it separately. */
export function applyMySeat(view: TableView, mySeat: number | null): TableView {
  return withMySeat(view, mySeat);
}
