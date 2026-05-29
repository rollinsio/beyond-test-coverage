#!/usr/bin/env python3
"""Score Run-3 generated suites vs baselines with the multi-language scorer.

Independent recompute (the authoritative Run-3 numbers): measures each
``wt-r3-<policy>`` suite and its repo's baseline using the bundled
``score.py`` per-language profiles, and emits
``results-run3-scorecard.{json,md}`` in the ``{baselines, arms}`` shape the
dashboard consumes — the same shape ``score_run2.py`` produces for Python.

Run AFTER the generation workflow finishes:
    python scripts/score_run3.py
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCORE_PY = ROOT / ".claude" / "skills" / "test-quality" / "scripts" / "score.py"

# repo -> (lang, tests_dir). "." = whole module (Go colocated _test.go).
REPOS = {
    "express": ("js", "test"),
    "jsonwebtoken": ("js", "test"),
    "zod": ("js", "packages/zod/src"),
    "chi": ("go", "."),
    "gjson": ("go", "."),
    "golang-jwt": ("go", "."),
}
POLICIES = ("oneshot", "iter2", "iter20")
AXES = ["A1_substring_match", "A2_private_symbol", "A4_recomputed_crypto",
        "A5_or_joined", "C1_mock_real", "B1_fixed_vector",
        "D1_loc_per_test", "D2_param_ratio"]


def load_scorer():
    spec = importlib.util.spec_from_file_location("score", SCORE_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["score"] = mod
    spec.loader.exec_module(mod)
    return mod


def tpath(root: Path, td: str) -> Path:
    return root if td == "." else root / td


def main() -> int:
    score = load_scorer()

    baselines = {}
    for repo, (lang, td) in REPOS.items():
        m = score.measure(tpath(ROOT / repo / "base", td), lang)
        baselines[repo] = {"lang": lang, **m}

    arms = []
    for repo, (lang, td) in REPOS.items():
        b = baselines[repo]
        for pol in POLICIES:
            wt = ROOT / repo / f"wt-r3-{pol}"
            tdir = tpath(wt, td)
            if not tdir.exists():
                arms.append({"repo": repo, "policy": pol, "present": False})
                continue
            g = score.measure(tdir, lang)
            axes, w, l, t = {}, 0, 0, 0
            for a in AXES:
                v = score.verdict(a, g.get(a), b.get(a))
                axes[a] = {"gen": g.get(a), "base": b.get(a), "verdict": v}
                w += v == "WIN"; l += v == "LOSS"; t += v == "TIE"
            arms.append({
                "repo": repo, "policy": pol, "present": True, "lang": lang,
                "test_count": g["test_count"], "test_loc": g["test_loc"],
                "c2_mock_framework": g.get("C2_mock_framework"),
                "axes": axes, "wins": w, "losses": l, "ties": t, "better": w > l,
            })

    (ROOT / "results-run3-scorecard.json").write_text(
        json.dumps({"baselines": baselines, "arms": arms}, indent=2) + "\n")

    # --- markdown ---
    scored = AXES
    md = ["# Run 3 scorecard — JS/TS + Go (gen vs baseline)", "",
          "Generated suites scored against each repo's human baseline with the",
          "multi-language `score.py`. Cell = `gen`v`base` then ✓ win / ✗ loss / "
          "= tie; `·` = n/a (axis not countable for the language).", "",
          "## Baselines", ""]
    for repo, (lang, _) in REPOS.items():
        b = baselines[repo]
        md.append(f"- **{repo}** ({lang}): tests={b['test_count']} loc={b['test_loc']} "
                  + " ".join(f"{a.split('_')[0]}={b.get(a)}" for a in scored))
    md += ["", "## Arms", "",
           "| repo/policy | " + " | ".join(a.split("_")[0] for a in scored)
           + " | W/L/T | better |",
           "|---|" + "---|" * len(scored) + "---|:--:|"]
    mark = {"WIN": "✓", "LOSS": "✗", "TIE": "=", "N/A": "·"}
    for r in arms:
        if not r["present"]:
            md.append(f"| {r['repo']}/{r['policy']} | "
                      + " | ".join(["—"] * len(scored)) + " | — | _absent_ |")
            continue
        cells = []
        for a in scored:
            ax = r["axes"][a]
            gv, bv = ax["gen"], ax["base"]
            fmt = lambda x: "·" if x is None else (f"{x:g}" if isinstance(x, float) else f"{x}")
            cells.append(f"{fmt(gv)}v{fmt(bv)}{mark[ax['verdict']]}")
        md.append(f"| {r['repo']}/{r['policy']} | " + " | ".join(cells)
                  + f" | {r['wins']}/{r['losses']}/{r['ties']} | "
                  + ("**yes**" if r["better"] else "no") + " |")
    md += ["", "_Direction: A.1/A.2/A.4/A.5/C.1/D.1 lower-better; B.1/D.2 higher-better. "
           "Raw-count axes (A.1, B.1) scale with suite size — read alongside test_count._"]
    (ROOT / "results-run3-scorecard.md").write_text("\n".join(md) + "\n")

    present = sum(1 for r in arms if r.get("present"))
    better = sum(1 for r in arms if r.get("better"))
    print(f"wrote results-run3-scorecard.{{json,md}}  "
          f"({present}/{len(arms)} arms present, {better} beat baseline)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
