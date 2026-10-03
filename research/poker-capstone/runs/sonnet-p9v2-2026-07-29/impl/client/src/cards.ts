// docs/CLIENT-TEST-CONTRACT.md fixes the DOM's data-suit values to exactly
// "s|h|d|c", while docs/HARNESS-CONTRACT.md explicitly leaves the server's
// own `suit` string free ("any consistent string values"). This module
// bridges the two: whatever the connected server sends, the data-attribute
// mirror always normalizes to the four canonical single-letter codes the
// test contract requires.
export function normalizeSuit(suit: string): "s" | "h" | "d" | "c" {
  const s = suit.trim().toLowerCase();
  if (s.startsWith("s") || s === "♠" || s === "spade") return "s";
  if (s.startsWith("h") || s === "♥" || s === "heart") return "h";
  if (s.startsWith("d") || s === "♦" || s === "diamond") return "d";
  if (s.startsWith("c") || s === "♣" || s === "club") return "c";
  // Fall back defensively rather than throwing — an unrecognized suit
  // string should never crash the render loop.
  return "s";
}

const RANK_LABELS: Record<number, string> = {
  11: "J",
  12: "Q",
  13: "K",
  14: "A",
};

export function rankLabel(rank: number): string {
  return RANK_LABELS[rank] ?? String(rank);
}

const SUIT_GLYPH: Record<string, string> = {
  s: "♠",
  h: "♥",
  d: "♦",
  c: "♣",
};

export function suitGlyph(suit: "s" | "h" | "d" | "c"): string {
  return SUIT_GLYPH[suit];
}
