/*
 * Generated matrix suite — failure contract.
 * Every case asserts the exception TYPE (SerializationException, the stable public
 * supertype of the experimental JsonDecoding/JsonEncodingException) — never message text,
 * never an or-joined message check. Each negative case is paired, where a flag governs it,
 * with the positive case in JsonConfigTest so only one branch is reachable per assertion.
 */
package kotlinx.serialization.genjson

import kotlinx.serialization.SerializationException
import kotlinx.serialization.decodeFromString
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import kotlin.test.assertFailsWith
import org.junit.jupiter.params.ParameterizedTest
import org.junit.jupiter.params.provider.MethodSource
import org.junit.jupiter.api.Test

class JsonErrorTest {

    companion object {
        /** Contract: each of these malformed/mismatched inputs fails decoding to Item with SerializationException. */
        @JvmStatic
        fun invalidItemInputs(): List<String> = listOf(
            """{"id":"notanumber","name":"a"}""", // type mismatch: string where Int expected
            """{"id":1,"name":""",                 // truncated / malformed input
            """{"id":1,"name":"a",}""",            // trailing comma, default config rejects
            """{"id":1,/*c*/"name":"a"}""",        // comment, default config rejects
            """{"id":1,"name":"a"}trailing""",     // trailing garbage after a complete value
            """{"id":1,"name":"a","extra":2}""",   // unknown key, default config rejects
            """[1,2,3]""",                          // wrong top-level shape (array, not object)
        )
    }

    @ParameterizedTest(name = "invalid input rejected: {0}")
    @MethodSource("invalidItemInputs")
    fun invalidInputThrowsSerializationException(input: String) {
        assertFailsWith<SerializationException> { Json.decodeFromString<Item>(input) }
    }

    /** Contract: a missing required field is a SerializationException (MissingFieldException subtype). */
    @Test
    fun missingRequiredFieldThrows() {
        assertFailsWith<SerializationException> { Json.decodeFromString<Item>("""{"id":1}""") }
    }

    /** Contract: encoding a non-finite Double without allowSpecialFloatingPointValues is rejected. */
    @Test
    fun encodingNaNWithoutOptInThrows() {
        assertFailsWith<SerializationException> { Json.encodeToString(listOf(Double.NaN)) }
    }

    /** Contract: with allowSpecialFloatingPointValues=true, NaN/Infinity encode as bare float literals. */
    @Test
    fun specialFloatsEncodeWhenAllowed() {
        val json = Json { allowSpecialFloatingPointValues = true }
        kotlin.test.assertEquals("[1.0,NaN,-Infinity]", json.encodeToString(listOf(1.0, Double.NaN, Double.NEGATIVE_INFINITY)))
    }
}
