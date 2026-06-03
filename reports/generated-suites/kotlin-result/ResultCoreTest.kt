package com.github.michaelbull.result

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertNotEquals
import kotlin.test.assertNull
import kotlin.test.assertTrue
import kotlin.test.fail

/**
 * Construction, the isOk/isErr partition, the nullable/default accessors, the
 * throwing accessors, structural equality, toString, and destructuring —
 * the user-observable contract of [Result] itself.
 */
class ResultCoreTest {

    // ── isOk / isErr partition every Result ──────────────────────────────────
    @Test
    fun okIsOkAndNotErr() {
        assertTrue(Ok(42).isOk)
        assertFalse(Ok(42).isErr)
    }

    @Test
    fun errIsErrAndNotOk() {
        assertTrue(Err("boom").isErr)
        assertFalse(Err("boom").isOk)
    }

    // ── get / getError: safe nullable extraction ─────────────────────────────
    @Test
    fun getReturnsValueForOkElseNull() {
        assertEquals("the-cached-value", Ok("the-cached-value").get())
        assertNull(Err("boom").get())
    }

    @Test
    fun getErrorReturnsErrorForErrElseNull() {
        assertEquals("the-error-detail", Err("the-error-detail").getError())
        assertNull(Ok("the-cached-value").getError())
    }

    // ── getOr / getErrorOr: eager default on the other branch ────────────────
    @Test
    fun getOrReturnsValueForOkElseDefault() {
        assertEquals("the-real-value-x", Ok("the-real-value-x").getOr("the-fallback-default"))
        assertEquals("the-fallback-default", Err("boom").getOr("the-fallback-default"))
    }

    @Test
    fun getErrorOrReturnsErrorForErrElseDefault() {
        assertEquals("the-real-error-x", Err("the-real-error-x").getErrorOr("the-fallback-default"))
        assertEquals("the-fallback-default", Ok("value").getErrorOr("the-fallback-default"))
    }

    // ── getOrElse / getErrorOrElse: transform runs on exactly one branch ─────
    @Test
    fun getOrElseUsesValueForOkWithoutCallingTransform() {
        assertEquals("the-ok-value-here", Ok("the-ok-value-here").getOrElse { fail("transform ran on Ok") })
    }

    @Test
    fun getOrElseTransformsErrorForErr() {
        assertEquals("recovered-from-13", Err("error message").getOrElse { "recovered-from-${it.length}" })
    }

    @Test
    fun getErrorOrElseUsesErrorForErrWithoutCallingTransform() {
        assertEquals("the-err-value-xx", Err("the-err-value-xx").getErrorOrElse { fail("transform ran on Err") })
    }

    @Test
    fun getErrorOrElseTransformsValueForOk() {
        assertEquals("derived-from-okay", Ok("okay").getErrorOrElse { "derived-from-${it}" })
    }

    // ── getOrThrow: rethrows the contained throwable on Err ───────────────────
    @Test
    fun getOrThrowReturnsValueForOk() {
        assertEquals("the-unwrapped-value", Ok("the-unwrapped-value").getOrThrow())
    }

    @Test
    fun getOrThrowRethrowsContainedThrowableForErr() {
        assertFailsWith<IllegalStateException> {
            Err(IllegalStateException("explode")).getOrThrow()
        }
    }

    @Test
    fun getOrThrowTransformThrowsTransformedThrowableForErr() {
        assertFailsWith<IllegalArgumentException> {
            Err("bad input").getOrThrow { IllegalArgumentException(it) }
        }
    }

    // ── merge: collapse to the common supertype ──────────────────────────────
    @Test
    fun mergeReturnsValueForOk() {
        val result: Result<String, String> = Ok("the-merged-value")
        assertEquals("the-merged-value", result.merge())
    }

    @Test
    fun mergeReturnsErrorForErr() {
        val result: Result<String, String> = Err("the-merged-error")
        assertEquals("the-merged-error", result.merge())
    }

    // ── unwrap / unwrapError: throwing accessors assert by TYPE ──────────────
    @Test
    fun unwrapReturnsValueForOk() {
        assertEquals("the-unwrapped-value", Ok("the-unwrapped-value").unwrap())
    }

    @Test
    fun unwrapThrowsUnwrapExceptionForErr() {
        assertFailsWith<UnwrapException> { Err("boom").unwrap() }
    }

    @Test
    fun unwrapErrorReturnsErrorForErr() {
        assertEquals("the-unwrapped-error", Err("the-unwrapped-error").unwrapError())
    }

    @Test
    fun unwrapErrorThrowsUnwrapExceptionForOk() {
        assertFailsWith<UnwrapException> { Ok("value").unwrapError() }
    }

    @Test
    fun expectThrowsUnwrapExceptionForErr() {
        assertFailsWith<UnwrapException> { Err("boom").expect { "expected a value" } }
    }

    @Test
    fun expectReturnsValueForOk() {
        assertEquals("the-expected-value", Ok("the-expected-value").expect { "unused" })
    }

    @Test
    fun expectErrorThrowsUnwrapExceptionForOk() {
        assertFailsWith<UnwrapException> { Ok("value").expectError { "expected an error" } }
    }

    @Test
    fun expectErrorReturnsErrorForErr() {
        assertEquals("the-expected-error", Err("the-expected-error").expectError { "unused" })
    }

    // ── structural equality: by contained value / error ──────────────────────
    @Test
    fun okEqualsOkWithEqualValue() {
        assertEquals(Ok("same-value-here"), Ok("same-value-here"))
        assertNotEquals(Ok("same-value-here"), Ok("other-value-xx"))
    }

    @Test
    fun errEqualsErrWithEqualError() {
        assertEquals(Err("same-error-here"), Err("same-error-here"))
        assertNotEquals(Err("same-error-here"), Err("other-error-xx"))
    }

    @Test
    fun okNeverEqualsErrEvenWithEqualPayload() {
        assertNotEquals<Result<Int, Int>>(Ok(1), Err(1))
    }

    // ── toString: documented Ok(..)/Err(..) rendering ────────────────────────
    @Test
    fun toStringRendersOkWrapper() {
        assertEquals("Ok(the-value-here)", Ok("the-value-here").toString())
    }

    @Test
    fun toStringRendersErrWrapper() {
        assertEquals("Err(the-error-here)", Err("the-error-here").toString())
    }

    // ── destructuring: component1 = value-or-null, component2 = error-or-null ─
    @Test
    fun destructuringOkExposesValueAndNullError() {
        val (value, error) = Ok("destructured-value")
        assertEquals("destructured-value", value)
        assertNull(error)
    }

    @Test
    fun destructuringErrExposesNullValueAndError() {
        val (value, error) = Err("destructured-error")
        assertNull(value)
        assertEquals("destructured-error", error)
    }
}
