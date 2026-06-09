/*
 * Generated matrix suite (iter20) — structural boundaries and default-on-decode.
 * Empty / single / nested JsonElement shapes and the decode-time default-value contract.
 * Fixed literals pinned directly (B.1); each protects a distinct, mutation-sensitive behaviour.
 */
package kotlinx.serialization.genjson

import kotlinx.serialization.decodeFromString
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.putJsonObject
import kotlin.test.assertEquals
import org.junit.jupiter.api.Test

class JsonBoundaryTest {

    /** Contract: an empty JsonObject stringifies to the empty-object literal. */
    @Test
    fun emptyJsonObjectStringifiesToBraces() =
        assertEquals("{}", buildJsonObject {}.toString())

    /** Contract: an empty JsonArray stringifies to the empty-array literal. */
    @Test
    fun emptyJsonArrayStringifiesToBrackets() =
        assertEquals("[]", buildJsonArray {}.toString())

    /** Contract: a nested JsonObject stringifies to a nested object literal. */
    @Test
    fun nestedJsonObjectStringifies() =
        assertEquals(
            """{"inner":{"x":1}}""",
            buildJsonObject { putJsonObject("inner") { put("x", JsonPrimitive(1)) } }.toString(),
        )

    /** Contract: parseToJsonElement on a top-level array re-stringifies to the array literal. */
    @Test
    fun parseTopLevelArrayRoundTrips() =
        assertEquals("[1,2,3]", Json.parseToJsonElement("[1,2,3]").toString())

    /** Contract: a missing optional field is filled with its declared default on decode. */
    @Test
    fun missingOptionalFieldUsesDefault() =
        assertEquals(Opt(1, 99), Json.decodeFromString<Opt>("""{"a":1}"""))

    /** Contract: a present value for an optional field overrides its default on decode. */
    @Test
    fun presentOptionalFieldOverridesDefault() =
        assertEquals(Opt(1, 5), Json.decodeFromString<Opt>("""{"a":1,"b":5}"""))

    /** Contract: ignoreUnknownKeys=true drops every unmodelled key, keeping defaults. */
    @Test
    fun ignoreUnknownKeysDropsMultipleUnknowns() =
        assertEquals(
            Opt(1, 99),
            Json { ignoreUnknownKeys = true }.decodeFromString<Opt>("""{"a":1,"x":2,"y":3}"""),
        )

    /** Contract: allowTrailingComma=true accepts a trailing comma in an array. */
    @Test
    fun allowTrailingCommaAcceptsArrayTrailingComma() =
        assertEquals(listOf(1, 2, 3), Json { allowTrailingComma = true }.decodeFromString<List<Int>>("[1,2,3,]"))

    /** Contract: allowComments=true skips a line comment to end of line. */
    @Test
    fun allowCommentsSkipsLineComment() =
        assertEquals(Opt(1, 99), Json { allowComments = true }.decodeFromString<Opt>("{\"a\":1 // c\n}"))
}
