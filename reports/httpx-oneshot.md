# Report — httpx / oneshot

**Policy:** one generation pass, no repair iterations.
**Model:** claude-opus-4-7.

> **Note:** Verdicts marked ❓ are inferred from structural signals
> (LOC ratio, file structure, mock count, SUMMARY commentary) rather than
> from a deep fragility audit like the one done for itsdangerous. A
> follow-up audit pass would refine those cells.

## Run profile

| Metric              | Value                                                                |
|---------------------|----------------------------------------------------------------------|
| Tests generated     | 449                                                                  |
| Tests passing       | 449                                                                  |
| Tests failing       | 0                                                                    |
| Wall-clock (pytest) | ~2.04 s                                                              |
| Test LOC            | 4147                                                                 |
| Mock LOC            | 95 (mostly `httpx.MockTransport` + `monkeypatch`, no `unittest.mock`)|
| Test files          | 16                                                                   |

## Coverage vs baseline

| Metric          | Baseline | This run | Delta     |
|-----------------|---------:|---------:|----------:|
| Line coverage   | 100.00 % | 95.27 %  | **−4.73 pp** |
| Branch coverage | 97.27 %  | 92.77 %  | **−4.50 pp** |

This is the first run where the generated suite does **not** match baseline
coverage. 127 of 3134 statements and 61 of 844 branches are uncovered.

## Suite structure vs original

| Aspect          | Original (31 files, 539 tests, 8620 LOC)                         | This run (16 files, 449 tests, 4147 LOC) |
|-----------------|------------------------------------------------------------------|--------------------------------------------|
| Layout          | Top-level + dedicated `client/` subdirectory (8 files) for `Client`/`AsyncClient` concerns | Flat — `client/` consolidated into one `test_client.py` |
| Missing files   | `test_asgi.py`, `test_timeouts.py` (own files)                  | Folded into `test_transports.py` / `test_config.py` |
| Async handling  | Uses pytest-anyio                                                | `anyio.run(...)` directly (no plugin installed) |
| I/O pattern     | `httpx.MockTransport` + `httpx.WSGITransport` + `httpx.ASGITransport` | Same                                       |

The restructuring (flat layout) is a stylistic choice and not inherently
worse; it does compress 31 files into 16. The coverage gap is the more
important signal.

## What this suite tests well

- **Uses the framework's intended testing primitives** — `httpx.MockTransport`, `httpx.WSGITransport`, `httpx.ASGITransport` instead of `unittest.mock`. No `MagicMock`, no `mocker`. Same pattern as the baseline.
- **Offline-by-construction** — the SUMMARY notes the suite never dials out; the top-level `httpx.get/post/...` helpers are exercised only via the `UnsupportedProtocol` failure path. Good hygiene.
- **Covers exception hierarchy explicitly** — `test_exceptions.py` exists as a dedicated file.
- **Cookies, multipart, decoders, URL parsing, status code helpers** — all covered with dedicated files.

## What this suite tests poorly

- **Coverage gap (−4.73 pp line, −4.50 pp branch) means whole code paths are untested.** With 127 missing lines, this is not just edge cases; whole modules are likely under-covered. (Per-module breakdown not in the SUMMARY but inferable from the gap.)
- **Client / AsyncClient consolidation may have lost depth.** The baseline dedicates 8 files in `client/` to specific concerns (auth, redirects, headers, cookies, event_hooks, properties, queryparams, client). One `test_client.py` in the generated suite covers them all in fewer LOC — probable depth loss on the more nuanced client behaviors.
- **No dedicated `test_timeouts.py` or `test_asgi.py`** — these get folded into broader files, which means depth of testing for those specific subsystems is likely shallower than baseline.

(Specific fragility patterns — substring error matches, private-symbol use,
re-implementing wire format — were not audited in detail for this run. A
deep audit pass would identify them.)

## Verdict matrix

| Dimension              | Original                                              | This suite                                                | Verdict          |
|------------------------|-------------------------------------------------------|-----------------------------------------------------------|:----------------:|
| Coverage               | 100 % / 97.27 %                                       | 95.27 % / 92.77 %                                         | **⬇ Worse**     |
| Behavioral breadth     | 31 files, dedicated client subdirectory, distinct asgi/timeouts files | 16 files, flat layout, consolidated client tests          | **⬇ Worse**     |
| Mutation-catching power | Inferred: dense + framework-correct + similar style  | Inferred from coverage gap: real branches missing → some real bugs would survive | **❓ ⬇ likely worse** |
| Fragility resistance   | Inferred: same `MockTransport` pattern; little mocking elsewhere | Same pattern + similar mock density. Specific anti-patterns unaudited. | **❓** |
| Maintainability        | 8620 LOC across 31 files                              | 4147 LOC across 16 files — denser, flatter, more conventional | **⬆ Better**    |
| Suite correctness      | All baseline tests pass                               | All 449 tests pass                                        | **=**            |

## Overall verdict — **Worse than original**

The most important signal is the coverage gap: a 4.7 pp drop on a
100 %-covered baseline means real code paths are untested. The
restructuring (flat layout, smaller LOC) is a positive in isolation but
comes paired with that coverage loss. The mock-LOC metric was a false
alarm — the suite uses the framework's intended pattern. The suite is
substantially smaller and arguably more conventional, but it does not
match the rigor of the original.
