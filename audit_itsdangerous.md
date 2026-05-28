# Deep test-quality audit — itsdangerous (oneshot / iter2 / iter20)

Three independent audit agents read each generated suite plus the source modules
they target. Their findings converged on the same anti-patterns from different
files, which is stronger than any single audit would be. This document
synthesizes their conclusions.

## Headline

**Coverage % is misleading us.** All three suites land between 97.7 % and 100 %
line coverage on `src/itsdangerous/`, yet none of them is meaningfully more
rigorous than the original 37 hand-written tests — and all three are
*measurably more fragile*. The original suite is dense and behavioral; the
generated suites are large, explicit, and pin implementation details the
maintainer never promised.

| Policy   | Tests | LOC  | Line %  | Branch % | Pass | Fail | Mock LOC | Behavioral grade |
|----------|------:|-----:|--------:|---------:|-----:|-----:|---------:|:-----------------|
| original |    37 |  481 | 97.65 % |  94.90 % |  297 |  0   | 0        | reference        |
| oneshot  |   159 | 1091 | 97.71 % |  95.92 % |  157 |  2   | 0        | weakest          |
| iter2    |   176 | 1185 | 100.00 %|  100.00 %|  176 |  0   | 0        | mid              |
| iter20   |   163 | 1121 | 100.00 %|  100.00 %|  163 |  0   | 0        | mid (≈ iter2)    |

Note: **iter20 stopped at iter_2** because coverage targets were met. The
iter20 budget was wasted — for a 97 % baseline, 2 iterations is enough to hit
100 %, and "the budget went unused" is itself a finding.

## Shared anti-patterns (present in all three suites)

### 1. Error-message substring matching instead of exception identity
The single most common fragility across all three suites. Every policy pins
prose:

| Policy   | Example                                                                                              |
|----------|------------------------------------------------------------------------------------------------------|
| oneshot  | `pytest.raises(BadPayload, match="zlib")` — `wt-oneshot/tests/.../test_url_safe.py:108`              |
| oneshot  | `pytest.raises(SignatureExpired, match="< 0 seconds")` — `wt-oneshot/tests/.../test_timed.py:82`     |
| iter2    | `assert "Malformed timestamp" in str(excinfo.value)` — repeated at `test_signer.py:111, 155`, `test_timed.py:110, 215`, `test_url_safe.py:55, 67`, `test_serializer.py:111`, `test_edge_cases.py:43` |
| iter20   | `pytest.raises(BadSignature, match="No")` — `wt-iter20/tests/.../test_signer.py:101`                 |

The original (`base/tests/.../test_signer.py`) asserts on the exception's
`payload` attribute, not on the message wording. A maintainer rewording any
error message would silently break dozens of generated tests without changing
any contract.

### 2. Re-implementing crypto / encoding inside tests (parallel-bug blindness)
All three suites do "round-trip with locally-recomputed expected value":

- oneshot `test_signer.py:43-47`: `expected = hmac.new(b"key", msg=b"value", digestmod=hashlib.sha1).digest()` — if a mutation broke `HMACAlgorithm.get_signature` in *the same way* the test mistypes the digest, both fail symmetrically and the test passes.
- iter20 has the same shape; iter2 mostly inherits it via `test_signer.py`.
- The original (`base/tests/.../test_serializer.py:186`) pins an *exact* signed-string byte literal (`"[42].-9cNi0CxsSB3hZPNCe9a2eEs1ZM"`). That single test catches mutations the generated suites can't, because there's no recomputation to mask the bug.

### 3. Tautological constructor-attribute readbacks
All three suites contain whole classes that pass a value to a constructor and
assert it was stored.

- iter20 `test_signer.py:194`: `assert s.salt == b"itsdangerous.Signer"` after `Signer("secret")` (asserting the *default*, not behavior)
- iter2 `test_signer.py:74-122`: per-attribute init assertions for every field
- oneshot `test_exc.py:14-97`: 9 nearly identical exception-init echo tests + 5 `issubclass(...)` checks

These survive every realistic mutation. The original has no `test_exc.py` at
all — exceptions are exercised through behavior.

### 4. Hand-recomputed allowed-character sets
oneshot `test_url_safe.py:44-47, 164-167` and iter20 do the same: build a Python
set of "URL-safe characters" inside the test, then assert
`set(signed) <= allowed`. This is *weaker* than the original's single
`test_digests` which pins the exact bytes.

### 5. Testing private symbols directly
- iter2 imports `_lazy_sha1` and `_make_keys_list` (`test_signer.py:13-14`) and dedicates a whole test class to `_make_keys_list`.
- iter2 + iter20 both call `s._loads_unsafe_impl(...)` directly with internal kwargs.
- iter20 tests `SigningAlgorithm()` (the abstract base) for `NotImplementedError`.

The original never reaches for these — it covers their behavior through public API.

### 6. No fixtures or parametrize → 2.3–2.5× LOC inflation
Every suite explodes parametrized cases. Example from iter20:

```python
# Original — base/test_signer.py:67-72 — 6 LOC, 4 cases
@pytest.mark.parametrize("key_derivation", ("concat", "django-concat", "hmac", "none"))
def test_key_derivation(self, signer_factory, key_derivation):
    signer = signer_factory(key_derivation=key_derivation)
    assert signer.unsign(signer.sign("value")) == b"value"

# Generated — iter20 test_signer.py:136-146 — 11 LOC, 3 cases (missing django-concat)
def test_concat_roundtrip(self):
    s = Signer("secret", key_derivation="concat")
    assert s.unsign(s.sign("hi")) == b"hi"

def test_hmac_roundtrip(self):
    s = Signer("secret", key_derivation="hmac")
    assert s.unsign(s.sign("hi")) == b"hi"

def test_none_roundtrip(self):
    s = Signer("secret", key_derivation="none")
    assert s.unsign(s.sign("hi")) == b"hi"
```

The original also reuses entire test classes via inheritance
(`TestTimedSerializer(FreezeMixin, TestSerializer)`), so every serializer
contract is verified against 4 classes for free. The generated suites
duplicate each class's tests in each file.

## Policy-specific differences

### oneshot — committed broken tests reveal a real fragility cost

The 2 failing tests are **both test-side misreads of the source code, not
real bug-finds**. Both assume `urlsafe_b64decode` raises on non-alphabet
characters; it does not — it silently filters them. The author wrote tests
against an imagined contract, not the actual one.

This is the structural cost of one-shot mode: the model can't validate its
assumptions against runtime behavior. The 2 failures look like coverage holes
but are actually *epistemic errors*. They'd merge into a real codebase as
flaky-or-wrong tests and rot quietly.

### iter2 — coverage-chasing is structural, not accidental

iter2 produced a file literally named `test_edge_cases.py` whose every class
has a docstring stating the source line it targets:

```
"""signer.py:231-232 — verify_signature returns False when the sig isn't valid base64."""
"""timed.py:114-115 (except: pass) and branch [120, 130] — sig error with an unparseable timestamp."""
"""serializer.py branch [386, 389] — _loads_unsafe_impl called with explicit load_payload_kwargs."""
```

The serializer test calls the *private* `_loads_unsafe_impl` with
`load_payload_kwargs={"serializer": json}` — but `serializer=json` is already
the default, so the kwarg has no observable effect. **The test would pass even
if `load_payload_kwargs` were silently dropped.** Pure line-flip.

Additionally, `test_timed.py:206-215` `test_malformed_timestamp_with_bad_sig`
uses an `or`-joined assertion:
```python
assert "Malformed timestamp" in str(excinfo.value) or "does not match" in str(excinfo.value)
```
which accepts either contract outcome. A bug that swapped the two errors goes
undetected.

### iter20 — mixed: half its iter_2 adds are real, half are coverage-chasing

The SUMMARY lists 4 iter_2 additions targeting specific source lines. The
audit found:
- 2 of 4 are **contract tests** (`timed.py:123/126` overflow/OSError; `timed.py:134` 9-byte timestamp `ts_int is None` path)
- 2 of 4 are **coverage-chasing**:
  - `_MarkerSigner(Signer): pass` as a "custom signer class" (tautology — verifies the constructor stored its parameter)
  - The `_loads_unsafe_impl(load_payload_kwargs=...)` pattern (same defect as iter2's)

This is interesting: when iter20 stopped at iter_2, the model was making the
*same kind of mistake* as iter2 — chasing branches that don't correspond to
real contracts. The extra budget didn't help because the model didn't have
the right framing for "what makes a test worth writing".

## Concrete mutation-survivor predictions (independent agreement)

Across the three audits, the agents converged on three mutations that survive
*all* the generated suites despite 100 % line coverage:

1. **`timed.py:139` (or :148)** — change `age > max_age` to `age >= max_age`.
   No test pins the boundary case `age == max_age`. All three suites use
   wide gaps (10s vs 0; 120s vs 60; ~24 hours vs 0).

2. **`url_safe.py:60`** — change `len(compressed) < (len(json) - 1)` to
   `len(compressed) <= (len(json) - 1)`. No test exercises the boundary;
   tests use either trivially-small (`{"x": 1}`, no compression) or
   trivially-large (1000 repetitions) payloads.

3. **`signer.py:236`** — replace `for secret_key in reversed(self.secret_keys):`
   with plain iteration. All key-rotation tests still pass because the loop
   tries every key and only needs one to succeed. No test pins
   "newest-first" ordering as observable behavior.

A fourth mutation (iter2-audit suggestion): **`serializer.py:262`** — change
`payload.decode("utf-8")` to `payload.decode("ascii")`. Survives all suites
because no test exercises a non-ASCII payload through the serializer.

## What this says about coverage-driven test generation

1. **High coverage is a lower bound on rigor, not an upper.** All three
   suites passed 97 % easily. None reliably catches the boundary mutations
   above. The 37-test original would catch some of these via its dense
   parametrize patterns; the generated 159-176-test suites do not.

2. **Iteration budget is bounded by epistemic framing, not by compute.**
   iter20 stopped at iter_2, then produced the same coverage-chasing pattern
   as iter2. More iterations would have produced more such tests, not better
   ones. The constraint binding the model isn't "how many tries" — it's
   "what does it mean for a test to be worth writing".

3. **The mock-LOC metric in section 5 is uninformative here.** All three
   suites have 0 mock LOC; itsdangerous is a pure library with no I/O to mock.
   The metric will be informative on `httpx` and `requests` but is a wash
   here. Don't draw conclusions from it on this repo.

## Suggested changes for the next benchmark run

These are *prompt-design* changes, not plan changes:

1. **Add a "fragility contract" section to the prompt.** Explicit guidance
   like: "Prefer asserting exception type + payload attributes over substring
   matches on `str(exception)`. Prefer asserting fixed-byte-string outputs
   over recomputed-from-the-same-algorithm equality. Do not import private
   symbols (underscore-prefix or dunder)."

2. **Add a mutation-aware target.** "After you achieve your coverage goal,
   for each numeric/comparison operator and each conditional in the source,
   verify at least one test exercises the boundary case (`==`, `>=` vs `>`,
   etc.)." This forces the model out of the trivial-payload pattern.

3. **Stop using line/branch coverage as the iter20 success criterion.** Use
   something like "estimate mutation score on top-N modules" instead. For
   itsdangerous, line/branch was satisfied in 2 iterations and the remaining
   18 iterations would have produced more of the same.

4. **For one-shot mode, add an explicit "verify your assumptions" step.**
   "Before writing each test that depends on the runtime behavior of an
   imported standard-library function, run a small Python REPL check to
   confirm the function behaves as you expect." Both oneshot failures would
   have been prevented by running `base64.urlsafe_b64decode(b'!@#$%^&*()')`
   once.

5. **Make the prompt aware of the original suite's parametrize/inheritance
   style.** The model can produce dense, behavioral suites — it just needs
   permission to look at the existing tests as a stylistic reference.
   Adding "if the repository's existing test style uses parametrize and
   inheritance, mirror that style" would likely cut LOC by ~40 %.

## Where to go next

- httpx and requests sessions are still running. When they finish, the same
  audit pattern applies (3 more agents, 1 per policy per repo). Worth
  noting: those repos do have I/O, so mock-LOC and fragility patterns will
  diverge from itsdangerous.
- The mutation-survivor predictions above should be validated by actually
  running `mutmut` on touched modules. That's the Section 5 work that's
  still pending.
