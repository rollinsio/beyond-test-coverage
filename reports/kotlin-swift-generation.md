# Kotlin + Swift generation arms (executed)

Two pilot arms extending the cross-language experiment to the Kotlin and Swift
profiles. For each, the human test suite was **deleted** and **regenerated from
source** against the quality scorecard, **built and run green with the real
toolchain**, then scored against the human baseline. Scores in
[`results-kotlin-swift-scorecard.md`](../results-kotlin-swift-scorecard.md); the
regenerated test code is preserved under
[`generated-suites/`](generated-suites/).

This is the runtime-verified complement to
[`kotlin-swift-baselines.md`](kotlin-swift-baselines.md) (which scores the scorer
on the human suites). Together they show the profiles work on real code **and**
that scorecard-driven regeneration beats the human baseline on the countable
axes — the same result the Python/JS/TS/Go experiment reached.

## kotlin-result (`kotlin`, kotlin.test)

- **Toolchain:** JDK 17 (Temurin) + the repo's Gradle wrapper (Gradle 9.4.1).
- **Scope:** the core `kotlin-result` module — construction & accessors, the
  get/unwrap families, map/flatMap/mapError/flatten/transpose/mapBoth,
  and/andThen/or/orElse, recover/recoverIf, onOk/onErr, runCatching/toResultOr.
- **Result:** `./gradlew :kotlin-result:jvmTest` → **63 tests, 0 failures**.
- **Scorecard vs human baseline (288 tests):** **2 wins / 0 losses / 6 ties —
  BETTER.** B.1 50 v 0, D.1 6.7 v 14.95; A.1/A.2/A.4/A.5/C.1 all 0; D.2 ties at 0
  (kotlin.test in common code has no parametrize primitive — the same constraint
  the human suite is under).

## SwiftyJSON (`swift`, Swift Testing)

- **Toolchain:** Apple Swift 6.1.2 (`swift test`, SwiftPM).
- **Scope:** the core `JSON` contract — type-gated optional getters vs coercing
  `*Value` getters, index/key/path subscripts with their typed `SwiftyJSONError`
  codes (900/901/500), `exists()`, `Equatable`, literal initialisation,
  `parseJSON`, `rawString` round-trip, and `merged(with:)`.
- **Framework choice:** regenerated with **Swift Testing** (`@Test`, `#expect`,
  `@Test(arguments:)`) — the modern framework available in the 6.1 toolchain —
  which lets the suite parametrize (the human XCTest suite cannot, so D.2 = 0).
- **Result:** `swift test` → **20 tests, 0 failures**.
- **Scorecard vs human baseline (149 tests):** **3 wins / 0 losses / 4 ties —
  BETTER.** B.1 28 v 24, D.1 10.5 v 18.67, D.2 0.1 v 0; A.1/A.4/A.5/C.1 all 0;
  A.2 n/a.

## Contract adherence (judgement axes)

- **Error type, not message (A.1 / rule 1):** thrown errors are asserted by TYPE
  (`assertFailsWith<UnwrapException>`) or typed error CODE
  (`error?.errorCode == 900`), never by message substring.
- **Fixed vectors (B.1 / rule 2):** every expected value is a pinned literal.
- **Public API only (rule 3):** kotlin-result tests avoid the `@Unsafe…Access`
  `value`/`error` accessors; SwiftyJSON uses `import SwiftyJSON` (not `@testable`).
- **Behaviour, not readback (rule 4):** transforms/coercions are exercised
  (`map`, `boolValue`, subscript errors) rather than constructor read-backs.
- **No hand mocks (C.1 = 0):** both libraries are pure value logic.

## Residual risks / honest scope

- These are **two pilot arms**, not the full 6-repo × 3-policy matrix. They are a
  single iterated ("regen") policy each, scoped to the core public surface — not
  every corner the larger human suites cover (e.g. SwiftyJSON Codable/Mutability,
  kotlin-result Zip/Iterable/Binding/Try are out of scope here).
- B.1 is an absolute count that scales with suite size; the generated suites are
  far smaller than the baselines yet still meet/exceed it by pinning vectors
  densely. The CHANGELOG `[Unreleased]` B.1-as-ratio reshape would make this
  cleaner.
- Numbers are from the cloned `HEAD`s recorded in `kotlin-swift-baselines.md`.
