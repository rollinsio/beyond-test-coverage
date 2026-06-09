#!/usr/bin/env python3
"""Score the Kotlin/Swift 3-policy matrix (oneshot/iter2/iter20) vs human baselines.

Independent recompute: for each repo, measures the human baseline (whole-repo
test suite) and each policy arm's generated suite with the bundled multi-language
``score.py``, and emits ``results-kotlin-swift-scorecard.{json,md}`` in the same
``{baselines, arms}`` shape the dashboard consumes.

This is the Kotlin/Swift counterpart to ``score_cross_language.py`` (JS/TS + Go).
It is driven by a manifest the orchestrator populates as arms complete, so green
status and the real passed/failed counts come from the actual toolchain runs and
are recorded alongside the scorer's deterministic axis recompute.

    python scripts/score_kotlin_swift_matrix.py            # uses bench-clones/.matrix-manifest.json
    python scripts/score_kotlin_swift_matrix.py PATH.json  # explicit manifest
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCORE_PY = ROOT / ".claude" / "skills" / "test-quality" / "scripts" / "score.py"
DEFAULT_MANIFEST = ROOT / "bench-clones" / ".matrix-manifest.json"
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


def main() -> int:
    manifest_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_MANIFEST
    manifest = json.loads(manifest_path.read_text())
    score = load_scorer()

    baselines, arms = {}, []
    for repo, cfg in manifest.items():
        lang = cfg["lang"]
        b = score.measure(Path(cfg["baseline_dir"]), lang)
        baselines[repo] = {"lang": lang, "scope": cfg.get("scope", ""), **b}

    for repo, cfg in manifest.items():
        lang = cfg["lang"]
        b = baselines[repo]
        for pol in POLICIES:
            arm = cfg.get("arms", {}).get(pol)
            if not arm:
                arms.append({"repo": repo, "policy": pol, "present": False})
                continue
            g = score.measure(Path(arm["gen_dir"]), lang)
            axes, w, l, t = {}, 0, 0, 0
            for a in AXES:
                v = score.verdict(a, g.get(a), b.get(a))
                axes[a] = {"gen": g.get(a), "base": b.get(a), "verdict": v}
                w += v == "WIN"; l += v == "LOSS"; t += v == "TIE"
            arms.append({
                "repo": repo, "policy": pol, "present": True, "lang": lang,
                "green": arm["green"], "passed": arm.get("passed"),
                "failed": arm.get("failed"), "run_cmd": arm.get("run_cmd"),
                "test_count": g["test_count"], "test_loc": g["test_loc"],
                "c2_mock_framework": g.get("C2_mock_framework"),
                "axes": axes, "wins": w, "losses": l, "ties": t, "better": w > l,
            })

    (ROOT / "results-kotlin-swift-scorecard.json").write_text(
        json.dumps({"baselines": baselines, "arms": arms}, indent=2) + "\n")

    # --- markdown ---
    md = ["# Kotlin + Swift scorecard — full 3-policy matrix (gen vs baseline)", "",
          "Generated suites scored against each repo's human baseline with the",
          "multi-language `score.py`. Cell = `gen`v`base` then ✓ win / ✗ loss / "
          "= tie; `·` = n/a. `green` and passed/failed are from the real toolchain run.", "",
          "## Baselines (whole human suite)", ""]
    for repo, b in baselines.items():
        md.append(f"- **{repo}** ({b['lang']}): tests={b['test_count']} loc={b['test_loc']} "
                  + " ".join(f"{a.split('_')[0]}={b.get(a)}" for a in AXES)
                  + (f"  _(scope: {b['scope']})_" if b.get("scope") else ""))
    md += ["", "## Arms", "",
           "| repo/policy | green | P/F | " + " | ".join(a.split("_")[0] for a in AXES)
           + " | W/L/T | better |",
           "|---|:--:|---|" + "---|" * len(AXES) + ":--:|:--:|"]
    mark = {"WIN": "✓", "LOSS": "✗", "TIE": "=", "N/A": "·"}
    fmt = lambda x: "·" if x is None else (f"{x:g}" if isinstance(x, float) else f"{x}")
    for r in arms:
        if not r["present"]:
            md.append(f"| {r['repo']}/{r['policy']} | — | — | "
                      + " | ".join(["—"] * len(AXES)) + " | — | _absent_ |")
            continue
        cells = [f"{fmt(r['axes'][a]['gen'])}v{fmt(r['axes'][a]['base'])}{mark[r['axes'][a]['verdict']]}"
                 for a in AXES]
        g = "🟢" if r["green"] else "🔴"
        pf = f"{r.get('passed','?')}/{r.get('failed','?')}"
        md.append(f"| {r['repo']}/{r['policy']} | {g} | {pf} | " + " | ".join(cells)
                  + f" | {r['wins']}/{r['losses']}/{r['ties']} | "
                  + ("**yes**" if r["better"] else "no") + " |")
    md += ["", "_Direction: A.1/A.2/A.4/A.5/C.1/D.1 lower-better; B.1/D.2 higher-better. "
           "Raw-count axes (A.1, B.1) scale with suite size — read alongside test_count. "
           "oneshot is allowed to ship red (one pass, no repair); iter2/iter20 must be green._"]
    (ROOT / "results-kotlin-swift-scorecard.md").write_text("\n".join(md) + "\n")

    present = sum(1 for r in arms if r.get("present"))
    better = sum(1 for r in arms if r.get("better"))
    green = sum(1 for r in arms if r.get("present") and r.get("green"))
    print(f"wrote results-kotlin-swift-scorecard.{{json,md}}  "
          f"({present}/{len(arms)} arms present, {green} green, {better} beat baseline)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
