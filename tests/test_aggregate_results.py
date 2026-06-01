"""Validation suite for scripts/aggregate_results.py — the coverage aggregator.

The headline regression here is the abs/rel path-matching fix: coverage JSONs
key files by *either* a relative path (``src/itsdangerous/x.py``) or an absolute
one (``/Users/.../base/src/itsdangerous/x.py``) depending on whether the package
resolved via an editable install. Both must be counted. An earlier version
silently reported 0.00% for the suites whose keys were absolute.
"""
import json

import pytest


# ── _matches_src: the abs/rel regression ────────────────────────────────────
@pytest.mark.parametrize("fname, prefix, expected", [
    ("src/itsdangerous/signer.py", "src/itsdangerous", True),               # relative key
    ("/Users/u/base/src/itsdangerous/signer.py", "src/itsdangerous", True),  # absolute key
    ("httpx/_models.py", "httpx", True),
    ("/abs/base/httpx/_models.py", "httpx", True),
    ("tests/test_signer.py", "httpx", False),       # not in src
    ("src/other/x.py", "src/itsdangerous", False),  # different package
])
def test_matches_src_handles_absolute_and_relative_keys(aggregate, fname, prefix, expected):
    assert aggregate._matches_src(fname, prefix) is expected


@pytest.mark.parametrize("fname, expected", [
    ("tests/test_x.py", True),
    ("a/tests/b/c.py", True),
    ("httpx/test/x.py", True),
    ("src/itsdangerous/signer.py", False),
    ("httpx/_models.py", False),
])
def test_is_test_file(aggregate, fname, expected):
    assert aggregate._is_test_file(fname) is expected


def test_norm_normalizes_separators_and_leading_slash(aggregate):
    assert aggregate._norm("a\\b/c.py") == "/a/b/c.py"
    assert aggregate._norm("/x/y.py") == "/x/y.py"


@pytest.mark.parametrize("experiment, prefix", [
    ("coverage", "wt-"), ("quality", "wt-r2-"), ("ablation", "wt-r2b-"),
])
def test_experiments_map_to_worktree_prefix(aggregate, experiment, prefix):
    assert aggregate.EXPERIMENTS[experiment] == prefix


# ── render_markdown: the table + per-iteration history rendering ─────────────
def test_render_markdown_table_row_and_iteration_history(aggregate):
    R = aggregate.WorktreeResult
    results = [
        R(repo="httpx", policy="oneshot", has_metrics=True,
          baseline_line_pct=100.0, final_line_pct=95.95, line_delta_pct=-4.05,
          baseline_branch_pct=97.27, final_branch_pct=92.77, branch_delta_pct=-4.50,
          test_loc=4147, mock_real_loc=0, mock_framework_loc=96, mock_real_ratio=0.0,
          iterations=[]),
        R(repo="itsdangerous", policy="iter2", has_metrics=True,
          baseline_line_pct=97.65, final_line_pct=100.0, line_delta_pct=2.35,
          test_loc=1185,
          iterations=[{"iter": 1, "line_pct": 50.0, "branch_pct": 40.0, "statements": 100},
                      {"iter": 2, "line_pct": 100.0, "branch_pct": 100.0, "statements": 120}]),
    ]
    md = aggregate.render_markdown(results)
    assert md.startswith("# Benchmark results")
    # the httpx row: has_metrics ✓, signed delta, framework-mock count surfaced
    assert "| httpx | oneshot | ✓ |" in md
    assert "95.95 %" in md and "-4.05" in md and "| 96 |" in md
    # per-iteration history only for the result that has iterations
    assert "### itsdangerous / iter2" in md
    assert "| 2 | 100.00 | 100.00 | 120 |" in md
    assert "### httpx / oneshot" not in md   # no iterations → no history block


def test_render_markdown_marks_absent_metrics_with_dash(aggregate):
    R = aggregate.WorktreeResult
    md = aggregate.render_markdown([R(repo="requests", policy="iter20", has_metrics=False)])
    assert "| requests | iter20 | — |" in md


# ── main(): end-to-end over a fake worktree (compute_one → render → write) ────
def _cov(stmts, missing, branches, covered, partial):
    return {"files": {"demo/m.py": {"summary": {
        "num_statements": stmts, "missing_lines": missing, "num_branches": branches,
        "covered_branches": covered, "num_partial_branches": partial}}}}


def test_main_aggregates_a_worktree_and_marks_absent(aggregate, tmp_path, monkeypatch):
    import json
    repo = tmp_path / "demo"
    (repo / "base" / ".rex_metrics").mkdir(parents=True)
    (repo / "base" / ".rex_metrics" / "baseline_coverage.json").write_text(
        json.dumps(_cov(10, 1, 4, 3, 1)))                 # baseline line = 90%
    wt = repo / "wt-r2-oneshot"
    (wt / ".rex_metrics").mkdir(parents=True)
    (wt / ".rex_metrics" / "generated_coverage.json").write_text(
        json.dumps(_cov(10, 0, 4, 4, 0)))                 # final line = 100%
    (wt / "tests").mkdir()
    (wt / "tests" / "t.py").write_text("def test_a():\n    assert 1 == 1\n")

    monkeypatch.setattr(aggregate, "ROOT", tmp_path)
    monkeypatch.setattr(aggregate, "REPOS", {"demo": {"src_prefix": "demo", "tests_dir": "tests"}})
    monkeypatch.setattr("sys.argv", ["aggregate_results.py", "--experiment", "quality"])

    assert aggregate.main() == 0

    rows = {(r["repo"], r["policy"]): r for r in json.loads((tmp_path / "results-quality.json").read_text())}
    one = rows[("demo", "oneshot")]
    assert one["has_metrics"] is True
    assert one["baseline_line_pct"] == 90.0
    assert one["final_line_pct"] == 100.0
    assert one["line_delta_pct"] == 10.0
    assert rows[("demo", "iter2")]["has_metrics"] is False   # no worktree → absent row
    assert (tmp_path / "results-quality.md").exists()


# ── _iter_cov: tolerate coverage.json vs cov.json ────────────────────────────
def test_iter_cov_prefers_coverage_json(aggregate, tmp_path):
    (tmp_path / "coverage.json").write_text("{}")
    (tmp_path / "cov.json").write_text("{}")
    assert aggregate._iter_cov(tmp_path).name == "coverage.json"


def test_iter_cov_falls_back_to_cov_json(aggregate, tmp_path):
    (tmp_path / "cov.json").write_text("{}")
    assert aggregate._iter_cov(tmp_path).name == "cov.json"


def test_iter_cov_none_when_absent(aggregate, tmp_path):
    assert aggregate._iter_cov(tmp_path) is None


# ── test_loc_and_mock: the real-vs-framework mock split (Finding 6) ──────────
def test_mock_loc_split_real_vs_framework(aggregate, tmp_path):
    (tmp_path / "test_x.py").write_text(
        "from unittest.mock import patch\n"   # mock_real (unittest.mock)
        "m = MagicMock()\n"                    # mock_real (MagicMock)
        "def test_a(monkeypatch):\n"           # mock_framework (monkeypatch)
        "    t = MockTransport(h)\n"           # mock_framework (MockTransport)
        "    assert True\n"                    # neither
    )
    loc, mock_real, mock_framework = aggregate.test_loc_and_mock(tmp_path)
    assert loc == 5
    assert mock_real == 2
    assert mock_framework == 2


# ── src_only_summary: end-to-end on a coverage-JSON fixture ──────────────────
def test_src_only_summary_counts_abs_and_rel_excludes_tests(aggregate, tmp_path):
    cov = {"files": {
        # absolute key (editable-install case) — the bug that reported 0.00%
        "/Users/u/base/src/itsdangerous/signer.py": {"summary": {
            "num_statements": 10, "missing_lines": 2,
            "num_branches": 4, "num_partial_branches": 1, "covered_branches": 3}},
        # relative key
        "src/itsdangerous/serializer.py": {"summary": {
            "num_statements": 20, "missing_lines": 0,
            "num_branches": 6, "num_partial_branches": 0, "covered_branches": 6}},
        # a test file — must be excluded from the source summary
        "tests/test_signer.py": {"summary": {
            "num_statements": 99, "missing_lines": 0,
            "num_branches": 0, "num_partial_branches": 0, "covered_branches": 0}},
    }}
    p = tmp_path / "coverage.json"
    p.write_text(json.dumps(cov))
    s = aggregate.src_only_summary(p, "src/itsdangerous")
    assert s.files_counted == 2          # both src files; test file excluded
    assert s.statements == 30
    assert s.missing_lines == 2
    assert s.line_coverage_pct == 93.33  # 100 * (30-2)/30
    assert s.branch_coverage_pct == 90.0  # 100 * 9/10
