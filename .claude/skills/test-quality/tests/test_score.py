"""Validation suite for the test-quality scorer (scripts/score.py).

These tests dogfood the rubric the scorer enforces:
  * Fixed-vector expectations — every count is hand-derived from the fixture
    by reading it as a human would, NOT recomputed with the scorer's own regex
    (that would be tautological and couldn't catch a wrong regex).
  * Boundary cases (the >=12-char B.1 threshold, etc.).
  * A named regression test for every bug found during Run-3 validation prep.
  * Known gaps are `xfail` (assert the *desired* behaviour, stay visible) rather
    than asserting the buggy number — so they flip to XPASS when fixed.

Run:  python -m pytest tests/ -q   (from the skill root)
"""
import importlib.util
from pathlib import Path

import pytest

# Load score.py by path so the suite is independent of cwd / packaging.
_SCORE_PY = Path(__file__).resolve().parent.parent / "scripts" / "score.py"
_spec = importlib.util.spec_from_file_location("score", _SCORE_PY)
score = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(score)


def write(tmp_path, name, body):
    """Materialize a fixture file (creating parent dirs) and return its path."""
    p = tmp_path / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body)
    return p


# ───────────────────────── verdict() — the scoring logic ─────────────────────
@pytest.mark.parametrize("axis, gen, base, expected", [
    # A.1 is lower-better: fewer than baseline wins.
    ("A1_substring_match", 2, 5, "WIN"),
    ("A1_substring_match", 5, 2, "LOSS"),
    ("A1_substring_match", 3, 3, "TIE"),
    # B.1 is higher-better: more than baseline wins.
    ("B1_fixed_vector", 9, 4, "WIN"),
    ("B1_fixed_vector", 4, 9, "LOSS"),
    ("B1_fixed_vector", 7, 7, "TIE"),
    # ratio axes carry their direction too
    ("D2_param_ratio", 0.30, 0.10, "WIN"),
    ("D2_param_ratio", 0.10, 0.30, "LOSS"),
    ("D1_loc_per_test", 8.0, 12.0, "WIN"),
    ("D1_loc_per_test", 12.0, 8.0, "LOSS"),
    # None on either side (e.g. Go A.2) is uncountable, not a win or loss.
    ("A2_private_symbol", None, 5, "N/A"),
    ("A2_private_symbol", 5, None, "N/A"),
    ("A2_private_symbol", None, None, "N/A"),
])
def test_verdict(axis, gen, base, expected):
    assert score.verdict(axis, gen, base) == expected


def test_scored_directions_are_pinned():
    # Direction is the whole ball game; pin it so a flip can't pass silently.
    assert score.SCORED["A1_substring_match"] is True      # lower better
    assert score.SCORED["A2_private_symbol"] is True
    assert score.SCORED["A4_recomputed_crypto"] is True
    assert score.SCORED["A5_or_joined"] is True
    assert score.SCORED["C1_mock_real"] is True
    assert score.SCORED["B1_fixed_vector"] is False        # higher better
    assert score.SCORED["D1_loc_per_test"] is True
    assert score.SCORED["D2_param_ratio"] is False
    assert "C2_mock_framework" not in score.SCORED          # reported, not scored


# ───────────────────────── detect_lang ──────────────────────────────────────
def test_detect_lang_js(tmp_path):
    write(tmp_path, "a.test.ts", "it('x', () => {})\n")
    assert score.detect_lang(tmp_path) == "js"


def test_detect_lang_python(tmp_path):
    write(tmp_path, "test_x.py", "def test_a():\n    assert True\n")
    assert score.detect_lang(tmp_path) == "python"


def test_detect_lang_go(tmp_path):
    write(tmp_path, "x_test.go", "func TestA(t *testing.T) {}\n")
    assert score.detect_lang(tmp_path) == "go"


# ───────────────────────── JS test-file detection (regressions) ─────────────
def test_js_detects_plain_js_under_test_dir_EXPRESS_regression(tmp_path):
    # Mocha/express convention: test/<name>.js with NO `.test.` suffix.
    # Pre-fix this scored files=0; the dir-membership rule must catch them.
    write(tmp_path, "test/app.js", "it('a', () => {})\n")
    write(tmp_path, "test/Router.js", "it('b', () => {})\n")
    write(tmp_path, "test/acceptance/basic.js", "it('c', () => {})\n")  # nested
    write(tmp_path, "lib/app.js", "module.exports = 1\n")               # NOT a test
    assert score.measure(tmp_path, "js")["files"] == 3


def test_js_detects_plural_tests_suffix_JSONWEBTOKEN_regression(tmp_path):
    # jsonwebtoken mixes singular `.test.js` and plural `.tests.js`.
    write(tmp_path, "sign.tests.js", "it('a', () => {})\n")    # plural
    write(tmp_path, "verify.test.js", "it('b', () => {})\n")   # singular
    write(tmp_path, "keys.pem", "----\n")                      # non-code, ignored
    write(tmp_path, "helper.js", "module.exports = 1\n")       # not a test, not in test/
    assert score.measure(tmp_path, "js")["files"] == 2


def test_js_skips_node_modules_and_vendor(tmp_path):
    write(tmp_path, "src/foo.test.js", "it('a', () => {})\n")          # counts
    write(tmp_path, "node_modules/p/bar.test.js", "it('b', () => {})\n")  # skip
    write(tmp_path, "node_modules/p/test/baz.js", "it('c', () => {})\n")  # skip
    write(tmp_path, "vendor/q/qux.test.js", "it('d', () => {})\n")        # skip
    assert score.measure(tmp_path, "js")["files"] == 1


def test_js_suffix_variants(tmp_path):
    for n in ["a.test.ts", "b.spec.tsx", "c.test.mjs", "d.specs.js"]:
        write(tmp_path, n, "test('t', () => {})\n")
    write(tmp_path, "__tests__/e.js", "test('t', () => {})\n")
    write(tmp_path, "plain.ts", "export const x = 1\n")        # not a test
    assert score.measure(tmp_path, "js")["files"] == 5


# ───────────────────────── JS axis counts (verified by REPL) ────────────────
def test_js_a1_message_and_throw_matchers(tmp_path):
    body = (
        "it('1', () => { expect(() => f()).toThrow('boom'); });\n"        # match
        "it('2', () => { expect(() => g()).to.throw('no'); });\n"          # match (chai)
        "it('3', () => { expect(e.message).toContain('x'); });\n"          # match
        "it('4', () => { expect(() => h()).toThrow(); });\n"               # no arg -> no
        "it('5', () => { expect(() => k()).toThrow(TypeError); });\n"      # class -> no
    )
    write(tmp_path, "a.test.js", body)
    assert score.measure(tmp_path, "js")["A1_substring_match"] == 3


def test_js_c1_counts_mock_creation_not_config(tmp_path):
    body = (
        "const a = jest.fn();\n"               # match
        "jest.spyOn(o, 'm');\n"                # match
        "vi.fn();\n"                           # match
        "sinon.stub(o, 'p');\n"                # match
        "a.mockReturnValue(3);\n"              # config on existing mock -> NOT counted
    )
    write(tmp_path, "a.test.js", body)
    assert score.measure(tmp_path, "js")["C1_mock_real"] == 4


def test_js_b1_fixed_vector_12char_boundary(tmp_path):
    body = (
        "expect(t).toBe('aaaaaaaaaaaa');\n"          # exactly 12 -> match
        "expect(s).toBe('bbbbbbbbbbb');\n"           # 11 -> no
        "expect(u).toEqual('cccccccccccccccc');\n"   # 16 -> match
        "expect(x).toBe('short');\n"                 # 5 -> no
    )
    write(tmp_path, "a.test.js", body)
    assert score.measure(tmp_path, "js")["B1_fixed_vector"] == 2


def test_js_c2_framework_supertest(tmp_path):
    body = (
        "const request = require('supertest');\n"    # 'supertest'
        "await request(app).get('/');\n"             # request(app
    )
    write(tmp_path, "a.test.js", body)
    assert score.measure(tmp_path, "js")["C2_mock_framework"] == 2


def test_js_param_ratio_and_loc(tmp_path):
    body = (
        "it.each([1, 2])('x', () => {});\n"   # parametrized -> 1 test, 1 param
        "test('y', () => {});\n"              # 1 test
        "it('z', () => {});\n"                # 1 test
    )
    write(tmp_path, "a.test.js", body)
    m = score.measure(tmp_path, "js")
    assert m["test_count"] == 3
    assert m["parametrize"] == 1
    assert m["test_loc"] == 3
    assert m["D2_param_ratio"] == 0.333
    assert m["D1_loc_per_test"] == 1.0


# ───────────────────────── Python axis counts (the validated profile) ───────
def test_python_a1_substring(tmp_path):
    body = (
        "def test_a():\n"
        "    with pytest.raises(ValueError, match='boom'):\n"   # match=
        "        f()\n"
        "def test_b():\n"
        "    assert 'x' in str(e)\n"                            # in str(
    )
    write(tmp_path, "test_x.py", body)
    assert score.measure(tmp_path, "python")["A1_substring_match"] == 2


def test_python_a2_private_symbol(tmp_path):
    body = (
        "from itsdangerous.signer import _make_keys_list\n"   # private import
        "def test_x():\n"
        "    s._loads_unsafe(1)\n"                             # obj._private(
    )
    write(tmp_path, "test_x.py", body)
    assert score.measure(tmp_path, "python")["A2_private_symbol"] == 2


def test_python_c1_counts_clear_mock_idioms(tmp_path):
    body = (
        "def test_x():\n"
        "    m = MagicMock()\n"        # MagicMock
        "    patch(target).start()\n"  # patch(bareword)
        "    mocker.spy(o, 'm')\n"     # mocker
    )
    write(tmp_path, "test_x.py", body)
    assert score.measure(tmp_path, "python")["C1_mock_real"] == 3


def test_python_c1_counts_patch_string_and_bare_mock(tmp_path):
    # Regression for the trailing-\b bug: the two most common idioms that the
    # old regex dropped — patch('literal') and a bare Mock() — must both count.
    body = (
        "def test_x():\n"
        "    with patch('pkg.mod.func'):\n"   # the most common patch idiom
        "        pass\n"
        "    x = Mock()\n"                     # bare Mock() call
    )
    write(tmp_path, "test_x.py", body)
    assert score.measure(tmp_path, "python")["C1_mock_real"] == 2


def test_python_c1_does_not_double_count_mocker_patch(tmp_path):
    # `mocker.patch(...)` is one mock; the lookbehind must stop `patch(` from
    # counting on top of `mocker`.
    body = "def test_x():\n    mocker.patch('pkg.f')\n"
    write(tmp_path, "test_x.py", body)
    assert score.measure(tmp_path, "python")["C1_mock_real"] == 1


def test_python_c2_framework_primitives(tmp_path):
    body = (
        "def test_x(monkeypatch):\n"          # monkeypatch
        "    t = MockTransport(handler)\n"    # MockTransport
    )
    write(tmp_path, "test_x.py", body)
    assert score.measure(tmp_path, "python")["C2_mock_framework"] == 2


# ───────────────────────── Go profile ───────────────────────────────────────
def test_go_a2_is_uncountable_not_zero(tmp_path):
    # Same-package access to unexported names is idiomatic in Go; A.2 must be
    # n/a (None), never a misleading 0 that could read as a "win".
    write(tmp_path, "x_test.go", "func TestA(t *testing.T) {}\n")
    assert score.measure(tmp_path, "go")["A2_private_symbol"] is None


def test_go_counts_subtests_httptest_and_vectors(tmp_path):
    body = (
        'package x\n'
        'import "net/http/httptest"\n'
        'func TestServe(t *testing.T) {\n'                        # test_def
        '    srv := httptest.NewServer(h)\n'                      # C2
        '    t.Run("ok", func(t *testing.T) {\n'                  # param (t.Run)
        '        want := "expected-value-here-1234"\n'            # B1 (>=12)
        '        _ = want\n'
        '    })\n'
        '}\n'
        'func TestOther(t *testing.T) {}\n'                       # test_def
    )
    write(tmp_path, "x_test.go", body)
    m = score.measure(tmp_path, "go")
    assert m["test_count"] == 2          # two func Test*, not the inner closure
    assert m["parametrize"] == 1         # one t.Run subtest
    assert m["C2_mock_framework"] == 1   # httptest.NewServer
    assert m["B1_fixed_vector"] == 1     # want := "long literal"


# ───────────────────────── Known JS calibration gap (Chai) ──────────────────
@pytest.mark.xfail(reason="JS B.1 only matches Jest/Vitest matchers (.toBe/.toEqual); "
                          "Mocha+Chai `.to.equal('vec')` is invisible — under-detection "
                          "on jsonwebtoken/express; see memory",
                   strict=True)
def test_js_b1_should_count_chai_equal_fixed_vector(tmp_path):
    body = "it('t', () => { expect(token).to.equal('aaaaaaaaaaaaaaaa'); });\n"
    write(tmp_path, "a.test.js", body)
    assert score.measure(tmp_path, "js")["B1_fixed_vector"] == 1


# ───────────────────────── Robustness ───────────────────────────────────────
def test_empty_dir_is_all_zeros_no_crash(tmp_path):
    m = score.measure(tmp_path, "js")
    assert m["files"] == 0 and m["test_count"] == 0
    assert m["D1_loc_per_test"] == 0.0 and m["D2_param_ratio"] == 0.0
    assert m["A1_substring_match"] == 0
