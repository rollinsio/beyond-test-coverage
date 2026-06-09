/*
 * Generated matrix suite — decoding direction (Json.decodeFromString) and round-trips.
 * Decode expectations are fixed model values; the input JSON is a pinned literal.
 */
package kotlinx.serialization.genjson

import kotlinx.serialization.decodeFromString
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import kotlin.test.assertEquals
import org.junit.jupiter.api.Test
import org.junit.jupiter.params.ParameterizedTest
import org.junit.jupiter.params.provider.Arguments
import org.junit.jupiter.params.provider.MethodSource

class JsonDecodeTest {

    companion object {
        /** Contract: a well-formed object literal decodes to the corresponding model value. */
        @JvmStatic
        fun itemDecodings(): List<Arguments> = listOf(
            Arguments.of(Item(7, "the-item-name"), """{"id":7,"name":"the-item-name"}"""),
            Arguments.of(Item(0, ""), """{"id":0,"name":""}"""),
            // Contract: object members may be reordered relative to declaration order.
            Arguments.of(Item(5, "reordered"), """{"name":"reordered","id":5}"""),
            // Contract: insignificant whitespace between tokens is ignored.
            Arguments.of(Item(3, "spaced"), """{ "id" : 3 , "name" : "spaced" }"""),
        )

        /** Contract: encodeToString then decodeFromString is identity for representable values. */
        @JvmStatic
        fun roundTripValues(): List<Item> = listOf(
            Item(7, "the-item-name"),
            Item(0, ""),
            Item(Int.MIN_VALUE, "min"),
            Item(Int.MAX_VALUE, "max"),
            Item(1, "a\"quote\"and\\slash\nnewline"),
        )
    }

    @ParameterizedTest(name = "decode {1}")
    @MethodSource("itemDecodings")
    fun decodesObjectLiteralToModel(expected: Item, input: String) =
        assertEquals(expected, Json.decodeFromString<Item>(input))

    @ParameterizedTest(name = "round-trip {0}")
    @MethodSource("roundTripValues")
    fun encodeThenDecodeIsIdentity(value: Item) =
        assertEquals(value, Json.decodeFromString<Item>(Json.encodeToString(value)))

    /** Contract: a nested object literal decodes the nested model and its list. */
    @Test
    fun decodesNestedObject() =
        assertEquals(
            Nested(Item(1, "a"), listOf("x", "y")),
            Json.decodeFromString<Nested>("""{"item":{"id":1,"name":"a"},"tags":["x","y"]}"""),
        )

    /** Contract: an enum serial-name string decodes back to the enum constant. */
    @Test
    fun decodesEnumByName() =
        assertEquals(Holder(Color.GREEN), Json.decodeFromString<Holder>("""{"c":"GREEN"}"""))

    /** Contract: an empty JSON array decodes to an empty list. */
    @Test
    fun decodesEmptyArrayToEmptyList() =
        assertEquals(emptyList(), Json.decodeFromString<List<Int>>("[]"))

    /** Contract: a JSON object decodes to a Map preserving keys and values. */
    @Test
    fun decodesObjectToMap() =
        assertEquals(mapOf("a" to 1, "b" to 2), Json.decodeFromString<Map<String, Int>>("""{"a":1,"b":2}"""))
}
