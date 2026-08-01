# P1 — local MoE model (Qwen3-Coder-30B-A3B-Instruct-4bit), 2026-07-31

**Verdict: FAIL, and worse than the 14B despite scoring more facts correct.**
Run after the 14B failed P1, to test whether the larger MoE model changes the
picture or whether on-device coding simply is not ready for this benchmark.

## Headline

The model **never produced a usable document at any temperature.** It
degenerates into a repetition loop and burns the entire token budget on it.

| Run | max_tokens | completion_tokens | duplicate lines | coherent prefix |
|---|---|---|---|---|
| temp 0.0 (greedy) | 12288 | 12288 (ceiling) | **86%** | 185 / 1393 lines (13%) |
| temp 0.3 | 20000 | 20000 (ceiling) | **94%** | 107 / 2009 lines (5%) |

In the greedy run one line — "`- **Pot Distribution**: Pot is distributed to
players who contributed to that pot`" — repeats **602 times**, and the header
"### Pot Allocation Algorithm" repeats **317 times** in the temp-0.3 run. Both
answers end mid-sentence at the token ceiling.

**Raising temperature made it worse, not better.** The initial hypothesis was
that this was a greedy-decoding pathology (a well-known cause of repetition
loops) rather than a capability result — that would have made scoring it
unfair, the same way a formatting slip is not a capability failure. Testing it
refuted the hypothesis: at temp 0.3 the duplicate ratio rose from 86% to 94%
and the collapse began *earlier* (line 107 vs 185). This is a genuine model
failure mode on long-form generation, not a decoding artifact.

## Judged result (generous best case)

Because the raw output is unusable, the judge was given only the model's
**coherent prefix** — everything before the first line to repeat three times,
185 lines / 7.5 KB from the greedy run. This is deliberately generous: it
grades the model's best 13% and discards its own failure.

| Signal | Sonnet | Haiku | 14B | **30B-A3B (prefix)** |
|---|---|---|---|---|
| CORRECT | 14 | 15 | 2 | **5** |
| INCORRECT | 0 | 0 | 0 | **4** |
| OMITTED | 1 | 0 | 13 | **6** |
| Usable full document | yes | yes | yes (thin) | **no** |

## Why "more facts correct" does not mean better

The MoE engages with behaviour far more than the 14B did — it commits to real
claims instead of listing field names, which is why it reaches 5 CORRECT
against the 14B's 2, and it covers the wheel straight and the short-all-in
rule that the 14B omitted entirely.

But it **confabulates**. Four claims contradict the implementation:

- **F14** — "Receives player actions over WebSocket". The source carries an
  explicit comment to the contrary: *"This socket is push-only from the
  server's side; the client never sends game commands over it (those go
  through REST)."* Verified against `main.py:126-148`.
- **F9** — "Pot is distributed to winners in order of seat number" (stated
  twice). The code sorts winners by distance clockwise from the button
  (`(seats.index(s) - seats.index(table.button_seat)) % len(seats)`), not by
  seat number. Verified against `game_engine.py:348-370`. **The 14B got this
  fact right.**
- **F2** — "Players can only act when active or all-in"; an all-in seat is not
  ACTIVE and cannot act.
- **F13** — "Preflop: Players act in turn starting from the button"; 3+ handed
  first-to-act is after the big blind.

The benchmark's own judge prompt states the value ordering explicitly: *"an
INCORRECT verdict is the most important signal this exercise produces (a model
confidently documenting something wrong is worse than a model saying nothing
about it)"*. By that standard the MoE is the **worse** of the two local
models — it trades the 14B's honest shallowness for confident wrongness, and
it does so while also failing to produce a usable document.

Both judge INCORRECT calls quoted above were independently re-verified against
the exemplar source before being accepted, per this project's standing rule
that a judge verdict is not trusted at face value. Both were confirmed.

## Conclusion on the local-model seat

Two 4-bit local models, both auditioned as the strongest available candidates,
both fail P1 decisively — the ladder's **easiest** phase, comprehension of
existing code rather than generation:

- **Qwen2.5-Coder-14B** — coherent but shallow. An API/attribute inventory;
  2/15 facts; zero confabulation.
- **Qwen3-Coder-30B-A3B** — deeper engagement, 5/15 facts, but 4 confabulations
  and a repetition collapse that makes the raw output unusable at any
  temperature.

Neither is close to Sonnet (14/15) or Haiku (15/15). For this benchmark, on
this hardware, at 4-bit quantisation, on-device coding is not ready.

**Scope of that claim, stated deliberately:** this is two models, both 4-bit
quantised, on a 32 GB Mac, on one phase of one benchmark. It is real evidence
for the local-seat decision in this project and should not be read as a
general claim about local models, larger quantisations, or other hardware.

The agentic wrapper built earlier the same day remains **unused and not the
constraint** — neither model reaches the build phases it unlocks. It stays
ready for a stronger local model.

## Files

- `run_p1.py` (in `../local14b-p1-2026-07-31/`) — shared runner, now takes
  `--model`, `--out-dir`, `--max-tokens`, `--temperature`
- `exemplar-documentation.md` — raw greedy answer (86% duplicate)
- `coherent-prefix.md` — the 185-line prefix actually judged
- `judge_prompt.txt`, `judge_verdict.json` — blind judge input and verdict
- `../local30ba3b-p1-2026-07-31-temp03/` — the temp-0.3 refutation run
