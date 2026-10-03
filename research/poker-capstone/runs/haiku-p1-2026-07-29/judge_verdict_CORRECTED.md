# P1 judge verdict — corrected (Haiku, P11 cross-model run)

The raw judge output (`judge_verdict.json`) scored F15 as **INCORRECT**:
Haiku's documentation claimed *every* seated player's hole cards are
revealed at showdown ("All players' hole cards are revealed to all
viewers"), while the ground-truth fact F15 said only *non-folded* seats'
cards become visible.

Verification against the actual source
(`exemplar/server/app/models.py` `Table.to_dict()`, line 170:
`reveal_hole_cards=(s == viewer_seat or showdown)`) found **the
ground-truth fact was wrong, not the candidate**: that line has no
folded-status check at all, and folding (`game_engine.py`
`submit_action`) never clears a player's `hole_cards` — only the next
hand's `reset_for_new_hand` does. So every seated player's cards really
are revealed at showdown in the `players[]` field, exactly as Haiku
described. The "non-folded only" behavior Fact F15 was pointing at
actually belongs to a different field, `last_showdown`, which genuinely
is built only from `non_folded_seats()`.

`docs/P1-GROUND-TRUTH-FACTS.md` F15 corrected in place, dated and
cross-referenced back here. This also required a retroactive correction
to Sonnet's own P1 record — see
`runs/sonnet-p1-2026-07-29/judge_verdict_SECOND_CORRECTION.md` — since
Sonnet's original documentation made the same (also wrong) "non-folded
only" claim and was originally marked correct only because it matched
the flawed fact.

## Corrected tally

**15 CORRECT, 0 INCORRECT, 0 OMITTED** (of 15 facts) — F15 reclassified
CORRECT, everything else unchanged from the raw verdict. A clean sweep:
Haiku's documentation is fully accurate against the (now-corrected)
ground truth, and in this one instance was more accurate about the
system's real behavior than Sonnet's own P1 documentation was.

## Why this matters for the P11 mechanism

This is the second real error found in `P1-GROUND-TRUTH-FACTS.md` (the
first was F1, found grading Sonnet). Both times a model's documentation
disagreed with an established fact and turned out to be right. This is
a direct, useful side-effect of running the same fixed grading apparatus
against a second, independently-produced model's output: it's a second
independent check on whether the grading apparatus itself is correct,
not just a second data point on the model. Worth keeping in mind for
every future P11 model run — a disagreement with a "ground truth" fact
is exactly as likely to be the fact's bug as the model's.
