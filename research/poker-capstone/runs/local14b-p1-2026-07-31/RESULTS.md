# P1 — local MLX model (Qwen2.5-Coder-14B-Instruct-4bit), 2026-07-31

**Verdict: FAIL.** First phase of the local model's ladder run, and the first
genuine failure. Per the ladder's fail-fast design intent, the run stops here.

## Setup

Same task as the Sonnet and Haiku P1 runs: document the exemplar from its four
server source files only (`exemplar/server/app/{models,hand_eval,game_engine,
main}.py`), with no access to the design docs and no sight of
`docs/P1-GROUND-TRUTH-FACTS.md`.

One deliberate adaptation, recorded for fairness: the baselines were subagents
with file access, told not to look for docs. A text-only local model cannot
read files, so the four sources were inlined into the prompt instead. Same
information, same exclusions. The prompt does **not** enumerate the ten
checklist topics — that would be teaching to the test and would break
comparability, and neither baseline's prompt did either.

Served by `mlx_lm.server` on :8081 with a bounded prompt cache. Single
one-shot call — P1 is a judged-document phase, so the agentic wrapper is not
involved. `max_tokens` was raised to 12288 (Sonnet's P1 answer was ~5.7k
tokens) so that truncation could not be mistaken for incompleteness.

## Result

| Signal | Sonnet | Haiku | **local 14B** |
|---|---|---|---|
| Checklist (topic coverage) | 1.00 (10/10) | 1.00 (10/10) | **0.60 (6/10)** |
| Judge — CORRECT | 14 | 15 | **2** |
| Judge — INCORRECT | 0 | 0 | **0** |
| Judge — OMITTED | 1 | 0 | **13** |
| Answer size | 20 KB | 38 KB | **8.8 KB** |

Missing checklist topics: `turn_enforcement_described`,
`short_all_in_raise_rule_described`, `wheel_straight_mentioned`,
`heads_up_special_case_mentioned`.

Judge marked CORRECT only F9 (odd chip clockwise from button) and F14 (REST
surface + WebSocket). All thirteen other facts OMITTED.

## What actually went wrong

The document is **structurally an API/attribute inventory, not a behavioural
specification**. It faithfully lists classes, fields, methods, parameters and
return types, but almost never states what the code *does* with them. Every
ground-truth fact that requires rule semantics was skipped:

- Turn enforcement (F1, F2): `current_actor` appears exactly once, as a field
  listing — "An integer representing the seat of the current actor". No
  validation ordering, no statement that a non-ACTIVE seat is rejected.
- Side pots (F7, F8): "`_side_pots` — Allocates side pots" plus one hedge,
  "side pots are allocated based on the contributions of players, ensuring
  that players with smaller contributions are not left out". No layering
  algorithm.
- Hand evaluation (F10, F11, F12): the word "straight" never appears anywhere
  in the document. No wheel/low-Ace rule, no category count, no C(7,5)
  enumeration.
- Short all-in raise rule (F6): entirely absent — this is the nuance the
  retrospective singled out Sonnet for catching unprompted.
- Heads-up (F13): zero mentions.

**A genuine positive worth recording: zero INCORRECT.** The model never
confabulated. Where it lacked understanding it stayed silent rather than
inventing behaviour, which is the better failure mode — the judge prompt
itself notes a confidently-wrong claim is worse than an omission. The failure
is one of depth and engagement with behaviour, not of accuracy.

## Instrument bug found by this run (fixed)

Grading a thin document exposed two real false positives in
`harness/doc_fidelity.py`'s `DOC_CHECKLIST`. `score_checklist` is an ANY-match
over the pattern list, so a substring pattern silently satisfies a topic from
unrelated prose:

1. `r"turn"` matched inside **"Returns"** — 21 of 23 hits in this document came
   from "**Returns**:" lines in the API inventory. It also matches the `TURN`
   betting-round enum. So `turn_enforcement_described` was satisfied by a
   document that never describes turn enforcement.
2. `r"layer"` matched inside **"player"** — all 35 occurrences in this document
   were "player"/"Player", none standalone. This satisfied
   `side_pot_algorithm_described` for *any* poker document.

Fixed: the turn patterns are now behavioural (`whose turn`, `turn order`,
`out of turn`, `acting seat`) and `layer` is word-anchored.

**Re-scored all three P1 documents after the fix**: Sonnet 1.00 and Haiku 1.00
are **unchanged** — their coverage was real, so the bug never affected them.
Only the 14B moved, 0.70 → 0.60, correctly reclassifying `turn_enforcement` as
missing. The bug inflated thin documents only, which is why two clean baseline
runs never surfaced it.

This is the fifth time in this project that a grading mechanism turned out to
have a real bug found only by running it against fresh output — the same
pattern noted for the REST harness, the client contract, the doc-fidelity
judge and the ground-truth fact list.

## Why the ladder stops here

P1 is the ladder's easiest phase — comprehension of existing code, not
generation. Both baselines passed it comfortably (Sonnet 14/15, Haiku 15/15,
both 10/10 on coverage). 2/15 is not a marginal result, and the phases above
P1 (P2 blind QA, P3/P4 judged design, P5/P6 spec-fidelity builds) all demand
strictly more of the same behavioural understanding this phase shows to be
absent. Continuing would spend real time to confirm a conclusion P1 already
establishes.

The agentic wrapper built on 2026-07-31 is therefore **not the constraint** —
it was built so build phases would be reachable, and it works, but this model
does not get far enough up the ladder to need it. The wrapper remains ready
for a stronger local model.

## Files

- `run_p1.py` — the runner (reproducible; re-run to regenerate)
- `prompt.txt` — exact prompt sent to the model
- `exemplar-documentation.md` — the model's answer
- `judge_prompt.txt` — prompt given to the blind judge
- `judge_verdict.json` — per-fact verdict
