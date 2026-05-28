# Report — itsdangerous / oneshot

**Policy:** one generation pass, no repair iterations.
**Model:** claude-opus-4-7.

## Run profile

| Metric              | Value                                  |
|---------------------|----------------------------------------|
| Tests generated     | 159                                    |
| Tests passing       | 157                                    |
| Tests failing       | **2 (committed as failing per policy)**|
| Wall-clock (pytest) | 0.24 s                                 |
| Test LOC            | 1091                                   |
| Mock LOC            | 0                                      |
| Test files          | 6 (`test_encoding`, `test_exc`, `test_serializer`, `test_signer`, `test_timed`, `test_url_safe`) |

## Coverage vs baseline

| Metric          | Baseline | This run | Delta     |
|-----------------|---------:|---------:|----------:|
| Line coverage   | 97.65 %  | 97.71 %  | +0.06 pp  |
| Branch coverage | 94.90 %  | 95.92 %  | +1.02 pp  |

Coverage is effectively the same as the human-written baseline.

## Suite structure vs original

| Aspect              | Original (37 tests, 481 LOC) | This run (159 tests, 1091 LOC) |
|---------------------|------------------------------|--------------------------------|
| Layout              | `test_<module>.py` per source module | Same, plus dedicated `test_exc.py` (which the original omits) |
| Reuse style         | `@pytest.mark.parametrize` + fixture factories (`signer_factory`) + class inheritance (`TestTimedSerializer(FreezeMixin, TestSerializer)`) | None — every case unrolled to an explicit test method |
| Fixed expected values | Yes — e.g., `assert signed == "[42].-9cNi0CxsSB3hZPNCe9a2eEs1ZM"` | No — every comparison is round-trip or re-derived |
| Mocking             | None                         | None                           |

## What this suite tests well

- **Key-derivation branches** — `test_signer.py:124–148` covers all 4 key-derivation modes (concat, django-concat, hmac, none) by computing the expected derived key with the same algorithm as the source. (Same coverage as the original.)
- **Fallback signers contract** — `test_serializer.py:231–241` verifies `len(signers) == 3` after constructing a `Serializer(["k1","k2"], fallback_signers=[...])`. Catches a real `iter_unsigners` contract.
- **Negative-age expiration branch** — `test_timed.py:77–83` reaches the `age < 0` arm at `timed.py:148`, which the original does not explicitly cover.

## What this suite tests poorly

Evidence below from the deep audit in `audit_itsdangerous.md`:

- **Error-message substring matches everywhere.** `pytest.raises(BadPayload, match="zlib")` (`test_url_safe.py:108`), `match="< 0 seconds"` (`test_timed.py:82`), `match="Unknown key derivation"` (`test_signer.py:147`). The original asserts on `e.payload`, not on message text. A maintainer rewording any error string silently breaks dozens of these.
- **Recomputed-expected HMAC.** `test_signer.py:43–47` computes `expected = hmac.new(b"key", b"value", sha1).digest()` and compares. If a mutation introduced the *same* mistake on the SUT side, the test would still pass. The original's fixed-byte-literal assertion catches this; this suite has no such fixed-vector test.
- **Whole `test_exc.py` is tautological** — 9 nearly-identical exception-init readback tests + 5 `issubclass(...)` checks. The original omits this file entirely.
- **Hand-coded URL-safe character set** at `test_url_safe.py:44–47` as a structural "no character outside this set" check, weaker than the original's exact-bytes assertion.

## The 2 committed failures

Both are **test-side mistaken assumptions, not bug-finds**:

1. `test_encoding.py::TestBase64Decode::test_invalid_raises_baddata` — assumes `urlsafe_b64decode(b"!@#$%^&*()")` raises. It does not; Python silently filters non-alphabet characters and returns `b""`. The model misread the source.
2. `test_url_safe.py::TestURLSafeSerializer::test_bad_base64_payload` — same lenient-base64 misread; a `BadPayload` *was* raised by JSON decode, but with the generic "Could not load the payload..." message instead of "base64". The `match="base64"` failed even though the actual contract (BadPayload on garbage input) was satisfied.

Both would have been prevented by the model running a one-line REPL check before writing the test.

## Verdict matrix

| Dimension              | Original posture                                     | This suite                                                       | Verdict      |
|------------------------|------------------------------------------------------|------------------------------------------------------------------|:------------:|
| Coverage               | 97.65 % / 94.90 %                                    | 97.71 % / 95.92 %                                                | **=**        |
| Behavioral breadth     | Covers same modules through public API + fixed vectors | Covers same modules through public API; misses `django-concat` round-trip; adds `test_exc.py` (tautological) | **=**        |
| Mutation-catching power | Fixed signed-byte literals catch parallel mutations  | Round-trip + recomputed-expected; no fixed vector. 3 specific mutations (timed.py boundary, url_safe.py compression threshold, signer.py reversed iteration) survive — see audit. | **⬇ Worse** |
| Fragility resistance   | Few message-match assertions; private symbols not tested | Pervasive `match="..."` substring matching; hand-coded alphabets; `int_to_bytes(0) == b""` implementation pin | **⬇ Worse** |
| Maintainability        | 481 LOC with parametrize + inheritance + fixtures    | 1091 LOC, no fixtures, no parametrize, no class reuse            | **⬇ Worse** |
| Suite correctness      | All tests pass; no test-side bugs                    | 2 committed failing tests that misread the source code's behavior | **⬇ Worse** |

## Overall verdict — **Worse than original**

Equivalent quantitative coverage, but every qualitative dimension is worse:
more code, more fragility, lower mutation-catching power, and two
committed-broken tests that reflect the model not validating its
assumptions against the source. The 0-mock score is good news; everything
else is regression.
