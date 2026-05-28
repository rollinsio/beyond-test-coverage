# Report — itsdangerous / iter2

**Policy:** up to 2 generate→run→fix iterations.
**Model:** claude-opus-4-7.

## Run profile

| Metric             | Value                            |
|--------------------|----------------------------------|
| Iterations used    | 2 (of 2 allowed)                 |
| Tests generated    | 176                              |
| Tests passing      | 176                              |
| Tests failing      | 0                                |
| Wall-clock (pytest) | 0.13 s (iter_2)                |
| Test LOC           | 1185                             |
| Mock LOC           | 0                                |
| Test files         | 7 — adds dedicated `test_edge_cases.py` |

## Coverage vs baseline

| Metric          | Baseline | iter_1 | iter_2  | Delta     |
|-----------------|---------:|-------:|--------:|----------:|
| Line coverage   | 97.65 %  | 98.47 %| 100.00 %| +2.35 pp  |
| Branch coverage | 94.90 %  | 96.94 %| 100.00 %| +5.10 pp  |

iter_2 closed the last gaps: `signer.py:231–232`, `timed.py:114–115/135`, and `serializer.py` branch `[386, 389]`.

## Suite structure vs original

Same per-module layout as oneshot, **plus a `test_edge_cases.py` whose every test class is docstring-annotated with the source line it targets**:

```text
"""signer.py:231-232 — verify_signature returns False when the sig isn't valid base64."""
"""timed.py:114-115 (except: pass) and branch [120, 130] — sig error with an unparseable timestamp."""
"""serializer.py branch [386, 389] — _loads_unsafe_impl called with explicit load_payload_kwargs."""
```

This is the smoking gun for coverage-chasing test generation.

## What this suite tests well

- **Real exception-chaining** at `test_serializer.py:117–124` — asserts `exc.value.original_error is not None`, exercising the chaining contract `serializer.py` actually promises.
- **Key rotation old→new** in `test_signer.py:233–252 TestSignerRotation` — covers the documented "sign with newest key; verify against any in the list" contract.
- **`freezegun`-based expiration** at `test_timed.py:55–84` — both expiration timeout *and* preservation of `date_signed` are asserted.
- **All three fallback shapes** (`test_serializer.py:175–216`) — dict, class, tuple. Mirrors the source's branch logic.

## What this suite tests poorly

Evidence from the audit (`audit_itsdangerous.md`) and `test_edge_cases.py` direct read:

- **Coverage-chasing in `test_edge_cases.py:62–80`.** `TestSerializerLoadsUnsafeImpl` calls the private `_loads_unsafe_impl` directly, passing `load_payload_kwargs={"serializer": json}` — but `serializer=json` is already the default, so the kwarg has no observable effect. **The test would still pass if `load_payload_kwargs` were silently dropped.** This is a line flip, not a contract test.
- **`or`-joined tautological assertion** at `test_timed.py:206–215`: `assert "Malformed timestamp" in str(...) or "does not match" in str(...)`. Accepts either contract outcome. A bug that *swapped* the two error messages would not be caught.
- **Direct test of private symbols** — `test_signer.py:13–14` imports `_lazy_sha1` and `_make_keys_list`; a whole `TestMakeKeysList` class tests the private helper directly. Refactoring breaks the tests without breaking the contract.
- **Same error-message substring patterns as oneshot** — `match="No"`, `match="separator"`, `match="Unknown key derivation"` — across `test_signer.py`, `test_serializer.py`, `test_timed.py`. Audit found these at ~10 distinct sites.
- **Recomputed HMAC** — same pattern as oneshot.

## Did iter_2 close real gaps or chase lines?

The 4 iter_2 additions targeting specific source lines split:

1. `serializer.py 386→389` (`_loads_unsafe_impl` with kwargs) — **coverage-chasing** (tautological, would pass against a silently-dropping implementation).
2. `signer.py:231–232` (`verify_signature` base64 except path) — borderline; duplicates an existing test at `test_signer.py:186–189`. **Coverage-chasing.**
3. `timed.py 114–115, 135` (Malformed timestamp paths) — **contract test**; a caller would notice if a corrupted timestamp slipped through.
4. `timed.py 134→135` (`ts_int is None` on 9-byte payload) — **contract test**; verifies the malformed-timestamp guard.

**Score: 2 of 4 iter_2 additions are real; 2 are pure line flips.** The iter_2 budget was half-wasted.

## Mutations predicted to survive (despite 100 % coverage)

Independent agreement across audit agents:

1. **`timed.py:139/148`** — flip `age > max_age` → `>=`. No test pins boundary `age == max_age`.
2. **`url_safe.py:60`** — flip `len(compressed) < (len(json) - 1)` → `<=`. No test exercises the boundary.
3. **`signer.py:236`** — replace `reversed(self.secret_keys)` with plain iteration. All rotation tests still pass.
4. **`serializer.py:262`** — `payload.decode("utf-8")` → `decode("ascii")`. No non-ASCII payload exercised.

## Verdict matrix

| Dimension              | Original                                              | This suite                                                  | Verdict           |
|------------------------|-------------------------------------------------------|-------------------------------------------------------------|:-----------------:|
| Coverage               | 97.65 % / 94.90 %                                     | 100 % / 100 %                                               | **⬆ Better**     |
| Behavioral breadth     | Same modules, dense parametrize                       | Same modules + a coverage-chase file (50 % of which is tautological) | **=**             |
| Mutation-catching power | Fixed signed-byte literals catch parallel mutations  | Round-trip + recomputed; 4 specific predicted survivors      | **⬇ Worse**      |
| Fragility resistance   | Few `str(e)`-matches; no private symbols              | Pervasive substring matches; private symbol tests; tamper-by-replace heuristics | **⬇ Worse**      |
| Maintainability        | 481 LOC with parametrize + inheritance                | 1185 LOC, no fixtures, no parametrize, separate class per attribute | **⬇ Worse**      |
| Suite correctness      | All tests pass                                        | All tests pass; some assertions are tautological            | **=**             |

## Overall verdict — **Worse than original**

The +2.35 pp / +5.10 pp coverage gain over baseline is misleading. Half the
iter_2 work was line-flipping against private internals; the other half
added real contract tests but they coexist with widespread fragility
patterns. The model treated "beat baseline coverage" as the success
condition and produced a suite that satisfies that proxy without
improving on the underlying test-quality.
