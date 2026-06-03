# Generated suites (evidence)

The actual test code produced by the two executed Kotlin/Swift generation arms
(see [`../kotlin-swift-generation.md`](../kotlin-swift-generation.md)). These are
**preserved as evidence** — they are written against the *target library's*
public API and do not build inside this repo; drop them back into a clone of the
target to run them.

| Dir | Target | Framework | Run command | Green |
|---|---|---|---|---|
| `kotlin-result/` | [michaelbull/kotlin-result](https://github.com/michaelbull/kotlin-result) `kotlin-result` module → `src/commonTest/kotlin/com/github/michaelbull/result/` | kotlin.test | `./gradlew :kotlin-result:jvmTest` | 63 tests, 0 failures |
| `SwiftyJSON/` | [SwiftyJSON/SwiftyJSON](https://github.com/SwiftyJSON/SwiftyJSON) → `Tests/SwiftJSONTests/` | Swift Testing | `swift test` | 20 tests, 0 failures |

Reproduce: clone the target at the SHA in
[`../kotlin-swift-baselines.md`](../kotlin-swift-baselines.md), delete the human
tests, copy these files into the path above, and run the command. Score with
`score.py --lang <kotlin|swift> --tests <gen-dir> --baseline <human-tests>`.
