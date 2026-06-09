/*
 * Generated matrix suite — canonical fixed-vector assertions (round 2 focus: B.1).
 * Each assertion pins a JSON literal directly in the assertEquals call (expected first,
 * kotlin.test convention). Literals are computed once out-of-band (.rex_metrics/verifications.log)
 * and never recomputed by the unit under test. These complement the parametrized tables by
 * pinning the exact wire form of the most important contracts as inline reviewed vectors.
 */
package kotlinx.serialization.genjson

import kotlinx.serialization.decodeFromString
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlin.test.assertEquals
import org.junit.jupiter.api.Test

class JsonVectorTest {

    /** Contract: the canonical object encodes to this exact wire form under default config. */
    @Test
    fun canonicalObjectEncodesToFixedLiteral() =
        assertEquals("""{"id":7,"name":"the-item-name"}""", Json.encodeToString(Item(7, "the-item-name")))

    /** Contract: the canonical wire form decodes back to the canonical model value. */
    @Test
    fun canonicalLiteralDecodesToModel() =
        assertEquals(Item(7, "the-item-name"), Json.decodeFromString<Item>("""{"id":7,"name":"the-item-name"}"""))

    /** Contract: encodeDefaults=true emits the defaulted property in the wire form. */
    @Test
    fun encodeDefaultsOnFixedLiteral() =
        assertEquals(
            """{"name":"p","language":"kotlin"}""",
            Json { encodeDefaults = true }.encodeToString(WithDefault("p")),
        )

    /** Contract: explicitNulls=true (default) emits an explicit null for the wire form. */
    @Test
    fun explicitNullFixedLiteral() =
        assertEquals("""{"name":"u","description":null}""", Json.encodeToString(Nullable("u", null)))

    /** Contract: a nested object + list encodes to this exact wire form. */
    @Test
    fun nestedObjectEncodesToFixedLiteral() =
        assertEquals(
            """{"item":{"id":1,"name":"a"},"tags":["x","y"]}""",
            Json.encodeToString(Nested(Item(1, "a"), listOf("x", "y"))),
        )

    /** Contract: special float values, when allowed, encode as these exact bare literals. */
    @Test
    fun specialFloatsFixedLiteral() =
        assertEquals(
            "[1.0,NaN,-Infinity]",
            Json { allowSpecialFloatingPointValues = true }.encodeToString(listOf(1.0, Double.NaN, Double.NEGATIVE_INFINITY)),
        )

    /** Contract: a non-ASCII character is emitted literally in the wire form. */
    @Test
    fun nonAsciiFixedLiteral() =
        assertEquals("""{"id":1,"name":"café"}""", Json.encodeToString(Item(1, "café")))

    /** Contract: a built JsonObject stringifies to this exact wire form. */
    @Test
    fun builtObjectStringifiesToFixedLiteral() =
        assertEquals(
            """{"id":7,"name":"the-item-name"}""",
            buildJsonObject { put("id", JsonPrimitive(7)); put("name", JsonPrimitive("the-item-name")) }.toString(),
        )

    /** Contract: a built JsonArray stringifies to this exact wire form. */
    @Test
    fun builtArrayStringifiesToFixedLiteral() =
        assertEquals(
            "[100,200,300]",
            buildJsonArray { add(JsonPrimitive(100)); add(JsonPrimitive(200)); add(JsonPrimitive(300)) }.toString(),
        )

    /** Contract: parseToJsonElement then toString preserves this exact wire form. */
    @Test
    fun parseToElementRoundTripsFixedLiteral() =
        assertEquals("""{"a":1,"b":[2,3]}""", Json.parseToJsonElement("""{"a":1,"b":[2,3]}""").toString())
}
