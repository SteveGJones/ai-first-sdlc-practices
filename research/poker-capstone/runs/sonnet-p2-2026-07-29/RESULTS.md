# P2 results — Sonnet, QA the exemplar (blind mode)

**Task**: given only the exemplar's three game-logic source files (no
existing tests, no docs, never told a bug exists anywhere), write a
thorough pytest suite. Graded by running the resulting suite —
unmodified — against two codebases via `harness/qa_fidelity.py`: the
real exemplar (expect all pass) and `broken-variants/wrong-pot-split`
(expect at least one failure, on payout logic specifically).

## Result: PASS, and precisely targeted

- **72 tests** written, all passing against the real exemplar
  (`all_pass_on_exemplar: True`) — independently re-verified via
  `harness/qa_fidelity.evaluate()`, not just Sonnet's own self-report.
- **3 tests fail against the broken variant** (`catches_planted_bug:
  True`), and — importantly — all three are exactly the payout-focused
  tests: `test_three_way_all_in_with_side_pots_pays_correct_winners`,
  `test_split_pot_with_odd_chip_goes_to_first_winner_clockwise_from_button`,
  `test_deeper_stack_reclaims_uncontested_side_pot_layer`. This isn't
  one lucky assertion — three independently-constructed payout scenarios
  all correctly caught the min()-instead-of-max() bug.
- Coverage went well beyond hand evaluation and turn enforcement (the
  "easy" surface): multi-way side pots with three distinct stack depths,
  chip-conservation invariant, odd-chip tie-break, fold-out full-pot
  award, and a direct unit test of the internal `_side_pots` layering
  function.
- **Process discipline observed, not just output quality**: Sonnet
  caught and fixed two bugs in its *own* first draft (a mislabeled
  assertion, two deck-exhaustion crashes) by actually running the suite
  against the real source rather than trusting hand-worked arithmetic —
  the same "run it, don't just trust it" pattern this entire project
  keeps rediscovering, this time demonstrated unprompted by the model
  under test itself.

## Bonus finding — a real, previously-unknown latent issue

Sonnet's suite includes a "pinning" test flagging that
`Table.non_folded_seats()` (in `models.py`) returns everyone whose
status `!= FOLDED`, which includes `SITTING_OUT` — a player who busted
in an earlier hand and is just watching. Traced and confirmed: this
feeds `_maybe_end_hand_early`'s remaining-player count
(`game_engine.py`), so at a 3+-seat table where one seat is
`SITTING_OUT`, a 2-player pot where one side folds would NOT correctly
trigger early-hand-end detection (the sitting-out ghost inflates the
"still contesting" count from 1 to 2). Not the planted bug, not chased
down or fixed in this session (scope discipline) — recorded as a
genuine follow-up in the retrospective's action items.

## Grading mechanism verification

Same discipline as everything else this session: the `qa_fidelity`
harness itself had a real bug (an unanchored all-optional regex that
always matched an empty string at position 0, so `_parse_summary` never
found the actual "N passed" numbers) — found by its own sanity-check
test suite against a synthetic scripted-hand test, fixed, re-verified,
*before* being trusted on Sonnet's real output.
