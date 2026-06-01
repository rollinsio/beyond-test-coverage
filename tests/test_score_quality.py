"""Validation suite for scripts/score_quality.py — the benchmark's independent
scorecard recompute. The quality-experiment headline (3/9 -> 8/9 -> 9/9) is
computed entirely by this module, so its counting must be pinned.

Fixed-vector expectations, hand-derived from each fixture. Known gaps are xfail.
"""
import json

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
    # pin test_loc accumulation and the D1 = loc/test ratio (10 lines, 2 tests)
    assert m["test_loc"] == 10
    assert m["D1_loc_per_test"] == 5.0


@pytest.mark.parametrize("axis, gen, base, expected", [
    ("A1_substring_match", 1, 4, "WIN"),
    ("A1_substring_match", 4, 1, "LOSS"),
    ("A1_substring_match", 2, 2, "TIE"),
    ("B1_fixed_vector", 5, 2, "WIN"),     # higher-better
    ("B1_fixed_vector", 2, 5, "LOSS"),
    ("D2_param_ratio", 0.3, 0.1, "WIN"),  # higher-better
    ("D1_loc_per_test", 8.0, 12.0, "WIN"),  # lower-better
    # pin the lower-better direction of every remaining anti-fragility axis
    # (otherwise flipping its SCORED entry to higher-better goes uncaught)
    ("A2_private_symbol", 0, 3, "WIN"),    ("A2_private_symbol", 3, 0, "LOSS"),
    ("A4_recomputed_crypto", 0, 2, "WIN"), ("A4_recomputed_crypto", 2, 0, "LOSS"),
    ("A5_or_joined", 0, 1, "WIN"),         ("A5_or_joined", 1, 0, "LOSS"),
    ("C1_mock_real", 0, 4, "WIN"),         ("C1_mock_real", 4, 0, "LOSS"),
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


def test_measure_sums_across_multiple_files(score_quality, tmp_path):
    # measure() must AGGREGATE loc, test_count, AND per-pattern counts over every
    # *.py in the dir — not stop at the first file or overwrite counts per file.
    (tmp_path / "test_a.py").write_text(
        "def test_a():\n    assert 'x' in str(e)\n")                                   # 2 loc, 1 test, A1=1
    (tmp_path / "test_b.py").write_text(
        "def test_b():\n    assert 'y' in str(e)\ndef test_c():\n    assert 1 == 1\n")  # 4 loc, 2 tests, A1=1
    m = score_quality.measure(tmp_path)
    assert m["test_count"] == 3          # 1 + 2
    assert m["test_loc"] == 6            # 2 + 4
    assert m["A1_substring_match"] == 2  # 1 + 1 — pattern counts sum across files


# ── main(): end-to-end over fake worktrees (measure → verdict → render → write) ─
def test_main_scores_present_arm_and_marks_absent(score_quality, tmp_path, monkeypatch):
    # baseline carries a substring-match assert (A1=1); the generated oneshot
    # suite drops it for a fixed vector (A1=0) → A1 is a WIN (lower-better).
    base = tmp_path / "demo" / "base" / "tests"
    base.mkdir(parents=True)
    (base / "t.py").write_text(
        "import pytest\n"
        "def test_a():\n"
        "    with pytest.raises(ValueError, match='boom'):\n"
        "        f()\n")
    gen = tmp_path / "demo" / "wt-r2-oneshot" / "tests"   # only the oneshot arm exists
    gen.mkdir(parents=True)
    (gen / "t.py").write_text(
        "def test_a():\n"
        "    assert sign(b'x') == b'aaaaaaaaaaaaaaaaaaaa'\n")

    monkeypatch.setattr(score_quality, "ROOT", tmp_path)
    monkeypatch.setattr(score_quality, "REPOS", {"demo": "tests"})
    monkeypatch.setattr("sys.argv", ["score_quality.py", "--experiment", "quality"])

    assert score_quality.main() == 0

    data = json.loads((tmp_path / "results-quality-scorecard.json").read_text())
    arms = {(a["repo"], a["policy"]): a for a in data["arms"]}
    one = arms[("demo", "oneshot")]
    assert one["present"] is True
    assert arms[("demo", "iter2")]["present"] is False     # no worktree on disk
    assert arms[("demo", "iter20")]["present"] is False
    assert one["axes"]["A1_substring_match"]["verdict"] == "WIN"
    assert data["baselines"]["demo"]["A1_substring_match"] == 1
    # pin the W/L/T tally and the better flag: gen wins A1 (0<1), B1 (1>0),
    # D1 (2.0<4.0); ties the other five axes; loses none.
    assert one["wins"] == 3
    assert one["losses"] == 0
    assert one["ties"] == 5
    assert one["better"] is True

    md = (tmp_path / "results-quality-scorecard.md").read_text()
    assert md.startswith("# quality — independent scorecard recompute")
    assert "demo/oneshot" in md
    assert "demo/iter2" in md and "_absent_" in md
    assert "demo/iter20" in md   # the LAST row must render too (absent branch continues, not breaks)


def test_main_experiment_flag_picks_worktree_prefix(score_quality, tmp_path, monkeypatch):
    # --experiment ablation must look under the wt-r2b- prefix, not wt-r2-
    base = tmp_path / "demo" / "base" / "tests"; base.mkdir(parents=True)
    (base / "t.py").write_text("def test_a():\n    assert 1 == 1\n")
    gen = tmp_path / "demo" / "wt-r2b-oneshot" / "tests"; gen.mkdir(parents=True)
    (gen / "t.py").write_text("def test_a():\n    assert 1 == 1\n")
    monkeypatch.setattr(score_quality, "ROOT", tmp_path)
    monkeypatch.setattr(score_quality, "REPOS", {"demo": "tests"})
    monkeypatch.setattr("sys.argv", ["score_quality.py", "--experiment", "ablation"])
    assert score_quality.main() == 0
    data = json.loads((tmp_path / "results-ablation-scorecard.json").read_text())
    arms = {(a["repo"], a["policy"]): a for a in data["arms"]}
    assert arms[("demo", "oneshot")]["present"] is True    # found under wt-r2b-


def test_main_treats_existing_but_empty_worktree_as_absent(score_quality, tmp_path, monkeypatch):
    # a worktree dir that exists but holds no *.py is NOT a real generated suite
    base = tmp_path / "demo" / "base" / "tests"; base.mkdir(parents=True)
    (base / "t.py").write_text("def test_a():\n    assert 1 == 1\n")
    (tmp_path / "demo" / "wt-r2-oneshot" / "tests").mkdir(parents=True)   # exists, but empty
    monkeypatch.setattr(score_quality, "ROOT", tmp_path)
    monkeypatch.setattr(score_quality, "REPOS", {"demo": "tests"})
    monkeypatch.setattr("sys.argv", ["score_quality.py", "--experiment", "quality"])
    assert score_quality.main() == 0
    data = json.loads((tmp_path / "results-quality-scorecard.json").read_text())
    arms = {(a["repo"], a["policy"]): a for a in data["arms"]}
    assert arms[("demo", "oneshot")]["present"] is False


def test_main_accumulates_multiple_losses(score_quality, tmp_path, monkeypatch):
    # gen is WORSE than baseline on several axes — the loss counter must
    # ACCUMULATE (l += ...), not be overwritten or decremented.
    base = tmp_path / "demo" / "base" / "tests"; base.mkdir(parents=True)
    (base / "t.py").write_text("def test_a():\n    assert ok\n")        # clean: A1=0, A2=0
    gen = tmp_path / "demo" / "wt-r2-oneshot" / "tests"; gen.mkdir(parents=True)
    (gen / "t.py").write_text(
        "def test_a():\n"
        "    with pytest.raises(E, match='x'):\n"   # A1 +1 (match=)
        "        obj._priv()\n"                       # A2 +1 (private call)
        "    assert 'y' in str(e)\n")                 # A1 +1 (in str(
    monkeypatch.setattr(score_quality, "ROOT", tmp_path)
    monkeypatch.setattr(score_quality, "REPOS", {"demo": "tests"})
    monkeypatch.setattr("sys.argv", ["score_quality.py", "--experiment", "quality"])
    assert score_quality.main() == 0
    one = [a for a in json.loads((tmp_path / "results-quality-scorecard.json").read_text())["arms"]
           if a["policy"] == "oneshot"][0]
    assert one["losses"] >= 2          # A1 and A2 both regress vs baseline
    assert one["better"] is False
