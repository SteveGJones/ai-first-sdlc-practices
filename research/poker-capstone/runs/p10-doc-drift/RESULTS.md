# P10 — post-hoc documentation drift check (Sonnet, 2026-07-29)

## Mechanism

A realistic "keep docs in sync after a code change" task: given (a) the
existing documentation row it wrote no faithfully-derived content for
(P1's own exemplar documentation, `runs/sonnet-p1-2026-07-29/exemplar-documentation.md`,
`POST /tables/{table_id}/players` row) and (b) a genuine unified diff
changing `buy_in<=0` validation to a `buy_in < 20 * big_blind` minimum
(`CHANGE.diff`), the model was asked to produce an updated version of
just that documentation row — nothing else, no exemplar re-read, no
broader context, to isolate whether it correctly reasons from a diff to
a doc update rather than re-deriving everything from scratch.

Note: `CHANGE.diff` is a synthetic diff for this test only — **not**
applied to the real `exemplar/server/app/main.py`, to avoid disturbing
every other phase that depends on the exemplar's actual current
behavior (`buy_in<=0` remains the exemplar's real validation rule).

## Model's output

```
| `POST /tables/{table_id}/players` | `{name: str, buy_in: int}` | `{seat: int}` | 404 if table missing, 400 if `buy_in` is less than 20x the table's big blind, 409 if a hand is currently in progress. Seat number is the smallest non-negative integer not already occupied. |
```

## Grading (deterministic checklist)

| Check | Result |
|---|---|
| Removes the now-stale `buy_in<=0` claim | ✅ removed |
| States the new rule (buy_in must be ≥ 20× big blind) | ✅ present, correctly phrased |
| Does not invent a wrong threshold or unrelated behavior not in the diff | ✅ clean |
| Retains still-correct, untouched details (404/409 conditions, seat-assignment rule) | ✅ retained verbatim |
| Output format matches the requested single-row markdown table | ✅ |

**Verdict: PASS, 5/5.** Sonnet correctly identified which single claim in
the existing documentation the diff invalidated, replaced only that
claim, left everything else in the row untouched, and did not hallucinate
detail beyond what the diff showed.
