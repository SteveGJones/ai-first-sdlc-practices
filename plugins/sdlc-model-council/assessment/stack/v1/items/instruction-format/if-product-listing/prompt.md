# Instruction following: structured product extraction

Read the product listing text below and extract it into a single JSON object
with exactly these fields:

- `sku` (string) — the product's SKU code.
- `price_usd` (number) — the price in US dollars, as a plain number (no `$`).
- `in_stock` (boolean) — whether the listing says the item is currently in stock.
- `tags` (array of strings) — the listed tags, at least 2.
- `category` (string) — one of: `electronics`, `apparel`, `home`, `toys`, `books`.

{{INPUT:listing.txt}}

Respond with ONLY a single JSON object matching the requested fields; no prose.
