# Scorecard JSON shape

`build_dashboard.py` consumes a single JSON object with two top-level keys:
`baselines` and `arms`. This is exactly what the benchmark's `score_quality.py`
and `score_cross_language.py` write, and matches what the `test-quality` skill's
`score.py` produces per suite.

```jsonc
{
  "baselines": {
    "<repo>": {
      "lang": "js",              // optional; present for the cross-language scorer
      "test_count": 117,
      "test_loc": 1430,
      "A1_substring_match": 25,  // raw per-axis counts for the human baseline
      "A2_private_symbol": 2,
      "B1_fixed_vector": 28,
      "D1_loc_per_test": 14.57,
      "D2_param_ratio": 0.0
      // …one entry per measured axis
    }
  },
  "arms": [
    {
      "repo": "express",
      "policy": "oneshot",       // oneshot | iter2 | iter20
      "present": true,
      "lang": "js",              // optional; drives the per-language hero split
      "test_count": 117,
      "test_loc": 1073,
      "c2_mock_framework": 0,
      "axes": {
        "A1_substring_match": { "gen": 0, "base": 25, "verdict": "WIN" },
        "B1_fixed_vector":    { "gen": 3, "base": 28, "verdict": "LOSS" },
        "D2_param_ratio":     { "gen": 0.179, "base": 0.0, "verdict": "WIN" }
        // …one entry per scored axis; gen/base may be null, verdict may be "N/A"
      },
      "wins": 4, "losses": 1, "ties": 3,
      "better": true             // wins > losses
    },
    { "repo": "express", "policy": "iter2", "present": false }
  ]
}
```

## What the renderer reads

- **Hero cards** — `len(arms where present)`, `len(arms where better)`, and, when
  arms carry `lang`, a `<better>/<total>` card per language.
- **Axis columns** — the keys of `axes` on the first `present` arm (so the matrix
  adapts to whichever axes the scorer measured). Each axis is labelled by its
  leading code (`A1_substring_match` → `A1`).
- **Verdicts** — `WIN` / `LOSS` / `TIE` / `N/A` per axis cell; `better` for the
  row badge; `wins`/`losses`/`ties` for the W/L/T column.

## Edge cases the renderer tolerates

- `present: false` arms → rendered as a single `absent` row.
- `gen` / `base` of `null` → rendered as `·`.
- A `verdict` outside the four known values → treated as `N/A`.
- Missing `baselines` → hero/axis logic still works off `arms` alone.
