---
name: results-dashboard
description: >-
  Turn a test-quality scorecard JSON into a self-contained interactive HTML
  readout — hero stats, a per-axis Win/Tie/Loss distribution chart, and the full
  per-suite matrix. Use when the user wants to visualize benchmark/scorecard
  results, regenerate the results dashboards in docs/, or render a
  {baselines, arms} scorecard (as emitted by the benchmark's score_quality.py /
  score_cross_language.py, or the test-quality skill's scorer) as a shareable
  web page. Produces one standalone .html file (Chart.js via CDN, no build step).
license: MIT
metadata:
  author: Michael Rollins
  version: "1.0"
---

# results-dashboard

Render a **scorecard JSON** into one self-contained HTML page you can open in a
browser or commit under `docs/`. The input is the `{baselines, arms}` shape the
benchmark's scorers emit (see `references/scorecard-json-shape.md`); the output
is a dark-themed readout with:

- **Hero stats** — arms scored, arms that beat their baseline (wins > losses),
  and a per-language split when arms carry a `lang`.
- **Per-axis Win / Tie / Loss chart** — a stacked bar per quality axis across all
  arms, so you can see at a glance which axes the generated suites win or lose.
- **Per-suite matrix** — every arm × every axis; each cell is `gen` over `base`
  with ✓ win / ✗ loss / = tie / · n-a, plus the W/L/T tally and a better? badge.

## When to use

- "Regenerate the results dashboard / readout for `<scorecard>.json`."
- "Visualize these scorecard results as a web page."
- After running `score_quality.py` / `score_cross_language.py` (or the
  `test-quality` skill's `score.py --json …`), to publish the numbers.

## Procedure

1. **Locate the input.** A scorecard JSON with a top-level `arms` array (and
   usually `baselines`). If the user points at a `results-*-scorecard.json`,
   use it directly. If they only have a raw tests dir, run the relevant scorer
   first to produce the JSON, then feed it here.
2. **Confirm the framing.** Ask for (or infer) a `--title` and a one-line
   `--subtitle`. Default title is derived from the filename.
3. **Generate:**
   ```bash
   python <skill>/scripts/build_dashboard.py <scorecard>.json \
       -o docs/<name>.html --title "…" --subtitle "…"
   ```
4. **Verify.** Open the file (or screenshot it) and check the hero counts match
   the scorer's own summary line (arms present / beat baseline). The script
   prints those counts on success — they must agree with the JSON.

## Notes

- **Self-contained.** The only external dependency is Chart.js from a CDN; the
  page needs network to draw the chart but renders the matrix offline.
- **Shape tolerance.** Arms with `"present": false` render as an `absent` row;
  `null` axis values render as `·`. Axis keys are read from the first present
  arm, so the columns adapt to whichever axes the scorer measured.
- **Don't hand-edit generated HTML.** Re-run the script after the scorer changes;
  the committed `docs/*.html` dashboards in this repo are curated, richer
  variants of the same idea — treat this skill's output as the reproducible base.
