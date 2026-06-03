# Kotlin + Swift generation matrix (executed — full 6×3)

The cross-language experiment extended to Kotlin and Swift: **six libraries ×
three iteration policies = 18 arms**, run the same way as the JS/TS + Go matrix.
For each arm the human test suite was **deleted** and **regenerated from source**
against the quality scorecard, **built and run with the real toolchain**, then
scored against the human baseline. Scores in
[`results-kotlin-swift-scorecard.md`](../results-kotlin-swift-scorecard.md); the
decisive (iter20) suite for every repo is preserved under
[`generated-suites/`](generated-suites/).

This is the runtime-verified complement to
[`kotlin-swift-baselines.md`](kotlin-swift-baselines.md) (which scores the scorer
on the human suites). Together they show the profiles work on real code **and**
that scorecard-driven regeneration beats the human baseline on the countable axes
— the same result the Python/JS/TS/Go experiment reached.

> **Validation tier.** The Kotlin and Swift `score.py` profiles are *heuristic*
> (regex-based, `validated: false`), not the empirically-validated Python set.
> Every arm below was **built and run green (or honestly recorded red) with the
> real toolchain**, and every W/L/T was **independently re-scored by the
> orchestrator** (not trusted from the generating agent) — but the axis counts
> remain trend indicators confirmed by reading, not validated ground truth.

## Headline

**18 / 18 arms beat their human baseline** on the countable axes (wins > losses).
**15 / 18 arms are green**; the three red arms are all **oneshot** (one pass, no
repair) and fail to *compile*, not on a wrong assertion — exactly the
"one pass wins the quality axes but ships failures; iteration makes it green"
finding from the Python/JS experiment. The wins are structural and consistent:
the generated suites are far more **LOC-efficient** (D.1) and, where the
framework allows it, **parametrized** (D.2); they carry **zero** message-substring
(A.1), private-access (A.2), recomputed (A.4), or `||`-joined (A.5) asserts and
**zero hand mocks** (C.1) of the unit.

## Toolchains & scope (per repo)

| repo | lang | scope (stated) | run command | baseline |
|---|---|---|---|---|
| kotlinx-serialization | kotlin | JSON format module (gen into `:kotlinx-serialization-json-tests`, JUnit5 wired as harness) | `./gradlew :kotlinx-serialization-json-tests:jvmTest` | whole suite, 1618 tests |
| kotlinx-datetime | kotlin | core date/time value types | `./gradlew :kotlinx-datetime:jvmTest -x compileJavaModuleInfo` | whole suite, 687 tests |
| kotlin-result | kotlin | core `Result<V,E>` public API | `./gradlew :kotlin-result:jvmTest` | whole suite, 387 tests |
| swift-argument-parser | swift | `ArgumentParserEndToEndTests` (public `ParsableCommand`) | `swift test --filter ArgumentParserEndToEndTests` | whole suite, 565 tests |
| swift-collections | swift | `OrderedCollections` (OrderedSet/Dictionary) | `swift test --filter OrderedCollectionsTests` | whole suite, 1095 tests |
| SwiftyJSON | swift | core `JSON` value contract | `swift test` | whole suite, 149 tests |

- JDK 17 (Temurin) + each repo's Gradle wrapper for Kotlin; Apple Swift 6.1.2 for Swift.
- The two largest repos (kotlinx-serialization, swift-collections) are **scoped to
  one coherent core module**; the rest target the core public surface. The baseline
  in every comparison is the **whole** human suite — so the scoped arms are
  compared against a much larger corpus (this is why they lose the absolute B.1
  count on the big repos; see caveats).
- `kotlinx-datetime`'s run skips the JPMS `compileJavaModuleInfo` task, which
  requires a JDK 11 toolchain this machine lacks and is unrelated to the tests.

## Per-policy result (green = real toolchain run; W/L/T = independently re-scored)

| repo | oneshot | iter2 | iter20 |
|---|---|---|---|
| kotlinx-serialization | 🔴 compile-fail · 5/1/2 | 🟢 73 · 5/1/2 | 🟢 106 · 5/1/2 |
| kotlinx-datetime | 🟢 46 · 2/1/5 | 🟢 53 · 2/1/5 | 🟢 68 · 2/1/5 |
| kotlin-result | 🟢 61 · 2/0/6 | 🟢 86 · 2/0/6 | 🟢 63 · 2/0/6 |
| swift-argument-parser | 🔴 compile-fail · 2/1/4 | 🟢 20 · 2/1/4 | 🟢 31 · 2/1/4 |
| swift-collections | 🔴 compile-fail · 2/1/4 | 🟢 36 · 2/1/4 | 🟢 42 · **3/0/4** |
| SwiftyJSON | 🟢 19 · 2/1/4 | 🟢 20 · **3/0/4** | 🟢 20 · **3/0/4** |

`green` is the passing test count from the real run (a 🔴 oneshot produced no test
binary — the source still scores its axes statically). Every cell is "better"
(W > L).

### What iteration buys
The iteration budget is what makes a suite green *and* widens the margin:
- **oneshot red → green:** swift-argument-parser (a `private` enum used in
  `@Test(arguments:)` — illegal in Swift Testing), swift-collections (mutating a
  `let` constant), kotlinx-serialization (a `JsonObject`/`Map` type-inference
  site) each failed to compile in one pass and were *not* repaired; iter2 fixed
  them in one round.
- **axis deepening:** swift-collections B.1 climbs 3 → 31 → 45 across oneshot →
  iter2 → iter20, flipping its B.1 loss into a win; kotlinx-serialization B.1
  10 → 20 → 28 while staying green.

## Contract adherence (judgement axes)

- **Error type/code, not message (A.1 / rule 1):** Kotlin uses
  `assertFailsWith<T>` and asserts the stable public supertype
  (`SerializationException`, `IllegalArgumentException`,
  `DateTimeArithmeticException`); Swift asserts typed `SwiftyJSONError` codes and
  argument-parser error *category* via `exitCode(for:)` — never message prose.
- **Fixed vectors (B.1 / rule 2):** expected values are pinned literals, each
  verified out-of-band before pasting (logged per worktree in
  `.rex_metrics/verifications.log`); several agents caught real surprises this way
  (e.g. `symmetricDifference([1,2,3,4],[0,2,4,6]) == [1,3,0,6]`, the negative-value
  `--ratio=-2.5` joined-form parsing rule, `toErrorUnlessNull` semantics).
- **Public API only (rule 3):** no `@Unsafe…`/internal Kotlin accessors; Swift
  uses `import <Module>` (not `@testable`) so A.2 stays n/a.
- **No hand mocks (C.1 = 0):** all six libraries are pure value/parse logic.
- **Mutation spot-checks:** several agents perturbed a pinned vector and confirmed
  the test fails, i.e. the assertions are mutation-sensitive, not tautological.

## Residual risks / honest scope

- **B.1 is an absolute count that scales with suite size.** The scoped arms are
  compared against the *whole* human suite, so on the big repos (kxser baseline
  B.1=211 across 1618 tests; scoll 36 across 1095; kxdt 127 across 687) a compact
  generated suite cannot out-count it and "loses" B.1 despite far higher
  per-test pin density. It still wins overall (more A-axis + D-axis wins than the
  one B.1 loss). The CHANGELOG `[Unreleased]` B.1-as-ratio reshape would remove
  this artifact. The Swift B.1 regex also only counts string literals ≥12 chars,
  so genuinely-pinned `Int`/`Bool`/enum/array vectors don't register — the true
  fixed-vector density is higher than the count shows.
- **D.2 ties at 0 for the kotlin.test arms** (kotlin-result, kotlinx-datetime):
  `commonTest` has no `@ParameterizedTest` primitive on the classpath — the same
  constraint binding the human baseline — so parametrization isn't a lever there.
- **Scope.** These arms target each library's core public surface, not every
  corner the human suites cover (kxser: multiplatform/streaming/contextual
  serializers; scoll: the other collection modules; sap: help/usage/completion;
  kxdt: timezone/Instant/DST). They are focused, high-rigor slices, not full
  replacements.
- **Heuristic scorer** (see the validation-tier note above). Coverage floor
  (F.1/F.2) was not separately instrumented for these arms.
- Numbers are from the cloned `HEAD`s recorded in `kotlin-swift-baselines.md`. The
  generated worktrees live under the git-ignored `bench-clones/`; the
  manifest that drives scoring is `bench-clones/.matrix-manifest.json` and the
  scorer is [`scripts/score_kotlin_swift_matrix.py`](../scripts/score_kotlin_swift_matrix.py).
