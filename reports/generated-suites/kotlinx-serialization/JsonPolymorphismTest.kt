/*
 * Generated matrix suite (iter20) — class discriminator + numeric wire forms.
 * New contracts not covered by the round-1 suite. Each pins a fixed literal directly
 * in the assertEquals (B.1) and is mutation-sensitive (the with/without-discriminator
 * pair would diverge if classDiscriminator were ignored).
 */
package kotlinx.serialization.genjson

import kotlinx.serialization.decodeFromString
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import kotlin.test.assertEquals
import org.junit.jupiter.api.Test

class JsonPolymorphismTest {

    /** Contract: a sealed subtype encodes with the default `type` discriminator carrying its serial name. */
    @Test
    fun polymorphicEncodesDefaultDiscriminator() =
        assertEquals("""{"type":"circle","r":5}""", Json.encodeToString<Shape>(Circle(5)))

    /** Contract: classDiscriminator renames the discriminator key in the wire form. */
    @Test
    fun polymorphicEncodesCustomDiscriminator() =
        assertEquals(
            """{"kind":"square","side":3}""",
            Json { classDiscriminator = "kind" }.encodeToString<Shape>(Square(3)),
        )

    /** Contract: a discriminated object decodes back to the concrete sealed subtype. */
    @Test
    fun polymorphicDecodesByDiscriminator() =
        assertEquals(Circle(5), Json.decodeFromString<Shape>("""{"type":"circle","r":5}"""))

    /** Contract: a custom-discriminator wire form decodes back when the same key is configured. */
    @Test
    fun polymorphicDecodesCustomDiscriminator() =
        assertEquals(
            Square(3),
            Json { classDiscriminator = "kind" }.decodeFromString<Shape>("""{"kind":"square","side":3}"""),
        )

    /** Contract: Long / UInt / ULong are written as bare numeric literals (incl. values beyond Int/Long range). */
    @Test
    fun unsignedAndLongNumbersEncodeAsBareLiterals() =
        assertEquals(
            """{"l":9999999999,"u":4294967295,"ul":18446744073709551615}""",
            Json.encodeToString(Nums(9999999999L, 4294967295u, ULong.MAX_VALUE)),
        )

    /** Contract: the large-number wire form round-trips back to the same model value. */
    @Test
    fun unsignedAndLongNumbersRoundTrip() {
        val v = Nums(9999999999L, 4294967295u, ULong.MAX_VALUE)
        assertEquals(v, Json.decodeFromString<Nums>(Json.encodeToString(v)))
    }
}
