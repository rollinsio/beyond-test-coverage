# Scorer-check — JS/Go profile validation

Baseline-only measurement of the bundled `test-quality` scorer over six
cloned OSS suites. **This is profile validation, not a benchmark run:**
there is no generated suite and no win/loss verdict — only confirmation
that each auto-counted axis fires sensibly on real framework idioms.

Direction: ↓ lower-is-better, ↑ higher-is-better. `n/a` = axis not
reliably countable for that language (excluded from any tally).

| repo | lang | head | files | tests | loc | A1 ↓ | A2 ↓ | A4 ↓ | A5 ↓ | C1 ↓ | B1 ↑ | D1 ↓ | D2 ↑ | C2 |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| expressjs/express | js | `dae209a` | 91 | 1128 | 16439 | 25 | 2 | 0 | 0 | 0 | 28 | 14.57 | 0 | 879 |
| auth0/node-jsonwebtoken | js | `02688b9` | 34 | 253 | 3799 | 15 | 0 | 1 | 0 | 0 | 21 | 15.02 | 0 | 9 |
| colinhacks/zod | js | `bbc68f9` | 172 | 1946 | 37466 | 69 | 497 | 0 | 0 | 0 | 915 | 19.25 | 0 | 0 |
| go-chi/chi | go | `3b17157` | 24 | 111 | 5957 | 0 | n/a | 0 | 0 | 0 | 110 | 53.67 | 0.369 | 100 |
| tidwall/gjson | go | `7d8b382` | 1 | 98 | 2760 | 0 | n/a | 0 | 0 | 0 | 11 | 28.16 | 0.02 | 0 |
| golang-jwt/jwt | go | `e8e5b83` | 19 | 45 | 3510 | 1 | n/a | 0 | 0 | 0 | 9 | 78 | 0.378 | 0 |

## Notes (what each axis confirms / caveats)

- **express** = `node:assert` + supertest. A.1 catches `assert.throws(fn, /re/)`;
  B.1 catches `assert.strictEqual(x, 'literal')`; C.2 is supertest `.expect`.
- **jsonwebtoken** = Chai BDD + chai-assert + `sinon.useFakeTimers`. A.1 catches
  `.to.throw('msg')` and `.message…include`; B.1 catches `.to.equal('literal')`;
  the sinon usage is **fake-timers → C.2** (legit time control), so **C.1 = 0**
  is correct, not a miss.
- **zod** = Vitest + inline snapshots. B.1 is high (exact `.toBe`/snapshots).
  `D2 = 0` is a **true negative**: zod parametrizes with raw `for` loops, not
  framework `.each` tables.
- **Go** A.2 = `n/a` (same-package access to unexported names is idiomatic).
  `D1_loc_per_test` is inflated (counts `func TestX`, not `t.Run` subtests) and
  is **not** cross-language comparable — prefer D.2 for Go.

_Profiles remain `validated:false`: calibrated to fire on real idioms, but not
yet run through a full gen-vs-baseline benchmark. Treat numbers as a guide;
read the tests for the judgement axes._
