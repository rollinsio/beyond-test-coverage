---
name: test-quality
description: >-
  Audit, harden, or generate unit tests with a focus on mutation-resistance and
  durable quality — not just coverage %. Use when the user asks to improve or
  harden test quality, make tests less fragile/brittle, review tests for
  anti-patterns (error-message-substring asserts, private-symbol access,
  tautological constructor readbacks, recomputed-crypto expectations,
  over-mocking, missing boundary tests, unrolled cases that should be
  parametrized), generate a high-quality suite for an untested module, or
  generally "make my tests better". Measures a suite against a validated quality
  scorecard and iterates until it plateaus, holding coverage as a non-regression
  floor and REPL-verifying library assumptions. Works across stacks —
  Python/pytest (validated), JavaScript/TypeScript (Jest, Vitest, Mocha/Chai,
  node:test), and Go — with a per-language scorer; the rubric is the same
  everywhere.
---

# test-quality

Bring a target's tests up to a durable-quality bar. "Quality" means tests that
**fail when behavior breaks and survive when it's only refactored** — the
opposite of coverage-chasing suites that hit 100% yet catch nothing.

This skill encodes the result of a controlled experiment: pointing test
generation at a multi-axis *quality* scorecard (rather than a coverage number)
produced suites that beat human-written baselines on 8 of 9 measured cells. The
two reference docs are that experiment's distilled output:
- `references/quality-contract.md` — 10 anti-fragility rules, each with the repair.
- `references/scorecard.md` — the scoring axes, the improvement gate, the stop condition.
- `scripts/score.py` — measures the auto-countable axes for any pytest suite.

**Read both reference docs before starting.** They are the substance; this file
is the procedure.

## Core principle

Coverage is a **floor, not a goal.** Once the suite is at or above its starting
coverage, more coverage doesn't count as improvement. What counts is moving the
quality axes: fewer fragility patterns, more rigor signals, less real mocking,
better LOC efficiency — with every test traceable to a user-observable contract.

## Inputs

- **Target** (required): a module/package to test, an existing test file/dir to
  improve, or both. If the user didn't specify, ask what to target.
- **Test command** (auto-detect, confirm if unsure): how to run the suite with
  coverage. Detect from the project's config/manifest, then by stack:
  - pytest: `python -m pytest <tests> --cov=<src> --cov-branch`
  - Jest: `npx jest --coverage` · Vitest: `npx vitest run --coverage`
  - Mocha: `npx c8 --check-coverage mocha` (c8/nyc for coverage)
  - Go: `go test -cover -coverprofile=cover.out ./... && go tool cover -func=cover.out`
  Read `pyproject.toml`/`pytest.ini`, `package.json`(`scripts.test`,
  jest/vitest config), `go.mod`, `Makefile` to find the project's real command —
  prefer it over the defaults above.

## Procedure

### 1. Scope & detect
Identify the source package and its tests dir. Detect the **language/framework**
(this sets the `score.py --lang` profile: `python`, `js`, or `go`) and the
coverage-enabled test command. Determine the **mode**:
- tests exist for the target → **audit + improve** (refactor in place).
- target is untested → **generate** a fresh suite.
(A target can be mixed: improve what exists, generate for the gaps.)

### 2. Capture the baseline (do this BEFORE changing anything)
- Run the suite with branch coverage; record line % and branch % — this is the
  coverage floor.
- `python <skill>/scripts/score.py --tests <tests_dir> [--lang python|js|go]`
  for the auto axes (`--lang` auto-detects if omitted).
- Preserve the starting state so you can score against it: copy the tests dir
  aside, or note the git ref. Later runs use `--baseline <that copy>`.
- For generate mode with no existing tests, the floor is the source's current
  coverage (often 0) and the baseline scorecard is empty — the bar is then the
  contract itself (zero violations), not "beat the old suite".

### 3. Audit against the contract
Read the tests (or, for generate mode, the source) and inventory:
- The auto axes from `score.py`.
- The judgement axes by reading: A.3 tautological readbacks, A.6 hand-coded
  char-sets, B.2 boundary coverage (enumerate every `<,<=,>,>=,==,!=` in the
  source and check each has a boundary test), B.3 real-I/O fixture use, E.3
  contract-naming.
Produce a concrete findings list: file:line → which rule → the repair.

### 4. Improve — iterate to plateau
Loop. Each round, make ONE focused, justified move:
- **Refactor** an existing fragile test (apply the contract repair in place — do
  not leave the old version; rewrite it), or
- **Add** a missing rigor test (a boundary case, a fixed-vector pin, a
  real-I/O/integration test, a parametrized consolidation), or
- **Generate** a cohesive new test file for an untested unit.

Rules for the loop:
- **REPL-verify first.** Before asserting on any stdlib/library runtime
  behavior, run it and assert what actually happens — `python -c "..."`,
  `node -e "..."` (or a scratch test you delete), `go run` a snippet. Don't
  assert from memory. Keep a short log of what you checked.
- **Public API only**; pin fixed expected literals; cover the boundary; prefer
  real-I/O fixtures over `unittest.mock`; parametrize instead of unrolling.
- **Run the suite** after each move. All tests must pass before you keep a move.
- **Apply the gate** (`references/scorecard.md`): keep the move only if the
  coverage floor holds, an A-axis dropped or a B-axis rose, nothing regressed,
  and every new test maps to a stated contract. If a move fails the gate, revert
  it — a no-op round is not progress.
- Re-score after each round (`score.py --tests <tests> --baseline <start>`).

**Stop** when 3 consecutive rounds can't produce a gated improvement, OR there
are no contract violations left and every source boundary has a test.

### 5. Verify & report
- Final full run: suite passes, coverage ≥ floor on both line and branch.
- Print the before/after scorecard (auto axes as a W/L/T tally vs. the captured
  baseline) plus the judgement-axis assessment.
- List residual risks honestly: boundaries still uncovered, mutations likely to
  survive, anything you couldn't verify.

## Hard rules

- **Never weaken a test to win an axis.** Deleting a strict assertion to drop an
  A-count, or loosening `==` to `in`, is a regression even if the score "improves".
  The gate's rule 3 exists to catch exactly this.
- **Never chase coverage through private internals.** If you can't name the
  user-observable contract a test protects, don't write it.
- **Don't invent library behavior.** REPL-verify or read the docs (check context7
  for library docs) — never assert from memory about what a call raises/returns.
- Match the existing suite's style, fixtures, and naming when improving in place.

## Notes

- **Validation tiers.** Python/pytest is empirically validated (the scorer's
  numbers were checked against a controlled experiment). The `js` (Jest/Vitest/
  Mocha/node:test) and `go` profiles apply the same axes with heuristic regexes —
  trustworthy for trends and worst-offenders, but lean harder on reading the
  tests, and treat the W/L/T tally as indicative, not authoritative.
- **Other stacks** (JUnit, RSpec, xUnit, …): the rubric and contract still apply
  by judgment. To add a first-class profile, extend `PROFILES` in
  `scripts/score.py` (file globs + a `test_def` regex + the per-axis regexes) —
  it's a self-contained dict per language.
- For a large target, scope to one module/package per invocation rather than a
  whole repo at once; the iterate-to-plateau loop is per-target.
