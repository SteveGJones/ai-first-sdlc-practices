import { useEffect, useState } from "react";
import type { SeatView } from "../state/tableView";
import { CardBack, PlayingCard } from "./Card";
import type { Card } from "../types/protocol";

interface SeatProps {
  seat: SeatView;
  isButton: boolean;
  isActing: boolean;
  actByMs: number | null;
  myHoleCards: [Card, Card] | null;
  revealedCards: [Card, Card] | undefined;
}

/** Pure display countdown — never authoritative for whether a timeout occurred
 * (design-client.md §4): the actual timeout is applied server-side. */
function useCountdown(actByMs: number | null): number | null {
  const [remaining, setRemaining] = useState<number | null>(
    actByMs === null ? null : Math.max(0, actByMs - Date.now())
  );

  useEffect(() => {
    if (actByMs === null) {
      setRemaining(null);
      return;
    }
    const tick = () => setRemaining(Math.max(0, actByMs - Date.now()));
    tick();
    const id = setInterval(tick, 250);
    return () => clearInterval(id);
  }, [actByMs]);

  return remaining;
}

export function Seat({ seat, isButton, isActing, actByMs, myHoleCards, revealedCards }: SeatProps) {
  const remainingMs = useCountdown(isActing ? actByMs : null);

  if (seat.status === "EMPTY") {
    return <div className="seat seat-empty">Open seat {seat.seatNo}</div>;
  }

  const holeCards: [Card, Card] | undefined = seat.isMe
    ? myHoleCards ?? undefined
    : revealedCards;

  return (
    <div className={`seat seat-${seat.status.toLowerCase()} ${isActing ? "seat-acting" : ""}`}>
      {isButton && <div className="button-chip" title="Dealer button">D</div>}
      <div className="seat-name">
        {seat.displayName ?? `Seat ${seat.seatNo}`}
        {seat.isMe && <span className="me-badge"> (you)</span>}
      </div>
      <div className="seat-hole-cards">
        {holeCards ? (
          <>
            <PlayingCard card={holeCards[0]} />
            <PlayingCard card={holeCards[1]} />
          </>
        ) : (
          <>
            <CardBack />
            <CardBack />
          </>
        )}
      </div>
      <div className="seat-stack">Stack: {seat.stack}</div>
      {seat.betThisStreet > 0 && <div className="seat-bet">Bet: {seat.betThisStreet}</div>}
      {seat.status === "ALL_IN" && <div className="badge badge-allin">ALL-IN</div>}
      {seat.status === "FOLDED" && <div className="badge badge-folded">FOLDED</div>}
      {seat.status === "SITTING_OUT" && <div className="badge badge-sitout">SITTING OUT</div>}
      {isActing && remainingMs !== null && (
        <div className="countdown">
          {(remainingMs / 1000).toFixed(1)}s
        </div>
      )}
    </div>
  );
}
