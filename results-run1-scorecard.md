# run1 — independent scorecard recompute (auto-countable axes only)

Baselines (same measure):
- **itsdangerous**: tests=37 loc=481 A1=4 A2=10 A4=10 A5=0 C1=0 B1=0 D1=13.0 D2=0.189
- **httpx**: tests=539 loc=8926 A1=7 A2=22 A4=1 A5=0 C1=3 B1=13 D1=16.56 D2=0.082
- **requests**: tests=345 loc=5132 A1=9 A2=18 A4=0 A5=0 C1=0 B1=6 D1=14.88 D2=0.223

| repo/policy | A1 | A2 | A4 | A5 | C1 | B1 | D1 | D2 | W/L/T | better |
|---|---|---|---|---|---|---|---|---|---|---|
| itsdangerous/oneshot | 10v4✗ | 9v10✓ | 10v10= | 0v0= | 0v0= | 2v0✓ | 6.86v13.0✓ | 0.0v0.189✗ | 3/2/3 | YES |
| itsdangerous/iter2 | 10v4✗ | 15v10✗ | 8v10✓ | 1v0✗ | 0v0= | 2v0✓ | 6.73v13.0✓ | 0.0v0.189✗ | 3/4/1 | no |
| itsdangerous/iter20 | 11v4✗ | 8v10✓ | 12v10✗ | 0v0= | 0v0= | 2v0✓ | 6.88v13.0✓ | 0.0v0.189✗ | 3/3/2 | no |
| httpx/oneshot | 9v7✗ | 5v22✓ | 0v1✓ | 0v0= | 0v3✓ | 6v13✗ | 9.34v16.56✓ | 0.002v0.082✗ | 4/3/1 | YES |
| httpx/iter2 | 16v7✗ | 13v22✓ | 0v1✓ | 0v0= | 0v3✓ | 6v13✗ | 10.22v16.56✓ | 0.0v0.082✗ | 4/3/1 | YES |
| httpx/iter20 | 7v7= | 23v22✗ | 1v1= | 0v0= | 3v3= | 13v13= | 16.56v16.56= | 0.078v0.082✗ | 0/2/6 | no |
| requests/oneshot | 1v9✓ | 30v18✗ | 0v0= | 0v0= | 2v0✗ | 6v6= | 6.81v14.88✓ | 0.0v0.223✗ | 2/3/3 | no |
| requests/iter2 | 1v9✓ | 42v18✗ | 0v0= | 0v0= | 21v0✗ | 4v6✗ | 8.24v14.88✓ | 0.0v0.223✗ | 2/4/2 | no |
| requests/iter20 | 0v9✓ | 40v18✗ | 0v0= | 0v0= | 1v0✗ | 4v6✗ | 7.4v14.88✓ | 0.0v0.223✗ | 2/4/2 | no |

Cell = `gen`v`base` then ✓ win / ✗ loss / = tie. Auto-scored axes only (A1,A2,A4,A5,C1,B1,D1,D2). A.3/A.6/B.2/B.3/E.* need semantic judgement — see each SUMMARY.md.