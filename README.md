# LLM test-generation benchmark

An iterative experiment: have an LLM regenerate the test suites of
three open-source Python repos (`pallets/itsdangerous`, `encode/httpx`,
`psf/requests`) from scratch under different iteration policies, and
measure whether the regenerated suites are *better* than the originals.

Each "Run" is a complete pass through the experiment with a frozen
prompt set. Findings from each run inform the prompt set for the next.

## Starting Run 2 (next session, fresh)

```bash
cd path/to/llm-testgen-bench   # the repo root

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
- **Run 2 results at a glance:** open
  [`docs/scorecard-results.html`](docs/scorecard-results.html) — an
  interactive dashboard of the per-axis baseline-vs-generated values
  across all three arms (Run 1 → r2b → Run 2), the model-vs-prompt
  decomposition (2/9 → 8/9 → 9/9), the coverage-floor caveat, and the
  full table of prompt-design changes with measured outcomes.

## Repository layout

```
.
├── .claude/
│   └── skills/
│       └── test-quality/ # bundled quality-scorecard skill (see below)
├── README.md             # this file
├── CHANGELOG.md          # run-to-run delta
├── FINDINGS.md           # running findings log (Run 1: §1–9; Run 2: §10–14 + decomposition)
├── audit_itsdangerous.md # deep 3-agent fragility audit (Run 1)
├── baseline_summary.md   # Run 1 baseline coverage figures
├── configs/              # versioned bench.coveragerc per repo
├── docs/
│   └── scorecard-results.html  # interactive axes before/after + changes dashboard
├── prompts/
│   └── run-2/            # Run 2 prompt set (scorecard-anchored)
├── reports/              # 9 per-run reports + VERIFICATION + index
├── runs/
│   └── run-1.md          # preserved Run 1 worktree inventory
└── scripts/
    ├── setup_run2.py     # creates Run 2 worktrees + materializes prompts
    ├── launch_run2.sh    # opens 9 iTerm tabs for Run 2
    ├── verify_run.sh     # re-runs a single worktree's suite for verification
    ├── aggregate_results.py  # cross-worktree coverage summary; --run N selects wt-rN-*
    └── ...               # gen_prompts.py + launch_all.sh from Run 1
```

OSS source trees live alongside (in `itsdangerous/`, `httpx/`,
`requests/`) and are `.gitignore`d. Each is its own git clone with its
own history; the `rex-wt-*` branches inside them preserve every run's
generated test content.

## Bundled skill: `test-quality`

This repo ships the [`test-quality`](.claude/skills/test-quality/) Claude Code
skill under `.claude/skills/`, so a clone is self-contained and the skill is
auto-discovered when you open the repo in Claude Code. It is the canonical,
cross-language (Python / JS-TS / Go) quality scorer, and the benchmark's rubric
is its Python instantiation — the two share the **same axis taxonomy**
(A.1–A.6 anti-fragility, B.1–B.3 rigor, C.1–C.2 mocking, D.1–D.3 reuse,
E.1–E.3 correctness, F.1–F.2 coverage floor):

- `references/scorecard.md` — the multi-axis scorecard + the "did I improve?"
  gate and iterate-to-plateau stop condition.
- `references/quality-contract.md` — the anti-fragility rules with examples.
- `scripts/score.py` — the per-language scorer (auto-counts A.1/A.2/A.4/A.5/
  B.1/C.1/C.2/D.1/D.2).

The relationship to the benchmark's own tooling:

- `prompts/run-2/quality_scorecard.md` is the **Python-specific instantiation**
  of the skill's `references/scorecard.md` — same axes, repo-specific examples.
- `scripts/score_run2.py` is a **benchmark-specific recompute** of just the
  auto-countable axes across the 9 worktrees + 3 baselines (so it can score
  every arm uniformly). It is *not* the skill's general scorer.

The skill is the general tool you'd apply to any suite; `score_run2.py` is this
experiment's instrument. The bundled copy is byte-identical to its upstream;
its redistribution license is TBD.

## Hermicity notes for the next session

- The shared `<repo>/base/.venv` is sufficient for all 9 worktrees.
  Sessions should NOT run `pip install -e .` from inside worktrees
  (Run 1 vulnerability: it clobbers the shared venv's editable
  install). The Run 2 prompts encode this constraint.
- The `requests/base/.venv` editable install was clobbered to
  `wt-iter20/` during Run 1; reset to `base/` on 2026-05-28. If
  Run 2 sessions also clobber it, fix with:
  `requests/base/.venv/bin/pip install -e requests/base --no-deps`.
- The aggregator script's src-prefix filter handled only relative
  paths; coverage JSONs store absolute keys when the package resolves
  via an editable install. **Fixed** — it now matches on a normalized
  path segment and is parameterized by `--run N`. `scripts/verify_run.sh`
  remains authoritative for per-worktree verification.

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
