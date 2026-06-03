# Anti-fragility contract

Ten rules for tests that survive refactors and catch real regressions. Each is
a pattern that produces brittle, mutation-blind, or LOC-bloated suites, with the
repair. These come from a controlled experiment (llm-testgen-bench): suites that
followed them beat human-written baselines on 8 of 9 measured cells.

The examples are Python/pytest, but the *principles* are language-agnostic — the
equivalent for Jest/JUnit/RSpec/Go is the same idea with different syntax.

---

### 1. Assert on type + payload, not error-message wording.

A message is documentation; the contract is the exception type and its
structured data. Pinning prose breaks on a reword and proves nothing.

❌ `with pytest.raises(BadPayload, match="zlib"): s.loads(corrupt)`
✅
```python
with pytest.raises(BadPayload) as exc:
    s.loads(corrupt)
assert isinstance(exc.value.original_error, zlib.error)
```
Test the message *only* if the message is itself a documented part of the
contract (rare).

### 2. Pin a fixed expected value; don't recompute crypto/encoding in the test.

If the test recomputes the expected value with the same library/logic the code
uses, a bug present in both sides cancels out — the test passes through the
mutation (parallel-mutation blindness).

❌ `expected = hmac.new(key, msg, sha1).digest(); assert sign(key, msg) == expected`
✅ `assert sign(b"key", b"value") == b"\x57\xd5\xbb\x55..."  # known-good literal, computed once`

Hard-code a literal you verified once with a trusted implementation. This is the
single largest mutation-survivor risk in generated suites.

### 3. Test through the public API; don't import private symbols.

❌ `from pkg.signer import _make_keys_list` / `obj._loads_impl(...)`
✅ Find the public call that reaches the branch. If no public call reaches it,
the branch may not be a real contract worth testing.

A common trap: calling a private method with what is already its default argument
— the test would pass even if the argument were silently dropped.

### 4. Test that a value *affects behavior*, not that you can read it back.

❌ `s = Signer("k", salt="custom"); assert s.salt == "custom"`  (you just set it)
✅ `assert Signer("k", salt="a").sign(v) != Signer("k", salt="b").sign(v)`

Constructor readbacks survive every realistic mutation. Whole files of them
(`test_exc.py`-style) add coverage and zero protection.

### 5. No `or`-joined assertions that accept either outcome.

❌ `assert "Malformed timestamp" in str(e) or "does not match" in str(e)`
A bug that *swapped* the two messages passes. Instead, set up conditions so only
ONE branch is reachable, then assert that branch specifically:
✅
```python
tampered = signed[:-2] + b"XX"           # signature only — timestamp still valid
with pytest.raises(BadTimeSignature) as e:
    s.unsign(tampered)
assert "does not match" in str(e.value)
```

### 6. Use parametrize / fixtures / inheritance. Don't unroll cases.

Unrolled suites run 2–3× the LOC of a good one and silently drop cases.

❌ three near-identical `def test_*_roundtrip` bodies, one per mode
✅
```python
@pytest.mark.parametrize("mode", ("concat", "django-concat", "hmac", "none"))
def test_key_derivation(self, signer_factory, mode):
    s = signer_factory(key_derivation=mode)
    assert s.unsign(s.sign("value")) == b"value"
```
Reuse whole test classes across types via inheritance
(`class TestTimedSerializer(FreezeMixin, TestSerializer): ...`).

### 7. Write a boundary test for every comparison in the source.

Standard coverage does not distinguish `>` from `>=`. Mutation testing does, and
so should you. For each `<`, `<=`, `>`, `>=`, `==`, `!=` in the source, add a
test at the boundary (`age == max_age`, `len == limit - 1`, …).

For ordering-dependent code (`reversed(...)`, sort), construct inputs where plain
vs. reversed iteration would pick *different* results, so the order is observable.

### 8. REPL-verify any stdlib/library assumption before asserting on it.

Before writing "`base64.urlsafe_b64decode(b'!@#')` raises", run it:
```bash
python -c "import base64; print(repr(base64.urlsafe_b64decode(b'!@#$%^==')))"
```
(It doesn't raise — it filters and returns `b""`.) A one-line check is far
cheaper than a committed-wrong test. Keep a short log of what you verified.

### 9. Prefer the framework's real-I/O fixtures over `unittest.mock`.

If `pytest-httpbin`, `httpx.MockTransport`, `httpx.WSGITransport`/`ASGITransport`,
`responses`, `respx`, `freezegun`, `tmp_path`, a test DB, etc. exist, use them —
they exercise real code paths. The one benchmark suite that beat its baseline on
*every* dimension did so by adding a real-I/O integration file with **zero**
`unittest.mock`. Reach for `MagicMock`/`patch` only when there is no real
primitive (true external side effects, nondeterminism, paid APIs).

### 10. Track two mock numbers, drive only one to zero.

- `mock_real` — `MagicMock` / `Mock(` / `patch(` / `mocker` / `unittest.mock`.
  This is the quality concern; target 0.
- `mock_framework` — `MockTransport` / `WSGITransport` / `ASGITransport` /
  `monkeypatch` / `httpbin`. Legitimate; the cost of using the framework
  correctly. Don't penalize it.

---

## JavaScript / TypeScript equivalents (Jest · Vitest · Mocha/Chai/Sinon)

Same rules, different syntax. The mapping for the ones that look different:

**1. Error type, not message.**
❌ `expect(() => f()).toThrow('zlib')` · `expect(err.message).toContain('zlib')`
✅ `expect(() => f()).toThrow(BadPayload)` (a class, not a string) then assert on
typed fields: `expect(err.cause).toBeInstanceOf(ZlibError)`. Async:
`await expect(p).rejects.toBeInstanceOf(BadPayload)`. `toThrow()` with no arg or a
class is good; `toThrow('text'|/re/)` pins the message and is what to avoid.

**2. Pin a literal; don't recompute.**
❌ `const expected = crypto.createHmac('sha1', k).update(v).digest('hex'); expect(sign(k,v)).toBe(expected)`
✅ `expect(sign(k, v)).toBe('57d5bb55...')` — or `.toMatchInlineSnapshot()`, which
is the idiomatic JS pinned vector (inline, reviewed once, committed in the test).

**3. Public API only.**
❌ `(svc as any)._helper()` · `svc['_private']` · deep import `../src/internal/x`
✅ Reach the branch through the exported surface. `as any` to poke internals is
the JS/TS tell here.

**4. Behavior, not readback.**
❌ `const s = new Signer({ salt }); expect(s.salt).toBe(salt)`
✅ `expect(new Signer({salt:'a'}).sign(v)).not.toBe(new Signer({salt:'b'}).sign(v))`

**5. No either-or message asserts.**
❌ `expect(/Malformed|does not match/.test(err.message)).toBe(true)` ·
`expect(['a','b']).toContain(err.message)`
✅ Arrange so only one branch is reachable, then assert that one.

**6. `it.each` / `test.each`, not copy-paste.**
✅
```ts
it.each([
  ['concat'], ['hmac'], ['none'],
])('round-trips %s', (mode) => {
  const s = makeSigner({ keyDerivation: mode })
  expect(s.unsign(s.sign('value'))).toBe('value')
})
```

**8. Verify assumptions in a REPL.** Before asserting library behavior, run it:
`node -e "console.log(require('node:buffer').Buffer.from('!@#','base64').toString())"`
(or `ts-node`/a scratch `*.test.ts` you delete). Don't assert from memory.

**9. Real-I/O over hand mocks.** Prefer `supertest`/`request(app)` (real HTTP
against your app), `@testing-library` (real render), `msw`/`nock` (intercept at
the network boundary), a real test DB, over `jest.fn()`/`jest.mock()`/
`vi.fn()`/`sinon.stub()`. Reach for hand mocks only for true external side
effects, nondeterminism, or paid APIs.

**10. Two mock numbers.** `mock_real` = `jest.fn/mock/spyOn`, `vi.fn/mock/spyOn`,
`sinon.stub/spy/mock`, `.mockReturnValue/.mockResolvedValue/.mockImplementation`
(drive to 0). `mock_framework` = `supertest`/`@testing-library`/`msw`/`nock`
(legitimate; context only).

---

## Kotlin equivalents (kotlin.test · JUnit5 · Kotest · MockK)

Same rules, different syntax. The mapping for the ones that look different:

**1. Error type, not message.**
❌ `assertTrue(ex.message!!.contains("zlib"))`
✅ kotlin.test `assertFailsWith<BadPayload> { s.loads(corrupt) }` then assert typed
fields on the returned exception; JUnit5 `assertThrows<BadPayload> { … }`; Kotest
`shouldThrow<BadPayload> { … }`. Assert the message text only if the message is a
documented part of the contract.

**2. Pin a literal; don't recompute.**
❌ `val expected = Mac.getInstance("HmacSHA1").also{…}.doFinal(v); assertEquals(expected, sign(k,v))`
✅ `assertEquals("57d5bb55…", sign(k, v))` — kotlin.test puts the **expected first**
(often a named `expected = …` arg). Use a triple-quoted `"""{"k":"v"}"""` for
JSON / multiline vectors (the kotlinx.serialization idiom).

**3. Public API only.**
❌ `obj.javaClass.getDeclaredField("secret").apply { isAccessible = true }`
✅ Reach the branch through the public / `internal` surface — the test source set
already sees `internal` for the same module. **Reflecting into privates** is the
Kotlin tell (the smell A.2 counts).

**4. Behavior, not readback.**
❌ `val s = Signer(salt = "x"); assertEquals("x", s.salt)`
✅ `assertNotEquals(Signer(salt="a").sign(v), Signer(salt="b").sign(v))`

**5. No either-or message asserts.**
❌ `assertTrue(e.message!!.contains("Malformed") || e.message!!.contains("does not match"))`
✅ Arrange so only one branch is reachable, then assert that one.

**6. Parametrize, don't unroll.**
✅ JUnit5 `@ParameterizedTest` + `@ValueSource`/`@MethodSource`/`@CsvSource`; Kotest
`withData(…) { }` (data-driven) or `checkAll { }` (property). Don't copy-paste
near-identical `@Test fun`s.

**8. Verify assumptions out-of-band.** `kotlin -e "…"`, a `jshell` snippet for JVM
stdlib, or a throwaway `@Test` you delete. Don't assert library behavior from memory.

**9. Real-I/O over hand mocks.** Prefer ktor `testApplication { }`, OkHttp
`MockWebServer`, kotlinx-coroutines-test `runTest { }`, JUnit `@TempDir` /
`TemporaryFolder` over `mockk()` / `Mockito.mock()`. Hand mocks only for true
external boundaries.

**10. Two mock numbers.** `mock_real` = `mockk`/`spyk`/`every {`/`coEvery {`/
`Mockito.mock`/`whenever(`/`@Mock` (drive to 0). `mock_framework` = `MockWebServer`/
`MockEngine`/`testApplication`/`runTest`/`TestDispatcher`/`@TempDir` (legitimate;
context only — e.g. `runTest` is how you test a `suspend` fun at all).

---

## Swift equivalents (XCTest · Swift Testing · Quick/Nimble)

**1. Error type, not message.**
❌ `XCTAssertTrue(error.localizedDescription.contains("zlib"))`
✅ XCTest `XCTAssertThrowsError(try f()) { XCTAssertTrue($0 is BadPayload) }`; Swift
Testing `#expect(throws: BadPayload.self) { try f() }`. `XCTAssertThrowsError` /
`#expect(throws:)` with no message-string is the good form; pinning the message text
is the smell.

**2. Pin a literal; don't recompute.**
❌ `let expected = HMAC<SHA256>.authenticationCode(for: v, using: k); XCTAssertEqual(sign(k,v), Data(expected))`
✅ `XCTAssertEqual(sign(k, v), "57d5bb55…")` — XCTest puts the **actual first** and
the literal **last**; Swift Testing `#expect(out == "57d5bb55…")`.

**3. Public API & `@testable`.** `@testable import` of `internal` is the sanctioned
way to test in Swift, and `private` is unreachable — so there's **no private-poke
tell**, and A.2 is `n/a` (as same-package access is in Go). The judgment call is
whether a test exercises observable behavior or an internal you exposed only for it.

**4. Behavior, not readback.**
❌ `let s = Signer(salt: "x"); XCTAssertEqual(s.salt, "x")`
✅ `XCTAssertNotEqual(Signer(salt:"a").sign(v), Signer(salt:"b").sign(v))`

**5. No either-or message asserts.**
❌ `XCTAssertTrue(msg.contains("Malformed") || msg.contains("does not match"))`
✅ Arrange so only one branch is reachable, then assert that one.

**6. Parametrize, don't unroll.**
✅ Swift Testing `@Test(arguments: […])`. XCTest has no native parametrization — a
`for` loop over a `[case]` array with a per-iteration failure message is the XCTest
equivalent (it reads as low D.2, which is accurate: a parametrized rewrite wins it).

**8. Verify assumptions out-of-band.** `swift -e "…"` or a scratch test you delete.
Don't assert library behavior from memory.

**9. Real-I/O over hand mocks.** Swift has no dominant runtime mocker — prefer real
objects, `URLProtocol` stubs at the network boundary, `FileManager` temp dirs, and
`XCTestExpectation` / `confirmation` for async, over hand-written `Mock*` / `Stub*`
doubles.

**10. Two mock numbers.** `mock_real` = hand `Mock*`/`Stub*`/`Fake*`/`Spy*` doubles,
Cuckoo (drive to 0). `mock_framework` = `XCTestExpectation`/`wait(for:)`/
`URLProtocol`/`confirmation` (legitimate; context only).

> The JS/TS, Go, Kotlin, and Swift axis counts from `score.py` are **heuristic**
> (regex approximations), unlike the empirically-validated Python set. Use them to
> spot trends and the worst offenders, but confirm by reading the tests.
