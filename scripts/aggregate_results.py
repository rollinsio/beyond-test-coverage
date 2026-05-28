#!/usr/bin/env python3
"""Aggregate Section 4 results across all 9 worktrees.

For each ``<repo>/wt-<policy>``, finds the *final* coverage JSON the spawned
session produced (preferring ``generated_coverage.json`` for one-shot,
``iter_N/coverage.json`` with the highest N otherwise) and computes:

- line/branch coverage on the src package only
- delta vs ``base/.rex_metrics/baseline_coverage.json``
- test LOC and mock-line count
- per-iteration history (where available)

Writes ``results.json`` and a Markdown table to ``results.md`` under the
benchmark root.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REPOS = {
    "itsdangerous": {"src_prefix": "src/itsdangerous", "tests_dir": "tests"},
    "httpx":        {"src_prefix": "httpx/",           "tests_dir": "tests"},
    "requests":     {"src_prefix": "src/requests",     "tests_dir": "tests"},
}
POLICIES = ("oneshot", "iter2", "iter20")

MOCK_RE = re.compile(r"\b(mock|patch|MagicMock|mocker|pytest-mock)\b", re.IGNORECASE)
TEST_PREFIXES = ("tests/", "test/")


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
        if any(fname.startswith(p) for p in TEST_PREFIXES):
            continue
        if not fname.startswith(src_prefix):
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
        cov = d / "coverage.json"
        if cov.exists():
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
        cov = d / "coverage.json"
        if not cov.exists():
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


def test_loc_and_mock(tests_dir: Path) -> tuple[int, int]:
    if not tests_dir.exists():
        return 0, 0
    test_loc = 0
    mock_lines = 0
    for path in tests_dir.rglob("*.py"):
        try:
            text = path.read_text()
        except Exception:
            continue
        for line in text.splitlines():
            test_loc += 1
            if MOCK_RE.search(line):
                mock_lines += 1
    return test_loc, mock_lines


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
    mock_lines: int = 0
    mock_ratio: float = 0.0
    iterations: list[dict] = field(default_factory=list)
    summary_md_path: str | None = None
    final_cov_path: str | None = None


def compute_one(repo: str, policy: str) -> WorktreeResult:
    repo_meta = REPOS[repo]
    wt = ROOT / repo / f"wt-{policy}"
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

    res.test_loc, res.mock_lines = test_loc_and_mock(tests_dir)
    if res.test_loc:
        res.mock_ratio = round(res.mock_lines / res.test_loc, 4)

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
        "| Repo | Policy | has? | baseline line | final line | Δ line | baseline branch | final branch | Δ branch | test LOC | mock lines | mock ratio | iters |"
    )
    lines.append(
        "|------|--------|:----:|--------------:|-----------:|-------:|----------------:|-------------:|---------:|---------:|-----------:|-----------:|------:|"
    )
    for r in results:
        lines.append(
            "| {repo} | {policy} | {has} | {bl:.2f} % | {fl:.2f} % | {dl:+.2f} | {bb:.2f} % | {fb:.2f} % | {db:+.2f} | {tl} | {ml} | {mr:.3f} | {it} |".format(
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
                ml=r.mock_lines,
                mr=r.mock_ratio,
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
    results = []
    for repo in REPOS:
        for policy in POLICIES:
            results.append(compute_one(repo, policy))

    out_json = ROOT / "results.json"
    out_md = ROOT / "results.md"
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
