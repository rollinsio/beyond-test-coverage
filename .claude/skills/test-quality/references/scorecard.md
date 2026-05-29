# Test-quality scorecard

The goal is a test suite that is **better** than where it started — not one that
hits a coverage number. **Coverage is a non-regression floor:** once you're at or
above the starting coverage, more coverage doesn't score. What scores is moving
the quality axes below. (This reframing — quality as the target, coverage as a
floor — is the single change that separated the brittle, coverage-chasing suites
from the ones that beat their human baselines.)

You compute this scorecard twice: once for the **baseline** (the suite before you
touch it, or the human suite you're trying to beat) and again after each
improvement round.

`scripts/score.py` computes the auto-countable axes for you, across languages:
```bash
python scripts/score.py --tests <tests_dir> [--baseline <prior_tests_dir>] [--lang python|js|go]
```
`--lang` auto-detects from the files if omitted. `js` covers Jest / Vitest /
Mocha+Chai+Sinon / node:test (`.js/.ts/.jsx/.tsx`). **The Python profile is the
empirically-validated one; the `js` and `go` axis regexes are heuristic** — use
them to surface trends and worst offenders, then confirm by reading. Axes shown
as `n/a` aren't reliably countable for that language; assess them by reading.

## The axes

**A. Anti-fragility — lower is better, target 0** (repairs in `quality-contract.md`)
- A.1 substring/`in str(e)` assertions on exception messages
- A.2 private-symbol imports / `obj._private(` access
- A.3 tautological constructor readbacks *(judgement — not auto-counted)*
- A.4 recomputed-expected crypto/encoding
- A.5 `or`-joined assertions on error text
- A.6 hand-coded char-set checks where a fixed value would do *(judgement)*

**B. Rigor signals — higher is better**
- B.1 tests pinning a fixed expected literal
- B.2 boundary tests: covered boundaries / total source comparisons *(judgement)*
- B.3 tests using real-I/O framework primitives *(judgement)*

**C. Mocking footprint**
- C.1 `mock_real` — target 0
- C.2 `mock_framework` — reported only, not scored

**D. LOC efficiency — given the coverage floor is met**
- D.1 `test_loc / test_count` (lower = more reuse)
- D.2 parametrize ratio (higher = less unrolling)
- D.3 shared-fixture reuse *(judgement: boolean)*

**E. Correctness — binary**
- E.1 all tests pass
- E.2 no committed-failing tests from misread library behavior (REPL-verified)
- E.3 each test names the contract it protects (so a failure tells the maintainer what broke)

**F. Coverage floor — binary**
- F.1 line % ≥ baseline line %
- F.2 branch % ≥ baseline branch %

Axes marked *(judgement)* aren't reliably regex-countable — assess them by reading
the tests. `score.py` covers A.1, A.2, A.4, A.5, B.1, C.1, C.2, D.1, D.2.

## The "did I actually improve?" gate

An improvement round counts **only if all of these hold** — otherwise revert it:
1. Coverage floor (F.1 + F.2) still satisfied.
2. The round delivers at least one of:
   - an A-axis went down, OR a B-axis went up; OR
   - it **covers a previously-untested contract** — a behavior nothing asserted
     before — and you verified the new test is *mutation-sensitive* (it fails
     when you break the behavior it claims to protect). This is the judgement
     case the auto-axes miss; it is a real win.
3. No axis moved the wrong way for a real reason (adding B.1 vectors while
   introducing 5 new A.1 substring asserts is not a win). Small D.1/D.2 wobble
   from adding one focused test is noise, not a regression.
4. No coverage was gained by reaching into private internals — you can state the
   user-observable contract every new test protects.

> **The auto W/L/T tally does not capture newly-covered contracts.** Adding a
> genuine test for previously-untested behavior often shows as flat or even
> "worse" on the countable axes (one more non-parametrized test nudges D.2 down;
> stubbing a return may nudge a mock count). Do not let the tally veto a
> mutation-verified new test — judge it by case 2's second bullet.

## Stop condition (iterate-to-plateau)

Keep iterating until **either**:
- 3 consecutive rounds cannot produce a gated improvement, **or**
- no contract violations remain and every source boundary has a test.

Then report the before/after scorecard and the residual judgement-axis risks.
