import type { PlayerState, ShowdownEntry } from "../types";
import { HoleCard } from "./HoleCard";

interface SeatProps {
  player: PlayerState;
  isMe: boolean;
  isButton: boolean;
  isActing: boolean;
  showdownEntry: ShowdownEntry | undefined;
}

// docs/CLIENT-TEST-CONTRACT.md "Per-seat state mirror" + "Hole cards".
//
// Card visibility: design-client.md §5 is explicit that a client only ever
// renders (a) its own hole cards when known, or (b) any seat's cards when
// the server has revealed them via SHOWDOWN-equivalent data. This client's
// wire protocol is the REST state endpoint (HARNESS-CONTRACT.md), whose
// hole-card-privacy mechanism is exactly `players[].hole_cards`: it is
// non-null only for the requesting viewer's own seat, or for every seat's
// once the state has genuinely reached showdown. We never derive
// visibility any other way (e.g. never infer "reveal" from local UI
// state) — we render exactly what the server chose to send back.
export function Seat({ player, isMe, isButton, isActing, showdownEntry }: SeatProps) {
  const revealed = player.hole_cards ?? showdownEntry?.hole_cards ?? null;

  return (
    <div
      className={`seat ${isActing ? "seat--acting" : ""} ${isMe ? "seat--me" : ""}`}
      data-testid={`seat-${player.seat}`}
      data-seat={player.seat}
      data-status={player.status}
      data-stack={player.stack}
      data-current-bet={player.current_bet}
      data-total-committed={player.total_committed}
    >
      <div className="seat__header">
        <span className="seat__label">Seat {player.seat}</span>
        {isButton && <span className="seat__button-badge" title="Dealer button">D</span>}
        {isMe && <span className="seat__me-badge">You</span>}
        {isActing && <span className="seat__acting-badge">Acting</span>}
      </div>
      <div className="seat__stats">
        <span>Stack: {player.stack}</span>
        <span>Bet: {player.current_bet}</span>
        <span>Committed: {player.total_committed}</span>
        <span className={`seat__status seat__status--${player.status}`}>{player.status}</span>
      </div>
      <div className="seat__hole-cards">
        <HoleCard seat={player.seat} index={0} card={revealed ? revealed[0] : null} />
        <HoleCard seat={player.seat} index={1} card={revealed ? revealed[1] : null} />
      </div>
      {showdownEntry && <div className="seat__hand-category">{showdownEntry.hand_category}</div>}
    </div>
  );
}
