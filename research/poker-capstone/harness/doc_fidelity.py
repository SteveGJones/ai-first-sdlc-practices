"""P1 scoring: documentation-of-the-exemplar (comprehension, not
generation). Two independent signals, same split as checklist.py vs. a
judge for stages 1-2:

1. `score_checklist` — cheap, deterministic topic-coverage check (did it
   address this concept at all), same style as `checklist.py`.
2. `build_judge_prompt` — assembles a prompt for a judge subagent to
   verify FACTUAL ACCURACY against `docs/P1-GROUND-TRUTH-FACTS.md`,
   which the model under test never sees. The judge call itself is an
   `Agent` dispatch made by the orchestrating session (there is no
   headless way to invoke a judge from inside this package — same
   reasoning as why P3/P4 need no new *infrastructure*, just a prompt).
"""

from __future__ import annotations

from .checklist import ChecklistResult, score_checklist

DOC_CHECKLIST: list[tuple[str, list[str]]] = [
    ("turn_enforcement_described", [r"turn", r"current[_ ]?actor"]),
    (
        "betting_round_closure_described",
        [r"round\s+(is|ends|complete)", r"acted_this_round", r"has_acted"],
    ),
    ("short_all_in_raise_rule_described", [r"short[- ]?all[- ]?in", r"reopen"]),
    ("side_pot_algorithm_described", [r"side[- ]?pot", r"layer"]),
    ("hand_evaluation_described", [r"hand\s+(rank|evaluat)", r"best[\s\S]{0,20}5"]),
    ("wheel_straight_mentioned", [r"wheel", r"A-2-3-4-5", r"ace[\s\S]{0,20}low"]),
    ("blinds_button_described", [r"\bblind", r"\bbutton\b"]),
    (
        "heads_up_special_case_mentioned",
        [r"heads[- ]?up", r"2[- ]?handed", r"two[- ]?handed"],
    ),
    ("api_contract_described", [r"\bAPI\b", r"REST", r"endpoint", r"POST /"]),
    ("hole_card_privacy_described", [r"hole card", r"privacy", r"redact"]),
]


def score_doc_checklist(text: str) -> ChecklistResult:
    return score_checklist(text, DOC_CHECKLIST)


JUDGE_PROMPT_TEMPLATE = """\
You are grading documentation for factual accuracy against a fixed set of
ground-truth facts about a codebase. You are NOT grading writing quality,
completeness of coverage, or style — only whether specific factual claims
the documentation makes (or should make, per the fact list) are correct.

## Ground-truth facts (the authoritative source — trust these over the
candidate documentation if they ever conflict)

{facts}

## The candidate documentation under review

{candidate_doc}

## Your task

For EACH numbered fact (F1, F2, ...) above, classify the candidate
documentation's treatment of it as exactly one of:
- CORRECT — the documentation states this fact accurately (need not use
  the same wording, just be factually consistent with it)
- INCORRECT — the documentation makes a claim that contradicts this fact
  (quote the specific contradicting sentence)
- OMITTED — the documentation does not address this topic at all

Report your verdict as a JSON object:
{{
  "per_fact": {{
    "F1": {{"verdict": "CORRECT"|"INCORRECT"|"OMITTED", "detail": "..."}},
    ...
  }},
  "summary": {{"correct": N, "incorrect": N, "omitted": N}}
}}

Be strict: a vague or hedged statement that could be read either way for
a fact should be marked OMITTED, not CORRECT — only mark CORRECT if the
documentation actually commits to the accurate claim. An INCORRECT
verdict is the most important signal this exercise produces (a model
confidently documenting something wrong is worse than a model saying
nothing about it), so scrutinize claims that touch each fact's topic
carefully before marking CORRECT.
"""


def build_judge_prompt(facts_md: str, candidate_doc: str) -> str:
    return JUDGE_PROMPT_TEMPLATE.format(facts=facts_md, candidate_doc=candidate_doc)
