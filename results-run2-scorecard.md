# run2 — independent scorecard recompute (auto-countable axes only)

Baselines (same measure):
- **itsdangerous**: tests=37 loc=481 A1=4 A2=10 A4=10 A5=0 C1=0 B1=0 D1=13.0 D2=0.189
- **httpx**: tests=539 loc=8926 A1=7 A2=22 A4=1 A5=0 C1=3 B1=13 D1=16.56 D2=0.082
- **requests**: tests=345 loc=5132 A1=9 A2=18 A4=0 A5=0 C1=0 B1=6 D1=14.88 D2=0.223

| repo/policy | A1 | A2 | A4 | A5 | C1 | B1 | D1 | D2 | W/L/T | better |
|---|---|---|---|---|---|---|---|---|---|---|
| itsdangerous/oneshot | 0v4✓ | 0v10✓ | 2v10✓ | 0v0= | 0v0= | 4v0✓ | 11.96v13.0✓ | 0.268v0.189✓ | 6/0/2 | YES |
| itsdangerous/iter2 | 0v4✓ | 1v10✓ | 0v10✓ | 0v0= | 0v0= | 7v0✓ | 11.75v13.0✓ | 0.197v0.189✓ | 6/0/2 | YES |
| itsdangerous/iter20 | 0v4✓ | 14v10✗ | 0v10✓ | 0v0= | 0v0= | 3v0✓ | 10.47v13.0✓ | 0.105v0.189✗ | 4/2/2 | YES |
| httpx/oneshot | 0v7✓ | 10v22✓ | 0v1✓ | 0v0= | 0v3✓ | 7v13✗ | 11.35v16.56✓ | 0.138v0.082✓ | 6/1/1 | YES |
| httpx/iter2 | 0v7✓ | 9v22✓ | 0v1✓ | 0v0= | 0v3✓ | 16v13✓ | 13.22v16.56✓ | 0.155v0.082✓ | 7/0/1 | YES |
| httpx/iter20 | 0v7✓ | 2v22✓ | 0v1✓ | 0v0= | 0v3✓ | 7v13✗ | 10.78v16.56✓ | 0.134v0.082✓ | 6/1/1 | YES |
| requests/oneshot | 0v9✓ | 6v18✓ | 0v0= | 0v0= | 0v0= | 11v6✓ | 8.79v14.88✓ | 0.183v0.223✗ | 4/1/3 | YES |
| requests/iter2 | 0v9✓ | 11v18✓ | 0v0= | 0v0= | 0v0= | 7v6✓ | 9.6v14.88✓ | 0.182v0.223✗ | 4/1/3 | YES |
| requests/iter20 | 0v9✓ | 6v18✓ | 0v0= | 0v0= | 0v0= | 8v6✓ | 8.68v14.88✓ | 0.238v0.223✓ | 5/0/3 | YES |

Cell = `gen`v`base` then ✓ win / ✗ loss / = tie. Auto-scored axes only (A1,A2,A4,A5,C1,B1,D1,D2). A.3/A.6/B.2/B.3/E.* need semantic judgement — see each SUMMARY.md.