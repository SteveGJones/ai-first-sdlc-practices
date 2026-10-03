import type { ReactNode } from "react";
import type { TableState } from "../types";

interface TableMirrorProps {
  state: TableState;
  children: ReactNode;
}

// docs/CLIENT-TEST-CONTRACT.md "Table-level state mirror" — one element,
// always present once loaded, carrying the table-scoped fields verbatim
// from the REST state response.
export function TableMirror({ state, children }: TableMirrorProps) {
  return (
    <div
      className="table"
      data-testid="table"
      data-hand-in-progress={state.hand_in_progress ? "true" : "false"}
      data-current-actor={state.current_actor === null ? "" : state.current_actor}
      data-current-bet={state.current_bet}
      data-button-seat={state.button_seat === null ? "" : state.button_seat}
    >
      {children}
    </div>
  );
}
