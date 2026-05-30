#!/usr/bin/env python3
"""Render a test-quality scorecard JSON into a self-contained HTML readout.

Input: a scorecard JSON in the ``{baselines, arms}`` shape emitted by the
benchmark's ``score_quality.py`` / ``score_cross_language.py`` and documented in
``references/scorecard-json-shape.md``. Output: one standalone ``.html`` file
(dark theme, Chart.js via CDN, no build step) containing:

  - hero stats: arms scored, arms that beat their baseline, and a per-language split
  - a per-axis Win / Tie / Loss / n-a distribution bar chart
  - the full per-suite matrix — every arm, every axis (cell = ``gen``v``base`` + verdict)

Usage:
    python build_dashboard.py results-cross-language-scorecard.json
    python build_dashboard.py results-quality-scorecard.json -o docs/python.html \
        --title "Quality experiment" --subtitle "Three Python suites, three policies."

With no -o, writes next to the input as ``<input-stem>.html``.
"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

VERDICT_MARK = {"WIN": "✓", "LOSS": "✗", "TIE": "=", "N/A": "·"}
VERDICTS = ("WIN", "TIE", "LOSS", "N/A")


def fmt(v) -> str:
    """Format an axis value: ints plain, floats minimal, None as a dot."""
    if v is None:
        return "·"
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)


def axis_keys(arms: list[dict]) -> list[str]:
    """The axis keys, taken from the first present arm that carries them."""
    for a in arms:
        if a.get("present") and a.get("axes"):
            return list(a["axes"].keys())
    return []


def short_axis(key: str) -> str:
    """``A1_substring_match`` -> ``A1`` (the leading code), else the whole key."""
    head = key.split("_", 1)[0]
    return head if head else key


def axis_distribution(arms: list[dict], keys: list[str]) -> dict[str, dict[str, int]]:
    dist = {k: {v: 0 for v in VERDICTS} for k in keys}
    for a in arms:
        if not a.get("present"):
            continue
        for k in keys:
            verdict = a.get("axes", {}).get(k, {}).get("verdict", "N/A")
            dist[k][verdict if verdict in dist[k] else "N/A"] += 1
    return dist


def build_html(baselines: dict, arms: list[dict], title: str,
               subtitle: str, source_name: str) -> str:
    present = [a for a in arms if a.get("present")]
    better = [a for a in present if a.get("better")]
    keys = axis_keys(arms)
    langs = sorted({a.get("lang") for a in present if a.get("lang")})

    # hero cards: overall, then one per language (if the arms are tagged with one)
    cards = [("arms beat baseline", f"{len(better)}", f"/{len(present)}",
              "wins &gt; losses on the auto-countable axes")]
    for lang in langs:
        lp = [a for a in present if a.get("lang") == lang]
        lb = [a for a in lp if a.get("better")]
        cards.append((f"{lang} arms", f"{len(lb)}", f"/{len(lp)}", "beat baseline"))

    hero = "\n".join(
        f'<div class="hcard"><div class="lab">{html.escape(lab)}</div>'
        f'<div class="big">{big}<small>{small}</small></div>'
        f'<div class="desc">{desc}</div></div>'
        for lab, big, small, desc in cards
    )

    # axis distribution -> Chart.js stacked bars
    dist = axis_distribution(arms, keys)
    labels = [short_axis(k) for k in keys]
    series = {v: [dist[k][v] for k in keys] for v in VERDICTS}

    # per-suite matrix
    head_cells = "".join(f"<th>{short_axis(k)}</th>" for k in keys)
    rows = []
    for a in arms:
        name = html.escape(f"{a.get('repo','?')} / {a.get('policy','?')}")
        if not a.get("present"):
            empty = "".join('<td class="cell-na">·</td>' for _ in keys)
            rows.append(f'<tr><td class="wt">{name}</td>{empty}'
                        f'<td class="cell-na">—</td><td class="cell-na">absent</td></tr>')
            continue
        cells = []
        for k in keys:
            ax = a["axes"].get(k, {})
            verdict = ax.get("verdict", "N/A")
            cls = {"WIN": "cell-win", "LOSS": "cell-loss",
                   "TIE": "cell-tie", "N/A": "cell-na"}.get(verdict, "cell-na")
            cells.append(f'<td class="{cls}">{fmt(ax.get("gen"))}'
                         f'<span class="v">{fmt(ax.get("base"))}{VERDICT_MARK.get(verdict, "·")}</span></td>')
        wlt = f"{a.get('wins', 0)}/{a.get('losses', 0)}/{a.get('ties', 0)}"
        better_badge = ('<span class="badge b-green">yes</span>' if a.get("better")
                        else '<span class="badge b-red">no</span>')
        rows.append(f'<tr><td class="wt">{name}</td>{"".join(cells)}'
                    f'<td>{wlt}</td><td>{better_badge}</td></tr>')
    matrix_rows = "\n".join(rows)

    return _TEMPLATE.format(
        title=html.escape(title),
        subtitle=html.escape(subtitle),
        hero=hero,
        chart_labels=json.dumps(labels),
        chart_win=json.dumps(series["WIN"]),
        chart_tie=json.dumps(series["TIE"]),
        chart_loss=json.dumps(series["LOSS"]),
        chart_na=json.dumps(series["N/A"]),
        n_arms=len(present),
        head_cells=head_cells,
        matrix_rows=matrix_rows,
        source=html.escape(source_name),
    )


_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         background: #0f1117; color: #e1e4e8; padding: 40px; }}
  .wrap {{ max-width: 1240px; margin: 0 auto; }}
  h1 {{ font-size: 26px; font-weight: 600; color: #fff; margin-bottom: 6px; }}
  .subtitle {{ color: #8b949e; margin-bottom: 32px; font-size: 14px; max-width: 1040px; line-height: 1.6; }}
  code {{ font-family: 'SF Mono','Fira Code',monospace; background: #1f2937; padding: 1px 5px;
         border-radius: 3px; font-size: 0.92em; color: #e3b341; }}
  section {{ margin-bottom: 44px; }}
  section > h2 {{ font-size: 18px; font-weight: 600; color: #fff; margin-bottom: 16px;
                 padding-bottom: 8px; border-bottom: 1px solid #30363d; }}
  .hero {{ display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 40px; }}
  .hcard {{ flex: 1; min-width: 180px; border: 1px solid #30363d; border-radius: 12px;
           padding: 20px 22px; background: #161b22; text-align: center; }}
  .hcard .lab {{ font-size: 12px; font-weight: 700; text-transform: uppercase;
                letter-spacing: 1px; margin-bottom: 12px; color: #c9d1d9; }}
  .hcard .big {{ font-size: 48px; font-weight: 700; line-height: 1; color: #3fb950; }}
  .hcard .big small {{ font-size: 22px; color: #8b949e; font-weight: 500; }}
  .hcard .desc {{ font-size: 12px; color: #8b949e; margin-top: 10px; }}
  .cbox {{ position: relative; height: 300px; border: 1px solid #30363d; border-radius: 10px;
          background: #161b22; padding: 16px; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
  th, td {{ border: 1px solid #30363d; padding: 7px 9px; text-align: center; }}
  th {{ background: #161b22; color: #8b949e; font-weight: 600; font-size: 12px; }}
  td.wt {{ text-align: left; font-family: 'SF Mono','Fira Code',monospace; font-size: 12px;
          color: #c9d1d9; background: #11151c; white-space: nowrap; }}
  td .v {{ display: block; font-size: 10px; color: #8b949e; }}
  .cell-win  {{ background: rgba(63,185,80,0.14); color: #3fb950; }}
  .cell-loss {{ background: rgba(248,81,73,0.13); color: #f85149; font-weight: 600; }}
  .cell-tie  {{ color: #687078; }}
  .cell-na   {{ color: #444c56; }}
  .badge {{ font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 10px; }}
  .b-green {{ background: rgba(63,185,80,0.16); color: #3fb950; }}
  .b-red   {{ background: rgba(248,81,73,0.16); color: #f85149; }}
  .footer {{ color: #586069; font-size: 12px; margin-top: 36px; border-top: 1px solid #30363d;
            padding-top: 16px; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>{title}</h1>
  <p class="subtitle">{subtitle}</p>

  <div class="hero">{hero}</div>

  <section>
    <h2>Per-axis: Win / Tie / Loss across {n_arms} arms</h2>
    <div class="cbox"><canvas id="axisChart"></canvas></div>
  </section>

  <section>
    <h2>Per-suite matrix — every arm, every axis</h2>
    <table>
      <thead><tr><th>repo / policy</th>{head_cells}<th>W/L/T</th><th>better</th></tr></thead>
      <tbody>{matrix_rows}</tbody>
    </table>
  </section>

  <div class="footer">
    Generated from <code>{source}</code> by the <code>results-dashboard</code> skill.
    Each cell is <code>gen</code> over <code>base</code> with ✓ win / ✗ loss / = tie / · n-a.
  </div>
</div>
<script>
new Chart(document.getElementById('axisChart'), {{
  type: 'bar',
  data: {{ labels: {chart_labels},
    datasets: [
      {{ label: 'win',  data: {chart_win},  backgroundColor: '#3fb950' }},
      {{ label: 'tie',  data: {chart_tie},  backgroundColor: '#444c56' }},
      {{ label: 'loss', data: {chart_loss}, backgroundColor: '#f85149' }},
      {{ label: 'n/a',  data: {chart_na},   backgroundColor: '#21262d' }},
    ] }},
  options: {{ responsive: true, maintainAspectRatio: false,
    scales: {{ x: {{ stacked: true, ticks: {{ color: '#8b949e' }}, grid: {{ color: '#21262d' }} }},
               y: {{ stacked: true, ticks: {{ color: '#8b949e' }}, grid: {{ color: '#21262d' }},
                    title: {{ display: true, text: 'arms', color: '#8b949e' }} }} }},
    plugins: {{ legend: {{ labels: {{ color: '#c9d1d9', boxWidth: 12 }} }} }} }}
}});
</script>
</body>
</html>
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scorecard", help="Path to a {baselines, arms} scorecard JSON.")
    ap.add_argument("-o", "--out", default=None,
                    help="Output HTML path. Default: <scorecard-stem>.html next to the input.")
    ap.add_argument("--title", default=None,
                    help="Page title. Default: derived from the scorecard filename.")
    ap.add_argument("--subtitle", default="",
                    help="One-line description shown under the title.")
    args = ap.parse_args()

    src = Path(args.scorecard)
    data = json.loads(src.read_text())
    baselines = data.get("baselines", {})
    arms = data.get("arms", [])
    if not arms:
        ap.error(f"{src} has no 'arms' array — is it a {{baselines, arms}} scorecard JSON?")

    title = args.title or src.stem.replace("results-", "").replace("-", " ").replace("_", " ").strip().title()
    out = Path(args.out) if args.out else src.with_suffix(".html")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_html(baselines, arms, title, args.subtitle, src.name))
    print(f"wrote {out}  ({sum(1 for a in arms if a.get('present'))} arms, "
          f"{sum(1 for a in arms if a.get('better'))} beat baseline)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
