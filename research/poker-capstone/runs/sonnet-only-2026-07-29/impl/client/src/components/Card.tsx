import type { Card as CardModel } from "../types/protocol";

const SUIT_SYMBOL: Record<CardModel["suit"], string> = {
  CLUBS: "♣",
  DIAMONDS: "♦",
  HEARTS: "♥",
  SPADES: "♠",
};

const RED_SUITS = new Set(["DIAMONDS", "HEARTS"]);

export function PlayingCard({ card }: { card: CardModel }) {
  const red = RED_SUITS.has(card.suit);
  return (
    <div className={`card ${red ? "card-red" : "card-black"}`}>
      <span>{card.rank}</span>
      <span>{SUIT_SYMBOL[card.suit]}</span>
    </div>
  );
}

export function CardBack() {
  return <div className="card card-back" aria-label="hidden card" />;
}
