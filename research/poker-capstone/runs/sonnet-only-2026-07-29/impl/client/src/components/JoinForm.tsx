import { useState } from "react";
import type { TableView } from "../state/tableView";

interface JoinFormProps {
  view: TableView;
  onSit: (seatNo: number, buyIn: number) => void;
  onSitOut: () => void;
  onSitIn: () => void;
}

export function JoinForm({ view, onSit, onSitOut, onSitIn }: JoinFormProps) {
  const [seatNo, setSeatNo] = useState<number>(0);
  const [buyIn, setBuyIn] = useState<number>(view.config?.minBuyIn ?? 0);

  const mySeatView = view.seats.find((s) => s.isMe);
  const openSeats = view.seats.filter((s) => s.status === "EMPTY");

  if (mySeatView) {
    return (
      <div className="join-form join-form-seated">
        Seated at seat {mySeatView.seatNo} — stack {mySeatView.stack}
        {mySeatView.status === "SITTING_OUT" ? (
          <button className="btn" onClick={onSitIn}>
            Sit back in
          </button>
        ) : (
          <button className="btn" onClick={onSitOut}>
            Sit out
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="join-form">
      <label>
        Seat
        <select value={seatNo} onChange={(e) => setSeatNo(Number(e.target.value))}>
          {openSeats.length === 0 && <option value={0}>No open seats</option>}
          {openSeats.map((s) => (
            <option key={s.seatNo} value={s.seatNo}>
              Seat {s.seatNo}
            </option>
          ))}
        </select>
      </label>
      <label>
        Buy-in
        <input
          type="number"
          min={view.config?.minBuyIn}
          max={view.config?.maxBuyIn}
          value={buyIn}
          onChange={(e) => setBuyIn(Number(e.target.value))}
        />
      </label>
      <button
        className="btn"
        disabled={openSeats.length === 0}
        onClick={() => onSit(seatNo, buyIn)}
      >
        Sit down
      </button>
    </div>
  );
}
