"""P3/P4 scoring: judged design quality, comparing a candidate's own
architecture/detailed-design doc against the exemplar's reference for
the same task. Unlike P1's fact-checker (a fixed list of checkable
claims about code that already exists), this is a genuine comparative
quality judgment over two independently-produced answers to the same
open-ended brief — there is no single ground truth, only "is this a
sound, complete design," so the judge is asked to reason about
completeness and soundness rather than verify discrete facts.

No new infrastructure beyond a prompt template: the judge call itself is
an `Agent` dispatch made by the orchestrating session, same as P1/P2's
judge steps.
"""

from __future__ import annotations

JUDGE_PROMPT_TEMPLATE = """\
You are a strict design-quality judge. You will compare a CANDIDATE design
document against a REFERENCE design document — both are independent
answers to the same design brief for a Texas Hold'em poker {dimension}.
The reference is not necessarily the only correct answer (the candidate is
free to make different, equally valid technical choices, e.g. a different
tech stack or protocol) — you are judging whether the candidate's design
is SOUND and COMPLETE, not whether it matches the reference's specific
choices.

## Reference design ({dimension})

{reference_doc}

## Candidate design under review

{candidate_doc}

## Your task

Score the candidate on each of these axes, 0-2 (0 = not addressed / wrong,
1 = partially addressed / present but thin, 2 = fully and soundly
addressed):

- **completeness**: does it address every major concern the reference
  does (even if via a different approach)?
- **turn_enforcement_soundness** (or, for a client doc, **state_sync_soundness**):
  is the core hard mechanism specified precisely enough that two
  different engineers implementing it independently would produce
  compatible, correct behavior?
- **edge_case_awareness**: does it identify and resolve the same
  non-obvious edge cases the reference does (e.g. short all-in raises,
  hole-card privacy, heads-up vs. multi-way differences) — or does it
  gloss over them?
- **internal_consistency**: does the document contradict itself anywhere,
  or leave any decision ambiguous that a later stage would need to
  resolve unilaterally?

Also explicitly note, separately from the score:
- **gaps**: anything the reference addresses that the candidate misses
  entirely or gets wrong.
- **superior_choices**: anything the candidate does BETTER than the
  reference, or a design choice that's different but equally or more
  sound — do not penalize a candidate merely for choosing differently
  than the reference.

Report your verdict as a JSON object:
{{
  "scores": {{"completeness": 0-2, "turn_enforcement_soundness": 0-2,
              "edge_case_awareness": 0-2, "internal_consistency": 0-2}},
  "gaps": ["..."],
  "superior_choices": ["..."],
  "summary": "one paragraph"
}}
"""


def build_judge_prompt(dimension: str, reference_doc: str, candidate_doc: str) -> str:
    return JUDGE_PROMPT_TEMPLATE.format(
        dimension=dimension, reference_doc=reference_doc, candidate_doc=candidate_doc
    )
