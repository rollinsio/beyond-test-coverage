# Run 2 prompt set

Drafted 2026-05-28 from [Run 1 findings](../../FINDINGS.md). Worktrees
for this run are named `wt-r2-<policy>` so they don't collide with
Run 1's preserved `wt-<policy>` worktrees.

## The single most important change vs Run 1

**Run 1 used coverage as the goal.** Sessions stopped at coverage
parity, then sat on their budget. Generated suites had high coverage
and low quality.

**Run 2 uses a multi-axis quality scorecard as the goal.** Coverage
is a non-regression floor (don't go below baseline) but not a target.
Iterations are spent until marginal scorecard improvement is zero.

The scorecard is in [`quality_scorecard.md`](quality_scorecard.md).
Six axis groups (A–F), countable from the test files via `grep -c`
and `wc -l`. The session computes a baseline scorecard from
`{BASE}/{TESTS_DIR}/` once at the start, then races to beat it.

## Files in this directory

- [`common_header.md`](common_header.md) — shared per-repo header (paths, env, no-git-recovery, framework primitives, coverage-is-a-floor framing)
- [`quality_contract.md`](quality_contract.md) — 10 anti-fragility rules with negative + positive examples (the underlying *what* to do)
- [`quality_scorecard.md`](quality_scorecard.md) — the operationalized goal (axes, how to measure, the win condition)
- [`oneshot.md`](oneshot.md) — body for `wt-r2-oneshot` worktrees (one pass, beat baseline scorecard)
- [`iter2.md`](iter2.md) — body for `wt-r2-iter2` worktrees (iter_1 foundation, iter_2 scorecard-improving moves)
- [`iter20.md`](iter20.md) — body for `wt-r2-iter20` worktrees (iterate until 3 consecutive iterations can't improve scorecard)

A session is given a single prompt that is `common_header.md` +
`quality_contract.md` + `quality_scorecard.md` + the matching
per-policy body, all with paths substituted.
`scripts/setup_run2.py` (in the project root) materializes these
into each worktree as `.rex_prompt.md` and writes `start.sh`.

## Key differences vs Run 1 prompts (full list)

| Change                                                                     | Encoded in                |
|----------------------------------------------------------------------------|---------------------------|
| Goal is scorecard-win, not coverage match                                  | `common_header.md`, per-policy bodies |
| Multi-axis quality scorecard with operational measurements                 | `quality_scorecard.md`    |
| Anti-fragility contract (10 rules with negative + positive examples)       | `quality_contract.md`     |
| Forbid recovering deleted tests from git history                           | `common_header.md`        |
| Forbid reading baseline test file bodies (still permits aggregate counting) | `common_header.md`        |
| Forbid `pip install -e .` from inside the worktree                         | `common_header.md`        |
| Require REPL verification of stdlib/third-party assumptions; logged        | `quality_contract.md`, all policy bodies |
| Report pure line%, pure branch%, combined % separately                     | per-policy bodies         |
| iter20 stopping condition: 3-consecutive-no-improvement, not coverage-parity | `iter20.md`               |
| Each iteration's commit message must name its scorecard move + axis delta  | `iter20.md`, `iter2.md`   |
| Point sessions at the framework's real-I/O fixtures by name (per repo)     | `common_header.md`        |
| Mention LOC efficiency via parametrize/fixtures/inheritance                | `quality_contract.md`     |
| Mock-LOC split: real mocking vs framework primitives                       | `quality_scorecard.md`    |
| Boundary-test requirement for `<`/`<=`/`==` in source                       | `quality_contract.md`, `quality_scorecard.md` |

## Falsifiable predictions for Run 2

If Run 2's prompts work, we predict:

1. **Mock-real-LOC** (`MagicMock`/`patch(`/`mocker`) trends to zero across all 9 worktrees.
2. **Substring-match assertions** drop by >80 % vs Run 1 (count per worktree).
3. **Private-symbol imports** go to zero across all 9 worktrees.
4. **No worktree restores baseline tests from git.** (Hash-compare check.)
5. **Oneshot test-side-bug count drops to zero.** No committed-failing tests from stdlib misunderstanding.
6. **iter20 iterations used rises** from Run 1's 2–3 toward the 20 budget — specifically because matching coverage no longer satisfies the stop condition.
7. **iter2/iter20 on httpx and requests add integration tests** (via `pytest-httpbin`, `MockTransport`, `WSGI`/`ASGI` transports) when unit tests plateau below baseline coverage.
8. **Generated suites have higher fixed-vector count** (B.1) than baseline — i.e., they catch parallel-mutation bugs better than the baseline did.
9. **Generated suites have higher boundary-test coverage** (B.2) than baseline — i.e., they catch off-by-one mutations better.
10. **Final scorecard tally is positive** (wins > losses) for at least 5 of 9 worktrees.

If any prediction fails, that's a finding for Run 3.

## What the run will produce

After all 9 sessions finish, each worktree has:

- `.rex_metrics/baseline_scorecard.json` — the baseline's measured axes
- `.rex_metrics/iter_<n>/*.json` — per-iteration coverage + scorecard
- `.rex_metrics/SUMMARY.md` — head-to-head scorecard + per-iteration table
- A commit history where each iteration's message names its move + axis delta

The aggregator script will need updating to read `final_scorecard.json`
and produce a cross-worktree comparison. That's Run 2 setup work, not
session-level work.
