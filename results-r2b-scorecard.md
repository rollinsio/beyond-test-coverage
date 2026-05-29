# r2b — independent scorecard recompute (auto-countable axes only)

Baselines (same measure):
- **itsdangerous**: tests=37 loc=481 A1=4 A2=10 A4=10 A5=0 C1=0 B1=0 D1=13.0 D2=0.189
- **httpx**: tests=539 loc=8926 A1=7 A2=22 A4=1 A5=0 C1=3 B1=13 D1=16.56 D2=0.082
- **requests**: tests=345 loc=5132 A1=9 A2=18 A4=0 A5=0 C1=0 B1=6 D1=14.88 D2=0.223

| repo/policy | A1 | A2 | A4 | A5 | C1 | B1 | D1 | D2 | W/L/T | better |
|---|---|---|---|---|---|---|---|---|---|---|
| itsdangerous/oneshot | 0v4✓ | 6v10✓ | 5v10✓ | 0v0= | 0v0= | 2v0✓ | 15.23v13.0✗ | 0.114v0.189✗ | 4/2/2 | YES |
| itsdangerous/iter2 | 0v4✓ | 10v10= | 6v10✓ | 0v0= | 0v0= | 1v0✓ | 12.37v13.0✓ | 0.202v0.189✓ | 5/0/3 | YES |
| itsdangerous/iter20 | 0v4✓ | 15v10✗ | 10v10= | 0v0= | 0v0= | 8v0✓ | 15.92v13.0✗ | 0.252v0.189✓ | 3/2/3 | YES |
| httpx/oneshot | 4v7✓ | 11v22✓ | 0v1✓ | 0v0= | 0v3✓ | 17v13✓ | 10.61v16.56✓ | 0.047v0.082✗ | 6/1/1 | YES |
| httpx/iter2 | 3v7✓ | 13v22✓ | 0v1✓ | 0v0= | 0v3✓ | 12v13✗ | 11.45v16.56✓ | 0.086v0.082✓ | 6/1/1 | YES |
| httpx/iter20 | 2v7✓ | 16v22✓ | 0v1✓ | 0v0= | 1v3✓ | 15v13✓ | 13.65v16.56✓ | 0.088v0.082✓ | 7/0/1 | YES |
| requests/oneshot | 0v9✓ | 28v18✗ | 0v0= | 0v0= | 0v0= | 2v6✗ | 8.82v14.88✓ | 0.104v0.223✗ | 2/3/3 | no |
| requests/iter2 | 0v9✓ | 12v18✓ | 0v0= | 0v0= | 1v0✗ | 6v6= | 8.7v14.88✓ | 0.094v0.223✗ | 3/2/3 | YES |
| requests/iter20 | 0v9✓ | 7v18✓ | 0v0= | 0v0= | 0v0= | 9v6✓ | 11.64v14.88✓ | 0.224v0.223✓ | 5/0/3 | YES |

Cell = `gen`v`base` then ✓ win / ✗ loss / = tie. Auto-scored axes only (A1,A2,A4,A5,C1,B1,D1,D2). A.3/A.6/B.2/B.3/E.* need semantic judgement — see each SUMMARY.md.