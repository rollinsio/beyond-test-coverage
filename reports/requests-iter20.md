# Report — requests / iter20

**Policy:** up to 20 generate→run→fix iterations; stop early when baseline is exceeded.
**Model:** claude-opus-4-7.

## Run profile

| Metric              | Value                                       |
|---------------------|---------------------------------------------|
| Iterations allowed  | 20                                          |
| Iterations used     | **2** (1 for unit tests, 1 for integration)|
| Tests generated     | 509                                         |
| Tests passing       | 509                                         |
| Tests failing       | 0                                           |
| Test LOC            | 3767                                        |
| Mock LOC            | **0** — uses pytest-httpbin like the baseline |
| Test files          | 11 (incl. dedicated `test_integration.py`) |

## Coverage vs baseline

| Metric          | Baseline | iter_1   | iter_2   | Delta vs baseline |
|-----------------|---------:|---------:|---------:|------------------:|
| Line coverage   | 87.86 %  | 86.59 %  | 91.71 %  | **+3.85 pp**      |
| Branch coverage | 79.48 %  | 80.97 %  | 85.70 %  | **+6.22 pp**      |

iter_1 was unit tests only. iter_2 added `tests/test_integration.py`
using `pytest-httpbin` for real HTTP — and that one addition closed the
remaining gap and pushed both metrics past baseline by wide margins.

## Suite structure vs original

| Aspect          | Original (9 files, 4902 LOC, 617 test functions+) | This run (11 files, 3767 LOC, 509 tests) |
|-----------------|---------------------------------------------------|------------------------------------------|
| Layout          | Mega-file (`test_requests.py`) + per-subsystem    | Per-subsystem + dedicated `test_integration.py` for pytest-httpbin work |
| I/O pattern     | `pytest-httpbin`                                  | Same — explicitly via `test_integration.py` |
| Mocking         | ~62 `mock|patch` matches                          | **0**                                    |

## What this suite tests well

- **Zero mock LOC.** Of the 9 runs, this is the only one with literally zero mock infrastructure. It tests behavior through real I/O the same way the baseline does.
- **Clean separation of unit vs integration.** `test_integration.py` is the integration layer; the other 10 files are unit-level. This is *better* organized than the baseline's mega-file.
- **Beat baseline on both metrics by wide margins** (+3.85 pp / +6.22 pp). Not coverage-chasing — the gain came from adding real integration tests using the framework's intended fixture (pytest-httpbin).
- **Real-world end-to-end testing.** The `test_integration.py` spot-check showed:
  ```python
  def test_api_get(httpbin):
      r = get(httpbin("get"))
      assert r.status_code == 200
  ```
  Simple tests, but they verify the round-trip works against a real HTTP server. Limited in bug-finding power (a 200 status doesn't verify response body details), but they catch any regression that breaks the basic request flow.
- **Smaller suite (3767 LOC vs 4902)** with higher coverage. LOC efficiency is positive.

## What this suite tests poorly

- **Integration tests are shallow.** Many integration tests only assert `status_code == 200`. If the response body were corrupted but the status code right, these tests pass. This is a real limitation for bug-finding power.
- **Cookie / streaming / large-body integration** likely under-tested at the integration layer — the SUMMARY's file list doesn't break down by integration test count, but the spot-check showed mostly simple HTTP-method tests.
- **No `test_lowlevel.py` equivalent** — the baseline has 428 LOC of low-level socket/transport tests; the generated suite covers some of this in `test_adapters.py` but probably not all of it.

## Why this run worked

Several reinforcing factors:
1. **Baseline coverage is lower (87.86 % / 79.48 %)** — there's actual headroom. Generated suites couldn't beat httpx's 100 % baseline because there was nowhere to go.
2. **The iteration loop produced an architectural improvement on iter_2**: realizing unit tests alone couldn't beat baseline, the model added an integration layer. This is the *correct* response to "we need more coverage" — add a new kind of test, not more of the same.
3. **The framework's testing primitives (pytest-httpbin) are well-suited to the gap.** Unlike httpx's `_transports/default.py` (which needs httpcore mocking or a live server), requests' uncovered surface was reachable via a stock fixture.

## Verdict matrix

| Dimension              | Original                                              | This suite                                                | Verdict          |
|------------------------|-------------------------------------------------------|-----------------------------------------------------------|:----------------:|
| Coverage               | 87.86 % / 79.48 %                                     | 91.71 % / 85.70 %                                         | **⬆ Better**    |
| Behavioral breadth     | Unit + integration mixed in mega-file                 | Explicit unit/integration split + real HTTP integration   | **⬆ Better**    |
| Mutation-catching power | Established                                          | Comparable — real I/O catches real regressions; some shallow `status==200` assertions weaken this | **⬆ Better** (with caveat) |
| Fragility resistance   | Uses framework-intended `pytest-httpbin`             | Same pattern + zero mocks                                 | **⬆ Better**    |
| Maintainability        | 4902 LOC                                              | 3767 LOC, cleaner organization                            | **⬆ Better**    |
| Suite correctness      | All pass                                              | All 509 pass; 0 mock infrastructure                       | **=**            |

## Overall verdict — **Better than original**

This is the standout run of the nine. The suite beats baseline on
coverage by wide margins, uses zero mock infrastructure, and is shorter
than the baseline. The architectural decision in iter_2 (add real
integration tests rather than more unit tests) is exactly the kind of
deepening that iterative generation *should* produce.

Caveats:
- The integration tests are shallow (`status_code == 200`). A maintainer adding response-body assertions would strengthen them.
- Some baseline coverage in `test_lowlevel.py`-equivalent areas may be missing; not verified in this report.
- A deep fragility audit would confirm whether the supplements pin any implementation details.

Net: the only run of the nine where I'd describe the generated suite as
substantially better than the human-written original.
