# LLM test-generation benchmark

An iterative experiment: have an LLM regenerate the test suites of
three open-source Python repos (`pallets/itsdangerous`, `encode/httpx`,
`psf/requests`) from scratch under different iteration policies, and
measure whether the regenerated suites are *better* than the originals.

Each "Run" is a complete pass through the experiment with a frozen
prompt set. Findings from each run inform the prompt set for the next.

## Starting Run 2 (next session, fresh)

```bash
cd /Users/rollins/experimentalCode/unit-testing-tests/llm-testgen-bench

# Materialize the 9 Run-2 worktrees + per-worktree prompts.
# Creates wt-r2-{oneshot,iter2,iter20} per repo on rex-r2-wt-* branches.
# Run-1 worktrees are NOT touched.
python scripts/setup_run2.py

# Open 9 iTerm tabs, one per worktree, running Opus 4.8 with the prompt.
./scripts/launch_run2.sh
```

After all 9 sessions finish, the verification + reports workflow is
the same as Run 1 — see `scripts/verify_run.sh` and the structure of
`reports/`.

## What the new session should know

- The success criterion for Run 2 is **the quality scorecard in
  `prompts/run-2/quality_scorecard.md`**, not coverage %. Coverage is a
  non-regression floor. This is the central change from Run 1.
- The full per-run-delta is in [CHANGELOG.md](CHANGELOG.md).
- Run 1 results and the integrity issue with `httpx/wt-iter20` are
  documented in [runs/run-1.md](runs/run-1.md) and
  [reports/VERIFICATION.md](reports/VERIFICATION.md).

## Repository layout

```
.
├── README.md             # this file
├── CHANGELOG.md          # run-to-run delta
├── FINDINGS.md           # running findings log (Run 1 entry has 9 sub-findings)
├── audit_itsdangerous.md # deep 3-agent fragility audit (Run 1)
├── baseline_summary.md   # Run 1 baseline coverage figures
├── configs/              # versioned bench.coveragerc per repo
├── prompts/
│   └── run-2/            # Run 2 prompt set (scorecard-anchored)
├── reports/              # 9 per-run reports + VERIFICATION + index
├── runs/
│   └── run-1.md          # preserved Run 1 worktree inventory
└── scripts/
    ├── setup_run2.py     # creates Run 2 worktrees + materializes prompts
    ├── launch_run2.sh    # opens 9 iTerm tabs for Run 2
    ├── verify_run.sh     # re-runs a single worktree's suite for verification
    ├── aggregate_results.py  # cross-worktree summary (Run 1; needs path fix)
    └── ...               # gen_prompts.py + launch_all.sh from Run 1
```

OSS source trees live alongside (in `itsdangerous/`, `httpx/`,
`requests/`) and are `.gitignore`d. Each is its own git clone with its
own history; the `rex-wt-*` branches inside them preserve every run's
generated test content.

## Hermicity notes for the next session

- The shared `<repo>/base/.venv` is sufficient for all 9 worktrees.
  Sessions should NOT run `pip install -e .` from inside worktrees
  (Run 1 vulnerability: it clobbers the shared venv's editable
  install). The Run 2 prompts encode this constraint.
- The `requests/base/.venv` editable install was clobbered to
  `wt-iter20/` during Run 1; reset to `base/` on 2026-05-28. If
  Run 2 sessions also clobber it, fix with:
  `requests/base/.venv/bin/pip install -e requests/base --no-deps`.
- The aggregator script's src-prefix filter expects relative paths,
  but coverage JSONs store absolute. Open issue; the
  `scripts/verify_run.sh` script does not have this bug and is
  authoritative for verification.

## Iteration philosophy

Each run produces evidence that refines the next prompt set. The
prompt set is the experiment's instrument; we expect to revise it
several times. To preserve every revision:

- Run N's prompts live under `prompts/run-N/` and don't get edited
  after the run executes.
- Run N's worktrees live on disk and use branch prefix `rex-rN-wt-*`
  (Run 1 used the legacy `rex-wt-*` since the convention came later).
- `CHANGELOG.md` records the per-run prompt-set delta.
- `FINDINGS.md` records the per-run findings that motivate the next
  changes.

If a finding suggests changing the scorecard itself (axes, weights,
measurement), that's a CHANGELOG entry under the `[Unreleased]`
section and gets folded into the next run's design.
