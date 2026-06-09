/*
 * Generated matrix suite (iter20) — naming strategy and polymorphism-output modes.
 * Each pins the exact wire form that the corresponding builder flag produces (B.1),
 * and is mutation-sensitive: the literal differs from the default-config output.
 */
package kotlinx.serialization.genjson

import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.ClassDiscriminatorMode
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonNamingStrategy
import kotlin.test.assertEquals
import org.junit.jupiter.api.Test

class JsonDiscriminatorModeTest {

    /** Contract: JsonNamingStrategy.SnakeCase rewrites camelCase property names to snake_case. */
    @Test
    fun snakeCaseNamingStrategyRewritesKeys() =
        assertEquals(
            """{"first_name":"a","last_name":"b"}""",
            Json { namingStrategy = JsonNamingStrategy.SnakeCase }.encodeToString(TwoWords("a", "b")),
        )

    /** Contract: useArrayPolymorphism=true emits the [name, body] array form for a polymorphic value. */
    @Test
    fun arrayPolymorphismEmitsArrayForm() =
        assertEquals(
            """["circle",{"r":5}]""",
            Json { useArrayPolymorphism = true }.encodeToString<Shape>(Circle(5)),
        )

    /** Contract: classDiscriminatorMode=NONE omits the discriminator from the polymorphic output. */
    @Test
    fun discriminatorModeNoneOmitsDiscriminator() =
        assertEquals(
            """{"r":5}""",
            Json { classDiscriminatorMode = ClassDiscriminatorMode.NONE }.encodeToString<Shape>(Circle(5)),
        )
}
