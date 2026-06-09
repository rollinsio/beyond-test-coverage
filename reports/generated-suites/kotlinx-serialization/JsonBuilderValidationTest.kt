/*
 * Generated matrix suite (iter20) — JsonBuilder.build() validation boundaries and the
 * JsonUnquotedLiteral null guard. These protect the require(...) / throw checks in the
 * public builder; each asserts the exception TYPE only (A.1 = 0).
 */
package kotlinx.serialization.genjson

import kotlinx.serialization.SerializationException
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonUnquotedLiteral
import kotlin.test.assertFailsWith
import org.junit.jupiter.api.Test

class JsonBuilderValidationTest {

    /** Contract: a non-whitespace prettyPrintIndent is rejected by the builder. */
    @Test
    fun rejectsNonWhitespaceIndent() =
        assertFailsWith<IllegalArgumentException> { Json { prettyPrint = true; prettyPrintIndent = "xx" } }

    /** Contract: specifying prettyPrintIndent without enabling prettyPrint is rejected. */
    @Test
    fun rejectsIndentWithoutPrettyPrint() =
        assertFailsWith<IllegalArgumentException> { Json { prettyPrintIndent = "  " } }

    /** Contract: useArrayPolymorphism with a non-default classDiscriminator is rejected. */
    @Test
    fun rejectsArrayPolymorphismWithCustomDiscriminator() =
        assertFailsWith<IllegalArgumentException> { Json { useArrayPolymorphism = true; classDiscriminator = "kind" } }

    /** Contract: JsonUnquotedLiteral("null") is forbidden and throws a SerializationException. */
    @Test
    fun rejectsUnquotedNullLiteral() =
        assertFailsWith<SerializationException> { JsonUnquotedLiteral("null") }
}
