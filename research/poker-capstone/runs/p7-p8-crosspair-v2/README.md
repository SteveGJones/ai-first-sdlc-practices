# P7-v2/P8-v2 — clean cross-pairing (2026-07-29, redo of P7/P8)

The original P7/P8 (`runs/p7-p8-crosspair/`) came back inconclusive: P9's
server/client predated several `HARNESS-CONTRACT.md` fields and all of
`CLIENT-TEST-CONTRACT.md`, so both cross-pairs failed on contract-version
drift rather than on anything informative about design/implementation
quality.

## What changed for this redo

Rather than re-running the whole ladder (architecture + design were
already independently judged in P3/P4 and didn't need re-scoring), only
**Stage 3 (implementation)** was redone from scratch — a fresh server and
a fresh client, each built by a blind Agent dispatch from Sonnet's
existing `stage1/architecture.md` + `stage2/design-{server,client}.md`,
against the CURRENT, complete `HARNESS-CONTRACT.md` +
`CLIENT-TEST-CONTRACT.md`. Artifacts: `runs/sonnet-p9v2-2026-07-29/`.

`docs/BRIEF-TEMPLATE.md` was also updated to point future full-autonomy
briefs at `CLIENT-TEST-CONTRACT.md`, not just `HARNESS-CONTRACT.md`, so
this gap doesn't recur for the next model run.

## A third real contract gap found (and fixed) along the way

Independently verifying P9-v2's own server+client paired together (before
even getting to the cross-pairs) failed immediately: the browser blocked
every fetch with a CORS error. `HARNESS-CONTRACT.md` never documented
that the server must send CORS headers — the exemplar has always quietly
depended on `CORSMiddleware(allow_origins=["*"])` without it ever being
written down as a requirement. Fixed by adding a "Cross-origin access
(CORS)" section to the contract, then asking the same server-build agent
to add the now-documented requirement — the same precedent as the
original P9 run's `current_bet` field: a contract-clarity fix the model
completes once told, not a backfill of its own logic. Re-verified clean
afterward.

## Results — all three passes clean

| Pairing | Result |
|---|---|
| P9-v2 self-paired (own server + own client) | REST: 3/3 scenarios pass. Browser: 3/3 scenarios pass. |
| **P7-v2**: P9-v2 server + exemplar client | 3/3 browser scenarios pass |
| **P8-v2**: exemplar server + P9-v2 client | 3/3 browser scenarios pass |

Unlike the original P9, P9-v2's server also passes the **REST harness's**
`basic_multihand` scenario (5 full hands, chip-conserving payouts) —
the original P9's real hand-completion bug (showdown evaluated,
`hand_in_progress` never cleared, no payout applied) does not reproduce
in this from-scratch implementation. Not a "fix" of the original bug
(that implementation is untouched, still recorded as FAIL) — a
different, independent implementation of the same design turned out not
to have it.

## What this now says about the ladder, cleanly

P9-v2's server and client both correctly implement the fixed contracts
well enough to interoperate with an independently-built reference
implementation in either direction — the actual signal P7/P8 was
designed to produce. Combined with P3/P4's judged design-quality result,
this closes out a clean Sonnet baseline across the full P1-P10 ladder
with no remaining contract-versioning caveats.
