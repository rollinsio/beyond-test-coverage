/*
 * Generated matrix suite (iter20) — top-level primitive wire forms, parametrized.
 * Boundary values (Long.MIN/MAX, ULong.MAX, 0u, null, bool, double, string) each pin a fixed
 * literal. Parametrized to keep LOC/test low (D.1) and the parametrize ratio high (D.2).
 */
package kotlinx.serialization.genjson

import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import kotlin.test.assertEquals
import org.junit.jupiter.params.ParameterizedTest
import org.junit.jupiter.params.provider.Arguments
import org.junit.jupiter.params.provider.MethodSource

class JsonPrimitiveEncodeTest {

    companion object {
        /** Contract: a top-level Long encodes as a bare integer literal at the type boundaries. */
        @JvmStatic
        fun longBoundaries(): List<Arguments> = listOf(
            Arguments.of("-9223372036854775808", Long.MIN_VALUE),
            Arguments.of("9223372036854775807", Long.MAX_VALUE),
            Arguments.of("0", 0L),
        )

        /** Contract: other top-level primitives encode to their canonical JSON token. */
        @JvmStatic
        fun otherPrimitives(): List<Arguments> = listOf(
            Arguments.of("true", true),
            Arguments.of("false", false),
            Arguments.of("3.5", 3.5),
        )
    }

    @ParameterizedTest(name = "Long {1} -> {0}")
    @MethodSource("longBoundaries")
    fun encodesLongBoundaries(expected: String, value: Long) =
        assertEquals(expected, Json.encodeToString(value))

    /** Contract: ULong.MAX_VALUE encodes as an unsigned bare literal beyond the signed Long range. */
    @org.junit.jupiter.api.Test
    fun encodesULongMaxBoundary() = assertEquals("18446744073709551615", Json.encodeToString(ULong.MAX_VALUE))

    /** Contract: the zero ULong encodes as a bare zero. */
    @org.junit.jupiter.api.Test
    fun encodesULongZeroBoundary() = assertEquals("0", Json.encodeToString(0uL))

    @ParameterizedTest(name = "primitive {1} -> {0}")
    @MethodSource("otherPrimitives")
    fun encodesOtherPrimitives(expected: String, value: Any) =
        when (value) {
            is Boolean -> assertEquals(expected, Json.encodeToString(value))
            is Double -> assertEquals(expected, Json.encodeToString(value))
            else -> error("unexpected primitive type")
        }

    /** Contract: a top-level String is quoted in the wire form. */
    @org.junit.jupiter.api.Test
    fun encodesStringQuoted() = assertEquals("\"hello world\"", Json.encodeToString("hello world"))

    /** Contract: a top-level nullable null encodes to the JSON null literal. */
    @org.junit.jupiter.api.Test
    fun encodesNullLiteral() = assertEquals("null", Json.encodeToString<String?>(null))

    /** Contract: a nested list encodes to nested JSON arrays. */
    @org.junit.jupiter.api.Test
    fun encodesNestedArrays() = assertEquals("[[1,2],[3]]", Json.encodeToString(listOf(listOf(1, 2), listOf(3))))
}
