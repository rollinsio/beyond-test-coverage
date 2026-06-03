# Kotlin + Swift scorer baselines (calibration evidence)

The `test-quality` scorer's `kotlin` and `swift` profiles, run over six real,
well-tested open-source suites. This is *calibration evidence* — proof the
heuristic regexes produce sensible, non-trivial numbers on real code — **not**
the validated generation experiment (that is Python/JS/TS/Go; see the README).
Every surprising count here is pinned as a named regression in
`.claude/skills/test-quality/tests/test_score.py`.

Reproduce: clone each repo (URLs in `scripts/setup_cross_language.py`), then
`python .claude/skills/test-quality/scripts/score.py --lang <lang> --tests <clone>`.

## Suites

- **kotlinx-serialization** (`kotlin`, kotlin.test / Kotest) @ `b51076f` — JSON/CBOR/ProtoBuf serialization
- **kotlinx-datetime** (`kotlin`, kotlin.test) @ `2443a61` — date/time arithmetic & parsing
- **kotlin-result** (`kotlin`, kotlin.test (+coroutines runTest)) @ `38a3915` — Result<V,E> monad
- **swift-argument-parser** (`swift`, XCTest) @ `955d761` — declarative CLI parsing
- **swift-collections** (`swift`, XCTest + Swift Testing) @ `9ade2f7` — Deque/OrderedSet/BitSet/…
- **SwiftyJSON** (`swift`, XCTest) @ `8805b54` — ergonomic JSON access

## Scores (whole-repo; the per-language `test_file` regex filters to test files)

| suite | lang | files | tests | D1 loc/test | D2 param | A1 | A2 | A4 | A5 | C1 | C2 | B1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| kotlinx-serialization | kotlin | 337 | 1618 | 21.55 | 0.03 | 21 | 1 | 0 | 1 | 0 | 0 | 211 |
| kotlinx-datetime | kotlin | 95 | 687 | 21.04 | 0.0 | 3 | 0 | 0 | 0 | 0 | 0 | 127 |
| kotlin-result | kotlin | 20 | 387 | 16.56 | 0.0 | 0 | 0 | 0 | 0 | 0 | 120 | 0 |
| swift-argument-parser | swift | 62 | 565 | 25.57 | 0.0 | 0 | n/a | 0 | 0 | 0 | 6 | 14 |
| swift-collections | swift | 109 | 1095 | 31.51 | 0.004 | 0 | n/a | 0 | 0 | 0 | 0 | 36 |
| SwiftyJSON | swift | 18 | 149 | 18.67 | 0.0 | 0 | n/a | 0 | 0 | 0 | 0 | 24 |

Direction: A.1/A.2/A.4/A.5/C.1/D.1 lower-better; B.1/D.2 higher-better; C.2 reported-only.

## Reading the numbers

- **A.1/A.4/A.5/C.1 ≈ 0** across the board: these are exemplary suites — they
  don't assert on error-message substrings, recompute crypto, `||`-join matches,
  or hand-mock the unit. The scorer correctly reports near-zero, not noise.
- **B.1 tracks the domain**: kotlinx.serialization (211) and kotlinx-datetime (127)
  pin many JSON / ISO-8601 string vectors; kotlin-result (0) tests `Result` with
  short (<12-char) values, so its fixed-vector count is honestly low.
- **C.2 = 120 for kotlin-result** is its coroutine `runTest { }` usage — a legit
  framework primitive (reported, not penalized), *not* a hand mock.
- **Swift A.2 = n/a**: `@testable import` of `internal` is idiomatic and `private`
  is unreachable, so there is no countable private-access smell (as in Go).
- **D.2 ≈ 0** for the XCTest/kotlin.test suites: they parametrize via hand loops
  rather than `@ParameterizedTest`/`@Test(arguments:)`, which the rubric scores as
  less reuse — accurate, and exactly what a generated suite would beat.

## Known heuristic limits (documented, not bugs)

- Kotest **StringSpec** (`"name" { … }`) and BehaviorSpec given/when/then leaves
  aren't counted; FunSpec/Describe/Should (`name("…") { … }`) are.
- B.1 counts a Swift string literal even when it contains `\(…)` interpolation
  (mirrors how the JS profile treats template literals).
- Project-specific assert helpers (e.g. argument-parser's `AssertErrorMessage`)
  are not introspected, so their pinned literals don't add to B.1.

