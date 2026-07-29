# Client test contract (normative, applies to every submitted client)

Same design principle as `HARNESS-CONTRACT.md`, applied to the UI: a fixed,
machine-readable surface a driver can rely on regardless of implementation,
while everything actually interesting about client design — framework,
layout, styling, component structure, visible copy/labels — stays entirely
free. **Playwright never parses rendered text or relies on CSS
selectors.** It reads `data-testid` elements and `data-*` attributes only.
This is the reason the contract can stay fixed forever while every
submission's actual UI looks completely different.

## Why a data-attribute mirror, not rendered-text parsing

Two submissions might render a card as `A♠`, `Ace of Spades`, or an SVG
image with no text at all — all valid, all untestable by string-matching.
Instead, every element the driver reads carries the **same data already in
the REST state JSON** (see `HARNESS-CONTRACT.md` "Response shape") as
`data-*` attributes, in parallel with whatever human-facing rendering the
client chooses. The visible page can look like anything; the attributes
must always agree with the last state the client received.

## URL contract (no lobby-driving needed)

The driver creates tables and seats players via the **existing fixed REST
API** (`HARNESS-CONTRACT.md`) — never through the client's own lobby UI,
which stays entirely free-form. The client's index page must support
direct deep-linking into an already-created table:

```
GET /?table={table_id}&seat={seat}
```

Loading this URL must take the browser straight to that table's view for
that seat (fetching initial state via the REST `GET /state`, then staying
current via whatever the client's own sync mechanism is). A lobby/landing
page may still exist for humans; the driver never uses it.

## Required elements

### Table-level state mirror (one element, always present once loaded)

```html
<div
  data-testid="table"
  data-hand-in-progress="true|false"
  data-current-actor="0|1|2|...|"          <!-- empty string when null -->
  data-current-bet="{int}"
  data-button-seat="{int}"
>
```

### Per-seat state mirror (one per seated player)

```html
<div
  data-testid="seat-{n}"
  data-seat="{n}"
  data-status="active|folded|all_in|sitting_out"
  data-stack="{int}"
  data-current-bet="{int}"
  data-total-committed="{int}"
>
```

### Hole cards (two per seat, always present as elements — visibility is a
data attribute, not element presence, so the driver can assert on
concealment directly rather than inferring it from absence)

```html
<div
  data-testid="seat-{n}-hole-card-{0|1}"
  data-hidden="true|false"
  data-rank="{2-14}"     <!-- omitted or "0" when data-hidden="true" -->
  data-suit="s|h|d|c"    <!-- omitted when data-hidden="true" -->
>
```

`data-hidden` must be `"false"` only for the viewing seat's own cards (or
every seat's, once the hand reaches showdown) — this is the exact
hole-card-privacy invariant `design-client.md` already requires; the
contract just makes it independently checkable.

### Community cards (one per dealt card — element only exists once dealt)

```html
<div data-testid="community-card-{i}" data-rank="{2-14}" data-suit="s|h|d|c">
```

(`i` = 0..4 in deal order: flop is 0-2, turn is 3, river is 4.)

### Pots

```html
<div data-testid="pot-{i}" data-amount="{int}">
```

At least `pot-0` must exist once a hand has posted blinds; additional
indices for side pots, same order the REST `pots` array uses.

### Action controls

```html
<button data-testid="action-fold">
<button data-testid="action-check-call">   <!-- single control; label is free, semantics (check when no bet owed, call when one is) match design-client.md -->
<button data-testid="action-bet-raise">
<input  data-testid="bet-amount-input" type="number">
<button data-testid="start-hand">          <!-- triggers POST /start -->
```

Every action button must carry the real HTML `disabled` attribute
whenever it would be illegal to click right now (not the acting seat, no
hand in progress for `start-hand`, etc.) — the driver checks
`.isDisabled()`, never a CSS class or visual state.

## What the (future) Playwright driver will check

Non-normative here for the same reason `HARNESS-CONTRACT.md`'s equivalent
section is — stated so the contract isn't written in a vacuum. At
minimum: deep-linking a seat shows only that seat's own hole cards
(`data-hidden="false"`) and every other seat's as `data-hidden="true"`;
the action buttons' `disabled` state tracks `data-current-actor` correctly
across all seated browser contexts; a submitted action updates the state
mirror within a bounded time (real-time sync working, not just
initial-load-correct); and the mirror's numbers agree with the REST
state at every point a cross-check is taken.

## Rollout note

This is new as of 2026-07-29, after the wire-API-contract lesson from the
first Sonnet verification. The exemplar's own client does not yet
implement this contract — it needs the same retrofit-and-verify treatment
`HARNESS-CONTRACT.md` got, in the same order: fix the exemplar first,
build the fixed Playwright driver against it, prove a deliberately-broken
client fails the right assertions, only then point it at model-submitted
clients.
