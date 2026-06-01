"""Validation suite for the results-dashboard generator (scripts/build_dashboard.py).

Pins the data→HTML contract: hero counts, the per-axis Win/Tie/Loss
distribution, and the per-suite matrix (verdict marks, CSS classes, absent
rows, null values). Counts are hand-derived from each fixture, not recomputed
with the module's own helpers, so a wrong helper can't make its own test pass.

Run:  python -m pytest tests/ -q   (from the skill root)
"""
import importlib.util
import json
import re
from pathlib import Path

import pytest

# Load build_dashboard.py by path so the suite is independent of cwd / packaging.
_BUILD_PY = Path(__file__).resolve().parent.parent / "scripts" / "build_dashboard.py"
_spec = importlib.util.spec_from_file_location("build_dashboard", _BUILD_PY)
bd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bd)


def arm(repo, policy, axes=None, *, present=True, lang=None, better=None,
        wins=0, losses=0, ties=0):
    """Build one arm dict. ``axes`` is {key: (gen, base, verdict)}."""
    if not present:
        return {"repo": repo, "policy": policy, "present": False}
    return {
        "repo": repo, "policy": policy, "present": True, "lang": lang,
        "axes": {k: {"gen": g, "base": b, "verdict": v} for k, (g, b, v) in (axes or {}).items()},
        "wins": wins, "losses": losses, "ties": ties,
        "better": (wins > losses) if better is None else better,
    }


# ───────────────────────────── fmt() ─────────────────────────────
@pytest.mark.parametrize("value, expected", [
    (None, "·"),
    (3, "3"),
    (1941, "1941"),
    (3.0, "3"),          # floats use %g — a whole float prints without ".0"
    (0.179, "0.179"),
    (14.57, "14.57"),
    (0, "0"),
])
def test_fmt(value, expected):
    assert bd.fmt(value) == expected


# ─────────────────────────── short_axis() ───────────────────────
@pytest.mark.parametrize("key, expected", [
    ("A1_substring_match", "A1"),
    ("D2_param_ratio", "D2"),
    ("B1_fixed_vector", "B1"),
    ("plain", "plain"),       # no underscore → whole key
])
def test_short_axis(key, expected):
    assert bd.short_axis(key) == expected


# ─────────────────────────── axis_keys() ────────────────────────
def test_axis_keys_from_first_present_arm():
    arms = [
        arm("x", "oneshot", present=False),                       # skipped
        arm("x", "iter2", {"A1_substring_match": (0, 5, "WIN"),
                           "B1_fixed_vector": (3, 1, "WIN")}),
    ]
    assert bd.axis_keys(arms) == ["A1_substring_match", "B1_fixed_vector"]


def test_axis_keys_empty_when_no_present_arm():
    assert bd.axis_keys([arm("x", "oneshot", present=False)]) == []


# ───────────────────────── axis_distribution() ──────────────────
def test_axis_distribution_counts_per_verdict():
    keys = ["A1_substring_match", "B1_fixed_vector"]
    arms = [
        arm("a", "p1", {"A1_substring_match": (0, 5, "WIN"),
                        "B1_fixed_vector": (3, 1, "WIN")}),
        arm("a", "p2", {"A1_substring_match": (5, 5, "TIE"),
                        "B1_fixed_vector": (0, 4, "LOSS")}),
        arm("a", "p3", {"A1_substring_match": (2, 5, "WIN"),
                        "B1_fixed_vector": (None, None, "N/A")}),
        arm("a", "absent", present=False),   # excluded from the distribution
    ]
    dist = bd.axis_distribution(arms, keys)
    assert dist["A1_substring_match"] == {"WIN": 2, "TIE": 1, "LOSS": 0, "N/A": 0}
    assert dist["B1_fixed_vector"] == {"WIN": 1, "TIE": 0, "LOSS": 1, "N/A": 1}


def test_axis_distribution_unknown_verdict_falls_to_na():
    keys = ["A1_substring_match"]
    arms = [arm("a", "p1", {"A1_substring_match": (0, 1, "BOGUS")})]
    assert bd.axis_distribution(arms, keys)["A1_substring_match"]["N/A"] == 1


def test_axis_distribution_missing_axis_key_falls_to_na():
    # present arm whose axes dict lacks the requested key
    keys = ["A1_substring_match", "C1_mock_real"]
    arms = [arm("a", "p1", {"A1_substring_match": (0, 1, "WIN")})]
    dist = bd.axis_distribution(arms, keys)
    assert dist["C1_mock_real"]["N/A"] == 1


# ───────────────────────── build_html(): hero ───────────────────
def test_build_html_hero_overall_and_per_language():
    arms = [
        arm("express", "oneshot", {"A1_substring_match": (0, 5, "WIN")}, lang="js", wins=1, losses=0),
        arm("express", "iter2",   {"A1_substring_match": (5, 5, "TIE")}, lang="js", wins=0, losses=1),  # not better
        arm("chi", "oneshot",     {"A1_substring_match": (0, 5, "WIN")}, lang="go", wins=1, losses=0),
    ]
    html = bd.build_html(arms, "T", "sub", "src.json")
    # overall: 2 of 3 arms beat baseline (better == wins>losses)
    assert ">2<small>/3</small>" in html
    # per-language cards must pair the RIGHT label with the RIGHT count
    # (js: 1 of 2 better, go: 1 of 1) — not just contain the digits somewhere
    assert re.search(r'js arms</div><div class="big">1<small>/2</small>', html)
    assert re.search(r'go arms</div><div class="big">1<small>/1</small>', html)


# ──────────────────────── build_html(): matrix ──────────────────
def test_build_html_matrix_cells_and_verdict_classes():
    arms = [arm("express", "oneshot",
                {"A1_substring_match": (0, 25, "WIN"),
                 "B1_fixed_vector": (3, 28, "LOSS"),
                 "C1_mock_real": (0, 0, "TIE")},
                lang="js", wins=1, losses=1, ties=1)]
    html = bd.build_html(arms, "T", "", "src.json")
    assert "express / oneshot" in html
    assert 'class="cell-win"' in html and 'class="cell-loss"' in html and 'class="cell-tie"' in html
    # WIN cell shows gen then base+✓; LOSS shows ✗
    assert re.search(r'cell-win"?>0<span class="v">25✓', html)
    assert re.search(r'cell-loss"?>3<span class="v">28✗', html)
    # W/L/T tally + better badge (assert the rendered badge, not the CSS class def).
    # This arm is 1 win / 1 loss → NOT better → red badge.
    assert "1/1/1" in html
    assert 'b-red">no</span>' in html


def test_build_html_absent_arm_row():
    arms = [arm("express", "iter2", present=False)]
    html = bd.build_html(arms, "T", "", "src.json")
    assert "express / iter2" in html
    assert "absent" in html


def test_build_html_null_axis_value_renders_dot():
    arms = [arm("chi", "oneshot", {"A2_private_symbol": (None, None, "N/A")},
                lang="go", wins=0, losses=0, ties=0)]
    html = bd.build_html(arms, "T", "", "src.json")
    # the n-a cell renders the value as a dot
    assert 'class="cell-na">·' in html


def test_build_html_not_better_badge_red():
    arms = [arm("x", "oneshot", {"A1_substring_match": (5, 1, "LOSS")},
                wins=0, losses=1, better=False)]
    html = bd.build_html(arms, "T", "", "src.json")
    # the rendered red badge — NOT the always-present `.b-red` CSS rule
    assert 'b-red">no</span>' in html
    assert 'b-green">yes</span>' not in html


def test_build_html_escapes_title():
    html = bd.build_html([arm("x", "p", {"A1_substring_match": (0, 1, "WIN")})],
                         "<script>alert(1)</script>", "", "src.json")
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_build_html_chart_arrays_align_with_axes():
    # axis order is [A1, B1]; A1 wins twice, B1 wins zero times → win series [2, 0]
    arms = [
        arm("a", "p1", {"A1_substring_match": (0, 5, "WIN"), "B1_fixed_vector": (0, 4, "LOSS")}),
        arm("a", "p2", {"A1_substring_match": (2, 5, "WIN"), "B1_fixed_vector": (4, 4, "TIE")}),
    ]
    html = bd.build_html(arms, "T", "", "src.json")
    assert "[2, 0]" in html        # json.dumps of the win series across [A1, B1]


# ───────────────────────────── main() ───────────────────────────
def _write_scorecard(tmp_path, arms, baselines=None):
    p = tmp_path / "results-demo-scorecard.json"
    p.write_text(json.dumps({"baselines": baselines or {}, "arms": arms}))
    return p


def test_main_writes_html(tmp_path, monkeypatch, capsys):
    src = _write_scorecard(tmp_path, [
        arm("express", "oneshot", {"A1_substring_match": (0, 5, "WIN")}, lang="js", wins=1, losses=0),
        arm("express", "iter2", present=False),
    ])
    out = tmp_path / "out.html"
    monkeypatch.setattr("sys.argv", ["build_dashboard.py", str(src), "-o", str(out),
                                     "--title", "Demo", "--subtitle", "S"])
    rc = bd.main()
    assert rc == 0
    assert out.exists()
    html = out.read_text()
    assert "<title>Demo</title>" in html and "express / oneshot" in html
    # the stdout summary must agree with the data (1 present, 1 beat baseline)
    summary = capsys.readouterr().out
    assert "1 arms" in summary and "1 beat baseline" in summary


def test_main_default_output_path_next_to_input(tmp_path, monkeypatch):
    src = _write_scorecard(tmp_path, [arm("x", "p", {"A1_substring_match": (0, 1, "WIN")})])
    monkeypatch.setattr("sys.argv", ["build_dashboard.py", str(src)])
    bd.main()
    assert src.with_suffix(".html").exists()


def test_main_rejects_json_without_arms(tmp_path, monkeypatch):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"baselines": {}}))   # no 'arms'
    monkeypatch.setattr("sys.argv", ["build_dashboard.py", str(bad)])
    with pytest.raises(SystemExit):
        bd.main()
