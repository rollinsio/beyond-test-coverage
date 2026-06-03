/*
 * Generated matrix suite — encoding direction (Json.encodeToString, default config).
 * Each expected JSON is a fixed literal pinned from an out-of-band run; never recomputed.
 */
package kotlinx.serialization.genjson

import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import kotlin.test.assertEquals
import org.junit.jupiter.api.Test
import org.junit.jupiter.params.ParameterizedTest
import org.junit.jupiter.params.provider.Arguments
import org.junit.jupiter.params.provider.MethodSource

class JsonEncodeTest {

    companion object {
        /** Contract: a class encodes its declared fields in declaration order under default config. */
        @JvmStatic
        fun itemEncodings(): List<Arguments> = listOf(
            Arguments.of("""{"id":7,"name":"the-item-name"}""", Item(7, "the-item-name")),
            Arguments.of("""{"id":0,"name":""}""", Item(0, "")),
            Arguments.of("""{"id":-2147483648,"name":"min"}""", Item(Int.MIN_VALUE, "min")),
            Arguments.of("""{"id":2147483647,"name":"max"}""", Item(Int.MAX_VALUE, "max")),
        )

        /** Contract: nested classes and lists nest as JSON objects / arrays; empty list -> []. */
        @JvmStatic
        fun nestedEncodings(): List<Arguments> = listOf(
            Arguments.of("""{"item":{"id":1,"name":"a"},"tags":["x","y"]}""", Nested(Item(1, "a"), listOf("x", "y"))),
            Arguments.of("""{"item":{"id":9,"name":"deep"},"tags":["only"]}""", Nested(Item(9, "deep"), listOf("only"))),
            Arguments.of("""{"item":{"id":1,"name":"a"},"tags":[]}""", Nested(Item(1, "a"), emptyList())),
        )

        /** Contract: an enum field is encoded as its serial-name string. */
        @JvmStatic
        fun enumEncodings(): List<Arguments> = listOf(
            Arguments.of("""{"c":"RED"}""", Holder(Color.RED)),
            Arguments.of("""{"c":"GREEN"}""", Holder(Color.GREEN)),
        )

        /** Contract: JSON-special characters inside a string field are backslash-escaped. */
        @JvmStatic
        fun escapingCases(): List<Arguments> = listOf(
            Arguments.of("""{"id":1,"name":"a\"b"}""", "a\"b"),
            Arguments.of("""{"id":1,"name":"line1\nline2"}""", "line1\nline2"),
            Arguments.of("""{"id":1,"name":"tab\there"}""", "tab\there"),
            Arguments.of("""{"id":1,"name":"back\\slash"}""", "back\\slash"),
        )
    }

    @ParameterizedTest(name = "encode item -> {0}")
    @MethodSource("itemEncodings")
    fun encodesItemToExpectedJsonLiteral(expected: String, value: Item) =
        assertEquals(expected, Json.encodeToString(value))

    @ParameterizedTest(name = "encode nested -> {0}")
    @MethodSource("nestedEncodings")
    fun encodesNestedToExpectedJsonLiteral(expected: String, value: Nested) =
        assertEquals(expected, Json.encodeToString(value))

    @ParameterizedTest(name = "encode enum -> {0}")
    @MethodSource("enumEncodings")
    fun encodesEnumToExpectedJsonLiteral(expected: String, value: Holder) =
        assertEquals(expected, Json.encodeToString(value))

    @ParameterizedTest(name = "escape {1} -> {0}")
    @MethodSource("escapingCases")
    fun escapesSpecialCharactersInStrings(expected: String, raw: String) =
        assertEquals(expected, Json.encodeToString(Item(1, raw)))

    /** Contract: an empty Kotlin list serializes to the JSON empty array literal. */
    @Test
    fun encodesEmptyListToEmptyJsonArray() =
        assertEquals("[]", Json.encodeToString(emptyList<Int>()))

    /** Contract: a Map<String,Int> serializes to a JSON object keyed by the map keys. */
    @Test
    fun encodesMapToJsonObject() =
        assertEquals("""{"a":1,"b":2}""", Json.encodeToString(mapOf("a" to 1, "b" to 2)))

    /** Contract: a list of primitives serializes to a JSON array of bare values. */
    @Test
    fun encodesIntListToJsonArray() =
        assertEquals("[10,20,30]", Json.encodeToString(listOf(10, 20, 30)))

    /** Contract: a non-ASCII character is emitted literally (not \\u-escaped) by default. */
    @Test
    fun encodesNonAsciiLiterally() =
        assertEquals("""{"id":1,"name":"café"}""", Json.encodeToString(Item(1, "café")))
}
