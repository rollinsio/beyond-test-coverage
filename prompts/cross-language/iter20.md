## Your task — ITER20 policy (cross-language)

Up to 20 generate→run→score→improve iterations. Success = winning the
quality scorecard decisively. The iteration budget is for *deepening
quality* — spend it until marginal improvement is genuinely zero.
(Lesson from the coverage-driven baseline: every iter20 session quit at ~iter 2 on coverage parity.
Coverage parity is NOT a stopping condition.)

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
   git commit -am "Remove tests for the benchmark (iter20)"
   ```

3. **Iteration 1** — fresh suite per the quality contract, already
   aiming to beat the baseline. Get GREEN (`{RUN_CMD}`), score
   (`{SCORE_CMD}`), save to `.rex_metrics/iter_1/`, commit.

4. **Iterations 2..20** — each must produce a **real scorecard
   improvement** without regressing another axis or going red:
   - an A.* anti-pattern count down (cite file:line in the commit)
   - fixed vectors (B.1) added for round-trip-only behaviors
   - a new source boundary covered (B.2), observable to a caller
   - framework-primitive integration tests (B.3)
   - repetition folded into tables (D.1↓, D.2↑) with no lost cases
   - hand mocks removed (C.1→0)

   **Not improvements:** tautological readbacks to flip a branch,
   defensive-arm tests of guards, duplicates, or pinning
   implementation details the contract doesn't promise.

5. **Stop early** only when all hold: suite is green, your tally beats
   the baseline, AND you've spent **3 consecutive iterations** unable to
   find a non-regressing improvement (document those 3 attempts).
   Otherwise keep going up to 20.

6. Save every iteration to `.rex_metrics/iter_<n>/` (with its scorecard
   JSON), and name the move + axis delta in each commit message.

7. Write `.rex_metrics/SUMMARY.md`: a per-iteration table, the stopping
   reason, the final head-to-head tally, a per-axis trajectory, and
   verification notes. Report the final W/L/T and green/red status.
