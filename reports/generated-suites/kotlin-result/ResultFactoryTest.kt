package com.github.michaelbull.result

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

/**
 * The factory surface that lifts ordinary code into a [Result]: [runCatching]
 * (plain and receiver form) and [toResultOr]. Thrown exceptions are asserted by
 * TYPE, never by message text.
 */
class ResultFactoryTest {

    @Test
    fun runCatchingWrapsSuccessfulBlockInOk() {
        assertEquals("the-computed-value", runCatching { "the-computed-value" }.get())
    }

    @Test
    fun runCatchingCapturesThrownExceptionAsErr() {
        val result = runCatching { throw IllegalStateException("explode") }
        assertTrue(result.getError() is IllegalStateException)
    }

    @Test
    fun receiverRunCatchingWrapsSuccessInOk() {
        assertEquals("HELLO-RECEIVER", "hello-receiver".runCatching { uppercase() }.get())
    }

    @Test
    fun receiverRunCatchingCapturesThrowAsErr() {
        val result = "input".runCatching { throw IllegalArgumentException(this) }
        assertTrue(result.getError() is IllegalArgumentException)
    }

    @Test
    fun toResultOrWrapsNonNullInOk() {
        val value: String? = "the-present-value"
        assertEquals("the-present-value", value.toResultOr { "missing" }.get())
    }

    @Test
    fun toResultOrUsesErrorForNull() {
        val value: String? = null
        assertEquals("the-missing-error", value.toResultOr { "the-missing-error" }.getError())
    }
}
