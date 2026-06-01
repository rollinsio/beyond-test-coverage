#!/usr/bin/env python3
"""Prove the test suite can actually fail — a curated, fast mutation check.

Coverage tells you a line *ran*; it does not tell you a test would *catch* that
line breaking. This harness deliberately introduces a handful of representative
bugs into the benchmark's measurement tooling and asserts the suite goes RED for
each one. A mutation that survives (suite still green) is a real blind spot.

It's a cheap, deterministic cousin of full mutation testing (see
``mutmut``/``cosmic-ray``): instead of thousands of random mutants it runs a
small, hand-picked set that pins the load-bearing invariants — so it's fast
enough to run in CI as a "the tests can fail" guard.

Each mutation is applied to the working tree, the relevant tests run, then the
file is **always restored via ``git checkout``** (even on error). The harness
refuses to run if any target file has uncommitted changes, so it can never
clobber your work.

    python scripts/sabotage_check.py          # run all; exit 1 if any survives
    python scripts/sabotage_check.py -v        # also show pytest output per mutation

Exit code 0 = every mutation was caught. Non-zero = at least one survived (or a
mutation's anchor text drifted and needs updating).
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ".claude/skills"


@dataclass
class Mutation:
    name: str          # what invariant this breaks
    file: str          # path relative to repo root
    old: str           # exact text to replace (must be unique in the file)
    new: str           # the sabotage
    tests: list[str]   # pytest node ids / paths expected to catch it


# Curated mutations across the three core modules. Each should turn a specific
# test RED — if one survives, that behavior isn't actually pinned.
MUTATIONS: list[Mutation] = [
    Mutation(
        "score_quality: verdict() win/loss direction flipped",
        "scripts/score_quality.py",
        "better = (gen < base) if lower_better else (gen > base)",
        "better = (gen > base) if lower_better else (gen < base)",
        ["tests/test_score_quality.py::test_verdict"],
    ),
    Mutation(
        "score_quality: B.1 fixed-vector length threshold weakened (16 -> 1)",
        "scripts/score_quality.py",
        r"xX_\-.]{16,}",
        r"xX_\-.]{1,}",
        ["tests/test_score_quality.py::test_b1_requires_16_char_literal_boundary"],
    ),
    Mutation(
        "score_quality: C.1 mocker.patch lookbehind removed (double-counts)",
        "scripts/score_quality.py",
        r"(?<![.\w])patch\(",
        r"patch\(",
        ["tests/test_score_quality.py::test_c1_does_not_double_count_mocker_patch"],
    ),
    Mutation(
        "aggregate: line-coverage % uses + instead of - (sign error)",
        "scripts/aggregate_results.py",
        "100.0 * (s.statements - s.missing_lines) / s.statements",
        "100.0 * (s.statements + s.missing_lines) / s.statements",
        ["tests/test_aggregate_results.py::test_src_only_summary_counts_abs_and_rel_excludes_tests"],
    ),
    Mutation(
        "aggregate: render_markdown has-metrics marker inverted",
        "scripts/aggregate_results.py",
        'has="✓" if r.has_metrics else "—"',
        'has="—" if r.has_metrics else "✓"',
        ["tests/test_aggregate_results.py::test_render_markdown_table_row_and_iteration_history"],
    ),
    Mutation(
        "build_dashboard: fmt() drops the null sentinel",
        f"{SKILL}/results-dashboard/scripts/build_dashboard.py",
        'return "·"',
        'return ""',
        [f"{SKILL}/results-dashboard/tests/test_build_dashboard.py::test_fmt"],
    ),
    Mutation(
        "build_dashboard: better? badge always green",
        f"{SKILL}/results-dashboard/scripts/build_dashboard.py",
        '\'<span class="badge b-green">yes</span>\' if a.get("better")',
        '\'<span class="badge b-green">yes</span>\' if True',
        [f"{SKILL}/results-dashboard/tests/test_build_dashboard.py::test_build_html_not_better_badge_red"],
    ),
]


def _is_dirty(rel: str) -> bool:
    """True if the file has staged or unstaged changes."""
    for args in (["diff", "--quiet", "--", rel], ["diff", "--cached", "--quiet", "--", rel]):
        if subprocess.run(["git", *args], cwd=ROOT).returncode != 0:
            return True
    return False


def _run_tests(tests: list[str], verbose: bool) -> int:
    # Isolate bytecode in a fresh dir so a stale __pycache__ from a pre-mutation
    # source can never make a test pass (or fail) for the wrong reason.
    env = dict(os.environ, PYTHONPYCACHEPREFIX=tempfile.mkdtemp(prefix="sabotage_pyc_"))
    cmd = [sys.executable, "-m", "pytest", *tests, "-q", "-p", "no:cacheprovider", "-x"]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=not verbose, text=True, env=env)
    return proc.returncode


def _restore(rel: str) -> None:
    subprocess.run(["git", "checkout", "--", rel], cwd=ROOT, check=False)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-v", "--verbose", action="store_true", help="show pytest output per mutation")
    args = ap.parse_args()

    # Safety: never run against a dirty target file (we restore via git checkout).
    dirty = sorted({m.file for m in MUTATIONS if _is_dirty(m.file)})
    if dirty:
        print("Refusing to run — uncommitted changes in target file(s):", file=sys.stderr)
        for d in dirty:
            print(f"  {d}", file=sys.stderr)
        print("Commit or stash them first.", file=sys.stderr)
        return 2

    results = []
    for m in MUTATIONS:
        path = ROOT / m.file
        text = path.read_text()
        if m.old not in text:
            results.append((m.name, "STALE"))   # anchor drifted — harness needs updating
            continue
        try:
            path.write_text(text.replace(m.old, m.new, 1))
            caught = _run_tests(m.tests, args.verbose) != 0
        finally:
            _restore(m.file)
        results.append((m.name, "caught" if caught else "SURVIVED"))

    width = max(len(n) for n, _ in results)
    print("\nSabotage check — each mutation should make the suite RED:\n")
    bad = 0
    for name, status in results:
        if status == "caught":
            mark = "✓ caught"
        elif status == "STALE":
            mark, bad = "⚠ STALE anchor (update harness)", bad + 1
        else:
            mark, bad = "✗ SURVIVED (blind spot!)", bad + 1
        print(f"  {name.ljust(width)}   {mark}")

    total = len(results)
    print(f"\n{total - bad}/{total} mutations caught.")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
