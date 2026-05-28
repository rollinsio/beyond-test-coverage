## Quality contract — read this before writing any tests

Run 1 produced suites that hit high coverage but were measurably more
fragile than the human-written baselines. The rules below come
directly from the patterns found in Run 1. Each has a negative form
("don't do X") and a positive form ("do Y instead").

### 1. Don't assert on error-message wording. Assert on type + payload.

❌ **Wrong** (pins prose, breaks on any reword):
```python
with pytest.raises(BadPayload, match="zlib"):
    s.loads(corrupt_value)
```

✅ **Right** (asserts the contract):
```python
with pytest.raises(BadPayload) as exc_info:
    s.loads(corrupt_value)
assert isinstance(exc_info.value.original_error, zlib.error)
```

If the only thing you can assert is the exception *type* (no useful
payload attributes), that's still better than pinning the message.
Test the message *only* when the message itself is documented as part
of the contract (rare).

### 2. Don't re-implement crypto/encoding inside the test. Pin a fixed expected value.

❌ **Wrong** (parallel-mutation blind):
```python
def test_signature():
    expected = hmac.new(b"key", msg=b"value", digestmod=hashlib.sha1).digest()
    assert HMACAlgorithm(hashlib.sha1).get_signature(b"key", b"value") == expected
```
If `get_signature` has a bug that also exists in your hand-computed
`expected` (because you wrote them with the same misunderstanding),
both sides break symmetrically and the test passes.

✅ **Right** (pin a known-good byte literal):
```python
def test_signature_pins_fixed_vector():
    # Computed once with a verified-correct implementation, hard-coded here.
    assert HMACAlgorithm(hashlib.sha1).get_signature(b"key", b"value") == (
        b"\x57\xd5\xbb\x55..."
    )
```

This is what the baseline does at `tests/test_serializer.py:186` with
`assert signed == "[42].-9cNi0CxsSB3hZPNCe9a2eEs1ZM"`. Run 1 audits
flagged this absence as the single largest mutation-survivor risk in
the generated suites.

### 3. Don't import private symbols. Test through the public API.

❌ **Wrong**:
```python
from itsdangerous.signer import _lazy_sha1, _make_keys_list
# ... tests of _make_keys_list directly ...

s._loads_unsafe_impl(signed, salt=None, load_payload_kwargs={...})
```

If you need to flip a private branch, find the public API call that
reaches it. If no public call reaches it, **that branch may not be
worth testing** (and may not even be a real contract).

In Run 1, multiple iter_2 sessions called `_loads_unsafe_impl`
directly with `load_payload_kwargs={"serializer": json}` — but
`serializer=json` is the default, so the kwarg had no observable
effect. The test would have passed even if the entire kwargs argument
were silently dropped. Don't write tests like that.

### 4. Don't write tautological constructor readbacks.

❌ **Wrong**:
```python
def test_signer_stores_salt():
    s = Signer("k", salt="custom")
    assert s.salt == "custom"  # we literally just passed this in
```

✅ **Right** — test that the value *affects behavior*:
```python
def test_salt_affects_signature():
    sig_a = Signer("k", salt="a").sign("value")
    sig_b = Signer("k", salt="b").sign("value")
    assert sig_a != sig_b
```

The Run 1 suites had whole files (`test_exc.py`) that were
exclusively this pattern.

### 5. Don't use `or`-joined assertions that accept either outcome.

❌ **Wrong**:
```python
assert "Malformed timestamp" in str(exc) or "does not match" in str(exc)
```
This passes whichever message the implementation produces — and a bug
that *swapped* the two messages would not be caught.

✅ **Right** — set up the test conditions so only ONE branch is
reachable, then assert that one:
```python
# Tamper signature only — timestamp is still valid bytes.
tampered = signed[:-2] + b"XX"
with pytest.raises(BadTimeSignature) as exc:
    s.unsign(tampered)
assert "does not match" in str(exc.value)  # specifically this branch
```

### 6. Use `@pytest.mark.parametrize` and fixtures. Don't unroll cases.

The Run 1 suites averaged **2.3–2.5× the LOC of the baseline** because
they unrolled parametrize and re-created `Signer("k")` in every test.

❌ **Wrong** (3 tests, 11 LOC, easy to forget a case):
```python
def test_concat_roundtrip(self):
    s = Signer("k", key_derivation="concat")
    assert s.unsign(s.sign("x")) == b"x"
def test_hmac_roundtrip(self):
    s = Signer("k", key_derivation="hmac")
    assert s.unsign(s.sign("x")) == b"x"
def test_none_roundtrip(self):
    s = Signer("k", key_derivation="none")
    assert s.unsign(s.sign("x")) == b"x"
```

✅ **Right** (one test, 6 LOC, 4 cases — and it's what the baseline does):
```python
@pytest.mark.parametrize("key_derivation", ("concat", "django-concat", "hmac", "none"))
def test_key_derivation(self, signer_factory, key_derivation):
    signer = signer_factory(key_derivation=key_derivation)
    assert signer.unsign(signer.sign("value")) == b"value"
```

Use class inheritance to apply the same tests to multiple classes too
(the baseline does this via
`class TestTimedSerializer(FreezeMixin, TestSerializer): ...` — every
serializer test runs against `TimedSerializer` for free).

### 7. Test boundary cases for every comparison in the source.

Run 1 audits independently predicted three mutations that survive 100
% coverage in itsdangerous:

- `timed.py:139` — `age > max_age` → `>=` survives (no boundary test
  at `age == max_age`)
- `url_safe.py:60` — `len(compressed) < (len(json) - 1)` → `<=`
  survives
- `signer.py:236` — `reversed(self.secret_keys)` → plain iteration
  survives (no test pins newest-first ordering)

**For every `<`, `<=`, `>`, `>=`, `==`, `!=` comparison in the source,
write at least one test that exercises the boundary case.** This is a
mutation-aware target — it forces tests that distinguish strict from
non-strict comparisons, which is exactly what survives standard
coverage.

For ordering-dependent code (`reversed(...)`, sort, etc.), add a test
where the order is *observable* (e.g., construct inputs such that
plain iteration would pick a different result than reversed
iteration).

### 8. Verify your assumptions before testing stdlib/library behavior.

If you're about to write a test that asserts "`base64.urlsafe_b64decode("!@#$%^")` raises `binascii.Error`," **run that line in a Python REPL first.** In Run 1, two `itsdangerous/oneshot` tests committed broken because the model assumed urlsafe-b64decode rejects non-alphabet characters. It doesn't — it silently filters them and returns `b""`.

When in doubt, do:
```bash
python -c "import base64; print(repr(base64.urlsafe_b64decode(b'!@#$%^==')))"
```

Then write the test to assert what actually happens. It's much cheaper
than committing a wrong test.

### 9. Use the framework's real-I/O fixtures over `unittest.mock`.

If `pytest-httpbin`, `httpx.MockTransport`, `httpx.WSGITransport`,
`httpx.ASGITransport`, or similar real-execution primitives are
available, **use them**. They exercise actual code paths and catch
real regressions.

The Run 1 standout (`requests/wt-iter20`, the only result that's
better than baseline on every dimension) added a dedicated
`test_integration.py` using `pytest-httpbin`. That single
architectural decision pushed coverage past baseline by +3.85 pp line
/ +6.22 pp branch with **zero** lines of `unittest.mock`. Look for
that opportunity in your repo.

### 10. The two `mock-LOC` numbers your SUMMARY reports

To make the mock metric meaningful across runs, report **two**
mock-LOC numbers separately:

- `mock_real_loc` — lines matching `\b(MagicMock|Mock\(|patch\(|mocker\b|unittest\.mock)\b` (real mocking)
- `mock_framework_loc` — lines matching `\b(MockTransport|WSGITransport|ASGITransport|monkeypatch|httpbin)\b` (framework primitives)

The first is what we care about driving toward zero. The second is
just the cost of using the framework correctly.
