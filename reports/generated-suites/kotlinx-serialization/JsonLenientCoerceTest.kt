/*
 * Generated matrix suite (iter20) — relaxation flags as with/without boundary pairs.
 * For each flag the strict (default) side asserts the exception TYPE only, and the relaxed
 * side asserts the decoded value — so the test fails if the flag is ignored in either direction.
 * No or-joined message checks; configuration is via the public Json { } builder only.
 */
package kotlinx.serialization.genjson

import kotlinx.serialization.SerializationException
import kotlinx.serialization.decodeFromString
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import org.junit.jupiter.api.Test

class JsonLenientCoerceTest {

    /** Contract: default config rejects an unquoted key/value (RFC-strict). */
    @Test
    fun strictRejectsUnquotedTokens() =
        assertFailsWith<SerializationException> { Json.decodeFromString<SingleKey>("""{key:value}""") }

    /** Contract: isLenient=true accepts unquoted keys and string values. */
    @Test
    fun lenientAcceptsUnquotedTokens() =
        assertEquals(SingleKey("value"), Json { isLenient = true }.decodeFromString<SingleKey>("""{key:value}"""))

    /** Contract: default config rejects an unknown enum member. */
    @Test
    fun strictRejectsUnknownEnumMember() =
        assertFailsWith<SerializationException> { Json.decodeFromString<Coercible>("""{"e":"unknown"}""") }

    /** Contract: coerceInputValues=true replaces an unknown enum value with the property default. */
    @Test
    fun coerceReplacesUnknownEnumWithDefault() =
        assertEquals(
            Coercible("def", Named.VALUE_A),
            Json { coerceInputValues = true }.decodeFromString<Coercible>("""{"e":"unknown"}"""),
        )

    /** Contract: default config rejects an enum serial name that differs only by case. */
    @Test
    fun strictRejectsMisCasedEnumName() =
        assertFailsWith<SerializationException> { Json.decodeFromString<NamedHolder>("""{"e":"value_a"}""") }

    /** Contract: decodeEnumsCaseInsensitive=true accepts an enum name in any case. */
    @Test
    fun caseInsensitiveAcceptsMisCasedEnumName() =
        assertEquals(
            NamedHolder(Named.VALUE_A),
            Json { decodeEnumsCaseInsensitive = true }.decodeFromString<NamedHolder>("""{"e":"value_a"}"""),
        )

    /** Contract: prettyPrint formats a primitive array across lines with the default indent. */
    @Test
    fun prettyPrintFormatsArray() {
        val expected = "[\n    1,\n    2\n]"
        assertEquals(expected, Json { prettyPrint = true }.encodeToString(listOf(1, 2)))
    }
}
