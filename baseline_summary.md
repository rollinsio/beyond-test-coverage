# Baseline summary — 2026-05-28

Coverage measured on each repo's own source package only (unified `bench.coveragerc`
written into each `<repo>/base/`). Branch coverage enabled. Tests run with the deps
specified in the plan's section 2.

| Repo          | Files | Stmts | Line cov | Branch cov | Tests passed | Notes |
|---------------|------:|------:|---------:|-----------:|-------------:|-------|
| itsdangerous  |     8 |   425 |  97.65 % |   94.90 %  |          297 | pyproject `[tool.coverage.run] source = ["jinja2", "tests"]` is a pallets-template leak — we override via `bench.coveragerc`. |
| httpx         |    23 |  3134 | 100.00 % |   97.27 %  |         1417 | One test produces a `PytestUnraisableExceptionWarning` from an async generator teardown; run with `-p no:unraisableexception` to suppress it. |
| requests      |    19 |  2364 |  87.86 % |   79.48 %  |          617 | 15 skipped, 1 xfailed (expected). httpbin tests bring up local servers. |

## What this means for the iter20 "beat baseline" goal

- **httpx**: line coverage is already 100 % — any iter20 run will at best tie line
  cov, so the only meaningful target is branch (>97.27 %). Recommend switching the
  goal to "beat baseline on touched-modules set" per Section 7.
- **itsdangerous**: small margin (97.65 % line, 94.90 % branch). Achievable but
  slim — a single uncovered branch is ~1 % of the budget.
- **requests**: most headroom (87.86 % line, 79.48 % branch). This is the most
  interesting iter20 target.

## Artifacts

- `<repo>/base/bench.coveragerc` — unified coverage config (branch on, source = pkg)
- `<repo>/base/.rex_metrics/baseline_coverage.{json,xml,txt}` — coverage artifacts
- `scripts/summarize_coverage.py` — extract src-only line/branch from a coverage.json
