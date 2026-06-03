/*
 * Generated matrix suite — the JsonElement tree (JsonObject / JsonArray / JsonPrimitive)
 * and the parseToJsonElement / toString round-trip. Public builders only.
 */
package kotlinx.serialization.genjson

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.int
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue
import org.junit.jupiter.api.Test

class JsonElementTest {

    /** Contract: JsonObject.toString renders a valid JSON object with quoted keys. */
    @Test
    fun jsonObjectToStringRendersJson() {
        val obj = buildJsonObject {
            put("id", JsonPrimitive(7))
            put("name", JsonPrimitive("the-item-name"))
        }
        assertEquals("""{"id":7,"name":"the-item-name"}""", obj.toString())
    }

    /** Contract: JsonArray.toString renders a bracketed, comma-separated array. */
    @Test
    fun jsonArrayToStringRendersJson() {
        val arr = buildJsonArray {
            add(JsonPrimitive(1)); add(JsonPrimitive(2)); add(JsonPrimitive(3))
        }
        assertEquals("[1,2,3]", arr.toString())
    }

    /** Contract: a string primitive is quoted; a number primitive is bare (isString distinguishes them). */
    @Test
    fun stringPrimitiveIsQuotedNumberIsBare() {
        assertEquals("\"42\"", JsonPrimitive("42").toString())
        assertEquals("42", JsonPrimitive(42).toString())
        assertTrue(JsonPrimitive("42").isString)
        assertTrue(!JsonPrimitive(42).isString)
    }

    /** Contract: parseToJsonElement parses arbitrary JSON into a tree that re-stringifies identically. */
    @Test
    fun parseToJsonElementRoundTrips() {
        val text = """{"a":1,"b":[2,3]}"""
        assertEquals(text, Json.parseToJsonElement(text).toString())
    }

    /** Contract: the jsonObject accessor narrows a parsed element and exposes member values. */
    @Test
    fun parsedTreeExposesTypedMembers() {
        val tree = Json.parseToJsonElement("""{"id":7,"tags":["x","y"]}""")
        assertEquals(7, tree.jsonObject.getValue("id").jsonPrimitive.int)
        assertEquals("x", tree.jsonObject.getValue("tags").jsonArray[0].jsonPrimitive.content)
    }

    /** Contract: JsonNull is the JSON null literal and its content is the string "null". */
    @Test
    fun jsonNullRendersNull() {
        assertEquals("null", JsonNull.toString())
        assertEquals("null", JsonNull.content)
    }

    /** Contract: a JsonObject equals an equivalent Map of elements (Map delegation). */
    @Test
    fun jsonObjectEqualsEquivalentMap() {
        val expected: Map<String, JsonElement> = mapOf("a" to JsonPrimitive(1))
        val obj: Map<String, JsonElement> = buildJsonObject { put("a", JsonPrimitive(1)) }
        assertEquals(expected, obj)
    }

    /** Contract: narrowing a primitive to jsonObject throws IllegalArgumentException (wrong shape). */
    @Test
    fun jsonObjectAccessorRejectsPrimitive() {
        assertFailsWith<IllegalArgumentException> { (JsonPrimitive(1) as JsonElement).jsonObject }
    }

    /** Contract: the int accessor on a non-numeric primitive throws NumberFormatException. */
    @Test
    fun intAccessorRejectsNonNumeric() {
        assertFailsWith<NumberFormatException> { JsonPrimitive("abc").int }
    }
}
