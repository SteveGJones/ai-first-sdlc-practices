# P2 results — Haiku (2026-07-29)

Same mechanism as Sonnet's P2: blind test-authoring against the
exemplar's three game-logic source files, no bug ever mentioned,
independently re-verified via `harness/qa_fidelity.evaluate()` against
both the real exemplar and `broken-variants/wrong-pot-split` (the
`min()`-instead-of-`max()` pot-split bug).

## Result

- **42 tests written**, all pass against the real exemplar
  (`all_pass_on_exemplar: True`).
- **0 of 42 fail against the broken variant** (`catches_planted_bug:
  False`) — the suite does not catch the planted bug at all. Contrast
  with Sonnet's P2: 72 tests, 3 independently-constructed payout tests
  all correctly failed on the same broken variant.

## Why, specifically

Every one of Haiku's side-pot/all-in/payout-adjacent tests
(`test_single_pot_heads_up`, `test_multiple_all_ins_create_side_pots`,
`test_odd_chip_distribution`, the `TestChipConservation` class) asserts
only **total chip conservation** — `sum(stacks before) ==
sum(stacks after)` — never which specific seat wins or how much a
specific seat's stack should increase by. The planted bug (`_finish_hand`
using `min()` instead of `max()` when picking a pot's winning hand) picks
the *worst* hand instead of the best one — chips still go to *someone*
seated at the table, so total conservation holds exactly the same whether
the winner-selection logic is right or backwards. A test suite built
entirely on chip-conservation invariants is structurally blind to this
entire class of bug, no matter how many of them you write.

Sonnet's suite caught it because three of its tests specifically asserted
*which seat* wins and *the exact amount* it should receive, derived by
hand-working the expected side-pot layering — payout-correctness
assertions, not just conservation ones.

## Reading for the capability ladder

Not a "worse pass rate" result in the way P1 or a REST harness scenario
count would be — Haiku's suite is well-organized, covers all 9 hand
categories plus the wheel case, exercises turn enforcement and betting
validation solidly, and every test genuinely passes against real code
(no fabricated or trivially-true assertions). The gap is narrower and
more specific: **the suite verifies structure and conservation, but never
verifies correctness of the one part of the system a payout bug would
actually corrupt** — a real, specific difference in test-design instinct
between the two models on this task, not a general quality gap.
