import type { TableView } from "../state/tableView";

export function Showdown({ view }: { view: TableView }) {
  if (!view.showdown) return null;
  const { pots } = view.showdown;

  return (
    <div className="showdown">
      <h3>Showdown</h3>
      <ul className="pot-breakdown">
        {pots.map((pot, i) => {
          const label = i === 0 ? "Main pot" : "Side pot";
          const winnerLabels = pot.winners
            .map((w) => {
              const seat = view.seats.find((s) => s.seatNo === w.seat);
              const name = seat?.displayName ?? `Seat ${w.seat}`;
              return `${name} (${w.amount}) — ${w.handDescription}`;
            })
            .join(pot.winners.length > 1 ? " / split " : "");
          return (
            <li key={i}>
              {label}: {pot.amount} → {pot.winners.length > 1 ? "split " : ""}
              {winnerLabels}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
