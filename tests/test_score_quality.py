"""Validation suite for scripts/score_quality.py — the benchmark's independent
scorecard recompute. The quality-experiment headline (3/9 -> 8/9 -> 9/9) is
computed entirely by this module, so its counting must be pinned.

Fixed-vector expectations, hand-derived from each fixture. Known gaps are xfail.
"""
import pytest


def measure_py(score_quality, tmp_path, body):
    (tmp_path / "test_x.py").write_text(body)
    return score_quality.measure(tmp_path)


# A single fixture exercising every auto-counted axis with known counts.
SAMPLE = (
    "from itsdangerous.signer import _make_keys_list\n"          # A2: private import
    "import hmac\n"
    "@pytest.mark.parametrize('a', [1, 2])\n"                    # parametrize
    "def test_a():\n"                                            # test_def
    "    with pytest.raises(BadSignature, match='zlib'):\n"      # A1: match=
    "        f()\n"
    "    expected = hmac.new(b'k', b'v').digest()\n"             # A4: recomputed crypto
    "    assert sign(b'x') == b'aaaaaaaaaaaaaaaaaaaa'\n"         # B1: 20-char fixed vector
    "def test_b():\n"                                            # test_def
    "    assert 'x' in str(e) or 'y' in str(e)\n"               # A5 (+ A1 'in str(' x2)
)


def test_measure_counts_every_axis(score_quality, tmp_path):
    m = measure_py(score_quality, tmp_path, SAMPLE)
    assert m["A1_substring_match"] == 3      # match= (1) + 'in str(' twice (2)
    assert m["A2_private_symbol"] == 1
    assert m["A4_recomputed_crypto"] == 1    # overlapping hmac./expected=hmac -> 1 match
    assert m["A5_or_joined"] == 1
    assert m["C1_mock_real"] == 0
    assert m["B1_fixed_vector"] == 1
    assert m["parametrize"] == 1
    assert m["test_count"] == 2
    assert m["D2_param_ratio"] == 0.5


@pytest.mark.parametrize("axis, gen, base, expected", [
    ("A1_substring_match", 1, 4, "WIN"),
    ("A1_substring_match", 4, 1, "LOSS"),
    ("A1_substring_match", 2, 2, "TIE"),
    ("B1_fixed_vector", 5, 2, "WIN"),     # higher-better
    ("B1_fixed_vector", 2, 5, "LOSS"),
    ("D2_param_ratio", 0.3, 0.1, "WIN"),  # higher-better
    ("D1_loc_per_test", 8.0, 12.0, "WIN"),  # lower-better
])
def test_verdict(score_quality, axis, gen, base, expected):
    assert score_quality.verdict(axis, gen, base) == expected


def test_b1_requires_16_char_literal_boundary(score_quality, tmp_path):
    body = (
        "def test_a():\n"
        "    assert f(x) == b'aaaaaaaaaaaaaaaa'\n"   # 16 chars -> match
        "    assert g(y) == b'bbbbbbbbbbbbbbb'\n"    # 15 chars -> no
    )
    assert measure_py(score_quality, tmp_path, body)["B1_fixed_vector"] == 1


def test_c1_counts_patch_with_string_literal(score_quality, tmp_path):
    # Regression for the trailing-\b bug: patch('literal') must count.
    body = "def test_a():\n    with patch('pkg.mod.func'):\n        pass\n"
    assert measure_py(score_quality, tmp_path, body)["C1_mock_real"] == 1


def test_c1_does_not_double_count_mocker_patch(score_quality, tmp_path):
    body = "def test_a():\n    mocker.patch('pkg.f')\n"
    assert measure_py(score_quality, tmp_path, body)["C1_mock_real"] == 1


def test_empty_dir_is_zeros(score_quality, tmp_path):
    m = score_quality.measure(tmp_path)
    assert m["test_count"] == 0
    assert m["D2_param_ratio"] == 0.0
    assert m["A1_substring_match"] == 0
