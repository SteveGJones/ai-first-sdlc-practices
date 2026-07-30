# P6 results — Haiku (2026-07-29): spec-fidelity client build

Built solely from `exemplar/docs/design-client.md` + `HARNESS-CONTRACT.md`
+ `CLIENT-TEST-CONTRACT.md` (blind to the exemplar's actual code). The
build agent's own compliance self-review explicitly checked off "Hole
Cards (12 total: 2 per seat, `data-testid="seat-{n}-hole-card-{0|1}"`)"
as present and correct. Independently re-verified by pairing with the
exemplar's known-good server and running `harness.client_verify`
(Playwright), per this project's standing rule to never trust a build
agent's self-report — including a self-review that explicitly claims a
specific contract requirement is satisfied.

## Result: FAIL

`python -m harness.client_verify` fails immediately: `seat-0-hole-card-0
element not found`.

## Root cause, confirmed by inspecting the live DOM and the source

The static `index.html` **does** contain correctly-placed
`data-testid="seat-{n}-hole-card-{0|1}"` elements for all 6 seats — the
markup itself is right. `app.js` has two separate blocks that both touch
the same `.hole-cards` container on every render:

1. **First block** (correct): queries for the existing
   `[data-testid="seat-N-hole-card-I"]` elements and sets `data-hidden`/
   `data-rank`/`data-suit` on them — exactly per the contract.
2. **Second block**, a few lines later, titled "Render hole cards
   visually": does `cardsContainer.innerHTML = ''` on the *same*
   `.hole-cards` container, then rebuilds it from scratch with plain
   `<div class="card">Q♣</div>`-style elements that carry **no**
   `data-testid`, `data-hidden`, `data-rank`, or `data-suit` attributes
   at all — only human-readable text.

The second block runs after the first on every single render, wiping out
the correctly-built contract elements from block 1 and replacing them
with non-compliant plain divs. Confirmed directly: the live rendered DOM
for seat 0 after a real hand-start showed
`<div class="hole-cards"><div class="card">Q♣</div><div class="card">J♦</div></div>`
— visually correct, contractually absent. This is why the build agent's
own self-review reported the requirement as satisfied — it checked the
source for the *existence* of the correct code (block 1, which is real
and correct) without noticing block 2 immediately undoes it every time
it runs.

## Reading for the capability ladder

A different failure mode than P5's (which was a genuine game-logic
defect in the all-in/turn-advancement path) — this is a self-inflicted
regression: two competing implementations of the same feature, written
close together, where the second silently destroys the first's correct
work. Notably, every *other* contract element (table mirror, per-seat
mirror, community cards, pots, action controls) worked correctly on
first inspection — this defect is narrowly scoped to hole cards
specifically, exactly where two code paths happened to collide.
