# Quality scorecard — how you are judged

Success = **beating the baseline on the auto-counted axes** below, with
all tests green. The bundled `test-quality` scorer computes them and
prints the Win/Loss/Tie tally for you.

## The auto-counted axes (direction in parens)

| axis | meaning | direction |
|------|---------|-----------|
| A.1 | substring/partial matches on error messages | ↓ lower |
| A.2 | private-symbol / internal access (n/a for Go) | ↓ lower |
| A.4 | recomputed crypto/encoding expected values | ↓ lower |
| A.5 | `||`-joined error matches | ↓ lower |
| C.1 | hand mocks of the unit (target 0) | ↓ lower |
| B.1 | fixed-vector asserts / inline snapshots | ↑ higher |
| D.1 | test LOC per test | ↓ lower |
| D.2 | parametrize/table ratio | ↑ higher |

C.2 (framework primitives: supertest / httptest / fake-timers) is
reported, not scored — it's the *good* side of the mocking line.

## The "did I improve?" gate

You win an axis when your value beats the baseline's in the right
direction; a higher win-count than loss-count means the suite is
**better than baseline**. Ties don't help. Your job is to maximize
wins and drive losses to zero.

## Running the scorer

```bash
{SCORE_CMD}
```

This prints each axis as `gen vs base` with ✓/✗/= and a final tally.
Run it on the baseline first (your target), then after each iteration.

## Judgement axes (no auto-count — satisfy them by construction)

- **A.3** no tautological readbacks (asserting a value you just set).
- **A.6** no hand-coded character sets / magic tables that duplicate
  the implementation.
- **B.2** boundary tests for the comparisons in the source.
- **B.3** integration tests through framework primitives.
- **E.2** out-of-band-verified assumptions (logged).

The scorer can't see these; a reviewer can. Don't sacrifice them to
move an auto-counted number.
