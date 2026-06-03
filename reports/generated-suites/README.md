# Generated suites (evidence)

The **decisive (iter20) generated suite for each repo** in the Kotlin/Swift
3-policy matrix (see [`../kotlin-swift-generation.md`](../kotlin-swift-generation.md)).
These are **preserved as evidence** — they are written against the *target
library's* public API and do not build inside this repo; drop them back into a
clone of the target at the recorded SHA to run them.

The oneshot and iter2 arms (and these iter20 arms) were generated in git
worktrees under the git-ignored `bench-clones/`; the full per-policy W/L/T and
green/red tally is in
[`../../results-kotlin-swift-scorecard.md`](../../results-kotlin-swift-scorecard.md),
driven by `bench-clones/.matrix-manifest.json` via
`scripts/score_kotlin_swift_matrix.py`.

| Dir | Target | Framework | iter20 run command | iter20 green |
|---|---|---|---|---|
| `kotlin-result/` | michaelbull/kotlin-result `kotlin-result` module → `src/commonTest/kotlin/com/github/michaelbull/result/` | kotlin.test | `./gradlew :kotlin-result:jvmTest` | 63 tests |
| `kotlinx-serialization/` | Kotlin/kotlinx.serialization JSON → `:kotlinx-serialization-json-tests` `jvmTest` (JUnit5 wired in that module's build.gradle.kts) | kotlin.test + JUnit5 | `./gradlew :kotlinx-serialization-json-tests:jvmTest` | 106 tests |
| `kotlinx-datetime/` | Kotlin/kotlinx-datetime core → `core/common/test/kotlinx/datetime/` | kotlin.test | `./gradlew :kotlinx-datetime:jvmTest -x compileJavaModuleInfo` | 68 tests |
| `swift-argument-parser/` | apple/swift-argument-parser → `Tests/ArgumentParserEndToEndTests/` | Swift Testing | `swift test --filter ArgumentParserEndToEndTests` | 31 tests |
| `swift-collections/` | apple/swift-collections → `Tests/OrderedCollectionsTests/` | Swift Testing | `swift test --filter OrderedCollectionsTests` | 42 tests |
| `SwiftyJSON/` | SwiftyJSON/SwiftyJSON → `Tests/SwiftJSONTests/` | Swift Testing | `swift test` | 20 tests |

(`kotlinx-serialization/JsonModel.kt` holds the shared `@Serializable` model
classes the JSON tests encode/decode — it is fixture, not a test file.)

Reproduce: clone the target at the SHA in
[`../kotlin-swift-baselines.md`](../kotlin-swift-baselines.md), delete the human
tests in scope, copy these files into the path above, and run the command. Score
with `score.py --lang <kotlin|swift> --tests <gen-dir> --baseline <human-tests>`.
