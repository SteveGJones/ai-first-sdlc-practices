import type { TableView } from "../state/tableView";
import { PlayingCard } from "./Card";

export function Board({ view }: { view: TableView }) {
  return (
    <div className="board">
      <div className="board-cards">
        {view.board.map((c, i) => (
          <PlayingCard key={i} card={c} />
        ))}
        {Array.from({ length: 5 - view.board.length }).map((_, i) => (
          <div key={`empty-${i}`} className="card card-empty" />
        ))}
      </div>
      <div className="pot-total">Pot: {view.potTotal}</div>
      {view.street && <div className="street-label">{view.street}</div>}
    </div>
  );
}
