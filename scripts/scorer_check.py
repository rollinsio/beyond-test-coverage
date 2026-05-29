#!/usr/bin/env python3
"""Scorer-check: validate the test-quality JS/Go profiles against real OSS suites.

Runs the bundled scorer (``.claude/skills/test-quality/scripts/score.py``) over
the *baseline* (human-written) test suites of six cloned repos and records the
auto-counted axis values. This is **profile validation** — confirming each axis
fires sensibly on real-world idioms — NOT a benchmark run: there is no
generation and no gen-vs-baseline verdict here, only the baseline measurement.

Repos (cloned under ``<repo>/base/``, git-ignored):
  JS/TS:  expressjs/express, auth0/node-jsonwebtoken, colinhacks/zod
  Go:     go-chi/chi, tidwall/gjson, golang-jwt/jwt

Why these: each is widely used, well-tested, and exercises a distinct stack —
express = node:assert + supertest, jsonwebtoken = Chai BDD + chai-assert +
sinon fake-timers, zod = Vitest + inline snapshots; the Go trio = stdlib
testing + subtests (+ httptest for chi).

Outputs ``results-scorer-check.{json,md}`` at the repo root.
Run:  python scripts/scorer_check.py
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCORE_PY = ROOT / ".claude" / "skills" / "test-quality" / "scripts" / "score.py"

# repo dir -> (slug, expected lang). Order = JS first, then Go.
REPOS = [
    ("express", "expressjs/express", "js"),
    ("jsonwebtoken", "auth0/node-jsonwebtoken", "js"),
    ("zod", "colinhacks/zod", "js"),
    ("chi", "go-chi/chi", "go"),
    ("gjson", "tidwall/gjson", "go"),
    ("golang-jwt", "golang-jwt/jwt", "go"),
]

# Axes in display order; (key, lower-is-better, one-word direction marker).
AXES = [
    ("A1_substring_match", True, "↓"),
    ("A2_private_symbol", True, "↓"),
    ("A4_recomputed_crypto", True, "↓"),
    ("A5_or_joined", True, "↓"),
    ("C1_mock_real", True, "↓"),
    ("B1_fixed_vector", False, "↑"),
    ("D1_loc_per_test", True, "↓"),
    ("D2_param_ratio", False, "↑"),
]


def load_scorer():
    spec = importlib.util.spec_from_file_location("score", SCORE_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["score"] = mod  # @dataclass-free, but register for safety
    spec.loader.exec_module(mod)
    return mod


def head(repo_base: Path) -> str | None:
    try:
        return subprocess.run(
            ["git", "-C", str(repo_base), "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except Exception:
        return None


def main() -> int:
    score = load_scorer()
    results = []
    for dirname, slug, expected_lang in REPOS:
        base = ROOT / dirname / "base"
        if not base.exists():
            print(f"skip {dirname}: {base} not found (clone missing)", file=sys.stderr)
            continue
        lang = expected_lang
        cur = score.measure(base, lang)
        results.append({
            "repo": dirname,
            "slug": slug,
            "lang": lang,
            "validated": score.PROFILES[lang].get("validated", False),
            "head": head(base),
            "files": cur["files"],
            "test_count": cur["test_count"],
            "test_loc": cur["test_loc"],
            "axes": {k: cur.get(k) for k, _, _ in AXES},
            "C2_mock_framework": cur.get("C2_mock_framework"),
        })

    payload = {
        "kind": "scorer-check",
        "note": "Baseline-only profile validation of the JS/Go scorer profiles. "
                "No generation, no gen-vs-baseline verdict — confirms each "
                "auto-counted axis fires on real-world idioms.",
        "scorer": str(SCORE_PY.relative_to(ROOT)),
        "results": results,
    }
    (ROOT / "results-scorer-check.json").write_text(json.dumps(payload, indent=2) + "\n")

    # --- markdown ---
    md = ["# Scorer-check — JS/Go profile validation", "",
          "Baseline-only measurement of the bundled `test-quality` scorer over six",
          "cloned OSS suites. **This is profile validation, not a benchmark run:**",
          "there is no generated suite and no win/loss verdict — only confirmation",
          "that each auto-counted axis fires sensibly on real framework idioms.",
          "",
          "Direction: ↓ lower-is-better, ↑ higher-is-better. `n/a` = axis not",
          "reliably countable for that language (excluded from any tally).",
          "",
          "| repo | lang | head | files | tests | loc | "
          + " | ".join(f"{k.split('_')[0]} {d}" for k, _, d in AXES)
          + " | C2 |",
          "|---|---|---|---:|---:|---:|" + "---:|" * (len(AXES) + 1)]
    for r in results:
        cells = []
        for k, _, _ in AXES:
            v = r["axes"][k]
            cells.append("n/a" if v is None else (f"{v}" if not isinstance(v, float) else f"{v:g}"))
        c2 = r["C2_mock_framework"]
        md.append(
            f"| {r['slug']} | {r['lang']} | `{r['head']}` | {r['files']} | "
            f"{r['test_count']} | {r['test_loc']} | " + " | ".join(cells)
            + f" | {'n/a' if c2 is None else c2} |"
        )
    md += [
        "",
        "## Notes (what each axis confirms / caveats)",
        "",
        "- **express** = `node:assert` + supertest. A.1 catches `assert.throws(fn, /re/)`;",
        "  B.1 catches `assert.strictEqual(x, 'literal')`; C.2 is supertest `.expect`.",
        "- **jsonwebtoken** = Chai BDD + chai-assert + `sinon.useFakeTimers`. A.1 catches",
        "  `.to.throw('msg')` and `.message…include`; B.1 catches `.to.equal('literal')`;",
        "  the sinon usage is **fake-timers → C.2** (legit time control), so **C.1 = 0**",
        "  is correct, not a miss.",
        "- **zod** = Vitest + inline snapshots. B.1 is high (exact `.toBe`/snapshots).",
        "  `D2 = 0` is a **true negative**: zod parametrizes with raw `for` loops, not",
        "  framework `.each` tables.",
        "- **Go** A.2 = `n/a` (same-package access to unexported names is idiomatic).",
        "  `D1_loc_per_test` is inflated (counts `func TestX`, not `t.Run` subtests) and",
        "  is **not** cross-language comparable — prefer D.2 for Go.",
        "",
        "_Profiles remain `validated:false`: calibrated to fire on real idioms, but not",
        "yet run through a full gen-vs-baseline benchmark. Treat numbers as a guide;",
        "read the tests for the judgement axes._",
    ]
    (ROOT / "results-scorer-check.md").write_text("\n".join(md) + "\n")
    print(f"wrote results-scorer-check.json + .md  ({len(results)} repos)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
