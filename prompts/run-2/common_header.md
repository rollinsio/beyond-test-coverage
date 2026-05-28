# Benchmark session — {REPO} / {POLICY} (Run 2)

You are running ONE arm of an iterative LLM test-generation benchmark
on the open-source repo `{REPO}`. You are in a dedicated git worktree
created specifically for this run.

This is **Run 2**. Run 1 produced patterns we now know to avoid; the
constraints below encode that. Don't deviate from them.

## The goal

**Produce a test suite that is *better* than the baseline's.** Not a
suite that hits a coverage number. Run 1's framing ("beat baseline
coverage") led every iterative session to stop early at coverage
parity and then sit on its iteration budget. The benchmark goal in
Run 2 is quality, measured by the scorecard in `quality_scorecard.md`.

Coverage appears in two places only: as a **non-regression floor**
(don't go below baseline) and as a **per-iteration sanity check**
(does this iteration's new code execute at all). You are not trying
to *hit* a coverage number; you're trying to win the quality
scorecard.

## Paths

- **Worktree (your CWD):** `{WORKTREE}`
- **Baseline clone (reference; do not modify):** `{BASE}`
- **Source package:** `{SOURCE_DIR}/` (importable as `{PACKAGE}`)
- **Tests directory to delete + regenerate:** `{TESTS_DIR}/`
- **Metrics output:** `.rex_metrics/` (inside this worktree)
- **Coverage config (shared with baseline):** `bench.coveragerc` —
  already copied into this worktree

## Environment

The dependencies you need are installed in a shared venv at
`../base/.venv`. Use it as-is:

```bash
cd {WORKTREE}
. ../base/.venv/bin/activate
mkdir -p .rex_metrics
```

**Do NOT run `pip install -e .` from inside this worktree.** That
clobbers the shared venv's editable install pointer and causes
coverage to record paths from the wrong worktree. (Discovered in Run
1: `requests/base/.venv` ended up pointing at `wt-iter20/src/`.)
{DEP_NOTE}

## How to run pytest and coverage

Always invoke pytest through coverage with the shared rcfile. The
extra pytest flag (if any) is required for this repo:

```bash
python -m coverage run --rcfile=bench.coveragerc -m pytest -q {PYTEST_EXTRA}
python -m coverage json --rcfile=bench.coveragerc -o .rex_metrics/<name>.json
python -m coverage xml  --rcfile=bench.coveragerc -o .rex_metrics/<name>.xml
python -m coverage report --rcfile=bench.coveragerc > .rex_metrics/<name>.txt
```

## Baseline figures — *informational, not the target*

Measured from the unchanged baseline (`{BASE}/.rex_metrics/baseline_coverage.json`):

- Pure line coverage:   {BL_LINE} %
- Pure branch coverage: {BL_BRANCH} %
- Combined (line+branch): {BL_COMBINED} %

These are the *floor* for axis F (the coverage floor) in the
scorecard. They are NOT the target you're trying to hit. You're
trying to beat the baseline on the *quality* axes in
`quality_scorecard.md`; coverage just keeps you from regressing.

## **Hard constraint: do not recover deleted tests from git history**

You will be instructed to delete the existing `{TESTS_DIR}/` directory
and commit the deletion. Once that commit is made, **treat the
deleted tests as if they never existed**:

- **DO NOT** use `git show <commit>:tests/...`
- **DO NOT** use `git log -p`, `git diff HEAD^`, `git restore --source=<commit>^`
- **DO NOT** inspect the reflog, stash, or anywhere else that could
  surface the deleted content
- **DO NOT** ask another tool to "remember what the tests looked like"
  on your behalf

The benchmark measures *generation*, not restoration. In Run 1, the
`httpx/wt-iter20` session used `git show` to restore 31 of 32
baseline files, then added a tiny supplement and reported "100 %
coverage." That run is recorded as a verification failure, not a
result. Don't repeat it.

You **may** look at the baseline clone at `{BASE}` for *high-level
project structure* (which modules exist, what `setup.py` /
`pyproject.toml` say). You **may not** read the baseline's test files
directly (they're the answer key; reading them is a different form of
the same cheat).

You **may** run `grep -c` / `wc -l` / `find` against `{BASE}/{TESTS_DIR}/`
to compute the baseline's *scorecard axes* (test counts, LOC,
substring-match counts, etc.) — those are aggregate signals, not
test content.

## Framework-intended test primitives

`{REPO}`'s baseline test suite uses these primitives. They are part of
the public API and the right tool for testing this codebase. Use them.
Do NOT introduce `unittest.mock` / `MagicMock` / `mocker` if a
framework primitive exists:

{FRAMEWORK_PRIMITIVES}
