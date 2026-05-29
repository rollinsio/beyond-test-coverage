# Run 3 scorecard — JS/TS + Go (gen vs baseline)

Generated suites scored against each repo's human baseline with the
multi-language `score.py`. Cell = `gen`v`base` then ✓ win / ✗ loss / = tie; `·` = n/a (axis not countable for the language).

## Baselines

- **express** (js): tests=1128 loc=16439 A1=25 A2=2 A4=0 A5=0 C1=0 B1=28 D1=14.57 D2=0.0
- **jsonwebtoken** (js): tests=253 loc=3799 A1=15 A2=0 A4=1 A5=0 C1=0 B1=21 D1=15.02 D2=0.0
- **zod** (js): tests=1941 loc=37068 A1=69 A2=497 A4=0 A5=0 C1=0 B1=914 D1=19.1 D2=0.0
- **chi** (go): tests=111 loc=5957 A1=0 A2=None A4=0 A5=0 C1=0 B1=147 D1=53.67 D2=0.369
- **gjson** (go): tests=98 loc=2760 A1=0 A2=None A4=0 A5=0 C1=0 B1=20 D1=28.16 D2=0.02
- **golang-jwt** (go): tests=45 loc=3510 A1=1 A2=None A4=0 A5=0 C1=0 B1=16 D1=78.0 D2=0.378

## Arms

| repo/policy | A1 | A2 | A4 | A5 | C1 | B1 | D1 | D2 | W/L/T | better |
|---|---|---|---|---|---|---|---|---|---|:--:|
| express/oneshot | 0v25✓ | 0v2✓ | 0v0= | 0v0= | 0v0= | 3v28✗ | 9.17v14.57✓ | 0.179v0✓ | 4/1/3 | **yes** |
| express/iter2 | 0v25✓ | 0v2✓ | 0v0= | 0v0= | 0v0= | 30v28✓ | 11.05v14.57✓ | 0.194v0✓ | 5/0/3 | **yes** |
| express/iter20 | 0v25✓ | 0v2✓ | 0v0= | 0v0= | 0v0= | 34v28✓ | 9.75v14.57✓ | 0.12v0✓ | 5/0/3 | **yes** |
| jsonwebtoken/oneshot | 0v15✓ | 0v0= | 0v1✓ | 0v0= | 0v0= | 4v21✗ | 9.27v15.02✓ | 0.258v0✓ | 4/1/3 | **yes** |
| jsonwebtoken/iter2 | 0v15✓ | 0v0= | 0v1✓ | 0v0= | 0v0= | 25v21✓ | 8.2v15.02✓ | 0.136v0✓ | 5/0/3 | **yes** |
| jsonwebtoken/iter20 | 0v15✓ | 0v0= | 0v1✓ | 0v0= | 0v0= | 22v21✓ | 9.93v15.02✓ | 0.232v0✓ | 5/0/3 | **yes** |
| zod/oneshot | 0v69✓ | 0v497✓ | 0v0= | 0v0= | 0v0= | 19v914✗ | 7.94v19.1✓ | 0.421v0✓ | 4/1/3 | **yes** |
| zod/iter2 | 0v69✓ | 0v497✓ | 0v0= | 0v0= | 0v0= | 82v914✗ | 6.59v19.1✓ | 0.078v0✓ | 4/1/3 | **yes** |
| zod/iter20 | 0v69✓ | 0v497✓ | 0v0= | 0v0= | 0v0= | 154v914✗ | 9.25v19.1✓ | 0.114v0✓ | 4/1/3 | **yes** |
| chi/oneshot | 0v0= | ·v·· | 0v0= | 0v0= | 0v0= | 36v147✗ | 25.74v53.67✓ | 0.547v0.369✓ | 2/1/4 | **yes** |
| chi/iter2 | 0v0= | ·v·· | 0v0= | 0v0= | 0v0= | 148v147✓ | 33.12v53.67✓ | 0.817v0.369✓ | 3/0/4 | **yes** |
| chi/iter20 | 0v0= | ·v·· | 0v0= | 0v0= | 0v0= | 107v147✗ | 29.51v53.67✓ | 0.871v0.369✓ | 2/1/4 | **yes** |
| gjson/oneshot | 0v0= | ·v·· | 0v0= | 0v0= | 0v0= | 20v20= | 20.09v28.16✓ | 1.067v0.02✓ | 2/0/5 | **yes** |
| gjson/iter2 | 0v0= | ·v·· | 0v0= | 0v0= | 0v0= | 33v20✓ | 25.9v28.16✓ | 0.795v0.02✓ | 3/0/4 | **yes** |
| gjson/iter20 | 0v0= | ·v·· | 0v0= | 0v0= | 0v0= | 89v20✓ | 21.51v28.16✓ | 1.111v0.02✓ | 3/0/4 | **yes** |
| golang-jwt/oneshot | 0v1✓ | ·v·· | 0v0= | 0v0= | 0v0= | 24v16✓ | 35.73v78✓ | 1.067v0.378✓ | 4/0/3 | **yes** |
| golang-jwt/iter2 | 0v1✓ | ·v·· | 0v0= | 0v0= | 0v0= | 20v16✓ | 27.54v78✓ | 1.098v0.378✓ | 4/0/3 | **yes** |
| golang-jwt/iter20 | 0v1✓ | ·v·· | 0v0= | 0v0= | 0v0= | 46v16✓ | 30.64v78✓ | 0.928v0.378✓ | 4/0/3 | **yes** |

_Direction: A.1/A.2/A.4/A.5/C.1/D.1 lower-better; B.1/D.2 higher-better. Raw-count axes (A.1, B.1) scale with suite size — read alongside test_count._
