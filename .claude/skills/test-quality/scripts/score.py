#!/usr/bin/env python3
"""Measure a test suite against the auto-countable test-quality axes.

Applies one fixed set of measurements (the grep/wc recipes from the
test-quality scorecard) to a tests directory. If a ``--baseline`` directory is
given (e.g. the suite *before* you started improving it, captured via
``git stash`` / a copy / an old commit), it also scores the current suite
against that baseline as a Win/Loss/Tie tally.

Multi-language via per-language *profiles*. The Python/pytest profile is the
one validated in the llm-testgen-bench quality experiment, where prompting a
model with these axes beat human-written baselines on the auto-countable axes
in 9 of 9 Python suites (8 of 9 with the model held fixed — the rubric, not the
model, drove the gain). The JavaScript/TypeScript and
Go profiles apply the same axes with framework-appropriate regexes; they are
heuristic and not yet empirically validated to the same degree — treat their
numbers as a guide, and lean on judgement (read the tests) more heavily.

Supported ``--lang``: python | js | go   (js = Jest / Vitest / Mocha+Chai+Sinon
/ node:test, .js/.ts/.jsx/.tsx). Omit ``--lang`` to auto-detect from the files.

Auto-scored axes (direction in parens):
  A.1 substring-match assertions on error messages   (lower better)
  A.2 private-symbol / internal access               (lower better)
  A.4 recomputed crypto/encoding expected values     (lower better)
  A.5 or-joined error-text assertions                (lower better)
  C.1 mock_real  (hand mocks/stubs/spies)            (lower better, target 0)
  B.1 fixed-vector asserts / inline snapshots        (higher better)
  D.1 test_loc / test_count                          (lower better)
  D.2 parametrize(table) / test_count                (higher better)
Reported, not scored:
  C.2 mock_framework (real-I/O primitives — legitimate, context only)
An axis shown as "n/a" is not reliably countable for that language; assess it by
reading (the skill handles the judgement axes A.3, A.6, B.2, B.3, E.* anyway).

Usage:
    python score.py --tests path/to/tests
    python score.py --tests path/to/tests --lang js
    python score.py --tests tests --baseline path/to/old_tests
    python score.py --tests tests --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

BT = "`"  # backtick, kept out of the raw strings for readability

# --- language profiles -------------------------------------------------------
# Each axis maps to a regex string, or None when it isn't reliably countable for
# that language (then it's reported as n/a and excluded from the W/L/T tally).
PROFILES = {
    "python": {
        "exts": [".py"],
        "test_file": r"\.py$",
        "test_def": r"\bdef test_\w*\(",
        "param": r"@pytest\.mark\.parametrize",
        "validated": True,
        "axes": {
            "A1_substring_match": r"pytest\.raises\([^)]*match=|\bin str\(",
            "A2_private_symbol": r"from [\w.]+ import [\w,\s]*_[a-zA-Z]\w*|\b\w+\._[a-zA-Z]\w*\(",
            "A4_recomputed_crypto": r"\bhmac\.|\bhashlib\.|expected\s*=\s*(?:hmac|hashlib|base64)",
            "A5_or_joined": r"in str\([^)]*\)\s*or\s",
            # `patch(` guarded by a lookbehind so `mocker.patch`/`mock.patch`
            # aren't double-counted (already covered by `mocker`); the old
            # trailing \b dropped patch('str')/@patch/Mock() entirely.
            "C1_mock_real": r"\bMagicMock\b|\bMock\(|(?<![.\w])patch\(|\bmocker\b",
            "C2_mock_framework": r"\b(?:MockTransport|WSGITransport|ASGITransport|monkeypatch|httpbin)\b",
            "B1_fixed_vector": r"""assert\s+[^\n=]*==\s*b?["'][A-Za-z0-9+/=\\xX_\-.]{16,}""",
        },
    },
    # Jest / Vitest / Mocha+Chai+Sinon / node:test. Heuristic, best-effort.
    "js": {
        "exts": [".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".mts", ".cts"],
        "test_file": r"\.(?:test|spec)s?\.[cm]?[jt]sx?$|[/\\]__tests__[/\\]|[/\\]tests?[/\\].*\.[cm]?[jt]sx?$",
        "test_def": r"\b(?:it|test)\s*(?:\.\s*(?:only|skip|concurrent|each|failing|todo|sequential))?\s*\(",
        "param": r"\b(?:it|test|describe)\s*\.\s*each\b",
        "validated": False,
        "axes": {
            # PARTIAL matchers only — substring/regex/membership/throw. Jest
            # `.toThrow('s')` & Chai `.to.throw('s')` match the message as a
            # substring; `.message` chained into a partial matcher likewise.
            # Exact `==`-literal assertions are a fixed vector → B.1, not A.1
            # (mirrors the validated Python split: match=/in str( → A.1).
            # toThrow()/toThrow(Class) pin nothing, so the quote/slash is required.
            "A1_substring_match": (
                r"\.(?:toThrow|toThrowError)\(\s*['\"" + BT + r"/]"
                r"|\.to(?:\.not)?\.throw\(\s*['\"" + BT + r"/]"
                r"|\.message\b[^;\n]{0,40}?\.(?:toContain|toMatch|include|includes|match)\b"
                r"|\bassert\.throws?\([^\n]*,\s*/"
            ),
            "A2_private_symbol": r"\bas any\b|\._[A-Za-z]\w*|\[\s*['\"]_[A-Za-z]",
            "A4_recomputed_crypto": (
                r"crypto\.(?:createHmac|createHash|createCipheriv|createSign)\b"
                r"|\bexpected\b[^;\n]*(?:createHmac|createHash|Buffer\.from)"
                r"|Buffer\.from\([^)]*\)\.toString\(\s*['\"" + BT + r"](?:base64|hex)"
            ),
            "A5_or_joined": r"\.toMatch\(\s*/[^/\n]*\||\|\|[^;\n]*(?:\.message|toThrow)",
            # Count mock *creation* (footprint), not return-value config:
            # `.mockReturnValue/.mockResolvedValue/...` configure an existing
            # mock and would double-count, penalizing a test that just stubs a
            # return on a mock it already owns.
            "C1_mock_real": (
                r"\bjest\.(?:fn|mock|spyOn|replaceProperty|createMockFromModule)\("
                r"|\bvi\.(?:fn|mock|spyOn|stubGlobal|stubEnv|importMock)\("
                r"|\bsinon\.(?:stub|spy|mock|fake|createStubInstance|replace)\b"
            ),
            # Legitimate framework doubles (context only, not scored). sinon
            # fake-timers/fake-server control time/transport boundaries — the
            # acceptable side of the C.1/C.2 line, not a hand mock of the unit.
            "C2_mock_framework": (
                r"\bsupertest\b|@testing-library|\bsetupServer\b|\bsetupWorker\b"
                r"|\bnock\(|\bfetchMock\b|fetch-mock|request\(\s*app\b|\brender\("
                r"|\bsinon\.(?:useFakeTimers|useFakeXMLHttpRequest|fakeServer)\b"
            ),
            # Exact-literal equality against a 12+ char literal (or hex/inline
            # snapshot): Jest/Vitest `.toBe/.toEqual`, Chai `.to.equal/.eql/
            # .deep.equal`, and node/chai `assert.equal/strictEqual/deepEqual`.
            "B1_fixed_vector": (
                r"\.(?:toBe|toEqual|toStrictEqual)\(\s*(?:['\"" + BT + r"][^'\"" + BT + r"\n]{12,}['\"" + BT + r"]"
                r"|0x[0-9a-fA-F]{8,}|Buffer\.from\(\s*['\"" + BT + r"][0-9a-fA-F]{16,})"
                r"|\btoMatchInlineSnapshot\("
                r"|\.to(?:\.deep)?\.(?:equal|eql)\(\s*['\"" + BT + r"][^'\"" + BT + r"\n]{12,}['\"" + BT + r"]"
                r"|\bassert\.(?:strictEqual|deepStrictEqual|deepEqual|equal)\([^,\n]*,\s*['\"" + BT + r"][^'\"" + BT + r"\n]{12,}['\"" + BT + r"]"
            ),
        },
    },
    # Go testing (+ testify / gomock / httptest). Best-effort.
    "go": {
        "exts": [".go"],
        "test_file": r"_test\.go$",
        "test_def": r"\bfunc\s+(?:Test|Fuzz)\w+\(",
        "param": r"\bt\.Run\(",  # subtests ≈ table-driven parametrization
        "validated": False,
        "axes": {
            "A1_substring_match": (
                r"strings\.Contains\([^)]*\.Error\(\)|\.Error\(\)\s*==\s*\""
                r"|(?:assert|require)\.(?:EqualError|ErrorContains)\("
            ),
            "A2_private_symbol": None,  # same-package _test access to unexported is idiomatic in Go
            "A4_recomputed_crypto": (
                r"\bhmac\.New\(|\bsha256\.|\bsha1\.|\bmd5\."
                r"|expected\s*:?=\s*[^;\n]*(?:hmac|sha256|sha1|hex\.EncodeToString)"
            ),
            "A5_or_joined": r"\|\|[^;\n]*\.Error\(\)",
            "C1_mock_real": r"\bgomock\.|\.EXPECT\(\)|\bmock\.Mock\b|\.On\(\s*\"",
            "C2_mock_framework": r"\bhttptest\.(?:NewServer|NewRequest|NewRecorder|NewTLSServer)\(",
            # Fixed vectors in Go are usually table-driven: literal expected
            # values sit in struct rows and are asserted via `got != tc.want`.
            # So count, beyond inline `want := "lit"` / `== "lit"` / `[]byte("`:
            #  - comparison sites against a want/expected-named field or var, and
            #  - named expected-field literals in table rows.
            # (Without this, table-driven suites — the idiom the contract wants —
            # scored ~0 on B.1.)
            "B1_fixed_vector": (
                r"want\s*:?=\s*\"[^\"\n]{12,}\"|==\s*\"[^\"\n]{12,}\"|\[\]byte\(\s*\""
                r"|(?:!=|==)\s*(?:tc\.|tt\.|c\.)?(?:want|wantErr|wantBody|wantStatus|expected|exp|output|out|result|wanted)\b"
                r"|\b(?:want|wantBody|expected|exp|output|out|wanted)\s*:\s*(?:\"[^\"\n]{8,}\"|`|\[\]byte\()"
            ),
        },
    },
}

# axis -> True if lower is better, False if higher is better
SCORED = {
    "A1_substring_match": True,
    "A2_private_symbol": True,
    "A4_recomputed_crypto": True,
    "A5_or_joined": True,
    "C1_mock_real": True,
    "B1_fixed_vector": False,
    "D1_loc_per_test": True,
    "D2_param_ratio": False,
}


def _compile(profile: dict) -> dict:
    out = {"test_def": re.compile(profile["test_def"]),
           "param": re.compile(profile["param"]),
           "test_file": re.compile(profile["test_file"]),
           "axes": {}}
    for k, rx in profile["axes"].items():
        out["axes"][k] = re.compile(rx) if rx else None
    return out


def _iter_test_files(target: Path, profile: dict, compiled: dict):
    exts = set(profile["exts"])
    # An explicitly-given single file is measured as-is (no test-name filter);
    # a directory is walked and filtered to files that look like tests.
    if target.is_file():
        if target.suffix in exts:
            yield target
        return
    skip = {"node_modules", ".git", "vendor", "coverage"}
    for p in sorted(target.rglob("*")):
        if not p.is_file() or p.suffix not in exts:
            continue
        if skip & set(p.parts):
            continue
        if compiled["test_file"].search(str(p)):
            yield p


def detect_lang(tests_dir: Path) -> str:
    """Pick the profile whose test-file pattern matches the most files."""
    best, best_n = "python", -1
    for name, profile in PROFILES.items():
        comp = _compile(profile)
        n = sum(1 for _ in _iter_test_files(tests_dir, profile, comp))
        if n > best_n:
            best, best_n = name, n
    return best


def measure(tests_dir: Path, lang: str) -> dict:
    profile = PROFILES[lang]
    comp = _compile(profile)
    counts = {k: (0 if rx else None) for k, rx in comp["axes"].items()}
    test_count = test_loc = files = param = 0
    if tests_dir.exists():
        for p in _iter_test_files(tests_dir, profile, comp):
            try:
                text = p.read_text(errors="replace")
            except Exception:
                continue
            files += 1
            test_loc += len(text.splitlines())
            test_count += len(comp["test_def"].findall(text))
            param += len(comp["param"].findall(text))
            for k, rx in comp["axes"].items():
                if rx is not None:
                    counts[k] += len(rx.findall(text))
    counts["files"] = files
    counts["test_count"] = test_count
    counts["test_loc"] = test_loc
    counts["parametrize"] = param
    counts["D1_loc_per_test"] = round(test_loc / test_count, 2) if test_count else 0.0
    counts["D2_param_ratio"] = round(param / test_count, 3) if test_count else 0.0
    return counts


def verdict(axis: str, gen, base) -> str:
    if gen is None or base is None:
        return "N/A"
    if gen == base:
        return "TIE"
    lower_better = SCORED[axis]
    better = (gen < base) if lower_better else (gen > base)
    return "WIN" if better else "LOSS"


def render(cur: dict, base: dict | None, lang: str) -> str:
    axes = list(SCORED)
    validated = PROFILES[lang].get("validated")
    tier = "validated" if validated else "heuristic — verify by reading"
    lines = [f"# test-quality scorecard — lang={lang} ({tier})", ""]
    c2 = cur["C2_mock_framework"]
    lines.append(f"current: files={cur['files']} tests={cur['test_count']} "
                 f"loc={cur['test_loc']} C2_framework={c2 if c2 is not None else 'n/a'}")
    if base is not None:
        bc2 = base["C2_mock_framework"]
        lines.append(f"baseline: files={base['files']} tests={base['test_count']} "
                     f"loc={base['test_loc']} C2_framework={bc2 if bc2 is not None else 'n/a'}")
    lines.append("")
    fmt = lambda v: "n/a" if v is None else v
    if base is None:
        lines += ["| axis | value | want |", "|---|---:|---|"]
        want = {True: "↓ lower", False: "↑ higher"}
        for a in axes:
            lines.append(f"| {a} | {fmt(cur[a])} | {want[SCORED[a]]} |")
        return "\n".join(lines)
    w = l = t = 0
    lines += ["| axis | current | baseline | verdict |", "|---|---:|---:|:--:|"]
    for a in axes:
        v = verdict(a, cur[a], base[a])
        if v == "WIN": w += 1
        elif v == "LOSS": l += 1
        elif v == "TIE": t += 1
        mark = {"WIN": "✓ win", "LOSS": "✗ loss", "TIE": "= tie", "N/A": "· n/a"}[v]
        lines.append(f"| {a} | {fmt(cur[a])} | {fmt(base[a])} | {mark} |")
    lines.append("")
    lines.append(f"**Tally: {w} wins / {l} losses / {t} ties — "
                 f"{'BETTER' if w > l else 'NOT better'} than baseline on countable axes.**")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tests", required=True, help="Path to the tests directory to measure.")
    ap.add_argument("--baseline", default=None,
                    help="Optional path to the prior/baseline tests dir to score against.")
    ap.add_argument("--lang", choices=sorted(PROFILES), default=None,
                    help="Language profile. Omit to auto-detect from the files.")
    ap.add_argument("--json", action="store_true", help="Emit JSON only (no table).")
    args = ap.parse_args()

    tests = Path(args.tests)
    if not tests.exists():
        print(f"tests dir not found: {tests}", file=sys.stderr)
        return 2
    lang = args.lang or detect_lang(tests)
    cur = measure(tests, lang)
    base = measure(Path(args.baseline), lang) if args.baseline else None

    if args.json:
        out = {"lang": lang, "validated": PROFILES[lang].get("validated", False), "current": cur}
        if base is not None:
            out["baseline"] = base
            out["verdicts"] = {a: verdict(a, cur[a], base[a]) for a in SCORED}
        print(json.dumps(out, indent=2))
    else:
        print(render(cur, base, lang))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
