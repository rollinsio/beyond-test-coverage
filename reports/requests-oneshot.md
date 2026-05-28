# Report — requests / oneshot

**Policy:** one generation pass, no repair iterations.
**Model:** claude-opus-4-7.

> ❓ Verdicts marked are inferred from structural signals + SUMMARY
> commentary, not a deep fragility audit.

## Run profile

| Metric              | Value                                       |
|---------------------|---------------------------------------------|
| Tests generated     | 380                                         |
| Tests passing       | 380                                         |
| Tests failing       | 0 (but 4 self-corrected during authoring)   |
| Wall-clock (pytest) | 1.13 s                                      |
| Test LOC            | 2587                                        |
| Mock LOC            | 32 (mostly `monkeypatch`, no `unittest.mock`) |
| Test files          | 10                                          |

## Coverage vs baseline

| Metric          | Baseline | This run | Delta     |
|-----------------|---------:|---------:|----------:|
| Line coverage   | 87.86 %  | 85.62 %  | **−2.24 pp** |
| Branch coverage | 79.48 %  | 72.51 %  | **−6.97 pp** |

Per-module from the SUMMARY: 100 % on `api.py`, `exceptions.py`,
`hooks.py`, `status_codes.py`; weak on `auth.py` (73 %), `adapters.py`
(71 %), `help.py` (61 %), `certs.py` (60 %).

## Suite structure vs original

| Aspect          | Original (9 files, 4902 LOC, 345 tests)            | This run (10 files, 2587 LOC, 380 tests) |
|-----------------|----------------------------------------------------|------------------------------------------|
| Layout          | One mega-`test_requests.py` (1500+ LOC, ~19 classes) + per-subsystem files | Per-subsystem decomposition: `test_sessions.py`, `test_models.py`, `test_adapters.py`, etc. |
| I/O pattern     | `pytest-httpbin` for real HTTP                     | Same                                     |
| Mocking         | ~62 mock/monkeypatch matches                       | ~32 matches (similar density)            |

The generated decomposition is more conventional Python testing
(one file per source module). Not inherently better or worse than the
baseline's mega-file approach; the layout is a wash.

## What this suite tests well

- **Uses `pytest-httpbin` like the baseline.** Same I/O pattern; no inappropriate mocking.
- **Per-module decomposition is more discoverable** — easier to find the test for `Session.send`.
- **The high-coverage modules** (api, exceptions, hooks, status_codes, _internal_utils, __version__, _types — all 100 %) are *easier* modules to cover well; the suite did fine there.

## What this suite tests poorly

- **Coverage gap is real and concentrated** in important modules:
  - `auth.py` 73 % — authentication is security-critical; missing 27 % of statements there is concerning.
  - `adapters.py` 71 % — `HTTPAdapter` is the production transport; mirror of httpx's `_transports/default.py` gap.
  - `help.py` 61 % — less critical (diagnostic info), but indicates whole functions untested.
  - `certs.py` 60 % — CA bundle handling; missing branches in security-sensitive code.

- **SUMMARY admits 4 self-corrected test-side bugs during authoring** — these were the model's own assertion mistakes (wrong exception types, inverted semantics on `multiple_domains`, wrong morsel date format, URL scheme misparse). The model corrected them mid-authoring rather than committing them as failing (unlike itsdangerous/oneshot which committed 2 failing tests). **The "all pass" headline obscures this self-correction history.**

- **No equivalent to the baseline's `test_lowlevel.py`** — 428 LOC of socket/transport-level tests that exercise paths the generated `test_adapters.py` doesn't reach.

## Verdict matrix

| Dimension              | Original                                              | This suite                                                | Verdict          |
|------------------------|-------------------------------------------------------|-----------------------------------------------------------|:----------------:|
| Coverage               | 87.86 % / 79.48 %                                     | 85.62 % / 72.51 %                                         | **⬇ Worse**     |
| Behavioral breadth     | Tests low-level transport + adapter paths in `test_lowlevel.py` | No equivalent low-level coverage; weaker on auth/adapters/certs | **⬇ Worse**     |
| Mutation-catching power | Inferred similar to baseline density                  | Inferred lower on the under-covered modules               | **❓ ⬇**         |
| Fragility resistance   | Uses `pytest-httpbin`; mock density ~62/4902         | Uses `pytest-httpbin`; mock density ~32/2587 (similar)    | **❓**           |
| Maintainability        | One mega-file + per-subsystem                         | All per-subsystem, smaller LOC                            | **⬆ Better**    |
| Suite correctness      | All baseline tests pass                               | All 380 pass; 4 self-corrected during authoring (not committed) | **⚠ Mixed**     |

## Overall verdict — **Worse than original**

Coverage shortfall is concentrated in important modules (auth, adapters,
certs) — the security and transport surface. The decomposition is
arguably more discoverable than the baseline's mega-file, and the
mock-LOC density is similar, but the gap on the critical modules is
the dominant signal.

The 4 self-corrected mistakes are a quieter version of the
itsdangerous/oneshot epistemic-error problem: the model writes tests
based on assumed-but-not-verified contracts. The fact that it
self-corrected here (and didn't on itsdangerous) suggests it had enough
context (real HTTP via pytest-httpbin) to notice its mistakes, but this
is fragile — when there's no test that gives the model feedback, the
mistake commits.
