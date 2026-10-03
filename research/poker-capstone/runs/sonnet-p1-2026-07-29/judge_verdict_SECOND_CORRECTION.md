# P1 judge verdict — second correction (found via the P11 Haiku run)

`judge_verdict_CORRECTED.md` (above) already corrected F1, landing on
**14 CORRECT, 0 INCORRECT, 1 OMITTED**. A second, independent error has
since been found in `docs/P1-GROUND-TRUTH-FACTS.md` F15 — this time
surfaced by grading a *different* model's documentation (Haiku, as part
of the P11 cross-model roster), not by re-reading Sonnet's own output
again.

## What happened

F15 (as originally written) claimed the showdown hole-card reveal
excludes folded seats. Haiku's P1 documentation stated the broader,
correct claim (every seated player's cards are revealed at showdown,
folded or not) and the judge marked it **INCORRECT** against the flawed
fact. Re-verifying against `models.py` `Table.to_dict()` directly (this
project's standing rule: never trust a judge verdict without checking
the source when a finding looks surprising) confirmed Haiku was right
and the fact was wrong — `reveal_hole_cards=(s == viewer_seat or
showdown)` has no folded-status check at all, and folding never clears
`hole_cards` (only the next hand's `reset_for_new_hand` does). The
"non-folded only" behavior actually belongs to the separate
`last_showdown` field, not the `players[].hole_cards` field F15 was
describing. Full correction recorded in `docs/P1-GROUND-TRUTH-FACTS.md`
F15.

## What this means for Sonnet's own P1 record

Sonnet's original documentation (`exemplar-documentation.md` §7) asserted
the narrower claim: "everyone's (non-folded, since only non-folded
players ... still hold hole_cards) hole cards become visible" — both the
headline claim (non-folded only) and the parenthetical justification
(folded players "no longer hold" `hole_cards`) are incorrect against the
real code. The original judge marked this **CORRECT** only because it
happened to match the also-wrong ground-truth fact.

## Re-corrected tally

**13 CORRECT, 1 INCORRECT (F15), 1 OMITTED (F6)** — of 15 facts.

This revises `judge_verdict_CORRECTED.md`'s "14/0/1" down by one. Not a
retraction of that document's own reasoning (its F1 correction was and
remains right) — a second, independent error found later in the same
fact list, on a fact that document didn't touch.

## Why this is worth recording plainly

This project's ground-truth fact lists have now had **two** real errors
found in them by two different mechanisms: F1 by re-reading source after
a judge flagged Sonnet's own doc as wrong, F15 by re-reading source after
a *different model's* doc disagreed with an established fact. Both times
the model under test was right and the fact list was wrong. A
cross-model roster isn't just useful for comparing models against each
other — running the same fixed grading apparatus against a second,
independently-produced answer is itself a second independent check on
whether that apparatus is actually correct. Worth remembering for P11
generally: expect more of this, and always re-verify against source
before accepting a judge's "incorrect" when a model's claim it disagrees
with looks reasonable on its face.
