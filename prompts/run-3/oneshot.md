## Your task — ONE-SHOT policy (Run 3)

Exactly ONE generation pass. No repair iterations after you first run
the suite. This policy measures whether you can get it right in one go.

### Steps

1. **Capture the baseline scorecard** (your target). Run the scorer
   against the baseline test dir and save the JSON:
   ```bash
   mkdir -p .rex_metrics
   {SCORE_CMD_BASELINE}
   ```
   This is aggregate counting — allowed. Do NOT read baseline test bodies.

2. **Delete the existing tests and commit the removal:**
   ```bash
   {DELETE_CMD}
   git commit -am "Remove tests for Run 3 benchmark (oneshot)"
   ```
   From here the deleted tests are off-limits (see hard constraints).

3. **Read the source under test.** Verify any non-obvious library
   behavior out-of-band ({VERIFY_CMD}); log to
   `.rex_metrics/verifications.log`.

4. **In ONE pass, write the suite** following the quality contract:
   fixed vectors over recomputed/substring asserts, framework
   primitives over hand mocks, table-driven cases, boundary tests.
   Aim to beat the baseline on every axis.

5. **Run the suite once** (`{RUN_CMD}`). If anything fails, **do not
   iterate** — record the failure in `.rex_metrics/SUMMARY.md` and stop.

6. **Score yourself** (`{SCORE_CMD}`), save to
   `.rex_metrics/final_scorecard.json`, write `.rex_metrics/SUMMARY.md`
   (tally + green/red + any failures + verification notes), and commit:
   `git add -A && git commit -m "Generated tests (Run 3 oneshot)"`.

Report your final tally (W/L/T) and whether the suite is green.
