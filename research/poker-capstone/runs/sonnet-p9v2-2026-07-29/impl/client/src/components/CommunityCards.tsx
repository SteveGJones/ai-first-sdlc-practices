import type { Card } from "../types";
import { normalizeSuit, rankLabel, suitGlyph } from "../cards";

interface CommunityCardsProps {
  cards: Card[];
}

// docs/CLIENT-TEST-CONTRACT.md "Community cards": one element per dealt
// card, index 0..4 in deal order — element only exists once dealt, so we
// simply render exactly `cards.length` elements, no placeholders.
export function CommunityCards({ cards }: CommunityCardsProps) {
  return (
    <div className="community-cards">
      {cards.map((card, i) => {
        const suit = normalizeSuit(card.suit);
        return (
          <div
            key={i}
            className="community-card"
            data-testid={`community-card-${i}`}
            data-rank={card.rank}
            data-suit={suit}
          >
            {rankLabel(card.rank)}
            {suitGlyph(suit)}
          </div>
        );
      })}
    </div>
  );
}
