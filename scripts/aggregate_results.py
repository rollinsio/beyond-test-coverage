#!/usr/bin/env python3
"""Aggregate coverage results across the three Python worktrees per repo.

For each ``<repo>/<wt-prefix><policy>``, finds the *final* coverage JSON the
spawned session produced (preferring ``generated_coverage.json`` for one-shot,
``iter_N/coverage.json`` with the highest N otherwise) and computes:

- line/branch coverage on the src package only
- delta vs ``base/.rex_metrics/baseline_coverage.json``
- test LOC and mock-line count
- per-iteration history (where available)

Writes ``results-<experiment>.{json,md}`` under the benchmark root, where
``<experiment>`` is one of the Python experiments below.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REPOS = {
    "itsdangerous": {"src_prefix": "src/itsdangerous", "tests_dir": "tests"},
    "httpx":        {"src_prefix": "httpx",            "tests_dir": "tests"},
    "requests":     {"src_prefix": "src/requests",     "tests_dir": "tests"},
}
POLICIES = ("oneshot", "iter2", "iter20")

# The Python experiments this aggregator covers, mapped to the (git-ignored,
# not-redistributed) on-disk worktree prefix each one's sessions wrote into.
# The prefixes are a historical filesystem fact; the experiment names are the
# interface. The cross-language experiment uses score_cross_language.py instead
# (different repos, multi-language scorer).
EXPERIMENTS = {
    "coverage": "wt-",      # coverage-driven control (Python)
    "quality":  "wt-r2-",   # quality-driven (Python)
    "ablation": "wt-r2b-",  # Opus 4.7 + quality prompts; isolates prompt vs model
}

# Mock-LOC split (Finding 6 / quality_contract rule 10): distinguish real
# mocking (a quality concern, drive toward 0) from the framework's intended
# real-I/O primitives (legitimate; reported for context only).
# `patch(` guarded by a lookbehind so `mocker.patch` isn't double-counted; the
# old trailing \b dropped patch('str')/@patch/Mock() (real-mock undercount).
MOCK_REAL_RE = re.compile(r"\bMagicMock\b|\bMock\(|(?<![.\w])patch\(|\bmocker\b|\bunittest\.mock\b")
MOCK_FRAMEWORK_RE = re.compile(
    r"\b(MockTransport|WSGITransport|ASGITransport|monkeypatch|httpbin)\b"
)
TEST_SEGMENTS = ("tests", "test")

# Sessions were inconsistent about the per-iteration coverage filename: most
# wrote ``coverage.json``; httpx/iter2 wrote ``cov.json``. Accept either so one
# session's naming quirk doesn't silently drop a real data point.
COV_NAMES = ("coverage.json", "cov.json")


def _norm(fname: str) -> str:
    """Normalize a coverage-JSON file key to a leading-slash forward-slash path.

    Coverage JSONs store *either* relative keys (``src/itsdangerous/x.py``,
    ``httpx/x.py``) or absolute keys (``/Users/.../base/src/itsdangerous/x.py``)
    depending on whether the package resolved via an editable install. Both
    must be matched the same way.
    """
    return "/" + fname.replace("\\", "/").lstrip("/")


def _matches_src(fname: str, src_prefix: str) -> bool:
    """True if a coverage key belongs to the source package, abs or rel."""
    return ("/" + src_prefix.strip("/") + "/") in _norm(fname)


def _is_test_file(fname: str) -> bool:
    norm = _norm(fname)
    return any(("/" + seg + "/") in norm for seg in TEST_SEGMENTS)


@dataclass
class CovSummary:
    files_counted: int = 0
    statements: int = 0
    missing_lines: int = 0
    branches: int = 0
    covered_branches: int = 0
    partial_branches: int = 0
    line_coverage_pct: float = 0.0
    branch_coverage_pct: float = 0.0


def src_only_summary(cov_json: Path, src_prefix: str) -> CovSummary:
    data = json.loads(cov_json.read_text())
    s = CovSummary()
    for fname, fdata in data.get("files", {}).items():
        if _is_test_file(fname):
            continue
        if not _matches_src(fname, src_prefix):
            continue
        fs = fdata["summary"]
        s.files_counted += 1
        s.statements += fs.get("num_statements", 0)
        s.missing_lines += fs.get("missing_lines", 0)
        s.branches += fs.get("num_branches", 0)
        s.covered_branches += fs.get("covered_branches", 0)
        s.partial_branches += fs.get("num_partial_branches", 0)
    if s.statements:
        s.line_coverage_pct = round(
            100.0 * (s.statements - s.missing_lines) / s.statements, 2
        )
    if s.branches:
        s.branch_coverage_pct = round(
            100.0 * s.covered_branches / s.branches, 2
        )
    return s


def _iter_cov(d: Path) -> Path | None:
    """First existing coverage JSON in an iter dir, tolerating name variants."""
    for name in COV_NAMES:
        p = d / name
        if p.exists():
            return p
    return None


def find_final_coverage(metrics_dir: Path) -> Path | None:
    # Prefer generated_coverage.json (one-shot policy).
    candidate = metrics_dir / "generated_coverage.json"
    if candidate.exists():
        return candidate
    # Else: highest-numbered iter_N/coverage.json
    iter_dirs = sorted(
        (p for p in metrics_dir.glob("iter_*") if p.is_dir()),
        key=lambda p: int(p.name.split("_")[1]) if p.name.split("_")[1].isdigit() else -1,
    )
    for d in reversed(iter_dirs):
        if d.name == "iter_0":
            continue  # iter_0 is "after-delete" baseline, ~0% by design
        cov = _iter_cov(d)
        if cov:
            return cov
    # Last-ditch: any *.json that looks like a coverage report
    for cov in metrics_dir.glob("*.json"):
        try:
            data = json.loads(cov.read_text())
            if "files" in data and "totals" in data:
                return cov
        except Exception:
            continue
    return None


def per_iteration_history(metrics_dir: Path, src_prefix: str) -> list[dict]:
    out = []
    iter_dirs = sorted(
        (p for p in metrics_dir.glob("iter_*") if p.is_dir()),
        key=lambda p: int(p.name.split("_")[1]) if p.name.split("_")[1].isdigit() else -1,
    )
    for d in iter_dirs:
        cov = _iter_cov(d)
        if not cov:
            continue
        n_part = d.name.split("_")[1]
        if not n_part.isdigit():
            continue
        n = int(n_part)
        s = src_only_summary(cov, src_prefix)
        out.append(
            {
                "iter": n,
                "line_pct": s.line_coverage_pct,
                "branch_pct": s.branch_coverage_pct,
                "statements": s.statements,
            }
        )
    return out


def test_loc_and_mock(tests_dir: Path) -> tuple[int, int, int]:
    """Return (test_loc, mock_real_loc, mock_framework_loc)."""
    if not tests_dir.exists():
        return 0, 0, 0
    test_loc = 0
    mock_real = 0
    mock_framework = 0
    for path in tests_dir.rglob("*.py"):
        try:
            text = path.read_text()
        except Exception:
            continue
        for line in text.splitlines():
            test_loc += 1
            if MOCK_REAL_RE.search(line):
                mock_real += 1
            if MOCK_FRAMEWORK_RE.search(line):
                mock_framework += 1
    return test_loc, mock_real, mock_framework


@dataclass
class WorktreeResult:
    repo: str
    policy: str
    has_metrics: bool = False
    baseline_line_pct: float = 0.0
    baseline_branch_pct: float = 0.0
    final_line_pct: float = 0.0
    final_branch_pct: float = 0.0
    line_delta_pct: float = 0.0
    branch_delta_pct: float = 0.0
    test_loc: int = 0
    mock_real_loc: int = 0
    mock_framework_loc: int = 0
    mock_real_ratio: float = 0.0
    iterations: list[dict] = field(default_factory=list)
    summary_md_path: str | None = None
    final_cov_path: str | None = None


def compute_one(repo: str, policy: str, wt_prefix: str) -> WorktreeResult:
    repo_meta = REPOS[repo]
    wt = ROOT / repo / f"{wt_prefix}{policy}"
    metrics_dir = wt / ".rex_metrics"
    tests_dir = wt / repo_meta["tests_dir"]
    res = WorktreeResult(repo=repo, policy=policy)

    base_json = ROOT / repo / "base" / ".rex_metrics" / "baseline_coverage.json"
    if base_json.exists():
        b = src_only_summary(base_json, repo_meta["src_prefix"])
        res.baseline_line_pct = b.line_coverage_pct
        res.baseline_branch_pct = b.branch_coverage_pct

    if not metrics_dir.exists():
        return res

    final = find_final_coverage(metrics_dir)
    if final:
        s = src_only_summary(final, repo_meta["src_prefix"])
        res.has_metrics = True
        res.final_line_pct = s.line_coverage_pct
        res.final_branch_pct = s.branch_coverage_pct
        res.line_delta_pct = round(s.line_coverage_pct - res.baseline_line_pct, 2)
        res.branch_delta_pct = round(s.branch_coverage_pct - res.baseline_branch_pct, 2)
        res.final_cov_path = str(final.relative_to(ROOT))

    res.test_loc, res.mock_real_loc, res.mock_framework_loc = test_loc_and_mock(tests_dir)
    if res.test_loc:
        res.mock_real_ratio = round(res.mock_real_loc / res.test_loc, 4)

    res.iterations = per_iteration_history(metrics_dir, repo_meta["src_prefix"])

    summary = metrics_dir / "SUMMARY.md"
    if summary.exists():
        res.summary_md_path = str(summary.relative_to(ROOT))

    return res


def render_markdown(results: list[WorktreeResult]) -> str:
    lines = []
    lines.append("# Benchmark results — Section 4 aggregation")
    lines.append("")
    lines.append(
        "| Repo | Policy | has? | baseline line | final line | Δ line | baseline branch | final branch | Δ branch | test LOC | mock_real | mock_fw | mock_real ratio | iters |"
    )
    lines.append(
        "|------|--------|:----:|--------------:|-----------:|-------:|----------------:|-------------:|---------:|---------:|----------:|--------:|----------------:|------:|"
    )
    for r in results:
        lines.append(
            "| {repo} | {policy} | {has} | {bl:.2f} % | {fl:.2f} % | {dl:+.2f} | {bb:.2f} % | {fb:.2f} % | {db:+.2f} | {tl} | {mr_loc} | {mf} | {mrr:.3f} | {it} |".format(
                repo=r.repo,
                policy=r.policy,
                has="✓" if r.has_metrics else "—",
                bl=r.baseline_line_pct,
                fl=r.final_line_pct,
                dl=r.line_delta_pct,
                bb=r.baseline_branch_pct,
                fb=r.final_branch_pct,
                db=r.branch_delta_pct,
                tl=r.test_loc,
                mr_loc=r.mock_real_loc,
                mf=r.mock_framework_loc,
                mrr=r.mock_real_ratio,
                it=len(r.iterations) or "-",
            )
        )
    lines.append("")
    lines.append("## Per-iteration histories")
    lines.append("")
    for r in results:
        if not r.iterations:
            continue
        lines.append(f"### {r.repo} / {r.policy}")
        lines.append("")
        lines.append("| iter | line % | branch % | stmts |")
        lines.append("|----:|------:|--------:|------:|")
        for it in r.iterations:
            lines.append(
                f"| {it['iter']} | {it['line_pct']:.2f} | {it['branch_pct']:.2f} | {it['statements']} |"
            )
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--experiment", choices=list(EXPERIMENTS), default="quality",
        help="Which Python experiment to aggregate (sets the worktree prefix and "
             "the output filename). Default: quality.",
    )
    args = ap.parse_args()

    name = args.experiment
    wt_prefix = EXPERIMENTS[name]
    results = []
    for repo in REPOS:
        for policy in POLICIES:
            results.append(compute_one(repo, policy, wt_prefix))

    # Each experiment writes its own results-<experiment>.{json,md}, so they
    # never overwrite one another.
    out_json = ROOT / f"results-{name}.json"
    out_md = ROOT / f"results-{name}.md"
    out_json.write_text(json.dumps([asdict(r) for r in results], indent=2))
    out_md.write_text(render_markdown(results))
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    # also print the table to stdout
    print()
    print(render_markdown(results))
    return 0


if __name__ == "__main__":
    sys.exit(main())
