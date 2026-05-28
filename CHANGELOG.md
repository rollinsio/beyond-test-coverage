# Changelog

Tracks changes to the experiment design, prompts, and tooling
between runs. Each `[Run N]` section is the design that produced (or
will produce) that run's worktrees. Once a run executes, its prompts
and metadata should not be edited — subsequent changes go into the
next `[Run N+1]` section.

Format roughly follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

Changes intended for Run 3+ go here. Currently empty.

---

## [Run 2] — 2026-05-28 (designed; not yet executed)

The defining shift from Run 1: **the success criterion is winning a
multi-axis quality scorecard, not hitting a coverage number.**
Coverage becomes a non-regression floor only.

### Added
- `prompts/run-2/quality_scorecard.md` — multi-axis quality goal (axes A–F: anti-fragility counts, rigor signals, mocking footprint, LOC efficiency, suite correctness, coverage floor). The session computes a baseline scorecard at the start and races to beat it.
- `prompts/run-2/common_header.md` — reframes coverage as a floor; forbids git-history recovery; forbids `pip install -e .` from worktrees; names framework primitives per repo.
- `prompts/run-2/quality_contract.md` — 10 anti-fragility rules with negative + positive examples covering: error-message substring matching, recomputed crypto, private symbols, tautological constructor readbacks, `or`-joined assertions, hand-coded char sets, parametrize/fixtures/inheritance, boundary tests, REPL verification of stdlib assumptions, framework-primitive preference.
- `prompts/run-2/oneshot.md` / `iter2.md` / `iter20.md` — per-policy bodies anchored on scorecard wins.
- `runs/run-1.md` — preserved Run 1 worktree inventory with verified pass/fail and coverage figures.
- `FINDINGS.md` — running log of findings; Run 1 entry has 9 sub-findings.
- `CHANGELOG.md` — this file.
- `configs/<repo>/bench.coveragerc` — versioned copies of the coverage config used in Run 1 (preserved so a future bootstrap can regenerate without depending on the OSS dirs).
- `scripts/setup_run2.py` — materializes `wt-r2-*` worktrees, copies `bench.coveragerc`, writes `.rex_prompt.md` and `start.sh`.
- `scripts/launch_run2.sh` — opens 9 iTerm tabs for Run 2.
- `scripts/verify_run.sh` — re-runs a worktree's suite under coverage for verification; produced [reports/VERIFICATION.md](reports/VERIFICATION.md) (caught the httpx/iter20 git-restore issue).
- `reports/VERIFICATION.md` — late-stage verification pass on all 9 Run 1 runs.
- `.gitignore` — excludes the OSS source directories, venvs, `__pycache__`, etc.

### Changed (vs Run 1's embedded prompts)
- **Goal: coverage% → scorecard win.** Sessions previously stopped at coverage parity; now they iterate until the scorecard can't improve.
- **iter20 stopping condition:** was "exceed baseline line+branch %"; is now "3 consecutive iterations without scorecard improvement OR 20 iterations reached."
- **iter2 stopping condition:** iter_2 must explicitly *deepen* on scorecard axes, not just close coverage holes.
- **SUMMARY format:** now reports pure line %, pure branch %, AND combined % side-by-side. (Run 1 SUMMARYs labeled inconsistently — see Finding 8c.)
- **Mock-LOC metric:** split into `mock_real_loc` (unittest.mock/MagicMock/mocker — quality concern) and `mock_framework_loc` (httpx.MockTransport/pytest-httpbin/monkeypatch — legitimate framework use).
- **Each iteration's commit message:** must name its scorecard move (a)–(f) and the axis delta. Makes coverage-chasing visible in `git log`.
- **Worktree naming:** Run 2 uses `wt-r2-<policy>` so Run 1's `wt-<policy>` stays preserved.
- **Branch naming:** Run 2 uses `rex-r2-wt-<policy>` so Run 1's `rex-wt-<policy>` stays preserved.

### Hard constraints added (Run 1 vulnerabilities)
- **No git-history recovery of deleted tests.** Run 1's `httpx/wt-iter20` restored 31 of 32 baseline files via `git show <delete-commit>^:tests/...`. Explicit `DO NOT git show / log -p / restore --source / read baseline test bodies` clauses in `common_header.md`.
- **No `pip install -e .` from inside worktrees.** Run 1's `requests/base/.venv` editable install was clobbered to point at `wt-iter20/src/`. Prompt now states the shared venv is sufficient.
- **REPL verification required** for any test that asserts on stdlib / third-party runtime behavior. Run 1's `itsdangerous/wt-oneshot` committed 2 failing tests that misread `urlsafe_b64decode` behavior; both would have been caught by a one-line REPL check.

### Tooling fixes
- `scripts/setup_run2.py` includes `quality_scorecard.md` in composed prompts (the original draft omitted it; fixed before any Run 2 worktree is materialized).
- `scripts/aggregate_results.py` src-prefix filter currently expects relative paths; coverage JSONs store absolute. **Not yet fixed.** Pending.

### Falsifiable predictions for Run 2
See `prompts/run-2/README.md`. Headline predictions:
- Substring-match assertions drop by >80 % vs Run 1.
- Private-symbol imports go to zero.
- No worktree restores baseline tests from git.
- iter20 iterations used rises from Run 1's 2–3 toward the 20 budget.
- Final scorecard tally is positive for ≥5 of 9 worktrees.

---

## [Run 1] — 2026-05-28 (executed and preserved)

Initial benchmark run. Three repos × three policies = 9 worktree
sessions on Opus 4.7. Coverage was the success criterion.

### Setup
- Cloned `pallets/itsdangerous`, `encode/httpx`, `psf/requests` into `<repo>/base/` (shallow clones).
- Created Python 3.12 venv per repo at `<repo>/base/.venv`, installed test deps per the project's `requirements*.txt` / `pip install -e .`.
- Unified coverage config (`bench.coveragerc`) per repo: `source = <package>`, `branch = True`.
- 3 git worktrees per repo on branches `rex-wt-{oneshot,iter2,iter20}`.

### Initial prompt design (embedded in plan doc)
- Common header: paths, env (`. ../base/.venv/bin/activate`), `bench.coveragerc`, baseline figures, repo-specific pytest extra flag (`-p no:unraisableexception` for httpx).
- Per-policy bodies:
  - `oneshot`: one generation pass, no repair; commit failures as-is.
  - `iter2`: up to 2 generate→run→fix iterations.
  - `iter20`: up to 20 iterations; stop early when baseline coverage is beaten.

### Tooling
- `scripts/gen_prompts.py` — wrote `.rex_prompt.md` per worktree.
- `scripts/launch_all.sh` — opened 9 iTerm Claude tabs (`--permission-mode auto --model claude-opus-4-7`).
- `scripts/summarize_coverage.py` — extract pure stats from coverage JSON.
- `scripts/aggregate_results.py` — cross-worktree summary table.
- Later additions during run:
  - `scripts/verify_run.sh` — re-run a worktree's suite for verification.
  - 9 per-run reports in `reports/`.
  - `audit_itsdangerous.md` — deep 3-agent fragility audit.
  - `reports/VERIFICATION.md` — late-stage integrity check.

### Outcomes
9 SUMMARYs + per-run reports in `reports/`. Net verdicts:

| Run                     | Overall              |
|-------------------------|----------------------|
| itsdangerous / oneshot  | Worse                |
| itsdangerous / iter2    | Worse                |
| itsdangerous / iter20   | Worse                |
| httpx / oneshot         | Worse                |
| httpx / iter2           | Worse                |
| **httpx / iter20**      | **Not legitimate — git-restored baseline** |
| requests / oneshot      | Worse                |
| requests / iter2        | Slightly better      |
| requests / iter20       | **Better**           |

Only requests/iter20 is unambiguously better than its baseline, via
real-I/O integration tests (`pytest-httpbin`) with zero mock LOC.

See [reports/README.md](reports/README.md) and
[reports/VERIFICATION.md](reports/VERIFICATION.md) for details.
