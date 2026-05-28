# Report — itsdangerous / iter20

**Policy:** up to 20 generate→run→fix iterations; stop early upon beating baseline.
**Model:** claude-opus-4-7.

## Run profile

| Metric              | Value                |
|---------------------|----------------------|
| Iterations allowed  | 20                   |
| Iterations used     | **2** (stopped early after exceeding baseline) |
| Tests generated     | 163                  |
| Tests passing       | 163                  |
| Tests failing       | 0                    |
| Wall-clock (pytest) | ~0.3 s (iter_2)      |
| Test LOC            | 1121                 |
| Mock LOC            | 0                    |
| Test files          | 6                    |

## Coverage vs baseline

| Metric          | Baseline | iter_1 | iter_2   | Delta    |
|-----------------|---------:|-------:|---------:|---------:|
| Line coverage   | 97.65 %  | 98.85 %| 100.00 % | +2.35 pp |
| Branch coverage | 94.90 %  | 96.94 %| 100.00 % | +5.10 pp |

Identical headline numbers to iter2. The 20-iteration budget went unused
because the coverage target was met on iteration 2.

## Suite structure vs original

Same per-module layout as oneshot (no dedicated edge-cases file like
iter2). The iter_2 additions are spread into the existing per-module
files instead of a separate file.

The SUMMARY explicitly lists the iter_2 targets:
- `timed.py` 123/126/135 — error-handling paths in `unsign`
- `serializer.py` 222→225 — custom `signer=` class branch
- `serializer.py` 386→389 — `_loads_unsafe_impl` with `load_payload_kwargs`
- `timed.py` 134→135 — 9-byte timestamp `ts_int is None`

## What this suite tests well

- **Negative-age branch** at `test_timed.py:63–70` covers the `age < 0` arm — a real expiration-bypass concern.
- **Key-rotation old→new** at `test_signer.py:217–221` + `test_serializer.py:79–83` is meaningful behavioral testing.
- **9-byte timestamp test** at `test_timed.py:144–155` — the strongest iter_2 addition. Verifies the malformed-timestamp guard rather than just executing the line.
- **Real `BadPayload.original_error` chain check** at `test_serializer.py:117–124`.

## What this suite tests poorly

Audit findings:

- **Coverage-chasing iter_2 additions:**
  - `test_serializer.py:248–256 TestSerializerCustomSigner.test_explicit_signer_class` — defines `class _MarkerSigner(Signer): pass` and asserts `s.signer is _MarkerSigner`. **Tautology.** Verifies the constructor stored its parameter.
  - `test_serializer.py:259–272` — calls `s._loads_unsafe_impl(...)` with `load_payload_kwargs={"serializer": json}`. But `serializer=json` is the default, so the kwarg has no effect. **Test would pass even if `load_payload_kwargs` were silently dropped.**
- **Hard-coded source-of-truth defaults** — `assert s.salt == b"itsdangerous.Signer"` (`test_signer.py:194`). Pins the literal default-salt string. A maintainer renaming it would break the test without breaking any contract.
- **Exact-string error matching** — `match="No"`, `match="Unknown key derivation"`, `match="separator"`, etc. Same anti-pattern as oneshot and iter2.
- **Re-implementing the wire format** — `test_timed.py:116–122, 139–140, 150–155` build `value + b"." + base64_encode(int_to_bytes(2**62)) + b".wrongsig"` directly. Any encoding-layout change breaks these tests even if public sign/unsign round-trips remain correct.
- **Direct test of `SigningAlgorithm()` base class** (`test_signer.py:18–21`) — tests the abstract base raising `NotImplementedError`, which is an implementation detail (the design choice between `NotImplementedError` and `@abstractmethod` is internal).

## iter_2 quality breakdown

Of the 4 iter_2 additions:
- **2 contract tests:** `timed.py` overflow/OSError (`test_overflow_timestamp_with_bad_signature`) and 9-byte timestamp (`test_unsign_ts_int_none_path`). Real-world catches.
- **2 coverage chasers:** `_MarkerSigner(Signer): pass` (tautological) and `_loads_unsafe_impl` direct call (no observable effect).

Same split as iter2's edge-cases additions. **The extra iter20 budget didn't fix the model's framing problem.**

## Mutations predicted to survive

Same three as oneshot and iter2 (independent agent agreement):
1. **`timed.py:148`** — `age > max_age` → `>=`. No boundary test (gaps are 10s, 24h).
2. **`url_safe.py:60`** — `len(compressed) < (len(json) - 1)` → `<=`. No boundary test.
3. **`signer.py:236`** — `reversed(self.secret_keys)` → plain iteration. Newest-first ordering is not observable in any test.

## Direct LOC comparison example

Original (`base/test_signer.py:67–72`, 6 LOC, 4 cases via parametrize):
```python
@pytest.mark.parametrize("key_derivation", ("concat", "django-concat", "hmac", "none"))
def test_key_derivation(self, signer_factory, key_derivation):
    signer = signer_factory(key_derivation=key_derivation)
    assert signer.unsign(signer.sign("value")) == b"value"
```

This suite (`wt-iter20/test_signer.py:136–146`, 11 LOC, 3 cases — missing `django-concat`):
```python
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

~2× the LOC, missing the `django-concat` case.

## Verdict matrix

| Dimension              | Original                                              | This suite                                                | Verdict      |
|------------------------|-------------------------------------------------------|-----------------------------------------------------------|:------------:|
| Coverage               | 97.65 % / 94.90 %                                     | 100 % / 100 %                                             | **⬆ Better**|
| Behavioral breadth     | Same                                                  | Same + 2 coverage chasers + 2 real edge tests             | **=**        |
| Mutation-catching power | Fixed vectors                                         | Round-trip + recomputed; same 3 predicted survivors        | **⬇ Worse** |
| Fragility resistance   | Few message matches, no private symbols               | Pervasive substring matches; pins default salt strings; abstract base test | **⬇ Worse** |
| Maintainability        | 481 LOC, parametrize + inheritance                    | 1121 LOC, no parametrize, fewer reuses than iter2          | **⬇ Worse** |
| Suite correctness      | All pass                                              | All pass; some tautological                                | **=**        |

## Overall verdict — **Worse than original** (essentially identical to iter2)

The 20-iteration budget was wasted — the model stopped at iter_2 because
"beat baseline" was satisfied. With more iterations available the model
had no incentive to deepen the existing tests; it just stopped. Same
fragility patterns and same mutation-survivors as oneshot and iter2.

The interesting structural finding from this run: **iter20 effectively ran
iter2 with a different label**. They produced suites of comparable
quality with comparable defects.
