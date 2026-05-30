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
