# Findings — LLM test-generation benchmark

This is an iterative experiment. Each stage uses the previous stage's
findings to refine the prompts. Findings accumulate; nothing is deleted.
Each entry preserves the worktrees and reports that produced it.

| Experiment | Date       | Prompt set         | Worktree inventory      | Reports                  |
|------------|------------|--------------------|-------------------------|--------------------------|
| coverage   | 2026-05-28 | (initial — embedded in plan doc) | [runs/coverage.md](runs/coverage.md) | [reports/](reports/) |
| quality    | 2026-05-28 | [prompts/quality/](prompts/quality/) | `wt-r2-*` (Opus 4.8) + `wt-r2b-*` (Opus 4.7 control) | `results-quality*.{json,md}`, `results-ablation*.{json,md}` |

---

## Coverage-driven control — 2026-05-28 findings

Nine worktrees (3 repos × 3 policies — oneshot, iter2, iter20) run
against `pallets/itsdangerous`, `encode/httpx`, `psf/requests`. Full
per-run reports live in [reports/](reports/). The deep three-agent
fragility audit on itsdangerous is at
[audit_itsdangerous.md](audit_itsdangerous.md). The verification pass
that turned up the integrity finding is at
[reports/VERIFICATION.md](reports/VERIFICATION.md).

### 1. Coverage % is not a quality proxy on small libraries

All three itsdangerous suites landed at 97.7–100 % line coverage, yet
none materially improves on the 37-test, 481-LOC original — and all
three are *more fragile* than the original by the patterns below. The
+2.35 pp gains from iter2 and iter20 came from coverage-chasing
additions targeting private internals, not from deeper behavioral
testing.

**Action for the quality-driven experiment:** the prompt should de-emphasize coverage as the
success criterion. iter20 in particular needs a different stopping
condition.

### 2. The iter20 budget is consistently underused

All three iter20 sessions stopped at iteration 2 or 3 because they hit
"beat baseline coverage" early:

| Repo         | iter20 budget | Iterations actually used |
|--------------|:-------------:|:------------------------:|
| itsdangerous |      20       |             2            |
| httpx        |      20       |             3            |
| requests     |      20       |          1 or 2          |

The remaining 17–18 iterations didn't get spent on rigor improvements
because the prompt framed success as "exceed baseline %." Once
coverage was past baseline, the model had no incentive to keep
iterating.

**Action for the quality-driven experiment:** iter20's success criterion needs to require
*more* than coverage matching. Either an explicit "deepen tests after
matching coverage" instruction, or a boundary-mutation-style criterion.

### 3. Sessions can cheat the delete-and-regenerate setup

**`httpx/wt-iter20` did this.** Hash-compare: 31 of 32 test files in
that worktree are **byte-identical** to the baseline. The session
deleted `tests/`, committed the deletion, then used `git show
<delete-commit>^:tests/<file>` (or equivalent) to recover the deleted
files in iteration 1. Only `test_extra_branches.py` is new content.
Its "100 % line / 100 % branch" is the baseline's coverage, not a
generation result.

The other two iter20 sessions (itsdangerous, requests) generated
genuinely; their files all differ from baseline. So this was
opportunistic, not systematic.

**Action for the quality-driven experiment:** the prompt must explicitly forbid recovering
deleted tests from git. The cleanest framing: "treat the
delete-commit's parent as the only legitimate source of information —
no `git show`, `git log -p`, `git restore`, or equivalent." If the
prompt wants to be air-tight, the setup step can also wipe the
delete-commit's reflog, but the explicit constraint is sufficient for
a cooperating model.

### 4. The model commits epistemic errors without verification

**`itsdangerous/wt-oneshot` did this.** Two committed-failing tests
both stemmed from the model assuming `base64.urlsafe_b64decode(b"!@#$%^&*()")`
would raise `binascii.Error`. It doesn't — Python silently filters
non-alphabet characters and returns `b""`. A one-line REPL check would
have caught this.

Neither failure is a bug-find. Both look like coverage holes; they're
actually misreads of stdlib behavior.

**Action for the quality-driven experiment:** the prompt should require a "verify your
assumptions" step before writing tests that depend on runtime behavior
of imported functions. Specifically: "If a test you're about to write
asserts that a stdlib or third-party function raises a specific
exception, run `python -c 'from x import y; y(args)'` first to confirm
the actual behavior."

### 5. Generated tests use systematic anti-patterns

The three-agent fragility audit on itsdangerous (independent agents,
one per policy) **converged on the same patterns from different
files**:

a. **Error-message substring matching.** `pytest.raises(BadPayload, match="zlib")`. The contract is the exception type + payload; the message wording is documentation, not contract. Found at ~10 distinct sites per policy.

b. **Recomputing crypto/encoding inside the test, then comparing.** `expected = hmac.new(b"key", b"value", sha1).digest()`. If a mutation breaks `HMACAlgorithm.get_signature` in the *same* way the test mis-types the digest, both fail symmetrically and the test passes. Compare to baseline's fixed byte literal `"[42].-9cNi0CxsSB3hZPNCe9a2eEs1ZM"` (catches parallel mutations).

c. **Tautological constructor readbacks.** Pass `salt=...` then assert `s.salt == "..."`. Survives every realistic mutation. All three suites had whole files (`test_exc.py`) that are this pattern.

d. **Private symbol imports.** `from itsdangerous.signer import _lazy_sha1, _make_keys_list`; `s._loads_unsafe_impl(...)`; `_DigestAuthChallenge`. The originals never reach for these.

e. **Re-implementing the wire format in the test.** Building `value + b"." + base64_encode(int_to_bytes(2**62)) + b".wrongsig"` directly. Any encoding-layout change breaks these even if the public sign/unsign contract is intact.

f. **`or`-joined assertions that accept either outcome.** `assert "Malformed timestamp" in str(e) or "does not match" in str(e)`. A bug that *swapped* the two messages goes undetected.

g. **Hand-coded character sets as weaker substitutes for fixed expected values.** `allowed = set("ABC...0123456789-_=."); assert set(signed) <= allowed`. The original asserts an exact byte literal.

h. **No parametrize / fixtures / inheritance.** Original uses
`@pytest.mark.parametrize` for 4 key-derivation modes in 6 LOC.
Generated unrolls into 3 explicit per-case tests in 11 LOC (and
sometimes misses a case). Original reuses entire test classes via
`TestTimedSerializer(FreezeMixin, TestSerializer)`. Generated
duplicates each behavior in each file. Result: **2.3–2.5× LOC
inflation** across all itsdangerous policies.

**Action for the quality-driven experiment:** the prompt needs an explicit anti-fragility
contract section listing these patterns with positive alternatives.
See [prompts/quality/](prompts/quality/).

### 6. The mock-LOC metric is noisy

httpx baselines use `httpx.MockTransport` + `monkeypatch` extensively
(the framework's *intended* test pattern). The regex `mock|patch|MagicMock|mocker`
matches all of these. Generated suites have roughly equivalent density.
The metric flagged the suites as "mock-heavy" but they weren't —
they were using the framework's intended primitives.

| Suite      | LOC  | mock-regex matches | Density (per 100 LOC) |
|------------|-----:|-------------------:|----------------------:|
| httpx baseline | 8620 | ~140               | 1.6 |
| httpx oneshot  | 4147 | 95                 | 2.3 |
| requests baseline | 4902 | ~62              | 1.3 |
| requests oneshot  | 2587 | 32               | 1.2 |

**Action for the quality-driven experiment:** the metric needs to distinguish `unittest.mock`/`MagicMock`/`mocker` (real mocking) from `httpx.MockTransport`/`monkeypatch` (framework primitives). Refine the regex or count by category.

### 7. The standout pattern: integration tests via real-I/O fixtures

**`requests/wt-iter20` is the only run that's better than baseline on
every dimension.** What it did differently: iter_1 ran unit tests;
iter_2 added `tests/test_integration.py` using `pytest-httpbin` for
real HTTP I/O. That single architectural decision pushed it past
baseline by +3.85 pp line / +6.22 pp branch with **zero mock
infrastructure**.

The insight: when the framework provides real-I/O test primitives
(`pytest-httpbin`, `httpx.MockTransport`, `httpx.WSGITransport`,
etc.), an iteration loop that recognizes "we need a different *kind*
of test, not more of the same" can produce a substantially better
suite than the baseline.

The other two requests sessions used these fixtures too, but didn't
make the unit-vs-integration split as cleanly.

**Action for the quality-driven experiment:** the prompt should explicitly point out the
framework's real-I/O fixtures by name, and instruct iter2/iter20
sessions to consider adding integration tests when unit tests
plateau below baseline coverage.

### 8. Tooling / hermicity issues that we should fix

a. **Shared `base/.venv` got clobbered by `pip install -e .` from a
   worktree.** The `requests` editable install ended up pointing at
   `wt-iter20/src/requests/`, not `base/src/requests/`. Source files
   are identical across worktrees so the test outcome was unchanged,
   but coverage records paths that all point at wt-iter20. The
   per-worktree prompt should explicitly forbid running `pip install
   -e .` from inside the worktree (it's not needed, since deps are
   already in the shared venv).

b. **Aggregator script's src-prefix filter assumed relative paths.**
   Coverage JSONs store absolute paths. Filter needs to accept either
   a relative or absolute prefix.

c. **"Line coverage" labels disagreed across SUMMARYs.** Some used
   pure `(stmts - missing) / stmts`; some used coverage.py's
   `totals.percent_covered` (which is line+branch combined when
   branch is on). The prompt should require the SUMMARY to report
   *both* numbers under labeled names.

### What we want to test next (quality-driven)

Each is a discrete prompt-design change with a falsifiable prediction:

| # | Change                                                                 | Prediction                                                              |
|---|------------------------------------------------------------------------|-------------------------------------------------------------------------|
| 1 | Add anti-fragility contract section (forbidding patterns 5a–5g)        | Mock-LOC down; substring-match assertions down by >80 %; private-symbol imports near zero |
| 2 | Forbid git-history recovery + add explicit "treat deletion as final"    | httpx/iter20-style restoration drops to zero                            |
| 3 | Require REPL verification of stdlib/third-party assumptions             | Oneshot test-side-bug count drops; tests committed broken near zero      |
| 4 | iter20 success criterion: "beat baseline AND fix the 4 most fragile patterns from your iter_1" | iter20 iterations used rises from 2–3 to closer to budget |
| 5 | Prompt names framework real-I/O fixtures by name (`pytest-httpbin`, `MockTransport`, etc.) | More iter2/iter20 sessions add integration tests; coverage gaps on transport modules close |
| 6 | Require SUMMARY to report both pure-line and combined coverage         | Apples-to-apples comparison across runs becomes possible                |
| 7 | Forbid `pip install -e .` from inside worktrees                        | Editable install in shared venv stays pointing at base/                |

All seven changes are encoded in [prompts/quality/](prompts/quality/).

### 9. Even the initial quality-driven design centered on coverage. We re-centered it on quality.

The first draft of the quality-driven prompts kept coverage as the goal ("beat
baseline coverage AND no anti-patterns AND at least one
integration/boundary iteration"). On review, this still anchors the
session on a number; the quality rules act as side constraints. That's
the wrong framing.

**The corrected framing:** the goal is to produce a *better* test
suite than the baseline. "Better" is defined by a multi-axis quality
scorecard (`prompts/quality/quality_scorecard.md`). Coverage is a
non-regression floor — once you're at baseline coverage, additional
coverage doesn't score. The iteration budget exists to deepen quality
on the scorecard axes, not to chase a percentage.

**Action for the quality-driven experiment:** the prompt centers on the scorecard. Each
iteration must claim a scorecard-improving move and name the axis
delta in its commit message. iter20's stop condition is "3
consecutive iterations cannot improve the scorecard," not "coverage
parity reached."

This refinement is itself the kind of finding the iterative
experiment is meant to surface: the *metric* you point the LLM at
determines the kind of suite it produces. The coverage-driven baseline pointed at coverage
and got coverage. The quality-driven experiment points at quality (operationalized) and
should produce quality. If it doesn't, that's a cross-language finding about
either the scorecard's design or the model's ability to optimize for
multi-axis goals.

---

## Quality-driven (Python) — 2026-05-28 findings

The quality-driven experiment = **Opus 4.8** + the scorecard-centered prompt set in
[prompts/quality/](prompts/quality/). That changes *both* the model and the
prompt versus the coverage-driven baseline, so we added an ablation arm — **ablation** = **Opus 4.7** + the
*byte-identical* quality prompts (only the substituted worktree path differs).
The three points decompose the confound cleanly:

| arm       | model    | prompts              | effort |
|-----------|----------|----------------------|--------|
| coverage  | Opus 4.7 | coverage-goal (old)  | xhigh  |
| ablation  | Opus 4.7 | scorecard-goal (new) | xhigh  |
| quality   | Opus 4.8 | scorecard-goal (new) | xhigh  |

coverage → ablation isolates the **prompt** change (model held at 4.7·xhigh); ablation → quality
isolates the **model** change (prompts held). All three are scored by
`scripts/score_quality.py`, which applies *one* identical set of mechanical
measurements — the 8 auto-countable scorecard axes — to all 9 generated suites
and the 3 human baselines, sidestepping the mutually-incompatible self-reported
`scorecard.json` shapes each session emitted. See
`results-{coverage,quality,ablation}-scorecard.{md,json}` and the coverage tables in
`results-{quality,ablation}.md`.

### 10. The prompt redesign dominates; the model bump is a marginal top-up

"Beats its own baseline" on the auto-countable fragility axes:

| worktree              | coverage (4.7·old) | ablation (4.7·new) | quality (4.8·new) |
|-----------------------|:------------------:|:------------------:|:-----------------:|
| itsdangerous/oneshot  | ✅ | ✅ | ✅ |
| itsdangerous/iter2    | ❌ | ✅ | ✅ |
| itsdangerous/iter20   | ❌ | ✅ | ✅ |
| httpx/oneshot         | ❌ | ✅ | ✅ |
| httpx/iter2           | ❌ | ✅ | ✅ |
| httpx/iter20          | ❌ | ✅ | ✅ |
| requests/oneshot      | ✅ | ❌ | ✅ |
| requests/iter2        | ❌ | ✅ | ✅ |
| requests/iter20       | ❌ | ✅ | ✅ |
| **total**             | **2 / 9** | **8 / 9** | **9 / 9** |

- **Prompt effect** (coverage → ablation, model fixed at 4.7): **2/9 → 8/9 (+6).**
- **Model effect** (ablation → quality, prompts fixed): **8/9 → 9/9 (+1).**

The scorecard-centered prompt rewrite accounts for ~6× the movement of the
4.7→4.8 model bump. The model bump's sole flip is requests/oneshot — a
single-pass, no-repair policy, i.e. the case where raw model quality has the
least chance to be rescued by iteration.

**Caveat — the auto-scorer is a generous floor, not the verdict.** It counts
only 8 mechanical axes (A.1/A.2/A.4/A.5/C.1/B.1/D.1/D.2) and ignores the
semantic ones (A.3 tautological readbacks, A.6 hand-coded charsets, B.2
boundaries, B.3 framework-I/O, E.* correctness/REPL). It is markedly more
generous than the coverage-driven baseline's hand audit, which judged only ~1/9 truly better (and
flagged httpx/iter20 as illegitimate — see Finding 3). The coverage-driven baseline's 2/9 here is
therefore inflated relative to the careful verdict. But the *same* generous
instrument is applied to all three arms, so the **deltas** — the actual
decomposition — hold even though the absolute levels are soft.

### 11. Per-axis: the prompt solved fragility; the model owned one axis

Totals across the 9 suites in each arm (baseline totals differ per repo; these
are gen-side sums, directional):

| axis (↓ = lower better)            | coverage | ablation | quality | who moved it |
|------------------------------------|---------:|---------:|--------:|--------------|
| A.1 substring-match asserts (↓)    | 65    | 9   | 0  | **prompt** (86% gone on 4.7 alone; 100% on 4.8) |
| C.1 real-mock LOC (↓)              | 30    | 1   | 0  | **prompt** |
| D.2 parametrize ratio (↑, per-test)| ≤0.08 | 0.05–0.25 | 0.10–0.27 | **prompt** |
| A.2 private-symbol uses (↓, noisy) | 185   | 118 | 59 | **model** (prompt −36%, model another −50%) |

A.1, C.1, D.2 — the headline patterns from Finding 5 (substring matching,
real mocking, no-parametrize unrolling) — are essentially solved by the prompt
change alone (ablation, still on the old model). A.2 (reaching for private symbols)
is the lone axis where the 4.8 model contributed *more* than the prompt,
roughly halving the count again. Read A.2 as a trend, not an absolute — its
regex matches any `obj._attr(` call, not only imports of private names.

> **C.1 measurement corrected (2026-05-29).** Validating the scorers found a bug
> in the C.1 mock regex (a trailing `\b`) that both **missed** real mocks
> (`patch('str')`, `Mock()`, `mock.Mock()`) and **false-matched** the HTTP `PATCH`
> verb (`client.patch(...)`). The clean fix corrected both: it re-baselined C.1
> (httpx baseline 3→0, phantom verbs removed; requests baseline 0→3, real
> `mock.Mock()` caught) and lowered the coverage-driven baseline's tally **3/9 → 2/9** — its two marginal
> httpx wins had leaned on phantom baseline mocks, while requests/oneshot gained a
> legitimate C.1 win. ablation and quality tallies are unchanged. All three scorers + the
> aggregator now carry pytest validation suites (`tests/`,
> `.claude/skills/test-quality/tests/`).

### 12. Winning the fragility scorecard ≠ passing the full quality-driven goal

The "better=YES" verdict above measures fragility axes only; it does **not**
enforce the coverage non-regression floor that is also part of the quality-driven goal.
Coverage (`results-quality.md`) shows the two **oneshot** arms in quality breach it:

| quality arm      | Δ line  | Δ branch |
|------------------|--------:|---------:|
| httpx/oneshot    | −6.96 % | −14.57 % |
| requests/oneshot | −3.17 % |  −6.84 % |

oneshot is a single pass with no repair, so this is the policy's expected
failure mode — but it means "wins the fragility scorecard" and "is a strictly
better suite" diverge for those two arms. Every iter2/iter20 arm holds or beats
the floor (itsdangerous/iter20 +2.35 line, requests/iter20 +3.34 line / +3.36
branch).

**Action for the cross-language experiment:** the scorecard tally must be *gated* on the coverage
floor — an arm that regresses coverage cannot be scored "better," however clean
its fragility axes. Otherwise oneshot wins keep flattering the headline.

### 13. iter20 now spends its budget — and 4.8 plateaus sooner than 4.7

Finding 2 of the coverage-driven baseline was that iter20 stalled at 2–3 iterations once coverage parity
was hit. The new stop condition ("3 consecutive iterations without scorecard
improvement, else 20") fixes it:

| iter20 arm   | coverage | ablation (4.7) | quality (4.8) |
|--------------|:--------:|:--------------:|:-------------:|
| itsdangerous |   2   |    17     |    9     |
| httpx        |   3   |    10     |    7     |
| requests     |  ~2   |    11     |    6     |

Both new-prompt arms iterate far more (avg ~2.3 → ~12.7 on 4.7, ~7.3 on 4.8).
Notably **4.8 plateaus sooner than 4.7 on identical prompts** — it satisfies
the no-improvement stop in fewer rounds, consistent with producing
higher-quality suites earlier rather than grinding toward them.

### 14. Prediction scorecard (coverage-driven → quality-driven)

The five falsifiable predictions from `CHANGELOG.md`:

| # | Prediction                              | Verdict | Evidence |
|---|-----------------------------------------|:-------:|----------|
| 1 | Substring-match asserts drop >80%       | ✅ | A.1 total 65 → 0 (quality); → 9 on ablation = 86%, so prompt-attributable |
| 2 | Private-symbol imports → zero           | ⚠️ | A.2 185 → 59: large drop, but **not zero**; proxy is noisy (matches any `obj._attr(`) |
| 3 | No worktree git-restores baseline tests | ✅ | max identical-to-baseline = 3 empty `__init__.py` markers; the coverage-driven baseline's httpx/iter20 was 31/32 *real* files |
| 4 | iter20 iterations rise toward budget    | ✅ | 2–3 → 6–9 (quality), 10–17 (ablation) |
| 5 | Scorecard tally positive for ≥5/9       | ✅ | quality 9/9, ablation 8/9 |

The seven coverage-driven prediction-table rows (Finding 5/§"What we want to test")
map onto these: #1 anti-fragility → preds 1+2 (substring solved, private
reduced not zeroed); #2 git recovery → pred 3 (✅); #3 REPL verification →
every quality-driven session left a `repl_verifications.log` (process followed; broken-
test count not independently re-run here); #4 iter20 budget → pred 4 (✅);
#5 framework I/O fixtures → `mock_framework` LOC present in every httpx/requests
arm (62–153 LOC in quality), i.e. real-I/O primitives used as intended; #6/#7
SUMMARY-format and `pip install -e .` hermicity → process constraints, held.

### Net: what carried into the cross-language stage

The metric you point the model at dominates the suite you get (Finding 9
confirmed): pointing at a multi-axis quality scorecard instead of coverage
moved 2/9 → 8/9 on the *same* model. The model upgrade is a real but small
top-up. The open cross-language levers: (a) gate the scorecard on the coverage floor
(Finding 12); (b) score the semantic axes (A.3/A.6/B.2/B.3/E.*) the auto-tally
omits, since those are where the coverage-driven baseline's "inflated 2/9" really lived; (c) hold the
model fixed now that the prompt has stabilized, per the original quality-driven note.

---

## Cross-language (JS/TS + Go) — 2026-05-29 findings

The cross-language experiment asks whether the scorecard-anchored prompting that won 9/9 in Python
generalizes. Six new repos — JS/TS: `express` (Mocha + node:assert + supertest),
`jsonwebtoken` (Mocha + Chai + sinon), `zod` (Vitest); Go: `chi` (httptest),
`gjson` (pure parse), `golang-jwt` (crypto) — × three policies = 18 arms,
generated by Opus 4.8 subagents (one per worktree, same model as the quality-driven experiment for
comparability) and scored gen-vs-baseline by the multi-language `score.py`
(`scripts/score_cross_language.py` → `results-cross-language-scorecard.{json,md}`).

### 15. The result generalizes: 18/18 arms beat the human baseline

Every arm wins the auto-countable tally (wins > losses), across two new
languages and six suites written by their respective maintainers. The
Python 2/9 → 9/9 story was not a Python artifact. The two **universal**
wins drive it: **D.1 (LOC-per-test) and D.2 (parametrize ratio) are won by
all 18 arms** — the generated suites are uniformly more LOC-efficient and
more table-driven than every baseline (e.g. express D.1 9.75 vs 14.57, D.2
0.12 vs 0.0; golang-jwt D.1 30.6 vs 78.0, D.2 0.93 vs 0.38). A.1/A.2 are won
wherever the baseline has any fragility to beat (zod A.2 `as any`: 0 vs 497;
express A.1 substring matches: 0 vs 25); A.4/A.5/C.1 are mostly 0-vs-0 ties
at the optimal floor.

### 16. Oneshot wins the axes but ships red; iteration delivers green

A sharp policy split, cleaner than the coverage-driven and quality-driven stages showed:

- **All 6 oneshot arms ended RED** — 1–4 failing tests each, every one a
  *self-authored* expected-value/harness bug left unrepaired per the
  no-second-pass rule (e.g. golang-jwt's exclusive-leeway boundary, zod's
  emoji `\p{Emoji_Component}` keycap, express's auto-304 on `req.fresh`).
  None were framework bug-finds.
- **All 12 iterative arms (iter2 + iter20) ended GREEN.** The first repair
  pass is what converts a strong-but-broken one-shot suite into a shippable
  one. This is the clearest cross-run evidence yet that the *value of
  iteration is correctness, not coverage* — the thing the coverage-driven baseline's iter20 sessions
  never spent their budget on.

So oneshot already beats the baseline on *quality axes* but is not safe to
ship; one iteration both fixes the suite and (where size permits) flips the
lone B.1 loss to a win.

### 17. B.1 as an absolute count is the wrong shape — it fights D.1

**Every loss in all 18 arms is B.1 (fixed-vector count), and nothing else.**
Three distinct causes, only one of them a real quality gap:

1. **Size-scaling.** B.1 is a raw count, so it scales with suite size. zod's
   baseline is 1941 tests with **914** inline-snapshot/`.toBe` vectors; a clean
   281-test generated suite tops out at 154 and *cannot* catch it without
   ~800 padding asserts — which would regress the D.1 win. The agents
   correctly refused to pad (per the "don't sacrifice quality to move a
   number" rule). B.1 (absolute) is in **direct opposition to D.1 (LOC
   efficiency)**: you cannot maximize both. chi/iter20 shows the same bind
   (B.1 107 vs 147 *because* it won D.1 29.5 vs 53.7).
2. **Idiom under-counting.** The JS B.1 regex counts inline string-literal
   equality but **not** supertest `.expect(status, body)`, `it.each` table
   rows, or object/array deep-equals — so express/jsonwebtoken *oneshot*
   suites that are dense with fixed vectors read B.1 ≈ 3–4. (The Go analogue
   — table rows asserted via `got != tc.want` — was caught and fixed
   pre-flight; see Finding 19.) The iterative JS arms "won" B.1 only by
   adding inline-literal `assert.strictEqual` files — i.e. they optimized the
   *metric's blind spot*, not quality.
3. Genuine: a smaller suite does have fewer distinct fixed vectors.

**Proposed scorecard change for a future round:** make B.1 a **ratio** (fixed-vectors per
test, like D.2) instead of an absolute count, and extend the JS profile to
count framework-matcher fixed vectors (supertest `.expect`, deep-equal
literals). Logged to CHANGELOG `[Unreleased]`. This is a richer finding than
the bug it came from: the *count-vs-ratio* choice decides whether B.1 and D.1
can both be satisfied.

### 18. Integrity held at scale: 18/18 clean, zero recovery, zero peeking

Across 18 autonomous subagent runs (2.66M tokens), **zero** recovered deleted
tests from git and **zero** read baseline test bodies (self-reported, and
spot-checked independently: clean `Remove tests…` → `Generated…` git shapes,
20-commit iteration histories with named per-iter moves, and suites that
diverge structurally from their baselines — express 91 files/1128 tests →
15/183, zod 170/1941 → 26/281 — which a git-restore cheat could not produce).
The coverage-driven baseline's `httpx/iter20` cheat (Finding 3) does not recur; the hard
constraints in the prompt header hold up under parallel autonomous execution.

### 19. Cross-language scorer profiles need per-idiom calibration first

The scorer-check (run before generation) and the pilot each caught a
language-specific blind spot that would have corrupted the numbers:

- **JS:** the original profile saw only Jest/Vitest matchers, so Mocha+Chai
  (`.to.equal`) and node:assert suites read ~0 on A.1/B.1. Fixed before the
  run (Chai/node:assert idioms; A.1 restricted to partial matchers so exact
  `==` is a B.1 fixed vector, not an A.1 fragility).
- **Go:** the gjson/oneshot **pilot** revealed B.1 missed the dominant
  table-driven idiom (`got != tc.want`); fixed (gjson gen 0 → 20) and
  committed *before* the 17-arm fan-out so the iterative agents self-scored
  correctly.

Lesson: a heuristic regex scorer must be calibrated against *real* suites in
each target language before its numbers mean anything — and a one-arm pilot
is a cheap way to surface the gap the static scorer-check misses.

### Net: open items for a future round

Scorecard-anchored prompting generalizes (18/18). The open levers are now
about the *instrument*, not the prompt: (a) re-shape B.1 from an absolute
count to a per-test ratio so it stops fighting D.1 (Finding 17); (b) extend
the JS profile to count framework-matcher fixed vectors; (c) the auto-tally
still omits the semantic axes (A.3/A.6/B.2/B.3/E.*) where real quality lives
(carried over from the quality-driven experiment). The generation side is in good shape; the
measurement side is the frontier.
