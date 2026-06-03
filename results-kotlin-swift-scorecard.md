# Kotlin + Swift scorecard — full 3-policy matrix (gen vs baseline)

Generated suites scored against each repo's human baseline with the
multi-language `score.py`. Cell = `gen`v`base` then ✓ win / ✗ loss / = tie; `·` = n/a. `green` and passed/failed are from the real toolchain run.

## Baselines (whole human suite)

- **kotlinx-serialization** (kotlin): tests=1618 loc=34861 A1=21 A2=1 A4=0 A5=1 C1=0 B1=211 D1=21.55 D2=0.03  _(scope: JSON format module (generated into :kotlinx-serialization-json-tests, JUnit5 wired into that module's build.gradle.kts as the test harness); whole human suite (1618 tests) is the baseline)_
- **kotlinx-datetime** (kotlin): tests=687 loc=14452 A1=3 A2=0 A4=0 A5=0 C1=0 B1=127 D1=21.04 D2=0.0  _(scope: core date/time value types (LocalDate/Time/DateTime, periods, units, UtcOffset); whole human suite (687 tests) is the baseline. Run skips the JPMS module-info task (needs a JDK 11 toolchain this box lacks; unrelated to tests))_
- **kotlin-result** (kotlin): tests=387 loc=6407 A1=0 A2=0 A4=0 A5=0 C1=0 B1=0 D1=16.56 D2=0.0  _(scope: core kotlin-result module public Result<V,E> API; whole human suite (387 tests) is the baseline)_
- **swift-argument-parser** (swift): tests=565 loc=14449 A1=0 A2=None A4=0 A5=0 C1=0 B1=14 D1=25.57 D2=0.0  _(scope: ArgumentParserEndToEndTests target — end-to-end parsing via the public ParsableCommand API (Swift Testing); whole human suite (565 tests) is the baseline)_
- **swift-collections** (swift): tests=1095 loc=34498 A1=0 A2=None A4=0 A5=0 C1=0 B1=36 D1=31.51 D2=0.004  _(scope: OrderedCollections module (OrderedSet + OrderedDictionary value semantics, Swift Testing); whole human suite (1095 tests) is the baseline)_
- **SwiftyJSON** (swift): tests=149 loc=2782 A1=0 A2=None A4=0 A5=0 C1=0 B1=24 D1=18.67 D2=0.0  _(scope: core JSON value contract via import SwiftyJSON; whole human XCTest suite (149 tests) is the baseline)_

## Arms

| repo/policy | green | P/F | A1 | A2 | A4 | A5 | C1 | B1 | D1 | D2 | W/L/T | better |
|---|:--:|---|---|---|---|---|---|---|---|---|:--:|:--:|
| kotlinx-serialization/oneshot | 🔴 | 0/0 | 0v21✓ | 0v1✓ | 0v0= | 0v1✓ | 0v0= | 10v211✗ | 11.46v21.55✓ | 0.171v0.03✓ | 5/1/2 | **yes** |
| kotlinx-serialization/iter2 | 🟢 | 73/0 | 0v21✓ | 0v1✓ | 0v0= | 0v1✓ | 0v0= | 20v211✗ | 10.92v21.55✓ | 0.137v0.03✓ | 5/1/2 | **yes** |
| kotlinx-serialization/iter20 | 🟢 | 106/0 | 0v21✓ | 0v1✓ | 0v0= | 0v1✓ | 0v0= | 28v211✗ | 11.21v21.55✓ | 0.11v0.03✓ | 5/1/2 | **yes** |
| kotlinx-datetime/oneshot | 🟢 | 46/0 | 0v3✓ | 0v0= | 0v0= | 0v0= | 0v0= | 8v127✗ | 10.89v21.04✓ | 0v0= | 2/1/5 | **yes** |
| kotlinx-datetime/iter2 | 🟢 | 53/0 | 0v3✓ | 0v0= | 0v0= | 0v0= | 0v0= | 16v127✗ | 10.85v21.04✓ | 0v0= | 2/1/5 | **yes** |
| kotlinx-datetime/iter20 | 🟢 | 68/0 | 0v3✓ | 0v0= | 0v0= | 0v0= | 0v0= | 22v127✗ | 10.84v21.04✓ | 0v0= | 2/1/5 | **yes** |
| kotlin-result/oneshot | 🟢 | 61/0 | 0v0= | 0v0= | 0v0= | 0v0= | 0v0= | 52v0✓ | 6.93v16.56✓ | 0v0= | 2/0/6 | **yes** |
| kotlin-result/iter2 | 🟢 | 86/0 | 0v0= | 0v0= | 0v0= | 0v0= | 0v0= | 71v0✓ | 7.19v16.56✓ | 0v0= | 2/0/6 | **yes** |
| kotlin-result/iter20 | 🟢 | 63/0 | 0v0= | 0v0= | 0v0= | 0v0= | 0v0= | 50v0✓ | 6.7v16.56✓ | 0v0= | 2/0/6 | **yes** |
| swift-argument-parser/oneshot | 🔴 | 0/0 | 0v0= | ·v·· | 0v0= | 0v0= | 0v0= | 0v14✗ | 17.6v25.57✓ | 0.5v0✓ | 2/1/4 | **yes** |
| swift-argument-parser/iter2 | 🟢 | 20/0 | 0v0= | ·v·· | 0v0= | 0v0= | 0v0= | 5v14✗ | 16.3v25.57✓ | 0.522v0✓ | 2/1/4 | **yes** |
| swift-argument-parser/iter20 | 🟢 | 31/0 | 0v0= | ·v·· | 0v0= | 0v0= | 0v0= | 12v14✗ | 16.03v25.57✓ | 0.424v0✓ | 2/1/4 | **yes** |
| swift-collections/oneshot | 🔴 | 0/0 | 0v0= | ·v·· | 0v0= | 0v0= | 0v0= | 3v36✗ | 11.42v31.51✓ | 0.097v0.004✓ | 2/1/4 | **yes** |
| swift-collections/iter2 | 🟢 | 36/0 | 0v0= | ·v·· | 0v0= | 0v0= | 0v0= | 31v36✗ | 12.36v31.51✓ | 0.139v0.004✓ | 2/1/4 | **yes** |
| swift-collections/iter20 | 🟢 | 42/0 | 0v0= | ·v·· | 0v0= | 0v0= | 0v0= | 45v36✓ | 12.6v31.51✓ | 0.119v0.004✓ | 3/0/4 | **yes** |
| SwiftyJSON/oneshot | 🟢 | 19/0 | 0v0= | ·v·· | 0v0= | 0v0= | 0v0= | 20v24✗ | 12.42v18.67✓ | 0.105v0✓ | 2/1/4 | **yes** |
| SwiftyJSON/iter2 | 🟢 | 20/0 | 0v0= | ·v·· | 0v0= | 0v0= | 0v0= | 30v24✓ | 13.35v18.67✓ | 0.1v0✓ | 3/0/4 | **yes** |
| SwiftyJSON/iter20 | 🟢 | 20/0 | 0v0= | ·v·· | 0v0= | 0v0= | 0v0= | 28v24✓ | 10.5v18.67✓ | 0.1v0✓ | 3/0/4 | **yes** |

_Direction: A.1/A.2/A.4/A.5/C.1/D.1 lower-better; B.1/D.2 higher-better. Raw-count axes (A.1, B.1) scale with suite size — read alongside test_count. oneshot is allowed to ship red (one pass, no repair); iter2/iter20 must be green._
