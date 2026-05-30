## Your task — ITER2 policy (quality)

Up to 2 generate→run→fix iterations. The hard constraints from the
common header and quality contract apply. The success criterion is
**winning the quality scorecard** (see `quality_scorecard.md`), not
hitting a coverage number.

### Steps

1. **Compute the baseline's scorecard** using the `grep -c`/`wc -l`
   recipes in `quality_scorecard.md` against `{BASE}/{TESTS_DIR}/`.
   Save to `.rex_metrics/baseline_scorecard.json`. **No reading
   baseline test file bodies.**

2. Delete `{TESTS_DIR}/` and commit. Save coverage-after-delete
   artifacts to `.rex_metrics/iter_0/`.

3. **Iteration 1 — foundation**. Goal: produce a suite that already
   beats the baseline on the scorecard. Follow the quality contract:
   - REPL checks before any stdlib-behavior assertion (log to `.rex_metrics/repl_verifications.log`)
   - Parametrize / fixtures / inheritance
   - Framework real-I/O primitives over `unittest.mock`
   - Fixed expected values, not recomputed
   - Boundary tests for source comparisons

   Save outputs and your iter_1 scorecard under `.rex_metrics/iter_1/`.
   Commit: `git add {TESTS_DIR} .rex_metrics && git commit -m "iter1: foundation"`.

4. **Iteration 2 — deepening**. The point of having a second
   iteration is to *improve the scorecard*, not to chase coverage.
   Compute iter_1's scorecard, look at the head-to-head against
   baseline, and target the axes where you're worst.

   Pick **two or more** scorecard-improving moves. Examples (not
   exhaustive — anything that improves an axis is fair game):

   a. **Replace recomputed-expected assertions with fixed vectors.**
      Move A.4 down, B.1 up.
   b. **Replace substring-match assertions with type+payload checks.**
      Move A.1 down.
   c. **Add boundary tests** for source comparisons you haven't
      exercised at the boundary. Move B.2 up.
   d. **Add integration tests via framework real-I/O fixtures.** Move
      B.3 up. Especially useful when iter_1's coverage is below
      baseline on the I/O / transport layer.
   e. **Restructure unrolled cases into parametrize/inheritance.**
      Move D.1 down (LOC), D.2 up (parametrize ratio).
   f. **Remove private-symbol uses** by finding the public API that
      reaches the same code path. Move A.2 down.
   g. **Eliminate tautological readbacks** by rewriting each as a
      behavioral assertion (effect-based, not state-based). Move A.3
      down.

   Fixing actual test failures from iter_1 is obligatory and does
   not count as one of your two deepening moves.

   Save outputs + iter_2 scorecard under `.rex_metrics/iter_2/`.
   Commit message must name the moves: e.g.
   `git commit -m "iter2 deepening: a (8 → 0 recomputed), c (added 6 boundary tests)"`.

5. After at most 2 iterations, stop regardless of remaining failures.

### SUMMARY.md template

```markdown
# {REPO} / iter2

## Coverage floor (informational, not the target)

| Iteration | Pure line % | Pure branch % | Combined % | Floor met? |
|-----------|------------:|--------------:|-----------:|:----------:|
| baseline  |  {BL_LINE} |   {BL_BRANCH} | {BL_COMBINED} |   floor    |
| iter_1    |       X.XX |          X.XX |       X.XX |    Y/N     |
| iter_2    |       X.XX |          X.XX |       X.XX |    Y/N     |

## Quality scorecard — head-to-head (final, iter_2)

(Same table format as oneshot. Mark wins/losses/ties.)

## Iter_2 moves

[For each move: which axis, what changed, count delta.
 e.g. "Move (a): replaced 8 recomputed-HMAC assertions in test_signer.py
       with fixed byte literals computed once via REPL. A.4 went 8 → 0;
       B.1 went 0 → 8."]

## Final tally vs baseline

**Wins:** N. **Losses:** M. **Ties:** T.
**Suite is better than baseline overall:** Y/N.

## REPL verifications performed
[List each]

## Verification notes
- git history for deleted tests consulted? (No, required)
- Baseline test bodies read? (No, required)
- `pip install -e .` from worktree? (No, required)
- Each iteration's commit message names its scorecard moves? (Y)
```
