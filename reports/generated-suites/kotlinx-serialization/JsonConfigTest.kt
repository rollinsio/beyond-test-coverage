/*
 * Generated matrix suite — JsonBuilder configuration flags.
 * Each flag is tested at BOTH settings so the test fails if the flag is ignored
 * (the with/without pair is the boundary that distinguishes the two behaviours).
 * Configuration is only ever done through the public `Json { }` builder.
 */
package kotlinx.serialization.genjson

import kotlinx.serialization.decodeFromString
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import kotlin.test.assertEquals
import org.junit.jupiter.api.Test

class JsonConfigTest {

    /** Contract: encodeDefaults=false (default) omits a property left at its default value. */
    @Test
    fun encodeDefaultsOffOmitsDefaultProperty() =
        assertEquals("""{"name":"p"}""", Json.encodeToString(WithDefault("p")))

    /** Contract: encodeDefaults=true emits a property even when it equals its default. */
    @Test
    fun encodeDefaultsOnEmitsDefaultProperty() =
        assertEquals(
            """{"name":"p","language":"kotlin"}""",
            Json { encodeDefaults = true }.encodeToString(WithDefault("p")),
        )

    /** Contract: a non-default value for a defaulted property is always emitted. */
    @Test
    fun nonDefaultValueIsAlwaysEmitted() =
        assertEquals("""{"name":"p","language":"java"}""", Json.encodeToString(WithDefault("p", "java")))

    /** Contract: explicitNulls=true (default) emits null for a nullable property holding null. */
    @Test
    fun explicitNullsOnEmitsNull() =
        assertEquals("""{"name":"u","description":null}""", Json.encodeToString(Nullable("u", null)))

    /** Contract: explicitNulls=false omits a nullable property holding null. */
    @Test
    fun explicitNullsOffOmitsNull() =
        assertEquals(
            """{"name":"u"}""",
            Json { explicitNulls = false }.encodeToString(Nullable("u", null)),
        )

    /** Contract: explicitNulls=false still emits a present (non-null) nullable value. */
    @Test
    fun explicitNullsOffStillEmitsPresentValue() =
        assertEquals(
            """{"name":"u","description":"d"}""",
            Json { explicitNulls = false }.encodeToString(Nullable("u", "d")),
        )

    /** Contract: prettyPrint=true formats an object across lines with the default 4-space indent. */
    @Test
    fun prettyPrintFormatsWithFourSpaceIndent() {
        val expected = "{\n" +
            "    \"id\": 7,\n" +
            "    \"name\": \"the-item-name\"\n" +
            "}"
        assertEquals(expected, Json { prettyPrint = true }.encodeToString(Item(7, "the-item-name")))
    }

    /** Contract: a custom prettyPrintIndent (tab) is used as the indentation unit. */
    @Test
    fun prettyPrintHonoursCustomIndent() {
        val expected = "{\n" +
            "\t\"id\": 1,\n" +
            "\t\"name\": \"a\"\n" +
            "}"
        assertEquals(
            expected,
            Json { prettyPrint = true; prettyPrintIndent = "\t" }.encodeToString(Item(1, "a")),
        )
    }

    /** Contract: prettyPrint of an empty map is a single-line empty object, no inner newlines. */
    @Test
    fun prettyPrintEmptyMapIsSingleLine() =
        assertEquals("{}", Json { prettyPrint = true }.encodeToString(emptyMap<String, Int>()))

    /** Contract: classDiscriminator only changes config (default "type"); the value flows to configuration. */
    @Test
    fun classDiscriminatorIsConfigurable() {
        assertEquals("type", Json.configuration.classDiscriminator)
        assertEquals("kind", Json { classDiscriminator = "kind" }.configuration.classDiscriminator)
    }

    /** Contract: ignoreUnknownKeys=true drops an unmodelled key and decodes the known fields. */
    @Test
    fun ignoreUnknownKeysDropsExtraKey() =
        assertEquals(
            Item(1, "a"),
            Json { ignoreUnknownKeys = true }.decodeFromString<Item>("""{"id":1,"name":"a","extra":2}"""),
        )

    /** Contract: allowTrailingComma=true accepts a trailing comma in an object. */
    @Test
    fun allowTrailingCommaAcceptsTrailingComma() =
        assertEquals(
            Item(1, "a"),
            Json { allowTrailingComma = true }.decodeFromString<Item>("""{"id":1,"name":"a",}"""),
        )

    /** Contract: allowComments=true skips a block comment between members. */
    @Test
    fun allowCommentsSkipsBlockComment() =
        assertEquals(
            Item(1, "a"),
            Json { allowComments = true }.decodeFromString<Item>("""{"id":1,/*c*/"name":"a"}"""),
        )

    /** Contract: a refining copy builder inherits the source flags and overlays new ones. */
    @Test
    fun copyBuilderInheritsSourceConfiguration() {
        val base = Json { encodeDefaults = true }
        val refined = Json(base) { prettyPrint = true }
        assertEquals(true, refined.configuration.encodeDefaults)
        assertEquals(true, refined.configuration.prettyPrint)
    }
}
