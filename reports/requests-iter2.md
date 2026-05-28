# Report — requests / iter2

**Policy:** up to 2 generate→run→fix iterations.
**Model:** claude-opus-4-7.

> ❓ Verdicts marked are inferred from structural signals + SUMMARY
> commentary, not a deep fragility audit.

## Run profile

| Metric              | Value                |
|---------------------|----------------------|
| Iterations used     | 2 (of 2 allowed)     |
| Tests generated     | 483 (iter_2)         |
| Tests passing       | 483                  |
| Tests failing       | 0 (5 failures fixed in iter_2) |
| Wall-clock (pytest) | 0.29 s               |
| Test LOC            | 3981                 |
| Mock LOC            | 23 (across iter_2 supplement + test_adapters + test_api) |

## Coverage vs baseline

| Metric          | Baseline | iter_1   | iter_2   | Delta vs baseline |
|-----------------|---------:|---------:|---------:|------------------:|
| Line coverage   | 87.86 %  | 82.07 %  | 90.21 %  | **+2.35 pp**      |
| Branch coverage | 79.48 %  | 75.62 %  | 83.83 %  | **+4.35 pp**      |

iter_2 went from "below baseline" (iter_1) to "above baseline." The
delta is real and largely came from a dedicated `test_iter2_supplement.py`
file targeting the gaps identified in iter_1.

## Suite structure vs original

iter_1 produced the same kind of decomposed layout as oneshot
(per-subsystem files). iter_2 added:

- **`test_iter2_supplement.py`** — explicitly named as the gap-filler.
  Contents per the SUMMARY:
  - `HTTPAdapter.send` error mapping (urllib3 → requests exception translation)
  - `Session.send` end-to-end via a `_MockAdapter`, including redirects, host-change auth stripping
  - `HTTPDigestAuth.handle_401` full dispatch path
  - `Response` streaming branches (`raw.stream`, fallback to `raw.read`, `ProtocolError`/`DecodeError`/`ReadTimeout`)
  - `help.info()` with each optional dep stubbed to None
  - `check_compatibility` / `_check_cryptography` paths

The acknowledged gaps that remain:
- `utils.proxy_bypass_registry` (Windows-only)
- `certs.py:__main__` block
- Several proxy/env-resolver branches that need Windows or DNS-resolver side effects

## What this suite tests well

- **iter_2 supplements target real contracts**, not coverage lines:
  - **HTTPAdapter exception translation** is a real bug-class (a urllib3 internal type leaking out would be a regression).
  - **`Session.send` redirect handling including host-change auth stripping** is a documented security contract (auth headers must not leak across hosts).
  - **`HTTPDigestAuth.handle_401`** is the digest auth flow — security-critical.

- **Failures-then-fixes in iter_1→iter_2** were real. iter_1 had 5 failing tests, all rooted in test-side issues (regex too permissive, status-code-table dedup wrong, fixture lifecycle wrong). iter_2 corrected them — a healthy iteration cycle.

- **Beats baseline on both metrics** with a smaller suite (3981 LOC vs 4902).

## What this suite tests poorly

- **`_MockAdapter` use in `test_iter2_supplement.py`** — the SUMMARY shows iter_2 used a hand-rolled `_MockAdapter` to drive `Session.send` end-to-end. Without seeing the implementation, this is *probably* a reasonable Transport substitute (mirrors the baseline's pattern), but it's a place where the suite trades real-I/O fidelity for test convenience.
- **Same per-module shortfalls as oneshot remain in some places** — `certs.py:__main__` block and Windows-only proxy paths are reasonably skipped, but coverage of those is non-zero in the baseline. Not a fatal issue; just a place where the baseline does slightly better.

## iter_2 quality breakdown

Unlike itsdangerous/iter2 (half coverage-chasing) and httpx/iter20 (mixed),
**the requests iter_2 supplement appears to be predominantly real
contract tests.** The list above describes behaviors a caller would
absolutely notice if broken:

- urllib3 exception leak → user gets the wrong exception type → catch-block mismatches
- host-change auth strip → security regression
- digest auth dispatch → 401 retry doesn't work

This is the pattern we *want* from iterative generation, and it's the
first sign of it in the runs so far.

## Verdict matrix

| Dimension              | Original                                              | This suite                                                | Verdict          |
|------------------------|-------------------------------------------------------|-----------------------------------------------------------|:----------------:|
| Coverage               | 87.86 % / 79.48 %                                     | 90.21 % / 83.83 %                                         | **⬆ Better**    |
| Behavioral breadth     | Tests low-level transport, full session redirect/auth | Per-subsystem coverage + iter_2 supplements on the same   | **=**            |
| Mutation-catching power | Established                                          | Similar — supplements target real contracts not branches  | **=**            |
| Fragility resistance   | Uses `pytest-httpbin`                                | Uses `pytest-httpbin` + `_MockAdapter` hand-roll          | **❓**           |
| Maintainability        | 4902 LOC                                              | 3981 LOC                                                  | **⬆ Better**    |
| Suite correctness      | All pass                                              | All 483 pass after iter_2 fixes                           | **=**            |

## Overall verdict — **Mixed / slightly better than original**

This is the second-best run of the nine. The +2.35 pp / +4.35 pp coverage
delta is real and was achieved by targeting genuine contracts, not by
coverage-chasing. The iter_2 supplements look much more like the kind of
deepening we'd hope iteration enables. The remaining gap (Windows-only
paths, `__main__` blocks) is reasonable to leave alone.

If a deep fragility audit confirms the supplements don't pin
implementation details, this would be the second clear "better than
baseline" result after requests/iter20.
