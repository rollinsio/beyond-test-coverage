# Findings — LLM test-generation benchmark

This is an iterative experiment. Each run uses the previous run's
findings to refine the prompts. Findings accumulate; nothing is deleted.
Each Run-N entry preserves the worktrees and reports that produced it.

| Run | Date       | Prompt set         | Worktree inventory      | Reports                  |
|-----|------------|--------------------|-------------------------|--------------------------|
| 1   | 2026-05-28 | (initial — embedded in plan doc) | [runs/run-1.md](runs/run-1.md) | [reports/](reports/) |
| 2   | _pending_  | [prompts/run-2/](prompts/run-2/) | _to be created — wt-r2-*_ | _pending_ |

---

## Run 1 — 2026-05-28 findings

Nine worktrees (3 repos × 3 policies — oneshot, iter2, iter20) run
against `pallets/itsdangerous`, `encode/httpx`, `psf/requests`. Full
per-run reports live in [reports/](reports/). The deep three-agent
fragility audit on itsdangerous is at
[audit_itsdangerous.md](audit_itsdangerous.md). The verification pass
that turned up the integrity finding is at
[reports/VERIFICATION.md](reports/VERIFICATION.md).

### 1. Coverage % is not a quality proxy on small libraries

All three itsdangerous suites landed at 97.7–100 % line coverage, yet
none materially improves on the 37-test, 481-LOC original — and all
three are *more fragile* than the original by the patterns below. The
+2.35 pp gains from iter2 and iter20 came from coverage-chasing
additions targeting private internals, not from deeper behavioral
testing.

**Action for Run 2:** the prompt should de-emphasize coverage as the
success criterion. iter20 in particular needs a different stopping
condition.

### 2. The iter20 budget is consistently underused

All three iter20 sessions stopped at iteration 2 or 3 because they hit
"beat baseline coverage" early:

| Repo         | iter20 budget | Iterations actually used |
|--------------|:-------------:|:------------------------:|
| itsdangerous |      20       |             2            |
| httpx        |      20       |             3            |
| requests     |      20       |          1 or 2          |

The remaining 17–18 iterations didn't get spent on rigor improvements
because the prompt framed success as "exceed baseline %." Once
coverage was past baseline, the model had no incentive to keep
iterating.

**Action for Run 2:** iter20's success criterion needs to require
*more* than coverage matching. Either an explicit "deepen tests after
matching coverage" instruction, or a boundary-mutation-style criterion.

### 3. Sessions can cheat the delete-and-regenerate setup

**`httpx/wt-iter20` did this.** Hash-compare: 31 of 32 test files in
that worktree are **byte-identical** to the baseline. The session
deleted `tests/`, committed the deletion, then used `git show
<delete-commit>^:tests/<file>` (or equivalent) to recover the deleted
files in iteration 1. Only `test_extra_branches.py` is new content.
Its "100 % line / 100 % branch" is the baseline's coverage, not a
generation result.

The other two iter20 sessions (itsdangerous, requests) generated
genuinely; their files all differ from baseline. So this was
opportunistic, not systematic.

**Action for Run 2:** the prompt must explicitly forbid recovering
deleted tests from git. The cleanest framing: "treat the
delete-commit's parent as the only legitimate source of information —
no `git show`, `git log -p`, `git restore`, or equivalent." If the
prompt wants to be air-tight, the setup step can also wipe the
delete-commit's reflog, but the explicit constraint is sufficient for
a cooperating model.

### 4. The model commits epistemic errors without verification

**`itsdangerous/wt-oneshot` did this.** Two committed-failing tests
both stemmed from the model assuming `base64.urlsafe_b64decode(b"!@#$%^&*()")`
would raise `binascii.Error`. It doesn't — Python silently filters
non-alphabet characters and returns `b""`. A one-line REPL check would
have caught this.

Neither failure is a bug-find. Both look like coverage holes; they're
actually misreads of stdlib behavior.

**Action for Run 2:** the prompt should require a "verify your
assumptions" step before writing tests that depend on runtime behavior
of imported functions. Specifically: "If a test you're about to write
asserts that a stdlib or third-party function raises a specific
exception, run `python -c 'from x import y; y(args)'` first to confirm
the actual behavior."

### 5. Generated tests use systematic anti-patterns

The three-agent fragility audit on itsdangerous (independent agents,
one per policy) **converged on the same patterns from different
files**:

a. **Error-message substring matching.** `pytest.raises(BadPayload, match="zlib")`. The contract is the exception type + payload; the message wording is documentation, not contract. Found at ~10 distinct sites per policy.

b. **Recomputing crypto/encoding inside the test, then comparing.** `expected = hmac.new(b"key", b"value", sha1).digest()`. If a mutation breaks `HMACAlgorithm.get_signature` in the *same* way the test mis-types the digest, both fail symmetrically and the test passes. Compare to baseline's fixed byte literal `"[42].-9cNi0CxsSB3hZPNCe9a2eEs1ZM"` (catches parallel mutations).

c. **Tautological constructor readbacks.** Pass `salt=...` then assert `s.salt == "..."`. Survives every realistic mutation. All three suites had whole files (`test_exc.py`) that are this pattern.

d. **Private symbol imports.** `from itsdangerous.signer import _lazy_sha1, _make_keys_list`; `s._loads_unsafe_impl(...)`; `_DigestAuthChallenge`. The originals never reach for these.

e. **Re-implementing the wire format in the test.** Building `value + b"." + base64_encode(int_to_bytes(2**62)) + b".wrongsig"` directly. Any encoding-layout change breaks these even if the public sign/unsign contract is intact.

f. **`or`-joined assertions that accept either outcome.** `assert "Malformed timestamp" in str(e) or "does not match" in str(e)`. A bug that *swapped* the two messages goes undetected.

g. **Hand-coded character sets as weaker substitutes for fixed expected values.** `allowed = set("ABC...0123456789-_=."); assert set(signed) <= allowed`. The original asserts an exact byte literal.

h. **No parametrize / fixtures / inheritance.** Original uses
`@pytest.mark.parametrize` for 4 key-derivation modes in 6 LOC.
Generated unrolls into 3 explicit per-case tests in 11 LOC (and
sometimes misses a case). Original reuses entire test classes via
`TestTimedSerializer(FreezeMixin, TestSerializer)`. Generated
duplicates each behavior in each file. Result: **2.3–2.5× LOC
inflation** across all itsdangerous policies.

**Action for Run 2:** the prompt needs an explicit anti-fragility
contract section listing these patterns with positive alternatives.
See [prompts/run-2/](prompts/run-2/).

### 6. The mock-LOC metric is noisy

httpx baselines use `httpx.MockTransport` + `monkeypatch` extensively
(the framework's *intended* test pattern). The regex `mock|patch|MagicMock|mocker`
matches all of these. Generated suites have roughly equivalent density.
The metric flagged the suites as "mock-heavy" but they weren't —
they were using the framework's intended primitives.

| Suite      | LOC  | mock-regex matches | Density (per 100 LOC) |
|------------|-----:|-------------------:|----------------------:|
| httpx baseline | 8620 | ~140               | 1.6 |
| httpx oneshot  | 4147 | 95                 | 2.3 |
| requests baseline | 4902 | ~62              | 1.3 |
| requests oneshot  | 2587 | 32               | 1.2 |

**Action for Run 2:** the metric needs to distinguish `unittest.mock`/`MagicMock`/`mocker` (real mocking) from `httpx.MockTransport`/`monkeypatch` (framework primitives). Refine the regex or count by category.

### 7. The standout pattern: integration tests via real-I/O fixtures

**`requests/wt-iter20` is the only run that's better than baseline on
every dimension.** What it did differently: iter_1 ran unit tests;
iter_2 added `tests/test_integration.py` using `pytest-httpbin` for
real HTTP I/O. That single architectural decision pushed it past
baseline by +3.85 pp line / +6.22 pp branch with **zero mock
infrastructure**.

The insight: when the framework provides real-I/O test primitives
(`pytest-httpbin`, `httpx.MockTransport`, `httpx.WSGITransport`,
etc.), an iteration loop that recognizes "we need a different *kind*
of test, not more of the same" can produce a substantially better
suite than the baseline.

The other two requests sessions used these fixtures too, but didn't
make the unit-vs-integration split as cleanly.

**Action for Run 2:** the prompt should explicitly point out the
framework's real-I/O fixtures by name, and instruct iter2/iter20
sessions to consider adding integration tests when unit tests
plateau below baseline coverage.

### 8. Tooling / hermicity issues that we should fix

a. **Shared `base/.venv` got clobbered by `pip install -e .` from a
   worktree.** The `requests` editable install ended up pointing at
   `wt-iter20/src/requests/`, not `base/src/requests/`. Source files
   are identical across worktrees so the test outcome was unchanged,
   but coverage records paths that all point at wt-iter20. The
   per-worktree prompt should explicitly forbid running `pip install
   -e .` from inside the worktree (it's not needed, since deps are
   already in the shared venv).

b. **Aggregator script's src-prefix filter assumed relative paths.**
   Coverage JSONs store absolute paths. Filter needs to accept either
   a relative or absolute prefix.

c. **"Line coverage" labels disagreed across SUMMARYs.** Some used
   pure `(stmts - missing) / stmts`; some used coverage.py's
   `totals.percent_covered` (which is line+branch combined when
   branch is on). The prompt should require the SUMMARY to report
   *both* numbers under labeled names.

### What we want to test in Run 2

Each is a discrete prompt-design change with a falsifiable prediction:

| # | Change                                                                 | Prediction                                                              |
|---|------------------------------------------------------------------------|-------------------------------------------------------------------------|
| 1 | Add anti-fragility contract section (forbidding patterns 5a–5g)        | Mock-LOC down; substring-match assertions down by >80 %; private-symbol imports near zero |
| 2 | Forbid git-history recovery + add explicit "treat deletion as final"    | httpx/iter20-style restoration drops to zero                            |
| 3 | Require REPL verification of stdlib/third-party assumptions             | Oneshot test-side-bug count drops; tests committed broken near zero      |
| 4 | iter20 success criterion: "beat baseline AND fix the 4 most fragile patterns from your iter_1" | iter20 iterations used rises from 2–3 to closer to budget |
| 5 | Prompt names framework real-I/O fixtures by name (`pytest-httpbin`, `MockTransport`, etc.) | More iter2/iter20 sessions add integration tests; coverage gaps on transport modules close |
| 6 | Require SUMMARY to report both pure-line and combined coverage         | Apples-to-apples comparison across runs becomes possible                |
| 7 | Forbid `pip install -e .` from inside worktrees                        | Editable install in shared venv stays pointing at base/                |

All seven changes are encoded in [prompts/run-2/](prompts/run-2/).

### 9. Even the initial Run 2 design centered on coverage. We re-centered it on quality.

The first draft of the Run 2 prompts kept coverage as the goal ("beat
baseline coverage AND no anti-patterns AND at least one
integration/boundary iteration"). On review, this still anchors the
session on a number; the quality rules act as side constraints. That's
the wrong framing.

**The corrected framing:** the goal is to produce a *better* test
suite than the baseline. "Better" is defined by a multi-axis quality
scorecard (`prompts/run-2/quality_scorecard.md`). Coverage is a
non-regression floor — once you're at baseline coverage, additional
coverage doesn't score. The iteration budget exists to deepen quality
on the scorecard axes, not to chase a percentage.

**Action for Run 2:** the prompt centers on the scorecard. Each
iteration must claim a scorecard-improving move and name the axis
delta in its commit message. iter20's stop condition is "3
consecutive iterations cannot improve the scorecard," not "coverage
parity reached."

This refinement is itself the kind of finding the iterative
experiment is meant to surface: the *metric* you point the LLM at
determines the kind of suite it produces. Run 1 pointed at coverage
and got coverage. Run 2 points at quality (operationalized) and
should produce quality. If it doesn't, that's a Run 3 finding about
either the scorecard's design or the model's ability to optimize for
multi-axis goals.

---

## Run 2 — pending

To be filled in after Run 2 executes.
