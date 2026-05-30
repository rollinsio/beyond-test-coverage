# beyond-test-coverage

**Are LLM-generated tests better or worse than the ones humans write?**
The only honest way to answer is to put numbers on it — and *code
coverage* is a vanity metric that doesn't. 100%-covered suites are
routinely brittle, over-mocked, and noisy; coverage tells you a line
*ran*, not that a test would *catch the regression that breaks it*.

`beyond-test-coverage` measures the thing coverage can't: **test
quality**. Point it at a repository and it regenerates the test suite
from the source through a **read → build → evaluate** loop, optimizing
for the qualities that make a suite actually load-bearing:

- **Anti-fragility** — tests that survive a benign refactor. No
  asserting on error-message *substrings*, no recomputing the expected
  value with the same code under test, no reaching into private
  internals, no `||`-joined "passes if any of these" assertions.
- **Rigor** — assert against *known-good fixed values* (precomputed
  vectors, inline snapshots), cover the boundaries, and exercise real
  behavior end-to-end rather than re-deriving it.
- **Mocking discipline** — zero hand-rolled mocks of the unit under
  test. Drive the real thing through framework primitives (supertest,
  `httptest`, fake timers) or real objects; mock only true external
  boundaries.
- **Reuse & efficiency** — fold repetition into table-driven /
  parametrized cases instead of copy-paste; fewer lines per test.
- **Correctness** — every test passes, and every non-obvious assumption
  is verified against the real library, not guessed.
- **Coverage as a floor, not a target** — never regress it, never chase
  it.

An **evaluate** function (the [`test-quality`](.claude/skills/test-quality/)
scorer) measures each of these axes on the generated suite *and* on the
original, and reports a win/loss/tie per axis. If the suite hasn't beaten
the baseline — or isn't green — the loop reads, rebuilds, and re-evaluates.
Through that loop the suite improves not just in coverage but in
**quality**: the result is a test suite that is **stronger, more robust,
and less noisy** than the surface it replaced.

## Does it actually work?

To find out, we took a set of widely-used open-source libraries with
**exceptional, maintainer-written test suites**, measured their baseline
on every axis, **deleted every test**, and regenerated the suite from the
source under increasing iteration budgets (a single pass, up to
iterate-until-it-stops-improving) — scoring each generated suite against
the human original. Every round's findings fed back into the prompts and
the scorer, hardening the tool with each pass.

Nine libraries, three languages, the strongest test suites we could find:

| Library | Lang | What it is | Beat the human baseline? |
|---|---|---|:--:|
| `pallets/itsdangerous` | Python | signing / serialization | ✅ |
| `encode/httpx` | Python | HTTP client | ✅ |
| `psf/requests` | Python | HTTP client | ✅ |
| `expressjs/express` | JS | web framework | ✅ |
| `auth0/node-jsonwebtoken` | JS | JWT | ✅ |
| `colinhacks/zod` | TS | schema validation | ✅ |
| `go-chi/chi` | Go | HTTP router | ✅ |
| `tidwall/gjson` | Go | JSON query | ✅ |
| `golang-jwt/jwt` | Go | JWT | ✅ |

### Results

The headline is the gap between *chasing coverage* and *chasing quality*.
When the loop was pointed at **coverage**, the regenerated suites beat the
human baseline on only **2 of 9** runs — they hit coverage parity and
stopped. Re-aimed at the **quality scorecard**, they won **every** run:

```
Regenerated suites that beat the human-written test suite
──────────────────────────────────────────────────────────
Coverage-driven   (Python)   ██░░░░░░░░   2 / 9     22%
Quality-driven    (Python)   ██████████   9 / 9    100%
Quality-driven    (JS / TS)  ██████████   9 / 9    100%
Quality-driven    (Go)       ██████████   9 / 9    100%
```

Across **27 quality-driven runs** (9 libraries × 3 iteration budgets),
**every one beat its human-written baseline** on the auto-countable axes —
9/9 on Python, 18/18 across JS/TS and Go. The wins are consistent and
structural: the generated suites are dramatically **more LOC-efficient**
and **more parametrized** than every baseline, carry **zero fragile
substring/private/recomputed assertions**, and use **no hand mocks** of
the code under test — while holding or raising coverage.

Two honest caveats the numbers also surfaced:

- **A single pass already wins the quality axes** for every library — but
  it tends to ship 1–4 self-authored failing tests. The *iteration* budget
  is what makes the suite green and widens the margin. Quality and
  shippability are different milestones.
- The one axis the generated suites sometimes lose is **fixed-vector
  count**, because we score it as an absolute count that scales with suite
  size and competes with LOC-efficiency. (Re-shaping it into a per-test
  *ratio* is the next change — see [`CHANGELOG.md`](CHANGELOG.md).)

**Explore the numbers yourself:**

- [`docs/run3-results.html`](docs/run3-results.html) — interactive
  dashboard for the cross-language run (JS/TS + Go): per-axis win/tie/loss
  across all 18 runs, the one-shot-vs-iterate split, and the full
  per-suite matrix.
- [`docs/scorecard-results.html`](docs/scorecard-results.html) — the
  Python dashboard, including the decomposition of *why* coverage-driven
  scored 2/9 and quality-driven scored 9/9.
- [`FINDINGS.md`](FINDINGS.md) — the full running analysis.

## The quality scorecard

The criteria above are a multi-axis rubric; the scorer auto-counts the
mechanical ones and leaves the judgement ones to review:

| Group | Axes |
|---|---|
| **A — anti-fragility** | A.1 error-substring asserts · A.2 private-symbol access · A.3 tautological readbacks · A.4 recomputed expected values · A.5 `‖`-joined matches · A.6 hand-coded charsets |
| **B — rigor** | B.1 fixed-vector asserts / snapshots · B.2 boundary coverage · B.3 framework-primitive integration |
| **C — mocking** | C.1 hand mocks of the unit (target 0) · C.2 framework primitives (legitimate) |
| **D — reuse** | D.1 LOC per test · D.2 parametrize ratio · D.3 fixture/inheritance reuse |
| **E — correctness** | E.1 all green · E.2 out-of-band-verified assumptions · E.3 mutation sensitivity |
| **F — coverage floor** | F.1 line · F.2 branch — non-regression only |

[`scripts/...score.py`](.claude/skills/test-quality/scripts/score.py)
auto-counts A.1/A.2/A.4/A.5, B.1, C.1/C.2, D.1/D.2 across Python, JS/TS,
and Go and prints the head-to-head Win/Loss/Tie tally. The rest are
review-time judgement calls.

## Use it on your own suite

The reusable artifact is the bundled [`test-quality`](.claude/skills/test-quality/)
Claude Code skill — the scorer, the anti-fragility contract, and the
read→build→evaluate loop definition. A clone is self-contained, so the
skill is auto-discovered when you open the repo in Claude Code. Score any
suite directly:

```bash
python .claude/skills/test-quality/scripts/score.py \
    --tests path/to/tests --baseline path/to/old_tests --lang python|js|go
```

## Repository layout

```
.
├── .claude/skills/test-quality/  # the reusable scorer + rubric + contract
├── docs/                         # interactive results dashboards
├── prompts/                      # the prompt sets that drive generation
├── scripts/                      # setup, scoring, and aggregation harness
├── configs/                      # per-repo coverage config
├── reports/ · runs/              # preserved per-run reports & inventories
├── results-*.{json,md}           # the scored results behind the dashboards
├── FINDINGS.md                   # running analysis (what we learned)
└── CHANGELOG.md                  # how the rubric & prompts evolved per round
```

The nine libraries under test are each cloned locally into their own
git-ignored directory; **they are not redistributed here** and remain
under their own licenses. Generated suites live on per-run branches inside
those clones.

## How the experiment is organized

The work proceeded in rounds; each round froze a prompt set, ran it, and
fed its findings into the next. They're referred to as **Run 1/2/3** in
the logs and dashboards:

- **Run 1 — the coverage-driven baseline.** Python, prompts aimed at
  coverage %. Beat the human baseline on 2/9 (it stopped at parity). This
  is the control that motivated everything else.
- **Run 2 — quality-driven, Python.** Same repos, prompts re-aimed at the
  quality scorecard. 9/9. (A model upgrade contributed a marginal top-up;
  the prompt redesign did the heavy lifting — see FINDINGS §10.)
- **Run 3 — quality-driven, cross-language.** New JS/TS + Go libraries,
  same approach. 18/18 — the result generalizes beyond Python.

Each round's prompts live frozen under `prompts/run-N/`; `CHANGELOG.md`
records the rubric/prompt delta and `FINDINGS.md` the evidence. Rubric
changes themselves queue under CHANGELOG `[Unreleased]` for the next round.

## License

[MIT](LICENSE) © Michael Rollins. The third-party repositories under test
are *not* included in this repo (each is cloned locally and git-ignored)
and remain under their own respective licenses.
