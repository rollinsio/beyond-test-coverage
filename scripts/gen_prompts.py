#!/usr/bin/env python3
"""Materialize per-worktree prompt files for the benchmark.

Writes ``<worktree>/.rex_prompt.md`` and ``<worktree>/start.sh`` for each
(repo, policy) combination. ``start.sh`` activates the base venv and launches
Claude Code with the prompt as the initial user message.
"""

from __future__ import annotations

import os
import stat
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REPOS = {
    "itsdangerous": {
        "package": "itsdangerous",
        "source_dir": "src/itsdangerous",
        "tests_dir": "tests",
        "pytest_extra": "",
        "baseline_line_pct": 97.65,
        "baseline_branch_pct": 94.90,
        "deps": "Already installed in the base venv: pytest, freezegun, coverage, mutmut, and itsdangerous via `pip install -e .`.",
    },
    "httpx": {
        "package": "httpx",
        "source_dir": "httpx",
        "tests_dir": "tests",
        "pytest_extra": "-p no:unraisableexception",
        "baseline_line_pct": 100.00,
        "baseline_branch_pct": 97.27,
        "deps": "Already installed in the base venv via `pip install -r requirements.txt` (which `-e .[brotli,cli,http2,socks,zstd]` and adds pytest, coverage, trio, trustme, etc).",
    },
    "requests": {
        "package": "requests",
        "source_dir": "src/requests",
        "tests_dir": "tests",
        "pytest_extra": "",
        "baseline_line_pct": 87.86,
        "baseline_branch_pct": 79.48,
        "deps": "Already installed in the base venv via `pip install -r requirements-dev.txt` (which installs `-e .[socks]`, pytest, pytest-httpbin, trustme, etc).",
    },
}

POLICIES = ("oneshot", "iter2", "iter20")


def shared_header(repo: str, policy: str) -> str:
    meta = REPOS[repo]
    worktree = ROOT / repo / f"wt-{policy}"
    base = ROOT / repo / "base"
    return textwrap.dedent(
        f"""\
        # Benchmark session — {repo} / {policy}

        You are running ONE arm of an LLM test-generation benchmark on the
        open-source repo `{repo}`. You are in a dedicated git worktree.

        ## Paths

        - **Worktree (your CWD):** `{worktree}`
        - **Base clone (reference; do not modify):** `{base}`
        - **Source package:** `{meta['source_dir']}/` (importable as `{meta['package']}`)
        - **Tests directory to delete + regenerate:** `{meta['tests_dir']}/`
        - **Metrics output:** `.rex_metrics/` (inside this worktree)
        - **Coverage config (shared with baseline):** `bench.coveragerc` — copy from `../base/bench.coveragerc`

        ## Environment

        Reuse the base venv — every dep you need is already installed there.
        Activate it once at the start of the session:

        ```bash
        cd {worktree}
        cp ../base/bench.coveragerc .
        . ../base/.venv/bin/activate
        mkdir -p .rex_metrics
        ```

        {meta['deps']}

        ## How to run pytest and coverage

        Always invoke pytest through coverage with the shared rcfile. The
        extra pytest flag (if any) is required for this repo:

        ```bash
        python -m coverage run --rcfile=bench.coveragerc -m pytest -q {meta['pytest_extra']}
        python -m coverage json --rcfile=bench.coveragerc -o .rex_metrics/<name>.json
        python -m coverage xml  --rcfile=bench.coveragerc -o .rex_metrics/<name>.xml
        python -m coverage report --rcfile=bench.coveragerc > .rex_metrics/<name>.txt
        ```

        ## Baseline (for context — measured from the unchanged repo)

        - Line coverage:   {meta['baseline_line_pct']:.2f} %
        - Branch coverage: {meta['baseline_branch_pct']:.2f} %

        These numbers come from `../base/.rex_metrics/baseline_coverage.json`.
        """
    )


ONESHOT_BODY = textwrap.dedent(
    """\
    ## Your task — ONE-SHOT policy

    You get exactly ONE generation pass. No repair iterations.

    1. Delete the entire `{tests_dir}/` directory and commit the deletion:
       ```bash
       git rm -r {tests_dir}
       git commit -m "Remove tests for benchmark (oneshot)"
       ```
    2. Confirm coverage drops to ~0 by running the suite again (empty test set).
       Save the result to `.rex_metrics/coverage_after_delete.{{json,xml,txt}}`.
    3. Read the source under `{source_dir}/`. In **one pass**, write a
       replacement unit test suite under `{tests_dir}/`. Aim for high
       behavioral coverage, prefer real I/O over mocks where reasonable.
       Mirror the existing test layout style if helpful.
    4. Run the suite ONCE with coverage. Save artifacts under
       `.rex_metrics/generated_coverage.{{json,xml,txt}}`.
    5. If any test fails, **do not iterate**. Record the failure in
       `.rex_metrics/SUMMARY.md` and stop.
    6. Commit the generated tests: `git add {tests_dir} && git commit -m "Generated tests (oneshot)"`.
    7. Write `.rex_metrics/SUMMARY.md` containing:
       - pass/fail count, wall-clock time, line %, branch %
       - delta vs baseline (line/branch)
       - test LOC and mock-line count (matches of `mock|patch|MagicMock|mocker`)
    """
)

ITER2_BODY = textwrap.dedent(
    """\
    ## Your task — ITER2 policy

    You get up to TWO iterations of: generate → run → fix → run.

    1. Delete the entire `{tests_dir}/` directory and commit:
       ```bash
       git rm -r {tests_dir}
       git commit -m "Remove tests for benchmark (iter2)"
       ```
    2. Save coverage-after-delete artifacts under `.rex_metrics/iter_0/`.
    3. **Iteration 1**: read source under `{source_dir}/`, write tests under
       `{tests_dir}/`, run coverage. Save outputs under `.rex_metrics/iter_1/`.
       Commit: `git add {tests_dir} && git commit -m "iter1 tests"`.
    4. **Iteration 2 (only if needed)**: examine failures + uncovered
       branches/lines from `iter_1/coverage.json`, then make targeted fixes
       and additions. Run coverage again into `.rex_metrics/iter_2/`.
       Commit: `git add {tests_dir} && git commit -m "iter2 tests"`.
    5. After at most 2 iterations, stop regardless of remaining failures.
    6. Write `.rex_metrics/SUMMARY.md` containing per-iteration:
       - pass/fail count, wall-clock seconds, line %, branch %
       - mock-line count
       And a final block with delta vs baseline (line/branch).
    """
)

ITER20_BODY = textwrap.dedent(
    """\
    ## Your task — ITER20 policy

    You may take UP TO 20 iterations to **beat the baseline coverage**.

    1. Delete the entire `{tests_dir}/` directory and commit:
       ```bash
       git rm -r {tests_dir}
       git commit -m "Remove tests for benchmark (iter20)"
       ```
    2. Iterate: each iteration ends with all tests passing AND a saved
       `.rex_metrics/iter_<n>/coverage.json`. Use the JSON to find missed
       branches/lines and target them in the next pass.
    3. Stop EARLY the moment you exceed BOTH the baseline line % and branch
       % (above). If after 20 iterations you still have not beaten the
       baseline, stop anyway.
    4. **Important caveats for this repo's baseline:**
       - If baseline line coverage is already 100 %, line cov cannot be
         beaten — succeed by exceeding branch coverage AND matching line.
       - Prefer behavioral assertions over implementation detail.
       - Avoid mocks unless absolutely unavoidable.
    5. After each iteration, commit: `git add {tests_dir} && git commit -m "iter<n>"`.
    6. Write `.rex_metrics/SUMMARY.md` with the per-iteration table
       (iter, time, pass/fail, line %, branch %, mock LOC) and a final
       block with delta vs baseline.
    """
)

BODIES = {"oneshot": ONESHOT_BODY, "iter2": ITER2_BODY, "iter20": ITER20_BODY}


def start_script(worktree: Path) -> str:
    return textwrap.dedent(
        f"""\
        #!/bin/bash
        set -euo pipefail
        cd "{worktree}"
        cp -n ../base/bench.coveragerc . 2>/dev/null || true
        # Don't pre-activate venv — the prompt instructs Claude to do so itself
        # so the actions are auditable in the transcript.
        exec claude --permission-mode auto --model claude-opus-4-7 "$(cat .rex_prompt.md)"
        """
    )


def main() -> None:
    written = []
    for repo in REPOS:
        for policy in POLICIES:
            wt = ROOT / repo / f"wt-{policy}"
            wt.mkdir(parents=True, exist_ok=True)
            prompt = shared_header(repo, policy) + BODIES[policy].format(
                tests_dir=REPOS[repo]["tests_dir"],
                source_dir=REPOS[repo]["source_dir"],
            )
            (wt / ".rex_prompt.md").write_text(prompt)
            start = wt / "start.sh"
            start.write_text(start_script(wt))
            start.chmod(start.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            written.append(str(wt))
    print("Wrote prompts + start.sh for:")
    for w in written:
        print(f"  {w}")


if __name__ == "__main__":
    main()
