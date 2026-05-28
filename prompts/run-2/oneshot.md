## Your task — ONE-SHOT policy (Run 2)

You get exactly ONE generation pass. No repair iterations. The hard
constraints from the common header and the quality contract apply.

The success criterion is **scorecard wins, not coverage %**. See
`quality_scorecard.md`. Coverage is a floor only.

### Steps

1. **Pre-compute the baseline's scorecard** before doing anything else.
   Use the `grep -c` / `wc -l` recipes from `quality_scorecard.md`
   against `{BASE}/{TESTS_DIR}/` to get the baseline's:
   - A.1–A.6 anti-pattern counts
   - B.1 fixed-vector test count (search for `assert\s+\w+\s*==\s*b?["'][A-Za-z0-9+/=\\\\x]{16,}` and similar)
   - C.1 mock_real_loc + C.2 mock_framework_loc
   - D.1 test_loc and test_count
   - D.2 parametrize occurrences
   Write these to `.rex_metrics/baseline_scorecard.json`. **You may
   not read the baseline's test file bodies** — only run aggregate
   commands.

2. Delete the entire `{TESTS_DIR}/` directory and commit the deletion:
   ```bash
   git rm -r {TESTS_DIR}
   git commit -m "Remove tests for Run 2 benchmark (oneshot)"
   ```
   From this point on, **the deleted tests are off-limits**.

3. Confirm coverage drops to ~0 by running the suite (empty test set).
   Save artifacts under `.rex_metrics/coverage_after_delete.{json,xml,txt}`.

4. Read the source under `{SOURCE_DIR}/`. **Before writing any tests
   that depend on stdlib or third-party behavior, verify your
   assumptions in a Python REPL.** Log each REPL check to
   `.rex_metrics/repl_verifications.log`.

5. In ONE pass, write a test suite that aims to **beat the baseline
   scorecard**:
   - Anti-pattern counts (A.1–A.6) below baseline's.
   - Fixed-vector test count (B.1) above baseline's.
   - Boundary tests (B.2) covering at least 80 % of source comparisons.
   - `mock_real_loc` (C.1) at or below baseline's (target 0).
   - LOC efficiency (D.1) at most 1.2× baseline's `test_loc/test_count` ratio.
   - All tests pass; coverage floor (F.1, F.2) met.

6. Run the suite ONCE with coverage. Save artifacts under
   `.rex_metrics/generated_coverage.{json,xml,txt}`.

7. If any test fails, **do not iterate**. Record the failure in
   `.rex_metrics/SUMMARY.md` and stop. (This is what the policy
   measures — your ability to get it right in one pass.)

8. Compute your own scorecard. Write it to
   `.rex_metrics/final_scorecard.json`. Commit:
   `git add {TESTS_DIR} .rex_metrics && git commit -m "Generated tests (Run 2 oneshot)"`.

### SUMMARY.md template

```markdown
# Run 2 — {REPO} / oneshot

## Coverage floor (informational)

| Metric            | Baseline | This suite | Floor met? |
|-------------------|---------:|-----------:|:----------:|
| Pure line %       |   {BL_LINE} | X.XX |   Y/N    |
| Pure branch %     |   {BL_BRANCH} | X.XX |   Y/N    |
| Combined %        |   {BL_COMBINED} | X.XX |   n/a    |

## Quality scorecard — head-to-head

| Axis | Baseline | This suite | Win/Loss/Tie |
|------|---------:|-----------:|:------------:|
| A.1 substring-match assertions  | N | M | W/L/T |
| A.2 private-symbol imports      | N | M | W/L/T |
| A.3 tautological readbacks      | N | M | W/L/T |
| A.4 recomputed crypto/encoding  | N | M | W/L/T |
| A.5 or-joined error matches     | N | M | W/L/T |
| A.6 hand-coded char sets        | N | M | W/L/T |
| B.1 fixed-vector tests          | N | M | W/L/T |
| B.2 boundary-test coverage      | N/total | M/total | W/L/T |
| B.3 framework-primitive tests   | N | M | W/L/T |
| C.1 mock_real_loc               | N | M | W/L/T |
| D.1 LOC per test                | N | M | W/L/T |
| D.2 parametrize ratio           | N | M | W/L/T |
| E.1 all tests pass              | Y | Y/N | n/a |
| E.2 REPL-verified assumptions   | n/a | Y/N | n/a |

**Final tally:** N wins, M losses, T ties. **Suite is better:** Y/N.

## Result
- Tests passed / failed: N / M
- Wall-clock (pytest only): T s

## REPL verifications performed
[For each: the function tested, the input, the actual output.
 If you wrote no tests that needed REPL verification, say so explicitly.]

## Failures (if any)
[For each failure: test name + root cause. State explicitly whether
 it's a test-side bug or a real bug-find in {REPO}.]

## Verification notes
- Did you consult git history for the deleted tests? (Required answer: No)
- Did you read individual baseline test file bodies? (Required: No)
- Did you run `pip install -e .` from this worktree? (Required: No)
```
