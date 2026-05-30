## Quality scorecard — the actual goal of this benchmark

**The goal is to produce a test suite that is *better* than the
baseline.** Not to match a coverage number. Coverage is a
non-regression floor — once you're at or above the baseline's
coverage, additional coverage doesn't count as improvement. What
counts is moving the quality axes below.

You compute this scorecard for two things in every session:

1. **The baseline** (`{BASE}/{TESTS_DIR}/`) — once, at the start, before
   you delete it. Use `wc -l`, `grep -c`, and equivalents — you may
   look at the baseline tests' *structure* and *counts* but **may not
   read individual baseline test bodies** (they're the answer key).
2. **Your suite**, after every iteration that writes tests.

Your suite "wins" an axis if its score is *better* than the baseline's
on that axis. Your suite wins overall if it wins more axes than it
loses, without regressing on the coverage floor.

### The axes

**A. Anti-fragility (lower count → better; target: 0)**
Count occurrences in your suite. Each is a coverage-driven-baseline-validated fragility
pattern with concrete repair guidance in `quality_contract.md`.

- A.1: Substring `match=`/`in str(e)` assertions on exception messages
- A.2: Private-symbol imports (`from x import _y`; uses of `obj._z`)
- A.3: Tautological constructor readbacks (`Foo(x=v); assert obj.x == v`)
- A.4: Recomputed-expected crypto/encoding (`expected = hmac.new(...)`)
- A.5: `or`-joined assertions on error-message text
- A.6: Hand-coded character-set membership checks where a fixed
  expected value would suffice

**B. Test-rigor signals (higher count → better)**

- B.1: Tests that pin a fixed expected literal (`assert sign(b"x") == b"<exact bytes>"`).  The baseline does this; coverage-driven baseline generated suites largely did not.
- B.2: Boundary tests for source comparisons. For each `<`, `<=`,
  `>`, `>=`, `==`, `!=` in `{SOURCE_DIR}/`, count whether at least
  one test exercises the boundary case (`age == max_age`,
  `len(compressed) == len(json) - 1`, etc.). Score = covered
  boundaries / total source comparisons.
- B.3: Tests using framework real-I/O primitives (see common header
  for the list per repo). Higher = exercising real code paths.

**C. Mocking footprint (`mock_real` lower → better)**

- C.1: `mock_real_loc` — matches of `\b(MagicMock|Mock\(|patch\(|mocker\b|unittest\.mock)\b`. Target: 0.
- C.2: `mock_framework_loc` — matches of `\b(MockTransport|WSGITransport|ASGITransport|monkeypatch|httpbin)\b`. Not a quality metric; reported for context (framework primitives are legitimate).

**D. LOC efficiency (lower per-test → better, given coverage floor met)**

- D.1: `test_loc / test_count` — proxy for fixture/parametrize reuse.
- D.2: parametrize-test ratio — `# @pytest.mark.parametrize occurrences / test_count`.
- D.3: shared-fixture use — boolean: do your test files declare and reuse fixtures, or does every test re-construct its inputs?

**E. Suite correctness (binary or near-binary)**

- E.1: All tests pass (Y/N).
- E.2: No committed-failing tests from epistemic errors about library
  behavior (each test you wrote that depends on stdlib/library
  behavior, you verified in a REPL — list those verifications in the
  SUMMARY).
- E.3: Each test claims a documented contract — its docstring or its
  class docstring names what behavior it's protecting (this isn't
  about lines of prose; it's about "if this test fails, the
  maintainer knows what's broken").

**F. Coverage floor (binary)**

- F.1: Pure line % ≥ min(baseline pure line %, 100). Y/N.
- F.2: Pure branch % ≥ baseline pure branch %. Y/N.

Coverage past baseline is fine but doesn't score. Below baseline =
regression.

### How to compute axes A and C cheaply

For your own suite:

```bash
# A.1 substring-match assertions
grep -rcE 'pytest\.raises\([^)]*match=|in str\(' {TESTS_DIR}/

# A.2 private-symbol imports
grep -rE 'from [a-zA-Z_.]+ import [_a-zA-Z_,\s]*_[a-zA-Z_]+|\._[a-zA-Z_]+\(' {TESTS_DIR}/

# A.4 recomputed-expected crypto
grep -rcE 'hmac\.|hashlib\.|expected\s*=\s*(hmac|hashlib|base64)' {TESTS_DIR}/

# A.5 or-joined error matches
grep -rE 'in str\([^)]*\)\s*or\s*' {TESTS_DIR}/

# C.1 real mocks
grep -rcE '\b(MagicMock|Mock\(|patch\(|mocker\b)' {TESTS_DIR}/

# C.2 framework primitives
grep -rcE '\b(MockTransport|WSGITransport|ASGITransport|monkeypatch|httpbin)\b' {TESTS_DIR}/
```

You may run these against the baseline (`{BASE}/{TESTS_DIR}/`) to get
baseline scores. **You may not** read baseline test file bodies.

### The "did I improve?" decision

An iteration is a *real* improvement only if **all** of these are true:

1. Coverage floor F.1 + F.2 still satisfied.
2. **At least one** of A.1–A.6 went down OR at least one of
   B.1–B.3 went up.
3. No axis went in the wrong direction (e.g., adding
   B.1 fixed-vector tests is improvement; adding them while
   introducing 5 new substring-match assertions is not).
4. Coverage % did **not** go up by chasing private internals (i.e.,
   you can describe the user-observable contract every new test
   protects).

If you can't say yes to all four, your iteration is a no-op (or worse)
and you should not commit it as an iteration.

### Comparing your final scorecard to the baseline

You win if you win more axes than you lose:

- A axes (anti-fragility): you win an axis if your count is < baseline's count.
- B axes (rigor signals): you win if your count is > baseline's count.
- C.1 mock_real_loc: you win if yours ≤ baseline's.
- D axes: you win each axis if you're not worse.
- E axes: you must hit E.1; E.2 and E.3 are wins if yes.

Report wins, losses, and ties as a final tally. The benchmark cares
about the tally, not about coverage %.
