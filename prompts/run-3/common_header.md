# Benchmark session — {REPO} / {POLICY} (Run 3)

You are running ONE arm of an iterative LLM test-generation benchmark
on the open-source repo `{REPO}` ({LANG}). You are in a dedicated git
worktree created specifically for this run. **Run 3 extends the
benchmark from Python to JS/TS and Go** — the question is whether
scorecard-anchored prompting beats human baselines in these languages
the way it did in Python (Run 2: 9/9).

## The goal

**Produce a test suite that beats the baseline's on the quality
scorecard** (see `quality_scorecard.md`) — NOT a suite that hits a
coverage number. The scorecard is computed by the bundled
`test-quality` scorer; you can run it on yourself at any time. Coverage
is only a non-regression sanity check (does your new code execute).

## Paths

- **Worktree (your CWD):** `{WORKTREE}`
- **Baseline clone (reference; do NOT modify):** `{BASE}`
- **Source under test:** {SOURCE_DESC}
- **Tests to delete + regenerate:** `{TESTS_DIR}` (inside the worktree)
- **Metrics output:** `.rex_metrics/` (create it inside this worktree)

## Environment — dependencies are already installed; do NOT reinstall

{ENV_NOTE}

**Do NOT run a fresh dependency install, upgrade, or `git clean` that
would remove the installed dependencies.** They are wired up for you.

## How to run the suite

```bash
cd {WORKTREE}
{RUN_CMD}
```

A run is GREEN when every test passes. **A suite that does not run
green is not a result** — getting to green is the first obligation of
every policy below.

## How to score yourself (this is the benchmark metric)

The scorer auto-counts the countable axes and prints a head-to-head
Win/Loss/Tie tally against the baseline:

```bash
{SCORE_CMD}
```

Run it against the baseline ONCE at the start to capture your target,
and again after each iteration to see where you stand. Reading the
scorer's *aggregate counts* off the baseline is allowed (it is
grep/wc, not test content) — see the hard constraint below.

## Hard constraints (Run-1/2 lessons — do not violate)

1. **Do not recover the deleted tests from git.** You will delete and
   commit the removal of `{TESTS_DIR}`. After that, treat those tests
   as if they never existed: no `git show`, `git log -p`, `git diff`,
   `git restore --source`, reflog, or stash to surface them. The
   benchmark measures *generation*, not restoration. (Run 1's
   `httpx/iter20` restored baseline tests via `git show` and was
   recorded as a verification failure, not a result.)
2. **Do not read the baseline's test files.** They are the answer key.
   You MAY read the baseline *source* for structure, and you MAY run
   the scorer (`{SCORE_CMD}`) against the baseline test dir for its
   aggregate axis counts — those are signals, not content. You may NOT
   open, cat, grep-for-content, or summarize individual baseline test
   bodies.
3. **Get the suite green.** Do not report a suite with failing/erroring
   tests as a finished result; either fix it or (per policy) record the
   failure honestly and stop.
4. **No hand mocks of the unit under test.** Use the framework
   primitives below, not ad-hoc stubs/spies of the code you're testing.

## Framework-intended test primitives

`{REPO}`'s baseline uses these — they are the right tools and the
scorer rewards them (C.2, not the C.1 penalty). Prefer them:

{FRAMEWORK_PRIMITIVES}
