import type { TableView } from "../state/tableView";
import { Board } from "./Board";
import { Seat } from "./Seat";
import { ActionPanel } from "./ActionPanel";
import { Showdown } from "./Showdown";
import { ConnectionBanner } from "./ConnectionBanner";
import { JoinForm } from "./JoinForm";
import type { ActionType } from "../types/protocol";

interface TableProps {
  view: TableView;
  pendingTimedOut: boolean;
  onSubmitAction: (action: ActionType, amount?: number) => void;
  onSit: (seatNo: number, buyIn: number) => void;
  onSitOut: () => void;
  onSitIn: () => void;
}

export function Table({ view, pendingTimedOut, onSubmitAction, onSit, onSitOut, onSitIn }: TableProps) {
  const revealedBySeat = new Map(
    (view.showdown?.revealedHands ?? []).map((r) => [r.seat, r.cards])
  );

  return (
    <div className="table">
      <ConnectionBanner status={view.connectionStatus} />
      <JoinForm view={view} onSit={onSit} onSitOut={onSitOut} onSitIn={onSitIn} />
      <Board view={view} />
      <div className="seats-ring">
        {view.seats.map((seat) => (
          <Seat
            key={seat.seatNo}
            seat={seat}
            isButton={view.buttonSeat === seat.seatNo}
            isActing={view.actingSeat === seat.seatNo}
            actByMs={view.actByMs}
            myHoleCards={view.myHoleCards}
            revealedCards={revealedBySeat.get(seat.seatNo)}
          />
        ))}
      </div>
      <Showdown view={view} />
      <ActionPanel view={view} pendingTimedOut={pendingTimedOut} onSubmit={onSubmitAction} />
    </div>
  );
}
