#!/usr/bin/env python3
"""Independent quality-scorecard recompute for the Python experiments.

The generation sessions each wrote their own ``scorecard.json`` /
``final_scorecard.json`` in mutually incompatible shapes (axes as
dict-of-{baseline,suite,result}, as dict-of-{mine,baseline,result}, as flat
``A1: 0`` counts, as grouped A/B/C/D blocks, ...). Trusting those is both
fragile (8 bespoke adapters) and circular (it trusts each session to score
itself).

This script instead applies ONE identical set of measurements to every test
suite — the 9 generated suites AND the 3 human baselines — using the grep/wc
recipes from ``prompts/quality/quality_scorecard.md``. It then scores each
generated suite against its own repo's baseline and prints a W/L/T tally.

Auto-scored axes (countable, unambiguous):
  A.1 substring-match assertions      (lower better)
  A.2 private-symbol uses             (lower better)
  A.4 recomputed crypto/encoding      (lower better)
  A.5 or-joined error matches         (lower better)
  C.1 mock_real_loc                   (lower better)
  B.1 fixed-vector asserts            (higher better)
  D.1 test_loc / test_count           (lower better)
  D.2 parametrize / test_count        (higher better)
Reported but not scored:
  C.2 mock_framework_loc  (framework primitives — legitimate, context only)

NOT auto-scored (need semantic judgement; see each SUMMARY.md): A.3 tautological
readbacks, A.6 hand-coded charsets, B.2 boundary coverage, B.3 framework-I/O
tests, E.* correctness/REPL/contract. The tally here is therefore a *floor* on
quality, not the whole scorecard.

Usage:
    python scripts/score_quality.py                       # quality experiment (default)
    python scripts/score_quality.py --experiment coverage # coverage-driven control
    python scripts/score_quality.py --experiment ablation # Opus-4.7 prompt-vs-model control
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REPOS = {
    "itsdangerous": "tests",
    "httpx": "tests",
    "requests": "tests",
}
POLICIES = ("oneshot", "iter2", "iter20")

# The Python experiments, mapped to the (git-ignored) on-disk worktree prefix
# each one's sessions wrote into. Prefixes are a historical filesystem fact;
# the experiment names are the interface.
EXPERIMENTS = {
    "coverage": "wt-",      # coverage-driven control
    "quality":  "wt-r2-",   # quality-driven
    "ablation": "wt-r2b-",  # Opus 4.7 + quality prompts; isolates prompt vs model
}

# Measurement recipes — match prompts/quality/quality_scorecard.md as closely as
# a single regex pass allows. Counts are total occurrences across all *.py files.
PATTERNS = {
    "A1_substring_match": re.compile(r"pytest\.raises\([^)]*match=|\bin str\("),
    "A2_private_symbol": re.compile(r"from [\w.]+ import [\w,\s]*_[a-zA-Z]\w*|\b\w+\._[a-zA-Z]\w*\("),
    "A4_recomputed_crypto": re.compile(r"\bhmac\.|\bhashlib\.|expected\s*=\s*(?:hmac|hashlib|base64)"),
    "A5_or_joined": re.compile(r"in str\([^)]*\)\s*or\s"),
    # `patch(` guarded by a lookbehind so `mocker.patch` isn't double-counted;
    # the old trailing \b dropped patch('str')/@patch/Mock() (real-mock undercount).
    "C1_mock_real": re.compile(r"\bMagicMock\b|\bMock\(|(?<![.\w])patch\(|\bmocker\b"),
    "C2_mock_framework": re.compile(r"\b(?:MockTransport|WSGITransport|ASGITransport|monkeypatch|httpbin)\b"),
    "B1_fixed_vector": re.compile(r"""assert\s+[^\n=]*==\s*b?["'][A-Za-z0-9+/=\\xX_\-.]{16,}"""),
    "parametrize": re.compile(r"@pytest\.mark\.parametrize"),
}
TEST_DEF = re.compile(r"\bdef test_\w*\(")

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


def measure(tests_dir: Path) -> dict:
    counts = {k: 0 for k in PATTERNS}
    test_count = 0
    test_loc = 0
    if tests_dir.exists():
        for p in sorted(tests_dir.rglob("*.py")):
            try:
                text = p.read_text()
            except Exception:
                continue
            test_loc += len(text.splitlines())
            test_count += len(TEST_DEF.findall(text))
            for k, rx in PATTERNS.items():
                counts[k] += len(rx.findall(text))
    counts["test_count"] = test_count
    counts["test_loc"] = test_loc
    counts["D1_loc_per_test"] = round(test_loc / test_count, 2) if test_count else 0.0
    counts["D2_param_ratio"] = round(counts["parametrize"] / test_count, 3) if test_count else 0.0
    return counts


def verdict(axis: str, gen: float, base: float) -> str:
    if gen == base:
        return "TIE"
    lower_better = SCORED[axis]
    better = (gen < base) if lower_better else (gen > base)
    return "WIN" if better else "LOSS"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--experiment", choices=list(EXPERIMENTS), default="quality",
                    help="Which Python experiment to score (sets the worktree prefix "
                         "and output filename). Default: quality.")
    args = ap.parse_args()
    tag = args.experiment
    prefix = EXPERIMENTS[tag]

    baselines = {repo: measure(ROOT / repo / "base" / td) for repo, td in REPOS.items()}

    rows = []
    for repo, td in REPOS.items():
        base = baselines[repo]
        for pol in POLICIES:
            gen_dir = ROOT / repo / f"{prefix}{pol}" / td
            if not gen_dir.exists() or not any(gen_dir.rglob("*.py")):
                rows.append({"repo": repo, "policy": pol, "present": False})
                continue
            gen = measure(gen_dir)
            axes = {}
            w = l = t = 0
            for axis in SCORED:
                v = verdict(axis, gen[axis], base[axis])
                axes[axis] = {"gen": gen[axis], "base": base[axis], "verdict": v}
                w += v == "WIN"; l += v == "LOSS"; t += v == "TIE"
            rows.append({
                "repo": repo, "policy": pol, "present": True,
                "test_count": gen["test_count"], "test_loc": gen["test_loc"],
                "c2_mock_framework": gen["C2_mock_framework"],
                "axes": axes, "wins": w, "losses": l, "ties": t,
                "better": w > l,
            })

    # ---- render ----
    scored_axes = list(SCORED)
    hdr = "| repo/policy | " + " | ".join(a.split("_")[0] for a in scored_axes) + " | W/L/T | better |"
    sep = "|" + "---|" * (len(scored_axes) + 3)
    lines = [f"# {tag} — independent scorecard recompute (auto-countable axes only)", "",
             "Baselines (same measure):"]
    for repo in REPOS:
        b = baselines[repo]
        lines.append(f"- **{repo}**: tests={b['test_count']} loc={b['test_loc']} "
                     f"A1={b['A1_substring_match']} A2={b['A2_private_symbol']} A4={b['A4_recomputed_crypto']} "
                     f"A5={b['A5_or_joined']} C1={b['C1_mock_real']} B1={b['B1_fixed_vector']} "
                     f"D1={b['D1_loc_per_test']} D2={b['D2_param_ratio']}")
    lines += ["", hdr, sep]
    for r in rows:
        if not r.get("present"):
            lines.append(f"| {r['repo']}/{r['policy']} | " + " | ".join(["—"] * len(scored_axes)) + " | — | _absent_ |")
            continue
        cells = []
        for a in scored_axes:
            ax = r["axes"][a]
            mark = {"WIN": "✓", "LOSS": "✗", "TIE": "="}[ax["verdict"]]
            cells.append(f"{ax['gen']}v{ax['base']}{mark}")
        lines.append(f"| {r['repo']}/{r['policy']} | " + " | ".join(cells)
                     + f" | {r['wins']}/{r['losses']}/{r['ties']} | {'YES' if r['better'] else 'no'} |")
    lines += ["", "Cell = `gen`v`base` then ✓ win / ✗ loss / = tie. "
              "Auto-scored axes only (A1,A2,A4,A5,C1,B1,D1,D2). "
              "A.3/A.6/B.2/B.3/E.* need semantic judgement — see each SUMMARY.md."]
    md = "\n".join(lines)

    out_md = ROOT / f"results-{tag}-scorecard.md"
    out_json = ROOT / f"results-{tag}-scorecard.json"
    out_md.write_text(md)
    out_json.write_text(json.dumps({"baselines": baselines, "arms": rows}, indent=2))
    print(md)
    print(f"\nWrote {out_md}\nWrote {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
