## Your task — ITER20 policy (Run 2)

Up to 20 generate→run→fix iterations. **The success criterion is
*winning the quality scorecard*, not hitting a coverage number.**
See `quality_scorecard.md`. Coverage is a non-regression floor only.

Run 1 lesson: all three iter20 sessions stopped at iteration 2–3
because they hit coverage parity. In Run 2, the iteration budget is
your tool for *deepening quality* — to be spent until marginal
improvement is genuinely zero.

The hard constraints (no git recovery, no `pip install -e .`, no
private symbols, no substring matches, etc.) apply throughout.

### Steps

1. **Pre-compute the baseline's scorecard** with `grep -c` / `wc -l`
   against `{BASE}/{TESTS_DIR}/`. Save to
   `.rex_metrics/baseline_scorecard.json`. **No reading baseline test
   bodies.** This is your benchmark target.

2. Delete `{TESTS_DIR}/`, commit, save coverage-after-delete to
   `.rex_metrics/iter_0/`.

3. **Iteration 1** — fresh generation following the quality contract.
   Aim to already beat the baseline scorecard on as many axes as
   possible. Save outputs + iter_1 scorecard to `.rex_metrics/iter_1/`.

4. **Iterations 2..20** — each iteration must produce a **real
   scorecard improvement** (definition below). If you cannot identify
   a real improvement to make, you may stop early.

   A real improvement (any **one** of these, without regressing
   anything else, without dropping coverage below the floor):

   a. Move at least one A.* anti-pattern count down (with concrete
      file:line examples in the commit message).
   b. Add fixed-vector tests (B.1) for behaviors currently tested
      only by round-trip.
   c. Cover a source-comparison boundary you haven't yet (B.2),
      where the boundary case is observable to a caller.
   d. Add integration tests via framework real-I/O primitives (B.3)
      to exercise production code paths unit tests can't reach
      cleanly.
   e. Restructure unrolled tests into parametrize/inheritance to
      bring D.1 down and D.2 up — but only if it doesn't lose any
      cases.
   f. Eliminate `unittest.mock` usage (C.1 → 0) by replacing with
      framework primitives or direct construction.

   **Things that do NOT count as a real improvement:**

   - Adding tests that exercise private internals with tautological
     assertions just to flip a coverage branch.
   - Adding tests for `None`-valued mounts, unknown ASGI message
     types, or other defensive-arm exercises that test the guard
     rather than the guarded function (audit caught these as
     coverage-chasing in Run 1).
   - Adding more of the same test you already have (duplicates).
   - Tightening an assertion in a way that pins implementation
     details the contract doesn't promise (e.g., asserting an exact
     byte length when only the contract is "non-empty").

5. **Stopping condition.** Stop early when **all three** are true:

   - Coverage floor F.1 + F.2 is satisfied.
   - You've spent at least **3 consecutive iterations** trying to
     improve scorecard axes and failed (no remaining axis can be
     improved without regressing another). Document those 3 attempts
     even if they don't commit.
   - Your final scorecard tally beats the baseline.

   Otherwise keep iterating up to 20. **Coverage parity is not a
   stopping condition.** "We're at baseline coverage and the
   scorecard ties" means keep going.

6. **Each iteration's commit message** names the move (a)–(f) and
   the axis delta (e.g., `iter5: move (a), A.1 went 12 → 4 by
   replacing 8 substring-match assertions in test_serializer.py`).

7. **Save outputs after every iteration** to `.rex_metrics/iter_<n>/`
   including that iteration's scorecard JSON.

### SUMMARY.md template

```markdown
# Run 2 — {REPO} / iter20

## Per-iteration table

| iter | wall | pass/fail | line% | branch% | combined% | scorecard wins/losses/ties (vs baseline) | move |
|-----:|-----:|----------:|------:|--------:|----------:|------------------------------------------|------|
| 0    | -    | 0/0       |  0.00 |   0.00  |    0.00   | -                                        | n/a  |
| 1    | Ts   | N/M       |  X    |   X     |    X      | W/L/T                                    | n/a  |
| 2    | Ts   | N/M       |  X    |   X     |    X      | W/L/T                                    | (a)  |
| 3    | Ts   | N/M       |  X    |   X     |    X      | W/L/T                                    | (c)  |
| ...  | ...  | ...       |  ...  |   ...   |    ...    | ...                                      | ...  |

## Stopping reason
[One of:
 - "Stopped at iter N: three consecutive iterations could not produce
   a scorecard improvement; final tally beats baseline (X wins, Y
   losses, Z ties)."
 - "Exhausted 20-iteration budget; final state below."
 - "Stopped at iter N because [specific reason]."]

## Final scorecard — head-to-head

(Same head-to-head table format as iter2. Show baseline and final
iteration side by side, with W/L/T per axis.)

## Per-axis trajectory

For each axis A.1–A.6, B.1–B.3, C.1, D.1, D.2: a one-line summary
of how it moved across iterations. Example:
- A.1 substring-match assertions: 14 (iter_1) → 11 (iter_3) → 4 (iter_5) → 0 (iter_8)

## What this run added on top of baseline quality

[Substantive paragraph: which axes you won, how. Naming the moves
that mattered. This is what Run 1's iter20 didn't produce; if you
can't write this paragraph, you stopped too early or chased coverage
instead of quality.]

## Verification notes
- git history consulted for deleted tests? (No)
- Baseline test bodies read? (No)
- REPL verifications? (list)
- `pip install -e .` from worktree? (No)
- Each iteration's commit message names the move + axis delta? (Y)
```
