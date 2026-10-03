import type { Pot } from "../types";

interface PotsProps {
  pots: Pot[];
}

// docs/CLIENT-TEST-CONTRACT.md "Pots": at least pot-0 once a hand has
// posted blinds; additional indices for side pots in the REST array order.
export function Pots({ pots }: PotsProps) {
  return (
    <div className="pots">
      {pots.map((pot, i) => (
        <div key={i} className="pot" data-testid={`pot-${i}`} data-amount={pot.amount}>
          {i === 0 ? "Main pot" : `Side pot ${i}`}: {pot.amount}
          {pot.eligible_seats.length > 0 && (
            <span className="pot__eligible">
              {" "}
              (seats: {pot.eligible_seats.join(", ")})
            </span>
          )}
        </div>
      ))}
    </div>
  );
}
