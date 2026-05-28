# Report — httpx / iter2

**Policy:** up to 2 generate→run→fix iterations.
**Model:** claude-opus-4-7.

> ❓ Verdicts marked are inferred from structural signals + SUMMARY
> commentary, not a deep fragility audit.

## Run profile

| Metric              | Value                |
|---------------------|----------------------|
| Iterations used     | 2 (of 2 allowed)     |
| Tests generated     | 416 (iter_2)         |
| Tests passing       | 416                  |
| Tests failing       | 0                    |
| Wall-clock (pytest) | ~0.52 s              |
| Mock LOC            | 122                  |
| Test files          | similar to oneshot   |

## Coverage vs baseline

| Metric          | Baseline | iter_1 | iter_2   | Delta vs baseline |
|-----------------|---------:|-------:|---------:|------------------:|
| Line coverage   | 100.00 % | 92.71 %| 96.33 %  | **−3.67 pp**      |
| Branch coverage | 97.27 %  | 86.73 %| 93.36 %  | **−3.91 pp**      |

iter_2 made a real improvement over iter_1 (+3.62 pp line, +6.63 pp branch),
but still **did not reach baseline coverage**. The SUMMARY explicitly
acknowledges the gap and names the largest uncovered surface:
**`httpx/_transports/default.py` (56 % line cov)** — the module that wraps
httpcore connection pools and proxy transports. Covering it requires
either a live HTTP server or extensive httpcore mocking; the session
deemed both out of scope.

## Suite structure vs original

Same broad shape as oneshot — flat layout, fewer files than baseline.
iter_2's increments went into existing test files rather than a dedicated
edge-cases file (contrast with itsdangerous/iter2 which created
`test_edge_cases.py`).

## What this suite tests well

- **Iter_2 actually improved on iter_1** — unlike itsdangerous/iter2 where iter_2 was half coverage-chasing, the httpx iter_2 increments added genuinely uncovered surface (+3.62 pp line).
- **Same `MockTransport` / `WSGI` / `ASGI` testing pattern as baseline.** Framework-correct.
- **All 416 tests pass on iter_2** — no committed-failing tests.
- **Realistic acknowledgement of scope** — the SUMMARY explicitly identifies the `_transports/default.py` gap as out-of-scope rather than papering over it.

## What this suite tests poorly

- **The 3.67 pp line gap is real and concentrated.** `_transports/default.py` is the **production HTTP transport** — it's not edge-case code. Tests of the SUT's actual production transport are essentially absent.
- **Branch gap (−3.91 pp)** suggests conditional logic in covered files is also under-tested.
- **No dedicated test for ASGI/sniffio detection branches**, called out in the SUMMARY as a smaller remaining gap.

## Why iter2 didn't reach baseline

The SUMMARY's own admission: covering `_transports/default.py` requires
either (a) live HTTP, which is out of scope for a unit-test suite, or
(b) extensive httpcore-internal mocking, which would be brittle and
implementation-pinning. The baseline tests this module via integration
patterns the iter_2 session didn't replicate.

This is a real constraint, but the session chose to stop at "covered
what we can cleanly cover" rather than attempting the harder
integration-style tests.

## Verdict matrix

| Dimension              | Original                                              | This suite                                                | Verdict          |
|------------------------|-------------------------------------------------------|-----------------------------------------------------------|:----------------:|
| Coverage               | 100 % / 97.27 %                                       | 96.33 % / 93.36 %                                         | **⬇ Worse**     |
| Behavioral breadth     | Covers `_transports/default.py` (the real transport)  | Does not cover `_transports/default.py`                   | **⬇ Worse**     |
| Mutation-catching power | Inferred better — covers the real transport          | Inferred worse on the uncovered transport surface         | **❓ ⬇**         |
| Fragility resistance   | Baseline pattern with `MockTransport`                 | Same pattern; specific anti-patterns unaudited            | **❓**           |
| Maintainability        | 8620 LOC                                              | Smaller (~4500 LOC estimated)                             | **⬆ Better**    |
| Suite correctness      | All pass                                              | All 416 pass; iter_1 failures fixed                       | **=**            |

## Overall verdict — **Worse than original**

Closer to baseline than oneshot (−3.67 pp vs −4.73 pp), and iter_2 used
its budget meaningfully (not coverage-chasing). But the gap is concentrated
on the production transport module — exactly the place where missing
coverage matters most. The session correctly diagnosed why it couldn't
close the gap; that doesn't make the gap less significant.
