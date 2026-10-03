import type { Card } from "../types";
import { normalizeSuit, rankLabel, suitGlyph } from "../cards";

interface HoleCardProps {
  seat: number;
  index: 0 | 1;
  card: Card | null; // null => not visible to this viewer (or seat empty of a dealt card)
}

// docs/CLIENT-TEST-CONTRACT.md "Hole cards": two elements per seat, always
// present as elements — visibility is a data attribute (data-hidden), not
// element presence. rank/suit attributes are omitted when hidden.
export function HoleCard({ seat, index, card }: HoleCardProps) {
  const hidden = card === null;
  const suit = card ? normalizeSuit(card.suit) : undefined;

  return (
    <div
      className={`hole-card ${hidden ? "hole-card--back" : "hole-card--face"}`}
      data-testid={`seat-${seat}-hole-card-${index}`}
      data-hidden={hidden ? "true" : "false"}
      data-rank={hidden ? undefined : card!.rank}
      data-suit={hidden ? undefined : suit}
    >
      {hidden ? (
        <span aria-hidden="true">🂠</span>
      ) : (
        <span>
          {rankLabel(card!.rank)}
          {suitGlyph(suit!)}
        </span>
      )}
    </div>
  );
}
