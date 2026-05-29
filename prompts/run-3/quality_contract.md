# Quality contract (anti-fragility rules)

These are the rules the scorecard rewards. Each maps to a scored axis.
Examples are given in both JS/TS and Go; apply the one for `{LANG}`.

## A.1 — Don't assert on error-message substrings (lower is better)

Coupling a test to human-readable error *prose* makes it brittle. Test
the error *type* / *code* / *structured field*, not a substring of its
message.

- ✗ JS: `expect(() => f()).to.throw('invalid signature')`
- ✗ JS: `expect(err.message).to.include('expired')`
- ✓ JS: `expect(() => f()).to.throw(TokenExpiredError)` ; assert
  `err.name === 'TokenExpiredError'` or a structured `err.code`.
- ✗ Go: `assert.EqualError(err, "unexpected end of JSON")` /
  `strings.Contains(err.Error(), "...")`
- ✓ Go: `errors.Is(err, ErrInvalidKey)` / `var te *ValidationError;
  errors.As(err, &te)` then assert a field.

## B.1 — Prefer fixed, known-good expected values (higher is better)

Assert against a literal you computed once and trust — a known token, a
serialized output, a digest, an inline snapshot. This is the opposite
of A.1 and of A.4.

- ✓ JS: `expect(token).to.equal('eyJhbGciOiJIUzI1NiIs...')` (a fixed,
  precomputed JWT) ; `expect(result).toMatchInlineSnapshot(...)`.
- ✓ Go: `want := "0x1f3b..."; if got != want { t.Errorf(...) }`.

## A.4 — Don't recompute the expected value with the code under test

If you derive the "expected" value by re-running the same algorithm the
implementation uses, the test proves nothing. Pin a literal (→ B.1).

- ✗ JS: `const expected = crypto.createHmac('sha256', k).update(d)...;
  expect(sig).to.equal(expected)`
- ✗ Go: `expected := sha256.Sum256(data); ...`
- ✓ Compute it once out-of-band, paste the literal, assert against it.

## A.2 — Reach the code through its public API (lower is better)

- ✗ JS: poking `obj._private` / casting `as any` to touch internals.
- Go: same-package `_test.go` access to unexported names is idiomatic —
  the scorer treats A.2 as n/a for Go. Don't contort to avoid it.

## A.5 — Don't `||`-join alternative error matches (lower is better)

- ✗ `expect(msg.includes('a') || msg.includes('b')).to.be.true` — pick
  the one true expectation.

## C.1 — Zero hand mocks of the unit (lower is better, target 0)

Don't hand-roll stubs/spies/mocks of the thing you're testing. Use the
framework's real-I/O primitives (supertest, httptest) or just construct
real objects. Controlling *time* (`sinon.useFakeTimers`) or a real test
*server* (`httptest.NewServer`) is fine — that's C.2, which is not
penalized.

## D.1 / D.2 — Be LOC-efficient and parametrize (D.1 lower, D.2 higher)

Fold repetitive cases into table-driven tests, not copy-paste.

- ✓ JS: `it.each([...])('case %s', ...)` (Jest/Vitest) or a `forEach`
  table with one `it` per row.
- ✓ Go: a `[]struct{...}` table with `t.Run(tc.name, func(t...){...})`.

## E — Correctness obligations

- Every test passes (green). A failing test is either fixed or recorded
  as a genuine bug-find, never left red.
- Before asserting any non-obvious stdlib/library behavior, **verify it
  out-of-band** ({VERIFY_CMD}) and log it to
  `.rex_metrics/verifications.log`. Don't assert what you assume.
