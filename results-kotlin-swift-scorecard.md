# Kotlin + Swift generation scorecard (gen vs human baseline)

Two **executed** cross-language arms: the human test suite was deleted and
regenerated from source against the quality scorecard, **verified green with the
real toolchain**, then scored against the human baseline with the multi-language
`score.py`. Cell = `gen`v`base` then ✓ win / ✗ loss / = tie; `·` = n/a.

| repo/policy | lang | green | A1 | A2 | A4 | A5 | C1 | B1 | D1 | D2 | W/L/T | better |
|---|---|---|---|---|---|---|---|---|---|---|---|:--:|
| kotlin-result/regen | kotlin | 63✓ | 0v0= | 0v0= | 0v0= | 0v0= | 0v0= | 50v0✓ | 6.7v14.95✓ | 0v0= | 2/0/6 | **yes** |
| SwiftyJSON/regen | swift | 20✓ | 0v0= | ·v·· | 0v0= | 0v0= | 0v0= | 28v24✓ | 10.5v18.67✓ | 0.1v0✓ | 3/0/4 | **yes** |

_Direction: A.1/A.2/A.4/A.5/C.1/D.1 lower-better; B.1/D.2 higher-better. A.2 is n/a for Swift. Raw-count B.1 scales with suite size — read alongside test_count._

- **kotlin-result** (kotlin): baseline 288 tests / loc 4307; regenerated 63 tests, all green via `./gradlew :kotlin-result:jvmTest`.
- **SwiftyJSON** (swift): baseline 149 tests / loc 2782; regenerated 20 tests, all green via `swift test`.
