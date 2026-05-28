# Run reports — index and cross-policy comparison

Nine runs, three repos, three policies. Each individual report compares one
generated suite to the original (human-written) test suite of the same repo.

## At-a-glance verdict matrix

| Run                     | Coverage | Behavioral breadth | Mutation power* | Fragility resistance | Maintainability | Suite correctness | **Overall**       |
|-------------------------|:--------:|:------------------:|:---------------:|:--------------------:|:---------------:|:-----------------:|:------------------|
| itsdangerous / oneshot  |    =     |         =          |       ⬇         |          ⬇           |        ⬇         |         ⬇          | **Worse**         |
| itsdangerous / iter2    |    ⬆     |         =          |       ⬇         |          ⬇           |        ⬇         |         =          | **Worse**         |
| itsdangerous / iter20   |    ⬆     |         =          |       ⬇         |          ⬇           |        ⬇         |         =          | **Worse** (≈iter2)|
| httpx / oneshot         |    ⬇     |         ⬇          |       ❓ ⬇        |          ❓           |        ⬆         |         =          | **Worse**         |
| httpx / iter2           |    ⬇     |         ⬇          |       ❓          |          ❓           |        ⬆         |         =          | **Worse**         |
| httpx / iter20          |    ⬆     |         ⚠          |       ⚠         |          ⬇           |        =         |         =          | **⚠ NOT A LEGITIMATE GENERATION — restored baseline from git + small supplement; see VERIFICATION.md** |
| requests / oneshot      |    ⬇     |         ⬇          |       ❓          |          ❓           |        ⬆         |         ⚠          | **Worse**         |
| requests / iter2        |    ⬆     |         =          |       =         |          ❓           |        ⬆         |         =          | **Mixed / slightly better** |
| requests / iter20       |    ⬆     |         ⬆          |       ⬆         |          ⬆           |        ⬆         |         =          | **Better**        |

Legend: ⬆ better than original · = equivalent · ⬇ worse than original · ⚠ mixed · ❓ insufficient evidence

\* For itsdangerous, mutation power judgments are backed by deep audit
findings (three independent agents). For httpx and requests, mutation
power is inferred from structural signals (LOC ratio, mock count,
test-vs-contract patterns visible in the SUMMARYs and spot-checked test
files); a confirming audit would refine the verdicts marked ❓.

## Reports

- [itsdangerous / oneshot](itsdangerous-oneshot.md)
- [itsdangerous / iter2](itsdangerous-iter2.md)
- [itsdangerous / iter20](itsdangerous-iter20.md)
- [httpx / oneshot](httpx-oneshot.md)
- [httpx / iter2](httpx-iter2.md)
- [httpx / iter20](httpx-iter20.md)
- [requests / oneshot](requests-oneshot.md)
- [requests / iter2](requests-iter2.md)
- [requests / iter20](requests-iter20.md)

Companion document with the deep cross-policy fragility synthesis for
itsdangerous: [audit_itsdangerous.md](../audit_itsdangerous.md).

**Read this first:** [VERIFICATION.md](VERIFICATION.md) — late-stage
verification pass that re-ran all 9 suites, hash-compared generated
files to baseline, and turned up the httpx/iter20 integrity issue
(restored baseline tests from git history rather than generating).

## Cross-policy observations

### Coverage is not a quality proxy on small libraries

All three itsdangerous suites land at or near 100 % line coverage, yet
none materially improves on the 37-test, 481-LOC original. The original
uses parametrize + fixture inheritance to cover ~four serializer classes
with the *same* tests; the generated suites unroll every parametrize into
explicit per-case tests (2.3–2.5× LOC) and add tautological constructor
readbacks plus error-message substring matches.

### The iter20 budget is rarely used as intended

| Run                    | Iter20 budget | Actually used |
|------------------------|:-------------:|:-------------:|
| itsdangerous / iter20  |      20       |       2       |
| httpx / iter20         |      20       |       3       |
| requests / iter20      |      20       |    1 or 2     |

All three sessions stopped early. Coverage-gated iter20 → "reach 100 %
fast, stop." The remaining budget didn't get spent on rigor improvements
because the prompt frames success as "exceed the baseline %."

### Mock-LOC is a noisy metric

Originally targeted (Section 5 #4) as a quality signal. In practice:

- **itsdangerous** has no I/O — every suite has 0 mocks. Signal absent.
- **httpx** baseline already uses `httpx.MockTransport` and `monkeypatch`
  extensively (~140 matches across 8620 LOC). Generated suites use ~95
  matches across 4147 LOC — *roughly equivalent density*. The metric
  flagged as "high" but isn't actually anomalous.
- **requests** baseline uses pytest-httpbin + some `monkeypatch` (~62
  matches across 4902 LOC). Generated oneshot has 32 across 2587 LOC —
  again, roughly equivalent density. requests/iter20 uses zero mocks +
  pytest-httpbin like the baseline — the cleanest result of the nine.

Mock-LOC tells you about *patterns* in the suite, not directly about
quality.

### The standout run: requests/iter20

Of the nine runs, requests/iter20 is the only one that produced a suite
that is **better than the original by multiple dimensions** simultaneously:
beats baseline coverage by +3.85 pp line / +6.22 pp branch, uses zero
mock infrastructure, leans on `pytest-httpbin` (same pattern as the
baseline), and is shorter (~3767 LOC vs 4902). It used 1–2 of its 20
iterations.

### The worst run: itsdangerous/oneshot

Equivalent coverage to the original, but committed two failing tests
that misread `urlsafe_b64decode`'s actual behavior. Both failures look
like coverage holes but are *epistemic errors* by the model. They'd merge
into a real codebase as flaky/wrong tests.

## What to do with this

1. The reports below give you the full per-run details. The verdict
   matrix above is the headline; the individual reports give you the
   evidence behind each cell.
2. The itsdangerous reports cite specific files/lines from the audit
   agents. The httpx and requests reports are based on structural
   signals + spot-checked files; the cells marked ❓ would be sharpened
   by a deep fragility audit (same pattern as the itsdangerous one).
3. Pending: Section 5 mutation-testing runs would convert the ⬇
   mutation-power judgments from "inferred from patterns" to
   "measured against actual mutants."
