# P7/P8 — cross-pairing Sonnet's P9 artifacts with the exemplar

P7 = P9's full-autonomy **server** + the exemplar's known-good **client**
(`client_verify`).
P8 = the exemplar's known-good **server** + P9's full-autonomy **client**
(`client_verify`).

## Result

Both fail, but **not informatively about P9's design/implementation
quality** — both failures are timeline artifacts, not fresh defects:

- **P7 fails**: `seat-0-hole-card-0 element not found`. P9's server
  response omits `hole_cards`, `table_id`, `small_blind`, `big_blind`,
  `betting_round`, `min_raise`, and `last_action_log` — all fields added
  to `HARNESS-CONTRACT.md`'s "Response shape" *after* P9 was built (see
  that doc's "Rollout note"). The exemplar client now depends on
  `hole_cards`. P9's server was contract-compliant *as of the version it
  was built against*.
- **P8 fails**: the Playwright driver times out waiting for
  `[data-testid="table"]` — P9's client predates `CLIENT-TEST-CONTRACT.md`
  entirely (authored later in this same session) and carries no
  `data-testid`/`data-*` attributes at all.

## What this is actually useful for

Not a P9 capability score (P7/P8 are excluded from the Sonnet baseline
tally for that reason) but a genuine, useful finding about the scoring
process itself: **contract versioning matters for a benchmark meant to be
re-run over time.** An implementation built against an earlier contract
version can fail a later contract's checks for reasons unrelated to its
actual design/engineering quality. Future runs of this ladder should
either pin a contract version per run, or accept that older artifacts
need re-verification only against the contract version they were built
against — not treated as failing the current one.

Separately, independently re-running the plain REST harness
(`python -m harness`) against P9's server standalone (not a cross-pair,
same server the P9 run already had) reproduces the original P9 failure:
a real bug in P9's own hand-completion logic — `last_showdown` gets
populated but `hand_in_progress` never flips to `false` and no payout is
applied. This is unrelated to the contract-versioning issue above and is
a genuine defect in P9's own code, consistent with the original P9 run's
FAIL.
