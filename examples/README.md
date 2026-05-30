# Example readouts

Static previews of the interactive dashboards in [`../docs/`](../docs/), captured
during the experiment. Open the live HTML for the per-axis charts, the worktree
selector, and hover detail.

| Preview | Live dashboard | What it shows |
|---|---|---|
| [`cross-language-results.png`](cross-language-results.png) | [`docs/cross-language-results.html`](../docs/cross-language-results.html) | The cross-language result: 18/18 JS/TS + Go arms beat their human baseline, with the one-shot-vs-iterate split and the full per-suite matrix. |
| [`python-results.png`](python-results.png) | [`docs/python-results.html`](../docs/python-results.html) | The Python decomposition: coverage-driven `2/9` → ablation `8/9` → quality `9/9`, isolating the prompt effect from the model effect. |

Regenerate the base readout from any scorecard JSON with the bundled
[`results-dashboard`](../.claude/skills/results-dashboard/) skill:

```bash
python .claude/skills/results-dashboard/scripts/build_dashboard.py \
    results-cross-language-scorecard.json -o docs/cross-language-results.html
```
