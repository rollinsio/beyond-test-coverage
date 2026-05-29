## Your task — ITER2 policy (Run 3)

Up to 2 generate→run→score→improve iterations. Success = winning the
quality scorecard, not hitting coverage.

### Steps

1. **Capture the baseline scorecard** (target):
   ```bash
   mkdir -p .rex_metrics
   {SCORE_CMD_BASELINE}
   ```
   Aggregate counting only — no reading baseline test bodies.

2. **Delete the tests and commit:**
   ```bash
   {DELETE_CMD}
   git commit -am "Remove tests for Run 3 benchmark (iter2)"
   ```

3. **Iteration 1 — foundation.** Read the source, verify non-obvious
   behavior out-of-band ({VERIFY_CMD}, log it), and write a suite that
   already beats the baseline on as many axes as possible (quality
   contract throughout). Get it GREEN (`{RUN_CMD}`). Score yourself
   (`{SCORE_CMD}`), save to `.rex_metrics/iter_1/`, commit.

4. **Iteration 2 — deepening.** Look at iter-1's head-to-head and
   target your worst axes. Pick **two or more** improving moves, e.g.:
   - replace recomputed-expected asserts with fixed vectors (A.4↓, B.1↑)
   - replace substring/`||` error matches with type/code checks (A.1↓, A.5↓)
   - fold repetition into table-driven cases (D.1↓, D.2↑)
   - add boundary tests / framework-primitive integration tests (B.2, B.3)
   - drop hand mocks for real construction or primitives (C.1→0)

   Fixing real failures is obligatory and doesn't count as a move.
   Keep it GREEN. Score, save to `.rex_metrics/iter_2/`, commit with a
   message naming the moves and axis deltas.

5. Stop after at most 2 iterations. Write `.rex_metrics/SUMMARY.md`
   with the final head-to-head tally, the moves you made, and
   verification notes. Report the final W/L/T and green/red status.
