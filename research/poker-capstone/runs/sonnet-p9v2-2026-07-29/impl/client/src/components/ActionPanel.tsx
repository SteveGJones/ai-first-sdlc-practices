import { useEffect, useState } from "react";
import type { PlayerState, TableState } from "../types";

interface ActionPanelProps {
  state: TableState;
  mySeat: number;
  myPlayer: PlayerState | undefined;
  pending: boolean;
  errorMessage: string | null;
  onFold: () => void;
  onCheckCall: () => void;
  onBetRaise: (amount: number) => void;
  onStartHand: () => void;
}

// docs/CLIENT-TEST-CONTRACT.md "Action controls". design-client.md §3.1:
// the panel is enabled iff it is this seat's turn per the server's
// authoritative `current_actor` — a UX convenience only, never the real
// enforcement (the server independently re-validates every submitted
// action per HARNESS-CONTRACT.md).
export function ActionPanel({
  state,
  mySeat,
  myPlayer,
  pending,
  errorMessage,
  onFold,
  onCheckCall,
  onBetRaise,
  onStartHand,
}: ActionPanelProps) {
  const isMyTurn = state.hand_in_progress && state.current_actor === mySeat;
  const toCall = myPlayer ? Math.max(0, state.current_bet - myPlayer.current_bet) : 0;
  const isCall = toCall > 0;

  // Bet/raise sizing bounds: the minimum a bet/raise may reach is the
  // current bet plus the server's min_raise increment (or just min_raise
  // itself when there is no live bet yet, i.e. opening the betting), the
  // maximum is going all-in with the player's remaining stack.
  const minTotal = state.current_bet > 0 ? state.current_bet + state.min_raise : state.min_raise;
  const maxTotal = myPlayer ? myPlayer.stack + myPlayer.current_bet : minTotal;

  const [betAmount, setBetAmount] = useState<number>(minTotal);

  useEffect(() => {
    // Re-clamp the default whenever the legal range moves under us (new
    // turn, new street) so a stale value from a previous turn is never
    // silently submitted.
    setBetAmount((prev) => Math.min(Math.max(prev, minTotal), Math.max(maxTotal, minTotal)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [minTotal, maxTotal, state.current_actor]);

  const canAct = isMyTurn && !pending && !!myPlayer && myPlayer.status === "active";
  const canBetRaise = canAct && maxTotal >= minTotal;
  const canStart = !state.hand_in_progress && state.players.length >= 2 && !pending;

  return (
    <div className="action-panel">
      {errorMessage && <div className="action-panel__error">{errorMessage}</div>}
      <div className="action-panel__buttons">
        <button
          type="button"
          data-testid="action-fold"
          disabled={!canAct}
          onClick={onFold}
        >
          Fold
        </button>
        <button
          type="button"
          data-testid="action-check-call"
          disabled={!canAct}
          onClick={onCheckCall}
        >
          {isCall ? `Call ${toCall}` : "Check"}
        </button>
        <button
          type="button"
          data-testid="action-bet-raise"
          disabled={!canBetRaise}
          onClick={() => onBetRaise(betAmount)}
        >
          {state.current_bet > 0 ? "Raise to" : "Bet"} {betAmount}
        </button>
        <input
          data-testid="bet-amount-input"
          type="number"
          min={minTotal}
          max={Math.max(maxTotal, minTotal)}
          step={1}
          value={betAmount}
          disabled={!canBetRaise}
          onChange={(e) => setBetAmount(Number(e.target.value))}
        />
        <button
          type="button"
          data-testid="start-hand"
          disabled={!canStart}
          onClick={onStartHand}
        >
          Start hand
        </button>
      </div>
      {isMyTurn && (
        <div className="action-panel__hint">
          To call: {toCall} · min raise-to: {minTotal} · max (all-in): {Math.max(maxTotal, minTotal)}
        </div>
      )}
    </div>
  );
}
