import { useEffect, useState } from "react";
import type { TableView } from "../state/tableView";
import type { ActionType } from "../types/protocol";

const REJECTION_MESSAGES: Record<string, string> = {
  NOT_SEATED: "You aren't seated at this table.",
  NOT_ACCEPTING_ACTIONS: "The table isn't accepting actions right now.",
  NOT_YOUR_TURN: "That wasn't your turn — the table has moved on.",
  ILLEGAL_ACTION: "That action isn't legal right now.",
  INVALID_AMOUNT: "Bet amount is out of range.",
  STALE_HAND: "That action was for a hand that has already ended.",
};

interface ActionPanelProps {
  view: TableView;
  pendingTimedOut: boolean;
  onSubmit: (action: ActionType, amount?: number) => void;
}

export function ActionPanel({ view, pendingTimedOut, onSubmit }: ActionPanelProps) {
  const isMyTurn = view.mySeat !== null && view.actingSeat === view.mySeat;
  const legalActions = isMyTurn ? view.legalActionsForMe : [];
  const enabled = isMyTurn && legalActions.length > 0 && view.pendingAction === null;

  const [raiseTo, setRaiseTo] = useState(view.minRaiseTo);
  useEffect(() => {
    setRaiseTo(view.minRaiseTo);
  }, [view.minRaiseTo, view.actingSeat]);

  if (!isMyTurn) {
    const actingLabel =
      view.actingSeat !== null
        ? view.seats.find((s) => s.seatNo === view.actingSeat)?.displayName ??
          `seat ${view.actingSeat}`
        : null;
    return (
      <div className="action-panel action-panel-disabled">
        {actingLabel ? `Waiting for ${actingLabel}'s action…` : "Waiting for the next hand…"}
      </div>
    );
  }

  const canCheck = legalActions.includes("CHECK");
  const canCall = legalActions.includes("CALL");
  const canRaise = legalActions.includes("RAISE");
  const canFold = legalActions.includes("FOLD");

  const rejectionMessage =
    view.lastRejection && Date.now() - view.lastRejection.at < 6000
      ? REJECTION_MESSAGES[view.lastRejection.reason] ?? view.lastRejection.reason
      : null;

  return (
    <div className="action-panel">
      <div className="action-buttons">
        {canFold && (
          <button
            className="btn btn-fold"
            disabled={!enabled}
            onClick={() => onSubmit("FOLD")}
          >
            Fold
          </button>
        )}
        {canCheck && (
          <button
            className="btn btn-check"
            disabled={!enabled}
            onClick={() => onSubmit("CHECK")}
          >
            Check
          </button>
        )}
        {canCall && (
          <button
            className="btn btn-call"
            disabled={!enabled}
            onClick={() => onSubmit("CALL")}
          >
            Call {view.toCall}
          </button>
        )}
        {canRaise && (
          <div className="raise-control">
            <input
              type="range"
              min={view.minRaiseTo}
              max={view.maxRaiseTo}
              value={raiseTo}
              disabled={!enabled}
              onChange={(e) => setRaiseTo(Number(e.target.value))}
            />
            <div className="raise-amount">
              {raiseTo}
              {raiseTo >= view.maxRaiseTo && <span className="all-in-label"> (All-in)</span>}
            </div>
            <button
              className="btn btn-raise"
              disabled={!enabled}
              onClick={() => onSubmit("RAISE", raiseTo)}
            >
              {view.toCall === 0 ? "Bet" : "Raise to"} {raiseTo}
            </button>
          </div>
        )}
      </div>
      {view.pendingAction && (
        <div className="pending-indicator">
          {pendingTimedOut ? "Still waiting for the server…" : "Waiting for server…"}
        </div>
      )}
      {rejectionMessage && <div className="rejection-message">{rejectionMessage}</div>}
    </div>
  );
}
