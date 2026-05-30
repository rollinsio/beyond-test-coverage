# Coverage-driven control — 2026-05-28

**Status:** preserved for posterity. Worktrees, branches, and reports
should not be modified or deleted.

## Worktree inventory

| Path                                | Branch              | Tests | Pass | Fail | Pure line % | Pure branch % | Verdict     |
|-------------------------------------|---------------------|------:|-----:|-----:|------------:|--------------:|-------------|
| `itsdangerous/base`                 | `main`              |   297 |  297 |   0  |    97.65 %  |    94.90 %    | baseline    |
| `itsdangerous/wt-oneshot`           | `rex-wt-oneshot`    |   159 |  157 |   2  |    98.12 %  |    95.92 %    | Worse       |
| `itsdangerous/wt-iter2`             | `rex-wt-iter2`      |   176 |  176 |   0  |   100.00 %  |   100.00 %    | Worse       |
| `itsdangerous/wt-iter20`            | `rex-wt-iter20`     |   163 |  163 |   0  |   100.00 %  |   100.00 %    | Worse       |
| `httpx/base`                        | `master`            |  1417 | 1417 |   0  |   100.00 %  |    97.27 %    | baseline    |
| `httpx/wt-oneshot`                  | `rex-wt-oneshot`    |   449 |  449 |   0  |    95.95 %  |    92.77 %    | Worse       |
| `httpx/wt-iter2`                    | `rex-wt-iter2`      |   416 |  416 |   0  |    97.13 %  |    93.36 %    | Worse       |
| `httpx/wt-iter20`                   | `rex-wt-iter20`     |  1440 | 1440 |   0  |   100.00 %  |   100.00 %    | **NOT LEGITIMATE — restored baseline tests from git history** |
| `requests/base`                     | `main`              |   617 |  617 |   0  |    87.86 %  |    79.48 %    | baseline    |
| `requests/wt-oneshot`               | `rex-wt-oneshot`    |   380 |  380 |   0  |    85.62 %  |    72.51 %    | Worse       |
| `requests/wt-iter2`                 | `rex-wt-iter2`      |   483 |  483 |   0  |    92.39 %  |    83.83 %    | Slightly better |
| `requests/wt-iter20`                | `rex-wt-iter20`     |   509 |  509 |   0  |    91.71 %  |    85.70 %    | **Better**  |

Numbers reproduced via `scripts/verify_run.sh`; see
[reports/VERIFICATION.md](../reports/VERIFICATION.md).

## Prompt files used (preserved in-place)

Each worktree's prompt is at `<worktree>/.rex_prompt.md`. The launcher
script is at `scripts/launch_all.sh`. The prompt generator that
produced them is at `scripts/gen_prompts.py`.

Common header per repo: paths, environment activation
(`. ../base/.venv/bin/activate`), `cp ../base/bench.coveragerc .`,
pytest extra flag (`-p no:unraisableexception` for httpx), the
baseline coverage figures.

Per-policy bodies:
- **oneshot**: one generation pass, no repair; commit failures as-is
- **iter2**: up to 2 generate→run→fix iterations
- **iter20**: up to 20 iterations; stop early when baseline is beaten

## Branches (all on shallow clones)

For each repo, three branches were created with `git worktree add -b`:
- `rex-wt-oneshot`
- `rex-wt-iter2`
- `rex-wt-iter20`

Each tracks the worktree of the same name. The quality-driven stage should use distinct
branch names (`rex-r2-wt-*`) so the two rounds don't conflict.

## Known issues with this run (kept for the record)

1. **`httpx/wt-iter20` restored baseline tests from git history**, then
   added a 23-test supplement. 31 of 32 test files are byte-identical
   to `httpx/base/tests/`. Not a legitimate generation result.
   See [reports/httpx-iter20.md](../reports/httpx-iter20.md).

2. **`requests/base/.venv` editable install was clobbered** — points
   to `wt-iter20/src/requests/` instead of `base/src/requests/`. Source
   files are identical across worktrees so test outcomes are unchanged,
   but coverage paths in JSON files reflect wt-iter20.
   See [reports/VERIFICATION.md](../reports/VERIFICATION.md).

3. **SUMMARY.md files use inconsistent labels for "Line coverage"** —
   some report pure statement %, others report combined line+branch %.
   The verification report computes both for every run.

## Where reports live

- Cross-policy synthesis (itsdangerous deep audit): [audit_itsdangerous.md](../audit_itsdangerous.md)
- Per-run reports: [reports/](../reports/)
- Verification pass: [reports/VERIFICATION.md](../reports/VERIFICATION.md)
- Findings + quality-driven implications: [FINDINGS.md](../FINDINGS.md)
