# P5 results — Haiku (2026-07-29): spec-fidelity server build

Built solely from `exemplar/docs/design-server.md` + `HARNESS-CONTRACT.md`
(blind to the exemplar's actual code), self-verified by the build agent
via curl scripts and reported working — including CORS, all required
response fields, and (per the agent's own summary) "perfect chip
conservation." Independently re-verified via `python -m harness`, per
this project's standing rule to never trust a build agent's self-report.

## Result: FAIL

`python -m harness --impl-dir runs/haiku-p5-2026-07-29/impl` fails during
`short_all_in_side_pot`:

```
POST /tables/d45be5b4/actions unexpectedly failed (400):
{'detail': "Cannot bet when there's already a bet this round"}
```

## Root cause, confirmed by manually stepping through the REST calls

Set up a 3-handed hand (short stack all-in preflop, exactly the
`short_all_in_side_pot` scenario) and drove it action-by-action to find
where a legitimate action gets rejected:

1. Seat 0 (short stack) raises all-in for 5. **Bug found immediately**:
   the response shows seat 0's `stack: 0` but `status: "active"`, not
   `"all_in"` — the server never transitions a player's status when
   their stack hits zero.
2. Preflop closes normally (p1, p2 call). Flop deals.
3. p1 bets 10, p2 calls 10. `current_actor` then becomes **seat 0 — the
   all-in player** — a second, related bug: an ALL_IN seat should never
   be selected as the next actor at all (the exemplar design and the
   real reference implementation both skip ALL_IN/FOLDED seats when
   advancing turn; `current_actor` should have gone straight to the next
   round instead of "back" to seat 0).
4. Seat 0 is made to submit a no-op "call 0" (they have no chips to
   call with). The server accepts this as if it were a real action
   requiring another lap of betting, rather than recognizing the flop
   round was already complete (both non-all-in players had matched at
   10) — so it does **not** reset `current_bet` or advance to the turn.
5. Play returns to seat 1 with `current_bet` still 10 (stale, from the
   round that should have already closed). Seat 1's own state correctly
   shows `current_bet: 10` too, so a normal player computing `to_call =
   current_bet - my_current_bet = 10 - 10 = 0` reasonably opens a fresh
   "bet" — which the server rejects, because *its own* internal
   understanding of the round never actually closed.

Two distinct, real defects, both in the exact area design already
flagged as risky (all-in / turn-skipping handling): (a) player status
never transitions to `all_in` when a stack reaches zero, and (b)
turn-advancement / round-completion logic doesn't correctly exempt
all-in players, corrupting subsequent round transitions once an all-in
player is present at the table.

## Reading for the capability ladder

Consistent with the pattern across Haiku's P2 (payout-correctness blind
spot) and P4 (arithmetic error, leftover draft comment in exactly the
all-in/betting-completion logic) results: Haiku's designs and
implementations are broadly complete and well-organized, but the
specific mechanics of all-in / side-pot / round-completion handling — the
single hardest, most failure-prone area of this whole system — are where
real defects keep surfacing. This is the first genuinely FAIL result in
Haiku's ladder run (matching the operator's own read that Haiku was
"getting closer to failure" after P4).
