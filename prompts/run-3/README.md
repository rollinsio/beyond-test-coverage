# Run 3 prompt set — cross-language (JS/TS + Go)

Run 3 extends the benchmark beyond Python to validate that
scorecard-anchored prompting generalizes. Six repos, three policies:

- **JS/TS:** `express` (Mocha + node:assert + supertest),
  `jsonwebtoken` (Mocha + Chai + sinon), `zod` (Vitest, monorepo).
- **Go:** `chi` (httptest router), `gjson` (pure parse + fuzz),
  `golang-jwt` (crypto signing).
- **Policies:** `oneshot`, `iter2`, `iter20` (same semantics as Run 2).

The prompt parts (`common_header`, `quality_contract`,
`quality_scorecard`, and the three policy bodies) are language-
parameterized; `scripts/setup_run3.py` substitutes per-repo commands
(`{RUN_CMD}`, `{SCORE_CMD}`, `{DELETE_CMD}`, …) and materializes a
`.rex_prompt.md` into each `wt-r3-<policy>` worktree.

The defining difference from Run 2's prompts: self-scoring is a single
`score.py --lang <L> --baseline …` call (the multi-language scorer),
not the Python-specific grep/wc recipes.
